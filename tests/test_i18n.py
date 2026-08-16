"""Textos: que los tres idiomas estén completos y coherentes entre sí."""

import re
import string

import pytest

from vecindad.i18n import (
    GestorIdiomas,
    IDIOMA_POR_DEFECTO,
    IDIOMAS_DISPONIBLES,
    NOMBRES_IDIOMAS,
)
from vecindad.i18n.textos import CATALOGOS


def campos_de(texto: str):
    """Los marcadores {asi} que lleva una cadena de formato."""
    return {
        nombre
        for _, nombre, _, _ in string.Formatter().parse(texto)
        if nombre is not None
    }


@pytest.mark.parametrize("idioma", IDIOMAS_DISPONIBLES)
def test_ningun_idioma_tiene_claves_de_menos(idioma):
    faltantes = set(CATALOGOS[IDIOMA_POR_DEFECTO]) - set(CATALOGOS[idioma])
    assert not faltantes, f"{idioma} no traduce: {sorted(faltantes)}"


@pytest.mark.parametrize("idioma", IDIOMAS_DISPONIBLES)
def test_ningun_idioma_tiene_claves_de_mas(idioma):
    """Una clave que solo existe en un idioma casi siempre es una errata: el
    juego la pediría y caería al español sin que nadie lo note."""
    sobrantes = set(CATALOGOS[idioma]) - set(CATALOGOS[IDIOMA_POR_DEFECTO])
    assert not sobrantes, f"{idioma} tiene claves que el español no: {sorted(sobrantes)}"


@pytest.mark.parametrize("idioma", IDIOMAS_DISPONIBLES)
def test_los_marcadores_de_formato_coinciden(idioma):
    """Si el español dice {nombre} y la traducción dice {name}, el juego
    revienta con KeyError justo al mostrar ese texto."""
    referencia = CATALOGOS[IDIOMA_POR_DEFECTO]
    diferencias = {
        clave: (campos_de(referencia[clave]), campos_de(texto))
        for clave, texto in CATALOGOS[idioma].items()
        if clave in referencia and campos_de(referencia[clave]) != campos_de(texto)
    }
    assert not diferencias, f"{idioma}: marcadores distintos en {diferencias}"


@pytest.mark.parametrize("idioma", IDIOMAS_DISPONIBLES)
def test_no_hay_textos_vacios(idioma):
    vacios = [clave for clave, texto in CATALOGOS[idioma].items() if not texto.strip()]
    assert not vacios, f"{idioma}: textos vacíos en {vacios}"


@pytest.mark.parametrize("idioma", IDIOMAS_DISPONIBLES)
def test_cada_idioma_tiene_su_nombre_para_el_selector(idioma):
    assert NOMBRES_IDIOMAS.get(idioma)


class TestGestorIdiomas:
    def test_traduce_al_idioma_activo(self):
        assert GestorIdiomas("en").t("menu_ajustes") == "Settings"

    def test_un_idioma_desconocido_cae_al_por_defecto(self):
        assert GestorIdiomas("klingon").idioma == IDIOMA_POR_DEFECTO

    def test_una_clave_que_no_existe_se_ve_a_simple_vista(self):
        assert GestorIdiomas().t("clave_inventada") == "[clave_inventada]"

    def test_aplica_el_formato(self):
        assert "3" in GestorIdiomas("es").t("hud_noche", noche=3)

    def test_el_selector_da_la_vuelta_por_todos_los_idiomas(self):
        gestor = GestorIdiomas(IDIOMAS_DISPONIBLES[0])
        recorridos = [gestor.siguiente_idioma() for _ in IDIOMAS_DISPONIBLES]
        assert set(recorridos) == set(IDIOMAS_DISPONIBLES)
        assert gestor.idioma == IDIOMAS_DISPONIBLES[0]

    def test_cambiar_a_un_idioma_invalido_no_hace_nada(self):
        gestor = GestorIdiomas("es")
        gestor.cambiar("klingon")
        assert gestor.idioma == "es"
