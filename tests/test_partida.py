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
from unittest.mock import patch

import pygame
import pytest

from vecindad.app.estados import EstadoJuego
from vecindad.config.audio import (
    ALERTA_PATIO_VOLUMEN,
    EFECTO_ALERTA_PATIO,
    EFECTO_EASTER_EGG,
    EFECTO_ENCENDIDO_CAMARAS,
    EFECTO_INTERFERENCIA,
    EFECTO_LLEGA_CHAVO,
    EFECTO_PASOS_DERECHA,
    EFECTO_PASOS_IZQUIERDA,
    EFECTO_RAMON_SE_VA,
    EFECTO_SORPRESA,
    EFECTOS_SALIDA_RAMON,
)
from vecindad.config.interfaz import (
    CAMARA_ENCENDIDO_SEGUNDOS,
    CAMARA_SALIDA_SEGUNDOS,
    TIRAS_BLOQUEO_SEGUNDOS,
)
from vecindad.config.partida import (
    NIVEL_IA_MAXIMO,
    NOCHE_EXTRA,
    PERIODICO_SEGUNDOS,
    TARJETA_NOCHE_SEGUNDOS,
)
from vecindad.config.jugabilidad import (
    AUDIO_QUICO_ESPERA_SEGUNDOS,
    BUSQUEDA_SEGUNDOS_MINIMOS,
    CAMARA_INTERFERENCIA_MAXIMA_SEGUNDOS,
    CAMARA_INTERFERENCIA_MINIMA_SEGUNDOS,
    CAMARA_SABOTAJE_POR_NOCHE,
    CAMARA_SABOTAJE_SEGUNDOS,
    CHILINDRINA_GRACIA_SEGUNDOS,
    LINTERNA_BATERIAS_MAXIMAS,
    SERVICIO_CAMARAS_SEGUNDOS,
)
from vecindad.config.ventana import ANCHO_PANTALLA
from vecindad.dominio.animatronicos import ELENCO, nombres
from vecindad.dominio.aparicion_rara import AparicionesRaras
from vecindad.dominio.busqueda import CAMARAS_CON_OBJETOS
from vecindad.dominio.objetos import ID_BATERIA, ObjetosEnElSuelo, obtener_objeto
from vecindad.dominio.servicios import Servicio
from vecindad.presentacion.hud import RECT_TIRA_BAJAR, RECT_TIRA_CAMARAS
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


def _correr(juego, segundos: float):
    for _ in range(int(segundos / FOTOGRAMA) + 1):
        juego._actualizar(FOTOGRAMA)


class TestYaNoHayTregua:
    """Nadie espera a que el jugador tenga con qué responder: la respuesta
    es la linterna, y quedarse sin batería o no atinarle es cosa suya."""

    def test_quico_ataca_si_no_se_le_espanta(self, juego, plantar_delante):
        plantar_delante(nombres.QUICO)
        _correr(juego, 2.0)
        assert not _sigue_jugando(juego)
        assert juego.noche.derrota.nombre_atacante == nombres.QUICO


class TestEspantarConLaLinterna:
    """La linterna como arma, en la partida de verdad: el haz sale del ratón
    y hay que sostenerlo sobre el punto débil hasta que se vaya."""

    @pytest.fixture
    def quico_delante(self, juego, plantar_delante):
        quico = plantar_delante(nombres.QUICO)
        quico.segundos_para_atacar = MARGEN_INALCANZABLE
        juego.jugador.posicion = POSICION_BARRIL
        juego.linterna.reiniciar(0)
        juego.linterna.encendida = True
        return quico

    @staticmethod
    def _seguir_el_punto(juego, monkeypatch, animatronic):
        """El ratón va siempre sobre su punto débil (o a su torso mientras
        el punto todavía no existe)."""
        def donde_apunta(_):
            punto = juego.espanto.punto_de(animatronic, POSICION_BARRIL)
            return punto if punto is not None else animatronic.punto_torso_en(POSICION_BARRIL)

        monkeypatch.setattr(juego.gestor_pantalla, "posicion_en_lienzo", donde_apunta)

    def test_sostenerle_la_luz_en_el_punto_lo_espanta(self, juego, monkeypatch, quico_delante):
        self._seguir_el_punto(juego, monkeypatch, quico_delante)
        _correr(juego, quico_delante.segundos_para_espantar() + 0.2)
        assert not quico_delante.esta_acechando()
        assert _sigue_jugando(juego)

    def test_espantarlo_gasta_bateria(self, juego, monkeypatch, quico_delante):
        self._seguir_el_punto(juego, monkeypatch, quico_delante)
        _correr(juego, quico_delante.segundos_para_espantar() + 0.2)
        assert juego.linterna.carga < 1.0

    def test_con_la_linterna_apagada_no_se_va(self, juego, monkeypatch, quico_delante):
        self._seguir_el_punto(juego, monkeypatch, quico_delante)
        juego.linterna.encendida = False
        _correr(juego, quico_delante.segundos_para_espantar() + 0.2)
        assert quico_delante.esta_acechando()

    def test_apuntarle_al_bulto_no_basta(self, juego, monkeypatch, quico_delante):
        """El haz de lleno sobre él no sirve: es el punto lo que cuenta."""
        x, y = quico_delante.punto_torso_en(POSICION_BARRIL)
        lejos_del_cuerpo = (x + 300, y)
        monkeypatch.setattr(juego.gestor_pantalla, "posicion_en_lienzo", lambda _: lejos_del_cuerpo)
        _correr(juego, quico_delante.segundos_para_espantar() + 0.2)
        assert quico_delante.esta_acechando()

    def test_cada_noche_empieza_sin_nada_sostenido(self, juego, monkeypatch, quico_delante):
        self._seguir_el_punto(juego, monkeypatch, quico_delante)
        _correr(juego, quico_delante.segundos_para_espantar() / 2)
        assert juego.espanto.progreso_de(quico_delante) > 0.0
        empezar_noche(juego)
        assert juego.espanto.progreso_de(quico_delante) == 0.0

    def test_ya_no_hay_teclas_de_arrojar(self, juego, quico_delante):
        juego._procesar_tecla(pygame.K_1)
        assert quico_delante.esta_acechando()


class TestLosPasosAvisanDeQuienLlega:
    """Unos pasos cada vez que alguien se planta en el patio. Dentro del
    barril con un panel levantado no se ve nada afuera: sin este aviso, la
    llegada sería invisible hasta que fuera tarde."""

    @pytest.fixture
    def escuchar(self, juego, monkeypatch):
        efectos = []
        monkeypatch.setattr(
            juego.audio, "reproducir_efecto", lambda nombre, *a, **k: efectos.append(nombre)
        )
        return efectos

    def _llegar(self, juego, nombre):
        """Hace aparecer a alguien delante como lo haría una ronda de
        movimiento, pasando por el aviso del bucle principal."""
        objetivo = next(a for a in juego.noche.animatronics if a.nombre == nombre)
        antes = juego._nombres_acechando()
        objetivo.irrumpir()
        juego._sonar_pasos_de_los_que_llegan(antes)
        return objetivo

    def test_al_plantarse_alguien_se_le_oye(self, juego, escuchar):
        empezar_noche(juego)
        self._llegar(juego, nombres.QUICO)
        assert escuchar == [EFECTO_PASOS_DERECHA]

    @pytest.mark.parametrize("config", ELENCO, ids=lambda c: c.nombre)
    def test_el_lado_dice_por_donde_apareció(self, juego, escuchar, config):
        empezar_noche(juego)
        llegado = self._llegar(juego, config.nombre)
        x, _ = llegado.punto_acecho_en(POSICION_BARRIL)
        esperado = (
            EFECTO_PASOS_IZQUIERDA if x < ANCHO_PANTALLA // 2 else EFECTO_PASOS_DERECHA
        )
        assert escuchar == [esperado]

    def test_quien_ya_estaba_delante_no_vuelve_a_sonar(self, juego, escuchar):
        empezar_noche(juego)
        self._llegar(juego, nombres.QUICO)
        escuchar.clear()
        juego._sonar_pasos_de_los_que_llegan(juego._nombres_acechando())
        assert escuchar == []

    def test_moverse_entre_camaras_no_suena(self, juego, escuchar):
        """Los pasos avisan de que hay alguien afuera, no de cada paso que
        dan por la vecindad: eso sería ruido constante."""
        empezar_noche(juego)
        quico = next(a for a in juego.noche.animatronics if a.nombre == nombres.QUICO)
        antes = juego._nombres_acechando()
        quico.habitacion_actual = "segundo_patio"
        juego._sonar_pasos_de_los_que_llegan(antes)
        assert escuchar == []


