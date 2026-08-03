"""Temporizador de la noche: controla la hora mostrada en pantalla
(12am-6am) y el consumo de energía disponible para operar las cámaras."""

from constants import (
    CONSUMO_ENERGIA_POR_SEGUNDO,
    CONSUMO_EXTRA_CAMARAS_POR_SEGUNDO,
    DURACION_NOCHE_SEGUNDOS,
    ENERGIA_MAXIMA,
    HORA_FIN_NOCHE,
    HORA_INICIO_NOCHE,
)


class Temporizador:
    """Lleva el paso del tiempo de la noche y el nivel de energía."""

    def __init__(self):
        self.segundos_transcurridos = 0.0
        self.energia = ENERGIA_MAXIMA
        self.noche_terminada = False
        self.sin_energia = False

    def actualizar(self, dt: float, camaras_activas: bool):
        if self.noche_terminada:
            return

        self.segundos_transcurridos += dt

        if not self.sin_energia:
            consumo = CONSUMO_ENERGIA_POR_SEGUNDO
            if camaras_activas:
                consumo += CONSUMO_EXTRA_CAMARAS_POR_SEGUNDO
            self.energia = max(0.0, self.energia - consumo * dt)
            if self.energia <= 0.0:
                self.sin_energia = True

        if self.segundos_transcurridos >= DURACION_NOCHE_SEGUNDOS:
            self.noche_terminada = True

    def hora_actual(self) -> int:
        """Hora entera mostrada en el HUD (12, 1, 2... hasta HORA_FIN_NOCHE)."""
        progreso = min(1.0, self.segundos_transcurridos / DURACION_NOCHE_SEGUNDOS)
        rango_horas = (HORA_FIN_NOCHE - HORA_INICIO_NOCHE) % 12 or 12
        hora = HORA_INICIO_NOCHE + int(progreso * rango_horas)
        return 12 if hora == 0 else hora

    def porcentaje_energia(self) -> float:
        return self.energia / ENERGIA_MAXIMA

    def reiniciar(self):
        self.segundos_transcurridos = 0.0
        self.energia = ENERGIA_MAXIMA
        self.noche_terminada = False
        self.sin_energia = False
