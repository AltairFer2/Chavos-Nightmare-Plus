"""La noche dentro de la partida de verdad: cómo empieza y qué mata.

El resto de las pruebas comprueba qué devuelven las funciones de dominio, y
eso no basta: el jugador no juega contra `detectar_luz_mortal`, juega contra
un fotograma entero de `Juego._actualizar`, donde el haz sale de la posición
del ratón, hay paneles que lo tapan y varias reglas se aplican seguidas en un
orden concreto. Un fallo de cableado entre esas piezas no lo ve ninguna
prueba de dominio.

Por eso aquí se monta el juego completo (pygame en modo dummy, sin ventana
real), se pone a alguien delante del jugador, se apunta el ratón a su torso y
se corre un fotograma como el del bucle principal. Lo que se afirma es lo que
el jugador vería en pantalla: si perdió, si se quedó sin batería y si le
salió algún texto.
"""

from types import SimpleNamespace

import pygame
import pytest

from vecindad.app.estados import EstadoJuego
from vecindad.config.partida import (
    NOCHE_EXTRA,
    PERIODICO_SEGUNDOS,
    TARJETA_NOCHE_SEGUNDOS,
)
from vecindad.dominio.animatronicos import ELENCO, nombres
from vecindad.dominio.objetos import ID_PELOTA_REDONDA
from vecindad.presentacion.inicio_noche import HORA_DE_ARRANQUE
from vecindad.mundo.posiciones import (
    POSICION_BARRIL,
    POSICION_DENTRO_BARRIL,
    POSICION_LAVADEROS,
)

FOTOGRAMA = 1.0 / 60.0

# Margen de ataque tan largo que no puede vencer dentro de la prueba: así, si
# el estado cambia, fue por la luz y no porque al personaje le tocara atacar.
MARGEN_INALCANZABLE = 999.0

# Noche 6: sale el elenco completo, así que hay ficha viva de todos.
NOCHE_CON_TODOS = 6

# Las dos vistas del mismo patio. Alumbrar tiene que hacer lo mismo desde las
# dos: son el mismo sitio con otro ángulo.
VISTAS = (POSICION_BARRIL, POSICION_LAVADEROS)

# A quiénes mata apuntarles la linterna de cerca.
MUEREN_POR_LA_LUZ = (nombres.DON_RAMON, nombres.FLORINDA)

# A quiénes solo les cuesta la batería entera.
DESCARGAN_LA_LINTERNA = (nombres.CHILINDRINA,)

TODOS = tuple(config.nombre for config in ELENCO)


def solicitud_de(numero: int, personalizada: bool = False, nueva_partida: bool = False):
    """Lo que el menú le pasa al juego para arrancar una noche."""
    return SimpleNamespace(
        numero=numero,
        personalizada=personalizada,
        niveles_ia={},
        nueva_partida=nueva_partida,
    )


def empezar_noche(juego, numero: int = NOCHE_CON_TODOS):
    """Arranca la noche y se salta las pantallas de entrada.

    La noche ya no empieza jugando: antes van el periódico y la tarjeta (ver
    TestLaEntradaDeLaNoche, que sí las mide). Estas pruebas hablan de lo que
    pasa en el patio, así que se corren fotogramas hasta llegar allí.
    """
    juego.iniciar_noche(solicitud_de(numero))
    juego.periodico.termino = True
    juego.tarjeta_noche.termino = True
    while not juego.gestor_estados.jugando():
        juego._actualizar(FOTOGRAMA)


@pytest.fixture(scope="module")
def juego():
    """Un juego montado una sola vez: abrirlo carga todos los assets.

    Nada de esto toca los archivos del jugador: se le hace creer que ya hay
    configuración guardada para que no escriba el configuracion.json, y se
    le tapa el guardado del progreso, que si no empezar una partida nueva
    aquí le borraría la campaña de verdad. Que el progreso se persista bien
    se prueba aparte, en test_guardado.py.
    """
    from unittest.mock import patch

    from vecindad.app.juego import Juego

    with patch("vecindad.app.juego.existe_configuracion_guardada", return_value=True):
        partida = Juego()
    partida.progreso.guardar = lambda: True
    yield partida
    pygame.quit()


