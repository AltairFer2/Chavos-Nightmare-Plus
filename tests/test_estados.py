"""Máquina de estados global: menú, jugando, pausa, susto y finales.

Es pura (sin pygame), así que se prueba igual que el dominio.
"""

from vecindad.app.estados import EstadoJuego, GestorEstados


def test_arranca_en_el_menu():
    assert GestorEstados().en_menu()


def test_cambiar_a_actualiza_el_estado():
    gestor = GestorEstados()
    gestor.cambiar_a(EstadoJuego.JUGANDO)
    assert gestor.estado is EstadoJuego.JUGANDO
    assert gestor.jugando()


def test_en_pausa_solo_es_verdadero_en_pausa():
    gestor = GestorEstados()
    gestor.cambiar_a(EstadoJuego.PAUSA)
    assert gestor.en_pausa()
    assert not gestor.jugando()
    assert not gestor.en_menu()


def test_pausar_y_reanudar_no_deja_residuos_en_otras_consultas():
    gestor = GestorEstados()
    gestor.cambiar_a(EstadoJuego.JUGANDO)
    gestor.cambiar_a(EstadoJuego.PAUSA)
    gestor.cambiar_a(EstadoJuego.JUGANDO)
    assert gestor.jugando()
    assert not gestor.en_pausa()


def test_las_consultas_de_final_distinguen_derrota_de_victoria():
    gestor = GestorEstados()
    gestor.cambiar_a(EstadoJuego.GAME_OVER)
    assert gestor.termino_en_derrota()
    assert not gestor.termino_en_victoria()

    gestor.cambiar_a(EstadoJuego.VICTORIA)
    assert gestor.termino_en_victoria()
    assert not gestor.termino_en_derrota()


def test_susto_no_se_confunde_con_pausa_ni_con_jugando():
    gestor = GestorEstados()
    gestor.cambiar_a(EstadoJuego.SUSTO)
    assert gestor.en_susto()
    assert not gestor.en_pausa()
    assert not gestor.jugando()
