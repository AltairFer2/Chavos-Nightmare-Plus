"""El monitor se vuelve errático con El Chavo en pantalla: la imagen tiembla
y el mapa se va a saltos con sus botones, para que escapar de su cámara
cueste."""

import random

import pygame
import pytest

from vecindad.config.interfaz import (
    CAMARA_ERRATICO_AMPLITUD_POR_IA,
    CAMARA_ERRATICO_INTENSIDAD_MINIMA,
    CAMARA_ERRATICO_MAPA_AMPLITUD,
)
from vecindad.config.partida import NIVEL_IA_MAXIMO
from vecindad.config.ventana import ANCHO_PANTALLA
from vecindad.dominio.animatronicos import crear_elenco_noche, nombres
from vecindad.presentacion.mapa_camaras import (
    AREA_MOVIMIENTO_MAPA,
    BOTONES_MAPA,
    RECT_MAPA,
    MapaVecindad,
)
from vecindad.presentacion.monitor_erratico import DesplazamientoErratico

FOTOGRAMA = 1.0 / 60.0


@pytest.fixture(scope="module", autouse=True)
def pantalla():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


def _erratico(semilla=1):
    return DesplazamientoErratico((100, 50), (0.1, 0.3), 20.0, azar=random.Random(semilla))


class TestDesplazamientoErratico:
    def test_sin_intensidad_se_queda_quieto(self):
        erratico = _erratico()
        for _ in range(60):
            erratico.actualizar(FOTOGRAMA, 0.0)
        assert erratico.quieto

    def test_con_intensidad_se_mueve(self):
        erratico = _erratico()
        posiciones = set()
        for _ in range(120):
            erratico.actualizar(FOTOGRAMA, 1.0)
            posiciones.add(erratico.desplazamiento)
        assert len(posiciones) > 10

    def test_no_se_pasa_de_su_amplitud(self):
        erratico = _erratico(5)
        for _ in range(2000):
            erratico.actualizar(FOTOGRAMA, 1.0)
            x, y = erratico.desplazamiento
            assert abs(x) <= 100 and abs(y) <= 50

    def test_cambia_de_direccion(self):
        """No es una deriva hacia un lado: va y viene."""
        erratico = _erratico(2)
        xs = []
        for _ in range(600):
            erratico.actualizar(FOTOGRAMA, 1.0)
            xs.append(erratico.desplazamiento[0])
        assert min(xs) < 0 < max(xs)

    def test_al_quitarle_la_intensidad_vuelve_a_su_sitio(self):
        erratico = _erratico()
        for _ in range(60):
            erratico.actualizar(FOTOGRAMA, 1.0)
        erratico.actualizar(FOTOGRAMA, 0.0)
        assert erratico.quieto


def _centro_del_boton(id_habitacion):
    x, y, ancho, alto = BOTONES_MAPA[id_habitacion]
    return (
        RECT_MAPA.x + int((x + ancho / 2) * RECT_MAPA.width),
        RECT_MAPA.y + int((y + alto / 2) * RECT_MAPA.height),
    )


class TestMapaMovido:
    def test_quieto_responde_donde_siempre(self):
        mapa = MapaVecindad()
        assert mapa.boton_en(_centro_del_boton("entrada")) == "entrada"

    def test_los_botones_se_mueven_con_el_mapa(self):
        mapa = MapaVecindad()
        mapa.desplazamiento = (-200, -120)
        x, y = _centro_del_boton("entrada")
        assert mapa.boton_en((x, y)) != "entrada"
        assert mapa.boton_en((x - 200, y - 120)) == "entrada"

    def test_no_se_sale_de_la_pantalla_ni_baja_a_las_pestanas(self):
        mapa = MapaVecindad()
        for desplazamiento in ((5000, 5000), (-5000, -5000), (300, 300)):
            mapa.desplazamiento = desplazamiento
            assert AREA_MOVIMIENTO_MAPA.contains(mapa.rect)
        assert AREA_MOVIMIENTO_MAPA.bottom == RECT_MAPA.bottom
        assert AREA_MOVIMIENTO_MAPA.right == ANCHO_PANTALLA


