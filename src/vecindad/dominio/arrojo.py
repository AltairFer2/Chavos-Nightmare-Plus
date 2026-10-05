"""Un objeto arrojado mientras va por el aire.

Se suelta hacia donde apunta el ratón y su efecto se resuelve al caer, no al
soltarlo: así el personaje se va cuando el objeto le llega, y el jugador ve
el tiro entero antes de saber si acertó. A quién le da y qué le hace lo
decide dominio/animatronicos/enfrentamiento.py en ese momento.
"""

from dataclasses import dataclass
from typing import Tuple

from ..config.jugabilidad import ARROJO_DURACION_VUELO_SEGUNDOS


@dataclass
class ObjetoEnVuelo:
    id_objeto: str
    # Adónde se apuntó, en píxeles del lienzo base.
    destino: Tuple[int, int]
    # Desde qué sitio se arrojó. El tiro se resuelve contra ese ángulo del
    # patio aunque el jugador se haya movido mientras volaba.
    id_posicion: str
    duracion: float = ARROJO_DURACION_VUELO_SEGUNDOS
    transcurrido: float = 0.0

    def avanzar(self, dt: float) -> bool:
        """Lo hace avanzar. True el fotograma en que cae."""
        self.transcurrido = min(self.duracion, self.transcurrido + dt)
        return self.cayo

    @property
    def cayo(self) -> bool:
        return self.transcurrido >= self.duracion

    @property
    def progreso(self) -> float:
        """De 0.0 al soltarlo a 1.0 al caer."""
        if self.duracion <= 0.0:
            return 1.0
        return self.transcurrido / self.duracion
