"""Los recursos de la noche: linterna, inventario, objetos del suelo,
jugador, temporizador y sabotaje de cámaras."""

import pytest

from vecindad.config.jugabilidad import (
    BATERIAS_INICIALES_EN_BARRIL,
    CAMARA_SABOTAJE_SEGUNDOS,
    LINTERNA_DURACION_BATERIA_SEGUNDOS,
    LINTERNA_RADIO,
    NOCHE_SIN_BATERIAS_FIJAS,
    OBJETO_INTERVALO_APARICION_SEGUNDOS,
)
from vecindad.config.partida import (
    DURACION_NOCHE_SEGUNDOS,
    HORAS_DE_NOCHE,
    INTERVALO_MOVIMIENTO_POR_DEFECTO,
)
from vecindad.dominio.inventario import ORDEN_ARROJABLES, Inventario
from vecindad.dominio.jugador import Jugador
from vecindad.dominio.linterna import Linterna, baterias_iniciales, esta_iluminado
from vecindad.dominio.objetos import (
    CATALOGO,
    ID_BATERIA,
    ID_CAFE,
    ID_CAFE_CHURRUMINO,
    ID_CHURRUMINO,
    OBJETOS_DEFENSIVOS,
    OBJETOS_UNICOS,
    ObjetosEnElSuelo,
    obtener_objeto,
)
from vecindad.dominio.sabotaje import ControlSabotaje
from vecindad.dominio.temporizador import TemporizadorNoche
from vecindad.mundo.posiciones import (
    POSICION_BARRIL,
    POSICION_DENTRO_BARRIL,
    POSICION_LAVADEROS,
    POSICIONES_CON_OBJETOS,
)

# Segundos que puede tardar de media en aparecer un objeto, contando que el
# jugador todavía tiene que ir hasta los Lavaderos, alumbrar el suelo y
# recogerlo. Es el tope que hace jugable la noche: los animatrónicos esperan
# a que tenga con qué responderles, así que un suelo lento no lo mata, pero
# lo deja encerrado en el barril sin poder hacer nada.
ESPERA_MAXIMA_POR_OBJETO = 20.0


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


