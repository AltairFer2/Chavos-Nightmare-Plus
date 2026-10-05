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
    EFECTO_CAMBIO_CAMARA,
    EFECTO_ENCENDIDO_CAMARAS,
    EFECTO_INTERFERENCIA,
    EFECTO_LLAMADA_BARRIGA,
    EFECTO_NOCHE_SUPERADA,
    EFECTO_PASOS_DERECHA,
    EFECTO_PASOS_IZQUIERDA,
    EFECTO_RAMON_SE_VA,
    EFECTO_REPARACION,
    EFECTO_SORPRESA,
    EFECTO_SUSTO,
    EFECTOS_LLAMADA_FLORINDA,
    PROPORCION_VOLUMEN_EN_PAUSA,
)
from ..config.interfaz import COLOR_NEGRO, TIRAS_BLOQUEO_SEGUNDOS
from ..config.ventana import ALTO_PANTALLA, ANCHO_PANTALLA, FPS
from ..dominio.animatronicos import (
    acechando,
    acechando_en,
    detectar_luz_mortal,
    detectar_luz_que_descarga,
    iluminados_en,
    nombres,
    objetivo_del_arrojo,
    resolver_arrojo,
)
from ..dominio.arrojo import ObjetoEnVuelo
from ..dominio.inventario import ORDEN_ARROJABLES, Inventario
from ..dominio.jugador import Jugador
from ..dominio.linterna import Linterna, baterias_iniciales, esta_iluminado
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
from ..presentacion.noche_superada import SOLICITUD_CONTINUAR, MenuVictoria, RelojVictoria
from ..presentacion.panel_servicios import PanelServicios
from ..presentacion.vista import VistaJugador
from .aviso import AvisoTemporal
from .entrada import Accion, accion_de, ranura_de
from .estados import EstadoJuego, GestorEstados
from .noche import MOTIVO_ATRAPADO, Noche

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
        self.susto = Susto()
        self.reloj_victoria = RelojVictoria(self.idiomas)
        self.menu_victoria = MenuVictoria(self.idiomas)
        self.periodico = PeriodicoInicial()
        self.tarjeta_noche = TarjetaNoche(self.idiomas)

        self.noche = Noche()
        self.punto_luz = (ANCHO_PANTALLA // 2, ALTO_PANTALLA // 2)
        # El objeto que va por el aire, si hay uno: su efecto llega al caer.
        self.objeto_en_vuelo = None
        self.aviso = AvisoTemporal()
        # Si en el fotograma anterior tenía a alguien delante, para que el
        # sobresalto suene al encontrárselo y no en bucle.
        self._vio_a_alguien = False
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
        self.inventario.reiniciar()
        self.servicios.reiniciar(self.noche.numero)
        self.objetos_en_suelo = ObjetosEnElSuelo(self.noche.numero)
        self.sistema_camaras.reiniciar(CAMARA_INICIAL)
        self.panel_servicios.activo = False
        self.objeto_en_vuelo = None
        self.aviso.limpiar()
        self._vio_a_alguien = False
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
            self.gestor_estados.cambiar_a(EstadoJuego.GAME_OVER)

    def _avisar(self, clave: str, **formato):
        self.aviso.mostrar(self.idiomas.t(clave, **formato))

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
            elif self.gestor_estados.en_pausa():
                self.menu_pausa.manejar_evento(evento, posicion)
            elif self.gestor_estados.en_menu_victoria():
                self.menu_victoria.manejar_evento(evento, posicion)
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

    def _procesar_tecla(self, tecla):
        accion = accion_de(tecla)

        if self.gestor_estados.estado is EstadoJuego.GAME_OVER:
            if accion is Accion.CONFIRMAR:
                self.volver_al_menu()
            elif accion is Accion.ESCAPE:
                self._ejecutando = False
            return

        if not self.gestor_estados.jugando():
            return

        if accion is Accion.ESCAPE:
            self._pausar()
            return

        if accion is not None:
            self._ejecutar_accion(accion)
            return

        ranura = ranura_de(tecla)
        if ranura is not None:
            self._arrojar(ranura)

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
        elif accion is Accion.COMBINAR_CAFE:
            self._combinar_cafe()
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

    def _alternar_camaras(self):
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
        self.sistema_camaras.activo = False
        self.panel_servicios.activo = False
        self._tira_usada = True
        self._tiras_bloqueadas = TIRAS_BLOQUEO_SEGUNDOS

    def _seleccionar_camara(self, posicion):
        if self.sistema_camaras.audio_en(posicion):
            self._sonar_audio_de_quico()
            return
        id_habitacion = self.sistema_camaras.boton_en(posicion)
        if id_habitacion is None:
            return
        if self.sistema_camaras.cambiar_camara(id_habitacion):
            self.audio.reproducir_efecto_camara(EFECTO_CAMBIO_CAMARA)

    def _sonar_audio_de_quico(self):
        """Botón de audio del monitor: gasta una reproducción y le quita una
        cámara de terreno a Doña Florinda.

        A propósito no avisa de si le hizo efecto. Saber dónde quedó es lo
        que se gana mirando las cámaras; si el juego lo dijera, el audio
        pasaría a ser también un detector y no habría razón para vigilarla.
        Lo único que se avisa es quedarse sin reproducciones, porque eso
        explica que el botón no haya hecho nada."""
        resultado = self.servicios.sonar_audio(self.noche.animatronics)
        if resultado is Resultado.SIN_USOS:
            self._avisar(MENSAJES_SERVICIO[resultado])
            return
        self.audio.reproducir_efecto_al_azar(EFECTOS_LLAMADA_FLORINDA)

    # ------------------------------------------------------------------
    # Objetos
    # ------------------------------------------------------------------
    def _recoger_objeto(self):
        """Las baterías van directas a la linterna; el resto, al inventario."""
        id_objeto = self._objeto_a_la_vista()
        if id_objeto is None or not self.objetos_en_suelo.recoger(id_objeto):
            return
        if id_objeto == ID_BATERIA:
            self.linterna.guardar_bateria()
        else:
            self.inventario.guardar(id_objeto)

    def _objeto_a_la_vista(self):
        """Id del objeto que el jugador puede recoger ahora mismo, o None.

        Sin apuntarle con la linterna no se puede recoger nada, y si el haz
        alcanza a varios se recoge el que esté más cerca del centro: para
        los otros hay que mover la luz."""
        posicion = self.jugador.posicion_actual
        if not posicion.permite_buscar or not self.linterna.encendida:
            return None
        x, y = self.punto_luz
        mas_cerca = None
        menor_distancia = None
        for id_objeto in self.objetos_en_suelo.objetos_en(posicion.id):
            punto = obtener_objeto(id_objeto).punto_suelo
            if not self._le_cabe(id_objeto) or not esta_iluminado(punto, self.punto_luz):
                continue
            distancia = (x - punto[0]) ** 2 + (y - punto[1]) ** 2
            if menor_distancia is None or distancia < menor_distancia:
                mas_cerca, menor_distancia = id_objeto, distancia
        return mas_cerca

    def _le_cabe(self, id_objeto: str) -> bool:
        """No se lleva más de uno de cada cosa, ni más baterías de las que
        caben en el bolsillo. Lo que no le cabe ni se recoge ni saca el aviso
        de recogerlo: se queda en su sitio hasta que gaste el suyo."""
        if id_objeto == ID_BATERIA:
            return not self.linterna.baterias_llenas
        return not self.inventario.tiene(id_objeto)

    def _combinar_cafe(self):
        if self.inventario.combinar_cafe():
            self._avisar("cafe_preparado")

    def _arrojar(self, indice: int):
        """Arroja el objeto de esa ranura hacia donde apunta el ratón. Se
        gasta siempre, acierte o no: ese es el castigo por fallar el tiro o
        por tirar el que no tocaba. Mientras uno vuela no sale otro."""
        if self.jugador.esta_escondido or indice >= len(ORDEN_ARROJABLES):
            return
        if self.objeto_en_vuelo is not None:
            return
        id_objeto = ORDEN_ARROJABLES[indice]
        if not self.inventario.gastar(id_objeto):
            return
        self.objeto_en_vuelo = ObjetoEnVuelo(
            id_objeto, tuple(self.punto_luz), self.jugador.posicion
        )

    def _avanzar_objeto_en_vuelo(self, dt: float):
        """Al caer el objeto se decide a quién le dio y qué le hizo. La luz
        se mira en ese momento: a Jaimico hay que tenerlo alumbrado cuando
        le llega el café, no cuando se suelta."""
        vuelo = self.objeto_en_vuelo
        if vuelo is None or not vuelo.avanzar(dt):
            return
        self.objeto_en_vuelo = None
        alcanzado = objetivo_del_arrojo(
            self.noche.animatronics, vuelo.id_posicion, vuelo.destino
        )
        iluminado = alcanzado is not None and alcanzado.nombre in iluminados_en(
            self.noche.animatronics, vuelo.id_posicion,
            self.punto_luz, self.linterna.encendida,
        )
        resultado = resolver_arrojo(alcanzado, vuelo.id_objeto, iluminado)

        nombre_objeto = self.idiomas.t(obtener_objeto(vuelo.id_objeto).clave_texto)
        if resultado.eliminado is not None:
            self._avisar(
                "arrojo_elimina", objeto=nombre_objeto,
                nombre=resultado.eliminado.nombre,
            )
        elif resultado.retrasado is not None:
            self._avisar("arrojo_retrasa", nombre=resultado.retrasado.nombre)
        elif resultado.alcanzado is None:
            self._avisar("arrojo_fallado", objeto=nombre_objeto)
        else:
            self._avisar(
                "arrojo_perdido", objeto=nombre_objeto,
                nombre=resultado.alcanzado.nombre,
            )

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
            # largándose después de que el Sr. Barriga fuera por él.
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
                self.gestor_estados.cambiar_a(EstadoJuego.GAME_OVER)
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
        self.sistema_camaras.actualizar(dt, self.noche.animatronics)
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
        self._sonar_pasos_de_los_que_llegan(acechaban)
        self._cortar_la_senal_de_quien_se_movio(vigilados)
        self._reaccionar_a_lo_que_ve()
        self._avanzar_objeto_en_vuelo(dt)
        self.aviso.actualizar(dt)

        if self._murio_por_la_luz():
            return
        self._castigo_por_la_luz()
        self._activar_a_los_alumbrados()
        if self._fue_atacado(dt):
            return

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

    def _quienes_se_ven(self):
        """La cámara que el jugador tiene delante y quiénes están dentro de
        ella ahora mismo, antes de que corra la ronda de movimiento. Devuelve
        la cámara en None si no está mirando el monitor."""
        if not self.sistema_camaras.activo:
            return None, ()
        camara = self.sistema_camaras.camara_actual
        return camara, tuple(
            animatronic for animatronic in self.noche.animatronics
            if animatronic.activo and animatronic.habitacion_actual == camara
        )

    def _cortar_la_senal_de_quien_se_movio(self, vigilados):
        """Si alguien se movió justo mientras se le estaba mirando, su cámara
        se queda sin señal unos segundos.

        Es lo que le pone precio a vigilar a alguien de cerca: se oye la
        interferencia y se sabe que se fue, pero no hacia dónde, así que hay
        que buscarlo por las demás cámaras en vez de seguirlo con la mirada.
        """
        camara, mirados = vigilados
        if camara is None:
            return
        if not any(otro.habitacion_actual != camara for otro in mirados):
            return
        if self.sistema_camaras.perder_senal(camara):
            self.audio.reproducir_efecto_camara(EFECTO_INTERFERENCIA)

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

    def _castigo_por_la_luz(self):
        """Alumbrar a La Chilindrina cuesta la batería entera, no la noche.

        No cambia de estado ni saca ningún aviso a propósito: la partida
        sigue corriendo igual y el jugador se entera de lo que hizo porque se
        queda a oscuras de golpe."""
        if not self.linterna.encendida or self._hay_panel_delante():
            return
        castigadora = detectar_luz_que_descarga(
            self.noche.animatronics, self.jugador.posicion, self.punto_luz
        )
        if castigadora is not None:
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

        No hay tregua para nadie: cada objeto está siempre en su sitio o a
        punto de volver, así que no tener con qué responder es haberlo
        gastado mal, no mala suerte."""
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
            )
        else:
            self.vista.dibujar(
                self.pantalla, self.jugador, self.noche.animatronics,
                self.objetos_en_suelo, self.linterna, self.punto_luz,
                fuente=self.interfaz.fuente_camara, idiomas=self.idiomas,
            )
            if self.objeto_en_vuelo is not None:
                self.vista.dibujar_objeto_en_vuelo(self.pantalla, self.objeto_en_vuelo)
            if self.panel_servicios.activo:
                self.panel_servicios.dibujar(
                    self.pantalla, self.servicios, self.punto_luz
                )
            # El monitor entrando o saliendo va encima de todo lo anterior:
            # sus cuadros solo tapan lo que ocupa el aparato, así que el
            # patio se sigue viendo alrededor mientras se mueve.
            self.sistema_camaras.animacion.dibujar(self.pantalla)

        self.interfaz.dibujar_hud(
            self.pantalla, self.temporizador, self.jugador, self.linterna,
            self.inventario, self._estado_hud(),
        )

    def _estado_hud(self) -> EstadoHud:
        id_peticion, peticion = self._peticion_de_clotilde()
        return EstadoHud(
            numero_noche=self.noche.numero,
            en_camaras=self.sistema_camaras.activo,
            en_servicios=self.panel_servicios.activo,
            objeto_a_recoger=self._nombre_objeto_a_la_vista(),
            peticion=peticion,
            id_peticion=id_peticion,
            tira_resaltada=self._tira_resaltada(),
            aviso=self.aviso.texto,
        )

    def _peticion_de_clotilde(self):
        """Qué objeto reclama quien lo esté pidiendo delante del jugador."""
        for animatronic in acechando_en(self.noche.animatronics, self.jugador.posicion):
            if animatronic.objeto_pedido is None:
                continue
            objeto = obtener_objeto(animatronic.objeto_pedido)
            return objeto.id, self.idiomas.t(objeto.clave_texto)
        return "", ""

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
