"""Configuración común de las pruebas.

Las pruebas cubren la capa de dominio, que no usa pygame, así que no hace
falta abrir ninguna ventana. Aun así se fuerzan los drivers de vídeo y audio
a "dummy" por si alguna prueba futura importa algo de presentacion/: sin
esto, pygame intentaría abrir una ventana real y fallaría en un CI.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from unittest.mock import patch  # noqa: E402  (después de fijar el entorno de SDL)

import pytest  # noqa: E402

from vecindad.dominio.animatronicos import (  # noqa: E402
    Animatronic,
    ELENCO,
    nombres,
)


def ficha_de(nombre: str):
    """La ConfiguracionAnimatronic del personaje con ese nombre."""
    for config in ELENCO:
        if config.nombre == nombre:
            return config
    raise AssertionError(f"El elenco no tiene a {nombre}")


def crear(nombre: str, nivel_ia: int = 1) -> Animatronic:
    """Un animatrónico suelto para probar, sin montar la noche entera."""
    return Animatronic(ficha_de(nombre), nivel_ia)


def llevar_a_acechar(animatronic: Animatronic) -> Animatronic:
    """Lo deja plantado delante del jugador, que es el estado del que parten
    casi todas las pruebas de enfrentamiento.

    Usa irrumpir() en vez de caminar el grafo a propósito: no todos tienen un
    camino de dados hasta el Primer Patio (El Chavo no tiene ninguno, y Doña
    Clotilde depende de dónde ande Don Ramón), así que recorrerlo a fuerza de
    rondas se colgaría con unos y sería lentísimo con otros. Que el recorrido
    de verdad lleve hasta el patio se prueba aparte, en test_animatronicos.py.
    """
    assert animatronic.activo, "un animatrónico inactivo nunca llega a acechar"
    animatronic.irrumpir()
    return animatronic


def caminar_hasta_acechar(animatronic: Animatronic, elenco=(), tope: int = 200) -> bool:
    """Lo hace avanzar por su grafo con el dado cargado a favor, hasta que
    llegue al jugador o se agote el tope de rondas.

    Carga el dado en vez de subirle el nivel: el nivel decide también el
    margen de ataque y el radio de la luz mortal, así que tocarlo falsearía
    justo lo que las pruebas quieren medir. Se deja intacto el random.choice
    que elige a cuál de los destinos posibles va.
    """
    with patch("vecindad.dominio.animatronicos.entidad.random.randint", return_value=1):
        for _ in range(tope):
            if animatronic.esta_acechando():
                return True
            animatronic.actualizar(elenco)
    return animatronic.esta_acechando()


@pytest.fixture
def don_ramon() -> Animatronic:
    """Sensible a la luz: sirve para probar la muerte por linterna."""
    return crear(nombres.DON_RAMON, nivel_ia=10)


@pytest.fixture
def quico() -> Animatronic:
    """Solo acepta objetos si está alumbrado."""
    return crear(nombres.QUICO, nivel_ia=10)


@pytest.fixture
def chavo() -> Animatronic:
    """El que se entretiene con el churrumino y sabotea las cámaras."""
    return crear(nombres.CHAVO, nivel_ia=10)


@pytest.fixture
def clotilde() -> Animatronic:
    """Al llegar pide un objeto al azar."""
    return crear(nombres.CLOTILDE, nivel_ia=10)
