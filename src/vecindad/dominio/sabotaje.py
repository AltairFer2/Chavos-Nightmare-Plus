"""El Chavo arruina las cámaras si se le observa demasiado rato.

La presión sube mientras se le tiene en pantalla y baja despacio en cuanto
se cambia de vista. El umbral es corto (uno o dos segundos según la noche) y
el enfriamiento lento, así que no basta con quitarle la vista al verlo:
volver a su cámara una y otra vez también suma. Una vez averiadas, solo se
arreglan con un servicio del barril.

Es una regla de juego y no de dibujo, de ahí que viva en el dominio: el panel
de cámaras se limita a decirle si el saboteador está a la vista.
"""

from ..config.jugabilidad import (
    CAMARA_SABOTAJE_AVISO,
    CAMARA_SABOTAJE_POR_NOCHE,
    CAMARA_SABOTAJE_RECUPERACION,
    CAMARA_SABOTAJE_SEGUNDOS,
)


def aguante_de_la_noche(numero_noche: int) -> float:
    """Segundos de observación que aguanta El Chavo esa noche antes de
    arruinar las cámaras."""
    return CAMARA_SABOTAJE_POR_NOCHE.get(numero_noche, CAMARA_SABOTAJE_SEGUNDOS)


class ControlSabotaje:
    """Cuánto lleva el jugador observando al saboteador y si ya rompió las
    cámaras."""

    def __init__(self, numero_noche: int = 1):
        self.aguante = aguante_de_la_noche(numero_noche)
        self.averiadas = False
        self.presion = 0.0

    @property
    def proporcion(self) -> float:
        """Qué tanto de la presión aguantable lleva acumulada, de 0 a 1."""
        return self.presion / self.aguante

    @property
    def a_punto(self) -> bool:
        """Si ya está cerca de romperlas: el monitor lo deja ver fallando."""
        return not self.averiadas and self.proporcion >= CAMARA_SABOTAJE_AVISO

    def actualizar(self, dt: float, observado: bool):
        """`observado` es si el saboteador está en la cámara que se está
        mirando ahora mismo."""
        if self.averiadas:
            return
        if observado:
            self.presion += dt
            if self.presion >= self.aguante:
                self.averiadas = True
                self.presion = self.aguante
            return
        self.presion = max(0.0, self.presion - dt * CAMARA_SABOTAJE_RECUPERACION)

    def reparar(self):
        self.averiadas = False
        self.presion = 0.0