class TestConElChavoEnPantalla:
    @staticmethod
    def _monitor(noche=6, nivel_ia=NIVEL_IA_MAXIMO):
        """Por defecto, El Chavo a nivel 20: lo más errático que se pone."""
        from vecindad.presentacion.camaras import SistemaCamaras

        camaras = SistemaCamaras()
        camaras.reiniciar("primer_patio", noche)
        elenco = crear_elenco_noche(noche)
        chavo = next(a for a in elenco if a.nombre == nombres.CHAVO)
        chavo.nivel_ia = nivel_ia
        for animatronic in elenco:
            animatronic.activo = animatronic is chavo
        camaras.activo = True
        camaras.animacion.cancelar()
        return camaras, elenco, chavo

    def test_sin_el_chavo_el_mapa_esta_quieto(self):
        camaras, elenco, chavo = self._monitor()
        chavo.habitacion_actual = "casa_paty"
        for _ in range(30):
            camaras.actualizar(FOTOGRAMA, elenco)
        assert not camaras.erratico
        assert camaras.desplazamiento_mapa == (0, 0)

    def test_al_verlo_el_mapa_se_mueve(self):
        camaras, elenco, chavo = self._monitor()
        chavo.habitacion_actual = camaras.camara_actual
        movimientos = set()
        for _ in range(40):
            camaras.actualizar(FOTOGRAMA, elenco)
            movimientos.add(camaras.desplazamiento_mapa)
        assert camaras.erratico
        assert len(movimientos) > 5

    def test_nada_mas_verlo_ya_se_descontrola(self):
        camaras, elenco, chavo = self._monitor()
        chavo.habitacion_actual = camaras.camara_actual
        camaras.actualizar(FOTOGRAMA, elenco)
        assert camaras._erratico_mapa.intensidad == pytest.approx(
            CAMARA_ERRATICO_INTENSIDAD_MINIMA
        )

    def test_el_clic_cae_donde_se_ve_el_boton(self):
        """Lo dibujado y lo que responde se mueven juntos."""
        camaras, elenco, chavo = self._monitor()
        chavo.habitacion_actual = camaras.camara_actual
        for _ in range(20):
            camaras.actualizar(FOTOGRAMA, elenco)
        dx, dy = camaras.desplazamiento_mapa
        x, y = _centro_del_boton("entrada")
        assert camaras.boton_en((x + dx, y + dy)) == "entrada"

    def test_al_cambiar_de_camara_se_calma(self):
        camaras, elenco, chavo = self._monitor()
        chavo.habitacion_actual = camaras.camara_actual
        for _ in range(20):
            camaras.actualizar(FOTOGRAMA, elenco)
        camaras.cambiar_camara("casa_paty")
        camaras.actualizar(FOTOGRAMA, elenco)
        assert not camaras.erratico
        assert camaras.desplazamiento_mapa == (0, 0)

    def test_el_mapa_recorre_bastante_y_no_se_traba_en_la_esquina(self):
        """Está pegado abajo a la derecha: si se moviera alrededor de su
        sitio, la mitad de los saltos chocarían con el borde."""
        # Noche 3: aguanta 2 s mirado, así que hay tiempo de medir antes de
        # que rompa las cámaras (rotas, el mapa ya no se mueve).
        camaras, elenco, chavo = self._monitor(noche=3)
        chavo.habitacion_actual = camaras.camara_actual
        xs, ys = [], []
        for _ in range(110):
            camaras.actualizar(FOTOGRAMA, elenco)
            dx, dy = camaras.desplazamiento_mapa
            xs.append(dx)
            ys.append(dy)
        assert max(xs) - min(xs) > 150
        assert max(ys) - min(ys) > 80
        assert sum(1 for x in xs if x == 0) < len(xs) // 4

    def test_amplitud_del_mapa_razonable(self):
        """Que se mueva bastante, pero que el mapa siga siendo alcanzable."""
        ancho, alto = CAMARA_ERRATICO_MAPA_AMPLITUD
        assert 0 < ancho < RECT_MAPA.x
        assert 0 < alto < RECT_MAPA.y


class TestSegunElNivelDeElChavo:
    """Lo errático del monitor escala con su nivel de IA: con nivel 20 es
    como siempre fue, con menos salta menos lejos y menos seguido."""

    _monitor = staticmethod(TestConElChavoEnPantalla._monitor)

    def _intensidad_al_verlo(self, nivel_ia):
        camaras, elenco, chavo = self._monitor(nivel_ia=nivel_ia)
        chavo.habitacion_actual = camaras.camara_actual
        camaras.actualizar(FOTOGRAMA, elenco)
        return camaras._erratico_mapa.intensidad

    def test_con_nivel_maximo_es_lo_de_siempre(self):
        assert self._intensidad_al_verlo(NIVEL_IA_MAXIMO) == pytest.approx(
            CAMARA_ERRATICO_INTENSIDAD_MINIMA
        )

    def test_con_nivel_minimo_se_escala(self):
        assert self._intensidad_al_verlo(1) == pytest.approx(
            CAMARA_ERRATICO_INTENSIDAD_MINIMA * CAMARA_ERRATICO_AMPLITUD_POR_IA[0]
        )

    def test_a_mas_nivel_mas_erratico(self):
        intensidades = [self._intensidad_al_verlo(nivel) for nivel in (1, 7, 10, 15, 20)]
        assert intensidades == sorted(intensidades)
        assert intensidades[0] < intensidades[-1]

    def test_con_poco_nivel_el_mapa_recorre_menos(self):
        def recorrido(nivel_ia):
            camaras, elenco, chavo = self._monitor(noche=3, nivel_ia=nivel_ia)
            camaras._erratico_mapa._azar = random.Random(4)
            chavo.habitacion_actual = camaras.camara_actual
            xs = []
            for _ in range(110):
                camaras.actualizar(FOTOGRAMA, elenco)
                xs.append(camaras.desplazamiento_mapa[0])
            return max(xs) - min(xs)

        assert recorrido(1) < recorrido(NIVEL_IA_MAXIMO)

    def test_el_ritmo_espacia_los_saltos(self):
        def saltos(ritmo):
            erratico = _erratico(3)
            destinos = set()
            for _ in range(600):
                erratico.actualizar(FOTOGRAMA, 1.0, ritmo)
                destinos.add(erratico._destino)
            return len(destinos)

        assert saltos(0.35) < saltos(1.0) * 0.6
