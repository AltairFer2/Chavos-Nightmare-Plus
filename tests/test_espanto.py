"""Espantar con la luz: sostener el centro del haz sobre el punto débil de
quien acecha hasta llenar su barra."""

import math
import random

import pytest

from conftest import crear, llevar_a_acechar
from vecindad.config.jugabilidad import (
    CHILINDRINA_GRACIA_SEGUNDOS,
    PUNTO_DEBIL_DRENADO,
    PUNTO_DEBIL_RADIO,
    PUNTO_DEBIL_SEGUNDOS,
    PUNTO_DEBIL_SEMIALTO,
    PUNTO_DEBIL_SEMIANCHO,
    PUNTO_DEBIL_VELOCIDAD,
)
from vecindad.dominio.animatronicos import (
    ELENCO,
    NIVELES_POR_NOCHE,
    Espanto,
    nombres,
    se_espanta,
)
from vecindad.mundo.posiciones import POSICION_BARRIL, POSICION_LAVADEROS

FOTOGRAMA = 1.0 / 60.0

# Doña Clotilde ya no: nunca llega al patio (se le busca la escoba).
SE_ESPANTAN = (
    nombres.QUICO, nombres.CHILINDRINA, nombres.CHAVO, nombres.JAIMICO,
)

# El nivel más alto que alcanza alguien en las seis noches de la campaña.
NIVEL_MAS_ALTO_DE_CAMPANA = max(
    nivel for niveles in NIVELES_POR_NOCHE.values() for nivel in niveles.values()
)


def _acechando(nombre, nivel_ia=10):
    return llevar_a_acechar(crear(nombre, nivel_ia=nivel_ia))


def _espanto(semilla=1):
    return Espanto(azar=random.Random(semilla))


def _paso(espanto, presentes, punto_luz, alumbrando=True, vista=POSICION_BARRIL):
    return espanto.actualizar(FOTOGRAMA, presentes, vista, punto_luz, alumbrando)


def _sostener(espanto, animatronic, segundos, vista=POSICION_BARRIL):
    """Un pulso perfecto: el cursor va siempre encima del punto. Devuelve el
    resultado del fotograma en que lo espantó, o None si no le alcanzó."""
    _paso(espanto, [animatronic], None, alumbrando=False, vista=vista)
    for _ in range(round(segundos / FOTOGRAMA)):
        punto = espanto.punto_de(animatronic, vista)
        resultado = _paso(espanto, [animatronic], punto, vista=vista)
        if resultado.espantados:
            return resultado
    return None


def _desplazamiento(espanto, animatronic, vista=POSICION_BARRIL):
    x, y = espanto.punto_de(animatronic, vista)
    torso_x, torso_y = animatronic.punto_torso_en(vista)
    return x - torso_x, y - torso_y


class TestQuienSeEspanta:
    def test_todos_menos_don_ramon_dona_florinda_y_la_bruja(self):
        assert {c.nombre for c in ELENCO if c.se_espanta_con_luz} == set(SE_ESPANTAN)

    def test_a_quien_mata_la_luz_no_se_le_espanta(self):
        """Don Ramón se va con el Sr. Barriga y Doña Florinda con el audio."""
        for config in ELENCO:
            assert not (config.luz_mortal and config.se_espanta_con_luz), config.nombre

    def test_don_ramon_no_tiene_punto_debil(self):
        espanto = _espanto()
        ramon = _acechando(nombres.DON_RAMON)
        _paso(espanto, [ramon], None)
        assert espanto.punto_de(ramon, POSICION_BARRIL) is None
        assert not se_espanta(ramon)

    def test_quien_viene_de_camino_no_tiene_punto_debil(self):
        espanto = _espanto()
        lejano = crear(nombres.QUICO, nivel_ia=10)
        _paso(espanto, [lejano], None)
        assert espanto.punto_de(lejano, POSICION_BARRIL) is None


class TestElPuntoDebil:
    @pytest.mark.parametrize("nombre", SE_ESPANTAN)
    def test_aparece_en_las_dos_vistas(self, nombre):
        espanto = _espanto()
        llegado = _acechando(nombre)
        for vista in (POSICION_BARRIL, POSICION_LAVADEROS):
            _paso(espanto, [llegado], None, vista=vista)
            assert espanto.punto_de(llegado, vista) is not None, vista

    def test_nunca_se_sale_del_cuerpo(self):
        espanto = _espanto(4)
        quico = _acechando(nombres.QUICO, nivel_ia=20)
        for _ in range(3000):
            _paso(espanto, [quico], None)
            dx, dy = _desplazamiento(espanto, quico)
            # Margen de un píxel por el redondeo a coordenadas del lienzo.
            assert (dx / (PUNTO_DEBIL_SEMIANCHO + 1)) ** 2 + (dy / (PUNTO_DEBIL_SEMIALTO + 1)) ** 2 <= 1

    def test_se_mueve_y_cambia_de_rumbo(self):
        espanto = _espanto(2)
        quico = _acechando(nombres.QUICO)
        xs = []
        for _ in range(600):
            _paso(espanto, [quico], None)
            xs.append(_desplazamiento(espanto, quico)[0])
        assert len(set(xs)) > 50
        subidas = sum(1 for a, b in zip(xs, xs[1:]) if b > a)
        bajadas = sum(1 for a, b in zip(xs, xs[1:]) if b < a)
        assert subidas > 30 and bajadas > 30

    def test_no_corre_mas_que_su_velocidad(self):
        espanto = _espanto(3)
        quico = _acechando(nombres.QUICO, nivel_ia=20)
        _paso(espanto, [quico], None)
        anterior = _desplazamiento(espanto, quico)
        for _ in range(600):
            _paso(espanto, [quico], None)
            actual = _desplazamiento(espanto, quico)
            assert math.dist(anterior, actual) <= quico.velocidad_punto_debil() * FOTOGRAMA + 2
            anterior = actual


