"""IA de los animatrónicos: movimiento por el grafo de cámaras, acecho y ataque."""

import random
from collections import Counter
from functools import lru_cache
from unittest.mock import patch

import pytest

from conftest import caminar_hasta_acechar, crear, ficha_de, llevar_a_acechar
from vecindad.config.partida import (
    DURACION_NOCHE_SEGUNDOS,
    INTERVALO_MOVIMIENTO_POR_DEFECTO,
    NIVEL_IA_MAXIMO,
    NIVEL_IA_MINIMO,
    SEGUNDOS_POR_HORA_NOCHE,
)
from vecindad.dominio.animatronicos import (
    ELENCO,
    INTERVALO_POR_NOCHE,
    VISTAS_DEL_PATIO,
    POSES_POR_PERSONAJE,
    Animatronic,
    crear_elenco_noche,
    crear_elenco_personalizado,
    hora_de_arranque,
    intervalo_de_movimiento,
    limitar_nivel_ia,
    nombres,
    nombres_del_elenco,
    niveles_iniciales_personalizada,
    validar_elenco,
)
from vecindad.mundo.habitaciones import HABITACION_JUGADOR

# El Chavo no tiene ninguna arista hacia el Primer Patio (solo llega si se le
# mira demasiado), Jaimico solo llega si no se encuentra su café a tiempo y
# Doña Clotilde nunca llega: mata desde su cámara. Los demás sí pueden llegar
# solos tirando el dado.
LLEGAN_SOLOS = [
    nombres.DON_RAMON, nombres.QUICO, nombres.CHILINDRINA, nombres.FLORINDA,
]

# Los que no empiezan en ninguna cámara: aparecen según su nivel.
APARECEN = [nombres.CHAVO, nombres.JAIMICO, nombres.CLOTILDE]

# Quienes pueden llegar a plantarse delante del jugador de una forma u otra.
LLEGAN_AL_PATIO = [c for c in ELENCO if not c.busqueda_mortal]


class TestNivelIA:
    def test_nivel_cero_deja_al_personaje_inactivo(self):
        assert not crear(nombres.QUICO, nivel_ia=NIVEL_IA_MINIMO).activo

    def test_nivel_uno_ya_lo_activa(self):
        assert crear(nombres.QUICO, nivel_ia=1).activo

    @pytest.mark.parametrize(
        "entrada,esperado", [(-5, 0), (0, 0), (10, 10), (20, 20), (99, 20)]
    )
    def test_el_nivel_se_recorta_a_su_rango(self, entrada, esperado):
        assert limitar_nivel_ia(entrada) == esperado

    def test_un_inactivo_nunca_intenta_moverse(self):
        quieto = crear(nombres.QUICO, nivel_ia=NIVEL_IA_MINIMO)
        assert not any(quieto.intentar_mover() for _ in range(200))

    def test_con_nivel_maximo_siempre_le_toca_moverse(self):
        lanzado = crear(nombres.QUICO, nivel_ia=NIVEL_IA_MAXIMO)
        assert all(lanzado.intentar_mover() for _ in range(200))


