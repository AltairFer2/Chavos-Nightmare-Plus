"""Vista en primera persona del jugador: el fondo de la posición donde está
parado, lo que hay tirado en el suelo, los animatrónicos que lo acechan desde
ahí y la oscuridad recortada por el haz de la linterna.

Todo se dibuja primero y la oscuridad se echa encima al final, así que lo que
queda fuera del círculo de luz simplemente no se ve: encontrar objetos y
detectar quién está enfrente depende de hacia dónde apunte el jugador.

Convención de assets:
- assets/posiciones/<archivo>.png: fondo de cada posición (ver posiciones.py).
- assets/animatronics/<Nombre del personaje>.png: figura del personaje
  acechando, centrada en su punto de acecho.
Si un archivo no existe todavía se dibuja un respaldo y el juego sigue.
"""

import pygame

from ..config.interfaz import (
    ALTO_ANIMATRONIC_VISTA,
    ARROJO_ALTURA_ARCO,
    ARROJO_ORIGEN,
    COLOR_GRIS,
    COLOR_GRIS_OSCURO,
    ICONO_OBJETO_SUELO,
    LINTERNA_COLOR_LUZ,
    OSCURIDAD_OPACIDAD,
)
from ..config.jugabilidad import LINTERNA_RADIO
from ..config.ventana import ALTO_PANTALLA, ANCHO_PANTALLA, RESOLUCION_BASE
from ..dominio.animatronicos import acechando_en
from ..dominio.objetos import obtener_objeto
from ..infraestructura.recursos import CacheImagenes

# Cuántos anillos se usan para el degradado del haz. Se dibuja una sola vez
# al iniciar, no por fotograma.
PASOS_DEGRADADO_LUZ = 48
# Exponente del degradado: por debajo de 1 el centro del haz se ve parejo y
# la caída se concentra en el borde.
CAIDA_DEGRADADO_LUZ = 0.6

COLOR_OBJETO = (235, 205, 90)


