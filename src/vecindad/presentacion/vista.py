"""Vista en primera persona del jugador: el fondo de la posición donde está
parado, lo que hay tirado en el suelo, los animatrónicos que lo acechan desde
ahí con su punto débil y la oscuridad recortada por el haz de la linterna.

Todo se dibuja primero y la oscuridad se echa encima al final, así que lo que
queda fuera del círculo de luz simplemente no se ve: encontrar objetos y
detectar quién está enfrente depende de hacia dónde apunte el jugador.

Convención de assets:
- assets/posiciones/<archivo>.png: fondo de cada posición (ver posiciones.py).
- assets/animatronics/<Nombre del personaje>.png: figura del personaje
  acechando, centrada en su punto de acecho.
Si un archivo no existe todavía se dibuja un respaldo y el juego sigue.
"""

import math

import pygame

from ..config.interfaz import (
    ALTO_ANIMATRONIC_VISTA,
    COLOR_GRIS,
    COLOR_GRIS_OSCURO,
    ICONO_OBJETO_SUELO,
    LINTERNA_COLOR_LUZ,
    OBJETO_PARPADEO_SEGUNDOS,
    OBJETO_PARPADEOS_POR_SEGUNDO,
    OSCURIDAD_OPACIDAD,
    PUNTO_DEBIL_COLOR,
    PUNTO_DEBIL_COLOR_PROGRESO,
    PUNTO_DEBIL_GROSOR_PROGRESO,
    PUNTO_DEBIL_LATIDOS_POR_SEGUNDO,
    PUNTO_DEBIL_OPACIDAD_HALO,
    PUNTO_DEBIL_RADIO_NUCLEO,
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
        # Halos del punto débil, uno por radio: se hacen la primera vez que
        # hace falta cada tamaño y se reutilizan.
        self._halos = {}

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
                objetos_en_suelo, linterna, punto_luz, fuente=None, idiomas=None,
                espanto=None):
        posicion = jugador.posicion_actual
        self._dibujar_fondo(superficie, posicion, fuente, idiomas)
        if posicion.permite_buscar:
            self._dibujar_objeto(superficie, posicion, objetos_en_suelo, fuente, idiomas)
        for animatronic in acechando_en(animatronics, posicion.id):
            self._dibujar_animatronic(superficie, animatronic, posicion.id)
            if espanto is not None:
                self._dibujar_punto_debil(superficie, animatronic, posicion.id, espanto)
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
        """Dibuja lo que haya tirado en su sitio. Cuando está por irse
        parpadea: el tiempo que le queda se lee mirándolo."""
        if self._oculto_por_parpadeo(objetos_en_suelo.segundos_para_irse()):
            return
        for id_objeto in objetos_en_suelo.objetos_en(posicion.id):
            self._dibujar_objeto_suelto(
                superficie, obtener_objeto(id_objeto).punto_suelo, id_objeto,
                fuente, idiomas,
            )

    @staticmethod
    def _oculto_por_parpadeo(segundos_para_irse: float) -> bool:
        """Si en este instante del parpadeo toca no dibujarlo. Se calcula
        del tiempo que le queda, así no hace falta otro reloj."""
        if not 0.0 < segundos_para_irse <= OBJETO_PARPADEO_SEGUNDOS:
            return False
        return int(segundos_para_irse * OBJETO_PARPADEOS_POR_SEGUNDO * 2) % 2 == 1

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

    def _dibujar_punto_debil(self, superficie, animatronic, id_posicion, espanto):
        """El punto que hay que sostener con el haz: un halo que late del
        tamaño de lo que cuenta como acertarle, un núcleo para apuntar y un
        arco alrededor con lo que lleva sostenido. Va antes de la penumbra,
        así que solo se ve alumbrándolo."""
        centro = espanto.punto_de(animatronic, id_posicion)
        if centro is None:
            return
        radio = round(animatronic.radio_punto_debil())
        halo = self._halo_de(radio)
        latido = (math.sin(pygame.time.get_ticks() / 1000.0
                           * PUNTO_DEBIL_LATIDOS_POR_SEGUNDO * 2 * math.pi) + 1) / 2
        minima, maxima = PUNTO_DEBIL_OPACIDAD_HALO
        halo.set_alpha(round(minima + (maxima - minima) * latido))
        superficie.blit(halo, halo.get_rect(center=centro))
        pygame.draw.circle(superficie, PUNTO_DEBIL_COLOR, centro, PUNTO_DEBIL_RADIO_NUCLEO)

        progreso = espanto.progreso_de(animatronic)
        if progreso <= 0.0:
            return
        caja = pygame.Rect(0, 0, radio * 2 + 12, radio * 2 + 12)
        caja.center = centro
        # Empieza arriba y avanza en el sentido de las agujas del reloj.
        inicio = math.pi / 2 - 2 * math.pi * min(1.0, progreso)
        pygame.draw.arc(
            superficie, PUNTO_DEBIL_COLOR_PROGRESO, caja, inicio, math.pi / 2,
            PUNTO_DEBIL_GROSOR_PROGRESO,
        )

    def _halo_de(self, radio: int) -> pygame.Surface:
        if radio not in self._halos:
            halo = pygame.Surface((radio * 2, radio * 2), pygame.SRCALPHA)
            pygame.draw.circle(halo, (*PUNTO_DEBIL_COLOR, 255), (radio, radio), radio)
            self._halos[radio] = halo
        return self._halos[radio]

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
