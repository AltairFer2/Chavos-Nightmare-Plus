"""Los recursos de la noche: linterna, baterías del suelo, jugador,
temporizador y las dos averías de las cámaras."""

import pytest

from vecindad.config.jugabilidad import (
    BATERIA_ESPERA_POR_NOCHE,
    BATERIA_ESPERA_SEGUNDOS,
    BATERIA_PERMANENCIA_POR_NOCHE,
    BATERIA_PERMANENCIA_SEGUNDOS,
    BATERIAS_INICIALES_EN_BARRIL,
    CAMARA_INTERFERENCIA_MAXIMA_SEGUNDOS,
    CAMARA_INTERFERENCIA_MINIMA_SEGUNDOS,
    CAMARA_SABOTAJE_AVISO,
    CAMARA_SABOTAJE_POR_NOCHE,
    CAMARA_SABOTAJE_RECUPERACION,
    CAMARA_SABOTAJE_SEGUNDOS,
    LINTERNA_BATERIAS_MAXIMAS,
    LINTERNA_DURACION_BATERIA_SEGUNDOS,
    LINTERNA_RADIO,
    NOCHE_SIN_BATERIAS_FIJAS,
)
from vecindad.config.partida import (
    DURACION_NOCHE_SEGUNDOS,
    HORAS_DE_NOCHE,
    INTERVALO_MOVIMIENTO_POR_DEFECTO,
)
from vecindad.config.ventana import ALTO_PANTALLA, ANCHO_PANTALLA
from vecindad.dominio.jugador import Jugador
from vecindad.dominio.linterna import Linterna, baterias_iniciales, esta_iluminado
from vecindad.dominio.objetos import (
    CATALOGO,
    ID_BATERIA,
    OBJETOS_QUE_APARECEN,
    ObjetosEnElSuelo,
    espera_de_la_noche,
    obtener_objeto,
    permanencia_de_la_noche,
)
from vecindad.dominio.interferencia import InterferenciaCamaras
from vecindad.dominio.sabotaje import ControlSabotaje, aguante_de_la_noche
from vecindad.dominio.temporizador import TemporizadorNoche
from vecindad.mundo.posiciones import (
    POSICION_BARRIL,
    POSICION_DENTRO_BARRIL,
    POSICION_LAVADEROS,
    POSICIONES_CON_OBJETOS,
)

class TestLinterna:
    def test_arranca_apagada_y_con_la_bateria_llena(self):
        linterna = Linterna()
        assert not linterna.encendida
        assert linterna.carga == 1.0

    def test_encender_y_apagar(self):
        linterna = Linterna()
        assert linterna.alternar()
        assert not linterna.alternar()

    def test_apagada_no_gasta_bateria(self):
        linterna = Linterna()
        linterna.actualizar(60.0)
        assert linterna.carga == 1.0

    def test_encendida_gasta_bateria(self):
        linterna = Linterna()
        linterna.alternar()
        linterna.actualizar(LINTERNA_DURACION_BATERIA_SEGUNDOS / 2)
        assert linterna.carga == pytest.approx(0.5)

    def test_al_agotarse_se_apaga_sola(self):
        linterna = Linterna()
        linterna.alternar()
        linterna.actualizar(LINTERNA_DURACION_BATERIA_SEGUNDOS + 1)
        assert linterna.agotada
        assert not linterna.encendida

    def test_agotada_no_se_puede_encender(self):
        linterna = Linterna()
        linterna.carga = 0.0
        assert not linterna.alternar()

    def test_no_se_cambia_una_bateria_que_todavia_sirve(self):
        linterna = Linterna(baterias_repuesto=1)
        assert not linterna.cambiar_bateria()
        assert linterna.baterias_repuesto == 1

    def test_agotada_y_con_repuesto_si_se_cambia(self):
        linterna = Linterna(baterias_repuesto=1)
        linterna.carga = 0.0
        assert linterna.cambiar_bateria()
        assert linterna.carga == 1.0
        assert linterna.baterias_repuesto == 0

    def test_agotada_y_sin_repuesto_no_hay_nada_que_hacer(self):
        linterna = Linterna(baterias_repuesto=0)
        linterna.carga = 0.0
        assert not linterna.cambiar_bateria()

    def test_el_bolsillo_tiene_tope(self):
        """Acaparar baterías no puede ser una estrategia."""
        linterna = Linterna(baterias_repuesto=LINTERNA_BATERIAS_MAXIMAS)
        assert linterna.baterias_llenas
        assert not linterna.guardar_bateria()
        assert linterna.baterias_repuesto == LINTERNA_BATERIAS_MAXIMAS

    def test_con_sitio_si_guarda_la_bateria(self):
        linterna = Linterna(baterias_repuesto=LINTERNA_BATERIAS_MAXIMAS - 1)
        assert not linterna.baterias_llenas
        assert linterna.guardar_bateria()
        assert linterna.baterias_llenas

    def test_gastar_una_deja_sitio_otra_vez(self):
        linterna = Linterna(baterias_repuesto=LINTERNA_BATERIAS_MAXIMAS)
        linterna.carga = 0.0
        assert linterna.cambiar_bateria()
        assert not linterna.baterias_llenas

    def test_la_noche_arranca_con_el_bolsillo_lleno(self):
        """Las primeras noches se empieza justo en el tope: si trajeran más
        de las que caben, sobrarían desde el primer segundo."""
        assert BATERIAS_INICIALES_EN_BARRIL <= LINTERNA_BATERIAS_MAXIMAS

    def test_las_primeras_noches_traen_baterias_en_el_barril(self):
        assert baterias_iniciales(1) == BATERIAS_INICIALES_EN_BARRIL

    def test_desde_la_noche_cuatro_hay_que_buscarlas_todas(self):
        assert baterias_iniciales(NOCHE_SIN_BATERIAS_FIJAS) == 0


