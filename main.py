"""Punto de entrada del juego: inicializa pygame, ejecuta el bucle principal
y coordina menú, estado, cámaras, animatrónicos, temporizador, audio e
interfaz."""

import sys

import pygame

from animatronics import crear_elenco_noche, crear_elenco_personalizado
from audio import GestorAudio
from camaras import SistemaCamaras
from constants import ALTO_PANTALLA, ANCHO_PANTALLA, COLOR_NEGRO, FPS
from game_state import EstadoJuego, GestorEstados
from guardado import Configuracion, ProgresoJugador, existe_configuracion_guardada
from idiomas import GestorIdiomas
from menu import MenuPrincipal
from pantalla import GestorPantalla
from temporizador import Temporizador
from ui import InterfazJuego

RECT_PANEL_SELECTOR = pygame.Rect(0, ALTO_PANTALLA - 200, ANCHO_PANTALLA, 180)
RECT_VISTA_CAMARA = pygame.Rect(40, 60, ANCHO_PANTALLA - 80, ALTO_PANTALLA - 320)

# Pista de música asociada a cada estado. El gestor de audio la resuelve
# dentro de la carpeta con o sin copyright según el modo streamer.
PISTAS_POR_ESTADO = {
    EstadoJuego.MENU: "menu",
    EstadoJuego.JUGANDO: "noche",
    EstadoJuego.GAME_OVER: "game_over",
    EstadoJuego.VICTORIA: "victoria",
}


