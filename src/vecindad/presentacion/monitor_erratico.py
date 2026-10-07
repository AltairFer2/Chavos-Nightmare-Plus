"""Desplazamiento errático para el monitor cuando El Chavo está en pantalla.

Lo usan dos piezas del panel de cámaras: la imagen de la cámara, que tiembla
a tirones cortos, y el mapa de selección, que se va de un lado a otro a
saltos. El mapa no solo se dibuja movido: sus botones se mueven con él, así
que cambiar de cámara exige atinarle a un recuadro que no se está quieto.

Cada cierto tiempo (al azar dentro de un rango) se elige un destino nuevo y
el desplazamiento corre hacia él; por eso no es un temblor parejo que se
pueda anticipar, sino arrancones en direcciones distintas.

No dibuja nada: solo calcula cuánto se corre cada cosa, para que el dibujo y
la detección de clics usen exactamente el mismo desplazamiento.
"""

import random
from typing import Optional, Tuple


class DesplazamientoErratico:
    """Un desplazamiento en píxeles que salta entre destinos al azar."""

    def __init__(
        self,
        amplitud: Tuple[int, int],
        cambio_segundos: Tuple[float, float],
        persecucion: float,
        azar: Optional[random.Random] = None,
    ):
        """`amplitud` es lo más que se aleja en cada eje con intensidad 1;
        `cambio_segundos`, cada cuánto (mínimo y máximo) elige destino nuevo;
        `persecucion`, qué tan rápido corre hacia él (por segundo)."""
        self._amplitud = amplitud
        self._cambio = cambio_segundos
        self._persecucion = persecucion
        self._azar = azar if azar is not None else random.Random()
        self.reiniciar()

    def reiniciar(self):
        self._actual = (0.0, 0.0)
        self._destino = (0.0, 0.0)
        self._para_cambiar = 0.0
        self.intensidad = 0.0

    @property
    def quieto(self) -> bool:
        return self.desplazamiento == (0, 0)

    @property
    def desplazamiento(self) -> Tuple[int, int]:
        x, y = self._actual
        return (
            round(x * self._amplitud[0] * self.intensidad),
            round(y * self._amplitud[1] * self.intensidad),
        )

    def actualizar(self, dt: float, intensidad: float):
        """`intensidad` va de 0 (quieto) a 1 (lo más errático)."""
        self.intensidad = max(0.0, min(1.0, intensidad))
        if self.intensidad == 0.0:
            self._actual = (0.0, 0.0)
            self._para_cambiar = 0.0
            return
        self._para_cambiar -= dt
        if self._para_cambiar <= 0.0:
            self._destino = (self._azar.uniform(-1.0, 1.0), self._azar.uniform(-1.0, 1.0))
            self._para_cambiar = self._azar.uniform(*self._cambio)
        avance = min(1.0, dt * self._persecucion)
        x, y = self._actual
        destino_x, destino_y = self._destino
        self._actual = (x + (destino_x - x) * avance, y + (destino_y - y) * avance)