class TestBajarLosPanelesConElRaton:
    """Con el monitor levantado había que soltar el ratón e ir a buscar la
    tecla para volver al patio. Ahora la franja de abajo lo baja igual que lo
    sube: pasándole el ratón por encima, y el clic también vale."""

    @pytest.fixture
    def escondido(self, juego):
        empezar_noche(juego)
        juego.jugador.posicion = POSICION_DENTRO_BARRIL
        return juego

    def test_pasar_el_raton_por_la_pestana_baja_el_monitor(self, escondido):
        """El mismo gesto que lo sube: el jugador no tiene que aprenderse dos
        formas distintas para el mismo sitio de la pantalla."""
        escondido.sistema_camaras.activo = True
        escondido.punto_luz = RECT_TIRA_BAJAR.center
        escondido._atender_tiras()
        assert not escondido.sistema_camaras.activo

    def test_al_bajarlo_no_se_vuelve_a_levantar_solo(self, escondido):
        """La pestaña de subir ocupa esa misma franja: sin el seguro, bajar
        el monitor lo levantaba otra vez en el fotograma siguiente."""
        escondido.sistema_camaras.activo = True
        escondido.punto_luz = RECT_TIRA_BAJAR.center
        for _ in range(30):
            escondido._atender_tiras()
        assert not escondido.sistema_camaras.activo

    def test_sacar_el_raton_y_volver_lo_levanta_de_nuevo(self, escondido):
        escondido.sistema_camaras.activo = True
        escondido.punto_luz = RECT_TIRA_BAJAR.center
        escondido._atender_tiras()

        escondido.punto_luz = (10, 10)
        self._pasar_el_bloqueo(escondido)
        escondido._atender_tiras()

        escondido.punto_luz = RECT_TIRA_CAMARAS.center
        escondido._atender_tiras()
        assert escondido.sistema_camaras.activo

    def test_recien_bajado_no_responde_ni_saliendo_y_volviendo(self, escondido):
        """El bug de verdad: se baja el monitor y el ratón sigue ahí abajo,
        así que cualquier roce en ese instante lo levantaba otra vez."""
        self._bajar_con_el_raton(escondido)
        self._salir_y_volver(escondido)
        assert not escondido.sistema_camaras.activo

    def test_dentro_del_bloqueo_no_responde_aunque_se_salga_y_se_vuelva(self, escondido):
        self._bajar_con_el_raton(escondido)
        escondido._descontar_bloqueo_de_tiras(TIRAS_BLOQUEO_SEGUNDOS - 0.1)
        self._salir_y_volver(escondido)
        assert not escondido.sistema_camaras.activo

    def test_pasado_el_bloqueo_vuelven_a_responder(self, escondido):
        self._bajar_con_el_raton(escondido)
        escondido._descontar_bloqueo_de_tiras(TIRAS_BLOQUEO_SEGUNDOS)
        self._salir_y_volver(escondido)
        assert escondido.sistema_camaras.activo

    def test_el_bloqueo_no_estorba_a_la_tecla(self, escondido):
        """Es un seguro para el ratón: quien usa ESPACIO no se topa con el
        problema y no tiene por qué esperar."""
        escondido.sistema_camaras.activo = True
        escondido._bajar_paneles()
        escondido._procesar_tecla(pygame.K_SPACE)
        assert escondido.sistema_camaras.activo

    @staticmethod
    def _pasar_el_bloqueo(juego):
        juego._descontar_bloqueo_de_tiras(TIRAS_BLOQUEO_SEGUNDOS)

    @staticmethod
    def _bajar_con_el_raton(juego):
        """Baja el monitor por la pestaña, que es como se llega al bloqueo."""
        juego.sistema_camaras.activo = True
        juego.punto_luz = RECT_TIRA_BAJAR.center
        juego._atender_tiras()

    @staticmethod
    def _salir_y_volver(juego):
        """Aparta el cursor de la franja y lo trae de vuelta a la pestaña de
        subir: el gesto que volvía a levantar el monitor sin querer."""
        juego.punto_luz = (10, 10)
        juego._atender_tiras()
        juego.punto_luz = RECT_TIRA_CAMARAS.center
        juego._atender_tiras()

    def test_con_la_tecla_tampoco_se_levanta_solo(self, escondido):
        """Bajar con ESPACIO deja el cursor donde estaba, que bien puede ser
        encima de la pestaña de subir."""
        escondido.punto_luz = RECT_TIRA_CAMARAS.center
        escondido._atender_tiras()
        escondido._procesar_tecla(pygame.K_SPACE)
        escondido._atender_tiras()
        assert not escondido.sistema_camaras.activo

    def test_el_clic_en_la_pestana_baja_el_monitor(self, escondido):
        escondido.sistema_camaras.activo = True
        escondido._procesar_click(RECT_TIRA_BAJAR.center)
        assert not escondido.sistema_camaras.activo

    def test_tras_el_clic_tampoco_se_levanta_solo(self, escondido):
        escondido.sistema_camaras.activo = True
        escondido.punto_luz = RECT_TIRA_BAJAR.center
        escondido._procesar_click(RECT_TIRA_BAJAR.center)
        escondido._atender_tiras()
        assert not escondido.sistema_camaras.activo

    def test_el_clic_en_la_pestana_cierra_el_tablero(self, escondido):
        escondido.panel_servicios.activo = True
        escondido._procesar_click(RECT_TIRA_BAJAR.center)
        assert not escondido.panel_servicios.activo

    def test_el_clic_en_otro_sitio_sigue_eligiendo_camara(self, escondido):
        escondido.sistema_camaras.activo = True
        escondido._procesar_click((100, 100))
        assert escondido.sistema_camaras.activo

    def test_la_tecla_sigue_funcionando(self, escondido):
        escondido.sistema_camaras.activo = True
        escondido._procesar_tecla(pygame.K_SPACE)
        assert not escondido.sistema_camaras.activo

    def test_la_pestana_se_resalta_al_pasarle_el_raton(self, escondido):
        escondido.sistema_camaras.activo = True
        escondido.punto_luz = RECT_TIRA_BAJAR.center
        assert escondido._tira_resaltada() == "bajar"

    def test_con_el_raton_lejos_no_se_resalta(self, escondido):
        escondido.sistema_camaras.activo = True
        escondido.punto_luz = (10, 10)
        assert escondido._tira_resaltada() == ""

    def test_con_los_paneles_bajados_manda_la_pestaña_que_toca(self, escondido):
        """Sin panel delante, esa misma franja son las dos pestañas de subir:
        la de bajar no puede robarles el sitio."""
        escondido.punto_luz = RECT_TIRA_CAMARAS.center
        assert escondido._tira_resaltada() == "camaras"