@pytest.fixture
def alumbrar(juego, monkeypatch):
    """Deja a un personaje solo delante del jugador y le apunta la linterna
    durante un fotograma. Devuelve su ficha viva."""

    def _alumbrar(
        nombre: str,
        id_posicion: str = POSICION_BARRIL,
        camaras_levantadas: bool = False,
    ):
        empezar_noche(juego, NOCHE_CON_TODOS)
        juego.jugador.posicion = id_posicion
        # Después de iniciar_noche, que baja todos los paneles.
        juego.sistema_camaras.activo = camaras_levantadas

        objetivo = next(a for a in juego.noche.animatronics if a.nombre == nombre)
        # Los demás apagados: si no, cualquiera podría acabar la noche por su
        # cuenta y el resultado ya no diría nada sobre la luz.
        for animatronic in juego.noche.animatronics:
            animatronic.activo = animatronic is objetivo
        objetivo.irrumpir()
        objetivo.segundos_para_atacar = MARGEN_INALCANZABLE

        # El haz sale de donde está el ratón: se falsea su traducción al
        # lienzo para dejarlo justo encima del torso. Dentro del barril no hay
        # patio que apuntar, así que se toma el punto de la vista de fuera:
        # es donde cae el ratón cuando se mira el monitor.
        vista = id_posicion if id_posicion in VISTAS else POSICION_BARRIL
        torso = objetivo.punto_torso_en(vista)
        monkeypatch.setattr(
            juego.gestor_pantalla, "posicion_en_lienzo", lambda _: torso
        )
        juego.linterna.reiniciar(0)
        juego.linterna.encendida = True

        juego._actualizar(FOTOGRAMA)
        return objetivo

    return _alumbrar


@pytest.fixture
def plantar_delante(juego):
    """Deja a un personaje delante del jugador, sin linterna de por medio, y
    devuelve su ficha viva junto con el juego listo para correr fotogramas."""

    def _plantar(nombre: str):
        empezar_noche(juego, NOCHE_CON_TODOS)
        objetivo = next(a for a in juego.noche.animatronics if a.nombre == nombre)
        for animatronic in juego.noche.animatronics:
            animatronic.activo = animatronic is objetivo
        objetivo.irrumpir()
        objetivo.segundos_para_atacar = 0.5
        return objetivo

    return _plantar


def _sigue_jugando(juego) -> bool:
    """El susto también cuenta como derrota: termina en el game over."""
    return juego.gestor_estados.estado is EstadoJuego.JUGANDO


class TestLaTreguaDelPrincipio:
    """Quien se quita con un objeto no puede matar hasta que el suelo le haya
    dado esa respuesta al jugador una primera vez. Después ya es cosa suya:
    haberla malgastado no le devuelve la protección."""

    def _correr(self, juego, segundos: float = 2.0):
        for _ in range(int(segundos / FOTOGRAMA)):
            juego._actualizar(FOTOGRAMA)

    def test_quico_espera_a_que_aparezca_la_pelota(self, juego, plantar_delante):
        quico = plantar_delante(nombres.QUICO)
        self._correr(juego)
        assert _sigue_jugando(juego)
        assert quico.esta_acechando(), "sigue delante, solo que sin poder matar"

    def test_con_la_pelota_en_la_mochila_si_ataca(self, juego, plantar_delante):
        plantar_delante(nombres.QUICO)
        juego.inventario.guardar(ID_PELOTA_REDONDA)
        self._correr(juego)
        assert not _sigue_jugando(juego)

    def test_haberla_gastado_mal_no_devuelve_la_tregua(self, juego, plantar_delante):
        """Tuvo la pelota, se la tiró a quien no era y se quedó sin nada:
        Quico lo mata igual. La respuesta existió."""
        plantar_delante(nombres.QUICO)
        juego.inventario.guardar(ID_PELOTA_REDONDA)
        juego.inventario.gastar(ID_PELOTA_REDONDA)
        self._correr(juego)
        assert not _sigue_jugando(juego)

    def test_don_ramon_no_espera_a_nadie(self, juego, plantar_delante):
        """Su respuesta es el Sr. Barriga, que está siempre en el panel: la
        tregua no le toca."""
        plantar_delante(nombres.DON_RAMON)
        self._correr(juego)
        assert not _sigue_jugando(juego)

    def test_cada_noche_empieza_con_la_tregua_otra_vez(self, juego, plantar_delante):
        """La memoria de lo que pasó por sus manos es de esa noche: al
        empezar la siguiente vuelve a tener su respiro."""
        plantar_delante(nombres.QUICO)
        juego.inventario.guardar(ID_PELOTA_REDONDA)
        plantar_delante(nombres.QUICO)  # inicia otra noche
        self._correr(juego)
        assert _sigue_jugando(juego)


