"""Progreso y preferencias: sobre todo, que un archivo manipulado a mano no
deje el juego en un estado imposible.

Estas pruebas no escriben en disco: trabajan sobre los constructores, que son
donde vive el saneado.
"""

from unittest.mock import patch

import pytest

from vecindad.config.audio import (
    VOLUMEN_MAXIMO,
    VOLUMEN_MINIMO,
    VOLUMEN_MUSICA_POR_DEFECTO,
)
from vecindad.config.partida import NOCHES_HISTORIA, ULTIMA_NOCHE
from vecindad.config.ventana import (
    BRILLO_MAXIMO,
    BRILLO_MINIMO,
    BRILLO_POR_DEFECTO,
    RESOLUCION_BASE,
    RESOLUCIONES_DISPONIBLES,
)
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

    def test_haber_superado_noches_implica_haber_empezado(self):
        """Los guardados viejos no traen el dato, pero si hay noches
        superadas es evidente que la partida existe."""
        assert ProgresoJugador(noches_completadas=3).hay_partida_guardada

    def test_sin_haber_empezado_nunca_no_hay_nada_que_continuar(self):
        assert not ProgresoJugador().hay_partida_guardada


class TestEmpezarDeCero:
    """Nuevo Juego borra el avance: es la regla que evita que Continuar siga
    apuntando a la noche 3 de la partida anterior."""

    @pytest.fixture
    def avanzado(self):
        """Un progreso con la campaña entera hecha, sin tocar el disco."""
        progreso = ProgresoJugador(noches_completadas=ULTIMA_NOCHE)
        with patch.object(ProgresoJugador, "guardar", return_value=True):
            yield progreso

    def test_borra_las_noches_superadas(self, avanzado):
        avanzado.empezar_de_cero()
        assert avanzado.noches_completadas == 0

    def test_continuar_vuelve_a_ofrecer_la_noche_uno(self, avanzado):
        avanzado.empezar_de_cero()
        assert avanzado.proxima_noche == 1

    def test_sigue_habiendo_partida_que_continuar(self, avanzado):
        """Aunque no haya ninguna noche superada todavía: la partida existe
        desde que se empieza, no desde que se gana algo."""
        avanzado.empezar_de_cero()
        assert avanzado.hay_partida_guardada

    def test_vuelve_a_cerrar_la_noche_seis_y_la_personalizada(self, avanzado):
        avanzado.empezar_de_cero()
        assert not avanzado.noche_extra_desbloqueada
        assert not avanzado.noche_personalizada_desbloqueada

    def test_se_persiste_al_momento(self):
        """Si no se guardara aquí, salir a mitad de la primera noche dejaría
        el avance viejo intacto en disco."""
        progreso = ProgresoJugador(noches_completadas=3)
        with patch.object(ProgresoJugador, "guardar", return_value=True) as guardar:
            progreso.empezar_de_cero()
        assert guardar.called

    def test_ganar_una_noche_vuelve_a_subir_el_contador(self, avanzado):
        """Y de ahí en adelante Continuar avanza como siempre."""
        avanzado.empezar_de_cero()
        assert avanzado.registrar_noche_completada(1)
        assert avanzado.proxima_noche == 2


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

    def test_el_brillo_arranca_neutro(self):
        assert Configuracion().brillo == BRILLO_POR_DEFECTO

    @pytest.mark.parametrize(
        "guardado,esperado",
        [(10, BRILLO_MINIMO), (500, BRILLO_MAXIMO), (120, 120)],
    )
    def test_un_brillo_fuera_de_rango_se_recorta(self, guardado, esperado):
        """Sin recorte, un archivo tocado a mano podía dejar la pantalla
        completamente negra o lavada, y sin manera de arreglarlo desde el
        propio juego."""
        assert Configuracion(brillo=guardado).brillo == esperado

    def test_un_brillo_que_no_es_numero_cae_al_por_defecto(self):
        assert Configuracion(brillo="claro").brillo == BRILLO_POR_DEFECTO