class TestInventario:
    def test_empieza_vacio(self):
        assert Inventario().arrojables() == []

    def test_guardar_y_gastar(self):
        inventario = Inventario()
        inventario.guardar(ID_BATERIA)
        assert inventario.tiene(ID_BATERIA)
        assert inventario.gastar(ID_BATERIA)
        assert not inventario.tiene(ID_BATERIA)

    def test_no_se_puede_gastar_lo_que_no_se_lleva(self):
        assert not Inventario().gastar(ID_BATERIA)

    def test_las_baterias_se_acumulan(self):
        inventario = Inventario()
        inventario.guardar(ID_BATERIA)
        inventario.guardar(ID_BATERIA)
        assert inventario.cantidad(ID_BATERIA) == 2

    def test_guardar_un_objeto_inventado_falla(self):
        with pytest.raises(ValueError):
            Inventario().guardar("piedra_filosofal")

    def test_el_cafe_necesita_los_dos_ingredientes(self):
        inventario = Inventario()
        inventario.guardar(ID_CAFE)
        assert not inventario.puede_combinar_cafe()
        assert not inventario.combinar_cafe()

    def test_combinar_gasta_los_dos_y_deja_el_cafe_preparado(self):
        inventario = Inventario()
        inventario.guardar(ID_CAFE)
        inventario.guardar(ID_CHURRUMINO)
        assert inventario.combinar_cafe()
        assert not inventario.tiene(ID_CAFE)
        assert not inventario.tiene(ID_CHURRUMINO)
        assert inventario.tiene(ID_CAFE_CHURRUMINO)

    def test_los_arrojables_salen_en_el_orden_del_hud(self):
        inventario = Inventario()
        for id_objeto in reversed(ORDEN_ARROJABLES):
            inventario.guardar(id_objeto)
        assert inventario.arrojables() == ORDEN_ARROJABLES

    def test_reiniciar_lo_deja_vacio(self):
        inventario = Inventario()
        inventario.guardar(ID_BATERIA)
        inventario.reiniciar()
        assert not inventario.tiene(ID_BATERIA)

    def test_lo_que_lleva_encima_lo_puede_usar(self):
        inventario = Inventario()
        inventario.guardar(ID_CHURRUMINO)
        assert inventario.puede_usar(ID_CHURRUMINO)

    def test_recuerda_lo_que_gasto(self):
        """Gastarlo no borra que lo tuvo: de eso depende que un objeto
        malgastado no siga protegiendo al jugador (ver esta_en_tregua)."""
        inventario = Inventario()
        inventario.guardar(ID_CHURRUMINO)
        inventario.gastar(ID_CHURRUMINO)
        assert not inventario.tiene(ID_CHURRUMINO)
        assert inventario.tuvo(ID_CHURRUMINO)

    def test_no_recuerda_lo_que_nunca_recogio(self):
        assert not Inventario().tuvo(ID_CHURRUMINO)

    def test_la_memoria_se_borra_al_empezar_otra_noche(self):
        inventario = Inventario()
        inventario.guardar(ID_CHURRUMINO)
        inventario.reiniciar()
        assert not inventario.tuvo(ID_CHURRUMINO)

    def test_no_puede_usar_lo_que_no_tiene(self):
        assert not Inventario().puede_usar(ID_CAFE_CHURRUMINO)

    def test_el_cafe_preparado_cuenta_aunque_falte_combinarlo(self):
        """Con los dos ingredientes encima la respuesta para Jaimico ya está:
        solo falta juntarlos. De esto depende que no le den una tregua de más
        (ver tiene_respuesta_para)."""
        inventario = Inventario()
        inventario.guardar(ID_CAFE)
        inventario.guardar(ID_CHURRUMINO)
        assert inventario.puede_usar(ID_CAFE_CHURRUMINO)


class TestCatalogoDeObjetos:
    def test_pedir_un_objeto_inexistente_falla(self):
        with pytest.raises(ValueError):
            obtener_objeto("chipote_de_oro")

    def test_los_seis_defensivos_son_arrojables(self):
        assert all(obtener_objeto(o).arrojable for o in OBJETOS_DEFENSIVOS)

    def test_la_bateria_no_se_arroja(self):
        assert not obtener_objeto(ID_BATERIA).arrojable

    def test_cada_objeto_ocupa_su_propia_celda_de_la_hoja(self):
        celdas = [objeto.celda for objeto in CATALOGO.values()]
        assert len(set(celdas)) == len(celdas)

    def test_el_id_del_objeto_coincide_con_su_clave(self):
        assert all(clave == objeto.id for clave, objeto in CATALOGO.items())