class TestElMonitorEntraYSale:
    """Levantar el panel ya no es un cambio de pantalla instantáneo: el
    monitor baja del techo con su chasquido y, al bajarlo, se retira por
    donde vino. Hasta que termina no hay ninguna cámara que mirar."""

    @pytest.fixture
    def escuchar(self, juego, monkeypatch):
        efectos = []
        monkeypatch.setattr(
            juego.audio, "reproducir_efecto_camara", lambda nombre: efectos.append(nombre)
        )
        return efectos

    @pytest.fixture
    def escondido(self, juego):
        empezar_noche(juego)
        juego.jugador.posicion = POSICION_DENTRO_BARRIL
        return juego

    def test_hay_cuadros_de_encendido_en_disco(self, juego):
        """Sin los "pos N.png" no habría animación que probar, y el resto de
        esta clase pasaría sin comprobar nada."""
        assert juego.sistema_camaras.animacion.hay_animacion

    def test_la_pestana_lo_enciende(self, escondido, escuchar):
        escondido.punto_luz = RECT_TIRA_CAMARAS.center
        escondido._atender_tiras()
        assert escondido.sistema_camaras.activo
        assert escondido.sistema_camaras.animacion.en_marcha
        assert escuchar == [EFECTO_ENCENDIDO_CAMARAS]

    def test_la_tecla_tambien_lo_enciende(self, escondido, escuchar):
        escondido._procesar_tecla(pygame.K_SPACE)
        assert escondido.sistema_camaras.animacion.en_marcha
        assert escuchar == [EFECTO_ENCENDIDO_CAMARAS]

    def test_mientras_baja_no_se_ve_ninguna_camara(self, escondido):
        escondido._levantar_camaras()
        assert escondido.sistema_camaras.animacion.cuadro_actual() is not None

    def test_termina_sola_y_deja_ver_la_camara(self, escondido):
        escondido._levantar_camaras()
        self._correr(escondido, CAMARA_ENCENDIDO_SEGUNDOS + FOTOGRAMA)
        assert not escondido.sistema_camaras.animacion.en_marcha
        assert escondido.sistema_camaras.animacion.cuadro_actual() is None

    def test_el_chasquido_no_se_repite_mientras_siga_arriba(self, escondido, escuchar):
        """Con el ratón parado sobre la pestaña, _atender_tiras corre en cada
        fotograma: si el encendido no supiera que ya está arriba, sonaría en
        bucle."""
        escondido.punto_luz = RECT_TIRA_CAMARAS.center
        for _ in range(30):
            escondido._atender_tiras()
        assert escuchar.count(EFECTO_ENCENDIDO_CAMARAS) == 1

    def test_cambiar_de_camara_no_vuelve_a_encenderlo(self, escondido, escuchar):
        escondido._levantar_camaras()
        escuchar.clear()
        escondido.sistema_camaras.cambiar_camara("casa_florinda")
        assert not escuchar or EFECTO_ENCENDIDO_CAMARAS not in escuchar

    def test_al_bajarlo_el_monitor_se_retira(self, escondido):
        """Bajar no es cortar la animación: el aparato se va por donde vino."""
        escondido._levantar_camaras()
        self._correr(escondido, CAMARA_ENCENDIDO_SEGUNDOS + FOTOGRAMA)
        escondido._bajar_paneles()
        assert escondido.sistema_camaras.animacion.en_marcha

    def test_al_salir_solo_se_ve_un_cuadro(self, escondido):
        """Bajar es una urgencia: se enseña un cuadro y se quita, en vez de
        dejar el monitor medio segundo tapando el patio."""
        escondido._levantar_camaras()
        self._correr(escondido, CAMARA_ENCENDIDO_SEGUNDOS + FOTOGRAMA)

        escondido._bajar_paneles()
        saliendo = self._recorrer_cuadros(escondido)

        assert len(saliendo) == 1
        assert not escondido.sistema_camaras.animacion.en_marcha

    def test_la_salida_es_mas_corta_que_la_entrada(self, escondido):
        assert CAMARA_SALIDA_SEGUNDOS < CAMARA_ENCENDIDO_SEGUNDOS

        escondido._levantar_camaras()
        self._correr(escondido, CAMARA_ENCENDIDO_SEGUNDOS + FOTOGRAMA)
        escondido._bajar_paneles()
        self._correr(escondido, CAMARA_SALIDA_SEGUNDOS + FOTOGRAMA)
        assert not escondido.sistema_camaras.animacion.en_marcha

    def test_mientras_se_retira_no_se_ve_el_monitor_puesto(self, escondido):
        """Con el aparato aún moviéndose, lo que manda es el patio: si se
        diera por puesto, el monitor daría un salto en pantalla."""
        escondido._levantar_camaras()
        self._correr(escondido, CAMARA_ENCENDIDO_SEGUNDOS + FOTOGRAMA)
        assert escondido.sistema_camaras.a_la_vista

        escondido._bajar_paneles()
        assert not escondido.sistema_camaras.a_la_vista

    def test_empezar_la_noche_no_deja_animacion_a_medias(self, escondido):
        escondido._levantar_camaras()
        empezar_noche(escondido)
        assert not escondido.sistema_camaras.animacion.en_marcha
        assert not escondido.sistema_camaras.activo

    def test_volver_a_levantarlo_lo_enciende_otra_vez(self, escondido, escuchar):
        escondido._levantar_camaras()
        escondido._bajar_paneles()
        escondido._levantar_camaras()
        assert escondido.sistema_camaras.animacion.en_marcha
        assert escuchar.count(EFECTO_ENCENDIDO_CAMARAS) == 2

    def test_los_cuadros_dejan_ver_el_patio_alrededor(self, escondido):
        """El fondo negro de la lámina se recorta al cargarla; la pantalla
        del propio aparato, encerrada por el chasis, sigue siendo opaca."""
        cuadro = escondido.sistema_camaras.animacion._cuadros[0]
        assert cuadro.get_at((2, 2))[3] == 0, "la esquina tiene que ser transparente"
        # No se exige 255 exactos: al escalar la lámina al lienzo se
        # interpolan también los bordes del recorte.
        assert cuadro.get_at(cuadro.get_rect().center)[3] > 200, (
            "el centro cae dentro de la pantalla del monitor y va tapado"
        )

    @staticmethod
    def _recorrer_cuadros(juego):
        """Los cuadros distintos que se ven de principio a fin de la
        animación que esté corriendo."""
        vistos = []
        animacion = juego.sistema_camaras.animacion
        while animacion.en_marcha:
            cuadro = animacion.cuadro_actual()
            if not vistos or cuadro is not vistos[-1]:
                vistos.append(cuadro)
            juego._actualizar(FOTOGRAMA)
        return vistos

    @staticmethod
    def _correr(juego, segundos: float):
        for _ in range(int(segundos / FOTOGRAMA) + 1):
            juego._actualizar(FOTOGRAMA)