class TestRecorrido:
    def test_empieza_en_su_habitacion_inicial(self, quico):
        assert quico.habitacion_actual == quico.configuracion.habitacion_inicial
        assert not quico.esta_acechando()

    @pytest.mark.parametrize("nombre", LLEGAN_SOLOS)
    def test_el_recorrido_lleva_hasta_el_jugador(self, nombre):
        """Lo que de verdad importa de un grafo: que sus caminos desemboquen
        en el Primer Patio y no den vueltas para siempre."""
        assert caminar_hasta_acechar(crear(nombre, nivel_ia=10))

    def test_solo_se_mueve_a_donde_su_grafo_permite(self, quico):
        """Un destino fuera de la lista sería un personaje teletransportado a
        una cámara para la que no hay arte dibujado."""
        with patch(
            "vecindad.dominio.animatronicos.entidad.random.randint", return_value=1
        ):
            for _ in range(60):
                if quico.esta_acechando():
                    break
                permitidos = quico.destinos_posibles()
                quico.actualizar()
                assert quico.habitacion_actual in permitidos

    def test_al_llegar_arranca_la_cuenta_atras_del_ataque(self, quico):
        llevar_a_acechar(quico)
        assert quico.segundos_para_atacar == pytest.approx(quico.espera_de_ataque())

    def test_acechando_ya_no_se_mueve_mas(self, quico):
        """Del Primer Patio no se sale tirando el dado: solo con la
        contramedida que le toque a cada uno."""
        llevar_a_acechar(quico)
        for _ in range(50):
            quico.actualizar()
        assert quico.habitacion_actual == HABITACION_JUGADOR

    def test_todo_destino_alcanzable_tiene_salida(self):
        """Una cámara sin salida encerraría al personaje ahí el resto de la
        noche. Lo comprueba validar_elenco(), pero conviene verlo explícito."""
        for config in ELENCO:
            for origen, destinos in config.transiciones.items():
                for destino in destinos:
                    assert destino in config.transiciones, f"{config.nombre}: {destino}"


class TestPasosCondicionados:
    """Una arista que solo se abre si otro personaje está en cierta cámara.
    Hoy no la usa nadie del elenco (era de Doña Clotilde antes de que
    pasara a aparecer), así que se prueba con una ficha de prueba que se
    porta como se portaba ella: no se mueve del Segundo Patio hasta que Don
    Ramón esté donde necesita."""

    def _clotilde_en_el_patio(self):
        from vecindad.dominio.animatronicos.definicion import ConfiguracionAnimatronic

        ficha = ConfiguracionAnimatronic(
            nombre="Prueba",
            habitacion_inicial="segundo_patio",
            transiciones={
                "segundo_patio": (HABITACION_JUGADOR, "casa_clotilde"),
                "casa_clotilde": ("segundo_patio",),
                HABITACION_JUGADOR: ("casa_clotilde",),
            },
            condiciones_de_paso={
                ("segundo_patio", HABITACION_JUGADOR): (nombres.DON_RAMON, "entrada"),
                ("segundo_patio", "casa_clotilde"): (nombres.DON_RAMON, "casa_clotilde"),
            },
            puntos_acecho={vista: (0, 0) for vista in VISTAS_DEL_PATIO},
            espera_ataque_lenta=1.0,
            espera_ataque_rapida=1.0,
        )
        return Animatronic(ficha, nivel_ia=NIVEL_IA_MAXIMO)

    def test_sin_don_ramon_cerca_se_queda_donde_esta(self):
        bruja = self._clotilde_en_el_patio()
        ramon = crear(nombres.DON_RAMON, nivel_ia=10)
        ramon.habitacion_actual = "casa_ramon"
        assert bruja.destinos_posibles([bruja, ramon]) == ()
        for _ in range(30):
            bruja.actualizar([bruja, ramon])
        assert bruja.habitacion_actual == "segundo_patio"

    def test_con_don_ramon_en_la_reja_baja_sobre_el_jugador(self):
        bruja = self._clotilde_en_el_patio()
        ramon = crear(nombres.DON_RAMON, nivel_ia=10)
        ramon.habitacion_actual = "entrada"
        assert bruja.destinos_posibles([bruja, ramon]) == (HABITACION_JUGADOR,)

    def test_con_don_ramon_en_su_casa_se_devuelve(self):
        bruja = self._clotilde_en_el_patio()
        ramon = crear(nombres.DON_RAMON, nivel_ia=10)
        ramon.habitacion_actual = "casa_clotilde"
        assert bruja.destinos_posibles([bruja, ramon]) == ("casa_clotilde",)

    def test_un_don_ramon_inactivo_no_le_abre_el_paso(self):
        """En una noche personalizada Don Ramón puede estar en nivel 0. Si
        contara igual, la bruja avanzaría por alguien que no está jugando."""
        bruja = self._clotilde_en_el_patio()
        ramon = crear(nombres.DON_RAMON, nivel_ia=NIVEL_IA_MINIMO)
        ramon.habitacion_actual = "entrada"
        assert bruja.destinos_posibles([bruja, ramon]) == ()


