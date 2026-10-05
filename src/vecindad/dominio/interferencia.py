"""Una cámara pierde la señal cuando alguien se mueve delante de ella.

Si al jugador le toca estar mirando justo la cámara desde la que un personaje
se marcha, esa vista se cae unos segundos: se oye la interferencia, pero no se
alcanza a ver hacia dónde fue. Así vigilar a alguien de cerca tiene un precio
y el jugador tiene que reconstruir el recorrido en vez de seguirlo con la
mirada.

Es distinto del sabotaje de El Chavo (ver sabotaje.py): aquello tumba el
circuito entero hasta que se restablece a mano desde el barril, y esto se
arregla solo, afecta a una sola cámara y no depende de haberla mirado de más.

Cuánto dura cada corte se sortea dentro de un rango, para que no se pueda
contar de memoria cuándo vuelve la imagen.
"""

import random
from typing import Dict

from ..config.jugabilidad import (
    CAMARA_INTERFERENCIA_MAXIMA_SEGUNDOS,
    CAMARA_INTERFERENCIA_MINIMA_SEGUNDOS,
)


class InterferenciaCamaras:
    """Qué cámaras están sin señal ahora mismo y cuánto les queda."""

    def __init__(self):
        self._restante: Dict[str, float] = {}

    def cortar(self, id_camara: str) -> float:
        """Deja esa cámara sin señal un rato al azar.

        Devuelve los segundos que va a durar el corte, o 0.0 si esa cámara ya
        estaba caída: un corte no se reinicia con otro, porque si no, un
        personaje moviéndose sin parar la dejaría muerta toda la noche.
        """
        if id_camara in self._restante:
            return 0.0
        segundos = random.uniform(
            CAMARA_INTERFERENCIA_MINIMA_SEGUNDOS, CAMARA_INTERFERENCIA_MAXIMA_SEGUNDOS
        )
        self._restante[id_camara] = segundos
        return segundos

    def sin_senal(self, id_camara: str) -> bool:
        return id_camara in self._restante

    def actualizar(self, dt: float):
        """Descuenta el tiempo de cada corte y devuelve la señal a las que ya
        cumplieron."""
        if not self._restante:
            return
        self._restante = {
            id_camara: restante - dt
            for id_camara, restante in self._restante.items()
            if restante - dt > 0.0
        }

    def limpiar(self):
        """Devuelve la señal a todas de golpe. Es lo que hace empezar una
        noche nueva o restablecer el circuito desde el barril."""
        self._restante.clear()