class TestLaSenalSeCaeAlMoverse:
    """Si alguien entra o sale de la cámara que se está mirando, esa cámara
    se cae unos segundos: se oye que alguien se movió, pero no se ve quién
    ni hacia dónde."""

    CAMARA_VIGILADA = "casa_florinda"

    @pytest.fixture
    def escuchar(self, juego, monkeypatch):
        efectos = []
        monkeypatch.setattr(
            juego.audio, "reproducir_efecto_camara", lambda nombre: efectos.append(nombre)
        )
        return efectos

    @pytest.fixture
    def vigilando(self, juego):
        """El jugador dentro del barril, mirando la cámara de la casa de Doña
        Florinda, que es donde arranca Quico."""
        empezar_noche(juego)
        juego.jugador.posicion = POSICION_DENTRO_BARRIL
        juego.sistema_camaras.activo = True
        juego.sistema_camaras.camara_actual = self.CAMARA_VIGILADA
        return juego

    def _mover(self, juego, nombre, destino):
        """Mueve a alguien como lo haría una ronda, pasando por el aviso del
        bucle principal."""
        objetivo = next(a for a in juego.noche.animatronics if a.nombre == nombre)
        vigilados = juego._quienes_se_ven()
        objetivo.habitacion_actual = destino
        juego._cortar_la_senal_si_cambio_quien_se_ve(vigilados)
        return objetivo

    def test_irse_de_la_camara_mirada_la_tumba(self, vigilando, escuchar):
        self._mover(vigilando, nombres.QUICO, "casa_paty")
        assert vigilando.sistema_camaras.sin_senal(self.CAMARA_VIGILADA)
        assert escuchar == [EFECTO_INTERFERENCIA]

    def test_moverse_en_otra_camara_no_tumba_nada(self, vigilando, escuchar):
        self._mover(vigilando, nombres.CHILINDRINA, "casa_paty")
        assert not vigilando.sistema_camaras.sin_senal(self.CAMARA_VIGILADA)
        assert escuchar == []

    def test_con_el_monitor_bajado_no_se_cae_ninguna(self, vigilando, escuchar):
        """La interferencia es lo que ve el jugador al mirar, no algo que
        pase a sus espaldas."""
        vigilando.sistema_camaras.activo = False
        self._mover(vigilando, nombres.QUICO, "casa_paty")
        assert not vigilando.sistema_camaras.sin_senal(self.CAMARA_VIGILADA)
        assert escuchar == []

    def test_llegar_a_la_camara_mirada_tambien_la_tumba(self, vigilando, escuchar):
        """Antes solo la cortaba quien se iba. Ahora también quien llega:
        se oye que alguien entró, pero no se ve quién hasta que vuelva la
        señal."""
        self._mover(vigilando, nombres.CHILINDRINA, self.CAMARA_VIGILADA)
        assert vigilando.sistema_camaras.sin_senal(self.CAMARA_VIGILADA)
        assert escuchar == [EFECTO_INTERFERENCIA]

    def test_la_senal_vuelve_sola(self, vigilando):
        """Esta avería no se restablece desde el barril: se arregla sola."""
        self._mover(vigilando, nombres.QUICO, "casa_paty")
        for _ in range(int(CAMARA_INTERFERENCIA_MAXIMA_SEGUNDOS / FOTOGRAMA) + 2):
            vigilando.sistema_camaras.actualizar(FOTOGRAMA)
        assert not vigilando.sistema_camaras.sin_senal(self.CAMARA_VIGILADA)

    def test_aguanta_al_menos_el_minimo(self, vigilando):
        self._mover(vigilando, nombres.QUICO, "casa_paty")
        for _ in range(int(CAMARA_INTERFERENCIA_MINIMA_SEGUNDOS / FOTOGRAMA) - 1):
            vigilando.sistema_camaras.actualizar(FOTOGRAMA)
        assert vigilando.sistema_camaras.sin_senal(self.CAMARA_VIGILADA)

    def test_otro_movimiento_no_alarga_el_corte(self, vigilando, escuchar):
        """Si cada movimiento reiniciara la cuenta, un personaje inquieto
        dejaría esa cámara muerta el resto de la noche."""
        self._mover(vigilando, nombres.QUICO, "casa_paty")
        escuchar.clear()
        self._mover(vigilando, nombres.FLORINDA, "casa_godinez")
        assert escuchar == []

    def test_empezar_la_noche_devuelve_la_senal(self, vigilando):
        self._mover(vigilando, nombres.QUICO, "casa_paty")
        empezar_noche(vigilando)
        assert not vigilando.sistema_camaras.sin_senal(self.CAMARA_VIGILADA)

    def test_una_ronda_de_verdad_tumba_la_camara(self, vigilando, escuchar, monkeypatch):
        """El fotograma completo: la ronda de movimiento la abre el
        temporizador dentro de _actualizar, y de ahí tiene que salir el corte
        sin que nadie lo llame a mano."""
        monkeypatch.setattr(
            "vecindad.dominio.animatronicos.entidad.random.randint", lambda *_: 1
        )
        vigilando._actualizar(vigilando.temporizador.intervalo_movimiento + FOTOGRAMA)
        assert vigilando.sistema_camaras.sin_senal(self.CAMARA_VIGILADA)
        assert EFECTO_INTERFERENCIA in escuchar


def _tirar_bateria(juego):
    """Deja la batería tirada en los Lavaderos sin esperar su turno."""
    suelo = ObjetosEnElSuelo(juego.noche.numero)
    suelo.actualizar(suelo.espera)
    juego.objetos_en_suelo = suelo


class TestRecogerDelSuelo:
    """Lo único que se encuentra son baterías, siempre en el mismo sitio de
    los Lavaderos. Se recogen alumbrándolas y pulsando E."""

    @staticmethod
    def _en_los_lavaderos(juego):
        empezar_noche(juego)
        for animatronic in juego.noche.animatronics:
            animatronic.activo = False
        _tirar_bateria(juego)
        juego.jugador.posicion = POSICION_LAVADEROS
        juego.linterna.encendida = True
        juego.linterna.baterias_repuesto = 0
        juego.punto_luz = obtener_objeto(ID_BATERIA).punto_suelo

    def test_la_noche_arranca_sin_nada_tirado(self, juego):
        empezar_noche(juego)
        assert juego.objetos_en_suelo.actual is None

    def test_la_bateria_va_al_bolsillo(self, juego):
        self._en_los_lavaderos(juego)
        juego._recoger_objeto()
        assert juego.linterna.baterias_repuesto == 1
        assert not juego.objetos_en_suelo.esta(ID_BATERIA)

    def test_a_oscuras_no_se_recoge_nada(self, juego):
        self._en_los_lavaderos(juego)
        juego.linterna.encendida = False
        juego._recoger_objeto()
        assert juego.linterna.baterias_repuesto == 0

    def test_desde_el_barril_no_se_recoge_nada(self, juego):
        self._en_los_lavaderos(juego)
        juego.jugador.posicion = POSICION_BARRIL
        juego._recoger_objeto()
        assert juego.linterna.baterias_repuesto == 0

    def test_hay_que_alumbrar_su_sitio(self, juego):
        self._en_los_lavaderos(juego)
        x, y = obtener_objeto(ID_BATERIA).punto_suelo
        juego.punto_luz = (x - 600, y)
        assert juego._objeto_a_la_vista() is None
        juego.punto_luz = (x, y)
        assert juego._objeto_a_la_vista() == ID_BATERIA

    def test_con_el_bolsillo_lleno_la_bateria_se_queda(self, juego):
        self._en_los_lavaderos(juego)
        juego.linterna.baterias_repuesto = LINTERNA_BATERIAS_MAXIMAS
        juego._recoger_objeto()
        assert juego.objetos_en_suelo.esta(ID_BATERIA)

    def test_tras_recogerla_sale_otra_con_el_paso_de_la_noche(self, juego):
        self._en_los_lavaderos(juego)
        juego._recoger_objeto()
        assert juego.objetos_en_suelo.actual is None
        _correr(juego, juego.objetos_en_suelo.espera)
        assert juego.objetos_en_suelo.actual == ID_BATERIA

    def test_si_no_la_recoge_se_va(self, juego):
        self._en_los_lavaderos(juego)
        _correr(juego, juego.objetos_en_suelo.permanencia)
        assert not juego.objetos_en_suelo.esta(ID_BATERIA)