class TestElAudioLaAtrae:
    """El audio de Quico lleva a Doña Florinda a la cámara donde suena, si
    es vecina de la suya. Si suena lejos, no lo oye."""

    @staticmethod
    def _florinda_en(camara):
        florinda = crear(nombres.FLORINDA, nivel_ia=10)
        florinda.habitacion_actual = camara
        return florinda

    def test_sus_vecinas_salen_de_su_recorrido_de_ida_y_vuelta(self):
        florinda = self._florinda_en("casa_popis")
        assert set(florinda.camaras_vecinas()) == {"casa_godinez", "segundo_patio"}

    def test_desde_el_segundo_patio_linda_con_las_casas_de_arriba(self):
        florinda = self._florinda_en("segundo_patio")
        assert set(florinda.camaras_vecinas()) == {
            "casa_popis", "casa_godinez", "casa_paty", "entrada",
        }

    def test_el_audio_la_lleva_a_casa_de_paty(self):
        """Solo llega ahí llevada por el audio, y hay arte para verla."""
        florinda = self._florinda_en("segundo_patio")
        assert florinda.atraer_a("casa_paty")
        assert florinda.habitacion_actual == "casa_paty"

    def test_de_casa_de_paty_vuelve_sola_al_segundo_patio(self):
        florinda = self._florinda_en("casa_paty")
        assert florinda.destinos_posibles() == ("segundo_patio",)

    def test_ponerle_el_audio_detras_la_hace_retroceder(self):
        florinda = self._florinda_en("casa_popis")
        assert florinda.atraer_a("casa_godinez")
        assert florinda.habitacion_actual == "casa_godinez"

    def test_ponerselo_delante_la_acerca(self):
        """Es el error que hay que evitar: el audio no siempre la aleja."""
        florinda = self._florinda_en("casa_popis")
        assert florinda.atraer_a("segundo_patio")
        assert florinda.habitacion_actual == "segundo_patio"

    def test_un_audio_lejos_no_lo_oye(self):
        florinda = self._florinda_en("segundo_patio")
        assert not florinda.atraer_a("casa_florinda")
        assert not florinda.atraer_a("casa_ramon")
        assert florinda.habitacion_actual == "segundo_patio"

    def test_en_su_misma_camara_no_la_mueve(self):
        florinda = self._florinda_en("casa_popis")
        assert not florinda.atraer_a("casa_popis")

    def test_desde_la_reja_ya_no_hace_caso(self):
        """Al llegar a la entrada el audio deja de servir: es el punto en el
        que el jugador ya no puede hacer nada más contra ella."""
        florinda = self._florinda_en("entrada")
        assert not florinda.atraer_a("segundo_patio")
        assert florinda.habitacion_actual == "entrada"

    def test_nunca_se_la_lleva_al_patio_con_un_audio(self):
        florinda = self._florinda_en("entrada")
        assert HABITACION_JUGADOR not in florinda.camaras_vecinas()
        assert not florinda.atraer_a(HABITACION_JUGADOR)

    def test_inactiva_no_se_mueve(self):
        florinda = self._florinda_en("casa_popis")
        florinda.activo = False
        assert not florinda.atraer_a("casa_godinez")


