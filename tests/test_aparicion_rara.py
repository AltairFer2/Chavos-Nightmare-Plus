"""Las apariciones raras (easter eggs): cuándo salen y cómo se ven."""

import random

import pygame
import pytest

from vecindad.config.interfaz import APARICION_RARA_OPACIDAD
from vecindad.config.jugabilidad import (
    APARICION_RARA_SEGUNDOS,
    APARICION_RARA_UNO_ENTRE_POR_NOCHE,
)
from vecindad.dominio.aparicion_rara import AparicionesRaras, uno_entre_de_la_noche
from vecindad.presentacion.aparicion_rara import (
    ImagenesRaras,
    opacidad_en,
    rutas_de_las_apariciones,
)


class AzarFijo:
    """Saca siempre lo mismo: 0 para "sí aparece", otra cosa para "no"."""

    def __init__(self, tirada, indice=0):
        self.tirada = tirada
        self.indice = indice
        self.tiradas = 0

    def randrange(self, tope):
        if tope == 10:  # elegir cuál de las diez
            return self.indice
        self.tiradas += 1
        return self.tirada


class TestCuandoAparecen:
    def test_la_noche_uno_es_uno_entre_diez_mil(self):
        assert uno_entre_de_la_noche(1) == 10000

    def test_las_noches_cinco_y_seis_uno_entre_cinco_mil(self):
        assert uno_entre_de_la_noche(5) == uno_entre_de_la_noche(6) == 5000

    def test_cada_noche_es_mas_probable_que_la_anterior(self):
        valores = [uno_entre_de_la_noche(n) for n in range(1, 7)]
        assert valores == sorted(valores, reverse=True)
        assert set(APARICION_RARA_UNO_ENTRE_POR_NOCHE) == set(range(1, 7))

    def test_se_tira_una_vez_por_segundo(self):
        azar = AzarFijo(tirada=1)
        apariciones = AparicionesRaras(1, 10, azar=azar)
        for _ in range(600):
            apariciones.actualizar(1 / 60)
        assert azar.tiradas == 10

    def test_si_sale_aparece_y_dice_cual(self):
        apariciones = AparicionesRaras(1, 10, azar=AzarFijo(tirada=0, indice=7))
        assert apariciones.actualizar(1.0) == 7
        assert apariciones.visible
        assert apariciones.actual == 7

    def test_mientras_se_ve_no_se_tira_otra(self):
        azar = AzarFijo(tirada=0)
        apariciones = AparicionesRaras(1, 10, azar=azar)
        apariciones.actualizar(1.0)
        tiradas = azar.tiradas
        apariciones.actualizar(APARICION_RARA_SEGUNDOS / 2)
        assert azar.tiradas == tiradas

    def test_se_va_sola(self):
        apariciones = AparicionesRaras(1, 10, azar=AzarFijo(tirada=0))
        apariciones.actualizar(1.0)
        apariciones.actualizar(APARICION_RARA_SEGUNDOS)
        assert not apariciones.visible

    def test_sin_imagenes_no_aparece_nada(self):
        apariciones = AparicionesRaras(1, 0, azar=AzarFijo(tirada=0))
        assert apariciones.actualizar(10.0) is None

    def test_la_probabilidad_es_la_de_la_noche(self):
        """Con muchas horas simuladas, salen más o menos las que tocan."""
        apariciones = AparicionesRaras(5, 10, azar=random.Random(3))
        segundos = 2_000_000
        vistas = 0
        for _ in range(segundos):
            if apariciones.actualizar(1.0) is not None:
                vistas += 1
                apariciones.actualizar(APARICION_RARA_SEGUNDOS)
        esperadas = segundos / 5000
        assert esperadas * 0.8 < vistas < esperadas * 1.2


@pytest.fixture(scope="module")
def pantalla():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


@pytest.mark.usefixtures("pantalla")
class TestComoSeVen:
    def test_estan_las_diez_imagenes_en_orden(self):
        rutas = rutas_de_las_apariciones()
        assert [r.name for r in rutas] == [f"rare {n}.png" for n in range(1, 11)]
        assert ImagenesRaras().cantidad == 10

    def test_entran_y_salen_fundiendose(self):
        assert opacidad_en(0.0) == 0
        assert opacidad_en(1.0) == 0
        assert opacidad_en(0.5) == APARICION_RARA_OPACIDAD

    def test_nunca_pasan_de_muy_tenues(self):
        """No deben estorbar: como mucho un 15% de opacidad."""
        assert max(opacidad_en(p / 100) for p in range(101)) <= 255 * 0.15

    def test_dibujarla_casi_no_cambia_la_pantalla(self):
        lienzo = pygame.Surface((1280, 720))
        lienzo.fill((0, 0, 0))
        ImagenesRaras().dibujar(lienzo, 0, 0.5)
        brillo = pygame.transform.average_color(lienzo)
        assert max(brillo[:3]) < 40