class TestAtadoAlTablero:
    """Mientras un servicio restablece algo, el jugador no suelta el
    tablero: ni lo baja, ni cambia al monitor, ni se asoma."""

    @pytest.fixture
    def restableciendo(self, juego):
        empezar_noche(juego)
        for animatronic in juego.noche.animatronics:
            animatronic.activo = False
        juego.jugador.posicion = POSICION_DENTRO_BARRIL
        juego.panel_servicios.activo = True
        juego.aviso.limpiar()
        juego.servicios.usar(Servicio.CAMARAS, juego.noche.animatronics)
        assert juego.servicios.ocupado
        return juego

    def test_no_se_baja_el_tablero(self, restableciendo):
        restableciendo._bajar_paneles()
        assert restableciendo.panel_servicios.activo

    def test_avisa_por_que_no_se_puede(self, restableciendo):
        restableciendo._bajar_paneles()
        assert restableciendo.aviso.texto == restableciendo.idiomas.t("servicio_sin_terminar")

    def test_ni_pasando_el_raton_por_la_pestana(self, restableciendo):
        restableciendo.punto_luz = RECT_TIRA_BAJAR.center
        restableciendo._atender_tiras()
        assert restableciendo.panel_servicios.activo

    def test_ni_con_el_clic_en_la_pestana(self, restableciendo):
        restableciendo._procesar_click(RECT_TIRA_BAJAR.center)
        assert restableciendo.panel_servicios.activo

    def test_ni_con_la_tecla_del_tablero(self, restableciendo):
        restableciendo._procesar_tecla(pygame.K_TAB)
        assert restableciendo.panel_servicios.activo

    def test_no_se_cambia_a_las_camaras(self, restableciendo):
        restableciendo._procesar_tecla(pygame.K_SPACE)
        assert restableciendo.panel_servicios.activo
        assert not restableciendo.sistema_camaras.activo

    def test_no_se_asoma(self, restableciendo):
        restableciendo._asomarse()
        assert restableciendo.jugador.esta_escondido

    def test_al_terminar_ya_se_puede_bajar(self, restableciendo):
        _correr(restableciendo, SERVICIO_CAMARAS_SEGUNDOS)
        assert not restableciendo.servicios.ocupado
        restableciendo._bajar_paneles()
        assert not restableciendo.panel_servicios.activo

    def test_la_llamada_al_senor_barriga_no_ata(self, juego):
        """Es inmediata: no hay nada que esperar."""
        empezar_noche(juego)
        juego.jugador.posicion = POSICION_DENTRO_BARRIL
        juego.panel_servicios.activo = True
        juego.servicios.usar(Servicio.BARRIGA, juego.noche.animatronics)
        juego._bajar_paneles()
        assert not juego.panel_servicios.activo


class TestElChavoRompeLasCamaras:
    """Mirarlo uno o dos segundos en el monitor basta para que las rompa."""

    @staticmethod
    def _mirando_al_chavo(juego, noche):
        empezar_noche(juego, noche)
        chavo = next(a for a in juego.noche.animatronics if a.nombre == nombres.CHAVO)
        for animatronic in juego.noche.animatronics:
            animatronic.activo = animatronic is chavo
        chavo.habitacion_actual = juego.sistema_camaras.camara_actual
        juego.sistema_camaras.activo = True
        juego.sistema_camaras.animacion.cancelar()

    @staticmethod
    def _mirar(juego, segundos):
        for _ in range(int(segundos / FOTOGRAMA)):
            juego.sistema_camaras.actualizar(FOTOGRAMA, juego.noche.animatronics)

    @pytest.mark.parametrize("noche", (5, 6))
    def test_en_las_ultimas_noches_basta_un_segundo(self, juego, noche):
        self._mirando_al_chavo(juego, noche)
        self._mirar(juego, CAMARA_SABOTAJE_SEGUNDOS + 0.05)
        assert juego.sistema_camaras.averiadas

    @pytest.mark.parametrize("noche", sorted(CAMARA_SABOTAJE_POR_NOCHE))
    def test_en_las_noches_3_y_4_aguanta_su_tiempo(self, juego, noche):
        self._mirando_al_chavo(juego, noche)
        self._mirar(juego, CAMARA_SABOTAJE_POR_NOCHE[noche] - 0.2)
        assert not juego.sistema_camaras.averiadas
        self._mirar(juego, 0.3)
        assert juego.sistema_camaras.averiadas


class TestElSobresaltoAlVerlos:
    """Encontrarse a alguien plantado en el patio saca un "¡ay!" del jugador.
    Es su reacción al verlo, así que solo tiene sentido fuera del barril y
    una vez por encuentro."""

    @pytest.fixture
    def escuchar(self, juego, monkeypatch):
        efectos = []
        monkeypatch.setattr(
            juego.audio, "reproducir_efecto", lambda nombre, *a, **k: efectos.append(nombre)
        )
        return efectos

    def _plantar(self, juego, nombre=nombres.QUICO):
        objetivo = next(a for a in juego.noche.animatronics if a.nombre == nombre)
        objetivo.irrumpir()
        objetivo.segundos_para_atacar = MARGEN_INALCANZABLE
        return objetivo

    def test_al_aparecer_alguien_el_jugador_se_sobresalta(self, juego, escuchar):
        empezar_noche(juego)
        juego.jugador.posicion = POSICION_BARRIL
        self._plantar(juego)
        juego._reaccionar_a_lo_que_ve()
        assert EFECTO_SORPRESA in escuchar

    def test_no_se_repite_mientras_siga_delante(self, juego, escuchar):
        """Si sonara en cada fotograma sería un grito continuo."""
        empezar_noche(juego)
        juego.jugador.posicion = POSICION_BARRIL
        self._plantar(juego)
        for _ in range(30):
            juego._reaccionar_a_lo_que_ve()
        assert escuchar.count(EFECTO_SORPRESA) == 1

    def test_el_patio_vacio_no_sobresalta_a_nadie(self, juego, escuchar):
        empezar_noche(juego)
        juego.jugador.posicion = POSICION_BARRIL
        juego._reaccionar_a_lo_que_ve()
        assert EFECTO_SORPRESA not in escuchar

    def test_dentro_del_barril_no_suena(self, juego, escuchar):
        """Escondido no ve el patio: ahí el aviso son los pasos."""
        empezar_noche(juego)
        juego.jugador.posicion = POSICION_DENTRO_BARRIL
        self._plantar(juego)
        juego._reaccionar_a_lo_que_ve()
        assert EFECTO_SORPRESA not in escuchar

    def test_asomarse_y_encontrarselo_tambien_sobresalta(self, juego, escuchar):
        empezar_noche(juego)
        juego.jugador.posicion = POSICION_DENTRO_BARRIL
        self._plantar(juego)
        juego._reaccionar_a_lo_que_ve()

        juego.jugador.posicion = POSICION_BARRIL
        juego._reaccionar_a_lo_que_ve()
        assert escuchar.count(EFECTO_SORPRESA) == 1

    def test_si_se_va_y_llega_otro_vuelve_a_sonar(self, juego, escuchar):
        empezar_noche(juego)
        juego.jugador.posicion = POSICION_BARRIL
        quico = self._plantar(juego)
        juego._reaccionar_a_lo_que_ve()

        quico.ahuyentar()
        juego._reaccionar_a_lo_que_ve()

        self._plantar(juego, nombres.CHILINDRINA)
        juego._reaccionar_a_lo_que_ve()
        assert escuchar.count(EFECTO_SORPRESA) == 2

    def test_desde_los_lavaderos_tambien_se_le_ve(self, juego, escuchar):
        """El patio se ve entero desde sus dos ángulos."""
        empezar_noche(juego)
        juego.jugador.posicion = POSICION_LAVADEROS
        self._plantar(juego)
        juego._reaccionar_a_lo_que_ve()
        assert EFECTO_SORPRESA in escuchar


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
    """Su regla: la luz no la mata, se la espanta como a los demás, y
    alumbrarle el cuerpo fuera del punto débil más de un momento cuesta la
    batería entera. Ni derrota, ni interrupción, ni aviso."""

    @pytest.mark.parametrize("id_posicion", VISTAS)
    def test_no_manda_al_game_over(self, juego, alumbrar, id_posicion):
        alumbrar(nombres.CHILINDRINA, id_posicion)
        assert _sigue_jugando(juego)
        assert juego.noche.derrota.nombre_atacante == ""

    def test_un_vistazo_no_cuesta_la_bateria(self, juego, alumbrar):
        """Hay un momento de gracia para encontrar el punto."""
        alumbrar(nombres.CHILINDRINA)
        assert juego.linterna.carga > 0.0

    @pytest.mark.parametrize("id_posicion", VISTAS)
    def test_fallarle_el_punto_deja_la_linterna_en_cero(
        self, juego, alumbrar, monkeypatch, id_posicion
    ):
        chilindrina = alumbrar(nombres.CHILINDRINA, id_posicion)
        x, y = chilindrina.punto_torso_en(id_posicion)

        def lejos_del_punto(_):
            # Sobre su cuerpo, en el extremo más alejado del punto débil.
            punto = juego.espanto.punto_de(chilindrina, id_posicion) or (x, y)
            return max(((x, y - 80), (x, y), (x, y + 80)),
                       key=lambda c: (c[0] - punto[0]) ** 2 + (c[1] - punto[1]) ** 2)

        monkeypatch.setattr(juego.gestor_pantalla, "posicion_en_lienzo", lejos_del_punto)
        _correr(juego, CHILINDRINA_GRACIA_SEGUNDOS + 0.1)
        assert juego.linterna.carga == 0.0
        assert not juego.linterna.encendida
        assert juego.aviso.texto == ""

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


