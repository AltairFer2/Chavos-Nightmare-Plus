"""Mensaje corto que aparece tras una acción y se borra solo.

Lo usan el arrojo de objetos, la combinación del café y los servicios del
barril para decir qué acaba de pasar sin interrumpir la partida.
"""

# Cuánto se queda en pantalla el mensaje de lo que acaba de pasar.
SEGUNDOS_AVISO = 2.5


class AvisoTemporal:
    """Un texto con cuenta atrás propia."""

    def __init__(self, duracion: float = SEGUNDOS_AVISO):
        self._duracion = duracion
        self.texto = ""
        self._restante = 0.0

    def mostrar(self, texto: str):
        """Un texto vacío borra el aviso actual."""
        self.texto = texto
        self._restante = self._duracion if texto else 0.0

    def actualizar(self, dt: float):
        if self._restante <= 0.0:
            return
        self._restante -= dt
        if self._restante <= 0.0:
            self.texto = ""

    def limpiar(self):
        self.mostrar("")
