"""Cara a cara con el jugador: quién acecha, a quién alumbra la linterna y
qué pasa al arrojarle un objeto."""

import pytest

from conftest import crear, llevar_a_acechar
from vecindad.config.jugabilidad import LINTERNA_RADIO, SEGUNDOS_RETRASO_CHURRUMINO
from vecindad.dominio.animatronicos import (
    ELENCO,
    Animatronic,
    acechando_en,
    detectar_luz_mortal,
    detectar_luz_que_descarga,
    iluminados_en,
    nombres,
    resolver_arrojo,
)
from vecindad.dominio.objetos import (
    ID_BALERO,
    ID_CAFE_CHURRUMINO,
    ID_CHURRUMINO,
    ID_PALETA,
    ID_PELOTA_CUADRADA,
    ID_PELOTA_REDONDA,
    OBJETOS_DEFENSIVOS,
)
from vecindad.mundo.posiciones import POSICION_BARRIL, POSICION_LAVADEROS


@pytest.fixture
def ramon_acechando():
    return llevar_a_acechar(crear(nombres.DON_RAMON, nivel_ia=10))


@pytest.fixture
def quico_acechando():
    return llevar_a_acechar(crear(nombres.QUICO, nivel_ia=10))


@pytest.fixture
def chavo_acechando():
    return llevar_a_acechar(crear(nombres.CHAVO, nivel_ia=10))


class TestQuienEstaDelante:
    def test_aparece_para_quien_esta_asomado_al_barril(self, quico_acechando):
        assert acechando_en([quico_acechando], POSICION_BARRIL) == [quico_acechando]

    def test_tambien_aparece_desde_los_lavaderos(self, quico_acechando):
        """El Barril y los Lavaderos son el mismo patio visto desde dos
        ángulos: quien llega a la cámara 1 se ve desde los dos. Si no, el
        jugador podría estar a dos metros de alguien sin poder verlo ni
        arrojarle nada, que es como se rompía antes."""
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
    """A ella la luz no la mata: se lleva la batería entera. Es el castigo
    más caro del juego sin ser una derrota."""

    @pytest.fixture
    def chilindrina_acechando(self):
        return llevar_a_acechar(crear(nombres.CHILINDRINA, nivel_ia=10))

    def test_alumbrarla_no_es_mortal(self, chilindrina_acechando):
        """Este era el fallo: su susto mandaba al game over."""
        assert detectar_luz_mortal(
            [chilindrina_acechando], POSICION_BARRIL,
            chilindrina_acechando.punto_torso_en(POSICION_BARRIL),
        ) is None

    def test_alumbrarla_cuesta_la_bateria(self, chilindrina_acechando):
        assert detectar_luz_que_descarga(
            [chilindrina_acechando], POSICION_BARRIL,
            chilindrina_acechando.punto_torso_en(POSICION_BARRIL),
        ) is chilindrina_acechando

    def test_sigue_teniendo_radio_de_reaccion(self, chilindrina_acechando):
        """Si el radio fuera 0 nunca se daría cuenta de que la alumbran."""
        assert chilindrina_acechando.radio_peligro() > 0
        assert chilindrina_acechando.reacciona_a_la_luz

    def test_apuntar_lejos_no_le_cuesta_nada(self, chilindrina_acechando):
        x, y = chilindrina_acechando.punto_torso_en(POSICION_BARRIL)
        lejos = (x + chilindrina_acechando.radio_peligro() + 5, y)
        assert detectar_luz_que_descarga(
            [chilindrina_acechando], POSICION_BARRIL, lejos
        ) is None

    def test_a_quien_mata_la_luz_no_se_le_aplica_el_castigo(self, ramon_acechando):
        """Don Ramón muere, no descarga: si saliera en las dos listas se
        aplicarían los dos efectos al mismo tiempo."""
        assert detectar_luz_que_descarga(
            [ramon_acechando], POSICION_BARRIL,
            ramon_acechando.punto_torso_en(POSICION_BARRIL),
        ) is None

    def test_la_luz_no_la_quita_de_encima(self, chilindrina_acechando):
        """Alumbrarla es solo el castigo; para que se vaya hay que darle su
        paleta o su balero."""
        assert chilindrina_acechando.esta_acechando()

    @pytest.mark.parametrize("id_objeto", [ID_PALETA, ID_BALERO])
    def test_se_va_con_la_paleta_o_con_el_balero(self, chilindrina_acechando, id_objeto):
        resultado = resolver_arrojo([chilindrina_acechando], id_objeto, set())
        assert resultado.eliminado is chilindrina_acechando


