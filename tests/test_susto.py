"""El susto final: su guion en el tiempo y que nadie se quede sin él.

El guion se prueba como aritmética pura. Lo que se comprueba con pygame es
que cada personaje que puede acabar la noche, con cuadros propios o sin
ellos, arranca su susto y que este se puede dibujar hasta el final.
"""

import pygame
import pytest

from vecindad.config.interfaz import (
    ACERCAMIENTO_CON_JUMPS,
    SUSTO_DURACION_NATURAL,
    SUSTO_ESTATICA_CIERRE_SEGUNDOS,
    SUSTO_PROPORCION_GOLPE,
    SUSTO_ZOOM_INICIAL_SIN_CUADROS,
    SUSTOS_COMPUESTOS,
)
from vecindad.config.rutas import DIR_ASSETS_ANIMATRONICS
from vecindad.config.ventana import RESOLUCION_BASE
from vecindad.dominio.animatronicos import carpetas_de_atacantes
from vecindad.mundo.posiciones import POSICIONES, POSICION_BARRIL
from vecindad.presentacion.jumpscare import GuionSusto, Susto, cuadros_de_hoja

DURACION = 3.0
CUADROS = 10
FOTOGRAMA = 1.0 / 60.0


@pytest.fixture
def guion():
    return GuionSusto(CUADROS, DURACION)


class TestGuion:
    def test_el_golpe_llega_en_su_proporcion(self, guion):
        assert guion.golpe == pytest.approx(DURACION * SUSTO_PROPORCION_GOLPE)

    def test_los_cuadros_avanzan_en_orden_y_terminan_en_el_ultimo(self, guion):
        indices = [guion.indice_cuadro(n * FOTOGRAMA) for n in range(int(DURACION / FOTOGRAMA))]
        assert indices == sorted(indices)
        assert indices[0] == 0
        assert indices[-1] == CUADROS - 1

    def test_el_ultimo_cuadro_solo_sale_con_el_golpe(self, guion):
        assert guion.indice_cuadro(guion.golpe - 0.01) < CUADROS - 1
        assert guion.indice_cuadro(guion.golpe) == CUADROS - 1

    def test_se_usan_todos_los_cuadros(self, guion):
        vistos = {guion.indice_cuadro(n * 0.001) for n in range(int(DURACION / 0.001))}
        assert vistos == set(range(CUADROS))

    def test_el_acercamiento_se_acelera(self, guion):
        """Los primeros cuadros duran más que los del final del acercamiento."""
        def cuanto_dura(indice):
            pasos = [n * 0.001 for n in range(int(guion.golpe / 0.001))]
            return sum(1 for t in pasos if guion.indice_cuadro(t) == indice)

        assert cuanto_dura(0) > cuanto_dura(CUADROS - 2)

    def test_el_golpe_entra_con_zoom_de_mas_y_se_asienta(self, guion):
        antes = guion.zoom(guion.golpe - 0.01)
        al_llegar = guion.zoom(guion.golpe)
        despues = guion.zoom(guion.golpe + 0.5)
        assert al_llegar > antes
        assert al_llegar > despues

    def test_el_temblor_pega_al_llegar(self, guion):
        assert guion.temblor(guion.golpe) > guion.temblor(guion.golpe - 0.01)
        assert guion.temblor(guion.golpe + 1.0) < guion.temblor(guion.golpe)

    def test_destello_y_velo_solo_tras_el_golpe(self, guion):
        assert guion.destello(guion.golpe - 0.01) == 0
        assert guion.velo(guion.golpe - 0.01) == 0
        assert guion.destello(guion.golpe) > 0
        assert guion.velo(guion.golpe) > 0

    def test_el_destello_es_corto(self, guion):
        """Si durara más taparía la cara justo cuando llega."""
        assert guion.destello(guion.golpe + 0.2) == 0

    def test_termina_tapado_por_la_estatica(self, guion):
        assert guion.estatica(DURACION) == 255
        assert guion.estatica(DURACION - SUSTO_ESTATICA_CIERRE_SEGUNDOS - 0.01) < 255

    def test_la_luz_solo_parpadea_mientras_se_acerca(self, guion):
        assert guion.parpadea(0.0)
        assert not guion.parpadea(guion.golpe)

    def test_sin_cuadros_propios_viene_desde_lejos(self):
        """Con un solo sprite no hay acercamiento dibujado: lo hace el zoom."""
        solo_sprite = GuionSusto(1, DURACION, tiene_cuadros_propios=False)
        assert solo_sprite.zoom(0.0) == pytest.approx(SUSTO_ZOOM_INICIAL_SIN_CUADROS)
        assert solo_sprite.indice_cuadro(0.0) == 0
        assert solo_sprite.zoom(solo_sprite.golpe - 0.01) > solo_sprite.zoom(0.0)


