"""Máquina de estados global del juego: menú, jugando, game over y victoria."""

from enum import Enum, auto


class EstadoJuego(Enum):
    MENU = auto()
    JUGANDO = auto()
    GAME_OVER = auto()
    VICTORIA = auto()


class GestorEstados:
    """Controla el estado activo del juego y expone consultas de conveniencia
    para el resto de los módulos."""

    def __init__(self):
        self.estado = EstadoJuego.MENU

    def cambiar_a(self, nuevo_estado: EstadoJuego):
        self.estado = nuevo_estado

    def en_menu(self) -> bool:
        return self.estado is EstadoJuego.MENU

    def jugando(self) -> bool:
        return self.estado is EstadoJuego.JUGANDO

    def termino_en_derrota(self) -> bool:
        return self.estado is EstadoJuego.GAME_OVER

    def termino_en_victoria(self) -> bool:
        return self.estado is EstadoJuego.VICTORIA