class TestQuicoSeVaConLaPelota:
    """Su contramedida tiene que poder ejecutarse a oscuras: alumbrarlo es
    mortal, así que exigirle luz para que recogiera el objeto la dejaba
    imposible de completar. Este era el fallo."""

    @pytest.mark.parametrize("id_objeto", [ID_PELOTA_CUADRADA, ID_PELOTA_REDONDA])
    def test_se_va_con_su_pelota_sin_alumbrarlo(self, quico_acechando, id_objeto):
        resultado = resolver_arrojo([quico_acechando], id_objeto, iluminados=set())
        assert resultado.eliminado is quico_acechando
        assert not quico_acechando.esta_acechando()

    def test_acepta_lo_suyo_este_alumbrado_o_no(self, quico_acechando):
        assert quico_acechando.acepta_objeto(iluminado=False)
        assert quico_acechando.acepta_objeto(iluminado=True)

    def test_los_objetos_que_no_son_suyos_siguen_sin_servir(self, quico_acechando):
        """Que se pueda a oscuras no significa que valga cualquier cosa: la
        paleta es de La Chilindrina."""
        resultado = resolver_arrojo([quico_acechando], ID_PALETA, iluminados=set())
        assert resultado.eliminado is None
        assert quico_acechando.esta_acechando()


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


class TestArrojarObjetos:
    def test_la_pelota_cuadrada_ahuyenta_a_quico_si_esta_alumbrado(self, quico_acechando):
        resultado = resolver_arrojo(
            [quico_acechando], ID_PELOTA_CUADRADA, {nombres.QUICO}
        )
        assert resultado.eliminado is quico_acechando
        assert not quico_acechando.esta_acechando()

    def test_jaimico_a_oscuras_ignora_su_cafe(self):
        """A él sí hay que alumbrarlo: es su regla, y la luz no le hace daño,
        así que su contramedida sí se puede completar."""
        jaimico = llevar_a_acechar(crear(nombres.JAIMICO, nivel_ia=10))
        resultado = resolver_arrojo([jaimico], ID_CAFE_CHURRUMINO, set())
        assert resultado.eliminado is None
        assert jaimico.esta_acechando()

    def test_el_balero_se_lleva_al_chavo_sin_necesidad_de_luz(self, chavo_acechando):
        resultado = resolver_arrojo([chavo_acechando], ID_BALERO, set())
        assert resultado.eliminado is chavo_acechando

    def test_el_churrumino_solo_entretiene_al_chavo(self, chavo_acechando):
        margen = chavo_acechando.segundos_para_atacar
        resultado = resolver_arrojo([chavo_acechando], ID_CHURRUMINO, set())
        assert resultado.eliminado is None
        assert resultado.retrasado is chavo_acechando
        assert chavo_acechando.segundos_para_atacar == pytest.approx(
            margen + SEGUNDOS_RETRASO_CHURRUMINO
        )

    def test_el_churrumino_sin_el_chavo_delante_se_pierde(self, quico_acechando):
        resultado = resolver_arrojo([quico_acechando], ID_CHURRUMINO, set())
        assert not resultado.sirvio

    def test_arrojar_el_objeto_equivocado_no_sirve_de_nada(self, quico_acechando):
        resultado = resolver_arrojo(
            [quico_acechando], ID_CAFE_CHURRUMINO, {nombres.QUICO}
        )
        assert not resultado.sirvio
        assert quico_acechando.esta_acechando()

    def test_arrojar_sin_nadie_delante_no_falla(self):
        assert not resolver_arrojo([], ID_BALERO, set()).sirvio

    @pytest.mark.parametrize("id_objeto", OBJETOS_DEFENSIVOS)
    def test_clotilde_se_va_con_lo_que_haya_pedido(self, id_objeto):
        clotilde = llevar_a_acechar(crear(nombres.CLOTILDE, nivel_ia=10))
        clotilde.objeto_pedido = id_objeto
        resultado = resolver_arrojo([clotilde], id_objeto, set())
        assert resultado.eliminado is clotilde

    def test_clotilde_tiene_prioridad_sobre_el_resto(self, chavo_acechando):
        """Si pidió el balero, se lo lleva ella aunque El Chavo también caiga
        con ese objeto: va dirigido a quien lo pidió."""
        clotilde = llevar_a_acechar(crear(nombres.CLOTILDE, nivel_ia=10))
        clotilde.objeto_pedido = ID_BALERO
        resultado = resolver_arrojo([clotilde, chavo_acechando], ID_BALERO, set())
        assert resultado.eliminado is clotilde
        assert chavo_acechando.esta_acechando()