class TestHazDeLuz:
    def test_el_centro_del_haz_ilumina(self):
        assert esta_iluminado((100, 100), (100, 100))

    def test_justo_dentro_del_radio_ilumina(self):
        assert esta_iluminado((100 + LINTERNA_RADIO - 1, 100), (100, 100))

    def test_fuera_del_radio_no_ilumina(self):
        assert not esta_iluminado((100 + LINTERNA_RADIO + 1, 100), (100, 100))

    def test_sin_punto_de_luz_no_se_ilumina_nada(self):
        assert not esta_iluminado((100, 100), None)


class TestCatalogoDeObjetos:
    def test_pedir_un_objeto_inexistente_falla(self):
        with pytest.raises(ValueError):
            obtener_objeto("chipote_de_oro")

    def test_solo_se_encuentran_baterias(self):
        """Ya no hay objetos que arrojar: la defensa es la linterna."""
        assert OBJETOS_QUE_APARECEN == (ID_BATERIA,)

    def test_el_id_del_objeto_coincide_con_su_clave(self):
        assert all(clave == objeto.id for clave, objeto in CATALOGO.items())


def suelo_con_bateria(noche=1):
    """Un suelo al que ya le salió la batería."""
    suelo = ObjetosEnElSuelo(noche)
    suelo.actualizar(suelo.espera)
    assert suelo.esta(ID_BATERIA)
    return suelo


