"""Cara a cara con el jugador: quién acecha, a quién alumbra la linterna y a
quién mata la luz. Espantar con la luz se prueba en test_espanto.py."""

import pytest

from conftest import crear, llevar_a_acechar
from vecindad.config.jugabilidad import LINTERNA_RADIO
from vecindad.dominio.animatronicos import (
    ELENCO,
    Animatronic,
    acechando_en,
    detectar_luz_mortal,
    iluminados_en,
    inminencia_en_el_patio,
    nombres,
)
from vecindad.mundo.posiciones import POSICION_BARRIL, POSICION_LAVADEROS


@pytest.fixture
def ramon_acechando():
    return llevar_a_acechar(crear(nombres.DON_RAMON, nivel_ia=10))


@pytest.fixture
def quico_acechando():
    return llevar_a_acechar(crear(nombres.QUICO, nivel_ia=10))


class TestQuienEstaDelante:
    def test_aparece_para_quien_esta_asomado_al_barril(self, quico_acechando):
        assert acechando_en([quico_acechando], POSICION_BARRIL) == [quico_acechando]

    def test_tambien_aparece_desde_los_lavaderos(self, quico_acechando):
        """El Barril y los Lavaderos son el mismo patio visto desde dos
        ángulos: quien llega a la cámara 1 se ve desde los dos. Si no, el
        jugador podría estar a dos metros de alguien sin poder verlo ni
        espantarlo, que es como se rompía antes."""
        assert acechando_en([quico_acechando], POSICION_LAVADEROS) == [quico_acechando]

    @pytest.mark.parametrize("config", ELENCO, ids=lambda c: c.nombre)
    def test_nadie_se_vuelve_invisible_en_ninguna_de_las_dos_vistas(self, config):
        llegado = llevar_a_acechar(Animatronic(config, nivel_ia=10))
        for id_posicion in (POSICION_BARRIL, POSICION_LAVADEROS):
            assert acechando_en([llegado], id_posicion) == [llegado], id_posicion
            assert llegado.punto_acecho_en(id_posicion) is not None

    def test_no_aparece_si_todavia_viene_de_camino(self):
        assert acechando_en([crear(nombres.QUICO, nivel_ia=1)], POSICION_BARRIL) == []

    def test_no_aparece_si_esta_inactivo(self):
        dormido = llevar_a_acechar(crear(nombres.QUICO, nivel_ia=1))
        dormido.activo = False
        assert acechando_en([dormido], POSICION_BARRIL) == []


class TestLaLuzSobreLaChilindrina:
    """A ella la luz no la mata. Fallarle el punto débil le cuesta la
    batería al jugador (ver test_espanto.py)."""

    @pytest.fixture
    def chilindrina_acechando(self):
        return llevar_a_acechar(crear(nombres.CHILINDRINA, nivel_ia=10))

    def test_alumbrarla_no_es_mortal(self, chilindrina_acechando):
        """Este era el fallo: su susto mandaba al game over."""
        assert detectar_luz_mortal(
            [chilindrina_acechando], POSICION_BARRIL,
            chilindrina_acechando.punto_torso_en(POSICION_BARRIL),
        ) is None

    def test_sigue_teniendo_radio_de_reaccion(self, chilindrina_acechando):
        """Es el radio dentro del cual fallarle el punto le descarga la
        batería: si fuera 0 nunca castigaría."""
        assert chilindrina_acechando.radio_peligro() > 0
        assert chilindrina_acechando.reacciona_a_la_luz


class TestLinterna:
    def test_con_la_linterna_apagada_no_hay_nadie_alumbrado(self, quico_acechando):
        alumbrados = iluminados_en(
            [quico_acechando], POSICION_BARRIL,
            quico_acechando.punto_torso_en(POSICION_BARRIL), encendida=False,
        )
        assert alumbrados == set()

    def test_apuntarle_al_torso_lo_deja_alumbrado(self, quico_acechando):
        alumbrados = iluminados_en(
            [quico_acechando], POSICION_BARRIL,
            quico_acechando.punto_torso_en(POSICION_BARRIL), encendida=True,
        )
        assert alumbrados == {nombres.QUICO}

    def test_apuntar_lejos_no_alumbra_a_nadie(self, quico_acechando):
        x, y = quico_acechando.punto_torso_en(POSICION_BARRIL)
        alumbrados = iluminados_en(
            [quico_acechando], POSICION_BARRIL,
            (x + LINTERNA_RADIO * 3, y), encendida=True,
        )
        assert alumbrados == set()


class TestLuzMortal:
    def test_alumbrar_de_cerca_a_don_ramon_es_fatal(self, ramon_acechando):
        victimario = detectar_luz_mortal(
            [ramon_acechando], POSICION_BARRIL, ramon_acechando.punto_torso_en(POSICION_BARRIL)
        )
        assert victimario is ramon_acechando

    def test_a_quico_la_luz_no_le_hace_nada(self, quico_acechando):
        assert detectar_luz_mortal(
            [quico_acechando], POSICION_BARRIL, quico_acechando.punto_torso_en(POSICION_BARRIL)
        ) is None

    def test_fuera_del_radio_de_peligro_se_sobrevive(self, ramon_acechando):
        x, y = ramon_acechando.punto_torso_en(POSICION_BARRIL)
        lejos = (x + ramon_acechando.radio_peligro() + 5, y)
        assert detectar_luz_mortal([ramon_acechando], POSICION_BARRIL, lejos) is None

    def test_sin_punto_de_luz_no_muere_nadie(self, ramon_acechando):
        assert detectar_luz_mortal([ramon_acechando], POSICION_BARRIL, None) is None


class TestInminencia:
    """Lo cerca que está el ataque: es lo que mide la alerta de peligro."""

    def test_fuera_del_patio_es_cero(self):
        assert crear(nombres.QUICO, nivel_ia=10).inminencia() == 0.0

    def test_al_llegar_es_cero(self, quico_acechando):
        assert quico_acechando.inminencia() == pytest.approx(0.0)

    def test_crece_conforme_corre_su_espera(self, quico_acechando):
        espera = quico_acechando.espera_de_ataque()
        quico_acechando.descontar_espera(espera / 2)
        assert quico_acechando.inminencia() == pytest.approx(0.5)

    def test_al_atacar_es_uno(self, quico_acechando):
        quico_acechando.descontar_espera(quico_acechando.espera_de_ataque() + 1.0)
        assert quico_acechando.inminencia() == 1.0

    def test_escondido_a_salvo_no_avanza(self, quico_acechando):
        """Dentro del barril la espera de Quico no corre, y la alerta se
        queda donde estaba."""
        quico_acechando.descontar_espera(5.0, jugador_escondido=True)
        assert quico_acechando.inminencia() == pytest.approx(0.0)


class TestInminenciaEnElPatio:
    def test_con_el_patio_vacio_no_hay(self):
        assert inminencia_en_el_patio([crear(nombres.QUICO, nivel_ia=10)]) is None

    def test_manda_el_ataque_mas_proximo(self, quico_acechando, ramon_acechando):
        quico_acechando.descontar_espera(quico_acechando.espera_de_ataque() * 0.8)
        assert inminencia_en_el_patio([ramon_acechando, quico_acechando]) == pytest.approx(0.8)

    def test_los_inactivos_no_cuentan(self, quico_acechando):
        quico_acechando.activo = False
        assert inminencia_en_el_patio([quico_acechando]) is None