class TestAtaque:
    def test_no_ataca_mientras_le_quede_margen(self, quico):
        llevar_a_acechar(quico)
        assert not quico.descontar_espera(0.1)

    def test_ataca_al_agotarse_el_margen(self, quico):
        llevar_a_acechar(quico)
        assert quico.descontar_espera(quico.segundos_para_atacar + 0.01)

    def test_quien_no_acecha_no_puede_atacar(self, quico):
        assert not quico.descontar_espera(999.0)

    def test_ahuyentar_lo_saca_del_patio(self, quico):
        llevar_a_acechar(quico)
        quico.ahuyentar()
        assert not quico.esta_acechando()
        assert quico.segundos_para_atacar == 0.0

    @pytest.mark.parametrize("config", LLEGAN_AL_PATIO, ids=lambda c: c.nombre)
    def test_ahuyentar_lo_deja_por_donde_su_recorrido_dice(self, config):
        """Cada uno se va por su lado: Don Ramón sale por la reja o vuelve a
        su casa, La Chilindrina se va a la suya; El Chavo y Jaimico
        desaparecen (empiezan sin estar en ninguna cámara)."""
        animatronic = Animatronic(config, nivel_ia=10)
        llevar_a_acechar(animatronic)
        animatronic.ahuyentar()
        # Doña Florinda no tiene salida: llegar al Primer Patio la deja ahí,
        # porque alcanzar al jugador con ella acaba la noche. Para esos casos
        # ahuyentar() cae en su casa, que es un estado coherente igualmente.
        salidas = config.transiciones[HABITACION_JUGADOR] or (config.habitacion_inicial,)
        assert animatronic.habitacion_actual in salidas

    def test_don_ramon_da_catorce_segundos_en_su_nivel_mas_bajo(self):
        """El diseño fija ese margen: es lo que tiene el jugador para llamar
        al Sr. Barriga antes de que se lo lleve por delante."""
        assert crear(nombres.DON_RAMON, nivel_ia=1).espera_de_ataque() == pytest.approx(
            14.0
        )

    def test_a_mas_nivel_menos_margen_para_reaccionar(self):
        lento = crear(nombres.QUICO, nivel_ia=1)
        rapido = crear(nombres.QUICO, nivel_ia=NIVEL_IA_MAXIMO)
        assert rapido.espera_de_ataque() < lento.espera_de_ataque()


# Los dos que alcanzan al jugador metido en el barril. Son los que impiden
# que esconderse sea la respuesta a todo.
ROMPEN_EL_REFUGIO = [nombres.DON_RAMON, nombres.FLORINDA]
RESPETAN_EL_REFUGIO = [c for c in ELENCO if c.nombre not in ROMPEN_EL_REFUGIO]


class TestRefugioDelBarril:
    """Metido en el barril el jugador está a salvo de casi todos; el resto
    solo llega hasta él si cometió el error de alumbrarlos."""

    @pytest.mark.parametrize("nombre", ROMPEN_EL_REFUGIO)
    def test_don_ramon_y_florinda_alcanzan_dentro_del_barril(self, nombre):
        acechador = llevar_a_acechar(crear(nombre, nivel_ia=10))
        assert acechador.descontar_espera(999.0, jugador_escondido=True)

    @pytest.mark.parametrize(
        "config",
        RESPETAN_EL_REFUGIO,
        ids=lambda c: c.nombre,
    )
    def test_los_demas_no_pueden_tocarlo_escondido(self, config):
        """Este era el fallo: Quico mataba al jugador mientras miraba las
        cámaras desde dentro del barril."""
        acechador = llevar_a_acechar(Animatronic(config, nivel_ia=10))
        assert not acechador.descontar_espera(999.0, jugador_escondido=True)

    @pytest.mark.parametrize(
        "config",
        RESPETAN_EL_REFUGIO,
        ids=lambda c: c.nombre,
    )
    def test_alumbrarlos_les_abre_el_barril(self, config):
        """Usar la linterna para comprobar quién hay delante tiene precio:
        al que no mata la luz, lo activa."""
        acechador = llevar_a_acechar(Animatronic(config, nivel_ia=10))
        acechador.alumbrar()
        assert acechador.descontar_espera(999.0, jugador_escondido=True)

    def test_fuera_del_barril_todos_atacan(self, quico):
        llevar_a_acechar(quico)
        assert quico.descontar_espera(999.0, jugador_escondido=False)

    def test_escondido_el_margen_ni_siquiera_corre(self, quico):
        """No es que no mate: es que la cuenta atrás se detiene. Si siguiera
        corriendo, salir del barril sería morir al instante."""
        llevar_a_acechar(quico)
        antes = quico.segundos_para_atacar
        quico.descontar_espera(5.0, jugador_escondido=True)
        assert quico.segundos_para_atacar == antes

    def test_ahuyentarlo_le_quita_lo_activado(self, quico):
        llevar_a_acechar(quico)
        quico.alumbrar()
        quico.ahuyentar()
        assert not quico.activado

    def test_solo_se_activa_al_que_ya_llego(self, quico):
        """Alumbrar la cámara donde se le ve no cuenta: hay que tenerlo
        delante."""
        quico.alumbrar()
        assert not quico.activado