@pytest.fixture(scope="module")
def susto():
    pygame.init()
    pygame.display.set_mode(RESOLUCION_BASE)
    yield Susto()
    pygame.quit()


@pytest.mark.parametrize("nombre", sorted(carpetas_de_atacantes()))
def test_nadie_se_queda_sin_susto(susto, nombre):
    """Con cuadros propios o con su sprite: todo el que puede acabar la noche
    se le echa encima al jugador, y el susto se dibuja hasta terminar."""
    lienzo = pygame.Surface(RESOLUCION_BASE)
    assert susto.iniciar(nombre, POSICIONES[POSICION_BARRIL])
    while not susto.termino:
        susto.actualizar(FOTOGRAMA)
        susto.dibujar(lienzo)
    assert not susto.activo


def _correr(susto, segundos: float):
    for _ in range(round(segundos / FOTOGRAMA)):
        susto.actualizar(FOTOGRAMA)


def test_dura_lo_que_el_audio(susto):
    nombre = sorted(carpetas_de_atacantes())[0]
    susto.iniciar(nombre, POSICIONES[POSICION_BARRIL], duracion_audio=1.0)
    _correr(susto, 0.95)
    assert not susto.termino
    _correr(susto, 0.1)
    assert susto.termino


def test_un_fotograma_largo_no_se_come_el_susto(susto):
    """Preparar los cuadros la primera vez puede tardar; ese salto no puede
    llevarse por delante el acercamiento."""
    nombre = sorted(carpetas_de_atacantes())[0]
    susto.iniciar(nombre, POSICIONES[POSICION_BARRIL], duracion_audio=1.0)
    susto.actualizar(5.0)
    assert not susto.termino


class TestHojaDePropuesta:
    """El juego recorta él mismo los cuadros de una hoja de propuesta: el
    arte llega como una cuadrícula y no se puede pedir cuadro por cuadro."""

    COLUMNAS, FILAS, LADO, SEPARADOR = 3, 2, 60, 4

    def _hoja(self, separador=(255, 255, 255)):
        ancho = self.COLUMNAS * self.LADO + (self.COLUMNAS - 1) * self.SEPARADOR
        alto = self.FILAS * self.LADO + (self.FILAS - 1) * self.SEPARADOR
        hoja = pygame.Surface((ancho, alto))
        hoja.fill(separador)
        for fila in range(self.FILAS):
            for columna in range(self.COLUMNAS):
                gris = 40 + 10 * (fila * self.COLUMNAS + columna + 1)
                x = columna * (self.LADO + self.SEPARADOR)
                y = fila * (self.LADO + self.SEPARADOR)
                hoja.fill((gris, gris, gris), pygame.Rect(x, y, self.LADO, self.LADO))
        return hoja

    def test_encuentra_todos_los_cuadros(self, susto):
        assert len(cuadros_de_hoja(self._hoja())) == self.COLUMNAS * self.FILAS

    def test_salen_en_orden_de_lectura(self, susto):
        """De izquierda a derecha y de arriba abajo: así se numeran en la
        receta."""
        hoja = self._hoja()
        grises = [hoja.get_at(rect.center)[0] for rect in cuadros_de_hoja(hoja)]
        assert grises == [40 + 10 * n for n in range(1, self.COLUMNAS * self.FILAS + 1)]

    def test_ningun_cuadro_arrastra_el_separador(self, susto):
        hoja = self._hoja()
        for rect in cuadros_de_hoja(hoja):
            esquina = hoja.get_at(rect.topleft)[:3]
            assert max(esquina) < 255, rect

    def test_tambien_con_separadores_negros(self, susto):
        """La hoja de Jaimico separa sus cuadros con negro."""
        assert len(cuadros_de_hoja(self._hoja(separador=(0, 0, 0)))) == self.COLUMNAS * self.FILAS

    def test_una_columna_oscura_del_arte_no_parte_un_cuadro(self, susto):
        """El arte es de noche: una franja casi negra dentro de un cuadro no
        es un separador mientras no sea negra de punta a punta."""
        hoja = self._hoja(separador=(0, 0, 0))
        x = self.LADO // 2
        pygame.draw.line(hoja, (0, 0, 0), (x, 0), (x, self.LADO - 10))
        assert len(cuadros_de_hoja(hoja)) == self.COLUMNAS * self.FILAS


