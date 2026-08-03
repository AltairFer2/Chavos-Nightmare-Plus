"""Punto de entrada del juego: inicializa pygame, ejecuta el bucle principal
y coordina menú, estado, hub del jugador, linterna, objetos, cámaras,
servicios del barril, animatrónicos, temporizador, audio e interfaz."""

import sys

import pygame

from animatronics import (
    acechando_en,
    crear_elenco_noche,
    crear_elenco_personalizado,
    detectar_luz_mortal,
    hora_de_arranque,
    iluminados_en,
    resolver_arrojo,
)
from audio import GestorAudio
from camaras import SistemaCamaras
from constants import (
    ALTO_PANTALLA,
    ANCHO_PANTALLA,
    COLOR_NEGRO,
    EFECTO_CAMBIO_CAMARA,
    FPS,
)
from game_state import EstadoJuego, GestorEstados
from guardado import Configuracion, ProgresoJugador, existe_configuracion_guardada
from iconos import IconosObjetos
from idiomas import GestorIdiomas
from inventario import ORDEN_ARROJABLES, Inventario
from jugador import Jugador
from linterna import Linterna, baterias_iniciales, esta_iluminado
from menu import MenuPrincipal
from objetos import ID_BATERIA, ObjetosEnElSuelo, obtener_objeto
from pantalla import GestorPantalla
from panel_servicios import PanelServicios
from servicios import Resultado, Servicio, ServiciosUtilidad
from temporizador import TemporizadorNoche
from ui import RECT_TIRA_CAMARAS, RECT_TIRA_SERVICIOS, EstadoHud, InterfazJuego
from vista import VistaJugador

# Pista de música asociada a cada estado. El gestor de audio la resuelve
# dentro de la carpeta con o sin copyright según el modo streamer.
PISTAS_POR_ESTADO = {
    EstadoJuego.MENU: "menu",
    EstadoJuego.JUGANDO: "noche",
    EstadoJuego.GAME_OVER: "game_over",
    EstadoJuego.VICTORIA: "victoria",
}

TECLAS_IZQUIERDA = (pygame.K_a, pygame.K_LEFT)
TECLAS_DERECHA = (pygame.K_d, pygame.K_RIGHT)
TECLAS_BAJAR = (pygame.K_s, pygame.K_DOWN)
TECLAS_SUBIR = (pygame.K_w, pygame.K_UP)
# Teclas 1..7: cada una arroja siempre el mismo objeto, esté o no en el
# inventario, para que el jugador no tenga que releer la fila cada vez.
TECLAS_ARROJAR = (
    pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
    pygame.K_5, pygame.K_6, pygame.K_7,
)

# Cuánto se queda en pantalla el mensaje de lo que acaba de pasar.
SEGUNDOS_AVISO = 2.5

# Servicios que dejan las cámaras otra vez en pie al terminar.
SERVICIOS_QUE_REPARAN_CAMARAS = (Servicio.CAMARAS, Servicio.TODO)