class TestReaccionALaLuz:
    def test_quien_no_teme_la_luz_no_tiene_radio_de_peligro(self, quico):
        assert quico.radio_peligro() == 0

    def test_quien_teme_la_luz_si_lo_tiene(self, don_ramon):
        assert don_ramon.radio_peligro() > 0

    def test_a_mas_nivel_mas_lejos_es_mortal_la_luz(self):
        flojo = crear(nombres.DON_RAMON, nivel_ia=1)
        bravo = crear(nombres.DON_RAMON, nivel_ia=NIVEL_IA_MAXIMO)
        assert bravo.radio_peligro() > flojo.radio_peligro()

    @pytest.mark.parametrize("vista", VISTAS_DEL_PATIO)
    def test_el_torso_queda_por_encima_de_los_pies(self, quico, vista):
        pies = quico.punto_acecho_en(vista)
        torso = quico.punto_torso_en(vista)
        assert torso[1] < pies[1]
        assert torso[0] == pies[0]

    def test_desde_un_sitio_sin_punto_no_hay_torso_al_que_apuntar(self, quico):
        assert quico.punto_acecho_en("dentro_barril") is None
        assert quico.punto_torso_en("dentro_barril") is None


class TestPoses:
    """Cuál de los diseños se le ve al personaje mientras acecha. Se sortea al
    llegar, para que no se le vea siempre igual."""

    def test_la_pose_esta_dentro_del_arte_que_existe(self, quico):
        llevar_a_acechar(quico)
        assert 1 <= quico.indice_pose() <= POSES_POR_PERSONAJE

    def test_no_siempre_llega_con_el_mismo_diseno(self):
        vistas = set()
        for _ in range(60):
            vistas.add(llevar_a_acechar(crear(nombres.DON_RAMON, 10)).indice_pose())
        assert len(vistas) > 1, f"siempre sale la misma pose: {vistas}"

    def test_la_pose_no_cambia_mientras_sigue_encima(self, quico):
        llevar_a_acechar(quico)
        antes = quico.clave_sprite()
        for _ in range(20):
            quico.actualizar()
        assert quico.clave_sprite() == antes

    def test_la_clave_de_sprite_nombra_al_personaje_y_su_pose(self, quico):
        llevar_a_acechar(quico)
        assert quico.clave_sprite() == f"{quico.nombre} {quico.indice_pose()}"


