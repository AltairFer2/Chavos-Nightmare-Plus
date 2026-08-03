"""Panel de servicios de utilidad: el tablero de madera del barril.

El arte (assets/ui/menu desplegable.png) ya trae dibujados los cuatro
recuadros con su rótulo, su icono y un piloto. Aquí solo se coloca encima el
estado que cambia durante la partida: el color del piloto, la barra de lo que
falta para que un servicio termine, los usos que le quedan al audio de Quico
y el oscurecido de lo que no se puede usar ahora mismo.

Los rótulos vienen pintados en el propio arte y están en español, así que
este panel no cambia con el idioma del juego.
"""

from typing import Dict, Optional, Tuple

import pygame

from constants import (
    ALTO_PANTALLA,
    ANCHO_PANTALLA,
    COLOR_NEGRO,
    DIR_ASSETS_UI,
    PANEL_SERVICIOS_LADO,
    PANEL_SERVICIOS_MARGEN_INFERIOR,
    USOS_AUDIO_QUICO,
)
from recursos import CacheImagenes
from servicios import Servicio

ARCHIVO_PANEL = "menu desplegable.png"

RECT_PANEL = pygame.Rect(
    (ANCHO_PANTALLA - PANEL_SERVICIOS_LADO) // 2,
    ALTO_PANTALLA - PANEL_SERVICIOS_LADO - PANEL_SERVICIOS_MARGEN_INFERIOR,
    PANEL_SERVICIOS_LADO,
    PANEL_SERVICIOS_LADO,
)

# Los cuatro recuadros del tablero, en fracciones del arte, en el mismo
# orden en que están rotulados: llamar al Sr. Barriga arriba a la izquierda,
# audio de Quico arriba a la derecha, cámaras abajo a la izquierda y
# restablecer todo abajo a la derecha.
BOTONES: Dict[Servicio, Tuple[float, float, float, float]] = {
    Servicio.BARRIGA: (0.112, 0.130, 0.376, 0.339),
    Servicio.AUDIO_QUICO: (0.513, 0.130, 0.381, 0.339),
    Servicio.CAMARAS: (0.112, 0.506, 0.376, 0.339),
    Servicio.TODO: (0.513, 0.506, 0.381, 0.339),
}

# Dónde cae el piloto dentro de cada recuadro, en fracciones del recuadro. El
# radio va algo holgado para tapar del todo el piloto que ya trae pintado el
# arte, que no está exactamente igual colocado en los cuatro cuadrantes.
PILOTO_X = 0.838
PILOTO_Y = 0.165
PILOTO_RADIO = 18

COLOR_PILOTO_LISTO = (70, 220, 110)
COLOR_PILOTO_TRABAJANDO = (240, 190, 60)
COLOR_PILOTO_BLOQUEADO = (215, 55, 45)
COLOR_BARRA_FONDO = (18, 14, 10)
COLOR_BARRA = (120, 210, 255)
COLOR_USO_LLENO = (215, 205, 170)
COLOR_USO_GASTADO = (60, 52, 42)
COLOR_HOVER = (255, 240, 190, 40)
COLOR_BLOQUEADO = (0, 0, 0, 120)

ALTO_BARRA = 16
MARGEN_BARRA = 18


