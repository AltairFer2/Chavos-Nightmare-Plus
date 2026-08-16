"""Progreso y preferencias: sobre todo, que un archivo manipulado a mano no
deje el juego en un estado imposible.

Estas pruebas no escriben en disco: trabajan sobre los constructores, que son
donde vive el saneado.
"""

import pytest

from vecindad.config.audio import (
    VOLUMEN_MAXIMO,
    VOLUMEN_MINIMO,
    VOLUMEN_MUSICA_POR_DEFECTO,
)
from vecindad.config.partida import NOCHES_HISTORIA, ULTIMA_NOCHE
from vecindad.config.ventana import RESOLUCION_BASE, RESOLUCIONES_DISPONIBLES
from vecindad.i18n import IDIOMA_POR_DEFECTO
from vecindad.infraestructura.guardado import Configuracion, ProgresoJugador


class TestProgreso:
    def test_una_partida_nueva_no_tiene_nada_desbloqueado(self):
        progreso = ProgresoJugador()
        assert not progreso.hay_partida_guardada
        assert not progreso.noche_extra_desbloqueada
        assert not progreso.noche_personalizada_desbloqueada

    def test_continuar_ofrece_la_noche_siguiente(self):
        assert ProgresoJugador(noches_completadas=2).proxima_noche == 3

    def test_al_final_de_la_campana_continuar_se_queda_en_la_ultima(self):
        assert ProgresoJugador(noches_completadas=ULTIMA_NOCHE).proxima_noche == ULTIMA_NOCHE

    def test_la_noche_seis_se_abre_al_terminar_la_cinco(self):
        assert ProgresoJugador(noches_completadas=NOCHES_HISTORIA).noche_extra_desbloqueada

    def test_la_personalizada_se_abre_al_terminar_la_seis(self):
        progreso = ProgresoJugador(noches_completadas=ULTIMA_NOCHE)
        assert progreso.noche_personalizada_desbloqueada

    @pytest.mark.parametrize(
        "guardado,esperado",
        [(-3, 0), (0, 0), (3, 3), (99, ULTIMA_NOCHE), ("cinco", 0), (None, 0), (True, 0)],
    )
    def test_un_progreso_manipulado_se_recorta(self, guardado, esperado):
        assert ProgresoJugador(noches_completadas=guardado).noches_completadas == esperado

    def test_rehacer_una_noche_ya_superada_no_cuenta_como_avance(self):
        progreso = ProgresoJugador(noches_completadas=3)
        assert not progreso.registrar_noche_completada(2)
        assert progreso.noches_completadas == 3


class TestConfiguracion:
    def test_los_valores_por_defecto_son_validos(self):
        configuracion = Configuracion()
        assert configuracion.idioma == IDIOMA_POR_DEFECTO
        assert configuracion.resolucion in RESOLUCIONES_DISPONIBLES
        assert configuracion.volumen_musica == VOLUMEN_MUSICA_POR_DEFECTO

    def test_un_idioma_desconocido_cae_al_por_defecto(self):
        assert Configuracion(idioma="klingon").idioma == IDIOMA_POR_DEFECTO

    @pytest.mark.parametrize(
        "guardada", [(999, 999), "1280x720", None, (), (1280,), {"ancho": 1280}]
    )
    def test_una_resolucion_imposible_cae_a_la_base(self, guardada):
        assert Configuracion(resolucion=guardada).resolucion == RESOLUCION_BASE

    def test_una_resolucion_soportada_se_respeta(self):
        soportada = RESOLUCIONES_DISPONIBLES[0]
        assert Configuracion(resolucion=list(soportada)).resolucion == soportada

    @pytest.mark.parametrize(
        "guardado,esperado",
        [(-20, VOLUMEN_MINIMO), (500, VOLUMEN_MAXIMO), (55, 55)],
    )
    def test_el_volumen_se_recorta_a_su_rango(self, guardado, esperado):
        assert Configuracion(volumen_musica=guardado).volumen_musica == esperado

    def test_un_volumen_que_no_es_numero_cae_al_por_defecto(self):
        assert Configuracion(volumen_musica="alto").volumen_musica == VOLUMEN_MUSICA_POR_DEFECTO