class TestElenco:
    def test_el_elenco_es_valido(self):
        validar_elenco()  # no debe lanzar

    def test_todos_pueden_acabar_donde_esta_el_jugador(self):
        for config in LLEGAN_AL_PATIO:
            assert HABITACION_JUGADOR in config.transiciones, config.nombre

    def test_dona_clotilde_nunca_llega_al_patio(self):
        """Mata desde su cámara si no se encuentra la escoba: en el patio no
        está nunca, aunque al aparecer se oiga como si estuviera."""
        assert HABITACION_JUGADOR not in ficha_de(nombres.CLOTILDE).habitaciones()

    def test_todos_empiezan_en_una_camara_de_su_recorrido(self):
        for config in ELENCO:
            for inicio in (config.habitacion_inicial, *config.aparece_en):
                if inicio is not None:
                    assert inicio in config.transiciones, config.nombre

    @pytest.mark.parametrize("nombre", APARECEN)
    def test_los_que_aparecen_no_empiezan_en_ninguna_camara(self, nombre):
        assert ficha_de(nombre).habitacion_inicial is None
        assert ficha_de(nombre).aparece_en

    def test_nadie_empieza_la_noche_encima_del_jugador(self):
        for config in ELENCO:
            assert config.habitacion_inicial != HABITACION_JUGADOR, config.nombre

    def test_no_hay_nombres_repetidos(self):
        assert len(set(nombres_del_elenco())) == len(ELENCO)

    def test_la_noche_personalizada_arranca_con_todos_en_cero(self):
        niveles = niveles_iniciales_personalizada()
        assert set(niveles) == set(nombres_del_elenco())
        assert all(nivel == NIVEL_IA_MINIMO for nivel in niveles.values())


class TestProgresionDeNoches:
    def test_la_noche_uno_solo_activa_a_tres_personajes(self):
        activos = [a.nombre for a in crear_elenco_noche(1) if a.activo]
        assert sorted(activos) == sorted(
            [nombres.DON_RAMON, nombres.QUICO, nombres.CHILINDRINA]
        )

    @pytest.mark.parametrize(
        "nombre,noche",
        [
            (nombres.DON_RAMON, 1), (nombres.QUICO, 1), (nombres.CHILINDRINA, 1),
            (nombres.FLORINDA, 2), (nombres.CHAVO, 3), (nombres.CLOTILDE, 3),
            (nombres.JAIMICO, 4),
        ],
    )
    def test_cada_personaje_debuta_en_la_noche_que_le_toca(self, nombre, noche):
        """El calendario de estrenos es parte del diseño de la campaña: cada
        noche presenta una mecánica nueva."""
        antes = {a.nombre for a in crear_elenco_noche(noche - 1) if a.activo}
        ahora = {a.nombre for a in crear_elenco_noche(noche) if a.activo}
        assert nombre not in antes, f"{nombre} ya salía en la noche {noche - 1}"
        assert nombre in ahora

    def test_el_elenco_siempre_tiene_a_todos_aunque_esten_inactivos(self):
        assert len(crear_elenco_noche(1)) == len(ELENCO)

    def test_la_dificultad_no_baja_de_una_noche_a_la_siguiente(self):
        for noche in range(1, 6):
            actual = {a.nombre: a.nivel_ia for a in crear_elenco_noche(noche)}
            siguiente = {a.nombre: a.nivel_ia for a in crear_elenco_noche(noche + 1)}
            for nombre, nivel in actual.items():
                assert siguiente[nombre] >= nivel, f"noche {noche + 1}: {nombre}"

    def test_el_elenco_crece_o_se_mantiene_cada_noche(self):
        for noche in range(1, 6):
            actuales = len([a for a in crear_elenco_noche(noche) if a.activo])
            siguientes = len([a for a in crear_elenco_noche(noche + 1) if a.activo])
            assert siguientes >= actuales, f"noche {noche + 1}"

    def test_una_noche_sin_tabla_deja_a_todos_quietos(self):
        assert not any(a.activo for a in crear_elenco_noche(99))

    def test_la_noche_uno_da_dos_horas_de_cortesia(self):
        assert hora_de_arranque(1) == 2

    def test_las_demas_noches_arrancan_a_las_doce(self):
        assert all(hora_de_arranque(n) == 0 for n in range(2, 7))


