"""Apariciones raras: los easter eggs que se cuelan de vez en cuando.

Cada segundo de partida se tira 1 entre N (ver config/jugabilidad.py) a que
aparezca una de las imágenes raras. No cambia nada del juego: dura unos
segundos, casi transparente, y se va. Mientras una está a la vista no se
tira por otra.

Aquí solo vive cuándo sale y cuál; cómo se dibuja es cosa de
presentacion/aparicion_rara.py. `azar` permite fijar la semilla en las
pruebas.
"""

import random
from typing import Optional

from ..config.jugabilidad import (
    APARICION_RARA_SEGUNDOS,
    APARICION_RARA_UNO_ENTRE,
    APARICION_RARA_UNO_ENTRE_POR_NOCHE,
)


def uno_entre_de_la_noche(numero_noche: int) -> int:
    """El N de "1 entre N" por segundo para esa noche."""
    return APARICION_RARA_UNO_ENTRE_POR_NOCHE.get(numero_noche, APARICION_RARA_UNO_ENTRE)


class AparicionesRaras:
    """Lleva la cuenta de los segundos y decide cuándo aparece una."""

    def __init__(self, numero_noche: int, cantidad: int,
                 azar: Optional[random.Random] = None):
        """`cantidad` es cuántas imágenes raras hay para elegir; con 0 no
        aparece nunca nada."""
        self.uno_entre = uno_entre_de_la_noche(numero_noche)
        self.cantidad = cantidad
        self._azar = azar if azar is not None else random.Random()
        self._acumulado = 0.0
        self.actual: Optional[int] = None  # índice de la que está a la vista
        self._restante = 0.0

    @property
    def visible(self) -> bool:
        return self.actual is not None

    @property
    def progreso(self) -> float:
        """De 0 (acaba de aparecer) a 1 (a punto de irse)."""
        if self.actual is None:
            return 0.0
        return 1.0 - self._restante / APARICION_RARA_SEGUNDOS

    def actualizar(self, dt: float) -> Optional[int]:
        """Avanza el tiempo. Devuelve el índice de la imagen que acaba de
        aparecer en este paso (para que suene su audio), o None."""
        if self.actual is not None:
            self._restante -= dt
            if self._restante <= 0.0:
                self.actual = None
            return None
        if self.cantidad <= 0:
            return None
        self._acumulado += dt
        while self._acumulado >= 1.0:
            self._acumulado -= 1.0
            if self._azar.randrange(self.uno_entre) == 0:
                self._acumulado = 0.0
                self.actual = self._azar.randrange(self.cantidad)
                self._restante = APARICION_RARA_SEGUNDOS
                return self.actual
        return None
