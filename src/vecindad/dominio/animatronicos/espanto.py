"""Espantar con la luz: la linterna como arma.

A quien se espanta con la luz (todos menos Don Ramón y Doña Florinda) se le
ve, mientras acecha, un punto débil que se mueve a tirones por su cuerpo.
Para quitárselo de encima hay que sostener el centro del haz (el cursor)
sobre ese punto hasta llenar su barra. Perderlo no la reinicia, pero la va
vaciando, así que lo que se juega es el pulso: seguir un blanco que cambia
de dirección sin avisar.

Cuanto más nivel de IA, más chico y más rápido es el punto, más seguido
cambia de rumbo y más rato hay que sostenerlo (ver Animatronic).

La Chilindrina añade un castigo: alumbrarle el cuerpo fuera del punto más de
CHILINDRINA_GRACIA_SEGUNDOS seguidos le descarga la batería al jugador.

Mientras dura el espanto la linterna sigue gastando batería, y alumbrar a
alguien lo sigue activando (ya no respeta el barril): empezar a espantarlo y
esconderse a medias no es una salida.

El punto se mueve al azar, pero eso no decide nada por sí solo: es un blanco
móvil, y alcanzarlo depende del pulso del jugador. `azar` permite fijar la
semilla en las pruebas.
"""

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from ...config.jugabilidad import (
    CHILINDRINA_GRACIA_SEGUNDOS,
    PUNTO_DEBIL_DRENADO,
    PUNTO_DEBIL_SEMIALTO,
    PUNTO_DEBIL_SEMIANCHO,
)
from .enfrentamiento import acechando_en
from .entidad import Animatronic


@dataclass
class PuntoDebil:
    """El punto débil de un personaje mientras acecha, y lo que lleva
    sostenido. Las coordenadas son relativas a su torso, en píxeles: así
    valen igual desde el Barril que desde los Lavaderos."""

    desplazamiento: Tuple[float, float] = (0.0, 0.0)
    destino: Tuple[float, float] = (0.0, 0.0)
    para_cambiar: float = 0.0
    progreso: float = 0.0  # de 0 a 1; al llegar a 1 se espanta
    # Segundos seguidos alumbrándole el cuerpo fuera del punto. Solo cuenta
    # para quien castiga fallar (La Chilindrina).
    fuera_del_punto: float = 0.0


@dataclass
class ResultadoEspanto:
    """Lo que pasó en un fotograma: a quién se espantó y si hay que
    descargarle la batería al jugador."""

    espantados: List[Animatronic] = field(default_factory=list)
    descarga: bool = False


def se_espanta(animatronic) -> bool:
    return animatronic.configuracion.se_espanta_con_luz