class PanelServicios:
    """Dibuja el tablero y dice qué botón cae bajo el ratón."""

    def __init__(self):
        self.activo = False
        self._arte = CacheImagenes(con_alfa=True, tamano=RECT_PANEL.size)
        self._botones = self._calcular_botones()

    @staticmethod
    def _calcular_botones() -> Dict[Servicio, pygame.Rect]:
        return {
            servicio: pygame.Rect(
                RECT_PANEL.x + int(x * RECT_PANEL.width),
                RECT_PANEL.y + int(y * RECT_PANEL.height),
                int(ancho * RECT_PANEL.width),
                int(alto * RECT_PANEL.height),
            )
            for servicio, (x, y, ancho, alto) in BOTONES.items()
        }

    def alternar(self):
        self.activo = not self.activo

    def boton_en(self, posicion) -> Optional[Servicio]:
        if posicion is None:
            return None
        for servicio, rect in self._botones.items():
            if rect.collidepoint(posicion):
                return servicio
        return None

    def dibujar(self, superficie: pygame.Surface, servicios, posicion_raton=None):
        arte = self._arte.obtener(ARCHIVO_PANEL, DIR_ASSETS_UI / ARCHIVO_PANEL)
        if arte is None:
            return
        superficie.blit(arte, RECT_PANEL)

        estado = servicios.estado()
        hover = self.boton_en(posicion_raton)
        for servicio, rect in self._botones.items():
            self._dibujar_estado(superficie, servicio, rect, servicios, estado)
            if hover is servicio and servicios.disponible(servicio):
                self._pintar(superficie, rect, COLOR_HOVER)

    def _dibujar_estado(self, superficie, servicio, rect, servicios, estado):
        trabajando = estado.en_marcha is servicio
        disponible = servicios.disponible(servicio)

        if not disponible and not trabajando:
            self._pintar(superficie, rect, COLOR_BLOQUEADO)

        if trabajando:
            color_piloto = COLOR_PILOTO_TRABAJANDO
        elif disponible:
            color_piloto = COLOR_PILOTO_LISTO
        else:
            color_piloto = COLOR_PILOTO_BLOQUEADO
        centro = (
            rect.x + int(rect.width * PILOTO_X),
            rect.y + int(rect.height * PILOTO_Y),
        )
        pygame.draw.circle(superficie, color_piloto, centro, PILOTO_RADIO)
        pygame.draw.circle(superficie, COLOR_NEGRO, centro, PILOTO_RADIO, 2)

        if trabajando and estado.total > 0.0:
            self._dibujar_barra(superficie, rect, 1.0 - estado.restante / estado.total)
        elif servicio is Servicio.BARRIGA and estado.espera_barriga > 0.0:
            self._dibujar_barra(superficie, rect, 0.0)
        elif servicio is Servicio.AUDIO_QUICO and not estado.audio_ilimitado:
            self._dibujar_usos(superficie, rect, estado.usos_audio)

    @staticmethod
    def _rect_barra(rect: pygame.Rect) -> pygame.Rect:
        return pygame.Rect(
            rect.x + MARGEN_BARRA,
            rect.bottom - MARGEN_BARRA - ALTO_BARRA,
            rect.width - MARGEN_BARRA * 2,
            ALTO_BARRA,
        )

    def _dibujar_barra(self, superficie, rect, proporcion: float):
        barra = self._rect_barra(rect)
        pygame.draw.rect(superficie, COLOR_BARRA_FONDO, barra)
        avance = max(0, min(barra.width, int(barra.width * proporcion)))
        if avance:
            pygame.draw.rect(
                superficie, COLOR_BARRA, (barra.x, barra.y, avance, barra.height)
            )
        pygame.draw.rect(superficie, COLOR_NEGRO, barra, width=2)

    def _dibujar_usos(self, superficie, rect, usos: int):
        """Casillas con las reproducciones que le quedan al audio de Quico."""
        barra = self._rect_barra(rect)
        pygame.draw.rect(superficie, COLOR_BARRA_FONDO, barra)
        ancho = barra.width // USOS_AUDIO_QUICO
        for indice in range(USOS_AUDIO_QUICO):
            casilla = pygame.Rect(
                barra.x + indice * ancho + 2, barra.y + 2, ancho - 4, barra.height - 4
            )
            color = COLOR_USO_LLENO if indice < usos else COLOR_USO_GASTADO
            pygame.draw.rect(superficie, color, casilla)
        pygame.draw.rect(superficie, COLOR_NEGRO, barra, width=2)

    @staticmethod
    def _pintar(superficie, rect, color):
        capa = pygame.Surface(rect.size, pygame.SRCALPHA)
        capa.fill(color)
        superficie.blit(capa, rect)
