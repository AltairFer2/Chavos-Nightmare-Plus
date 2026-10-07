"""La imagen avisando de que hay alguien en el Primer Patio.

Mientras alguien acecha, todo lo que se ve (el patio, el barril o el
monitor) va y viene entre color y un blanco y negro más oscuro, y tiembla.
Cuanto más cerca está el ataque, más rápido es el vaivén y más fuerte el
temblor: sirve de reloj sin tener que leer nada, también desde las cámaras,
donde el patio no se ve.

Se aplica sobre la escena ya dibujada y antes del HUD, que no se mueve ni
pierde color: la hora y la batería se tienen que poder leer.
"""

import math
import random
from typing import Optional

import pygame

from ..config.interfaz import (
    COLOR_NEGRO,
    PELIGRO_OSCURIDAD,
    PELIGRO_PERIODO_SEGUNDOS,
    PELIGRO_TEMBLOR_PIXELES,
)
from ..config.ventana import RESOLUCION_BASE

# Por debajo de esta mezcla el gris no se nota: no vale la pena calcularlo.
MEZCLA_INAPRECIABLE = 0.02

# El gris se calcula a 1/REDUCCION_GRIS de resolución y se vuelve a estirar:
# a tamaño completo grayscale se come medio fotograma (unos 9 ms a 1280x720),
# a la mitad son menos de 3. Que la capa gris salga algo más blanda no
# estorba: se ve encima del color, y es parte de que la imagen se degrade.
REDUCCION_GRIS = 2


def _poner_opacidad(superficie: pygame.Surface, opacidad: int):
    """Como set_alpha, pero a opacidad completa la quita: un blit con alfa
    exactamente 255 va por un camino lentísimo de pygame (unos 8 ms a
    1280x720, contra menos de 1 con cualquier otro valor)."""
    superficie.set_alpha(opacidad if opacidad < 255 else None)


def _interpolar(extremos, proporcion: float) -> float:
    inicio, fin = extremos
    return inicio + (fin - inicio) * proporcion


class AlertaPeligro:
    """El vaivén de color y el temblor; no sabe nada del juego, solo de lo
    cerca que está el ataque (la inminencia, de 0 a 1)."""

    def __init__(self, azar: Optional[random.Random] = None):
        self._azar = azar if azar is not None else random.Random()
        # Se reutilizan fotograma a fotograma. Se crean al primer dibujo, con
        # el formato de la superficie, porque grayscale y scale lo exigen.
        self._reducida: Optional[pygame.Surface] = None
        self._gris: Optional[pygame.Surface] = None
        self._oscuridad = pygame.Surface(RESOLUCION_BASE)
        self._oscuridad.fill(COLOR_NEGRO)
        self.reiniciar()

    def reiniciar(self):
        self._inminencia: Optional[float] = None
        self._fase = 0.0
        self.temblor = (0, 0)

    @property
    def activa(self) -> bool:
        return self._inminencia is not None

    @property
    def mezcla(self) -> float:
        """Qué tan gris y oscura está la imagen ahora: 0 en color, 1 en el
        punto más gris del vaivén. Empieza en color al llegar alguien."""
        if not self.activa:
            return 0.0
        return 0.5 - 0.5 * math.cos(2.0 * math.pi * self._fase)

    def periodo(self) -> float:
        """Segundos de un ciclo completo (color, gris, color)."""
        return _interpolar(PELIGRO_PERIODO_SEGUNDOS, self._inminencia or 0.0)

    def amplitud_temblor(self) -> float:
        if not self.activa:
            return 0.0
        return _interpolar(PELIGRO_TEMBLOR_PIXELES, self._inminencia)

    def actualizar(self, dt: float, inminencia: Optional[float]):
        """`inminencia` es None con el patio vacío. La fase avanza a la
        velocidad de ahora, así que acelerar no hace saltar la imagen."""
        if inminencia is None:
            self.reiniciar()
            return
        self._inminencia = max(0.0, min(1.0, inminencia))
        self._fase = (self._fase + dt / self.periodo()) % 1.0
        amplitud = round(self.amplitud_temblor())
        self.temblor = (
            self._azar.randint(-amplitud, amplitud),
            self._azar.randint(-amplitud, amplitud),
        )

    def dibujar(self, superficie: pygame.Surface):
        if not self.activa:
            return
        mezcla = self.mezcla
        if mezcla > MEZCLA_INAPRECIABLE:
            self._calcular_gris(superficie)
            _poner_opacidad(self._gris, round(255 * mezcla))
            superficie.blit(self._gris, (0, 0))
            _poner_opacidad(self._oscuridad, round(PELIGRO_OSCURIDAD * mezcla))
            superficie.blit(self._oscuridad, (0, 0))
        self._temblar(superficie)

    def _calcular_gris(self, superficie: pygame.Surface):
        tamano = superficie.get_size()
        if self._gris is None or self._gris.get_size() != tamano:
            reducido = (tamano[0] // REDUCCION_GRIS, tamano[1] // REDUCCION_GRIS)
            self._reducida = pygame.Surface(reducido, 0, superficie)
            self._gris = pygame.Surface(tamano, 0, superficie)
        pygame.transform.scale(superficie, self._reducida.get_size(), self._reducida)
        pygame.transform.grayscale(self._reducida, self._reducida)
        pygame.transform.scale(self._reducida, tamano, self._gris)

    def _temblar(self, superficie: pygame.Surface):
        """Corre la imagen y tapa de negro la franja que queda al
        descubierto, como una cámara sacudida."""
        dx, dy = self.temblor
        if dx == 0 and dy == 0:
            return
        superficie.scroll(dx, dy)
        ancho, alto = superficie.get_size()
        if dx > 0:
            superficie.fill(COLOR_NEGRO, (0, 0, dx, alto))
        elif dx < 0:
            superficie.fill(COLOR_NEGRO, (ancho + dx, 0, -dx, alto))
        if dy > 0:
            superficie.fill(COLOR_NEGRO, (0, 0, ancho, dy))
        elif dy < 0:
            superficie.fill(COLOR_NEGRO, (0, alto + dy, ancho, -dy))