class TestReintentarTrasMorir:
    """Al perder, la pantalla de derrota ofrece reintentar la misma noche
    (marcado por defecto) o volver al menú."""

    @staticmethod
    def _morir(juego, numero=NOCHE_CON_TODOS, personalizada=False, niveles=None,
               nueva_partida=False):
        juego.iniciar_noche(SimpleNamespace(
            numero=numero, personalizada=personalizada,
            niveles_ia=niveles or {}, nueva_partida=nueva_partida,
        ))
        juego.periodico.termino = True
        juego.tarjeta_noche.termino = True
        while not juego.gestor_estados.jugando():
            juego._actualizar(FOTOGRAMA)
        juego._perder(nombres.QUICO, "game_over_motivo")
        for _ in range(int(10 / FOTOGRAMA)):
            if juego.gestor_estados.termino_en_derrota():
                return
            juego._actualizar(FOTOGRAMA)
        pytest.fail("no llegó a la pantalla de derrota")

    @staticmethod
    def _tecla(juego, tecla):
        juego._manejar_evento_derrota(pygame.event.Event(pygame.KEYDOWN, key=tecla), None)
        juego._atender_derrota()

    def test_reintentar_viene_marcado(self, juego):
        self._morir(juego)
        assert juego.menu_derrota.indice_seleccionado == 0

    def test_enter_reintenta_la_misma_noche(self, juego):
        self._morir(juego, numero=4)
        self._tecla(juego, pygame.K_RETURN)
        assert juego.gestor_estados.estado is EstadoJuego.TARJETA_NOCHE
        assert juego.noche.numero == 4
        assert juego.noche.derrota.nombre_atacante == ""

    def test_reintentar_deja_la_noche_como_nueva(self, juego):
        self._morir(juego)
        self._tecla(juego, pygame.K_RETURN)
        assert all(not a.esta_acechando() for a in juego.noche.animatronics)
        assert juego.temporizador.hora_actual() == 12

    def test_reintentar_tras_nuevo_juego_no_repite_el_periodico(self, juego):
        self._morir(juego, numero=1, nueva_partida=True)
        self._tecla(juego, pygame.K_RETURN)
        assert juego.gestor_estados.estado is EstadoJuego.TARJETA_NOCHE

    def test_la_personalizada_se_reintenta_con_sus_niveles(self, juego):
        niveles = {nombres.QUICO: 15, nombres.CHAVO: 4}
        self._morir(juego, numero=NOCHE_EXTRA, personalizada=True, niveles=niveles)
        self._tecla(juego, pygame.K_RETURN)
        assert juego.noche.personalizada
        quico = next(a for a in juego.noche.animatronics if a.nombre == nombres.QUICO)
        assert quico.nivel_ia == 15

    def test_abajo_y_enter_vuelve_al_menu(self, juego):
        self._morir(juego)
        self._tecla(juego, pygame.K_DOWN)
        self._tecla(juego, pygame.K_RETURN)
        assert juego.gestor_estados.en_menu()

    def test_clic_en_reintentar(self, juego):
        self._morir(juego)
        rect = juego.menu_derrota._rects()[0]
        evento = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center)
        juego._manejar_evento_derrota(evento, rect.center)
        juego._atender_derrota()
        assert juego.gestor_estados.estado is EstadoJuego.TARJETA_NOCHE

    def test_esc_sigue_cerrando_el_juego(self, juego):
        self._morir(juego)
        try:
            self._tecla(juego, pygame.K_ESCAPE)
            assert not juego._ejecutando
        finally:
            juego._ejecutando = True

    def test_cada_derrota_vuelve_a_marcar_reintentar(self, juego):
        self._morir(juego)
        self._tecla(juego, pygame.K_DOWN)
        self._tecla(juego, pygame.K_RETURN)
        self._morir(juego)
        assert juego.menu_derrota.indice_seleccionado == 0


@pytest.fixture
def efectos(juego, monkeypatch):
    """Lo que va sonando, en orden, sin pasar por la tarjeta de sonido."""
    sonados = []
    monkeypatch.setattr(juego.audio, "reproducir_efecto", lambda nombre, *a: sonados.append(nombre))
    monkeypatch.setattr(juego.audio, "reproducir_efecto_camara", lambda nombre: sonados.append(nombre))

    def al_azar(nombres, *a):
        sonados.append(nombres[0])
        return nombres[0]

    monkeypatch.setattr(juego.audio, "reproducir_efecto_al_azar", al_azar)
    return sonados


def _solo(juego, nombre):
    """Deja activo solo a ese personaje y devuelve su ficha viva."""
    elegido = next(a for a in juego.noche.animatronics if a.nombre == nombre)
    for animatronic in juego.noche.animatronics:
        animatronic.activo = animatronic is elegido
    return elegido


class TestElChavoLlegaAlRomperLasCamaras:
    @pytest.fixture
    def mirandolo(self, juego):
        empezar_noche(juego, 6)
        chavo = _solo(juego, nombres.CHAVO)
        juego.jugador.posicion = POSICION_DENTRO_BARRIL
        juego.sistema_camaras.activo = True
        juego.sistema_camaras.animacion.cancelar()
        chavo.habitacion_actual = juego.sistema_camaras.camara_actual = "casa_paty"
        return chavo

    def test_al_romperlas_aparece_en_el_patio(self, juego, mirandolo, efectos):
        _correr(juego, CAMARA_SABOTAJE_SEGUNDOS + 0.1)
        assert juego.sistema_camaras.averiadas
        assert mirandolo.esta_acechando()

    def test_suena_su_llegada(self, juego, mirandolo, efectos):
        _correr(juego, CAMARA_SABOTAJE_SEGUNDOS + 0.1)
        assert efectos.count(EFECTO_LLEGA_CHAVO) == 1

    def test_sin_romperlas_no_llega(self, juego, mirandolo, efectos):
        _correr(juego, CAMARA_SABOTAJE_SEGUNDOS / 2)
        assert not mirandolo.esta_acechando()
        assert EFECTO_LLEGA_CHAVO not in efectos

    def test_si_ya_estaba_en_el_patio_no_vuelve_a_llegar(self, juego, efectos):
        empezar_noche(juego, 6)
        chavo = _solo(juego, nombres.CHAVO)
        chavo.irrumpir()
        espera = chavo.segundos_para_atacar = 50.0
        juego._llega_el_chavo()
        assert chavo.segundos_para_atacar == espera
        assert efectos == []

    def test_hay_que_enfrentarlo(self, juego, mirandolo, efectos):
        """Fuera del barril, si no se le espanta, ataca."""
        _correr(juego, CAMARA_SABOTAJE_SEGUNDOS + 0.1)
        juego.sistema_camaras.activo = False
        juego.jugador.posicion = POSICION_BARRIL
        _correr(juego, mirandolo.segundos_para_atacar + 0.5)
        assert not _sigue_jugando(juego)
        assert juego.noche.derrota.nombre_atacante == nombres.CHAVO


