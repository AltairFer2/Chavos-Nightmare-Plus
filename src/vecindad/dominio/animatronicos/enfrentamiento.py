"""Lo que ocurre cuando el jugador y un animatrónico se encuentran cara a
cara: a quién tiene delante, a quién está alumbrando, a quién mata la luz y
a quién le da un objeto arrojado y qué le hace.

Estar delante del jugador es estar en el Primer Patio, y punto: el Barril y
los Lavaderos son dos ángulos del mismo sitio, así que desde los dos se ve a
todo el que haya llegado. Lo único que cambia con el ángulo es en qué punto
del lienzo cae cada uno (ver ConfiguracionAnimatronic.puntos_acecho), que es
lo que decide si la linterna le está apuntando o no.

Todo son funciones sobre una lista de animatrónicos, sin estado propio, para
poder probarlas sin montar una partida entera.
"""

from dataclasses import dataclass
from typing import List, Optional

from ...config.jugabilidad import SEGUNDOS_RETRASO_CHURRUMINO
from ..linterna import esta_iluminado
from ..objetos import ID_CHURRUMINO, obtener_objeto
from . import nombres
from .entidad import Animatronic


def acechando(animatronics) -> List[Animatronic]:
    """Personajes que ya llegaron al Primer Patio y acechan al jugador, o sea
    los que puede ver, alumbrar y a los que puede arrojarles algo, esté
    asomado al barril o en los lavaderos."""
    return [
        animatronic for animatronic in animatronics
        if animatronic.activo and animatronic.esta_acechando()
    ]


def acechando_en(animatronics, id_posicion: str) -> List[Animatronic]:
    """Los que acechan y además tienen un sitio dibujado desde esa posición.

    En la práctica son todos, porque el patio se ve entero desde sus dos
    ángulos; la comprobación está para que un personaje al que se le olvidara
    su punto en uno de los dos no se dibuje encima de las esquinas.
    """
    return [
        animatronic for animatronic in acechando(animatronics)
        if animatronic.punto_acecho_en(id_posicion) is not None
    ]


def iluminados_en(animatronics, id_posicion: str, punto_luz, encendida: bool):
    """Nombres de los personajes que el jugador tiene dentro del haz."""
    if not encendida:
        return set()
    return {
        animatronic.nombre
        for animatronic in acechando_en(animatronics, id_posicion)
        if esta_iluminado(animatronic.punto_torso_en(id_posicion), punto_luz)
    }


def _alumbrado_de_cerca(animatronics, id_posicion: str, punto_luz, condicion):
    """El primero al que la linterna apunta lo bastante cerca como para que
    reaccione y que además cumpla `condicion`, o None."""
    if punto_luz is None:
        return None
    x, y = punto_luz
    for animatronic in acechando_en(animatronics, id_posicion):
        radio = animatronic.radio_peligro()
        if radio <= 0 or not condicion(animatronic):
            continue
        torso = animatronic.punto_torso_en(id_posicion)
        distancia_x = x - torso[0]
        distancia_y = y - torso[1]
        if distancia_x * distancia_x + distancia_y * distancia_y <= radio * radio:
            return animatronic
    return None


def detectar_luz_mortal(animatronics, id_posicion: str, punto_luz):
    """Devuelve el personaje al que la linterna está apuntando lo bastante
    cerca como para que sea mortal, o None si no hay ninguno."""
    return _alumbrado_de_cerca(
        animatronics, id_posicion, punto_luz,
        lambda a: a.configuracion.luz_mortal,
    )


def detectar_luz_que_descarga(animatronics, id_posicion: str, punto_luz):
    """Devuelve el personaje al que apuntarle cuesta la batería entera pero
    no la vida, o None. Hoy solo La Chilindrina."""
    return _alumbrado_de_cerca(
        animatronics, id_posicion, punto_luz,
        lambda a: a.configuracion.luz_descarga_linterna and not a.configuracion.luz_mortal,
    )


def objetivo_del_arrojo(animatronics, id_posicion: str, punto_mira):
    """A quién le da un objeto arrojado hacia `punto_mira`, o None si no le
    da a nadie.

    Le da a quien tenga el punto dentro de su elipse de acierto (ver
    Animatronic.semiejes_acierto). Si dos se pisan, a aquel en cuyo centro
    caiga más de lleno: el objeto va a una sola persona.
    """
    if punto_mira is None:
        return None
    x, y = punto_mira
    mas_cerca = None
    menor_distancia = None
    for animatronic in acechando_en(animatronics, id_posicion):
        torso = animatronic.punto_torso_en(id_posicion)
        semiancho, semialto = animatronic.semiejes_acierto()
        # 0 en el torso, 1 justo en el borde de la elipse.
        distancia = ((x - torso[0]) / semiancho) ** 2 + ((y - torso[1]) / semialto) ** 2
        if distancia > 1.0:
            continue
        if menor_distancia is None or distancia < menor_distancia:
            mas_cerca, menor_distancia = animatronic, distancia
    return mas_cerca


@dataclass
class ResultadoArrojo:
    """Qué pasó al arrojar un objeto: a quién le dio, y si a ese se lo llevó
    por delante o solo lo entretuvo."""

    alcanzado: Optional[Animatronic] = None
    eliminado: Optional[Animatronic] = None
    retrasado: Optional[Animatronic] = None

    @property
    def sirvio(self) -> bool:
        return self.eliminado is not None or self.retrasado is not None


def resolver_arrojo(alcanzado, id_objeto: str, iluminado: bool) -> ResultadoArrojo:
    """Qué le hace el objeto a quien le dio (ver objetivo_del_arrojo).

    Solo cuenta a quién le dio: si el tiro le cae a quien no era, se pierde
    aunque detrás hubiera alguien a quien sí le servía.

    - A Doña Clotilde solo le vale lo que haya pedido.
    - El churrumino suelto no elimina a nadie: solo entretiene a El Chavo.
    - Al resto se lo lleva su objeto, si lo acepta (Jaimico solo con luz).
    """
    if alcanzado is None:
        return ResultadoArrojo()
    resultado = ResultadoArrojo(alcanzado=alcanzado)

    if alcanzado.objeto_pedido is not None:
        if alcanzado.objeto_pedido == id_objeto:
            alcanzado.ahuyentar()
            resultado.eliminado = alcanzado
        return resultado

    if id_objeto == ID_CHURRUMINO:
        if alcanzado.nombre == nombres.CHAVO:
            alcanzado.retrasar(SEGUNDOS_RETRASO_CHURRUMINO)
            resultado.retrasado = alcanzado
        return resultado

    le_sirve = alcanzado.nombre in obtener_objeto(id_objeto).elimina
    if le_sirve and alcanzado.acepta_objeto(iluminado):
        alcanzado.ahuyentar()
        resultado.eliminado = alcanzado
    return resultado
