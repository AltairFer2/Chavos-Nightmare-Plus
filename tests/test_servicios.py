"""Los cuatro servicios del barril y el audio que se dispara desde el monitor.

Ojo con el reparto: el panel del barril **repone** las reproducciones del
audio de Quico (Servicio.REPONER_AUDIO) y el botón del monitor las **gasta**
(ServiciosUtilidad.sonar_audio). Son dos cosas distintas.
"""

import pytest

from conftest import crear, llevar_a_acechar
from vecindad.config.jugabilidad import (
    BARRIGA_COOLDOWN_SEGUNDOS,
    NOCHE_AUDIO_LIMITADO,
    SERVICIO_CAMARAS_SEGUNDOS,
)
from vecindad.dominio.animatronicos import nombres
from vecindad.dominio.servicios import (
    Resultado,
    Servicio,
    ServiciosUtilidad,
    usos_de_audio,
)

# Reproducciones con las que arranca la noche de las pruebas.
USOS = usos_de_audio(NOCHE_AUDIO_LIMITADO)


@pytest.fixture
def servicios():
    """Noche 2 en adelante: el audio de Quico ya tiene usos contados."""
    return ServiciosUtilidad(numero_noche=NOCHE_AUDIO_LIMITADO)


@pytest.fixture
def ramon():
    return llevar_a_acechar(crear(nombres.DON_RAMON, nivel_ia=10))


@pytest.fixture
def florinda():
    """A media ruta, que es donde el audio le hace efecto: no la manda a su
    casa, le quita una cámara de terreno."""
    florinda = crear(nombres.FLORINDA, nivel_ia=10)
    florinda.habitacion_actual = "casa_popis"
    return florinda


class TestSenorBarriga:
    def test_llamarlo_con_don_ramon_delante_se_lo_lleva(self, servicios, ramon):
        assert servicios.usar(Servicio.BARRIGA, [ramon]) is Resultado.AHUYENTADO
        assert not ramon.esta_acechando()

    def test_llamarlo_sin_necesidad_le_cuesta_la_noche_al_jugador(self, servicios):
        assert servicios.usar(Servicio.BARRIGA, []) is Resultado.LLAMADA_EN_VANO

    def test_no_sirve_si_don_ramon_todavia_viene_de_camino(self, servicios):
        de_camino = crear(nombres.DON_RAMON, nivel_ia=1)
        assert servicios.usar(Servicio.BARRIGA, [de_camino]) is Resultado.LLAMADA_EN_VANO

    def test_queda_en_espera_tras_cada_llamada(self, servicios, ramon):
        servicios.usar(Servicio.BARRIGA, [ramon])
        assert not servicios.disponible(Servicio.BARRIGA)

    def test_vuelve_a_estar_listo_al_pasar_la_espera(self, servicios, ramon):
        servicios.usar(Servicio.BARRIGA, [ramon])
        servicios.actualizar(BARRIGA_COOLDOWN_SEGUNDOS, jugador_escondido=True)
        assert servicios.disponible(Servicio.BARRIGA)


class TestAudioDeQuico:
    def test_le_quita_terreno_a_dona_florinda(self, servicios, florinda):
        antes = florinda.habitacion_actual
        assert servicios.sonar_audio([florinda]) is Resultado.AHUYENTADO
        assert florinda.habitacion_actual != antes

    def test_no_la_devuelve_a_su_casa(self, servicios, florinda):
        """Si la reiniciara, un solo uso bastaría para toda la noche y no
        tendría sentido racionar los audios."""
        servicios.sonar_audio([florinda])
        assert florinda.habitacion_actual != florinda.configuracion.habitacion_inicial

    def test_la_alcanza_aunque_no_este_delante(self, servicios, florinda):
        """El audio suena en la vecindad entera, no solo donde está el
        jugador: por eso sirve para frenarla antes de que llegue."""
        assert not florinda.esta_acechando()
        assert servicios.sonar_audio([florinda]) is Resultado.AHUYENTADO

    def test_al_llegar_a_la_reja_ya_no_le_hace_nada(self, servicios, florinda):
        """Es el punto de no retorno de su recorrido: a partir de ahí el
        jugador ya no puede empujarla más."""
        florinda.habitacion_actual = "entrada"
        assert servicios.sonar_audio([florinda]) is Resultado.SONO
        assert florinda.habitacion_actual == "entrada"

    def test_sin_ella_en_la_noche_solo_suena(self, servicios):
        assert servicios.sonar_audio([]) is Resultado.SONO

    def test_la_primera_noche_es_ilimitado(self):
        assert ServiciosUtilidad(numero_noche=1).audio_ilimitado

    def test_desde_la_segunda_noche_los_usos_se_cuentan(self, servicios):
        assert not servicios.audio_ilimitado
        assert servicios.usos_audio == USOS

    def test_cada_uso_descuenta_uno(self, servicios):
        servicios.sonar_audio([])
        assert servicios.usos_audio == USOS - 1

    def test_al_agotarse_deja_de_estar_disponible(self, servicios):
        for _ in range(USOS):
            servicios.sonar_audio([])
            servicios.actualizar(999.0, jugador_escondido=True)
        assert servicios.sonar_audio([]) is Resultado.SIN_USOS

    def test_la_noche_uno_no_se_queda_sin_usos(self):
        servicios = ServiciosUtilidad(numero_noche=1)
        for _ in range(USOS * 3):
            assert servicios.sonar_audio([]) is not Resultado.SIN_USOS
            servicios.actualizar(999.0, jugador_escondido=True)


