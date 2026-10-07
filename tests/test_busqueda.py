"""Doña Clotilde, Jaimico y El Chavo aparecen según su nivel, y a los dos
primeros se les quita de encima encontrando su objeto en las cámaras."""

import random
from unittest.mock import patch

import pytest

from conftest import crear, ficha_de, llevar_a_acechar
from vecindad.config.jugabilidad import (
    BUSQUEDA_SEGUNDOS_MINIMOS,
    OBJETO_BUSCADO_RADIO_CLIC,
    PUNTO_DEBIL_FACTOR_MAS_DIFICIL,
    PUNTO_DEBIL_RADIO,
    SITIOS_OBJETOS_BUSCADOS,
)
from vecindad.config.partida import NIVEL_IA_MAXIMO, NIVEL_IA_MINIMO
from vecindad.dominio.animatronicos import NIVELES_POR_NOCHE, nombres
from vecindad.dominio.busqueda import (
    CAMARAS_CON_OBJETOS,
    BusquedasEnCamaras,
    Desenlace,
    segundos_para_buscar,
)
from vecindad.mundo.habitaciones import (
    HABITACION_JUGADOR,
    HABITACIONES,
    distancia_al_jugador,
)

FOTOGRAMA = 1.0 / 60.0

# Las que dan al Primer Patio y las del Segundo Patio.
CERCANAS = ("entrada", "casa_jaimito", "casa_clotilde", "casa_florinda", "casa_ramon", "segundo_patio")
LEJANAS = ("casa_paty", "casa_godinez", "casa_popis", "casa_chavo")


def _busquedas(semilla=1):
    return BusquedasEnCamaras(azar=random.Random(semilla))


def _aparecida(nombre, camara=None, nivel_ia=10):
    animatronic = crear(nombre, nivel_ia=nivel_ia)
    animatronic.habitacion_actual = camara or animatronic.configuracion.aparece_en[0]
    return animatronic


def _aparecer_seguro(animatronic):
    """Una ronda con el dado y la probabilidad de aparición a favor."""
    with patch("vecindad.dominio.animatronicos.entidad.random.random", return_value=0.0):
        animatronic.actualizar()
    return animatronic


def _correr(busquedas, animatronics, segundos):
    agotadas = []
    for _ in range(round(segundos / FOTOGRAMA)):
        agotadas += busquedas.actualizar(FOTOGRAMA, animatronics).agotadas
    return agotadas


