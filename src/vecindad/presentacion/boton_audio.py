"""El botón de audio del monitor de cámaras.

Es lo único con lo que se puede actuar sobre la vecindad sin salir del barril:
suena una grabación de Quico en la cámara que se está mirando, y Doña
Florinda va hacia allá si es vecina de la suya. Va abajo a la izquierda del
monitor, entre la fecha y el mapa.

Las reproducciones están contadas por noche (la primera es ilimitada), pero
el botón no dice cuántas quedan: llevar la cuenta es parte de lo que el
jugador tiene que hacer de cabeza. Lo único que se nota es que el botón se
apaga cuando ya no queda ninguna. Reponerlas es cosa del panel del barril.
"""

import pygame

from ..config.interfaz import (
    CAMARA_AUDIO_ALTO,
    CAMARA_AUDIO_ANCHO,
    CAMARA_AUDIO_MARGEN_INFERIOR,
    CAMARA_AUDIO_MARGEN_IZQUIERDO,
    COLOR_BLANCO,
)
from ..config.ventana import ALTO_PANTALLA

RECT_BOTON = pygame.Rect(
    CAMARA_AUDIO_MARGEN_IZQUIERDO,
    ALTO_PANTALLA - CAMARA_AUDIO_ALTO - CAMARA_AUDIO_MARGEN_INFERIOR,
    CAMARA_AUDIO_ANCHO,
    CAMARA_AUDIO_ALTO,
)

# El monitor está muy oscuro, así que el botón necesita su propio fondo para
# leerse encima de cualquier cámara.
COLOR_FONDO = (18, 20, 24, 205)
COLOR_FONDO_HOVER = (44, 52, 62, 225)
COLOR_BORDE = (150, 170, 190)
COLOR_BORDE_HOVER = (215, 238, 255)
COLOR_APAGADO = (120, 120, 120)
COLOR_FONDO_APAGADO = (14, 14, 16, 180)


class BotonAudio:
    """Dibuja el botón y dice si un clic cae dentro."""

    def contiene(self, posicion) -> bool:
        return posicion is not None and RECT_BOTON.collidepoint(posicion)

    def dibujar(self, superficie: pygame.Surface, estado, fuente=None,
                idiomas=None, posicion_raton=None):
        """`estado` es el EstadoServicios de la noche. De ahí solo se mira si
        el botón está usable: cuántas reproducciones quedan no se enseña."""
        activo = self._disponible(estado)
        sobre_el = activo and self.contiene(posicion_raton)

        fondo = pygame.Surface(RECT_BOTON.size, pygame.SRCALPHA)
        if not activo:
            fondo.fill(COLOR_FONDO_APAGADO)
        else:
            fondo.fill(COLOR_FONDO_HOVER if sobre_el else COLOR_FONDO)
        superficie.blit(fondo, RECT_BOTON)

        borde = COLOR_APAGADO if not activo else (
            COLOR_BORDE_HOVER if sobre_el else COLOR_BORDE
        )
        pygame.draw.rect(superficie, borde, RECT_BOTON, width=2)
        self._dibujar_rotulo(superficie, fuente, idiomas, activo)

    @staticmethod
    def _disponible(estado) -> bool:
        """Se apaga con otro servicio en marcha, durante la espera entre usos
        o sin reproducciones."""
        if estado.en_marcha is not None or estado.espera_audio > 0.0:
            return False
        return estado.audio_ilimitado or estado.usos_audio > 0

    @staticmethod
    def _dibujar_rotulo(superficie, fuente, idiomas, activo: bool):
        if not fuente or not idiomas:
            return
        texto = fuente.render(
            idiomas.t("camara_audio"),
            True,
            COLOR_BLANCO if activo else COLOR_APAGADO,
        )
        superficie.blit(texto, texto.get_rect(center=RECT_BOTON.center))