class TestReponerAudio:
    """El botón del barril repara la cinta; no suena ni mueve a nadie."""

    def test_deja_el_contador_lleno(self, servicios):
        servicios.sonar_audio([])
        assert servicios.usar(Servicio.REPONER_AUDIO, []) is Resultado.EN_MARCHA
        assert servicios.usos_audio == USOS

    def test_no_mueve_a_dona_florinda(self, servicios, florinda):
        servicios.sonar_audio([])
        antes = florinda.habitacion_actual
        servicios.usar(Servicio.REPONER_AUDIO, [florinda])
        assert florinda.habitacion_actual == antes

    def test_con_la_cinta_entera_no_hay_nada_que_reponer(self, servicios):
        assert servicios.usar(Servicio.REPONER_AUDIO, []) is Resultado.OCUPADO

    def test_no_se_ofrece_con_la_cinta_entera(self, servicios):
        assert not servicios.disponible(Servicio.REPONER_AUDIO)
        servicios.sonar_audio([])
        assert servicios.disponible(Servicio.REPONER_AUDIO)

    def test_en_la_noche_uno_no_hace_falta(self):
        """El audio es ilimitado, así que reponerlo no tendría sentido."""
        primera = ServiciosUtilidad(numero_noche=1)
        assert not primera.disponible(Servicio.REPONER_AUDIO)

    def test_cada_noche_trae_sus_reproducciones(self):
        """Van bajando conforme avanza la campaña: 5, 4, 3 y 3."""
        por_noche = [ServiciosUtilidad(numero_noche=n).usos_audio for n in range(2, 6)]
        assert por_noche == [5, 4, 3, 3]


class TestOcupacion:
    def test_mientras_uno_trabaja_no_se_puede_lanzar_otro(self, servicios):
        servicios.usar(Servicio.CAMARAS, [])
        assert servicios.usar(Servicio.TODO, []) is Resultado.OCUPADO

    def test_al_terminar_se_avisa_de_cual_fue(self, servicios):
        servicios.usar(Servicio.CAMARAS, [])
        assert servicios.actualizar(SERVICIO_CAMARAS_SEGUNDOS, jugador_escondido=True) is Servicio.CAMARAS

    def test_mientras_dura_no_se_avisa_de_nada(self, servicios):
        servicios.usar(Servicio.CAMARAS, [])
        assert servicios.actualizar(SERVICIO_CAMARAS_SEGUNDOS / 2, jugador_escondido=True) is None

    def test_al_terminar_queda_libre(self, servicios):
        servicios.usar(Servicio.CAMARAS, [])
        servicios.actualizar(SERVICIO_CAMARAS_SEGUNDOS, jugador_escondido=True)
        assert not servicios.ocupado

    def test_restablecer_todo_repone_los_usos_del_audio(self, servicios):
        servicios.usos_audio = 0
        servicios.usar(Servicio.TODO, [])
        assert servicios.usos_audio == USOS


class TestEstadoParaElPanel:
    def test_refleja_el_servicio_en_marcha(self, servicios):
        servicios.usar(Servicio.CAMARAS, [])
        estado = servicios.estado()
        assert estado.en_marcha is Servicio.CAMARAS
        assert estado.total == SERVICIO_CAMARAS_SEGUNDOS
        assert estado.restante == pytest.approx(SERVICIO_CAMARAS_SEGUNDOS)

    def test_en_reposo_no_hay_nada_en_marcha(self, servicios):
        assert servicios.estado().en_marcha is None


def test_reiniciar_deja_todo_como_al_empezar_la_noche(servicios, ramon):
    servicios.usar(Servicio.BARRIGA, [ramon])
    servicios.reiniciar(numero_noche=1)
    assert servicios.audio_ilimitado
    assert servicios.usos_audio == usos_de_audio(1)
    assert not servicios.ocupado
    assert servicios.disponible(Servicio.BARRIGA)