# Qué mensaje corresponde a cada resultado de usar un servicio.
MENSAJES_SERVICIO = {
    Resultado.OCUPADO: "servicio_ocupado",
    Resultado.SIN_USOS: "servicio_sin_usos",
    Resultado.EN_MARCHA: "servicio_en_marcha",
    Resultado.AHUYENTADO: "servicio_ahuyentado",
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
        # Una sola hoja de iconos compartida por el HUD y por el suelo.
        self.iconos = IconosObjetos()
        self.interfaz = InterfazJuego(self.idiomas, self.iconos)
        self.vista = VistaJugador(self.iconos)
        self.sistema_camaras = SistemaCamaras()
        self.panel_servicios = PanelServicios()
        self.temporizador = TemporizadorNoche()
        self.jugador = Jugador()
        self.linterna = Linterna()
        self.inventario = Inventario()
        self.servicios = ServiciosUtilidad()
        self.objetos_en_suelo = ObjetosEnElSuelo(1)

        self.animatronics = []
        self.hora_arranque = 0
        self.noche_actual = 1
        self.es_noche_personalizada = False
        self.nombre_atacante = ""
        self.clave_derrota = "game_over_motivo"
        self.punto_luz = (ANCHO_PANTALLA // 2, ALTO_PANTALLA // 2)
        self.aviso = ""
        self._aviso_restante = 0.0

        self._ejecutando = True

    # ------------------------------------------------------------------
    # Ciclo de vida de una noche
    # ------------------------------------------------------------------
    def iniciar_noche(self, solicitud):
        self.noche_actual = solicitud.numero
        self.es_noche_personalizada = solicitud.personalizada
        self.temporizador.reiniciar()
        if solicitud.personalizada:
            self.animatronics = crear_elenco_personalizado(solicitud.niveles_ia)
            self.hora_arranque = 0
        else:
            self.animatronics = crear_elenco_noche(solicitud.numero)
            self.hora_arranque = hora_de_arranque(solicitud.numero)
        self.jugador.reiniciar()
        self.linterna.reiniciar(baterias_iniciales(solicitud.numero))
        self.inventario.reiniciar()
        self.servicios.reiniciar(solicitud.numero)
        self.objetos_en_suelo = ObjetosEnElSuelo(solicitud.numero)
        self.sistema_camaras.camara_actual = "primer_patio"
        self.sistema_camaras.activo = False
        self.sistema_camaras.reparar()
        self.panel_servicios.activo = False
        self.nombre_atacante = ""
        self.clave_derrota = "game_over_motivo"
        self._avisar("")
        self.gestor_estados.cambiar_a(EstadoJuego.JUGANDO)

    def volver_al_menu(self):
        self.menu.volver_al_inicio()
        self.gestor_estados.cambiar_a(EstadoJuego.MENU)

    def _perder(self, nombre: str, clave_motivo: str):
        self.nombre_atacante = nombre
        self.clave_derrota = clave_motivo
        self.gestor_estados.cambiar_a(EstadoJuego.GAME_OVER)

    def _avisar(self, texto: str):
        self.aviso = texto
        self._aviso_restante = SEGUNDOS_AVISO if texto else 0.0

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

    # ------------------------------------------------------------------
    # Entrada
    # ------------------------------------------------------------------
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
            return

        if self.gestor_estados.estado in (EstadoJuego.GAME_OVER, EstadoJuego.VICTORIA):
            if tecla == pygame.K_RETURN:
                self.volver_al_menu()
            return

        if not self.gestor_estados.jugando():
            return

        if tecla in TECLAS_IZQUIERDA:
            self._caminar(-1)
        elif tecla in TECLAS_DERECHA:
            self._caminar(1)
        elif tecla in TECLAS_BAJAR:
            self._meterse_al_barril()
        elif tecla in TECLAS_SUBIR:
            self._asomarse()
        elif tecla == pygame.K_e:
            self._recoger_objeto()
        elif tecla == pygame.K_r:
            self.linterna.cambiar_bateria()
        elif tecla == pygame.K_c:
            self._combinar_cafe()
        elif tecla in TECLAS_ARROJAR:
            self._arrojar(TECLAS_ARROJAR.index(tecla))
        elif tecla == pygame.K_SPACE and self.jugador.esta_escondido:
            self._alternar_camaras()
        elif tecla == pygame.K_TAB and self.jugador.esta_escondido:
            self._alternar_servicios()

    def _caminar(self, direccion: int):
        """Caminar solo tiene sentido fuera del barril; dentro, el jugador
        primero tiene que asomarse."""
        if not self.jugador.esta_escondido:
            self.jugador.mover(direccion)

    def _meterse_al_barril(self):
        """Al esconderse se apaga la linterna: dentro del barril no se puede
        usar, y así no se gasta batería sin querer."""
        if self.jugador.bajar():
            self.linterna.encendida = False

    def _asomarse(self):
        """Solo se puede sacar la cabeza estando dentro del barril y con los
        dos paneles bajados: mientras se mira uno no se ve nada afuera."""
        if self.sistema_camaras.activo or self.panel_servicios.activo:
            return
        self.jugador.subir()

    def _alternar_camaras(self):
        self.panel_servicios.activo = False
        self.sistema_camaras.alternar_panel()

    def _alternar_servicios(self):
        self.sistema_camaras.activo = False
        self.panel_servicios.alternar()

    def _procesar_click(self, posicion):
        if not self.gestor_estados.jugando():
            return
        if self.sistema_camaras.activo:
            self._seleccionar_camara(posicion)
        elif self.panel_servicios.activo:
            self._usar_servicio(posicion)
        elif not self.jugador.esta_escondido:
            self.linterna.alternar()

    def _seleccionar_camara(self, posicion):
        id_habitacion = self.sistema_camaras.boton_en(posicion)
        if id_habitacion is None:
            return
        if self.sistema_camaras.cambiar_camara(id_habitacion):
            self.audio.reproducir_efecto_camara(EFECTO_CAMBIO_CAMARA)

    # ------------------------------------------------------------------
    # Objetos
    # ------------------------------------------------------------------
    def _recoger_objeto(self):
        """Las baterías van directas a la linterna; el resto, al inventario."""
        if self._objeto_a_la_vista() is None:
            return
        id_objeto = self.objetos_en_suelo.recoger(self.jugador.posicion)
        if id_objeto == ID_BATERIA:
            self.linterna.guardar_bateria()
        elif id_objeto is not None:
            self.inventario.guardar(id_objeto)

    def _objeto_a_la_vista(self):
        """Id del objeto que el jugador tiene iluminado en el suelo, o None.
        Sin apuntarle con la linterna no se puede recoger nada."""
        posicion = self.jugador.posicion_actual
        if not posicion.permite_buscar or not self.linterna.encendida:
            return None
        id_objeto = self.objetos_en_suelo.objeto_en(posicion.id)
        if id_objeto is None or not esta_iluminado(posicion.punto_objeto, self.punto_luz):
            return None
        return id_objeto

    def _combinar_cafe(self):
        if self.inventario.combinar_cafe():
            self._avisar(self.idiomas.t("cafe_preparado"))

    def _arrojar(self, indice: int):
        """Arroja el objeto de esa ranura contra quien tenga delante. El
        objeto se gasta siempre, acierte o no: ese es el castigo por tirar el
        que no tocaba."""
        if self.jugador.esta_escondido or indice >= len(ORDEN_ARROJABLES):
            return
        id_objeto = ORDEN_ARROJABLES[indice]
        if not self.inventario.gastar(id_objeto):
            return

        nombre_objeto = self.idiomas.t(obtener_objeto(id_objeto).clave_texto)
        resultado = resolver_arrojo(
            acechando_en(self.animatronics, self.jugador.posicion),
            id_objeto,
            iluminados_en(
                self.animatronics, self.jugador.posicion,
                self.punto_luz, self.linterna.encendida,
            ),
        )

        if resultado.eliminado is not None:
            self._avisar(self.idiomas.t(
                "arrojo_elimina", objeto=nombre_objeto, nombre=resultado.eliminado.nombre
            ))
        elif resultado.retrasado is not None:
            self._avisar(self.idiomas.t(
                "arrojo_retrasa", nombre=resultado.retrasado.nombre
            ))
        else:
            self._avisar(self.idiomas.t("arrojo_perdido", objeto=nombre_objeto))

    # ------------------------------------------------------------------
    # Servicios del barril
    # ------------------------------------------------------------------
    def _usar_servicio(self, posicion):
        servicio = self.panel_servicios.boton_en(posicion)
        if servicio is None:
            return
        resultado = self.servicios.usar(servicio, self.animatronics)
        if resultado is Resultado.LLAMADA_EN_VANO:
            self._perder("Señor Barriga", "game_over_barriga")
            return
        self._avisar(self.idiomas.t(MENSAJES_SERVICIO[resultado]))

    # ------------------------------------------------------------------
    # Actualización
    # ------------------------------------------------------------------
    def _actualizar(self, dt: float):
        if self.gestor_estados.en_menu():
            self.menu.actualizar(dt)
            return

        if not self.gestor_estados.jugando():
            return

        self.punto_luz = self.gestor_pantalla.posicion_en_lienzo(pygame.mouse.get_pos())
        self._atender_tiras()
        self.linterna.actualizar(dt)
        self.objetos_en_suelo.actualizar(dt)
        self.sistema_camaras.actualizar(dt, self.animatronics)
        if self.servicios.actualizar(dt) in SERVICIOS_QUE_REPARAN_CAMARAS:
            self.sistema_camaras.reparar()
        self.temporizador.actualizar(dt, self._elenco_en_movimiento())

        if self._aviso_restante > 0.0:
            self._aviso_restante -= dt
            if self._aviso_restante <= 0.0:
                self.aviso = ""

        if self._murio_por_la_luz() or self._fue_atacado(dt):
            return

        if self.temporizador.noche_terminada:
            if not self.es_noche_personalizada:
                self.progreso.registrar_noche_completada(self.noche_actual)
            self.gestor_estados.cambiar_a(EstadoJuego.VICTORIA)

    def _atender_tiras(self):
        """Pasar el ratón por una de las pestañas de abajo levanta ese panel,
        como en el género. Solo dentro del barril y con todo bajado."""
        if not self.jugador.esta_escondido:
            return
        if self.sistema_camaras.activo or self.panel_servicios.activo:
            return
        if RECT_TIRA_CAMARAS.collidepoint(self.punto_luz):
            self.sistema_camaras.activo = True
        elif RECT_TIRA_SERVICIOS.collidepoint(self.punto_luz):
            self.panel_servicios.activo = True

    def _elenco_en_movimiento(self):
        """Los animatrónicos que ya tienen permiso de moverse. Algunas noches
        arrancan más tarde: en la noche 1 nadie se mueve hasta las 2 AM."""
        if self.temporizador.horas_transcurridas() < self.hora_arranque:
            return ()
        return self.animatronics

    def _murio_por_la_luz(self) -> bool:
        """Apuntarle la linterna de cerca a quien no tolera la luz es fatal.
        Con un panel delante el haz no llega al patio: el jugador sigue
        expuesto a que lo ataquen, pero no a alumbrar a nadie sin querer."""
        if not self.linterna.encendida:
            return False
        if self.sistema_camaras.activo or self.panel_servicios.activo:
            return False
        victimario = detectar_luz_mortal(
            self.animatronics, self.jugador.posicion, self.punto_luz
        )
        if victimario is None:
            return False
        self._perder(victimario.nombre, "game_over_luz")
        return True

    def _fue_atacado(self, dt: float) -> bool:
        """Los que ya llegaron esperan un margen antes de atacar; el jugador
        sigue siendo vulnerable esté donde esté, incluso dentro del barril."""
        for animatronic in self.animatronics:
            if animatronic.descontar_espera(dt):
                self._perder(animatronic.nombre, "game_over_motivo")
                return True
        return False

    def _actualizar_musica(self):
        pista = PISTAS_POR_ESTADO.get(self.gestor_estados.estado)
        if pista:
            self.audio.reproducir_musica(pista)

    # ------------------------------------------------------------------
    # Dibujado
    # ------------------------------------------------------------------
    def _dibujar(self):
        self.pantalla.fill(COLOR_NEGRO)

        if self.gestor_estados.en_menu():
            self.menu.dibujar(self.pantalla)
        elif self.gestor_estados.jugando():
            self._dibujar_partida()
        elif self.gestor_estados.termino_en_derrota():
            self.interfaz.dibujar_game_over(
                self.pantalla, self.nombre_atacante, self.clave_derrota
            )
        elif self.gestor_estados.termino_en_victoria():
            self.interfaz.dibujar_victoria(self.pantalla, self.es_noche_personalizada)

    def _dibujar_partida(self):
        if self.sistema_camaras.activo:
            self.sistema_camaras.dibujar(
                self.pantalla,
                animatronics=[a for a in self.animatronics if a.activo],
                fuente=self.interfaz.fuente_camara,
                idiomas=self.idiomas,
                posicion_raton=self.punto_luz,
            )
        else:
            self.vista.dibujar(
                self.pantalla, self.jugador, self.animatronics, self.objetos_en_suelo,
                self.linterna, self.punto_luz,
                fuente=self.interfaz.fuente_camara, idiomas=self.idiomas,
            )
            if self.panel_servicios.activo:
                self.panel_servicios.dibujar(
                    self.pantalla, self.servicios, self.punto_luz
                )

        self.interfaz.dibujar_hud(
            self.pantalla, self.temporizador, self.jugador, self.linterna,
            self.inventario, self._estado_hud(),
        )

    def _estado_hud(self) -> EstadoHud:
        id_peticion, peticion = self._peticion_de_clotilde()
        return EstadoHud(
            numero_noche=self.noche_actual,
            en_camaras=self.sistema_camaras.activo,
            en_servicios=self.panel_servicios.activo,
            objeto_a_recoger=self._nombre_objeto_a_la_vista(),
            peticion=peticion,
            id_peticion=id_peticion,
            tira_resaltada=self._tira_resaltada(),
            aviso=self.aviso,
        )

    def _peticion_de_clotilde(self):
        """Qué objeto reclama quien lo esté pidiendo delante del jugador."""
        for animatronic in acechando_en(self.animatronics, self.jugador.posicion):
            if animatronic.objeto_pedido is None:
                continue
            objeto = obtener_objeto(animatronic.objeto_pedido)
            return objeto.id, self.idiomas.t(objeto.clave_texto)
        return "", ""

    def _tira_resaltada(self) -> str:
        if not self.jugador.esta_escondido:
            return ""
        if RECT_TIRA_CAMARAS.collidepoint(self.punto_luz):
            return "camaras"
        if RECT_TIRA_SERVICIOS.collidepoint(self.punto_luz):
            return "servicios"
        return ""

    def _nombre_objeto_a_la_vista(self) -> str:
        id_objeto = self._objeto_a_la_vista()
        if id_objeto is None:
            return ""
        return self.idiomas.t(obtener_objeto(id_objeto).clave_texto)


def main():
    juego = Juego()
    juego.ejecutar()


if __name__ == "__main__":
    main()
