"""Lo que ocurre cuando el jugador y un animatrónico se encuentran cara a
cara: a quién tiene delante, a quién está alumbrando y a quién mata la luz.
Espantar con la luz a los demás vive aparte, en espanto.py.

Estar delante del jugador es estar en el Primer Patio, y punto: el Barril y
los Lavaderos son dos ángulos del mismo sitio, así que desde los dos se ve a
todo el que haya llegado. Lo único que cambia con el ángulo es en qué punto
del lienzo cae cada uno (ver ConfiguracionAnimatronic.puntos_acecho), que es
lo que decide si la linterna le está apuntando o no.

Todo son funciones sobre una lista de animatrónicos, sin estado propio, para
poder probarlas sin montar una partida entera.
"""

from typing import List

from ..linterna import esta_iluminado
from .entidad import Animatronic


def acechando(animatronics) -> List[Animatronic]:
    """Personajes que ya llegaron al Primer Patio y acechan al jugador, o sea
    los que puede ver y alumbrar, esté asomado al barril o en los
    lavaderos."""
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
