"""Linterna del jugador: el único recurso limitado de la noche.

Encendida consume la batería puesta; al agotarse se apaga sola y no vuelve a
encender hasta que el jugador cambia la batería por una de repuesto. Las
baterías de repuesto se recogen fuera del barril (ver objetos.py), salvo las
que ya trae puestas al empezar en las primeras noches.
"""

from ..config.jugabilidad import (
    BATERIAS_INICIALES_EN_BARRIL,
    LINTERNA_BATERIAS_MAXIMAS,
    LINTERNA_DURACION_BATERIA_SEGUNDOS,
    LINTERNA_RADIO,
    NOCHE_SIN_BATERIAS_FIJAS,
)


def esta_iluminado(punto, punto_luz) -> bool:
    """True si el punto cae dentro del círculo de luz. Sirve para saber qué
    alcanza a ver el jugador con el haz donde lo tiene apuntado."""
    if punto_luz is None:
        return False
    distancia_x = punto[0] - punto_luz[0]
    distancia_y = punto[1] - punto_luz[1]
    return distancia_x * distancia_x + distancia_y * distancia_y <= LINTERNA_RADIO ** 2


def baterias_iniciales(numero_noche: int) -> int:
    """Repuestos que el jugador encuentra dentro del barril al empezar la
    noche. Desde NOCHE_SIN_BATERIAS_FIJAS ya no hay ninguno."""
    return BATERIAS_INICIALES_EN_BARRIL if numero_noche < NOCHE_SIN_BATERIAS_FIJAS else 0


class Linterna:
    """Estado de la linterna y de las baterías que carga el jugador."""

    def __init__(self, baterias_repuesto: int = 0):
        self.encendida = False
        self.carga = 1.0  # 0.0 a 1.0 de la batería puesta
        self.baterias_repuesto = baterias_repuesto

    @property
    def agotada(self) -> bool:
        return self.carga <= 0.0

    def alternar(self) -> bool:
        """Enciende o apaga. Con la batería agotada no hace nada; devuelve el
        estado en que quedó."""
        if self.agotada:
            self.encendida = False
        else:
            self.encendida = not self.encendida
        return self.encendida

    def actualizar(self, dt: float):
        if not self.encendida:
            return
        self.carga = max(0.0, self.carga - dt / LINTERNA_DURACION_BATERIA_SEGUNDOS)
        if self.agotada:
            self.encendida = False

    def descargar(self):
        """Deja la batería a cero de golpe y apaga la linterna. Es el castigo
        por alumbrar a La Chilindrina: no mata, pero deja al jugador a
        oscuras hasta que ponga un repuesto."""
        self.carga = 0.0
        self.encendida = False

    @property
    def baterias_llenas(self) -> bool:
        """Si ya no le cabe otro repuesto en el bolsillo."""
        return self.baterias_repuesto >= LINTERNA_BATERIAS_MAXIMAS

    def guardar_bateria(self) -> bool:
        """Guarda un repuesto. False si el bolsillo ya está lleno: el tope
        existe para que acaparar baterías no sea una estrategia, y para que
        el suelo siga ofreciendo lo que de verdad hace falta."""
        if self.baterias_llenas:
            return False
        self.baterias_repuesto += 1
        return True

    def cambiar_bateria(self) -> bool:
        """Pone una batería de repuesto. Devuelve False si no hay repuestos o
        si la puesta todavía sirve (para no desperdiciarla)."""
        if self.baterias_repuesto <= 0 or not self.agotada:
            return False
        self.baterias_repuesto -= 1
        self.carga = 1.0
        return True

    def reiniciar(self, baterias_repuesto: int = 0):
        self.encendida = False
        self.carga = 1.0
        self.baterias_repuesto = baterias_repuesto