class Juego:
    def __init__(self):
        pygame.init()
        self.reloj = pygame.time.Clock()

        self.configuracion = Configuracion.cargar()
        self.progreso = ProgresoJugador.cargar()
        self.idiomas = GestorIdiomas(self.configuracion.idioma)
        self.audio = GestorAudio(
            self.configuracion.modo_streamer,
            self.configuracion.volumen_musica,
            self.configuracion.volumen_efectos,
        )

        # Todo se dibuja en gestor_pantalla.lienzo (tamaño fijo) y se escala
        # a la ventana al presentar el fotograma.
        self.gestor_pantalla = GestorPantalla(
            self.configuracion.resolucion, self.configuracion.pantalla_completa
        )
        self.pantalla = self.gestor_pantalla.lienzo

        # Si no existía configuracion.json todavía, Configuracion.cargar()
        # tomó el valor por defecto (pantalla completa); se deja guardado de
        # una vez para que quede como preferencia explícita del jugador.
        if not existe_configuracion_guardada():
            self.configuracion.guardar()

        self.gestor_estados = GestorEstados()
        self.menu = MenuPrincipal(
            self.idiomas, self.progreso, self.configuracion, self.audio, self.gestor_pantalla
        )
        self.interfaz = InterfazJuego(self.idiomas)
        self.sistema_camaras = SistemaCamaras()
        self.temporizador = Temporizador()

        self.animatronics = []
        self.noche_actual = 1
        self.es_noche_personalizada = False
        self.nombre_atacante = ""
        self._botones_panel = {}

        self._ejecutando = True

    def iniciar_noche(self, solicitud):
        self.noche_actual = solicitud.numero
        self.es_noche_personalizada = solicitud.personalizada
        self.temporizador.reiniciar()
        self.animatronics = (
            crear_elenco_personalizado(solicitud.dificultades)
            if solicitud.personalizada
            else crear_elenco_noche(solicitud.numero)
        )
        self.sistema_camaras.camara_actual = "primer_patio"
        self.sistema_camaras.activo = False
        self.nombre_atacante = ""
        self.gestor_estados.cambiar_a(EstadoJuego.JUGANDO)

    def volver_al_menu(self):
        self.menu.volver_al_inicio()
        self.gestor_estados.cambiar_a(EstadoJuego.MENU)

    def ejecutar(self):
        while self._ejecutando:
            dt = self.reloj.tick(FPS) / 1000.0
            self._procesar_eventos()
            self._actualizar(dt)
            self._actualizar_musica()
            self._dibujar()
            self.gestor_pantalla.presentar()
        pygame.quit()
        sys.exit()

    def _procesar_eventos(self):
        for evento in pygame.event.get():
            posicion = None
            if evento.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
                posicion = self.gestor_pantalla.posicion_en_lienzo(evento.pos)

            if evento.type == pygame.QUIT:
                self._ejecutando = False
            elif self.gestor_estados.en_menu():
                self.menu.manejar_evento(evento, posicion)
            elif evento.type == pygame.KEYDOWN:
                self._procesar_tecla(evento.key)
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                self._procesar_click(posicion)

        if self.gestor_estados.en_menu():
            self._atender_menu()

    def _atender_menu(self):
        if self.menu.salir_solicitado:
            self._ejecutando = False
            return
        solicitud = self.menu.consumir_solicitud()
        if solicitud is not None:
            self.iniciar_noche(solicitud)

    def _procesar_tecla(self, tecla):
        if tecla == pygame.K_ESCAPE:
            self._ejecutando = False
        elif self.gestor_estados.jugando() and tecla == pygame.K_SPACE:
            self.sistema_camaras.alternar_panel()
        elif (
            self.gestor_estados.estado in (EstadoJuego.GAME_OVER, EstadoJuego.VICTORIA)
            and tecla == pygame.K_RETURN
        ):
            self.volver_al_menu()

    def _procesar_click(self, posicion):
        if not (self.gestor_estados.jugando() and self.sistema_camaras.activo):
            return
        for id_habitacion, boton_rect in self._botones_panel.items():
            if boton_rect.collidepoint(posicion):
                self.sistema_camaras.cambiar_camara(id_habitacion)
                break

    def _actualizar(self, dt: float):
        if self.gestor_estados.en_menu():
            self.menu.actualizar(dt)
            return

        if not self.gestor_estados.jugando():
            return

        self.sistema_camaras.actualizar()
        self.temporizador.actualizar(dt, camaras_activas=self.sistema_camaras.activo)

        for animatronic in self.animatronics:
            animatronic.actualizar(dt)
            if animatronic.alcanzo_al_jugador():
                self.nombre_atacante = animatronic.nombre
                self.gestor_estados.cambiar_a(EstadoJuego.GAME_OVER)
                return

        if self.temporizador.noche_terminada:
            if not self.es_noche_personalizada:
                self.progreso.registrar_noche_completada(self.noche_actual)
            self.gestor_estados.cambiar_a(EstadoJuego.VICTORIA)

    def _actualizar_musica(self):
        pista = PISTAS_POR_ESTADO.get(self.gestor_estados.estado)
        if pista:
            self.audio.reproducir_musica(pista)

    def _dibujar(self):
        self.pantalla.fill(COLOR_NEGRO)

        if self.gestor_estados.en_menu():
            self.menu.dibujar(self.pantalla)
        elif self.gestor_estados.jugando():
            self.sistema_camaras.dibujar(
                self.pantalla, RECT_VISTA_CAMARA,
                animatronics_presentes=self.animatronics,
                fuente=self.interfaz.fuente_camara,
                idiomas=self.idiomas,
            )
            self.interfaz.dibujar_hud(
                self.pantalla, self.temporizador,
                self.sistema_camaras.camara_actual, self.noche_actual,
            )
            if self.sistema_camaras.activo:
                self._botones_panel = self.interfaz.dibujar_panel_selector(
                    self.pantalla, self.sistema_camaras.camara_actual, RECT_PANEL_SELECTOR
                )
            else:
                self._botones_panel = {}
        elif self.gestor_estados.termino_en_derrota():
            self.interfaz.dibujar_game_over(self.pantalla, self.nombre_atacante)
        elif self.gestor_estados.termino_en_victoria():
            self.interfaz.dibujar_victoria(self.pantalla, self.es_noche_personalizada)


def main():
    juego = Juego()
    juego.ejecutar()


if __name__ == "__main__":
    main()