class TestBateriasEnElSuelo:
    def test_la_noche_arranca_con_el_suelo_vacio(self):
        suelo = ObjetosEnElSuelo(1)
        assert suelo.actual is None
        assert suelo.objetos_en(POSICION_LAVADEROS) == ()

    def test_tras_la_espera_aparece_justo_a_tiempo(self):
        """Sin sorteo: el ritmo se puede aprender."""
        suelo = ObjetosEnElSuelo(1)
        suelo.actualizar(suelo.espera - 0.5)
        assert suelo.actual is None
        assert suelo.segundos_para_aparecer() == pytest.approx(0.5)
        suelo.actualizar(0.5)
        assert suelo.actual == ID_BATERIA

    def test_solo_hay_objetos_en_los_lavaderos(self):
        """Es el único sitio del patio donde el jugador puede rebuscar; en el
        barril está asomado y dentro no ve el suelo."""
        assert POSICIONES_CON_OBJETOS == (POSICION_LAVADEROS,)
        assert suelo_con_bateria().objetos_en(POSICION_BARRIL) == ()

    def test_su_sitio_esta_dentro_del_lienzo(self):
        x, y = obtener_objeto(ID_BATERIA).punto_suelo
        assert 0 <= x <= ANCHO_PANTALLA and 0 <= y <= ALTO_PANTALLA

    def test_recogerla_deja_el_suelo_vacio(self):
        suelo = suelo_con_bateria()
        assert suelo.recoger(ID_BATERIA)
        assert suelo.actual is None
        assert not suelo.recoger(ID_BATERIA)

    def test_tras_recogerla_vuelve_a_correr_la_espera(self):
        suelo = suelo_con_bateria()
        suelo.recoger(ID_BATERIA)
        suelo.actualizar(suelo.espera - 0.5)
        assert suelo.actual is None
        suelo.actualizar(0.5)
        assert suelo.actual == ID_BATERIA

    def test_si_nadie_la_recoge_se_va(self):
        suelo = suelo_con_bateria()
        suelo.actualizar(suelo.permanencia - 0.5)
        assert suelo.esta(ID_BATERIA)
        assert suelo.segundos_para_irse() == pytest.approx(0.5)
        suelo.actualizar(0.5)
        assert suelo.actual is None

    def test_con_el_suelo_vacio_no_hay_cuenta_para_irse(self):
        assert ObjetosEnElSuelo(1).segundos_para_irse() == 0.0

    @pytest.mark.parametrize("noche", sorted(BATERIA_ESPERA_POR_NOCHE))
    def test_cada_noche_usa_sus_tiempos(self, noche):
        suelo = ObjetosEnElSuelo(noche)
        assert suelo.espera == BATERIA_ESPERA_POR_NOCHE[noche]
        assert suelo.permanencia == BATERIA_PERMANENCIA_POR_NOCHE[noche]

    def test_la_personalizada_usa_los_tiempos_por_defecto(self):
        assert espera_de_la_noche(99) == BATERIA_ESPERA_SEGUNDOS
        assert permanencia_de_la_noche(99) == BATERIA_PERMANENCIA_SEGUNDOS

    def test_las_noches_tardias_aprietan_mas(self):
        """Salen más espaciadas y duran menos tiradas."""
        esperas = [espera_de_la_noche(n) for n in range(1, 7)]
        permanencias = [permanencia_de_la_noche(n) for n in range(1, 7)]
        assert esperas == sorted(esperas) and esperas[-1] > esperas[0]
        assert permanencias == sorted(permanencias, reverse=True)
        assert permanencias[-1] < permanencias[0]


class TestJugador:
    def test_arranca_asomado_al_barril(self):
        assert Jugador().posicion == POSICION_BARRIL

    def test_camina_a_izquierda_y_derecha(self):
        jugador = Jugador()
        assert jugador.mover(-1)
        assert jugador.posicion == POSICION_LAVADEROS
        assert jugador.mover(1)
        assert jugador.posicion == POSICION_BARRIL

    def test_no_se_puede_pasar_de_los_extremos(self):
        """El patio tiene dos sitios y se acabó: a la reja no se sale. Todo lo
        que hay más allá solo se ve por las cámaras."""
        jugador = Jugador()
        assert not jugador.mover(1)
        assert jugador.posicion == POSICION_BARRIL
        jugador.mover(-1)
        assert not jugador.mover(-1)
        assert jugador.posicion == POSICION_LAVADEROS

    def test_meterse_y_salir_del_barril(self):
        jugador = Jugador()
        assert jugador.bajar()
        assert jugador.posicion == POSICION_DENTRO_BARRIL
        assert jugador.esta_escondido
        assert jugador.subir()
        assert not jugador.esta_escondido

    def test_solo_se_baja_al_barril_desde_el_barril(self):
        jugador = Jugador()
        jugador.mover(-1)  # lavaderos
        assert not jugador.bajar()

    def test_dentro_del_barril_no_se_busca_nada(self):
        jugador = Jugador()
        jugador.bajar()
        assert not jugador.puede_buscar

    def test_en_los_lavaderos_si_se_puede_buscar(self):
        jugador = Jugador()
        jugador.mover(-1)
        assert jugador.puede_buscar

    def test_asomado_al_barril_no_se_busca_nada(self):
        """Ahí está mirando el patio, no el suelo: para rebuscar hay que
        caminar hasta los lavaderos."""
        assert not Jugador().puede_buscar

    def test_reiniciar_lo_devuelve_al_barril(self):
        jugador = Jugador()
        jugador.bajar()
        jugador.reiniciar()
        assert jugador.posicion == POSICION_BARRIL


class EspiaAnimatronic:
    """Cuenta cuántas rondas de movimiento abrió el temporizador."""

    def __init__(self):
        self.rondas = 0

    def actualizar(self, elenco=()):
        self.rondas += 1