class TestNuevoJuegoBorraElAvance:
    """Nuevo Juego empieza la campaña otra vez: Continuar no puede seguir
    apuntando a la noche a la que había llegado la partida anterior."""

    def test_al_empezar_de_cero_continuar_vuelve_a_la_noche_uno(self, juego):
        juego.progreso.noches_completadas = 3
        juego.progreso.partida_iniciada = True

        juego.iniciar_noche(solicitud_de(1, nueva_partida=True))

        assert juego.progreso.noches_completadas == 0
        assert juego.progreso.proxima_noche == 1
        assert juego.progreso.hay_partida_guardada, "sigue habiendo qué continuar"

    def test_continuar_una_partida_no_toca_el_avance(self, juego):
        juego.progreso.noches_completadas = 3
        juego.progreso.partida_iniciada = True

        juego.iniciar_noche(solicitud_de(4))

        assert juego.progreso.noches_completadas == 3

    def test_ganar_la_noche_uno_deja_continuar_en_la_dos(self, juego):
        juego.progreso.noches_completadas = 3
        juego.iniciar_noche(solicitud_de(1, nueva_partida=True))

        juego.noche.numero = 1
        juego._ganar_la_noche()

        assert juego.progreso.proxima_noche == 2


class TestLaEntradaDeLaNoche:
    """Antes del patio van dos pantallas sobre negro: el recorte del
    periódico (solo al empezar de cero) y la tarjeta con la noche y las 12:00
    am. Ninguna de las dos deja correr la noche todavía."""

    def _correr(self, juego, segundos: float):
        for _ in range(int(segundos / FOTOGRAMA) + 1):
            juego._actualizar(FOTOGRAMA)

    def test_una_partida_nueva_abre_con_el_periodico(self, juego):
        juego.iniciar_noche(solicitud_de(1, nueva_partida=True))
        assert juego.gestor_estados.estado is EstadoJuego.PERIODICO

    def test_el_periodico_se_queda_los_veinte_segundos(self, juego):
        juego.iniciar_noche(solicitud_de(1, nueva_partida=True))
        self._correr(juego, PERIODICO_SEGUNDOS - 1.0)
        assert juego.gestor_estados.estado is EstadoJuego.PERIODICO

    def test_del_periodico_se_pasa_a_la_tarjeta_y_de_ahi_al_patio(self, juego):
        juego.iniciar_noche(solicitud_de(1, nueva_partida=True))
        self._correr(juego, PERIODICO_SEGUNDOS)
        assert juego.gestor_estados.estado is EstadoJuego.TARJETA_NOCHE
        self._correr(juego, TARJETA_NOCHE_SEGUNDOS)
        assert juego.gestor_estados.jugando()

    def test_continuar_una_partida_no_repite_el_periodico(self, juego):
        """El anuncio cuenta de dónde salió el trabajo: solo hace falta una
        vez, al empezar."""
        juego.iniciar_noche(solicitud_de(3))
        assert juego.gestor_estados.estado is EstadoJuego.TARJETA_NOCHE

    def test_sin_el_arte_del_periodico_se_salta_esa_pantalla(self, juego, monkeypatch):
        """Un archivo que falta no puede convertirse en veinte segundos de
        pantalla negra sin explicación."""
        monkeypatch.setattr(juego.periodico, "hay_recorte", lambda: False)
        juego.iniciar_noche(solicitud_de(1, nueva_partida=True))
        assert juego.gestor_estados.estado is EstadoJuego.TARJETA_NOCHE

    def test_la_tarjeta_dice_la_noche_en_la_que_estas(self, juego):
        juego.iniciar_noche(solicitud_de(4))
        assert "4" in juego.tarjeta_noche.texto_noche()

    def test_la_tarjeta_siempre_marca_las_doce(self, juego):
        assert HORA_DE_ARRANQUE == "12:00 AM"

    def test_la_noche_personalizada_no_se_anuncia_con_numero(self, juego):
        """Su número está fuera de la campaña: "Noche 7" no le diría nada al
        jugador."""
        juego.iniciar_noche(solicitud_de(NOCHE_EXTRA + 1, personalizada=True))
        texto = juego.tarjeta_noche.texto_noche()
        assert str(NOCHE_EXTRA + 1) not in texto
        assert texto == juego.idiomas.t("menu_noche_personalizada")

    def test_el_reloj_de_la_noche_no_corre_durante_la_entrada(self, juego):
        """Si corriera, el jugador perdería minutos de noche leyendo."""
        juego.iniciar_noche(solicitud_de(1, nueva_partida=True))
        self._correr(juego, PERIODICO_SEGUNDOS - 1.0)
        assert juego.temporizador.progreso() == 0.0

    def test_las_pantallas_de_entrada_van_en_silencio(self, juego, monkeypatch):
        """La música del menú no puede seguir sonando encima del periódico:
        el corte es justo lo que separa el menú de la noche."""
        sonaron = []
        monkeypatch.setattr(juego.audio, "detener_musica", lambda: sonaron.append("silencio"))
        monkeypatch.setattr(
            juego.audio, "reproducir_musica", lambda *a, **k: sonaron.append("musica")
        )

        juego.iniciar_noche(solicitud_de(1, nueva_partida=True))
        juego._actualizar_musica()
        assert sonaron == ["silencio"]

        juego._mostrar_tarjeta_de_la_noche()
        juego._actualizar_musica()
        assert sonaron == ["silencio", "silencio"]

    def test_al_llegar_al_patio_vuelve_la_musica(self, juego, monkeypatch):
        pistas = []
        monkeypatch.setattr(juego.audio, "reproducir_musica", lambda pista, *a, **k: pistas.append(pista))
        empezar_noche(juego)
        juego._actualizar_musica()
        assert pistas == ["noche"]

    def test_nadie_se_mueve_durante_la_entrada(self, juego):
        juego.iniciar_noche(solicitud_de(NOCHE_CON_TODOS, nueva_partida=True))
        partida = {a.nombre: a.habitacion_actual for a in juego.noche.animatronics}
        self._correr(juego, PERIODICO_SEGUNDOS - 1.0)
        assert {
            a.nombre: a.habitacion_actual for a in juego.noche.animatronics
        } == partida


