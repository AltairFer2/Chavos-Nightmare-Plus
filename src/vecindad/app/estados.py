"""Máquina de estados global del juego: menú, pantallas de arranque de la
noche, jugando, game over y noche superada."""

from enum import Enum, auto


class EstadoJuego(Enum):
    MENU = auto()
    # Antes de jugar: el recorte del periódico (solo en partida nueva) y la
    # tarjeta con la noche y las 12:00 am. Ver presentacion/inicio_noche.py.
    PERIODICO = auto()
    TARJETA_NOCHE = auto()
    JUGANDO = auto()
    PAUSA = auto()  # la noche se congela mientras se muestra el menú de pausa
    SUSTO = auto()  # ráfaga de jumpscare tras perder, antes del game over
    GAME_OVER = auto()
    # Al ganar la noche: primero el reloj salta de 5:59 a 6:00 sin nada más
    # en pantalla, y enseguida el menú que pregunta si se continúa o se
    # vuelve al menú principal.
    NOCHE_SUPERADA_RELOJ = auto()
    NOCHE_SUPERADA_MENU = auto()


class GestorEstados:
    """Controla el estado activo del juego y expone consultas de conveniencia
    para el resto de los módulos."""

    def __init__(self):
        self.estado = EstadoJuego.MENU

    def cambiar_a(self, nuevo_estado: EstadoJuego):
        self.estado = nuevo_estado

    def en_menu(self) -> bool:
        return self.estado is EstadoJuego.MENU

    def en_periodico(self) -> bool:
        return self.estado is EstadoJuego.PERIODICO

    def en_tarjeta_noche(self) -> bool:
        return self.estado is EstadoJuego.TARJETA_NOCHE

    def jugando(self) -> bool:
        return self.estado is EstadoJuego.JUGANDO

    def en_pausa(self) -> bool:
        return self.estado is EstadoJuego.PAUSA

    def en_susto(self) -> bool:
        return self.estado is EstadoJuego.SUSTO

    def termino_en_derrota(self) -> bool:
        return self.estado is EstadoJuego.GAME_OVER

    def en_reloj_victoria(self) -> bool:
        return self.estado is EstadoJuego.NOCHE_SUPERADA_RELOJ

    def en_menu_victoria(self) -> bool:
        return self.estado is EstadoJuego.NOCHE_SUPERADA_MENU
