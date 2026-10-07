"""Objetos que hay que encontrar en las cámaras: la escoba de Doña Clotilde
y el café de Jaimico.

En cuanto uno de los dos aparece en su cámara, su objeto queda escondido en
alguna cámara al azar (nunca en la del Chavo, que solo tiene micrófono) y
empieza a correr el tiempo. Mientras corre, el juego avisa como si hubiera
alguien en el patio, aunque no haya nadie: hay que levantar el monitor e ir
cámara por cámara hasta dar con el objeto y hacerle clic.

- Encontrarlo a tiempo: el personaje desaparece (y puede volver a aparecer).
- Si se acaba el tiempo: Doña Clotilde mata en el acto; Jaimico se planta
  en el Primer Patio y hay que espantarlo con la linterna.

Cuánto tiempo hay: para Doña Clotilde depende de lo lejos del patio que haya
aparecido (BUSQUEDA_SEGUNDOS_*); para Jaimico, de su nivel
(busqueda_segundos en su ficha).

Es una regla de juego y no sabe nada de pygame: los sitios donde puede quedar
el objeto son puntos del monitor (config/jugabilidad.py) y el clic llega ya
traducido a esas coordenadas.
"""

import random
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

from ..config.jugabilidad import (
    BUSQUEDA_SEGUNDOS_MINIMOS,
    BUSQUEDA_SEGUNDOS_POR_PASO,
    OBJETO_BUSCADO_RADIO_CLIC,
    SITIOS_OBJETOS_BUSCADOS,
)
from ..mundo.habitaciones import HABITACIONES, distancia_al_jugador

# Dónde puede quedar escondido un objeto: cualquier cámara con imagen. La
# del Chavo (8) solo tiene micrófono, así que ahí no se vería nunca.
CAMARAS_CON_OBJETOS: Tuple[str, ...] = tuple(
    id_habitacion for id_habitacion, habitacion in HABITACIONES.items()
    if not habitacion.solo_audio
)


class Desenlace(Enum):
    """Qué pasa cuando se acaba el tiempo de una búsqueda."""

    MATA = "mata"          # Doña Clotilde: la noche termina ahí
    IRRUMPE = "irrumpe"    # Jaimico: se planta en el Primer Patio


@dataclass
class Busqueda:
    """El objeto de un personaje, escondido, y lo que queda para encontrarlo."""

    nombre: str
    id_objeto: str
    camara: str
    punto: Tuple[int, int]
    segundos_totales: float
    segundos_restantes: float

    @property
    def inminencia(self) -> float:
        """0.0 al esconderse y 1.0 al acabarse el tiempo."""
        if self.segundos_totales <= 0.0:
            return 1.0
        return max(0.0, min(1.0, 1.0 - self.segundos_restantes / self.segundos_totales))


@dataclass
class ResultadoBusquedas:
    """Lo que cambió en un fotograma: quién acaba de esconder su objeto (su
    aparición suena como si llegara alguien al patio) y a quién se le acabó
    el tiempo."""

    empezadas: List[object]
    agotadas: List[Tuple[object, Desenlace]]


def segundos_para_buscar(animatronic) -> float:
    """El tiempo que hay para encontrar su objeto, según dónde está ahora."""
    config = animatronic.configuracion
    if config.busqueda_por_distancia:
        pasos_de_mas = max(0, distancia_al_jugador(animatronic.habitacion_actual) - 1)
        return BUSQUEDA_SEGUNDOS_MINIMOS + BUSQUEDA_SEGUNDOS_POR_PASO * pasos_de_mas
    return animatronic.segun_ia(config.busqueda_segundos)


def _esperando_a_que_lo_encuentren(animatronic) -> bool:
    """En una cámara que no es el patio: ahí es donde su objeto cuenta."""
    return (
        animatronic.activo
        and bool(animatronic.configuracion.objeto_buscado)
        and animatronic.presente
        and not animatronic.esta_acechando()
    )


