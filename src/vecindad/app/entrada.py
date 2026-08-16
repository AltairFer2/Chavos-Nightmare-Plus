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
    COMBINAR_CAFE = auto()
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
    pygame.K_c: Accion.COMBINAR_CAFE,
    pygame.K_SPACE: Accion.ALTERNAR_CAMARAS,
    pygame.K_TAB: Accion.ALTERNAR_SERVICIOS,
    pygame.K_RETURN: Accion.CONFIRMAR,
    pygame.K_ESCAPE: Accion.ESCAPE,
}

# Teclas 1..7: cada una arroja siempre el mismo objeto, esté o no en el
# inventario, para que el jugador no tenga que releer la fila cada vez.
TECLAS_ARROJAR = (
    pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
    pygame.K_5, pygame.K_6, pygame.K_7,
)


def accion_de(tecla: int) -> Optional[Accion]:
    """Acción que corresponde a esa tecla, o None si no está asignada."""
    return ACCIONES_POR_TECLA.get(tecla)


def ranura_de(tecla: int) -> Optional[int]:
    """Ranura de inventario (0..6) de las teclas numéricas, o None."""
    if tecla not in TECLAS_ARROJAR:
        return None
    return TECLAS_ARROJAR.index(tecla)
