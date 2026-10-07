"""Qué tecla hace qué.

Traduce un código de tecla de pygame a una acción del juego, para que el
bucle principal razone en términos de "asomarse" o "recoger" y no de
constantes K_*. Cambiar los controles se hace aquí y en ningún otro sitio.
"""

from enum import Enum, auto
from typing import Dict, Optional

import pygame


class Accion(Enum):
    """Lo que el jugador puede pedir durante una noche."""

    CAMINAR_IZQUIERDA = auto()
    CAMINAR_DERECHA = auto()
    ESCONDERSE = auto()
    ASOMARSE = auto()
    RECOGER = auto()
    CAMBIAR_BATERIA = auto()
    ALTERNAR_CAMARAS = auto()
    ALTERNAR_SERVICIOS = auto()
    CONFIRMAR = auto()
    # Su significado depende del estado del juego: abre o cierra la pausa
    # durante la noche, y sale desde las pantallas de fin de partida.
    ESCAPE = auto()


ACCIONES_POR_TECLA: Dict[int, Accion] = {
    pygame.K_a: Accion.CAMINAR_IZQUIERDA,
    pygame.K_LEFT: Accion.CAMINAR_IZQUIERDA,
    pygame.K_d: Accion.CAMINAR_DERECHA,
    pygame.K_RIGHT: Accion.CAMINAR_DERECHA,
    pygame.K_s: Accion.ESCONDERSE,
    pygame.K_DOWN: Accion.ESCONDERSE,
    pygame.K_w: Accion.ASOMARSE,
    pygame.K_UP: Accion.ASOMARSE,
    pygame.K_e: Accion.RECOGER,
    pygame.K_r: Accion.CAMBIAR_BATERIA,
    pygame.K_SPACE: Accion.ALTERNAR_CAMARAS,
    pygame.K_TAB: Accion.ALTERNAR_SERVICIOS,
    pygame.K_RETURN: Accion.CONFIRMAR,
    pygame.K_ESCAPE: Accion.ESCAPE,
}


def accion_de(tecla: int) -> Optional[Accion]:
    """Acción que corresponde a esa tecla, o None si no está asignada."""
    return ACCIONES_POR_TECLA.get(tecla)
