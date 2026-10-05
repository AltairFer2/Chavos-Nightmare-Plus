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
from vecindad.config.audio import (
    EFECTO_ENCENDIDO_CAMARAS,
    EFECTO_INTERFERENCIA,
    EFECTO_PASOS_DERECHA,
    EFECTO_PASOS_IZQUIERDA,
    EFECTO_SORPRESA,
)
from vecindad.config.interfaz import (
    CAMARA_ENCENDIDO_SEGUNDOS,
    CAMARA_SALIDA_SEGUNDOS,
    TIRAS_BLOQUEO_SEGUNDOS,
)
from vecindad.config.partida import (
    NOCHE_EXTRA,
    PERIODICO_SEGUNDOS,
    TARJETA_NOCHE_SEGUNDOS,
)
from vecindad.config.jugabilidad import (
    ARROJO_DURACION_VUELO_SEGUNDOS,
    CAMARA_INTERFERENCIA_MAXIMA_SEGUNDOS,
    CAMARA_INTERFERENCIA_MINIMA_SEGUNDOS,
    LINTERNA_BATERIAS_MAXIMAS,
)
from vecindad.config.ventana import ANCHO_PANTALLA
from vecindad.dominio.animatronicos import ELENCO, nombres
from vecindad.dominio.inventario import ORDEN_ARROJABLES
from vecindad.dominio.objetos import (
    ID_BALERO,
    ID_BATERIA,
    ID_CAFE_CHURRUMINO,
    ID_PALETA,
    ID_PELOTA_CUADRADA,
    ID_PELOTA_REDONDA,
    obtener_objeto,
)
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
    """Antes, quien se quitaba con un objeto no podía matar hasta que el
    sorteo del suelo le diera al jugador la respuesta. Ya no hay sorteo:
    cada objeto está en su sitio o a punto de volver, así que no tener con
    qué responder es haberlo gastado mal."""

    def test_quico_ataca_aunque_no_lleve_la_pelota(self, juego, plantar_delante):
        plantar_delante(nombres.QUICO)
        _correr(juego, 2.0)
        assert not _sigue_jugando(juego)
        assert juego.noche.derrota.nombre_atacante == nombres.QUICO


class TestArrojarConPunteria:
    """El objeto vuela adonde apunta el ratón y hace efecto al caer."""

    @pytest.fixture
    def apuntar(self, juego, monkeypatch):
        def _apuntar(punto):
            monkeypatch.setattr(juego.gestor_pantalla, "posicion_en_lienzo", lambda _: punto)
            juego.punto_luz = punto

        return _apuntar

    @pytest.fixture
    def quico_delante(self, juego, plantar_delante):
        quico = plantar_delante(nombres.QUICO)
        quico.segundos_para_atacar = MARGEN_INALCANZABLE
        return quico

    @staticmethod
    def _arrojar(juego, id_objeto):
        juego.inventario.guardar(id_objeto)
        juego._arrojar(ORDEN_ARROJABLES.index(id_objeto))

    def test_apuntarle_se_lo_lleva(self, juego, quico_delante, apuntar):
        apuntar(quico_delante.punto_torso_en(POSICION_BARRIL))
        self._arrojar(juego, ID_PELOTA_REDONDA)
        _correr(juego, ARROJO_DURACION_VUELO_SEGUNDOS)
        assert not quico_delante.esta_acechando()
        assert juego.objeto_en_vuelo is None

    def test_hace_efecto_al_caer_y_no_al_soltarlo(self, juego, quico_delante, apuntar):
        apuntar(quico_delante.punto_torso_en(POSICION_BARRIL))
        self._arrojar(juego, ID_PELOTA_REDONDA)
        juego._actualizar(FOTOGRAMA)
        assert quico_delante.esta_acechando()
        assert juego.objeto_en_vuelo is not None

    def test_apuntar_lejos_falla_y_lo_gasta(self, juego, quico_delante, apuntar):
        x, y = quico_delante.punto_torso_en(POSICION_BARRIL)
        apuntar((x + quico_delante.semiejes_acierto()[0] + 50, y))
        self._arrojar(juego, ID_PELOTA_REDONDA)
        _correr(juego, ARROJO_DURACION_VUELO_SEGUNDOS)
        assert quico_delante.esta_acechando()
        assert not juego.inventario.tiene(ID_PELOTA_REDONDA)
        assert juego.aviso.texto == juego.idiomas.t(
            "arrojo_fallado",
            objeto=juego.idiomas.t(obtener_objeto(ID_PELOTA_REDONDA).clave_texto),
        )

    def test_darle_con_lo_que_no_es_suyo_avisa_a_quien_le_dio(
        self, juego, quico_delante, apuntar
    ):
        apuntar(quico_delante.punto_torso_en(POSICION_BARRIL))
        self._arrojar(juego, ID_PALETA)
        _correr(juego, ARROJO_DURACION_VUELO_SEGUNDOS)
        assert quico_delante.esta_acechando()
        assert nombres.QUICO in juego.aviso.texto

    def test_mientras_uno_vuela_no_sale_otro(self, juego, quico_delante, apuntar):
        apuntar(quico_delante.punto_torso_en(POSICION_BARRIL))
        self._arrojar(juego, ID_PELOTA_REDONDA)
        self._arrojar(juego, ID_PELOTA_CUADRADA)
        assert juego.inventario.tiene(ID_PELOTA_CUADRADA)

    def test_cada_noche_empieza_sin_nada_en_el_aire(self, juego, quico_delante, apuntar):
        apuntar(quico_delante.punto_torso_en(POSICION_BARRIL))
        self._arrojar(juego, ID_PELOTA_REDONDA)
        empezar_noche(juego)
        assert juego.objeto_en_vuelo is None

    def test_a_jaimico_hay_que_alumbrarlo_cuando_le_llega(
        self, juego, plantar_delante, apuntar
    ):
        jaimico = plantar_delante(nombres.JAIMICO)
        jaimico.segundos_para_atacar = MARGEN_INALCANZABLE
        apuntar(jaimico.punto_torso_en(POSICION_BARRIL))
        juego.linterna.encendida = True
        self._arrojar(juego, ID_CAFE_CHURRUMINO)
        _correr(juego, ARROJO_DURACION_VUELO_SEGUNDOS)
        assert not jaimico.esta_acechando()

    def test_a_oscuras_jaimico_ignora_su_cafe(self, juego, plantar_delante, apuntar):
        jaimico = plantar_delante(nombres.JAIMICO)
        jaimico.segundos_para_atacar = MARGEN_INALCANZABLE
        apuntar(jaimico.punto_torso_en(POSICION_BARRIL))
        juego.linterna.encendida = False
        self._arrojar(juego, ID_CAFE_CHURRUMINO)
        _correr(juego, ARROJO_DURACION_VUELO_SEGUNDOS)
        assert jaimico.esta_acechando()


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
    """Si a alguien le toca moverse justo mientras se le está mirando, esa
    cámara se cae unos segundos: se oye que se fue, pero no se ve hacia
    dónde."""

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
        juego._cortar_la_senal_de_quien_se_movio(vigilados)
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

    def test_llegar_a_la_camara_mirada_no_la_tumba(self, vigilando, escuchar):
        """Lo que corta la señal es que se vaya quien estaba dentro; ver
        llegar a alguien es justo lo que se busca vigilando."""
        self._mover(vigilando, nombres.CHILINDRINA, self.CAMARA_VIGILADA)
        assert not vigilando.sistema_camaras.sin_senal(self.CAMARA_VIGILADA)
        assert escuchar == []

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