class VistaJugador:
    """Dibuja lo que el jugador tiene delante desde su posición actual."""

    def __init__(self, iconos):
        self._iconos = iconos
        self._fondos = CacheImagenes(con_alfa=True, tamano=RESOLUCION_BASE)
        self._figuras = CacheImagenes(con_alfa=True, alto=ALTO_ANIMATRONIC_VISTA)
        # Superficies reutilizadas en cada fotograma para no reservar memoria
        # dentro del bucle de dibujado.
        self._oscuridad = pygame.Surface(RESOLUCION_BASE, pygame.SRCALPHA)
        self._mascara_luz = self._crear_degradado(
            lambda intensidad: (0, 0, 0, int(OSCURIDAD_OPACIDAD * intensidad))
        )
        self._brillo_luz = self._crear_degradado(
            lambda intensidad: tuple(int(canal * intensidad) for canal in LINTERNA_COLOR_LUZ)
        )

    @staticmethod
    def _crear_degradado(color_segun_intensidad) -> pygame.Surface:
        """Círculo pintado en anillos, de intensidad 1 en el centro a 0 en el
        borde. Se dibuja una sola vez al iniciar: la máscara que destapa la
        oscuridad y el brillo que suma luz comparten esta misma forma."""
        diametro = LINTERNA_RADIO * 2
        degradado = pygame.Surface((diametro, diametro), pygame.SRCALPHA)
        centro = (LINTERNA_RADIO, LINTERNA_RADIO)
        for paso in range(PASOS_DEGRADADO_LUZ, 0, -1):
            proporcion = paso / PASOS_DEGRADADO_LUZ
            intensidad = (1.0 - proporcion) ** CAIDA_DEGRADADO_LUZ
            pygame.draw.circle(
                degradado, color_segun_intensidad(intensidad), centro,
                int(LINTERNA_RADIO * proporcion),
            )
        return degradado

    def _fondo_de(self, posicion):
        return self._fondos.obtener(posicion.id, posicion.ruta_fondo)

    def _figura_de(self, animatronic):
        return self._figuras.obtener(animatronic.clave_sprite(), animatronic.ruta_sprite())

    def dibujar(self, superficie: pygame.Surface, jugador, animatronics,
                objetos_en_suelo, linterna, punto_luz, fuente=None, idiomas=None):
        posicion = jugador.posicion_actual
        self._dibujar_fondo(superficie, posicion, fuente, idiomas)
        if posicion.permite_buscar:
            self._dibujar_objeto(superficie, posicion, objetos_en_suelo, fuente, idiomas)
        for animatronic in acechando_en(animatronics, posicion.id):
            self._dibujar_animatronic(superficie, animatronic, posicion.id)
        self._dibujar_oscuridad(superficie, posicion, linterna, punto_luz)

    def _dibujar_fondo(self, superficie, posicion, fuente, idiomas):
        fondo = self._fondo_de(posicion)
        if fondo is not None:
            superficie.blit(fondo, (0, 0))
            return

        superficie.fill(COLOR_GRIS_OSCURO)
        pygame.draw.line(
            superficie, COLOR_GRIS,
            (0, ALTO_PANTALLA - 180), (ANCHO_PANTALLA, ALTO_PANTALLA - 180), 3,
        )
        if fuente and idiomas:
            texto = fuente.render(
                idiomas.t("vista_sin_fondo", posicion=posicion.nombre), True, COLOR_GRIS
            )
            superficie.blit(texto, texto.get_rect(center=(ANCHO_PANTALLA // 2, 140)))

    def _dibujar_objeto(self, superficie, posicion, objetos_en_suelo, fuente, idiomas):
        """Dibuja lo que esté en su sitio, cada cosa en el suyo. Lo que se
        recogió y todavía no vuelve simplemente no está."""
        for id_objeto in objetos_en_suelo.objetos_en(posicion.id):
            self._dibujar_objeto_suelto(
                superficie, obtener_objeto(id_objeto).punto_suelo, id_objeto,
                fuente, idiomas,
            )

    def _dibujar_objeto_suelto(self, superficie, punto, id_objeto, fuente, idiomas):
        icono = self._iconos.obtener(id_objeto, ICONO_OBJETO_SUELO)
        if icono is not None:
            superficie.blit(icono, icono.get_rect(center=punto))
        if fuente and idiomas:
            nombre = idiomas.t(obtener_objeto(id_objeto).clave_texto)
            texto = fuente.render(nombre, True, COLOR_OBJETO)
            superficie.blit(
                texto,
                texto.get_rect(
                    midtop=(punto[0], punto[1] + ICONO_OBJETO_SUELO // 2 + 4)
                ),
            )

    def _dibujar_animatronic(self, superficie, animatronic, id_posicion):
        """La figura se ancla por los pies en el punto que le toque desde
        donde esté mirando el jugador: el Barril y los Lavaderos son dos
        ángulos del mismo patio y el personaje no cae en el mismo sitio del
        lienzo en los dos."""
        figura = self._figura_de(animatronic)
        pisa = animatronic.punto_acecho_en(id_posicion)
        if figura is not None and pisa is not None:
            superficie.blit(figura, figura.get_rect(midbottom=pisa))

    def dibujar_objeto_en_vuelo(self, superficie, objeto_en_vuelo):
        """El objeto arrojado camino de donde se apuntó, en arco desde la
        mano del jugador. Va encima de la penumbra para que se vea adónde
        fue aunque se arroje a oscuras."""
        icono = self._iconos.obtener(objeto_en_vuelo.id_objeto, ICONO_OBJETO_SUELO)
        if icono is None:
            return
        avance = objeto_en_vuelo.progreso
        origen_x, origen_y = ARROJO_ORIGEN
        destino_x, destino_y = objeto_en_vuelo.destino
        # Parábola que vale 0 en los dos extremos y 1 a mitad de camino.
        elevacion = 4 * avance * (1 - avance) * ARROJO_ALTURA_ARCO
        centro = (
            origen_x + (destino_x - origen_x) * avance,
            origen_y + (destino_y - origen_y) * avance - elevacion,
        )
        superficie.blit(icono, icono.get_rect(center=centro))

    def _dibujar_oscuridad(self, superficie, posicion, linterna, punto_luz):
        """Tapa la escena de penumbra y, si la linterna está encendida, abre
        el haz: primero destapa el círculo y después le suma luz encima."""
        self._oscuridad.fill((0, 0, 0, posicion.oscuridad))
        alumbrando = linterna.encendida and punto_luz is not None
        if alumbrando:
            rect_haz = self._mascara_luz.get_rect(center=punto_luz)
            self._oscuridad.blit(
                self._mascara_luz, rect_haz, special_flags=pygame.BLEND_RGBA_SUB
            )
        superficie.blit(self._oscuridad, (0, 0))
        if alumbrando:
            superficie.blit(
                self._brillo_luz, rect_haz, special_flags=pygame.BLEND_RGB_ADD
            )
