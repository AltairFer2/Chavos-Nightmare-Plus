"""Temporizador de la noche: lleva la hora mostrada en pantalla (12am-6am) y
abre las rondas de movimiento de los animatrónicos.

Cada `intervalo_movimiento` segundos reales se abre una ronda: todos los
animatrónicos tiran su dado de nivel_ia a la vez. El temporizador es quien
marca ese compás, para que todos avancen sobre la misma base de tiempo.

El intervalo lo fija cada noche (ver dominio/animatronicos/progresion.py): es
la palanca de ritmo de la campaña, y por eso no es una constante global sino
un dato de cada partida.
"""

from ..config.partida import (
    DURACION_NOCHE_SEGUNDOS,
    HORA_FIN_NOCHE,
    HORA_INICIO_NOCHE,
    HORAS_DE_NOCHE,
    INTERVALO_MOVIMIENTO_POR_DEFECTO,
)


class TemporizadorNoche:
    """Avanza el reloj de la noche y abre las rondas de movimiento."""

    def __init__(self, intervalo_movimiento: float = INTERVALO_MOVIMIENTO_POR_DEFECTO):
        self.intervalo_movimiento = self._sanear(intervalo_movimiento)
        self.segundos_transcurridos = 0.0
        self.noche_terminada = False
        self._tiempo_para_siguiente_ronda = self.intervalo_movimiento

    @staticmethod
    def _sanear(intervalo: float) -> float:
        """Un intervalo de cero o negativo dispararía rondas infinitas dentro
        del bucle de actualización y colgaría el juego."""
        if intervalo <= 0.0:
            return INTERVALO_MOVIMIENTO_POR_DEFECTO
        return float(intervalo)

    def actualizar(self, dt: float, animatronics=()):
        """Avanza el reloj y, cada vez que se cumple una ronda, llama a
        actualizar() en cada animatrónico recibido.

        La lista entera se le pasa a cada uno porque hay recorridos que
        dependen de dónde esté otro: Doña Clotilde no se mueve del Segundo
        Patio hasta que Don Ramón llegue a donde ella necesita."""
        if self.noche_terminada:
            return

        self.segundos_transcurridos += dt

        self._tiempo_para_siguiente_ronda -= dt
        while self._tiempo_para_siguiente_ronda <= 0.0:
            self._tiempo_para_siguiente_ronda += self.intervalo_movimiento
            for animatronic in animatronics:
                animatronic.actualizar(animatronics)

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

    def reiniciar(self, intervalo_movimiento: float = None):
        """Deja el reloj a las 12. Si se pasa un intervalo, la noche que
        arranca usa ese ritmo; si no, conserva el que ya tenía."""
        if intervalo_movimiento is not None:
            self.intervalo_movimiento = self._sanear(intervalo_movimiento)
        self.segundos_transcurridos = 0.0
        self.noche_terminada = False
        self._tiempo_para_siguiente_ronda = self.intervalo_movimiento