# ----------------------------------------------------------------------
# Medición del ritmo real de cada noche
# ----------------------------------------------------------------------
# Con recorridos en línea recta bastaba una fórmula: rondas x probabilidad
# entre número de etapas. Con grafos ya no, porque la distancia hasta el
# jugador depende de por dónde salga cada uno (Don Ramón puede plantarse en
# dos movimientos o perderse en casa de la bruja) y porque hay pasos que
# dependen de dónde esté otro personaje. Así que se mide jugando: se simula
# la noche entera muchas veces y se cuentan las llegadas.

SEMILLA_SIMULACION = 20260815
# Con 60 noches la media de quien va justo (Doña Clotilde en la noche 3,
# ~0,6 llegadas) bailaba por debajo del mínimo según cómo cayera la
# semilla. Con 300 la medición ya no depende de la suerte.
NOCHES_SIMULADAS = 300

# Veces que un personaje activo tiene que poder plantarse delante del jugador
# a lo largo de su noche para que valga la pena que salga. Media llegada es
# poco, pero en la noche 1 es lo que se busca: que aparezca de vez en cuando
# sin que la noche se convierta en un desfile.
LLEGADAS_MINIMAS = 0.5


def _rondas_de_la_noche(noche: int) -> int:
    segundos = DURACION_NOCHE_SEGUNDOS - (
        hora_de_arranque(noche) * SEGUNDOS_POR_HORA_NOCHE
    )
    return int(segundos / intervalo_de_movimiento(noche))


@lru_cache(maxsize=None)
def llegadas_por_noche(noche: int):
    """Cuántas veces llega de media cada personaje hasta el jugador.

    Se supone un jugador que siempre reacciona: en cuanto alguien se planta
    delante, lo ahuyenta y ese personaje vuelve a empezar. Es el número de
    veces que la noche le exige reaccionar, que es lo que se siente como
    dificultad. Doña Clotilde y Jaimico exigen reaccionar al aparecer (hay
    que buscar su objeto), así que para ellos se cuenta cada aparición y se
    da por encontrado el objeto.
    """
    llegadas = Counter()
    aleatorio = random.Random(SEMILLA_SIMULACION + noche)
    rondas = _rondas_de_la_noche(noche)
    with patch("vecindad.dominio.animatronicos.entidad.random", aleatorio):
        for _ in range(NOCHES_SIMULADAS):
            elenco = [a for a in crear_elenco_noche(noche) if a.activo]
            for _ in range(rondas):
                for animatronic in elenco:
                    animatronic.actualizar(elenco)
                for animatronic in elenco:
                    if animatronic.esta_acechando():
                        llegadas[animatronic.nombre] += 1
                        animatronic.ahuyentar()
                    elif animatronic.configuracion.objeto_buscado and animatronic.presente:
                        llegadas[animatronic.nombre] += 1
                        animatronic.desaparecer()
    activos = {a.nombre for a in crear_elenco_noche(noche) if a.activo}
    return {nombre: llegadas[nombre] / NOCHES_SIMULADAS for nombre in activos}


