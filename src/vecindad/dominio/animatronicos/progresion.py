"""Dificultad por noche: quién sale, cada cuánto se mueven y desde qué hora.

Es el archivo que se toca para equilibrar la campaña; el comportamiento de
cada personaje no cambia, solo su ritmo y su nivel.

Cómo se reparte la dificultad
-----------------------------
Hay tres palancas y **se multiplican entre sí**, así que conviene mover una
sola a la vez:

1. `INTERVALO_POR_NOCHE`: cada cuántos segundos se abre una ronda de
   movimiento. Es la palanca principal y la que se nota como "ritmo".
2. `NIVELES_POR_NOCHE`: la probabilidad de dar un paso en cada ronda. Sirve
   sobre todo para igualar recorridos de largos muy distintos.
3. Cuántos personajes salen esa noche, que va de 3 a 7.

Con estos valores, las veces que el jugador tiene que reaccionar en una
noche entera quedan así:

    Noche 1:  1,9 llegadas (una cada ~190 s)   Noche 4: 11,1 (cada ~49 s)
    Noche 2:  4,4 llegadas (una cada ~122 s)   Noche 5: 17,3 (cada ~31 s)
    Noche 3:  6,6 llegadas (una cada  ~82 s)   Noche 6: 26,3 (cada ~20 s)

Esa curva no se calcula: se mide simulando noches completas, porque con
recorridos en grafo la distancia hasta el jugador depende de por dónde salga
cada uno. Al tocar cualquiera de las tres palancas hay que volver a medirla
(tests/test_animatronicos.py, sección "Medición del ritmo real de cada
noche"), y las pruebas fallan si alguien deja de llegar o si una noche deja
de apretar más que la anterior.
"""

from typing import Dict, List

from ...config.partida import (
    HORA_INICIO_NOCHE,
    INTERVALO_MOVIMIENTO_POR_DEFECTO,
    NIVEL_IA_MINIMO,
)
from . import nombres
from .elenco import ELENCO
from .entidad import Animatronic

# Hora de la noche a partir de la cual el elenco empieza a moverse. En la
# noche 1 nadie se mueve hasta las 2 AM, para que el jugador tenga tiempo de
# hacerse a los controles. Las noches que no aparezcan arrancan a las 12.
HORA_ARRANQUE_POR_NOCHE: Dict[int, int] = {1: 2}

# Segundos reales entre rondas de movimiento en cada noche. En la noche 1 el
# elenco decide si cambia de cámara cada 20 segundos; en la 6, cada 8.
#
# Ojo con leerlo como "cada cuánto llega alguien": una ronda es un paso, no
# una llegada. Don Ramón necesita 3,3 pasos de media para plantarse delante
# del jugador, pero La Chilindrina necesita 13,3, porque su recorrido da
# vueltas y puede devolverse. Por eso los intervalos son bastante más cortos
# que el paso que se quiere sentir.
INTERVALO_POR_NOCHE: Dict[int, float] = {
    1: 20.0,
    2: 17.0,
    3: 14.0,
    4: 12.0,
    5: 10.0,
    6: 8.0,
}

# Nivel de IA de cada personaje en cada noche de la campaña.
#
# No se lee como "quién da más miedo": el nivel compensa lo largo que sea el
# recorrido. La Chilindrina va muy alta (11-13) porque su vuelta por las casas
# le cuesta 13 movimientos de media, y Don Ramón muy bajo (3-6) porque se
# planta en 3. Con el mismo nivel, ella no llegaría nunca y él llegaría sin
# parar. Quien manda en la sensación de dificultad es el intervalo.
#
# Los números salen de simular la noche entera, no de una fórmula: con grafos
# la distancia hasta el jugador depende de por dónde salga cada uno. Al tocar
# cualquier cosa hay que volver a medir (tests/test_animatronicos.py, sección
# "Medición del ritmo real de cada noche").
NIVELES_POR_NOCHE: Dict[int, Dict[str, int]] = {
    1: {nombres.DON_RAMON: 3, nombres.QUICO: 3, nombres.CHILINDRINA: 11},
    2: {
        nombres.DON_RAMON: 3, nombres.QUICO: 3, nombres.CHILINDRINA: 11,
        nombres.FLORINDA: 4,
    },
    3: {
        nombres.DON_RAMON: 3, nombres.QUICO: 3, nombres.CHILINDRINA: 11,
        nombres.FLORINDA: 5, nombres.CLOTILDE: 6, nombres.CHAVO: 7,
    },
    4: {
        nombres.DON_RAMON: 4, nombres.QUICO: 4, nombres.CHILINDRINA: 11,
        nombres.FLORINDA: 5, nombres.CLOTILDE: 7, nombres.CHAVO: 7,
        nombres.JAIMICO: 2,
    },
    5: {
        nombres.DON_RAMON: 5, nombres.QUICO: 5, nombres.CHILINDRINA: 12,
        nombres.FLORINDA: 6, nombres.CLOTILDE: 9, nombres.CHAVO: 8,
        nombres.JAIMICO: 3,
    },
    6: {
        nombres.DON_RAMON: 6, nombres.QUICO: 6, nombres.CHILINDRINA: 13,
        nombres.FLORINDA: 7, nombres.CLOTILDE: 11, nombres.CHAVO: 10,
        nombres.JAIMICO: 4,
    },
}


def hora_de_arranque(numero_noche: int) -> int:
    """Horas de noche que deben pasar antes de que el elenco se mueva."""
    return HORA_ARRANQUE_POR_NOCHE.get(numero_noche, HORA_INICIO_NOCHE)


def intervalo_de_movimiento(numero_noche: int) -> float:
    """Segundos entre rondas de movimiento en esa noche. Las noches fuera de
    la campaña (la personalizada) usan el ritmo por defecto."""
    return INTERVALO_POR_NOCHE.get(numero_noche, INTERVALO_MOVIMIENTO_POR_DEFECTO)


def niveles_iniciales_personalizada() -> Dict[str, int]:
    """Todos los personajes en 0, como arranca cualquier noche personalizada
    antes de que el jugador suba a alguien."""
    return {config.nombre: NIVEL_IA_MINIMO for config in ELENCO}


def crear_elenco_noche(numero_noche: int) -> List[Animatronic]:
    """Crea el elenco de una noche de la campaña. Los personajes que no
    aparecen en la tabla de esa noche quedan en nivel 0 (inactivos)."""
    niveles = NIVELES_POR_NOCHE.get(numero_noche, {})
    return crear_elenco_personalizado(niveles)


def crear_elenco_personalizado(niveles: Dict[str, int]) -> List[Animatronic]:
    """Crea el elenco con el nivel de IA elegido para cada personaje."""
    return [
        Animatronic(config, niveles.get(config.nombre, NIVEL_IA_MINIMO))
        for config in ELENCO
    ]
