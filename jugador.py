"""El jugador: por dónde se mueve durante la noche y qué puede hacer desde
cada sitio.

Solo lleva la posición; la linterna y los objetos viven en sus propios
módulos para que cada recurso se pueda probar por separado.
"""

from posiciones import POSICION_INICIAL, obtener_posicion


class Jugador:
    """Posición del jugador dentro del hub del Primer Patio."""

    def __init__(self):
        self.posicion = POSICION_INICIAL

    @property
    def posicion_actual(self):
        return obtener_posicion(self.posicion)

    @property
    def esta_escondido(self) -> bool:
        """Dentro del barril: única posición desde la que se usan las cámaras
        y los servicios de utilidad."""
        return self.posicion_actual.es_refugio

    @property
    def puede_buscar(self) -> bool:
        return self.posicion_actual.permite_buscar

    def mover(self, direccion: int) -> bool:
        """Camina a un lado (-1 izquierda, 1 derecha). Devuelve False si no
        hay nada en esa dirección."""
        actual = self.posicion_actual
        destino = actual.izquierda if direccion < 0 else actual.derecha
        return self._ir_a(destino)

    def bajar(self) -> bool:
        """Se mete al barril."""
        return self._ir_a(self.posicion_actual.abajo)

    def subir(self) -> bool:
        """Se asoma fuera del barril."""
        return self._ir_a(self.posicion_actual.arriba)

    def _ir_a(self, destino) -> bool:
        if destino is None:
            return False
        self.posicion = destino
        return True

    def reiniciar(self):
        self.posicion = POSICION_INICIAL
