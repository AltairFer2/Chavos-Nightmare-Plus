"""Ficha de un personaje: los datos fijos que no cambian durante la noche.

Recorridos
----------
El recorrido de cada personaje es un **grafo dirigido**: `transiciones` dice,
para cada cámara donde puede estar, a cuáles puede pasar en su siguiente
movimiento. Al abrirse una ronda tira su dado de nivel_ia y, si le toca
avanzar, elige al azar uno de los destinos de la cámara en la que está.

No es un camino lineal: hay rutas que se devuelven (La Chilindrina vuelve del
Segundo Patio a casa de Don Ramón), callejones sin salida (Don Ramón entra a
casa de la bruja y tiene que regresar) y ciclos completos. Por eso la
distancia hasta el jugador no es fija: depende de por dónde haya salido.

Llegar al Primer Patio (HABITACION_JUGADOR) es lo que cuenta como acechar. De
ahí no se sale tirando el dado: solo se sale por la contramedida que le
corresponde a cada uno, y `transiciones[HABITACION_JUGADOR]` dice a dónde va
cuando esa contramedida funciona.

El recorrido es autoral y no se deriva de las conexiones del grafo de
habitaciones: describe el camino que hace el personaje, no la geometría de
la vecindad (que sigue documentada en mundo/habitaciones.py).

Pasos condicionados
-------------------
`condiciones_de_paso` bloquea aristas concretas hasta que otro personaje esté
en cierta cámara. Solo lo usa Doña Clotilde, que desde el Segundo Patio no se
mueve a ningún lado mientras Don Ramón no esté donde ella necesita.

Retrocesos y audio
------------------
`retrocesos` son pasos hacia atrás que su recorrido no trae de ida (del
Segundo Patio a la casa de los Godínez, por ejemplo). Solo los usa Doña
Florinda: junto con su recorrido forman el mapa de cámaras vecinas por el
que la mueve el audio de Quico (ver Animatronic.atraer_a). `sorda_en` son
las cámaras desde las que el audio ya no le hace efecto.
"""

from dataclasses import dataclass, field
from typing import Mapping, Tuple

from ...config.rutas import DIR_ASSETS_ANIMATRONICS

# Cámaras a las que se puede pasar desde una dada.
Destinos = Tuple[str, ...]

# Qué personaje tiene que estar en qué cámara para que una arista se abra.
Condicion = Tuple[str, str]

# Poses de acercamiento que tiene cada personaje: 1 quieto, 2 encorvado y
# 3 lanzado. Al llegar al Primer Patio se elige una al azar y se queda con
# ella mientras acecha, para que no se le vea siempre igual.
POSES_POR_PERSONAJE = 3


@dataclass(frozen=True)
class ConfiguracionAnimatronic:
    """Datos fijos de un personaje: por dónde va, dónde acecha, con qué arte
    se dibuja y cómo reacciona el jugador ante él. El nivel_ia no vive aquí
    porque cambia en cada noche y en la Noche Personalizada."""

    nombre: str
    habitacion_inicial: str  # dónde empieza la noche
    transiciones: Mapping[str, Destinos]
    # Dónde pisa el personaje en cada sitio desde el que el jugador puede
    # mirarlo. El Barril y los Lavaderos son dos ángulos del mismo patio, así
    # que quien llega a la cámara 1 se ve desde los dos: lo que cambia es en
    # qué punto del lienzo cae según desde dónde se le mire.
    puntos_acecho: Mapping[str, Tuple[int, int]]
    espera_ataque_lenta: float  # segundos de margen con nivel_ia 1
    espera_ataque_rapida: float  # segundos de margen con nivel_ia 20
    # Aristas que solo se abren si otro personaje está en cierta cámara.
    condiciones_de_paso: Mapping[Tuple[str, str], Condicion] = field(default_factory=dict)
    # Pasos hacia atrás que el recorrido no trae de ida; cuentan como
    # cámaras vecinas para el audio de Quico.
    retrocesos: Mapping[str, Destinos] = field(default_factory=dict)
    # Cámaras desde las que el audio de Quico ya no la mueve.
    sorda_en: Tuple[str, ...] = ()
    # Arte: assets/animatronics/<carpeta>/<prefijo> <n>.png. La carpeta y el
    # prefijo no siempre coinciden (bruja/clotilde, don ramon/ramon).
    carpeta_sprite: str = ""
    prefijo_sprite: str = ""
    luz_mortal: bool = False  # iluminarlo de cerca mata al instante
    # Se le quita de encima sosteniendo el haz sobre su punto débil (ver
    # dominio/espanto.py). Todos menos Don Ramón y Doña Florinda, que tienen
    # su propio servicio y a quienes la luz mata.
    se_espanta_con_luz: bool = False
    # La Chilindrina: alumbrarle el cuerpo fuera del punto débil más de un
    # momento se lleva la batería entera. No corta la noche ni avisa de nada:
    # el jugador se entera porque se queda a oscuras de golpe.
    luz_descarga_linterna: bool = False
    # Si puede acabar con el jugador mientras está metido en el barril. Solo
    # Don Ramón y Doña Florinda pueden desde que llegan: son los que rompen
    # el refugio y obligan a salir. Del resto se está a salvo escondido...
    # hasta que se les alumbre, porque eso los activa (ver Animatronic).
    alcanza_escondido: bool = False
    # Llegar al Primer Patio acaba la noche en el acto, sin margen de
    # reacción. Solo Doña Florinda. Tiene una consecuencia práctica: no hace
    # falta dibujarla en la cámara 1, porque para cuando estuviera ahí la
    # partida ya terminó y esa imagen no se vería nunca.
    llegada_mortal: bool = False

    def habitaciones(self) -> Tuple[str, ...]:
        """Todas las cámaras por las que puede pasar, en orden estable."""
        vistas = [self.habitacion_inicial]
        for origen, destinos in self.transiciones.items():
            for id_habitacion in (origen, *destinos):
                if id_habitacion not in vistas:
                    vistas.append(id_habitacion)
        return tuple(vistas)

    def ruta_pose(self, numero: int):
        return (
            DIR_ASSETS_ANIMATRONICS / self.carpeta_sprite
            / f"{self.prefijo_sprite} {numero}.png"
        )