FLORINDA = "Doña Florinda"


def _armar_varias(susto, nombre, veces=60):
    resultados = []
    for _ in range(veces):
        assert susto.iniciar(nombre, POSICIONES[POSICION_BARRIL])
        resultados.append(list(susto._frames))
    return resultados


class TestSustoCompuestoDeFlorinda:
    def test_sale_uno_de_sus_dos_acercamientos(self, susto):
        """Propuesta 1: 7 cuadros; propuesta 2: 6 (se salta el 6). Más el
        golpe."""
        largos = {len(cuadros) for cuadros in _armar_varias(susto, FLORINDA)}
        assert largos == {8, 7}

    def test_el_golpe_sale_al_azar(self, susto):
        golpes = {id(cuadros[-1]) for cuadros in _armar_varias(susto, FLORINDA)}
        assert len(golpes) > 1

    def test_el_golpe_horizontal_cubre_la_pantalla(self, susto):
        golpe = _armar_varias(susto, FLORINDA, veces=1)[0][-1]
        ancho, alto = RESOLUCION_BASE
        assert golpe.get_width() >= ancho and golpe.get_height() >= alto


class TestSustoCompuestoDeJaimico:
    def test_sale_la_propuesta_o_sus_jump(self, susto):
        """Propuesta: 8 cuadros; sus jump: del 1 al 6. Más el golpe."""
        largos = {len(cuadros) for cuadros in _armar_varias(susto, "Jaimico")}
        assert largos == {9, 7}

    def test_los_cuadros_de_la_propuesta_cubren_la_pantalla(self, susto):
        """Son horizontales: se ven a pantalla completa, sin recorte vertical."""
        ruta = DIR_ASSETS_ANIMATRONICS / "jaimico" / "propuesta 1.png"
        recorte = SUSTOS_COMPUESTOS["jaimico"]["recortes"]["propuesta 1.png"]
        ancho, alto = RESOLUCION_BASE
        for cuadro in susto._cuadros_de_hoja(ruta, recorte):
            assert cuadro.get_width() >= ancho and cuadro.get_height() >= alto


class TestSustoCompuestoDeLaBruja:
    def test_sale_la_propuesta_o_sus_jump(self, susto):
        """Propuesta: 8 cuadros; sus jump: del 1 al 5. Más el golpe."""
        largos = {len(cuadros) for cuadros in _armar_varias(susto, "Doña Clotilde")}
        assert largos == {9, 6}

    def test_el_golpe_sale_de_sus_dos_mejores_jump(self, susto):
        golpes = {id(cuadros[-1]) for cuadros in _armar_varias(susto, "Doña Clotilde")}
        assert len(golpes) == 2


@pytest.mark.parametrize("carpeta", sorted(SUSTOS_COMPUESTOS))
def test_la_receta_apunta_a_lo_que_existe(susto, carpeta):
    """Un nombre mal escrito en la receta no rompería nada: ese acercamiento
    simplemente no saldría nunca. Por eso se comprueba aquí."""
    directorio = DIR_ASSETS_ANIMATRONICS / carpeta
    receta = SUSTOS_COMPUESTOS[carpeta]
    for origen, numeros in receta["acercamientos"].items():
        assert numeros, origen
        if origen == ACERCAMIENTO_CON_JUMPS:
            for numero in numeros:
                assert (directorio / f"jump {numero}.png").exists(), numero
            continue
        assert (directorio / origen).exists(), origen
        disponibles = len(susto._cuadros_de_hoja(directorio / origen))
        assert max(numeros) <= disponibles, (origen, disponibles)
    for origen in receta.get("recortes", {}):
        assert origen in receta["acercamientos"], origen
    if receta["golpes"] is not None:
        for numero in receta["golpes"]:
            assert (directorio / f"jump {numero}.png").exists(), numero


def test_sin_audio_dura_lo_natural(susto):
    nombre = sorted(carpetas_de_atacantes())[0]
    susto.iniciar(nombre, POSICIONES[POSICION_BARRIL])
    _correr(susto, SUSTO_DURACION_NATURAL - 0.05)
    assert not susto.termino
    _correr(susto, 0.1)
    assert susto.termino