class TestRitmoDeLaNoche:
    """El intervalo entre rondas de movimiento es la palanca de dificultad."""

    def test_cada_noche_de_la_campana_tiene_su_ritmo(self):
        assert set(INTERVALO_POR_NOCHE) == set(range(1, 7))

    def test_la_noche_va_acelerando(self):
        for noche in range(1, 6):
            assert intervalo_de_movimiento(noche + 1) < intervalo_de_movimiento(noche)

    def test_ninguna_noche_corre_mas_rapido_que_el_reloj(self):
        """Un intervalo por debajo de un fotograma abriría varias rondas por
        cuadro y volvería el movimiento instantáneo."""
        assert all(intervalo > 1.0 for intervalo in INTERVALO_POR_NOCHE.values())

    def test_una_noche_fuera_de_la_campana_usa_el_ritmo_por_defecto(self):
        assert intervalo_de_movimiento(99) == INTERVALO_MOVIMIENTO_POR_DEFECTO

    @pytest.mark.parametrize("noche", range(1, 7))
    def test_nadie_activo_queda_de_adorno(self, noche):
        """Si a un personaje activo no le da el tiempo ni para llegar una vez,
        la calibración lo dejó fuera de juego: sale en la tabla de esa noche
        pero el jugador no llegaría a verlo nunca.

        El Chavo queda fuera de la cuenta porque no llega por su recorrido,
        sino solo si el jugador lo mira demasiado rato por la cámara."""
        for nombre, llegadas in llegadas_por_noche(noche).items():
            if nombre == nombres.CHAVO:
                continue
            assert llegadas >= LLEGADAS_MINIMAS, (
                f"noche {noche}: {nombre} llega solo {llegadas:.1f} veces"
            )

    def test_la_presion_total_sube_noche_a_noche(self):
        """Lo que el jugador siente no es el nivel de nadie en concreto, sino
        cuántas veces por noche tiene que reaccionar. Esa cuenta es la que
        tiene que crecer, y es la que hay que revisar al tocar intervalos,
        niveles, recorridos o el número de personajes activos."""
        totales = {
            noche: sum(llegadas_por_noche(noche).values()) for noche in range(1, 7)
        }
        for noche in range(1, 6):
            assert totales[noche + 1] > totales[noche], (
                f"noche {noche + 1} no aprieta más que la {noche}: "
                f"{totales[noche + 1]:.1f} vs {totales[noche]:.1f}"
            )

    def test_la_primera_noche_es_tranquila(self):
        """La noche 1 es el tutorial. El diseño pide que al jugador lo lleguen
        a atacar una o dos veces en toda la noche entre todos los activos: lo
        justo para aprender a reaccionar sin agobiarse."""
        total = sum(llegadas_por_noche(1).values())
        assert 1.0 <= total <= 3.0, f"noche 1: {total:.1f} llegadas"

    def test_la_noche_personalizada_usa_los_niveles_elegidos(self):
        elenco = crear_elenco_personalizado({nombres.CHAVO: 20})
        por_nombre = {a.nombre: a for a in elenco}
        assert por_nombre[nombres.CHAVO].nivel_ia == 20
        assert not por_nombre[nombres.QUICO].activo

    def test_un_nombre_desconocido_se_ignora_sin_romper(self):
        elenco = crear_elenco_personalizado({"Don Nadie": 20})
        assert len(elenco) == len(ELENCO)
        assert not any(a.activo for a in elenco)


def test_quien_empieza_en_el_patio_nace_ya_acechando():
    """Caso límite: si su cámara inicial es la del jugador, el personaje nace
    encima. La validación del elenco lo prohíbe, pero la entidad tiene que
    comportarse de forma coherente igualmente."""
    from vecindad.dominio.animatronicos.definicion import ConfiguracionAnimatronic

    ficha = ConfiguracionAnimatronic(
        nombre="Prueba",
        habitacion_inicial=HABITACION_JUGADOR,
        transiciones={HABITACION_JUGADOR: ("entrada",), "entrada": (HABITACION_JUGADOR,)},
        puntos_acecho={vista: (0, 0) for vista in VISTAS_DEL_PATIO},
        espera_ataque_lenta=1.0,
        espera_ataque_rapida=1.0,
    )
    assert Animatronic(ficha, nivel_ia=1).esta_acechando()


def test_el_chavo_no_llega_al_patio_por_su_cuenta():
    """Su mecánica es otra: solo aparece encima si el jugador lo mira
    demasiado rato por la cámara. Si su grafo lo llevara ahí solo, se
    saltaría esa regla."""
    chavo = ficha_de(nombres.CHAVO)
    for origen, destinos in chavo.transiciones.items():
        assert HABITACION_JUGADOR not in destinos, origen
