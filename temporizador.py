"""Temporizador de la noche: lleva la hora mostrada en pantalla (12am-6am) y
dispara los ticks de inteligencia artificial de los animatrónicos.

El tiempo real se convierte en horas in-game y cada hora se divide en
TICKS_POR_HORA intentos de movimiento. En cada tick, todos los animatrónicos
tiran su dado de nivel_ia; el temporizador es quien marca el compás para que
todos avancen sobre la misma base de tiempo.
"""

from constants import (
    DURACION_NOCHE_SEGUNDOS,
    HORA_FIN_NOCHE,
    HORA_INICIO_NOCHE,
    HORAS_DE_NOCHE,
    SEGUNDOS_POR_TICK,
)


class TemporizadorNoche:
    """Avanza el reloj de la noche y emite los ticks de la IA."""

    def __init__(self):
        self.segundos_transcurridos = 0.0
        self.noche_terminada = False
        self._tiempo_para_siguiente_tick = SEGUNDOS_POR_TICK

    def actualizar(self, dt: float, animatronics=()):
        """Avanza el reloj y, cada vez que se cumple un tick, llama a
        actualizar() en cada animatrónico recibido."""
        if self.noche_terminada:
            return

        self.segundos_transcurridos += dt

        self._tiempo_para_siguiente_tick -= dt
        while self._tiempo_para_siguiente_tick <= 0.0:
            self._tiempo_para_siguiente_tick += SEGUNDOS_POR_TICK
            for animatronic in animatronics:
                animatronic.actualizar()

        if self.segundos_transcurridos >= DURACION_NOCHE_SEGUNDOS:
            self.noche_terminada = True

    def horas_transcurridas(self) -> int:
        """Horas enteras de noche que ya pasaron, de 0 (12 am) a HORAS_DE_NOCHE.
        Es la medida útil para comparar contra una hora concreta; hora_actual()
        es solo para mostrar."""
        return min(HORAS_DE_NOCHE, int(self.progreso() * HORAS_DE_NOCHE))

    def hora_actual(self) -> int:
        """Hora entera mostrada en el HUD (12, 1, 2... hasta HORA_FIN_NOCHE)."""
        hora = min(HORA_INICIO_NOCHE + self.horas_transcurridas(), HORA_FIN_NOCHE)
        return 12 if hora == 0 else hora

    def progreso(self) -> float:
        """Avance de la noche, de 0.0 (12am) a 1.0 (6am)."""
        return min(1.0, self.segundos_transcurridos / DURACION_NOCHE_SEGUNDOS)

    def reiniciar(self):
        self.segundos_transcurridos = 0.0
        self.noche_terminada = False
        self._tiempo_para_siguiente_tick = SEGUNDOS_POR_TICK