class TestDonRamonSeVa:
    def test_suena_una_de_sus_salidas(self, juego, plantar_delante, efectos, monkeypatch):
        ramon = plantar_delante(nombres.DON_RAMON)
        juego.jugador.posicion = POSICION_DENTRO_BARRIL
        juego.panel_servicios.activo = True
        monkeypatch.setattr(juego.panel_servicios, "boton_en", lambda _: Servicio.BARRIGA)
        juego._usar_servicio((0, 0))
        assert not ramon.esta_acechando()
        assert EFECTOS_SALIDA_RAMON[0] in efectos

    def test_son_diez_variantes(self):
        assert EFECTOS_SALIDA_RAMON == tuple(f"salida_ramon_{n}" for n in range(1, 11))

    def test_sin_variantes_suena_la_de_siempre(self, juego, plantar_delante, monkeypatch):
        sonados = []
        monkeypatch.setattr(juego.audio, "reproducir_efecto", lambda nombre, *a: sonados.append(nombre))
        monkeypatch.setattr(juego.audio, "reproducir_efecto_al_azar", lambda *a: None)
        plantar_delante(nombres.DON_RAMON)
        juego.jugador.posicion = POSICION_DENTRO_BARRIL
        juego.panel_servicios.activo = True
        monkeypatch.setattr(juego.panel_servicios, "boton_en", lambda _: Servicio.BARRIGA)
        juego._usar_servicio((0, 0))
        assert EFECTO_RAMON_SE_VA in sonados


class TestAudioDeQuicoEnElMonitor:
    @pytest.fixture
    def florinda_en_popis(self, juego):
        empezar_noche(juego, 6)
        florinda = _solo(juego, nombres.FLORINDA)
        florinda.habitacion_actual = "casa_popis"
        juego._florinda_estaba = "casa_popis"
        juego.jugador.posicion = POSICION_DENTRO_BARRIL
        juego.sistema_camaras.activo = True
        juego.sistema_camaras.animacion.cancelar()
        return florinda

    def _sonar_en(self, juego, camara):
        juego.sistema_camaras.camara_actual = camara
        juego._sonar_audio_de_quico()

    def test_suena_en_la_camara_que_se_mira_y_la_atrae(self, juego, florinda_en_popis, efectos):
        self._sonar_en(juego, "casa_godinez")
        assert florinda_en_popis.habitacion_actual == "casa_godinez"
        assert juego.sistema_camaras.suena_audio_en("casa_godinez")

    def test_las_ondas_solo_se_ven_en_esa_camara(self, juego, florinda_en_popis, efectos):
        self._sonar_en(juego, "casa_paty")
        assert juego.sistema_camaras.suena_audio_en("casa_paty")
        assert not juego.sistema_camaras.suena_audio_en("casa_godinez")

    def test_lejos_de_ella_no_se_mueve(self, juego, florinda_en_popis, efectos):
        self._sonar_en(juego, "casa_paty")
        assert florinda_en_popis.habitacion_actual == "casa_popis"

    def test_al_entrar_en_la_camara_mirada_se_pierde_la_senal(self, juego, florinda_en_popis, efectos):
        self._sonar_en(juego, "casa_godinez")
        assert juego.sistema_camaras.sin_senal("casa_godinez")
        assert EFECTO_INTERFERENCIA in efectos

    def test_hay_que_esperar_para_volver_a_usarlo(self, juego, florinda_en_popis, efectos):
        self._sonar_en(juego, "casa_godinez")
        efectos.clear()
        self._sonar_en(juego, "casa_florinda")
        assert florinda_en_popis.habitacion_actual == "casa_godinez"
        assert efectos == []

    def test_pasada_la_espera_vuelve_a_servir(self, juego, florinda_en_popis, efectos):
        self._sonar_en(juego, "casa_godinez")
        _correr(juego, AUDIO_QUICO_ESPERA_SEGUNDOS)
        self._sonar_en(juego, "casa_florinda")
        assert florinda_en_popis.habitacion_actual == "casa_florinda"

    def test_al_moverse_distorsiona_el_monitor(self, juego, florinda_en_popis, efectos):
        self._sonar_en(juego, "casa_godinez")
        juego.sistema_camaras.camara_actual = "casa_paty"
        juego._actualizar(FOTOGRAMA)
        assert juego.sistema_camaras.distorsionada

    def test_moverse_por_su_cuenta_tambien_distorsiona(self, juego, florinda_en_popis):
        juego.sistema_camaras.camara_actual = "casa_paty"
        florinda_en_popis.habitacion_actual = "segundo_patio"
        juego._actualizar(FOTOGRAMA)
        assert juego.sistema_camaras.distorsionada

    def test_si_no_se_mueve_no_hay_distorsion(self, juego, florinda_en_popis):
        juego._actualizar(FOTOGRAMA)
        assert not juego.sistema_camaras.distorsionada


class TestAparicionesEnLaPartida:
    def test_al_aparecer_suena_y_no_cambia_nada_del_juego(self, juego, efectos):
        empezar_noche(juego, 1)
        juego.apariciones = AparicionesRaras(
            1, juego.imagenes_raras.cantidad,
            azar=SimpleNamespace(randrange=lambda tope: 0),
        )
        estado = juego.gestor_estados.estado
        carga = juego.linterna.carga
        _correr(juego, 1.0)
        assert juego.apariciones.visible
        assert EFECTO_EASTER_EGG in efectos
        assert juego.gestor_estados.estado is estado
        assert juego.linterna.carga == carga
        juego._dibujar()  # se dibuja sin fallar encima de la partida

    def test_cada_noche_usa_su_probabilidad(self, juego):
        empezar_noche(juego, 5)
        assert juego.apariciones.uno_entre == 5000
        empezar_noche(juego, 1)
        assert juego.apariciones.uno_entre == 10000


class TestAlertaDelPatio:
    """Con alguien en el patio suena un aviso en bucle y la imagen va y
    viene entre color y gris; las dos cosas apuran conforme se acerca el
    ataque."""

    @pytest.fixture
    def bucle(self, juego, monkeypatch):
        """Lo que se le pide al bucle de audio: el último volumen, o None si
        se mandó callar."""
        estado = {"volumen": None, "nombre": None}

        def sonar(nombre, subcarpeta, intensidad=1.0):
            estado["nombre"] = nombre
            estado["volumen"] = intensidad

        def callar():
            estado["volumen"] = None

        monkeypatch.setattr(juego.audio, "sonar_en_bucle", sonar)
        monkeypatch.setattr(juego.audio, "detener_bucle", callar)
        return estado

    @pytest.fixture
    def quico(self, juego):
        empezar_noche(juego, NOCHE_CON_TODOS)
        quico = _solo(juego, nombres.QUICO)
        quico.irrumpir()
        juego.jugador.posicion = POSICION_BARRIL
        return quico

    def _fotograma(self, juego):
        juego._actualizar(FOTOGRAMA)
        juego._sonar_alerta_del_patio()

    def test_con_el_patio_vacio_no_suena_ni_se_ve(self, juego, bucle):
        empezar_noche(juego, 1)
        for animatronic in juego.noche.animatronics:
            animatronic.activo = False
        self._fotograma(juego)
        assert bucle["volumen"] is None
        assert not juego.alerta_peligro.activa

    def test_con_alguien_en_el_patio_suena_y_se_ve(self, juego, bucle, quico):
        self._fotograma(juego)
        assert bucle["nombre"] == EFECTO_ALERTA_PATIO
        assert bucle["volumen"] == pytest.approx(ALERTA_PATIO_VOLUMEN[0], abs=0.05)
        assert juego.alerta_peligro.activa

    def test_tambien_suena_dentro_del_barril_mirando_las_camaras(self, juego, bucle, quico):
        juego.jugador.posicion = POSICION_DENTRO_BARRIL
        juego.sistema_camaras.activo = True
        juego.sistema_camaras.animacion.cancelar()
        self._fotograma(juego)
        assert bucle["volumen"] is not None
        juego._dibujar()  # el monitor también se tiñe, sin fallar

    def test_sube_conforme_se_acerca_el_ataque(self, juego, bucle, quico):
        self._fotograma(juego)
        al_llegar = bucle["volumen"]
        periodo_al_llegar = juego.alerta_peligro.periodo()
        quico.segundos_para_atacar = quico.espera_de_ataque() * 0.1
        self._fotograma(juego)
        assert bucle["volumen"] > al_llegar
        assert juego.alerta_peligro.periodo() < periodo_al_llegar

    def test_al_espantarlo_se_calla(self, juego, bucle, quico):
        self._fotograma(juego)
        quico.ahuyentar()
        self._fotograma(juego)
        assert bucle["volumen"] is None
        assert not juego.alerta_peligro.activa

    def test_al_morir_se_calla(self, juego, bucle, quico):
        quico.segundos_para_atacar = FOTOGRAMA / 2
        self._fotograma(juego)
        assert not _sigue_jugando(juego)
        assert bucle["volumen"] is None

    def test_en_pausa_sigue_y_al_salir_al_menu_se_calla(self, juego, bucle, quico):
        self._fotograma(juego)
        juego._pausar()
        juego._sonar_alerta_del_patio()
        assert bucle["volumen"] is not None
        juego.volver_al_menu()
        juego._sonar_alerta_del_patio()
        assert bucle["volumen"] is None

    def test_el_hud_no_se_tine(self, juego, quico, monkeypatch):
        """La hora y la batería se tienen que poder leer."""
        llamadas = []
        monkeypatch.setattr(
            juego.alerta_peligro, "dibujar", lambda superficie: llamadas.append("alerta")
        )
        monkeypatch.setattr(
            juego.interfaz, "dibujar_hud", lambda *a, **k: llamadas.append("hud")
        )
        self._fotograma(juego)
        juego._dibujar()
        assert llamadas == ["alerta", "hud"]


