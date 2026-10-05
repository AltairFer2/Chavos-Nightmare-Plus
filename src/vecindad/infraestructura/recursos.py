"""Carga de imágenes con caché.

Todos los assets del juego se cargan por aquí para que una imagen que se
reutiliza (el fondo de una cámara, la figura de un animatrónico) se lea del
disco una sola vez y no en cada fotograma. Si un archivo no existe todavía
se devuelve None y cada pantalla dibuja su propio respaldo, de modo que el
juego siga corriendo mientras el arte está en producción.
"""

from typing import Dict, Optional

import pygame


def quitar_fondo_negro(imagen: pygame.Surface) -> pygame.Surface:
    """Convierte el negro de una imagen en transparencia.

    Pensado para el arte dibujado sobre fondo negro (el mapa de las
    cámaras): el canal más fuerte de cada píxel pasa a ser su alfa, así que
    lo negro desaparece del todo, lo blanco queda opaco y los bordes
    suavizados conservan su degradado. Se toma el máximo de los tres canales
    y no solo el brillo para que un resaltado de color saturado (el rojo de
    la cámara activa) quede igual de opaco que el blanco.

    Todo se resuelve con slicing de bytes y blits (código C) en vez de
    recorrer píxel a píxel, y ocurre una sola vez al cargar la imagen.
    """
    tamano = imagen.get_size()
    canales = pygame.image.tostring(imagen, "RGB")
    total = tamano[0] * tamano[1]

    pixeles = bytearray(total * 4)
    pixeles[0::4] = canales[0::3]
    pixeles[1::4] = canales[1::3]
    pixeles[2::4] = canales[2::3]
    pixeles[3::4] = canales[0::3]
    resultado = pygame.image.frombuffer(bytes(pixeles), tamano, "RGBA").convert_alpha()

    # Sube el alfa al máximo de los tres canales: BLEND_RGBA_MAX deja el RGB
    # intacto (los otros dos parches son negros) y solo eleva el alfa.
    for desplazamiento in (1, 2):
        parche = bytearray(total * 4)
        parche[3::4] = canales[desplazamiento::3]
        capa = pygame.image.frombuffer(bytes(parche), tamano, "RGBA").convert_alpha()
        resultado.blit(capa, (0, 0), special_flags=pygame.BLEND_RGBA_MAX)
    return resultado


# Qué tan lejos del negro puro puede estar un píxel y seguir contando como
# fondo. Lo justo para absorber el ruido de compresión: subirlo se empieza a
# comer las partes oscuras del propio dibujo.
TOLERANCIA_FONDO = 2

# Tamaño mínimo, en píxeles, de una mancha oscura para tomarla por fondo. El
# fondo de una lámina siempre es una extensión grande; lo que toca el borde y
# es diminuto son motas del propio dibujo, y vale más dejarlas opacas que
# empezar a mordisquear el arte.
MINIMO_FONDO = 64


def quitar_fondo_alrededor(
    imagen: pygame.Surface, tolerancia: int = TOLERANCIA_FONDO
) -> pygame.Surface:
    """Vuelve transparente el negro que rodea al dibujo y deja intacto el que
    queda encerrado dentro de él.

    Es lo que separa el fondo de la lámina del monitor, que tiene que dejar
    ver el patio de detrás, de la pantalla apagada del propio aparato, que
    tiene que seguir siendo negra. Las dos zonas son del mismo color: lo único
    que las distingue es que una llega hasta el borde de la imagen y la otra
    está rodeada por el chasis.

    Se resuelve con máscaras de pygame (código C) y una sola vez, al cargar:
    se agrupan los píxeles casi negros y se conservan los grupos grandes que
    tocan el marco de la imagen. Si no hay ninguno, la imagen se queda entera.
    """
    ancho, alto = imagen.get_size()
    oscuros = pygame.mask.from_threshold(
        imagen, (0, 0, 0), (tolerancia, tolerancia, tolerancia, 255)
    )
    marco = _mascara_del_marco(ancho, alto)
    fondo = pygame.mask.Mask((ancho, alto))
    for grupo in oscuros.connected_components(minimum=MINIMO_FONDO):
        if grupo.overlap(marco, (0, 0)):
            fondo.draw(grupo, (0, 0))

    # BLEND_RGBA_MIN deja como está lo que la capa marca en blanco opaco y
    # pone a cero (transparente) lo que marca en negro sin alfa.
    capa = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    fondo.to_surface(capa, setcolor=(0, 0, 0, 0), unsetcolor=(255, 255, 255, 255))
    recortada = imagen.convert_alpha()
    recortada.blit(capa, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return recortada


def _mascara_del_marco(ancho: int, alto: int) -> "pygame.mask.Mask":
    """Solo el borde de un píxel de la imagen: es contra lo que se comprueba
    si una mancha oscura llega hasta fuera o está encerrada dentro del
    dibujo."""
    marco = pygame.mask.Mask((ancho, alto), fill=True)
    marco.erase(pygame.mask.Mask((ancho - 2, alto - 2), fill=True), (1, 1))
    return marco


def cargar_imagen(ruta, con_alfa: bool = False) -> Optional[pygame.Surface]:
    """Lee una imagen del disco. Devuelve None si no está o si pygame no
    puede decodificarla."""
    if not ruta.exists():
        return None
    try:
        imagen = pygame.image.load(str(ruta))
    except pygame.error:
        return None
    return imagen.convert_alpha() if con_alfa else imagen.convert()


class CacheImagenes:
    """Diccionario de imágenes ya cargadas, indexadas por una clave propia
    (el id de la habitación, el nombre del personaje...) para no depender de
    la ruta completa en cada consulta.

    La transformación y el escalado se aplican una sola vez, al cargar: así
    el dibujado se reduce a un blit y no se reescala una imagen enorme en
    cada fotograma.
    """

    def __init__(self, con_alfa: bool = False, tamano=None, alto=None,
                 transformacion=None):
        self._con_alfa = con_alfa
        # tamano fuerza un ancho y alto exactos; alto escala conservando la
        # proporción original. Se usa uno o el otro, no los dos.
        self._tamano = tamano
        self._alto = alto
        self._transformacion = transformacion
        self._imagenes: Dict[str, Optional[pygame.Surface]] = {}

    def obtener(self, clave: str, ruta) -> Optional[pygame.Surface]:
        if clave not in self._imagenes:
            self._imagenes[clave] = self._preparar(cargar_imagen(ruta, self._con_alfa))
        return self._imagenes[clave]

    def _preparar(self, imagen: Optional[pygame.Surface]) -> Optional[pygame.Surface]:
        if imagen is None:
            return None
        if self._transformacion is not None:
            imagen = self._transformacion(imagen)
        if self._tamano is not None and imagen.get_size() != self._tamano:
            imagen = pygame.transform.smoothscale(imagen, self._tamano)
        elif self._alto is not None and imagen.get_height() != self._alto:
            escala = self._alto / imagen.get_height()
            imagen = pygame.transform.smoothscale(
                imagen, (round(imagen.get_width() * escala), self._alto)
            )
        return imagen
