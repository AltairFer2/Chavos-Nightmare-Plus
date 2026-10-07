"""Bucle principal: monta todas las piezas y las hace avanzar juntas.

Es la única capa que conoce a todas las demás. Su trabajo es coordinar, no
decidir: las reglas viven en dominio/, el dibujo en presentacion/ y el acceso
a disco, audio y ventana en infraestructura/.

Cada fotograma hace lo mismo: leer los eventos, actualizar el estado, ajustar
la música y dibujar.
"""

import sys

# pyrefly: ignore [missing-import]
import pygame

from ..config.audio import (
    ALERTA_PATIO_VOLUMEN,
    EFECTO_ALERTA_PATIO,
    EFECTO_CAMBIO_CAMARA,
    EFECTO_EASTER_EGG,
    EFECTO_ENCENDIDO_CAMARAS,
    EFECTO_INTERFERENCIA,
    EFECTO_LLAMADA_BARRIGA,
    EFECTO_LLEGA_CHAVO,
    EFECTO_NOCHE_SUPERADA,
    EFECTO_PASOS_DERECHA,
    EFECTO_PASOS_IZQUIERDA,
    EFECTO_RAMON_SE_VA,
    EFECTO_REPARACION,
    EFECTO_SORPRESA,
    EFECTO_SUSTO,
    EFECTOS_LLAMADA_FLORINDA,
    EFECTOS_SALIDA_RAMON,
    PROPORCION_VOLUMEN_EN_PAUSA,
    SUBCARPETA_AMBIENTE,
)
from ..config.interfaz import COLOR_NEGRO, TIRAS_BLOQUEO_SEGUNDOS
from ..config.ventana import ALTO_PANTALLA, ANCHO_PANTALLA, FPS
from ..dominio.animatronicos import (
    Espanto,
    acechando,
    acechando_en,
    detectar_luz_mortal,
    iluminados_en,
    inminencia_en_el_patio,
    nombres,
)
from ..dominio.jugador import Jugador
from ..dominio.linterna import Linterna, baterias_iniciales, esta_iluminado
from ..dominio.aparicion_rara import AparicionesRaras
from ..dominio.busqueda import BusquedasEnCamaras, Desenlace
from ..dominio.objetos import ID_BATERIA, ObjetosEnElSuelo, obtener_objeto
from ..dominio.servicios import Resultado, Servicio, ServiciosUtilidad
from ..dominio.temporizador import TemporizadorNoche
from ..i18n import GestorIdiomas
from ..mundo.posiciones import POSICION_BARRIL
from ..infraestructura.guardado import (
    Configuracion,
    ProgresoJugador,
    existe_configuracion_guardada,
)
from ..infraestructura.audio import GestorAudio
from ..infraestructura.pantalla import GestorPantalla
from ..presentacion.alerta_peligro import AlertaPeligro
from ..presentacion.aparicion_rara import ImagenesRaras
from ..presentacion.camaras import SistemaCamaras
from ..presentacion.hud import (
    RECT_FRANJA_TIRAS,
    RECT_TIRA_BAJAR,
    RECT_TIRA_CAMARAS,
    RECT_TIRA_SERVICIOS,
    EstadoHud,
    InterfazJuego,
)
from ..presentacion.iconos import IconosObjetos
from ..presentacion.inicio_noche import PeriodicoInicial, TarjetaNoche
from ..presentacion.jumpscare import Susto
from ..presentacion.menu import (
    SOLICITUD_MENU_PRINCIPAL,
    SOLICITUD_REANUDAR,
    MenuPausa,
    MenuPrincipal,
    SolicitudNoche,
)
from ..presentacion.menu_derrota import SOLICITUD_REINTENTAR, MenuDerrota
from ..presentacion.noche_superada import SOLICITUD_CONTINUAR, MenuVictoria, RelojVictoria
from ..presentacion.panel_servicios import PanelServicios
from ..presentacion.vista import VistaJugador
from .aviso import AvisoTemporal
from .entrada import Accion, accion_de
from .estados import EstadoJuego, GestorEstados
from .noche import MOTIVO_ATRAPADO, MOTIVO_ESCOBA, Noche

# Pista de música asociada a cada estado. El gestor de audio la resuelve
# dentro de la carpeta con o sin copyright según el modo streamer.
PISTAS_POR_ESTADO = {
    EstadoJuego.MENU: "menu",
    EstadoJuego.JUGANDO: "noche",
    EstadoJuego.GAME_OVER: "game_over",
}

# Estados que se ven en silencio: la música del menú se corta al entrar a la
# noche y no vuelve hasta que el jugador está en el patio. El periódico y la
# tarjeta son el cambio de tono entre el menú y la noche, y con la música del
# menú encima no se sentiría como tal.
ESTADOS_EN_SILENCIO = (EstadoJuego.PERIODICO, EstadoJuego.TARJETA_NOCHE)

# Servicios que dejan las cámaras otra vez en pie al terminar.
SERVICIOS_QUE_REPARAN_CAMARAS = (Servicio.CAMARAS, Servicio.TODO)

# Qué mensaje corresponde a cada resultado de usar un servicio.
# Qué se le escribe al jugador según cómo saliera el servicio. Los resultados
# que no aparecen aquí no llevan aviso a propósito: que una contramedida haya
# funcionado se nota mirando y oyendo, no leyéndolo.
MENSAJES_SERVICIO = {
    Resultado.OCUPADO: "servicio_ocupado",
    Resultado.SIN_USOS: "servicio_sin_usos",
    Resultado.EN_MARCHA: "servicio_en_marcha",
}