class Espanto:
    """Los puntos débiles de quienes acechan y cuánto lleva cada uno."""

    def __init__(self, azar: Optional[random.Random] = None):
        self._azar = azar if azar is not None else random.Random()
        self._puntos: Dict[str, PuntoDebil] = {}

    def reiniciar(self):
        self._puntos.clear()

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------
    def punto_de(self, animatronic, id_posicion: str) -> Optional[Tuple[int, int]]:
        """Dónde está su punto débil en el lienzo, visto desde esa posición,
        o None si no tiene (no acecha, o no se espanta con la luz)."""
        punto = self._puntos.get(animatronic.nombre)
        torso = animatronic.punto_torso_en(id_posicion)
        if punto is None or torso is None:
            return None
        dx, dy = punto.desplazamiento
        return (round(torso[0] + dx), round(torso[1] + dy))

    def progreso_de(self, animatronic) -> float:
        punto = self._puntos.get(animatronic.nombre)
        return punto.progreso if punto is not None else 0.0

    # ------------------------------------------------------------------
    # Paso del tiempo
    # ------------------------------------------------------------------
    def actualizar(self, dt: float, animatronics, id_posicion: str, punto_luz,
                   alumbrando: bool) -> ResultadoEspanto:
        """Mueve los puntos y suma o resta lo sostenido.

        `alumbrando` es si el haz llega de verdad al patio: linterna
        encendida, fuera del barril y sin un panel delante. A quien se
        espanta se lo saca de encima aquí mismo (ahuyentar)."""
        presentes = [a for a in acechando_en(animatronics, id_posicion) if se_espanta(a)]
        self._olvidar_a_los_que_se_fueron(presentes)

        resultado = ResultadoEspanto()
        for animatronic in presentes:
            punto = self._puntos.get(animatronic.nombre)
            if punto is None:
                punto = self._puntos[animatronic.nombre] = self._nuevo_punto()
            self._mover(punto, animatronic, dt)
            if self._sostener(punto, animatronic, dt, id_posicion, punto_luz,
                              alumbrando, resultado):
                animatronic.ahuyentar()
                del self._puntos[animatronic.nombre]
                resultado.espantados.append(animatronic)
        return resultado

    def _olvidar_a_los_que_se_fueron(self, presentes):
        """Quien ya no está delante (o el jugador ya no lo ve) pierde lo
        sostenido: al volver se empieza de cero."""
        nombres = {animatronic.nombre for animatronic in presentes}
        for nombre in list(self._puntos):
            if nombre not in nombres:
                del self._puntos[nombre]

    def _punto_al_azar(self) -> Tuple[float, float]:
        """Un punto cualquiera de la elipse del cuerpo, repartido parejo."""
        angulo = self._azar.uniform(0.0, 2.0 * math.pi)
        radio = math.sqrt(self._azar.random())
        return (
            radio * math.cos(angulo) * PUNTO_DEBIL_SEMIANCHO,
            radio * math.sin(angulo) * PUNTO_DEBIL_SEMIALTO,
        )

    def _nuevo_punto(self) -> PuntoDebil:
        return PuntoDebil(desplazamiento=self._punto_al_azar())

    def _mover(self, punto: PuntoDebil, animatronic, dt: float):
        """Corre hacia su destino a velocidad fija y, cada tanto, cambia de
        destino: son esos cambios de rumbo los que hay que leer."""
        punto.para_cambiar -= dt
        if punto.para_cambiar <= 0.0:
            punto.destino = self._punto_al_azar()
            punto.para_cambiar = self._azar.uniform(*animatronic.cambio_punto_debil())
        x, y = punto.desplazamiento
        destino_x, destino_y = punto.destino
        distancia = math.hypot(destino_x - x, destino_y - y)
        paso = animatronic.velocidad_punto_debil() * dt
        if distancia <= paso:
            punto.desplazamiento = punto.destino
            return
        avance = paso / distancia
        punto.desplazamiento = (x + (destino_x - x) * avance, y + (destino_y - y) * avance)

    def _sostener(self, punto: PuntoDebil, animatronic, dt: float, id_posicion: str,
                  punto_luz, alumbrando: bool, resultado: ResultadoEspanto) -> bool:
        """Suma si el centro del haz está encima del punto y resta si no.
        Devuelve True cuando la barra se llena."""
        if not alumbrando or punto_luz is None:
            self._perder(punto, dt)
            punto.fuera_del_punto = 0.0
            return False

        centro = self.punto_de(animatronic, id_posicion)
        radio = animatronic.radio_punto_debil()
        if _distancia2(punto_luz, centro) <= radio * radio:
            punto.progreso += dt / animatronic.segundos_para_espantar()
            punto.fuera_del_punto = 0.0
            return punto.progreso >= 1.0

        self._perder(punto, dt)
        if self._castiga_fallar(animatronic, id_posicion, punto_luz):
            punto.fuera_del_punto += dt
            if punto.fuera_del_punto >= CHILINDRINA_GRACIA_SEGUNDOS:
                punto.fuera_del_punto = 0.0
                resultado.descarga = True
        else:
            punto.fuera_del_punto = 0.0
        return False

    @staticmethod
    def _perder(punto: PuntoDebil, dt: float):
        punto.progreso = max(0.0, punto.progreso - PUNTO_DEBIL_DRENADO * dt)

    @staticmethod
    def _castiga_fallar(animatronic, id_posicion: str, punto_luz) -> bool:
        """Si el haz le está dando en el cuerpo a quien no perdona fallar:
        dentro de su radio de reacción a la luz, alrededor del torso."""
        if not animatronic.configuracion.luz_descarga_linterna:
            return False
        radio = animatronic.radio_peligro()
        torso = animatronic.punto_torso_en(id_posicion)
        return torso is not None and _distancia2(punto_luz, torso) <= radio * radio


def _distancia2(a, b) -> float:
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2
