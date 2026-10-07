"""La alerta de que hay alguien en el Primer Patio: la imagen va y viene
entre color y gris, tiembla, y suena un aviso en bucle."""

import random

import pygame
import pytest

from vecindad.config.audio import EFECTO_ALERTA_PATIO, SUBCARPETA_AMBIENTE
from vecindad.config.interfaz import (
    PELIGRO_PERIODO_SEGUNDOS,
    PELIGRO_TEMBLOR_PIXELES,
)
from vecindad.config.ventana import RESOLUCION_BASE
from vecindad.infraestructura.audio import GestorAudio
from vecindad.presentacion.alerta_peligro import AlertaPeligro

FOTOGRAMA = 1.0 / 60.0
ROJO = (200, 30, 30)


@pytest.fixture(scope="module", autouse=True)
def pantalla():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


def _alerta():
    return AlertaPeligro(azar=random.Random(1))


def _avanzar(alerta, segundos, inminencia):
    for _ in range(round(segundos / FOTOGRAMA)):
        alerta.actualizar(FOTOGRAMA, inminencia)


def _lienzo():
    lienzo = pygame.Surface(RESOLUCION_BASE)
    lienzo.fill(ROJO)
    return lienzo


class TestVaivenDeColor:
    def test_con_el_patio_vacio_no_hace_nada(self):
        alerta = _alerta()
        _avanzar(alerta, 1.0, None)
        lienzo = _lienzo()
        alerta.dibujar(lienzo)
        assert not alerta.activa
        assert lienzo.get_at((640, 360))[:3] == ROJO

    def test_empieza_en_color(self):
        alerta = _alerta()
        alerta.actualizar(0.0, 0.0)
        assert alerta.mezcla == pytest.approx(0.0)

    def test_a_medio_ciclo_esta_en_gris_y_mas_oscuro(self):
        alerta = _alerta()
        _avanzar(alerta, PELIGRO_PERIODO_SEGUNDOS[0] / 2, 0.0)
        assert alerta.mezcla == pytest.approx(1.0, abs=0.01)
        lienzo = _lienzo()
        alerta.temblor = (0, 0)
        alerta.dibujar(lienzo)
        r, g, b = lienzo.get_at((640, 360))[:3]
        assert abs(r - g) <= 2 and abs(g - b) <= 2  # sin color
        assert r < ROJO[0]

    def test_en_el_punto_mas_gris_no_usa_alfa_255(self):
        """Un blit con alfa exactamente 255 es lentísimo en pygame (8 ms
        contra menos de 1): a opacidad completa se quita el alfa."""
        alerta = _alerta()
        _avanzar(alerta, PELIGRO_PERIODO_SEGUNDOS[0] / 2, 0.0)
        alerta._fase = 0.5
        alerta.dibujar(_lienzo())
        assert alerta._gris.get_alpha() is None

    def test_vuelve_al_color(self):
        alerta = _alerta()
        _avanzar(alerta, PELIGRO_PERIODO_SEGUNDOS[0], 0.0)
        assert alerta.mezcla == pytest.approx(0.0, abs=0.01)

    def test_al_acercarse_el_ataque_va_mas_rapido(self):
        alerta = _alerta()
        alerta.actualizar(FOTOGRAMA, 0.0)
        al_llegar = alerta.periodo()
        alerta.actualizar(FOTOGRAMA, 0.9)
        assert alerta.periodo() < al_llegar
        alerta.actualizar(FOTOGRAMA, 1.0)
        assert alerta.periodo() == pytest.approx(PELIGRO_PERIODO_SEGUNDOS[1])

    def test_al_vaciarse_el_patio_se_apaga(self):
        alerta = _alerta()
        _avanzar(alerta, 0.5, 0.5)
        alerta.actualizar(FOTOGRAMA, None)
        assert not alerta.activa
        assert alerta.mezcla == 0.0
        assert alerta.temblor == (0, 0)


class TestTemblor:
    def _maximo(self, inminencia):
        alerta = _alerta()
        maximo = 0
        for _ in range(300):
            alerta.actualizar(FOTOGRAMA, inminencia)
            maximo = max(maximo, abs(alerta.temblor[0]), abs(alerta.temblor[1]))
        return maximo

    def test_no_pasa_de_su_amplitud(self):
        assert self._maximo(0.0) <= PELIGRO_TEMBLOR_PIXELES[0]
        assert self._maximo(1.0) <= PELIGRO_TEMBLOR_PIXELES[1]

    def test_crece_al_acercarse_el_ataque(self):
        assert self._maximo(1.0) > self._maximo(0.0)

    def test_corre_la_imagen_y_tapa_el_borde(self):
        alerta = _alerta()
        alerta.actualizar(FOTOGRAMA, 0.0)
        alerta.temblor = (5, 0)
        lienzo = _lienzo()
        lienzo.fill((0, 200, 0), (0, 0, 10, RESOLUCION_BASE[1]))
        alerta.dibujar(lienzo)
        assert lienzo.get_at((2, 300))[:3] == (0, 0, 0)  # franja descubierta
        assert lienzo.get_at((12, 300))[1] > lienzo.get_at((12, 300))[0]  # el verde se corrió


class TestSonidoEnBucle:
    @pytest.fixture
    def audio(self):
        gestor = GestorAudio()
        if not gestor.disponible:
            pytest.skip("sin mezclador de audio")
        yield gestor
        gestor.detener_bucle()

    def test_suena_y_se_calla(self, audio):
        audio.sonar_en_bucle(EFECTO_ALERTA_PATIO, SUBCARPETA_AMBIENTE)
        assert audio.sonando_en_bucle
        audio.detener_bucle()
        assert not audio.sonando_en_bucle

    def test_pedirlo_cada_fotograma_no_lo_reinicia(self, audio):
        audio.sonar_en_bucle(EFECTO_ALERTA_PATIO, SUBCARPETA_AMBIENTE)
        canal = audio._bucle[1]
        audio.sonar_en_bucle(EFECTO_ALERTA_PATIO, SUBCARPETA_AMBIENTE, 0.7)
        assert audio._bucle[1] is canal
        assert canal.get_volume() == pytest.approx(0.7, abs=0.01)

    def test_existe_en_los_dos_arboles(self, audio):
        """Si faltara, la alerta se quedaría muda sin avisar."""
        for streamer in (False, True):
            audio.aplicar_modo_streamer(streamer)
            assert audio._buscar_archivo(SUBCARPETA_AMBIENTE, EFECTO_ALERTA_PATIO) is not None