class TestAparecer:
    @pytest.mark.parametrize("nombre", [nombres.CHAVO, nombres.JAIMICO, nombres.CLOTILDE])
    def test_empiezan_sin_estar_en_ninguna_camara(self, nombre):
        animatronic = crear(nombre, nivel_ia=10)
        assert not animatronic.presente
        assert not animatronic.esta_acechando()

    @pytest.mark.parametrize("nombre", [nombres.CHAVO, nombres.JAIMICO, nombres.CLOTILDE])
    def test_con_todo_a_favor_aparece_en_la_primera_ronda(self, nombre):
        animatronic = _aparecer_seguro(crear(nombre, nivel_ia=NIVEL_IA_MAXIMO))
        assert animatronic.habitacion_actual in animatronic.configuracion.aparece_en

    def test_el_nivel_decide_lo_probable_que_es(self):
        """Con el dado cargado en contra no aparece; a favor, sí."""
        bruja = crear(nombres.CLOTILDE, nivel_ia=5)
        with patch("vecindad.dominio.animatronicos.entidad.random.random", return_value=0.0):
            with patch("vecindad.dominio.animatronicos.entidad.random.randint", return_value=6):
                bruja.actualizar()
            assert not bruja.presente
            with patch("vecindad.dominio.animatronicos.entidad.random.randint", return_value=5):
                bruja.actualizar()
        assert bruja.presente

    @pytest.mark.parametrize("nombre", [nombres.JAIMICO, nombres.CLOTILDE])
    def test_su_probabilidad_espacia_las_apariciones(self, nombre):
        """Aun con el dado a favor, no aparecen en cada ronda: si no, la
        bruja estaría encima casi toda la noche."""
        probabilidad = crear(nombre).configuracion.probabilidad_aparicion
        assert 0.0 < probabilidad < 1.0
        with patch("vecindad.dominio.animatronicos.entidad.random.random", return_value=probabilidad):
            animatronic = crear(nombre, nivel_ia=NIVEL_IA_MAXIMO)
            animatronic.actualizar()
        assert not animatronic.presente

    def test_el_chavo_usa_el_dado_tal_cual(self):
        assert crear(nombres.CHAVO).configuracion.probabilidad_aparicion == 1.0
        chavo = crear(nombres.CHAVO, nivel_ia=NIVEL_IA_MAXIMO)
        chavo.actualizar()
        assert chavo.presente

    def test_jaimico_solo_aparece_en_su_casa(self):
        for _ in range(30):
            jaimico = _aparecer_seguro(crear(nombres.JAIMICO, nivel_ia=NIVEL_IA_MAXIMO))
            assert jaimico.habitacion_actual == "casa_jaimito"

    def test_la_bruja_aparece_en_cualquier_camara_menos_el_patio(self):
        vistas = set()
        for _ in range(400):
            bruja = _aparecer_seguro(crear(nombres.CLOTILDE, nivel_ia=NIVEL_IA_MAXIMO))
            vistas.add(bruja.habitacion_actual)
        assert vistas == set(HABITACIONES) - {HABITACION_JUGADOR}

    def test_una_vez_ahi_ni_la_bruja_ni_jaimico_se_mueven(self):
        for nombre in (nombres.CLOTILDE, nombres.JAIMICO):
            animatronic = _aparecida(nombre, nivel_ia=NIVEL_IA_MAXIMO)
            antes = animatronic.habitacion_actual
            for _ in range(30):
                animatronic.actualizar()
            assert animatronic.habitacion_actual == antes

    def test_el_chavo_aparecido_sigue_deambulando(self):
        chavo = _aparecida(nombres.CHAVO, "casa_paty", nivel_ia=NIVEL_IA_MAXIMO)
        chavo.actualizar()
        assert chavo.habitacion_actual not in (None, "casa_paty", HABITACION_JUGADOR)

    @pytest.mark.parametrize("nombre", [nombres.CHAVO, nombres.JAIMICO])
    def test_al_espantarlo_desaparece(self, nombre):
        animatronic = llevar_a_acechar(crear(nombre, nivel_ia=10))
        animatronic.ahuyentar()
        assert not animatronic.presente

    def test_un_inactivo_nunca_aparece(self):
        bruja = crear(nombres.CLOTILDE, nivel_ia=NIVEL_IA_MINIMO)
        for _ in range(50):
            bruja.actualizar()
        assert not bruja.presente


class TestDistancia:
    @pytest.mark.parametrize("camara", CERCANAS)
    def test_las_que_dan_al_patio_estan_a_un_paso(self, camara):
        assert distancia_al_jugador(camara) == 1

    @pytest.mark.parametrize("camara", LEJANAS)
    def test_las_del_segundo_patio_estan_a_dos(self, camara):
        assert distancia_al_jugador(camara) == 2

    def test_una_habitacion_inventada_falla(self):
        with pytest.raises(ValueError):
            distancia_al_jugador("la_luna")