class TestObjetosEnElSuelo:
    def test_los_sitios_arrancan_vacios(self):
        assert ObjetosEnElSuelo(1).objeto_en(POSICION_LAVADEROS) is None

    def test_solo_aparecen_en_los_lavaderos(self):
        """Es el único sitio del patio donde el jugador puede rebuscar; en el
        barril está asomado y dentro no ve el suelo."""
        assert POSICIONES_CON_OBJETOS == (POSICION_LAVADEROS,)

    def test_en_el_barril_no_aparece_nada(self):
        assert ObjetosEnElSuelo(1).objeto_en(POSICION_BARRIL) is None

    def test_recoger_deja_el_sitio_vacio(self):
        suelo = ObjetosEnElSuelo(1)
        suelo._objetos[POSICION_LAVADEROS] = ID_BATERIA
        assert suelo.recoger(POSICION_LAVADEROS) == ID_BATERIA
        assert suelo.objeto_en(POSICION_LAVADEROS) is None

    def test_recoger_de_un_sitio_vacio_devuelve_nada(self):
        assert ObjetosEnElSuelo(1).recoger(POSICION_LAVADEROS) is None

    def test_con_probabilidad_total_aparece_algo_al_cumplirse_el_plazo(self):
        suelo = ObjetosEnElSuelo(1)
        suelo.probabilidad = 1.0
        suelo.actualizar(OBJETO_INTERVALO_APARICION_SEGUNDOS + 0.1)
        assert suelo.objeto_en(POSICION_LAVADEROS) is not None

    def test_antes_del_plazo_no_aparece_nada(self):
        suelo = ObjetosEnElSuelo(1)
        suelo.probabilidad = 1.0
        suelo.actualizar(OBJETO_INTERVALO_APARICION_SEGUNDOS - 1)
        assert suelo.objeto_en(POSICION_LAVADEROS) is None

    def test_los_unicos_salen_una_sola_vez_y_luego_solo_baterias(self):
        suelo = ObjetosEnElSuelo(1)
        suelo.probabilidad = 1.0
        salidos = []
        for _ in range(len(OBJETOS_UNICOS) + 6):
            suelo.actualizar(OBJETO_INTERVALO_APARICION_SEGUNDOS + 0.1)
            for sitio in POSICIONES_CON_OBJETOS:
                recogido = suelo.recoger(sitio)
                if recogido is not None:
                    salidos.append(recogido)

        unicos_salidos = [o for o in salidos if o in OBJETOS_UNICOS]
        assert len(unicos_salidos) == len(set(unicos_salidos))
        assert set(unicos_salidos) == set(OBJETOS_UNICOS)
        assert salidos[-1] == ID_BATERIA

    def test_las_noches_tardias_son_mas_tacanas(self):
        assert ObjetosEnElSuelo(6).probabilidad < ObjetosEnElSuelo(1).probabilidad

    @pytest.mark.parametrize("noche", range(1, 7))
    def test_ninguna_noche_hace_esperar_de_mas_por_un_objeto(self, noche):
        """La espera media por objeto es intervalo / probabilidad, y solo hay
        un sitio donde buscar desde que la Entrada dejó de ser accesible. Si
        se pasa de este tope, el jugador se queda mirando el suelo vacío
        mientras el elenco sigue llegando."""
        espera = OBJETO_INTERVALO_APARICION_SEGUNDOS / ObjetosEnElSuelo(noche).probabilidad
        assert espera <= ESPERA_MAXIMA_POR_OBJETO, (
            f"noche {noche}: un objeto cada {espera:.0f} s de media"
        )


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
        control.actualizar(CAMARA_SABOTAJE_SEGUNDOS - 0.1, observado=True)
        assert not control.averiadas

    def test_mirarlo_demasiado_seguido_las_rompe(self):
        control = ControlSabotaje()
        control.actualizar(CAMARA_SABOTAJE_SEGUNDOS, observado=True)
        assert control.averiadas

    def test_dejar_de_mirarlo_enfria_la_presion(self):
        control = ControlSabotaje()
        control.actualizar(4.0, observado=True)
        acumulado = control.presion
        control.actualizar(2.0, observado=False)
        assert control.presion < acumulado

    def test_la_presion_no_baja_de_cero(self):
        control = ControlSabotaje()
        control.actualizar(999.0, observado=False)
        assert control.presion == 0.0

    def test_una_vez_averiadas_siguen_asi_hasta_repararlas(self):
        control = ControlSabotaje()
        control.actualizar(CAMARA_SABOTAJE_SEGUNDOS, observado=True)
        control.actualizar(999.0, observado=False)
        assert control.averiadas

    def test_reparar_las_deja_como_nuevas(self):
        control = ControlSabotaje()
        control.actualizar(CAMARA_SABOTAJE_SEGUNDOS, observado=True)
        control.reparar()
        assert not control.averiadas
        assert control.presion == 0.0