class TestSostenerlo:
    @pytest.mark.parametrize("nombre", SE_ESPANTAN)
    def test_sostenerlo_lo_espanta(self, nombre):
        espanto = _espanto()
        llegado = _acechando(nombre)
        resultado = _sostener(espanto, llegado, llegado.segundos_para_espantar() + 0.1)
        assert resultado is not None
        assert resultado.espantados == [llegado]
        assert not llegado.esta_acechando()

    def test_no_se_espanta_antes_de_tiempo(self):
        espanto = _espanto()
        quico = _acechando(nombres.QUICO)
        assert _sostener(espanto, quico, quico.segundos_para_espantar() - 0.1) is None
        assert quico.esta_acechando()

    def test_desde_los_lavaderos_tambien(self):
        espanto = _espanto()
        quico = _acechando(nombres.QUICO)
        resultado = _sostener(
            espanto, quico, quico.segundos_para_espantar() + 0.1, vista=POSICION_LAVADEROS
        )
        assert resultado is not None

    def test_a_oscuras_no_suma(self):
        espanto = _espanto()
        quico = _acechando(nombres.QUICO)
        _paso(espanto, [quico], None)
        for _ in range(300):
            punto = espanto.punto_de(quico, POSICION_BARRIL)
            _paso(espanto, [quico], punto, alumbrando=False)
        assert espanto.progreso_de(quico) == 0.0
        assert quico.esta_acechando()

    def test_apuntarle_lejos_no_suma(self):
        espanto = _espanto()
        quico = _acechando(nombres.QUICO)
        x, y = quico.punto_torso_en(POSICION_BARRIL)
        for _ in range(300):
            _paso(espanto, [quico], (x + 400, y))
        assert espanto.progreso_de(quico) == 0.0

    def test_perderlo_vacia_la_barra_poco_a_poco(self):
        """No la reinicia: recuperarlo enseguida no lo deja en cero."""
        espanto = _espanto()
        quico = _acechando(nombres.QUICO)
        _sostener(espanto, quico, quico.segundos_para_espantar() / 2)
        lleno = espanto.progreso_de(quico)
        x, y = quico.punto_torso_en(POSICION_BARRIL)
        for _ in range(30):
            _paso(espanto, [quico], (x + 400, y))
        assert espanto.progreso_de(quico) == pytest.approx(lleno - PUNTO_DEBIL_DRENADO * 0.5)

    def test_si_se_va_se_olvida_lo_sostenido(self):
        espanto = _espanto()
        quico = _acechando(nombres.QUICO)
        _sostener(espanto, quico, quico.segundos_para_espantar() / 2)
        _paso(espanto, [], None)
        assert espanto.progreso_de(quico) == 0.0

    def test_con_dos_delante_cada_uno_lleva_su_barra(self):
        espanto = _espanto()
        quico = _acechando(nombres.QUICO)
        chavo = _acechando(nombres.CHAVO)
        presentes = [quico, chavo]
        _paso(espanto, presentes, None, alumbrando=False)
        for _ in range(60):
            _paso(espanto, presentes, espanto.punto_de(quico, POSICION_BARRIL))
        assert espanto.progreso_de(quico) > 0.0
        assert espanto.progreso_de(chavo) == 0.0


class TestElNivelLoEndurece:
    def test_extremos_de_la_configuracion(self):
        facil = crear(nombres.QUICO, nivel_ia=1)
        dificil = crear(nombres.QUICO, nivel_ia=20)
        assert facil.radio_punto_debil() == PUNTO_DEBIL_RADIO[0]
        assert dificil.radio_punto_debil() == PUNTO_DEBIL_RADIO[1]
        assert facil.segundos_para_espantar() == PUNTO_DEBIL_SEGUNDOS[0]
        assert dificil.segundos_para_espantar() == PUNTO_DEBIL_SEGUNDOS[1]
        assert facil.velocidad_punto_debil() == PUNTO_DEBIL_VELOCIDAD[0]
        assert dificil.velocidad_punto_debil() == PUNTO_DEBIL_VELOCIDAD[1]

    def test_a_mas_nivel_mas_dificil(self):
        facil = crear(nombres.QUICO, nivel_ia=3)
        dificil = crear(nombres.QUICO, nivel_ia=15)
        assert dificil.radio_punto_debil() < facil.radio_punto_debil()
        assert dificil.segundos_para_espantar() > facil.segundos_para_espantar()
        assert dificil.velocidad_punto_debil() > facil.velocidad_punto_debil()
        assert dificil.cambio_punto_debil()[1] < facil.cambio_punto_debil()[1]


