"""Cara a cara con el jugador: quién acecha, a quién alumbra la linterna, a
quién le da un objeto arrojado y qué le hace."""

from dataclasses import replace

import pytest

from conftest import crear, llevar_a_acechar
from vecindad.config.jugabilidad import (
    ALTURA_TORSO,
    ARROJO_ACIERTO_SEMIALTO,
    ARROJO_ACIERTO_SEMIANCHO,
    LINTERNA_RADIO,
    SEGUNDOS_RETRASO_CHURRUMINO,
)
from vecindad.dominio.animatronicos import (
    ELENCO,
    NIVELES_POR_NOCHE,
    Animatronic,
    acechando_en,
    detectar_luz_mortal,
    detectar_luz_que_descarga,
    iluminados_en,
    nombres,
    objetivo_del_arrojo,
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

# El nivel más alto que alcanza alguien en las seis noches de la campaña.
NIVEL_MAS_ALTO_DE_CAMPANA = max(
    nivel for niveles in NIVELES_POR_NOCHE.values() for nivel in niveles.values()
)


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
        resultado = resolver_arrojo(chilindrina_acechando, id_objeto, iluminado=False)
        assert resultado.eliminado is chilindrina_acechando


class TestQuicoSeVaConLaPelota:
    """Su contramedida tiene que poder ejecutarse a oscuras: alumbrarlo es
    mortal, así que exigirle luz para que recogiera el objeto la dejaba
    imposible de completar. Este era el fallo."""

    @pytest.mark.parametrize("id_objeto", [ID_PELOTA_CUADRADA, ID_PELOTA_REDONDA])
    def test_se_va_con_su_pelota_sin_alumbrarlo(self, quico_acechando, id_objeto):
        resultado = resolver_arrojo(quico_acechando, id_objeto, iluminado=False)
        assert resultado.eliminado is quico_acechando
        assert not quico_acechando.esta_acechando()

    def test_acepta_lo_suyo_este_alumbrado_o_no(self, quico_acechando):
        assert quico_acechando.acepta_objeto(iluminado=False)
        assert quico_acechando.acepta_objeto(iluminado=True)

    def test_los_objetos_que_no_son_suyos_siguen_sin_servir(self, quico_acechando):
        """Que se pueda a oscuras no significa que valga cualquier cosa: la
        paleta es de La Chilindrina."""
        resultado = resolver_arrojo(quico_acechando, ID_PALETA, iluminado=False)
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
        resultado = resolver_arrojo(quico_acechando, ID_PELOTA_CUADRADA, iluminado=True)
        assert resultado.eliminado is quico_acechando
        assert not quico_acechando.esta_acechando()

    def test_jaimico_a_oscuras_ignora_su_cafe(self):
        """A él sí hay que alumbrarlo: es su regla, y la luz no le hace daño,
        así que su contramedida sí se puede completar."""
        jaimico = llevar_a_acechar(crear(nombres.JAIMICO, nivel_ia=10))
        resultado = resolver_arrojo(jaimico, ID_CAFE_CHURRUMINO, iluminado=False)
        assert resultado.eliminado is None
        assert jaimico.esta_acechando()

    def test_el_balero_se_lleva_al_chavo_sin_necesidad_de_luz(self, chavo_acechando):
        resultado = resolver_arrojo(chavo_acechando, ID_BALERO, iluminado=False)
        assert resultado.eliminado is chavo_acechando

    def test_el_churrumino_solo_entretiene_al_chavo(self, chavo_acechando):
        margen = chavo_acechando.segundos_para_atacar
        resultado = resolver_arrojo(chavo_acechando, ID_CHURRUMINO, iluminado=False)
        assert resultado.eliminado is None
        assert resultado.retrasado is chavo_acechando
        assert chavo_acechando.segundos_para_atacar == pytest.approx(
            margen + SEGUNDOS_RETRASO_CHURRUMINO
        )

    def test_el_churrumino_a_otro_que_no_sea_el_chavo_se_pierde(self, quico_acechando):
        resultado = resolver_arrojo(quico_acechando, ID_CHURRUMINO, iluminado=False)
        assert not resultado.sirvio
        assert resultado.alcanzado is quico_acechando

    def test_arrojar_el_objeto_equivocado_no_sirve_de_nada(self, quico_acechando):
        resultado = resolver_arrojo(quico_acechando, ID_CAFE_CHURRUMINO, iluminado=True)
        assert not resultado.sirvio
        assert quico_acechando.esta_acechando()

    def test_si_no_le_dio_a_nadie_no_pasa_nada(self):
        resultado = resolver_arrojo(None, ID_BALERO, iluminado=False)
        assert not resultado.sirvio
        assert resultado.alcanzado is None

    def test_a_jaimico_alumbrado_su_cafe_si_le_sirve(self):
        jaimico = llevar_a_acechar(crear(nombres.JAIMICO, nivel_ia=10))
        resultado = resolver_arrojo(jaimico, ID_CAFE_CHURRUMINO, iluminado=True)
        assert resultado.eliminado is jaimico

    @pytest.mark.parametrize("id_objeto", OBJETOS_DEFENSIVOS)
    def test_clotilde_se_va_con_lo_que_haya_pedido(self, id_objeto):
        clotilde = llevar_a_acechar(crear(nombres.CLOTILDE, nivel_ia=10))
        clotilde.objeto_pedido = id_objeto
        resultado = resolver_arrojo(clotilde, id_objeto, iluminado=False)
        assert resultado.eliminado is clotilde

    def test_a_clotilde_no_le_vale_otra_cosa(self):
        clotilde = llevar_a_acechar(crear(nombres.CLOTILDE, nivel_ia=10))
        clotilde.objeto_pedido = ID_PALETA
        resultado = resolver_arrojo(clotilde, ID_BALERO, iluminado=False)
        assert not resultado.sirvio
        assert clotilde.esta_acechando()


def _con_torso_en(configuracion, torso):
    """Copia de la ficha con el torso, visto desde el Barril, en ese punto."""
    puntos = dict(configuracion.puntos_acecho)
    puntos[POSICION_BARRIL] = (torso[0], torso[1] + ALTURA_TORSO)
    return replace(configuracion, puntos_acecho=puntos)


class TestPunteria:
    """El objeto va adonde apunta el ratón y solo le da a quien tenga el
    torso cerca. Ya no basta con pulsar el número correcto."""

    def test_apuntarle_al_torso_le_da(self, quico_acechando):
        torso = quico_acechando.punto_torso_en(POSICION_BARRIL)
        assert objetivo_del_arrojo([quico_acechando], POSICION_BARRIL, torso) is quico_acechando

    def test_justo_dentro_de_la_elipse_le_da(self, quico_acechando):
        x, y = quico_acechando.punto_torso_en(POSICION_BARRIL)
        semiancho, semialto = quico_acechando.semiejes_acierto()
        for borde in ((x + semiancho - 1, y), (x, y - semialto + 1), (x, y + semialto - 1)):
            assert objetivo_del_arrojo(
                [quico_acechando], POSICION_BARRIL, borde
            ) is quico_acechando, borde

    def test_fuera_de_la_elipse_falla(self, quico_acechando):
        x, y = quico_acechando.punto_torso_en(POSICION_BARRIL)
        semiancho, semialto = quico_acechando.semiejes_acierto()
        for lejos in ((x + semiancho + 1, y), (x, y - semialto - 1)):
            assert objetivo_del_arrojo([quico_acechando], POSICION_BARRIL, lejos) is None, lejos

    @pytest.mark.parametrize("config", ELENCO, ids=lambda c: c.nombre)
    def test_apuntarle_a_la_cara_le_da(self, config):
        """Este era el fallo: con un círculo de pecho, apuntar a la cara de
        La Chilindrina fallaba, y es donde el jugador apunta sin pensarlo.
        Se mide con el nivel más alto de la campaña."""
        llegado = llevar_a_acechar(Animatronic(config, nivel_ia=NIVEL_MAS_ALTO_DE_CAMPANA))
        for vista in (POSICION_BARRIL, POSICION_LAVADEROS):
            x, y = llegado.punto_torso_en(vista)
            cara = (x, y - int(ALTURA_TORSO * 0.6))
            assert objetivo_del_arrojo([llegado], vista, cara) is llegado, vista

    def test_sin_nadie_delante_no_le_da_a_nadie(self):
        assert objetivo_del_arrojo([], POSICION_BARRIL, (640, 360)) is None

    def test_a_quien_viene_de_camino_no_se_le_puede_dar(self):
        lejano = crear(nombres.QUICO, nivel_ia=10)
        torso = lejano.punto_torso_en(POSICION_BARRIL)
        assert objetivo_del_arrojo([lejano], POSICION_BARRIL, torso) is None

    def test_sin_punto_de_mira_no_le_da_a_nadie(self, quico_acechando):
        assert objetivo_del_arrojo([quico_acechando], POSICION_BARRIL, None) is None

    def test_se_apunta_igual_desde_los_lavaderos(self, quico_acechando):
        torso = quico_acechando.punto_torso_en(POSICION_LAVADEROS)
        assert objetivo_del_arrojo(
            [quico_acechando], POSICION_LAVADEROS, torso
        ) is quico_acechando

    def test_si_dos_se_pisan_le_da_al_mas_cercano(self, quico_acechando, chavo_acechando):
        """El objeto va a una sola persona: a la que se apuntó."""
        x, y = chavo_acechando.punto_torso_en(POSICION_BARRIL)
        quico_acechando.configuracion = _con_torso_en(
            quico_acechando.configuracion, (x + 40, y)
        )
        presentes = [quico_acechando, chavo_acechando]
        assert objetivo_del_arrojo(presentes, POSICION_BARRIL, (x, y)) is chavo_acechando
        assert objetivo_del_arrojo(presentes, POSICION_BARRIL, (x + 35, y)) is quico_acechando

    def test_a_nivel_alto_hay_que_afinar_mas(self):
        facil = crear(nombres.QUICO, nivel_ia=1)
        dificil = crear(nombres.QUICO, nivel_ia=20)
        assert facil.semiejes_acierto() == (ARROJO_ACIERTO_SEMIANCHO, ARROJO_ACIERTO_SEMIALTO)
        assert dificil.semiejes_acierto()[0] < ARROJO_ACIERTO_SEMIANCHO
        assert dificil.semiejes_acierto()[1] < ARROJO_ACIERTO_SEMIALTO

    def test_tirarle_al_que_no_era_no_alcanza_al_de_atras(self, quico_acechando):
        """Si el tiro le cae a quien no le sirve, se pierde: no rebota hacia
        quien sí lo necesitaba."""
        chilindrina = llevar_a_acechar(crear(nombres.CHILINDRINA, nivel_ia=10))
        torso_quico = quico_acechando.punto_torso_en(POSICION_BARRIL)
        alcanzado = objetivo_del_arrojo(
            [quico_acechando, chilindrina], POSICION_BARRIL, torso_quico
        )
        resultado = resolver_arrojo(alcanzado, ID_PALETA, iluminado=False)
        assert alcanzado is quico_acechando
        assert not resultado.sirvio
        assert chilindrina.esta_acechando()