class TestRecogerDelSuelo:
    """Cada objeto tiene su sitio en los Lavaderos. Se recoge alumbrándolo y
    pulsando E, y no se lleva más de uno de cada a la vez."""

    @staticmethod
    def _en_los_lavaderos(juego, apuntando_a):
        empezar_noche(juego)
        for animatronic in juego.noche.animatronics:
            animatronic.activo = False
        juego.jugador.posicion = POSICION_LAVADEROS
        juego.linterna.encendida = True
        juego.punto_luz = obtener_objeto(apuntando_a).punto_suelo

    def test_alumbrarlo_y_recogerlo(self, juego):
        self._en_los_lavaderos(juego, ID_BALERO)
        juego._recoger_objeto()
        assert juego.inventario.tiene(ID_BALERO)
        assert not juego.objetos_en_suelo.esta(ID_BALERO)

    def test_a_oscuras_no_se_recoge_nada(self, juego):
        self._en_los_lavaderos(juego, ID_BALERO)
        juego.linterna.encendida = False
        juego._recoger_objeto()
        assert not juego.inventario.tiene(ID_BALERO)

    def test_desde_el_barril_no_se_recoge_nada(self, juego):
        self._en_los_lavaderos(juego, ID_BALERO)
        juego.jugador.posicion = POSICION_BARRIL
        juego._recoger_objeto()
        assert not juego.inventario.tiene(ID_BALERO)

    def test_se_recoge_el_que_esta_en_el_centro_del_haz(self, juego):
        """El haz alcanza a varios a la vez; se lleva el que apunta."""
        for id_objeto in (ID_PALETA, ID_BALERO, ID_PELOTA_REDONDA):
            self._en_los_lavaderos(juego, id_objeto)
            assert juego._objeto_a_la_vista() == id_objeto

    def test_no_se_lleva_dos_iguales(self, juego):
        self._en_los_lavaderos(juego, ID_BALERO)
        juego._recoger_objeto()
        juego.objetos_en_suelo.actualizar(juego.objetos_en_suelo.reaparicion)
        juego._recoger_objeto()
        assert juego.inventario.cantidad(ID_BALERO) == 1
        assert juego.objetos_en_suelo.esta(ID_BALERO)

    def test_con_el_bolsillo_lleno_la_bateria_se_queda(self, juego):
        self._en_los_lavaderos(juego, ID_BATERIA)
        juego.linterna.baterias_repuesto = LINTERNA_BATERIAS_MAXIMAS
        juego._recoger_objeto()
        assert juego.objetos_en_suelo.esta(ID_BATERIA)

    def test_la_bateria_va_al_bolsillo(self, juego):
        self._en_los_lavaderos(juego, ID_BATERIA)
        juego.linterna.baterias_repuesto = 0
        juego._recoger_objeto()
        assert juego.linterna.baterias_repuesto == 1

    def test_lo_recogido_vuelve_con_el_paso_de_la_noche(self, juego):
        self._en_los_lavaderos(juego, ID_BALERO)
        juego._recoger_objeto()
        _correr(juego, juego.objetos_en_suelo.reaparicion)
        assert juego.objetos_en_suelo.esta(ID_BALERO)


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
