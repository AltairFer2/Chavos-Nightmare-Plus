"""Animatrónicos: personajes que se desplazan por el grafo de habitaciones
hacia el Primer Patio, donde se encuentra el jugador."""

import random
from dataclasses import dataclass
from typing import Dict, List

from constants import DIFICULTAD_MAXIMA, DIFICULTAD_MINIMA
from habitaciones import HABITACION_JUGADOR, obtener_habitacion


@dataclass
class ConfiguracionAnimatronic:
    nombre: str
    habitacion_inicial: str
    dificultad: int  # 1 (lento/predecible) a 5 (agresivo)
    intervalo_movimiento_min: float = 8.0
    intervalo_movimiento_max: float = 20.0


class Animatronic:
    """Controla la posición y el movimiento de un animatrónico dentro del
    grafo de habitaciones. Cada cierto intervalo (en segundos) intenta
    avanzar una habitación; la probabilidad de dirigirse directamente hacia
    el jugador, cuando es posible, aumenta con la dificultad."""

    def __init__(self, configuracion: ConfiguracionAnimatronic):
        self.nombre = configuracion.nombre
        self.dificultad = configuracion.dificultad
        self._intervalo_min = configuracion.intervalo_movimiento_min
        self._intervalo_max = configuracion.intervalo_movimiento_max
        self.habitacion_actual = configuracion.habitacion_inicial
        self.activo = True
        self._tiempo_para_moverse = self._nuevo_intervalo()

    def _nuevo_intervalo(self) -> float:
        factor = max(0.3, 1.0 - (self.dificultad - 1) * 0.15)
        return random.uniform(self._intervalo_min, self._intervalo_max) * factor

    def actualizar(self, dt: float):
        if not self.activo or self.alcanzo_al_jugador():
            return
        self._tiempo_para_moverse -= dt
        if self._tiempo_para_moverse <= 0:
            self._moverse()
            self._tiempo_para_moverse = self._nuevo_intervalo()

    def _moverse(self):
        conexiones = obtener_habitacion(self.habitacion_actual).conexiones
        probabilidad_avance = 0.5 + self.dificultad * 0.08
        if HABITACION_JUGADOR in conexiones and random.random() < probabilidad_avance:
            self.habitacion_actual = HABITACION_JUGADOR
        else:
            self.habitacion_actual = random.choice(conexiones)

    def alcanzo_al_jugador(self) -> bool:
        return self.habitacion_actual == HABITACION_JUGADOR

    def reiniciar(self, habitacion_inicial: str):
        self.habitacion_actual = habitacion_inicial
        self.activo = True
        self._tiempo_para_moverse = self._nuevo_intervalo()


# Elenco de ejemplo para la noche: cada personaje inicia en su propia casa
# dentro del mapa de 11 cámaras. Es un punto de partida para probar el
# sistema de movimiento; el elenco final (personajes, casa de origen y
# dificultad) queda a definir junto con el resto del diseño de niveles.
ELENCO_BASE: List[ConfiguracionAnimatronic] = [
    ConfiguracionAnimatronic("Don Ramón", "casa_ramon", dificultad=2),
    ConfiguracionAnimatronic("Doña Clotilde", "casa_clotilde", dificultad=2),
    ConfiguracionAnimatronic("Godínez", "casa_godinez", dificultad=1),
    ConfiguracionAnimatronic("Paty", "casa_paty", dificultad=1),
]


def _limitar_dificultad(nivel: int) -> int:
    return max(DIFICULTAD_MINIMA, min(DIFICULTAD_MAXIMA, nivel))


def _instanciar(config: ConfiguracionAnimatronic, dificultad: int) -> Animatronic:
    return Animatronic(
        ConfiguracionAnimatronic(
            nombre=config.nombre,
            habitacion_inicial=config.habitacion_inicial,
            dificultad=_limitar_dificultad(dificultad),
            intervalo_movimiento_min=config.intervalo_movimiento_min,
            intervalo_movimiento_max=config.intervalo_movimiento_max,
        )
    )


def crear_elenco_noche(numero_noche: int = 1) -> List[Animatronic]:
    """Crea el elenco de una noche de la campaña: cada personaje parte de su
    dificultad base y sube un nivel por cada noche superada."""
    return [_instanciar(config, config.dificultad + numero_noche - 1) for config in ELENCO_BASE]


def crear_elenco_personalizado(dificultades: Dict[str, int]) -> List[Animatronic]:
    """Crea el elenco de la Noche Personalizada con el nivel elegido por el
    jugador para cada personaje. Los que no aparezcan en el diccionario
    conservan su dificultad base."""
    return [
        _instanciar(config, dificultades.get(config.nombre, config.dificultad))
        for config in ELENCO_BASE
    ]