class TestBuscarEnLasCamaras:
    """La escoba de Doña Clotilde y el café de Jaimico: aparecen, su objeto
    se esconde en una cámara y hay que encontrarlo a tiempo."""

    @pytest.fixture
    def bruja(self, juego):
        empezar_noche(juego, NOCHE_CON_TODOS)
        bruja = _solo(juego, nombres.CLOTILDE)
        bruja.habitacion_actual = "entrada"
        juego.jugador.posicion = POSICION_DENTRO_BARRIL
        return bruja

    def _mirar(self, juego, camara):
        juego.sistema_camaras.activo = True
        juego.sistema_camaras.animacion.cancelar()
        juego.sistema_camaras.camara_actual = camara

    def _escoba(self, juego):
        (busqueda,) = juego.busquedas.activas
        return busqueda

    def test_al_aparecer_suena_y_se_ve_como_si_hubiera_alguien(self, juego, bruja, efectos):
        _correr(juego, FOTOGRAMA)
        assert set(efectos) & {EFECTO_PASOS_IZQUIERDA, EFECTO_PASOS_DERECHA}
        assert juego.alerta_peligro.activa
        assert juego._inminencia_del_peligro() is not None
        assert not bruja.esta_acechando()

    def test_si_no_se_encuentra_a_tiempo_mata(self, juego, bruja):
        _correr(juego, BUSQUEDA_SEGUNDOS_MINIMOS + 0.2)
        assert not _sigue_jugando(juego)
        assert juego.noche.derrota.nombre_atacante == nombres.CLOTILDE
        assert juego.noche.derrota.clave_motivo == "game_over_escoba"

    def test_mata_aunque_el_jugador_este_escondido(self, juego, bruja):
        juego.jugador.posicion = POSICION_DENTRO_BARRIL
        _correr(juego, BUSQUEDA_SEGUNDOS_MINIMOS + 0.2)
        assert not _sigue_jugando(juego)

    def test_encontrar_la_escoba_la_hace_desaparecer(self, juego, bruja):
        _correr(juego, FOTOGRAMA)
        escoba = self._escoba(juego)
        self._mirar(juego, escoba.camara)
        juego._procesar_click(escoba.punto)
        assert not bruja.presente
        assert juego.busquedas.activas == []
        # Que no vuelva a aparecer por azar mientras se mide.
        with patch("vecindad.dominio.animatronicos.entidad.random.random", return_value=0.99):
            _correr(juego, BUSQUEDA_SEGUNDOS_MINIMOS + 0.2)
        assert _sigue_jugando(juego)
        assert not juego.alerta_peligro.activa

    def test_mirando_otra_camara_no_se_encuentra(self, juego, bruja):
        _correr(juego, FOTOGRAMA)
        escoba = self._escoba(juego)
        otra = next(c for c in CAMARAS_CON_OBJETOS if c != escoba.camara)
        self._mirar(juego, otra)
        juego._procesar_click(escoba.punto)
        assert bruja.presente

    def test_con_las_camaras_rotas_no_se_ve(self, juego, bruja):
        _correr(juego, FOTOGRAMA)
        escoba = self._escoba(juego)
        self._mirar(juego, escoba.camara)
        juego.sistema_camaras._sabotaje.averiadas = True
        juego._procesar_click(escoba.punto)
        assert bruja.presente

    def test_sin_senal_no_se_ve(self, juego, bruja):
        _correr(juego, FOTOGRAMA)
        escoba = self._escoba(juego)
        self._mirar(juego, escoba.camara)
        juego.sistema_camaras.perder_senal(escoba.camara)
        juego._procesar_click(escoba.punto)
        assert bruja.presente

    def test_el_clic_cuenta_con_lo_que_tiembla_la_imagen(self, juego, bruja):
        _correr(juego, FOTOGRAMA)
        escoba = self._escoba(juego)
        self._mirar(juego, escoba.camara)
        juego.sistema_camaras.distorsionar()
        dx, dy = juego.sistema_camaras.desplazamiento_vista
        assert (dx, dy) != (0, 0)
        juego._procesar_click((escoba.punto[0] + dx, escoba.punto[1] + dy))
        assert not bruja.presente

    def test_se_dibuja_en_su_camara(self, juego, bruja):
        _correr(juego, FOTOGRAMA)
        escoba = self._escoba(juego)
        self._mirar(juego, escoba.camara)
        juego._dibujar()

    def test_jaimico_sin_cafe_se_planta_en_el_patio(self, juego, efectos):
        empezar_noche(juego, NOCHE_CON_TODOS)
        jaimico = _solo(juego, nombres.JAIMICO)
        jaimico.nivel_ia = NIVEL_IA_MAXIMO
        jaimico.habitacion_actual = "casa_jaimito"
        juego.jugador.posicion = POSICION_DENTRO_BARRIL
        _correr(juego, 7.2)
        assert jaimico.esta_acechando()
        assert _sigue_jugando(juego)

    def test_jaimico_con_su_cafe_encontrado_desaparece(self, juego):
        empezar_noche(juego, NOCHE_CON_TODOS)
        jaimico = _solo(juego, nombres.JAIMICO)
        jaimico.habitacion_actual = "casa_jaimito"
        juego.jugador.posicion = POSICION_DENTRO_BARRIL
        _correr(juego, FOTOGRAMA)
        (cafe,) = juego.busquedas.activas
        assert cafe.id_objeto == "cafe"
        self._mirar(juego, cafe.camara)
        juego._procesar_click(cafe.punto)
        assert not jaimico.presente

    def test_al_empezar_la_noche_no_estan_en_ninguna_camara(self, juego):
        empezar_noche(juego, NOCHE_CON_TODOS)
        for nombre in (nombres.CHAVO, nombres.JAIMICO, nombres.CLOTILDE):
            animatronic = next(a for a in juego.noche.animatronics if a.nombre == nombre)
            assert not animatronic.presente, nombre
        assert juego.busquedas.activas == []

    def test_reintentar_limpia_lo_que_quedaba_escondido(self, juego, bruja):
        _correr(juego, FOTOGRAMA)
        juego._reintentar()
        assert juego.busquedas.activas == []