class TestTiempoParaBuscar:
    @pytest.mark.parametrize("camara", CERCANAS)
    def test_la_bruja_cerca_da_el_minimo(self, camara):
        assert segundos_para_buscar(_aparecida(nombres.CLOTILDE, camara)) == BUSQUEDA_SEGUNDOS_MINIMOS

    @pytest.mark.parametrize("camara", LEJANAS)
    def test_la_bruja_lejos_da_mas(self, camara):
        assert segundos_para_buscar(_aparecida(nombres.CLOTILDE, camara)) > BUSQUEDA_SEGUNDOS_MINIMOS

    def test_nunca_menos_de_diez_segundos_con_la_bruja(self):
        for camara in CERCANAS + LEJANAS:
            for nivel in (1, 10, NIVEL_IA_MAXIMO):
                bruja = _aparecida(nombres.CLOTILDE, camara, nivel_ia=nivel)
                assert segundos_para_buscar(bruja) >= 10.0

    def test_jaimico_con_nivel_maximo_da_siete_segundos(self):
        jaimico = _aparecida(nombres.JAIMICO, nivel_ia=NIVEL_IA_MAXIMO)
        assert segundos_para_buscar(jaimico) == pytest.approx(7.0)

    def test_a_jaimico_con_menos_nivel_hay_mas_tiempo(self):
        lento = segundos_para_buscar(_aparecida(nombres.JAIMICO, nivel_ia=1))
        rapido = segundos_para_buscar(_aparecida(nombres.JAIMICO, nivel_ia=NIVEL_IA_MAXIMO))
        assert lento > rapido


class TestEsconderElObjeto:
    def test_al_aparecer_esconde_su_objeto(self):
        busquedas = _busquedas()
        bruja = _aparecida(nombres.CLOTILDE)
        resultado = busquedas.actualizar(FOTOGRAMA, [bruja])
        assert resultado.empezadas == [bruja]
        (busqueda,) = busquedas.activas
        assert busqueda.id_objeto == "escoba"
        assert busqueda.camara in CAMARAS_CON_OBJETOS
        assert busqueda.punto in SITIOS_OBJETOS_BUSCADOS

    def test_el_de_jaimico_es_el_cafe(self):
        busquedas = _busquedas()
        busquedas.actualizar(FOTOGRAMA, [_aparecida(nombres.JAIMICO)])
        assert busquedas.activas[0].id_objeto == "cafe"

    def test_nunca_queda_en_la_camara_del_chavo(self):
        assert "casa_chavo" not in CAMARAS_CON_OBJETOS
        busquedas = _busquedas(7)
        for _ in range(300):
            busquedas.reiniciar()
            busquedas.actualizar(FOTOGRAMA, [_aparecida(nombres.CLOTILDE)])
            assert busquedas.activas[0].camara != "casa_chavo"

    def test_puede_quedar_en_cualquier_otra(self):
        busquedas = _busquedas(3)
        camaras = set()
        for _ in range(500):
            busquedas.reiniciar()
            busquedas.actualizar(FOTOGRAMA, [_aparecida(nombres.CLOTILDE)])
            camaras.add(busquedas.activas[0].camara)
        assert camaras == set(HABITACIONES) - {"casa_chavo"}

    def test_sin_aparecer_no_hay_nada_que_buscar(self):
        busquedas = _busquedas()
        busquedas.actualizar(FOTOGRAMA, [crear(nombres.CLOTILDE, nivel_ia=10)])
        assert busquedas.activas == []
        assert busquedas.inminencia() is None

    def test_los_demas_no_esconden_nada(self):
        busquedas = _busquedas()
        quico = crear(nombres.QUICO, nivel_ia=10)
        chavo = _aparecida(nombres.CHAVO)
        busquedas.actualizar(FOTOGRAMA, [quico, chavo])
        assert busquedas.activas == []

    def test_dos_objetos_en_la_misma_camara_no_se_tapan(self):
        busquedas = BusquedasEnCamaras(azar=random.Random(1))
        with patch.object(busquedas._azar, "choice", side_effect=lambda opciones: opciones[0]):
            busquedas.actualizar(
                FOTOGRAMA, [_aparecida(nombres.CLOTILDE), _aparecida(nombres.JAIMICO)]
            )
        escoba, cafe = busquedas.activas
        assert escoba.camara == cafe.camara
        assert escoba.punto != cafe.punto

    def test_la_inminencia_sube_con_el_tiempo(self):
        busquedas = _busquedas()
        bruja = _aparecida(nombres.CLOTILDE, "entrada")
        busquedas.actualizar(FOTOGRAMA, [bruja])
        assert busquedas.inminencia() == pytest.approx(0.0)
        _correr(busquedas, [bruja], BUSQUEDA_SEGUNDOS_MINIMOS / 2)
        assert busquedas.inminencia() == pytest.approx(0.5, abs=0.02)


