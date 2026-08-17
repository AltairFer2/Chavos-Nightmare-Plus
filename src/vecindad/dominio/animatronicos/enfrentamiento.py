"""Lo que ocurre cuando el jugador y un animatrónico se encuentran cara a
cara: a quién tiene delante, a quién está alumbrando, a quién mata la luz y
qué pasa al arrojarle un objeto.

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
from ..objetos import ID_CHURRUMINO, objetos_que_ahuyentan_a, obtener_objeto
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


def _respuestas_posibles(animatronic: Animatronic):
    """Los objetos con los que este personaje se quita de encima ahora mismo.

    A Doña Clotilde solo le sirve lo que haya pedido: es la única a la que no
    le vale cualquier objeto de su lista.
    """
    if animatronic.objeto_pedido is not None:
        return (animatronic.objeto_pedido,)
    return objetos_que_ahuyentan_a(animatronic.nombre)


def esta_en_tregua(animatronic: Animatronic, inventario) -> bool:
    """Si todavía no puede matar al jugador porque el suelo no le ha dado la
    respuesta ni una sola vez en toda la noche.

    Mientras sea True, ese personaje no descuenta el margen de ataque (ver
    Animatronic.descontar_espera): se planta delante y mete miedo, pero no
    mata. Es un seguro contra perder por una mala racha del sorteo del suelo,
    no un escudo:

    - La tregua se rompe en cuanto el objeto le pasa por las manos, y ya no
      vuelve. Si lo desperdició tirándoselo a quien no era, el personaje lo
      mata igual aunque el jugador se haya quedado sin nada: la respuesta
      existió y la gastó mal.
    - Quien no se contrarresta con objetos (Don Ramón con el Sr. Barriga,
      Doña Florinda con el audio) nunca está en tregua: su respuesta está en
      el panel del barril y no depende de la suerte.
    """
    opciones = _respuestas_posibles(animatronic)
    if not opciones:
        return False
    return not any(
        inventario.puede_usar(id_objeto) or inventario.tuvo(id_objeto)
        for id_objeto in opciones
    )


@dataclass
class ResultadoArrojo:
    """Qué pasó al arrojar un objeto: a quién se llevó por delante y a quién
    solo entretuvo."""

    eliminado: Optional[Animatronic] = None
    retrasado: Optional[Animatronic] = None

    @property
    def sirvio(self) -> bool:
        return self.eliminado is not None or self.retrasado is not None


def resolver_arrojo(presentes, id_objeto: str, iluminados) -> ResultadoArrojo:
    """Decide a quién le toca el objeto que se acaba de arrojar.

    Primero se atiende a Doña Clotilde si pidió justo eso, porque el objeto
    va dirigido a ella. Después se recorre la lista del objeto en orden: el
    primero de esa lista que esté delante y lo acepte es el que se va. El
    churrumino suelto es el caso aparte: no elimina a nadie, solo entretiene
    a El Chavo un rato.
    """
    objeto = obtener_objeto(id_objeto)

    for animatronic in presentes:
        if animatronic.objeto_pedido == id_objeto:
            animatronic.ahuyentar()
            return ResultadoArrojo(eliminado=animatronic)

    if id_objeto == ID_CHURRUMINO:
        for animatronic in presentes:
            if animatronic.nombre == nombres.CHAVO:
                animatronic.retrasar(SEGUNDOS_RETRASO_CHURRUMINO)
                return ResultadoArrojo(retrasado=animatronic)
        return ResultadoArrojo()

    por_nombre = {animatronic.nombre: animatronic for animatronic in presentes}
    for nombre in objeto.elimina:
        animatronic = por_nombre.get(nombre)
        if animatronic is None:
            continue
        if not animatronic.acepta_objeto(nombre in iluminados):
            continue
        animatronic.ahuyentar()
        return ResultadoArrojo(eliminado=animatronic)
    return ResultadoArrojo()
