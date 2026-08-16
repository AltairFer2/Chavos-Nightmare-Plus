"""El mapa de la vecindad: los dos sistemas de lugares que usa el juego.

- habitaciones.py -> grafo de cámaras por el que se mueven los animatrónicos.
- posiciones.py   -> los cuatro sitios del Primer Patio por los que camina el
                     jugador (Lavaderos, Barril, Entrada y dentro del barril).

Son mapas distintos a propósito: el jugador no recorre la vecindad entera,
solo su rincón, y los animatrónicos no se paran en sus posiciones sino que
llegan a acecharlo desde ellas.

Solo depende de config/. No conoce pygame ni las reglas del juego.
"""

from .habitaciones import (
    HABITACION_JUGADOR,
    HABITACIONES,
    Habitacion,
    obtener_habitacion,
    son_adyacentes,
)
from .posiciones import (
    POSICION_BARRIL,
    POSICION_DENTRO_BARRIL,
    POSICION_INICIAL,
    POSICION_LAVADEROS,
    POSICIONES,
    POSICIONES_CON_OBJETOS,
    PosicionJugador,
    obtener_posicion,
)

__all__ = [
    "HABITACION_JUGADOR",
    "HABITACIONES",
    "Habitacion",
    "obtener_habitacion",
    "son_adyacentes",
    "POSICION_BARRIL",
    "POSICION_DENTRO_BARRIL",
    "POSICION_INICIAL",
    "POSICION_LAVADEROS",
    "POSICIONES",
    "POSICIONES_CON_OBJETOS",
    "PosicionJugador",
    "obtener_posicion",
]