class TestSeLePuedeGanar:
    """Que sea difícil no puede querer decir imposible: un jugador con un
    retraso de reacción humano (0,1 s) tiene que poder espantar al nivel más
    alto de la campaña, aunque tarde más que el tiempo justo."""

    RETRASO_FOTOGRAMAS = 6

    @pytest.mark.parametrize("semilla", range(5))
    def test_con_reaccion_humana_se_logra(self, semilla):
        espanto = _espanto(semilla)
        llegado = _acechando(nombres.CHILINDRINA, nivel_ia=NIVEL_MAS_ALTO_DE_CAMPANA)
        _paso(espanto, [llegado], None, alumbrando=False)
        vistos = []
        tope = round(llegado.segundos_para_espantar() * 3 / FOTOGRAMA)
        for _ in range(tope):
            vistos.append(espanto.punto_de(llegado, POSICION_BARRIL))
            # Apunta adonde estaba el punto hace RETRASO_FOTOGRAMAS.
            apunta = vistos[max(0, len(vistos) - 1 - self.RETRASO_FOTOGRAMAS)]
            if _paso(espanto, [llegado], apunta).espantados:
                return
        pytest.fail("con reacción humana no se le pudo espantar")


def _sobre_el_cuerpo_lejos_del_punto(espanto, animatronic):
    """Un punto de su cuerpo (dentro de su radio de reacción) a más de 80 px
    del punto débil: de tres puntos en fila separados 80 px, el más lejano
    siempre lo está."""
    x, y = animatronic.punto_torso_en(POSICION_BARRIL)
    punto = espanto.punto_de(animatronic, POSICION_BARRIL)
    candidatos = ((x, y - 80), (x, y), (x, y + 80))
    return max(candidatos, key=lambda candidato: math.dist(candidato, punto))


class TestLaChilindrinaCastigaFallar:
    def test_alumbrarle_el_cuerpo_fuera_del_punto_descarga_la_bateria(self):
        espanto = _espanto()
        chilindrina = _acechando(nombres.CHILINDRINA)
        assert chilindrina.radio_peligro() > 80
        _paso(espanto, [chilindrina], None, alumbrando=False)
        descargo = False
        for _ in range(round((CHILINDRINA_GRACIA_SEGUNDOS + 0.1) / FOTOGRAMA)):
            fuera = _sobre_el_cuerpo_lejos_del_punto(espanto, chilindrina)
            descargo = descargo or _paso(espanto, [chilindrina], fuera).descarga
        assert descargo

    def test_un_roce_corto_se_perdona(self):
        espanto = _espanto()
        chilindrina = _acechando(nombres.CHILINDRINA)
        _paso(espanto, [chilindrina], None, alumbrando=False)
        for _ in range(round((CHILINDRINA_GRACIA_SEGUNDOS - 0.2) / FOTOGRAMA)):
            fuera = _sobre_el_cuerpo_lejos_del_punto(espanto, chilindrina)
            assert not _paso(espanto, [chilindrina], fuera).descarga

    def test_recuperar_el_punto_reinicia_la_gracia(self):
        espanto = _espanto()
        chilindrina = _acechando(nombres.CHILINDRINA)
        _paso(espanto, [chilindrina], None, alumbrando=False)
        for _ in range(4):
            for _ in range(round((CHILINDRINA_GRACIA_SEGUNDOS - 0.2) / FOTOGRAMA)):
                fuera = _sobre_el_cuerpo_lejos_del_punto(espanto, chilindrina)
                assert not _paso(espanto, [chilindrina], fuera).descarga
            _paso(espanto, [chilindrina], espanto.punto_de(chilindrina, POSICION_BARRIL))

    def test_sobre_el_punto_nunca_descarga(self):
        espanto = _espanto()
        chilindrina = _acechando(nombres.CHILINDRINA)
        _paso(espanto, [chilindrina], None, alumbrando=False)
        for _ in range(round(chilindrina.segundos_para_espantar() / FOTOGRAMA) - 1):
            punto = espanto.punto_de(chilindrina, POSICION_BARRIL)
            assert not _paso(espanto, [chilindrina], punto).descarga

    def test_lejos_de_ella_no_descarga(self):
        espanto = _espanto()
        chilindrina = _acechando(nombres.CHILINDRINA)
        x, y = chilindrina.punto_torso_en(POSICION_BARRIL)
        for _ in range(120):
            assert not _paso(espanto, [chilindrina], (x + 500, y)).descarga

    def test_a_los_demas_fallarles_no_les_cuesta_la_bateria(self):
        espanto = _espanto()
        quico = _acechando(nombres.QUICO)
        _paso(espanto, [quico], None, alumbrando=False)
        for _ in range(120):
            fuera = _sobre_el_cuerpo_lejos_del_punto(espanto, quico)
            assert not _paso(espanto, [quico], fuera).descarga