class TestAlumbrarALaChilindrina:
    """Su regla: jumpscare, la batería entera y nada más. Ni derrota, ni
    interrupción, ni aviso. Este era el fallo que llegaba al jugador: la
    partida se cortaba con 'Alumbraste a La Chilindrina'.
    """

    @pytest.mark.parametrize("id_posicion", VISTAS)
    def test_no_manda_al_game_over(self, juego, alumbrar, id_posicion):
        alumbrar(nombres.CHILINDRINA, id_posicion)
        assert _sigue_jugando(juego)
        assert juego.noche.derrota.nombre_atacante == ""

    @pytest.mark.parametrize("id_posicion", VISTAS)
    def test_deja_la_linterna_en_cero(self, juego, alumbrar, id_posicion):
        alumbrar(nombres.CHILINDRINA, id_posicion)
        assert juego.linterna.carga == 0.0
        assert not juego.linterna.encendida

    def test_no_saca_ningun_aviso(self, juego, alumbrar):
        """Se entera porque se quedó a oscuras, no porque se lo escriban."""
        alumbrar(nombres.CHILINDRINA)
        assert juego.aviso.texto == ""

    def test_no_se_la_quita_de_encima(self, juego, alumbrar):
        """La luz es el castigo, no la contramedida: para que se vaya hay que
        darle su paleta o su balero."""
        chilindrina = alumbrar(nombres.CHILINDRINA)
        assert chilindrina.esta_acechando()

    def test_verla_en_el_monitor_no_cuesta_bateria(self, juego, alumbrar):
        """Dentro del barril con las cámaras levantadas el haz no sale al
        patio: mirarla por el monitor no es alumbrarla."""
        alumbrar(
            nombres.CHILINDRINA,
            POSICION_DENTRO_BARRIL,
            camaras_levantadas=True,
        )
        assert juego.linterna.carga > 0.0


class TestAlumbrarAlResto:
    @pytest.mark.parametrize("nombre", MUEREN_POR_LA_LUZ)
    @pytest.mark.parametrize("id_posicion", VISTAS)
    def test_a_quien_le_mata_la_luz_se_pierde_la_noche(
        self, juego, alumbrar, nombre, id_posicion
    ):
        alumbrar(nombre, id_posicion)
        assert not _sigue_jugando(juego)
        assert juego.noche.derrota.clave_motivo == "game_over_luz"
        assert juego.noche.derrota.nombre_atacante == nombre

    @pytest.mark.parametrize(
        "nombre",
        [n for n in TODOS if n not in MUEREN_POR_LA_LUZ],
    )
    def test_nadie_mas_acaba_la_noche_por_alumbrarlo(self, juego, alumbrar, nombre):
        alumbrar(nombre)
        assert _sigue_jugando(juego)

    @pytest.mark.parametrize(
        "nombre",
        [n for n in TODOS if n not in MUEREN_POR_LA_LUZ + DESCARGAN_LA_LINTERNA],
    )
    def test_a_los_demas_la_luz_no_les_cuesta_la_bateria(
        self, juego, alumbrar, nombre
    ):
        """Solo el gasto normal del fotograma: nadie más se la vacía."""
        alumbrar(nombre)
        assert juego.linterna.carga > 0.0