CAMARA_INICIAL = "primer_patio"


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
            self.configuracion.resolucion,
            self.configuracion.pantalla_completa,
            self.configuracion.brillo,
        )
        self.pantalla = self.gestor_pantalla.lienzo

        # Si no existía configuracion.json todavía, Configuracion.cargar()
        # tomó el valor por defecto (pantalla completa); se deja guardado de
        # una vez para que quede como preferencia explícita del jugador.
        if not existe_configuracion_guardada():
            self.configuracion.guardar()

        self.gestor_estados = GestorEstados()
        self.menu = MenuPrincipal(
            self.idiomas, self.progreso, self.configuracion, self.audio,
            self.gestor_pantalla,
        )
        self.menu_pausa = MenuPausa(
            self.idiomas, self.configuracion, self.audio, self.gestor_pantalla
        )
        self.iconos = IconosObjetos()
        self.interfaz = InterfazJuego(self.idiomas)
        self.vista = VistaJugador(self.iconos)
        self.sistema_camaras = SistemaCamaras()
        self.panel_servicios = PanelServicios()
        self.temporizador = TemporizadorNoche()
        self.jugador = Jugador()
        self.linterna = Linterna()
        self.espanto = Espanto()
        self.servicios = ServiciosUtilidad()
        self.objetos_en_suelo = ObjetosEnElSuelo(1)
        self.imagenes_raras = ImagenesRaras()
        self.apariciones = AparicionesRaras(1, self.imagenes_raras.cantidad)
        self.alerta_peligro = AlertaPeligro()
        self.busquedas = BusquedasEnCamaras()
        self.susto = Susto()
        self.reloj_victoria = RelojVictoria(self.idiomas)
        self.menu_victoria = MenuVictoria(self.idiomas)
        self.menu_derrota = MenuDerrota(self.idiomas)
        self.periodico = PeriodicoInicial()
        self.tarjeta_noche = TarjetaNoche(self.idiomas)

        self.noche = Noche()
        self.punto_luz = (ANCHO_PANTALLA // 2, ALTO_PANTALLA // 2)
        self.aviso = AvisoTemporal()
        # Si en el fotograma anterior tenía a alguien delante, para que el
        # sobresalto suene al encontrárselo y no en bucle.
        self._vio_a_alguien = False
        # Dónde estaba Doña Florinda el fotograma anterior: cuando se mueve,
        # el monitor da un tirón (ver _distorsionar_si_se_movio_florinda).
        self._florinda_estaba = None
        # Los dos seguros de las pestañas de abajo: uno se levanta al salir el
        # cursor de la franja y el otro es un rato muerto tras bajar un panel
        # (ver _atender_tiras).
        self._tira_usada = False
        self._tiras_bloqueadas = 0.0

        self._ejecutando = True

    # ------------------------------------------------------------------
    # Ciclo de vida de una noche
    # ------------------------------------------------------------------
    def iniciar_noche(self, solicitud):
        """Deja la noche montada y arranca las pantallas de entrada. Todo
        queda listo antes de enseñarlas, así que mientras se leen ya no hay
        nada que preparar: son la transición entre el menú y el patio."""
        nueva_partida = getattr(solicitud, "nueva_partida", False)
        if nueva_partida:
            # Nuevo Juego empieza la campaña otra vez: se borra el avance en
            # el acto, no al terminar la noche, para que salir a mitad no
            # deje Continuar apuntando a la partida vieja.
            self.progreso.empezar_de_cero()
        self.noche = Noche.desde_solicitud(solicitud)
        self.temporizador.reiniciar(self.noche.intervalo_movimiento)
        self.jugador.reiniciar()
        self.linterna.reiniciar(baterias_iniciales(self.noche.numero))
        self.espanto.reiniciar()
        self.servicios.reiniciar(self.noche.numero)
        self.objetos_en_suelo = ObjetosEnElSuelo(self.noche.numero)
        self.apariciones = AparicionesRaras(self.noche.numero, self.imagenes_raras.cantidad)
        self.alerta_peligro.reiniciar()
        self.busquedas.reiniciar()
        self.sistema_camaras.reiniciar(CAMARA_INICIAL, self.noche.numero)
        self.panel_servicios.activo = False
        self.aviso.limpiar()
        self._vio_a_alguien = False
        self._florinda_estaba = self._donde_esta_florinda()
        self._tira_usada = False
        self._tiras_bloqueadas = 0.0
        self._entrar_a_la_noche(nueva_partida)

    def _entrar_a_la_noche(self, nueva_partida: bool):
        """El periódico solo sale al empezar de cero (y solo si su arte
        existe); la tarjeta de la noche, siempre."""
        if nueva_partida and self.periodico.iniciar():
            self.gestor_estados.cambiar_a(EstadoJuego.PERIODICO)
            return
        self._mostrar_tarjeta_de_la_noche()

    def _mostrar_tarjeta_de_la_noche(self):
        self.tarjeta_noche.iniciar(self.noche.numero, self.noche.personalizada)
        self.gestor_estados.cambiar_a(EstadoJuego.TARJETA_NOCHE)

    def volver_al_menu(self):
        self.audio.restaurar_volumen()
        self.menu.volver_al_inicio()
        self.gestor_estados.cambiar_a(EstadoJuego.MENU)

    def _pausar(self):
        """La partida se congela y el audio baja a la mitad: en pausa el
        jugador suele estar atendiendo otra cosa, y el juego no tiene por qué
        seguir sonando encima."""
        self.menu_pausa.abrir()
        self.audio.atenuar(PROPORCION_VOLUMEN_EN_PAUSA)
        self.gestor_estados.cambiar_a(EstadoJuego.PAUSA)

    def _reanudar(self):
        self.audio.restaurar_volumen()
        self.gestor_estados.cambiar_a(EstadoJuego.JUGANDO)

    def _perder(self, nombre: str, clave_motivo: str):
        self.noche.registrar_derrota(nombre, clave_motivo)
        duracion_audio = self.audio.duracion_efecto(EFECTO_SUSTO)
        if self.susto.iniciar(nombre, self.jugador.posicion_actual, duracion_audio):
            self.audio.reproducir_efecto(EFECTO_SUSTO)
            self.gestor_estados.cambiar_a(EstadoJuego.SUSTO)
        else:
            self._mostrar_game_over()

    def _mostrar_game_over(self):
        self.menu_derrota.abrir()
        self.gestor_estados.cambiar_a(EstadoJuego.GAME_OVER)

    def _reintentar(self):
        """Vuelve a empezar la misma noche, con los mismos niveles si era la
        personalizada. No es una partida nueva: no borra el avance ni vuelve
        a enseñar el periódico, solo la tarjeta de la noche."""
        self.iniciar_noche(SolicitudNoche(
            numero=self.noche.numero,
            personalizada=self.noche.personalizada,
            niveles_ia=dict(self.noche.niveles_ia),
        ))

    def _avisar(self, clave: str, **formato):
        self.aviso.mostrar(self.idiomas.t(clave, **formato))

    def ejecutar(self):
        while self._ejecutando:
            dt = self.reloj.tick(FPS) / 1000.0
            self._procesar_eventos()
            self._actualizar(dt)
            self._actualizar_musica()
            self._sonar_alerta_del_patio()
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
            elif self.gestor_estados.en_pausa():
                self.menu_pausa.manejar_evento(evento, posicion)
            elif self.gestor_estados.en_menu_victoria():
                self.menu_victoria.manejar_evento(evento, posicion)
            elif self.gestor_estados.termino_en_derrota():
                self._manejar_evento_derrota(evento, posicion)
            elif evento.type == pygame.KEYDOWN:
                self._procesar_tecla(evento.key)
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                self._procesar_click(posicion)

        if self.gestor_estados.en_menu():
            self._atender_menu()
        elif self.gestor_estados.en_pausa():
            self._atender_pausa()
        elif self.gestor_estados.en_menu_victoria():
            self._atender_menu_victoria()
        elif self.gestor_estados.termino_en_derrota():
            self._atender_derrota()

    def _atender_menu(self):
        if self.menu.salir_solicitado:
            self._ejecutando = False
            return
        solicitud = self.menu.consumir_solicitud()
        if solicitud is not None:
            self.iniciar_noche(solicitud)

    def _atender_pausa(self):
        solicitud = self.menu_pausa.consumir_solicitud()
        if solicitud == SOLICITUD_REANUDAR:
            self._reanudar()
        elif solicitud == SOLICITUD_MENU_PRINCIPAL:
            self.volver_al_menu()

    def _atender_menu_victoria(self):
        solicitud = self.menu_victoria.consumir_solicitud()
        if solicitud == SOLICITUD_CONTINUAR:
            self.iniciar_noche(SolicitudNoche(numero=self.progreso.proxima_noche))
        elif solicitud == SOLICITUD_MENU_PRINCIPAL:
            self.volver_al_menu()

    def _manejar_evento_derrota(self, evento, posicion):
        """ESC sigue cerrando el juego desde aquí, como antes; lo demás lo
        lleva el menú de derrota."""
        if evento.type == pygame.KEYDOWN and accion_de(evento.key) is Accion.ESCAPE:
            self._ejecutando = False
            return
        self.menu_derrota.manejar_evento(evento, posicion)

    def _atender_derrota(self):
        solicitud = self.menu_derrota.consumir_solicitud()
        if solicitud == SOLICITUD_REINTENTAR:
            self._reintentar()
        elif solicitud == SOLICITUD_MENU_PRINCIPAL:
            self.volver_al_menu()

    def _procesar_tecla(self, tecla):
        accion = accion_de(tecla)

        if not self.gestor_estados.jugando():
            return

        if accion is Accion.ESCAPE:
            self._pausar()
            return

        if accion is not None:
            self._ejecutar_accion(accion)

    def _ejecutar_accion(self, accion: Accion):
        if accion is Accion.CAMINAR_IZQUIERDA:
            self._caminar(-1)
        elif accion is Accion.CAMINAR_DERECHA:
            self._caminar(1)
        elif accion is Accion.ESCONDERSE:
            self._meterse_al_barril()
        elif accion is Accion.ASOMARSE:
            self._asomarse()
        elif accion is Accion.RECOGER:
            self._recoger_objeto()
        elif accion is Accion.CAMBIAR_BATERIA:
            self.linterna.cambiar_bateria()
        elif accion is Accion.ALTERNAR_CAMARAS and self.jugador.esta_escondido:
            self._alternar_camaras()
        elif accion is Accion.ALTERNAR_SERVICIOS and self.jugador.esta_escondido:
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
        if self._hay_panel_delante():
            return
        self.jugador.subir()

    def _hay_panel_delante(self) -> bool:
        """Si el monitor o el tablero de servicios están levantados."""
        return self.sistema_camaras.activo or self.panel_servicios.activo

    def _atado_al_tablero(self) -> bool:
        """Con un servicio en marcha el jugador no suelta el tablero: ni lo
        baja, ni se asoma, ni cambia al monitor hasta que termine. Ese rato
        a ciegas y sin poder salir es el precio de restablecer algo."""
        return self.panel_servicios.activo and self.servicios.ocupado

    def _avisar_si_esta_atado(self) -> bool:
        """Si está atado al tablero, se lo dice y devuelve True para que
        quien preguntó no haga nada más."""
        if not self._atado_al_tablero():
            return False
        self._avisar("servicio_sin_terminar")
        return True

    def _alternar_camaras(self):
        if self._avisar_si_esta_atado():
            return
        if self.sistema_camaras.activo:
            self._bajar_paneles()
            return
        self.panel_servicios.activo = False
        self._levantar_camaras()

    def _levantar_camaras(self):
        """Sube el monitor con su encendido: la animación del aparato bajando
        del techo la lleva el propio panel, y el chasquido del tubo se suelta
        aquí, que es donde vive el audio."""
        if self.sistema_camaras.abrir():
            self.audio.reproducir_efecto_camara(EFECTO_ENCENDIDO_CAMARAS)

    def _alternar_servicios(self):
        if self.panel_servicios.activo:
            self._bajar_paneles()
            return
        self.sistema_camaras.activo = False
        self.panel_servicios.activo = True

    def _procesar_click(self, posicion):
        if not self.gestor_estados.jugando():
            return
        if self._hay_panel_delante():
            # La pestaña de abajo baja el panel, se esté en el monitor o en
            # el tablero. Basta con pasarle el ratón (ver _atender_tiras),
            # pero el clic también vale: quien venga de pulsar un botón del
            # tablero no tiene por qué saber que aquí no hace falta.
            if RECT_TIRA_BAJAR.collidepoint(posicion):
                self._bajar_paneles()
            elif self.sistema_camaras.activo:
                self._seleccionar_camara(posicion)
            else:
                self._usar_servicio(posicion)
            return
        if not self.jugador.esta_escondido:
            self.linterna.alternar()

    def _bajar_paneles(self):
        """Retira lo que estuviera levantado y deja muerta un rato la franja
        de abajo: las pestañas de subir ocupan ese mismo sitio, así que sin
        los seguros bajar el monitor sería volverlo a levantar en el
        fotograma siguiente."""
        if self._avisar_si_esta_atado():
            return
        self.sistema_camaras.activo = False
        self.panel_servicios.activo = False
        self._tira_usada = True
        self._tiras_bloqueadas = TIRAS_BLOQUEO_SEGUNDOS

    def _seleccionar_camara(self, posicion):
        if self._encontrar_objeto(posicion):
            return
        if self.sistema_camaras.audio_en(posicion):
            self._sonar_audio_de_quico()
            return
        id_habitacion = self.sistema_camaras.boton_en(posicion)
        if id_habitacion is None:
            return
        if self.sistema_camaras.cambiar_camara(id_habitacion):
            self.audio.reproducir_efecto_camara(EFECTO_CAMBIO_CAMARA)

    def _encontrar_objeto(self, posicion) -> bool:
        """Clic sobre la escoba o el café escondidos en la cámara que se
        mira: su dueño desaparece. Solo si de verdad se ve la imagen (sin
        sabotaje ni corte de señal), y contando con lo que esté temblando."""
        if not self.sistema_camaras.se_ve_la_camara:
            return False
        dx, dy = self.sistema_camaras.desplazamiento_vista
        busqueda = self.busquedas.objeto_en(
            self.sistema_camaras.camara_actual, (posicion[0] - dx, posicion[1] - dy)
        )
        if busqueda is None:
            return False
        return self.busquedas.encontrar(busqueda, self.noche.animatronics)

    def _sonar_audio_de_quico(self):
        """Botón de audio del monitor: suena en la cámara que se está
        mirando, y Doña Florinda va hacia allá si es vecina de la suya.

        Si ella entra justo en la cámara que se mira, esa cámara pierde la
        señal como con cualquier otro que llegue (ver
        _cortar_la_senal_si_cambio_quien_se_ve): se oye que funcionó, pero
        hay que comprobar dónde quedó. Lo único que se avisa es quedarse sin
        reproducciones; durante la espera entre usos el botón está apagado y
        no hace nada."""
        camara = self.sistema_camaras.camara_actual
        vistos = self._quienes_se_ven()
        resultado = self.servicios.sonar_audio(self.noche.animatronics, camara)
        if resultado is Resultado.OCUPADO:
            return
        if resultado is Resultado.SIN_USOS:
            self._avisar(MENSAJES_SERVICIO[resultado])
            return
        self.audio.reproducir_efecto_al_azar(EFECTOS_LLAMADA_FLORINDA)
        self.sistema_camaras.sonar_audio_en(camara)
        self._cortar_la_senal_si_cambio_quien_se_ve(vistos)

    # ------------------------------------------------------------------
    # Baterías del suelo
    # ------------------------------------------------------------------
    def _recoger_objeto(self):
        """Lo único que hay tirado son baterías, y van directas al bolsillo."""
        id_objeto = self._objeto_a_la_vista()
        if id_objeto is None or not self.objetos_en_suelo.recoger(id_objeto):
            return
        if id_objeto == ID_BATERIA:
            self.linterna.guardar_bateria()

    def _objeto_a_la_vista(self):
        """Id de lo que el jugador puede recoger ahora mismo, o None. Sin
        apuntarle con la linterna no se puede recoger nada."""
        posicion = self.jugador.posicion_actual
        if not posicion.permite_buscar or not self.linterna.encendida:
            return None
        for id_objeto in self.objetos_en_suelo.objetos_en(posicion.id):
            punto = obtener_objeto(id_objeto).punto_suelo
            if self._le_cabe(id_objeto) and esta_iluminado(punto, self.punto_luz):
                return id_objeto
        return None

    def _le_cabe(self, id_objeto: str) -> bool:
        """No se llevan más baterías de las que caben en el bolsillo. La que
        no cabe ni se recoge ni saca el aviso de recogerla: se queda tirada
        hasta que se vaya sola."""
        return id_objeto != ID_BATERIA or not self.linterna.baterias_llenas

    # ------------------------------------------------------------------
    # Servicios del barril
    # ------------------------------------------------------------------
    def _usar_servicio(self, posicion):
        servicio = self.panel_servicios.boton_en(posicion)
        if servicio is None:
            return
        resultado = self.servicios.usar(servicio, self.noche.animatronics)
        if servicio is Servicio.BARRIGA and resultado in (
            Resultado.AHUYENTADO, Resultado.LLAMADA_EN_VANO,
        ):
            # Suena tanto si la llamada sirvió como si no: lo que se oye es
            # que se marcó, no si Don Ramón estaba ahí para que se lo lleven.
            self.audio.reproducir_efecto(EFECTO_LLAMADA_BARRIGA)
        if servicio is Servicio.BARRIGA and resultado is Resultado.AHUYENTADO:
            # Que la llamada haya servido se oye, no se lee: es Don Ramón
            # largándose después de que el Sr. Barriga fuera por él, con una
            # de sus frases al azar (o la de siempre si no hay variantes).
            if self.audio.reproducir_efecto_al_azar(EFECTOS_SALIDA_RAMON) is None:
                self.audio.reproducir_efecto(EFECTO_RAMON_SE_VA)
        if servicio is Servicio.REPONER_AUDIO and resultado is Resultado.EN_MARCHA:
            # Aquí no suena la grabación: se está reparando la cinta para
            # poder volver a usarla desde el monitor.
            self.audio.reproducir_efecto(EFECTO_REPARACION)
        if resultado is Resultado.LLAMADA_EN_VANO:
            # El Sr. Barriga no llega de inmediato: la muerte se resuelve
            # más tarde, cuando self.servicios.barriga_letal se ponga en
            # True (ver _actualizar).
            return
        aviso = MENSAJES_SERVICIO.get(resultado)
        if aviso is not None:
            self._avisar(aviso)

    # ------------------------------------------------------------------
    # Actualización
    # ------------------------------------------------------------------
    def _actualizar(self, dt: float):
        if self.gestor_estados.en_menu():
            self.menu.actualizar(dt)
            return

        if self.gestor_estados.en_pausa():
            # La partida se congela por completo: ni el reloj, ni la IA, ni
            # la batería avanzan mientras el menú de pausa está abierto.
            return

        if self.gestor_estados.en_periodico():
            self.periodico.actualizar(dt)
            if self.periodico.termino:
                self._mostrar_tarjeta_de_la_noche()
            return

        if self.gestor_estados.en_tarjeta_noche():
            self.tarjeta_noche.actualizar(dt)
            if self.tarjeta_noche.termino:
                self.gestor_estados.cambiar_a(EstadoJuego.JUGANDO)
            return

        if self.gestor_estados.en_susto():
            self.susto.actualizar(dt)
            if self.susto.termino:
                self._mostrar_game_over()
            return

        if self.gestor_estados.en_reloj_victoria():
            self.reloj_victoria.actualizar(dt)
            if self.reloj_victoria.debe_sonar:
                # Golpe de sonido de un solo disparo, justo en el instante en
                # que el reloj cruza de 5:59 a 6:00. No es música de fondo:
                # no se repite ni sigue sonando durante el menú.
                self.audio.reproducir_efecto(EFECTO_NOCHE_SUPERADA)
            if self.reloj_victoria.termino:
                self.menu_victoria.abrir(
                    self.noche.personalizada, self.progreso.proxima_noche,
                    self.reloj_victoria.particulas,
                )
                self.gestor_estados.cambiar_a(EstadoJuego.NOCHE_SUPERADA_MENU)
            return

        if self.gestor_estados.en_menu_victoria():
            self.menu_victoria.actualizar(dt)
            return

        if not self.gestor_estados.jugando():
            return

        self.punto_luz = self.gestor_pantalla.posicion_en_lienzo(pygame.mouse.get_pos())
        self._descontar_bloqueo_de_tiras(dt)
        self._atender_tiras()
        self.linterna.actualizar(dt)
        self.objetos_en_suelo.actualizar(dt)
        self._dejar_pasar_las_apariciones(dt)
        estaban_rotas = self.sistema_camaras.averiadas
        self.sistema_camaras.actualizar(dt, self.noche.animatronics)
        if self.sistema_camaras.averiadas and not estaban_rotas:
            self._llega_el_chavo()
        if self.servicios.actualizar(dt, self.jugador.esta_escondido) in SERVICIOS_QUE_REPARAN_CAMARAS:
            self.sistema_camaras.reparar()
        if self.servicios.barriga_letal:
            # El Sr. Barriga llega exactamente ahora, sin importar qué esté
            # haciendo el jugador en ese momento: la llamada en vano no se
            # puede esquivar cerrando un panel.
            self._perder(nombres.BARRIGA, "game_over_barriga")
            return
        acechaban = self._nombres_acechando()
        vigilados = self._quienes_se_ven()
        self.temporizador.actualizar(dt, self._elenco_en_movimiento())
        if self._atender_busquedas(dt):
            return
        self._sonar_pasos_de_los_que_llegan(acechaban)
        self._cortar_la_senal_si_cambio_quien_se_ve(vigilados)
        self._distorsionar_si_se_movio_florinda()
        self._reaccionar_a_lo_que_ve()
        self.aviso.actualizar(dt)

        if self._murio_por_la_luz():
            return
        self._espantar_con_la_luz(dt)
        self._activar_a_los_alumbrados()
        if self._fue_atacado(dt):
            return
        self.alerta_peligro.actualizar(dt, self._inminencia_del_peligro())

        if self.temporizador.noche_terminada:
            self._ganar_la_noche()

    def _ganar_la_noche(self):
        if not self.noche.personalizada:
            self.progreso.registrar_noche_completada(self.noche.numero)
        self.reloj_victoria.iniciar(self.noche.personalizada)
        self.gestor_estados.cambiar_a(EstadoJuego.NOCHE_SUPERADA_RELOJ)

    def _descontar_bloqueo_de_tiras(self, dt: float):
        """Va gastando el rato muerto que dejó bajar un panel."""
        if self._tiras_bloqueadas > 0.0:
            self._tiras_bloqueadas = max(0.0, self._tiras_bloqueadas - dt)

    def _atender_tiras(self):
        """Las pestañas de abajo se usan pasándoles el ratón por encima, como
        en el género: la misma franja levanta el panel y lo vuelve a bajar.

        Hay dos seguros, y los dos son por lo mismo: las tres pestañas se
        pisan, así que al bajar un panel el cursor se queda encima de la de
        subir sin haberse movido.

        - Usada una, la franja **entera** no vuelve a responder hasta que el
          cursor sale de ella. Por eso el límite es el conjunto y no cada
          pestaña por su lado.
        - Y al bajar un panel se queda muerta TIRAS_BLOQUEO_SEGUNDOS, para
          que ni un roce del ratón en ese medio segundo lo vuelva a levantar.
        """
        if self._tiras_bloqueadas > 0.0:
            return
        if not RECT_FRANJA_TIRAS.collidepoint(self.punto_luz):
            self._tira_usada = False
            return
        if self._tira_usada:
            return
        tira = self._tira_resaltada()
        if not tira:
            return
        self._tira_usada = True
        if tira == "bajar":
            self._bajar_paneles()
        elif tira == "camaras":
            self._levantar_camaras()
        else:
            self.panel_servicios.activo = True

    def _elenco_en_movimiento(self):
        return self.noche.elenco_en_movimiento(self.temporizador.horas_transcurridas())

    def _nombres_acechando(self):
        return {a.nombre for a in acechando(self.noche.animatronics)}

    def _sonar_pasos_de_los_que_llegan(self, acechaban):
        """Unos pasos por cada personaje que acaba de plantarse delante.

        Es el aviso de que hay alguien afuera: sin él, meterse al barril a
        mirar las cámaras sería jugar a ciegas, porque con un panel levantado
        no se ve el patio. Suena el paso del lado por el que apareció, para
        que el jugador sepa hacia dónde apuntar al asomarse.
        """
        for animatronic in self.noche.animatronics:
            if animatronic.esta_acechando() and animatronic.nombre not in acechaban:
                self.audio.reproducir_efecto(self._pasos_de(animatronic))

    def _atender_busquedas(self, dt: float) -> bool:
        """Los objetos escondidos de Doña Clotilde y Jaimico (ver
        dominio/busqueda.py). Al aparecer suenan los pasos como si alguien
        llegara al patio, aunque no haya nadie. Devuelve True si se acabó el
        tiempo de Doña Clotilde, que termina la noche."""
        resultado = self.busquedas.actualizar(dt, self.noche.animatronics)
        for animatronic in resultado.empezadas:
            self.audio.reproducir_efecto(self._pasos_de(animatronic))
        for animatronic, desenlace in resultado.agotadas:
            if desenlace is Desenlace.MATA:
                self._perder(animatronic.nombre, MOTIVO_ESCOBA)
                return True
            animatronic.irrumpir()
        return False

    def _inminencia_del_peligro(self):
        """Lo cerca que está el peligro más apurado, de 0 a 1, o None si no
        hay ninguno: alguien de verdad en el patio o un objeto escondido
        corriendo. La alerta no distingue entre los dos a propósito."""
        candidatas = [
            valor for valor in (
                inminencia_en_el_patio(self.noche.animatronics),
                self.busquedas.inminencia(),
            )
            if valor is not None
        ]
        return max(candidatas) if candidatas else None

    def _quienes_se_ven(self):
        """La cámara que el jugador tiene delante y los nombres de quienes
        están dentro de ella ahora mismo, antes de que alguien se mueva.
        Devuelve la cámara en None si no está mirando el monitor."""
        if not self.sistema_camaras.activo:
            return None, frozenset()
        camara = self.sistema_camaras.camara_actual
        return camara, self._ocupantes_de(camara)

    def _ocupantes_de(self, camara: str) -> frozenset:
        return frozenset(
            animatronic.nombre for animatronic in self.noche.animatronics
            if animatronic.activo and animatronic.habitacion_actual == camara
        )

    def _cortar_la_senal_si_cambio_quien_se_ve(self, vigilados):
        """Si alguien entra o sale de la cámara que se está mirando, esa
        cámara se queda sin señal unos segundos.

        Es lo que le pone precio a vigilar de cerca: se oye la interferencia
        y se sabe que alguien se movió, pero no hacia dónde ni quién llegó,
        así que hay que buscarlo por las demás cámaras.
        """
        camara, antes = vigilados
        if camara is None or self._ocupantes_de(camara) == antes:
            return
        if self.sistema_camaras.perder_senal(camara):
            self.audio.reproducir_efecto_camara(EFECTO_INTERFERENCIA)

    def _donde_esta_florinda(self):
        for animatronic in self.noche.animatronics:
            if animatronic.nombre == nombres.FLORINDA and animatronic.activo:
                return animatronic.habitacion_actual
        return None

    def _distorsionar_si_se_movio_florinda(self):
        """Cuando Doña Florinda cambia de cámara (por su cuenta o por el
        audio), el monitor da un tirón breve en la cámara que se esté
        mirando, sea cual sea: se sabe que se movió, no adónde."""
        ahora = self._donde_esta_florinda()
        if ahora != self._florinda_estaba and self._florinda_estaba is not None:
            self.sistema_camaras.distorsionar()
        self._florinda_estaba = ahora

    def _llega_el_chavo(self):
        """El Chavo acaba de romper las cámaras: aparece de golpe en el
        Primer Patio y hay que enfrentarlo. Suena su llegada en vez de los
        pasos de los demás."""
        for animatronic in self.noche.animatronics:
            if (
                animatronic.nombre == nombres.SABOTEADOR
                and animatronic.activo
                and not animatronic.esta_acechando()
            ):
                animatronic.irrumpir()
                self.audio.reproducir_efecto(EFECTO_LLEGA_CHAVO)
                return

    def _dejar_pasar_las_apariciones(self, dt: float):
        """Las apariciones raras: de vez en cuando se cuela una imagen casi
        transparente con su sonido. No cambia nada del juego."""
        if self.apariciones.actualizar(dt) is not None:
            self.audio.reproducir_efecto(EFECTO_EASTER_EGG)

    def _reaccionar_a_lo_que_ve(self):
        """El sobresalto de encontrarse a alguien plantado en el patio.

        Suena una sola vez por encuentro, no en cada fotograma: mientras siga
        ahí delante el jugador ya lo tiene visto. Vuelve a sonar cuando se
        queda solo y aparece otro, o cuando sale del barril y se lo topa.
        Dentro del barril no suena: ahí no ve el patio, y para eso están los
        pasos.
        """
        tiene_a_alguien_delante = not self.jugador.esta_escondido and bool(
            acechando_en(self.noche.animatronics, self.jugador.posicion)
        )
        if tiene_a_alguien_delante and not self._vio_a_alguien:
            self.audio.reproducir_efecto(EFECTO_SORPRESA)
        self._vio_a_alguien = tiene_a_alguien_delante

    @staticmethod
    def _pasos_de(animatronic) -> str:
        """El lado se mide sobre la vista del Barril, que es el patio de
        frente: sirve igual esté el jugador donde esté, incluso escondido."""
        punto = animatronic.punto_acecho_en(POSICION_BARRIL)
        if punto is not None and punto[0] < ANCHO_PANTALLA // 2:
            return EFECTO_PASOS_IZQUIERDA
        return EFECTO_PASOS_DERECHA

    def _murio_por_la_luz(self) -> bool:
        """Apuntarle la linterna de cerca a quien no tolera la luz es fatal.
        Con un panel delante el haz no llega al patio: el jugador sigue
        expuesto a que lo ataquen, pero no a alumbrar a nadie sin querer."""
        if not self.linterna.encendida or self._hay_panel_delante():
            return False
        victimario = detectar_luz_mortal(
            self.noche.animatronics, self.jugador.posicion, self.punto_luz
        )
        if victimario is None:
            return False
        self._perder(victimario.nombre, "game_over_luz")
        return True

    def _alumbrando_el_patio(self) -> bool:
        """Si el haz llega de verdad al patio: con un panel delante o dentro
        del barril no alumbra a nadie."""
        return (
            self.linterna.encendida
            and not self._hay_panel_delante()
            and not self.jugador.esta_escondido
        )

    def _espantar_con_la_luz(self, dt: float):
        """La linterna como arma: sostener el centro del haz sobre el punto
        débil de quien se espanta con la luz lo saca de encima (ver
        dominio/animatronicos/espanto.py).

        Que funcionó se ve, no se lee: el personaje se va. Y fallarle a La
        Chilindrina tampoco avisa: el jugador se entera porque se queda a
        oscuras de golpe."""
        resultado = self.espanto.actualizar(
            dt, self.noche.animatronics, self.jugador.posicion,
            self.punto_luz, self._alumbrando_el_patio(),
        )
        if resultado.descarga:
            self.linterna.descargar()

    def _activar_a_los_alumbrados(self):
        """Alumbrar a alguien que la luz no mata lo activa: a partir de ahí
        deja de respetar el barril. Es el precio de usar la linterna para
        comprobar quién hay delante."""
        if not self.linterna.encendida or self._hay_panel_delante():
            return
        alumbrados = iluminados_en(
            self.noche.animatronics, self.jugador.posicion,
            self.punto_luz, self.linterna.encendida,
        )
        for animatronic in self.noche.animatronics:
            if animatronic.nombre in alumbrados:
                animatronic.alumbrar()

    def _fue_atacado(self, dt: float) -> bool:
        """Los que ya llegaron esperan un margen antes de atacar.

        Dentro del barril el jugador está a salvo de casi todos: solo Don
        Ramón y Doña Florinda lo alcanzan ahí, y los demás únicamente si ya
        los alumbró alguna vez (ver Animatronic.puede_alcanzar_escondido).

        No hay tregua para nadie: a quien no se va con un servicio se le
        espanta con la linterna, así que no tener con qué responder es haberse
        quedado sin batería o no haberle atinado."""
        for animatronic in self.noche.animatronics:
            if animatronic.descontar_espera(dt, self.jugador.esta_escondido):
                self._perder(animatronic.nombre, MOTIVO_ATRAPADO)
                return True
        return False

    def _actualizar_musica(self):
        estado = self.gestor_estados.estado
        if estado in ESTADOS_EN_SILENCIO:
            self.audio.detener_musica()
            return
        pista = PISTAS_POR_ESTADO.get(estado)
        if pista:
            self.audio.reproducir_musica(pista)

    def _sonar_alerta_del_patio(self):
        """El aviso de que hay alguien en el Primer Patio: suena en bucle
        mientras alguien acecha, se esté donde se esté, y sube de volumen
        conforme se acerca el ataque. En pausa sigue sonando, atenuado como
        todo lo demás; fuera de la noche se calla."""
        en_la_noche = self.gestor_estados.jugando() or self.gestor_estados.en_pausa()
        inminencia = self._inminencia_del_peligro() if en_la_noche else None
        if inminencia is None:
            self.audio.detener_bucle()
            return
        bajo, alto = ALERTA_PATIO_VOLUMEN
        self.audio.sonar_en_bucle(
            EFECTO_ALERTA_PATIO, SUBCARPETA_AMBIENTE, bajo + (alto - bajo) * inminencia
        )

    # ------------------------------------------------------------------
    # Dibujado
    # ------------------------------------------------------------------
    def _dibujar(self):
        self.pantalla.fill(COLOR_NEGRO)

        if self.gestor_estados.en_menu():
            self.menu.dibujar(self.pantalla)
        elif self.gestor_estados.en_periodico():
            self.periodico.dibujar(self.pantalla)
        elif self.gestor_estados.en_tarjeta_noche():
            self.tarjeta_noche.dibujar(self.pantalla)
        elif self.gestor_estados.jugando():
            self._dibujar_partida()
        elif self.gestor_estados.en_pausa():
            # La partida sigue dibujada detrás, tal como quedó al pausar; el
            # menú se pinta encima ya oscurecido.
            self._dibujar_partida()
            self.menu_pausa.dibujar(self.pantalla)
        elif self.gestor_estados.en_susto():
            self.susto.dibujar(self.pantalla)
        elif self.gestor_estados.termino_en_derrota():
            self.interfaz.dibujar_game_over(
                self.pantalla,
                self.noche.derrota.nombre_atacante,
                self.noche.derrota.clave_motivo,
            )
            self.menu_derrota.dibujar(self.pantalla)
        elif self.gestor_estados.en_reloj_victoria():
            self.reloj_victoria.dibujar(self.pantalla)
        elif self.gestor_estados.en_menu_victoria():
            self.menu_victoria.dibujar(self.pantalla)

    def _dibujar_partida(self):
        if self.sistema_camaras.a_la_vista:
            self.sistema_camaras.dibujar(
                self.pantalla,
                animatronics=[a for a in self.noche.animatronics if a.activo],
                fuente=self.interfaz.fuente_camara,
                idiomas=self.idiomas,
                posicion_raton=self.punto_luz,
                estado_servicios=self.servicios.estado(),
                objetos=[
                    (busqueda.id_objeto, busqueda.punto)
                    for busqueda in self.busquedas.en_camara(self.sistema_camaras.camara_actual)
                ],
            )
        else:
            self.vista.dibujar(
                self.pantalla, self.jugador, self.noche.animatronics,
                self.objetos_en_suelo, self.linterna, self.punto_luz,
                fuente=self.interfaz.fuente_camara, idiomas=self.idiomas,
                espanto=self.espanto,
            )
            if self.panel_servicios.activo:
                self.panel_servicios.dibujar(
                    self.pantalla, self.servicios, self.punto_luz
                )
            # El monitor entrando o saliendo va encima de todo lo anterior:
            # sus cuadros solo tapan lo que ocupa el aparato, así que el
            # patio se sigue viendo alrededor mientras se mueve.
            self.sistema_camaras.animacion.dibujar(self.pantalla)

        # Con alguien en el patio todo va y viene entre color y gris y
        # tiembla, también en el monitor; el HUD no, para poder leerlo.
        self.alerta_peligro.dibujar(self.pantalla)
        if self.apariciones.visible:
            # Encima de la escena y debajo del HUD: se ve, pero no tapa nada
            # de lo que hace falta leer.
            self.imagenes_raras.dibujar(
                self.pantalla, self.apariciones.actual, self.apariciones.progreso
            )
        self.interfaz.dibujar_hud(
            self.pantalla, self.temporizador, self.jugador, self.linterna,
            self._estado_hud(),
        )

    def _estado_hud(self) -> EstadoHud:
        return EstadoHud(
            numero_noche=self.noche.numero,
            en_camaras=self.sistema_camaras.activo,
            en_servicios=self.panel_servicios.activo,
            objeto_a_recoger=self._nombre_objeto_a_la_vista(),
            tira_resaltada=self._tira_resaltada(),
            aviso=self.aviso.texto,
        )

    def _tira_resaltada(self) -> str:
        if not self.jugador.esta_escondido:
            return ""
        if self._hay_panel_delante():
            return "bajar" if RECT_TIRA_BAJAR.collidepoint(self.punto_luz) else ""
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
    Juego().ejecutar()