class TestTemporizador:
    def test_arranca_a_las_doce(self):
        assert TemporizadorNoche().hora_actual() == 12

    def test_a_mitad_de_noche_marca_las_tres(self):
        temporizador = TemporizadorNoche()
        temporizador.actualizar(DURACION_NOCHE_SEGUNDOS / 2)
        assert temporizador.hora_actual() == 3

    def test_la_noche_termina_a_las_seis(self):
        temporizador = TemporizadorNoche()
        temporizador.actualizar(DURACION_NOCHE_SEGUNDOS)
        assert temporizador.noche_terminada
        assert temporizador.hora_actual() == 6

    def test_una_vez_terminada_ya_no_avanza(self):
        temporizador = TemporizadorNoche()
        temporizador.actualizar(DURACION_NOCHE_SEGUNDOS)
        transcurrido = temporizador.segundos_transcurridos
        temporizador.actualizar(60.0)
        assert temporizador.segundos_transcurridos == transcurrido

    def test_el_progreso_va_de_cero_a_uno(self):
        temporizador = TemporizadorNoche()
        assert temporizador.progreso() == 0.0
        temporizador.actualizar(DURACION_NOCHE_SEGUNDOS * 2)
        assert temporizador.progreso() == 1.0

    def test_las_horas_transcurridas_no_pasan_del_total(self):
        temporizador = TemporizadorNoche()
        temporizador.actualizar(DURACION_NOCHE_SEGUNDOS * 2)
        assert temporizador.horas_transcurridas() == HORAS_DE_NOCHE

    def test_cada_ronda_mueve_al_elenco(self):
        espia = EspiaAnimatronic()
        temporizador = TemporizadorNoche(intervalo_movimiento=10.0)
        temporizador.actualizar(30.0, [espia])
        assert espia.rondas == 3

    def test_un_intervalo_mas_corto_abre_mas_rondas(self):
        lento, rapido = EspiaAnimatronic(), EspiaAnimatronic()
        TemporizadorNoche(intervalo_movimiento=40.0).actualizar(120.0, [lento])
        TemporizadorNoche(intervalo_movimiento=16.0).actualizar(120.0, [rapido])
        assert lento.rondas == 3
        assert rapido.rondas > lento.rondas

    def test_reiniciar_puede_cambiar_el_ritmo_de_la_noche(self):
        temporizador = TemporizadorNoche(intervalo_movimiento=40.0)
        temporizador.reiniciar(16.0)
        assert temporizador.intervalo_movimiento == 16.0

    def test_reiniciar_sin_intervalo_conserva_el_que_tenia(self):
        temporizador = TemporizadorNoche(intervalo_movimiento=40.0)
        temporizador.reiniciar()
        assert temporizador.intervalo_movimiento == 40.0

    @pytest.mark.parametrize("invalido", [0.0, -5.0])
    def test_un_intervalo_imposible_cae_al_por_defecto(self, invalido):
        """Con intervalo cero el bucle de rondas no terminaría nunca."""
        temporizador = TemporizadorNoche(intervalo_movimiento=invalido)
        assert temporizador.intervalo_movimiento == INTERVALO_MOVIMIENTO_POR_DEFECTO
        espia = EspiaAnimatronic()
        temporizador.actualizar(1.0, [espia])  # no debe colgarse
        assert espia.rondas == 0

    def test_reiniciar_devuelve_el_reloj_a_las_doce(self):
        temporizador = TemporizadorNoche()
        temporizador.actualizar(DURACION_NOCHE_SEGUNDOS)
        temporizador.reiniciar()
        assert not temporizador.noche_terminada
        assert temporizador.hora_actual() == 12