class TestSeAcabaElTiempo:
    def test_la_bruja_mata(self):
        busquedas = _busquedas()
        bruja = _aparecida(nombres.CLOTILDE, "entrada")
        busquedas.actualizar(FOTOGRAMA, [bruja])
        agotadas = _correr(busquedas, [bruja], BUSQUEDA_SEGUNDOS_MINIMOS + 0.1)
        assert agotadas == [(bruja, Desenlace.MATA)]

    def test_no_antes_de_tiempo(self):
        busquedas = _busquedas()
        bruja = _aparecida(nombres.CLOTILDE, "entrada")
        busquedas.actualizar(FOTOGRAMA, [bruja])
        assert _correr(busquedas, [bruja], BUSQUEDA_SEGUNDOS_MINIMOS - 0.2) == []

    def test_jaimico_irrumpe(self):
        busquedas = _busquedas()
        jaimico = _aparecida(nombres.JAIMICO, nivel_ia=NIVEL_IA_MAXIMO)
        busquedas.actualizar(FOTOGRAMA, [jaimico])
        agotadas = _correr(busquedas, [jaimico], 7.1)
        assert agotadas == [(jaimico, Desenlace.IRRUMPE)]

    def test_si_su_dueno_se_va_la_busqueda_se_cierra(self):
        busquedas = _busquedas()
        jaimico = _aparecida(nombres.JAIMICO)
        busquedas.actualizar(FOTOGRAMA, [jaimico])
        jaimico.desaparecer()
        busquedas.actualizar(FOTOGRAMA, [jaimico])
        assert busquedas.activas == []

    def test_con_jaimico_en_el_patio_ya_no_se_busca(self):
        busquedas = _busquedas()
        jaimico = _aparecida(nombres.JAIMICO)
        busquedas.actualizar(FOTOGRAMA, [jaimico])
        jaimico.irrumpir()
        busquedas.actualizar(FOTOGRAMA, [jaimico])
        assert busquedas.activas == []


class TestEncontrarlo:
    @pytest.fixture
    def escondida(self):
        busquedas = _busquedas()
        bruja = _aparecida(nombres.CLOTILDE)
        busquedas.actualizar(FOTOGRAMA, [bruja])
        return busquedas, bruja, busquedas.activas[0]

    def test_clic_encima_lo_encuentra(self, escondida):
        busquedas, _, busqueda = escondida
        assert busquedas.objeto_en(busqueda.camara, busqueda.punto) is busqueda

    def test_clic_al_borde_tambien(self, escondida):
        busquedas, _, busqueda = escondida
        x, y = busqueda.punto
        assert busquedas.objeto_en(busqueda.camara, (x + OBJETO_BUSCADO_RADIO_CLIC, y)) is busqueda

    def test_clic_lejos_no(self, escondida):
        busquedas, _, busqueda = escondida
        x, y = busqueda.punto
        assert busquedas.objeto_en(busqueda.camara, (x + OBJETO_BUSCADO_RADIO_CLIC + 5, y)) is None

    def test_en_otra_camara_no_esta(self, escondida):
        busquedas, _, busqueda = escondida
        otra = next(c for c in CAMARAS_CON_OBJETOS if c != busqueda.camara)
        assert busquedas.objeto_en(otra, busqueda.punto) is None

    def test_encontrarlo_hace_desaparecer_a_su_duena(self, escondida):
        busquedas, bruja, busqueda = escondida
        assert busquedas.encontrar(busqueda, [bruja])
        assert not bruja.presente
        assert busquedas.activas == []

    def test_no_se_encuentra_dos_veces(self, escondida):
        busquedas, bruja, busqueda = escondida
        busquedas.encontrar(busqueda, [bruja])
        assert not busquedas.encontrar(busqueda, [bruja])


