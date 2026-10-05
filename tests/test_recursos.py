"""El recorte del fondo de una lámina.

Separar el negro de alrededor del negro que el propio dibujo encierra es lo
que permite que el monitor de cámaras deje ver el patio por los lados y siga
teniendo la pantalla apagada. Como los dos negros son el mismo color, lo único
que los distingue es la forma, y eso es fácil de romper sin enterarse.

Se prueba con figuras hechas aquí mismo, sin depender de ningún asset: lo que
se comprueba es la regla, no el arte.
"""

import pygame
import pytest

from vecindad.infraestructura.recursos import MINIMO_FONDO, quitar_fondo_alrededor

LADO = 120
CENTRO = (LADO // 2, LADO // 2)
FUERA = (2, 2)


@pytest.fixture(scope="module", autouse=True)
def pantalla():
    """convert_alpha() necesita un modo de vídeo abierto, aunque sea el
    driver dummy que fija conftest."""
    pygame.init()
    pygame.display.set_mode((LADO, LADO))
    yield
    pygame.quit()


def rosquilla() -> pygame.Surface:
    """Un anillo claro sobre negro: por fuera hay negro que llega al borde y
    por dentro, negro encerrado. Es la forma del monitor en pequeño."""
    imagen = pygame.Surface((LADO, LADO))
    imagen.fill((0, 0, 0))
    pygame.draw.circle(imagen, (200, 200, 200), CENTRO, 40)
    pygame.draw.circle(imagen, (0, 0, 0), CENTRO, 25)
    return imagen


def alfa_en(imagen: pygame.Surface, punto) -> int:
    return imagen.get_at(punto)[3]


class TestQuitarFondoAlrededor:
    def test_el_negro_de_fuera_se_vuelve_transparente(self):
        assert alfa_en(quitar_fondo_alrededor(rosquilla()), FUERA) == 0

    def test_el_negro_encerrado_sigue_tapando(self):
        """Es la pantalla apagada del monitor: si se volviera transparente,
        se vería la cámara antes de tiempo."""
        assert alfa_en(quitar_fondo_alrededor(rosquilla()), CENTRO) == 255

    def test_el_dibujo_no_se_toca(self):
        recortada = quitar_fondo_alrededor(rosquilla())
        borde_del_anillo = (CENTRO[0], CENTRO[1] - 32)
        assert alfa_en(recortada, borde_del_anillo) == 255
        assert recortada.get_at(borde_del_anillo)[:3] == (200, 200, 200)

    def test_sin_fondo_negro_no_se_recorta_nada(self):
        """Una lámina que llega hasta el borde se queda entera en vez de
        desaparecer a medias."""
        llena = pygame.Surface((LADO, LADO))
        llena.fill((120, 120, 120))
        assert alfa_en(quitar_fondo_alrededor(llena), FUERA) == 255

    def test_una_mota_oscura_en_el_borde_no_es_fondo(self):
        """Las manchas diminutas que tocan el marco son ruido del propio
        dibujo; hacerlas transparentes sería mordisquearlo."""
        imagen = pygame.Surface((LADO, LADO))
        imagen.fill((120, 120, 120))
        mota = pygame.Rect(0, 0, 2, 2)
        imagen.fill((0, 0, 0), mota)
        assert mota.width * mota.height < MINIMO_FONDO
        assert alfa_en(quitar_fondo_alrededor(imagen), (0, 0)) == 255
