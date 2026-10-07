"""La tipografía viaja con el juego y tiene todos los caracteres que usan
los textos."""

import pathlib

import pygame
import pytest

from vecindad.config.interfaz import FUENTE_NOMBRE
from vecindad.config.rutas import DIR_ASSETS_FUENTES
from vecindad.infraestructura.fuentes import _buscar_archivo_fuente
from vecindad.i18n.textos import en, es, pt

IDIOMAS = {"es": es, "en": en, "pt": pt}


@pytest.fixture(scope="module", autouse=True)
def fuentes():
    pygame.font.init()
    yield


def _textos(modulo):
    """Todos los textos de un idioma, sea cual sea el nombre del diccionario."""
    return [
        valor
        for nombre in dir(modulo) if not nombre.startswith("_")
        for diccionario in [getattr(modulo, nombre)] if isinstance(diccionario, dict)
        for valor in diccionario.values() if isinstance(valor, str)
    ]


def test_la_fuente_esta_en_assets_con_su_licencia():
    """No depende de lo que tenga instalado cada PC, y su licencia (OFL)
    permite repartirla con el juego."""
    regular, _ = _buscar_archivo_fuente(FUENTE_NOMBRE)
    negrita, es_negrita = _buscar_archivo_fuente(FUENTE_NOMBRE, negrita=True)
    assert regular is not None and regular.parent == DIR_ASSETS_FUENTES
    assert negrita is not None and es_negrita
    assert (DIR_ASSETS_FUENTES / "OFL.txt").exists()


@pytest.mark.parametrize("idioma", sorted(IDIOMAS))
def test_tiene_todos_los_caracteres_de_los_textos(idioma):
    """Un carácter que la fuente no trae sale como un cuadrito (pasó con las
    flechas de la ayuda). Se compara cada uno con el cuadrito de un carácter
    que seguro no existe."""
    ruta, _ = _buscar_archivo_fuente(FUENTE_NOMBRE)
    fuente = pygame.font.Font(str(ruta), 24)

    def huella(caracter):
        superficie = fuente.render(caracter, True, (255, 255, 255))
        return pygame.image.tobytes(superficie, "RGBA") if superficie.get_width() else b""

    cuadrito = huella("")
    textos = _textos(IDIOMAS[idioma])
    assert textos, "no se encontraron los textos del idioma"
    caracteres = {c for texto in textos for c in texto if not c.isspace() and ord(c) > 126}
    faltan = sorted(c for c in caracteres if huella(c) == cuadrito)
    assert faltan == [], [f"U+{ord(c):04X}" for c in faltan]