def _los_demas_en_campana():
    """Todo el que se espanta con la luz, con cada nivel que tiene en las
    seis noches de la campaña."""
    return [
        crear(nombre, nivel_ia=nivel)
        for niveles in NIVELES_POR_NOCHE.values()
        for nombre, nivel in niveles.items()
        if nivel > 0 and nombre != nombres.JAIMICO and ficha_de(nombre).se_espanta_con_luz
    ]


class TestJaimicoEsElMasDificilDeEspantar:
    def test_su_punto_debil_es_el_mas_chico_de_la_campana(self):
        jaimico = crear(nombres.JAIMICO, nivel_ia=1)
        assert all(
            jaimico.radio_punto_debil() < otro.radio_punto_debil()
            for otro in _los_demas_en_campana()
        )

    def test_hay_que_sostenerlo_mas_que_a_cualquiera_de_la_campana(self):
        jaimico = crear(nombres.JAIMICO, nivel_ia=1)
        assert all(
            jaimico.segundos_para_espantar() > otro.segundos_para_espantar()
            for otro in _los_demas_en_campana()
        )

    def test_su_punto_es_el_mas_rapido_de_la_campana(self):
        jaimico = crear(nombres.JAIMICO, nivel_ia=1)
        assert all(
            jaimico.velocidad_punto_debil() > otro.velocidad_punto_debil()
            for otro in _los_demas_en_campana()
        )

    def test_pero_no_es_imposible(self):
        """Por encima de la mitad de la escala el punto corre más de lo que
        se tarda en reaccionar: ahí ya no es difícil, es imposible."""
        assert PUNTO_DEBIL_FACTOR_MAS_DIFICIL <= 0.5

    def test_no_depende_de_su_nivel(self):
        bajo = crear(nombres.JAIMICO, nivel_ia=1)
        alto = crear(nombres.JAIMICO, nivel_ia=NIVEL_IA_MAXIMO)
        assert bajo.radio_punto_debil() == alto.radio_punto_debil()

    def test_los_demas_siguen_escalando_con_su_nivel(self):
        quico = crear(nombres.QUICO, nivel_ia=1)
        assert quico.radio_punto_debil() == PUNTO_DEBIL_RADIO[0]


class TestLaChilindrinaSeEspantaComoLosDemas:
    """Tiene nivel 12-13 desde la noche 1 para que su recorrido largo le dé
    para llegar; si su punto débil usara ese nivel entero sería casi
    imposible de seguir. Cuenta solo una parte."""

    def test_su_punto_no_usa_su_nivel_entero(self):
        chilindrina = crear(nombres.CHILINDRINA, nivel_ia=12)
        quico_igual = crear(nombres.QUICO, nivel_ia=12)
        assert chilindrina.radio_punto_debil() > quico_igual.radio_punto_debil()
        assert chilindrina.segundos_para_espantar() < quico_igual.segundos_para_espantar()

    def test_en_la_noche_6_no_es_mas_dificil_que_el_chavo(self):
        chilindrina = crear(nombres.CHILINDRINA, nivel_ia=NIVELES_POR_NOCHE[6][nombres.CHILINDRINA])
        chavo = crear(nombres.CHAVO, nivel_ia=NIVELES_POR_NOCHE[6][nombres.CHAVO])
        assert chilindrina.radio_punto_debil() >= chavo.radio_punto_debil()
        assert chilindrina.velocidad_punto_debil() <= chavo.velocidad_punto_debil()

    def test_sigue_castigando_fallar(self):
        assert ficha_de(nombres.CHILINDRINA).luz_descarga_linterna