class TestSabotaje:
    def test_las_camaras_empiezan_sanas(self):
        assert not ControlSabotaje().averiadas

    def test_mirarlo_un_momento_no_las_rompe(self):
        control = ControlSabotaje()
        control.actualizar(control.aguante - 0.1, observado=True)
        assert not control.averiadas

    def test_mirarlo_demasiado_las_rompe(self):
        control = ControlSabotaje()
        control.actualizar(control.aguante, observado=True)
        assert control.averiadas

    @pytest.mark.parametrize("noche", sorted(CAMARA_SABOTAJE_POR_NOCHE))
    def test_cada_noche_aguanta_lo_suyo(self, noche):
        assert ControlSabotaje(noche).aguante == CAMARA_SABOTAJE_POR_NOCHE[noche]

    def test_las_noches_tardias_y_la_personalizada_aguantan_un_segundo(self):
        """El spec: 2 s en las noches 3 y 4, 1 s en el resto."""
        assert aguante_de_la_noche(5) == aguante_de_la_noche(6) == CAMARA_SABOTAJE_SEGUNDOS
        assert aguante_de_la_noche(99) == CAMARA_SABOTAJE_SEGUNDOS
        assert CAMARA_SABOTAJE_SEGUNDOS == 1.0
        assert CAMARA_SABOTAJE_POR_NOCHE == {3: 2.0, 4: 2.0}

    def test_dejar_de_mirarlo_enfria_la_presion(self):
        control = ControlSabotaje()
        control.actualizar(control.aguante / 2, observado=True)
        acumulado = control.presion
        control.actualizar(1.0, observado=False)
        assert control.presion == pytest.approx(acumulado - CAMARA_SABOTAJE_RECUPERACION)

    def test_los_vistazos_cortos_se_van_sumando(self):
        """Quitarle la vista y volver enseguida no basta: se enfría más
        despacio de lo que se calienta."""
        control = ControlSabotaje(3)
        for _ in range(10):
            control.actualizar(0.5, observado=True)
            control.actualizar(1.0, observado=False)
        assert control.averiadas

    def test_avisa_antes_de_romperlas(self):
        control = ControlSabotaje()
        assert not control.a_punto
        control.actualizar(control.aguante * CAMARA_SABOTAJE_AVISO, observado=True)
        assert control.a_punto
        assert not control.averiadas

    def test_ya_rotas_no_avisa(self):
        control = ControlSabotaje()
        control.actualizar(control.aguante, observado=True)
        assert not control.a_punto

    def test_la_presion_no_baja_de_cero(self):
        control = ControlSabotaje()
        control.actualizar(999.0, observado=False)
        assert control.presion == 0.0

    def test_una_vez_averiadas_siguen_asi_hasta_repararlas(self):
        control = ControlSabotaje()
        control.actualizar(control.aguante, observado=True)
        control.actualizar(999.0, observado=False)
        assert control.averiadas

    def test_reparar_las_deja_como_nuevas(self):
        control = ControlSabotaje()
        control.actualizar(control.aguante, observado=True)
        control.reparar()
        assert not control.averiadas
        assert control.presion == 0.0


class TestInterferencia:
    """El corte de señal de una sola cámara, el que se arregla solo. Cuándo
    se dispara es cosa del bucle (ver test_partida.py); aquí se mide cuánto
    dura y cómo se comporta."""

    def test_todas_empiezan_con_senal(self):
        assert not InterferenciaCamaras().sin_senal("casa_florinda")

    def test_cortar_la_deja_sin_senal(self):
        interferencia = InterferenciaCamaras()
        interferencia.cortar("casa_florinda")
        assert interferencia.sin_senal("casa_florinda")

    def test_el_corte_dura_lo_pactado(self):
        duracion = InterferenciaCamaras().cortar("casa_florinda")
        assert (
            CAMARA_INTERFERENCIA_MINIMA_SEGUNDOS
            <= duracion
            <= CAMARA_INTERFERENCIA_MAXIMA_SEGUNDOS
        )

    def test_solo_se_cae_la_cámara_cortada(self):
        interferencia = InterferenciaCamaras()
        interferencia.cortar("casa_florinda")
        assert not interferencia.sin_senal("casa_ramon")

    def test_pasado_el_rato_vuelve_sola(self):
        interferencia = InterferenciaCamaras()
        interferencia.cortar("casa_florinda")
        interferencia.actualizar(CAMARA_INTERFERENCIA_MAXIMA_SEGUNDOS)
        assert not interferencia.sin_senal("casa_florinda")

    def test_antes_del_minimo_sigue_caida(self):
        interferencia = InterferenciaCamaras()
        interferencia.cortar("casa_florinda")
        interferencia.actualizar(CAMARA_INTERFERENCIA_MINIMA_SEGUNDOS - 0.1)
        assert interferencia.sin_senal("casa_florinda")

    def test_cortar_dos_veces_no_alarga_el_corte(self):
        """Si cada movimiento reiniciara la cuenta, un personaje inquieto
        dejaría su cámara muerta el resto de la noche."""
        interferencia = InterferenciaCamaras()
        interferencia.cortar("casa_florinda")
        assert interferencia.cortar("casa_florinda") == 0.0

    def test_limpiar_devuelve_la_senal_a_todas(self):
        interferencia = InterferenciaCamaras()
        interferencia.cortar("casa_florinda")
        interferencia.cortar("casa_ramon")
        interferencia.limpiar()
        assert not interferencia.sin_senal("casa_florinda")
        assert not interferencia.sin_senal("casa_ramon")