class BusquedasEnCamaras:
    """Las búsquedas en marcha, una por personaje como mucho."""

    def __init__(self, azar: Optional[random.Random] = None):
        self._azar = azar if azar is not None else random.Random()
        self._por_nombre: Dict[str, Busqueda] = {}

    def reiniciar(self):
        self._por_nombre.clear()

    @property
    def activas(self) -> List[Busqueda]:
        return list(self._por_nombre.values())

    def inminencia(self) -> Optional[float]:
        """La de la búsqueda más apurada, o None si no hay ninguna. Es lo que
        hace sonar y verse la alerta como si hubiera alguien en el patio."""
        if not self._por_nombre:
            return None
        return max(busqueda.inminencia for busqueda in self._por_nombre.values())

    def en_camara(self, id_camara: str) -> List[Busqueda]:
        return [b for b in self._por_nombre.values() if b.camara == id_camara]

    def actualizar(self, dt: float, animatronics) -> ResultadoBusquedas:
        """Empieza la búsqueda de quien acaba de aparecer, descuenta el tiempo
        de las que siguen y cierra las de quien ya no está esperando (lo
        espantaron, desapareció o lo sacaron de la noche)."""
        resultado = ResultadoBusquedas(empezadas=[], agotadas=[])
        for animatronic in animatronics:
            busqueda = self._por_nombre.get(animatronic.nombre)
            if not _esperando_a_que_lo_encuentren(animatronic):
                if busqueda is not None:
                    del self._por_nombre[animatronic.nombre]
                continue
            if busqueda is None:
                busqueda = self._esconder(animatronic)
                resultado.empezadas.append(animatronic)
                continue
            busqueda.segundos_restantes -= dt
            if busqueda.segundos_restantes <= 0.0:
                del self._por_nombre[animatronic.nombre]
                desenlace = (
                    Desenlace.MATA if animatronic.configuracion.busqueda_mortal
                    else Desenlace.IRRUMPE
                )
                resultado.agotadas.append((animatronic, desenlace))
        return resultado

    def _esconder(self, animatronic) -> Busqueda:
        """Elige cámara y sitio. Dos objetos en la misma cámara nunca quedan
        en el mismo sitio, para que uno no tape al otro."""
        camara = self._azar.choice(CAMARAS_CON_OBJETOS)
        ocupados = {b.punto for b in self.en_camara(camara)}
        libres = [sitio for sitio in SITIOS_OBJETOS_BUSCADOS if sitio not in ocupados]
        segundos = segundos_para_buscar(animatronic)
        busqueda = Busqueda(
            nombre=animatronic.nombre,
            id_objeto=animatronic.configuracion.objeto_buscado,
            camara=camara,
            punto=self._azar.choice(libres or list(SITIOS_OBJETOS_BUSCADOS)),
            segundos_totales=segundos,
            segundos_restantes=segundos,
        )
        self._por_nombre[animatronic.nombre] = busqueda
        return busqueda

    def objeto_en(self, id_camara: str, punto) -> Optional[Busqueda]:
        """La búsqueda cuyo objeto está bajo ese punto del monitor, mirando
        esa cámara, o None."""
        x, y = punto
        for busqueda in self.en_camara(id_camara):
            dx = x - busqueda.punto[0]
            dy = y - busqueda.punto[1]
            if dx * dx + dy * dy <= OBJETO_BUSCADO_RADIO_CLIC * OBJETO_BUSCADO_RADIO_CLIC:
                return busqueda
        return None

    def encontrar(self, busqueda: Busqueda, animatronics) -> bool:
        """El jugador dio con el objeto: su dueño desaparece. Devuelve si la
        búsqueda seguía en marcha."""
        if self._por_nombre.get(busqueda.nombre) is not busqueda:
            return False
        del self._por_nombre[busqueda.nombre]
        for animatronic in animatronics:
            if animatronic.nombre == busqueda.nombre:
                animatronic.desaparecer()
        return True
