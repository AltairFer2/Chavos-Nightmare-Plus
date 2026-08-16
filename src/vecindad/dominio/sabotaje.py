"""El Chavo arruina las cámaras si se le observa demasiado rato seguido.

La presión sube mientras se le tiene en pantalla y baja sola en cuanto se
cambia de vista, así que mirarlo un momento es gratis y quedarse pegado a su
cámara no. Una vez averiadas, solo se arreglan con un servicio del barril.

Es una regla de juego y no de dibujo, de ahí que viva en el dominio: el panel
de cámaras se limita a decirle si el saboteador está a la vista.
"""

from ..config.jugabilidad import (
    CAMARA_SABOTAJE_RECUPERACION,
    CAMARA_SABOTAJE_SEGUNDOS,
)


class ControlSabotaje:
    """Cuánto lleva el jugador observando al saboteador y si ya rompió las
    cámaras."""

    def __init__(self):
        self.averiadas = False
        self.presion = 0.0

    def actualizar(self, dt: float, observado: bool):
        """`observado` es si el saboteador está en la cámara que se está
        mirando ahora mismo."""
        if self.averiadas:
            return
        if observado:
            self.presion += dt
            if self.presion >= CAMARA_SABOTAJE_SEGUNDOS:
                self.averiadas = True
                self.presion = CAMARA_SABOTAJE_SEGUNDOS
            return
        self.presion = max(0.0, self.presion - dt * CAMARA_SABOTAJE_RECUPERACION)

    def reparar(self):
        self.averiadas = False
        self.presion = 0.0
