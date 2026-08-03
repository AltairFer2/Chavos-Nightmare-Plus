"""Menú principal del juego y sus dos subpantallas: Ajustes y Noche
Personalizada.

El menú no arranca partidas por sí mismo: cuando el jugador elige una noche
deja una SolicitudNoche en `solicitud`, que main.py consume. Así el menú no
necesita conocer la clase Juego.

Imágenes que espera en assets/menu/ (opcionales, hay respaldo si faltan):
- fondo.png  -> imagen de fondo a pantalla completa
- titulo.png -> logotipo/título del juego
"""

import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional

import pygame

from animatronics import ELENCO_BASE
from constants import (
    ALTO_PANTALLA,
    ANCHO_PANTALLA,
    ARCHIVO_MENU_FONDO,
    ARCHIVO_MENU_TITULO,
    COLOR_AMARILLO_AVISO,
    COLOR_BLANCO,
    COLOR_GRIS_OSCURO,
    COLOR_NEGRO,
    COLOR_OPCION_DESHABILITADA,
    COLOR_OPCION_NORMAL,
    COLOR_OPCION_RESALTADA,
    COLOR_VERDE_ENERGIA,
    DIFICULTAD_MAXIMA,
    DIFICULTAD_MINIMA,
    DIR_ASSETS_MENU,
    FUENTE_TAMANO_MENU,
    FUENTE_TAMANO_TITULO,
    MENU_ALTO_LINEA,
    MENU_DESLIZADOR_ALTO,
    MENU_DESLIZADOR_ANCHO,
    MENU_DESLIZADOR_X,
    MENU_ESTATICA_ALTO,
    MENU_ESTATICA_ANCHO,
    MENU_ESTATICA_FRAMES,
    MENU_ESTATICA_OPACIDAD,
    MENU_FONDO_VARIANTE_DURACION_MAX,
    MENU_FONDO_VARIANTE_DURACION_MIN,
    MENU_FONDO_VARIANTE_INTERVALO_MAX,
    MENU_FONDO_VARIANTE_INTERVALO_MIN,
    MENU_MARGEN_IZQUIERDO,
    MENU_TITULO_ALTO_MAXIMO,
    MENU_TITULO_Y,
    MENU_Y_PRIMERA_OPCION,
    NOCHE_EXTRA,
    PATRON_MENU_FONDO_VARIANTES,
    TITULO_JUEGO,
    VOLUMEN_MAXIMO,
    VOLUMEN_MINIMO,
    VOLUMEN_PASO,
)
from fuentes import crear_fuente

# Claves de EntradaMenu que se controlan con una barra deslizante en vez de
# con texto cíclico. Sus getters/setters viven en Configuracion y GestorAudio.
CLAVES_DESLIZABLES = ("volumen_musica", "volumen_efectos")


def _generar_frame_estatica() -> pygame.Surface:
    """Genera un cuadro de ruido translúcido en escala de grises.

    Se construye el buffer de píxeles con slicing de bytearray (resuelto en
    C, no con un bucle Python por píxel) y se renderiza a baja resolución
    para luego escalar: así el costo real de "por píxel" ocurre una sola vez
    al precalcular los cuadros, no en cada fotograma dibujado.
    """
    ancho, alto = MENU_ESTATICA_ANCHO, MENU_ESTATICA_ALTO
    total = ancho * alto
    grises = random.randbytes(total)
    pixeles = bytearray(total * 4)
    pixeles[0::4] = grises
    pixeles[1::4] = grises
    pixeles[2::4] = grises
    pixeles[3::4] = bytes((MENU_ESTATICA_OPACIDAD,)) * total
    frame = pygame.image.frombuffer(bytes(pixeles), (ancho, alto), "RGBA").convert_alpha()
    return pygame.transform.scale(frame, (ANCHO_PANTALLA, ALTO_PANTALLA))


class SeccionMenu(Enum):
    PRINCIPAL = auto()
    AJUSTES = auto()
    PERSONALIZADA = auto()


@dataclass
class SolicitudNoche:
    """Petición de iniciar una noche, generada al elegir una opción."""

    numero: int
    personalizada: bool = False
    dificultades: Dict[str, int] = field(default_factory=dict)


@dataclass
class EntradaMenu:
    clave: str
    texto: str
    texto_resaltado: str = ""
    habilitada: bool = True

    def __post_init__(self):
        if not self.texto_resaltado:
            self.texto_resaltado = self.texto


class MenuPrincipal:
    """Dibuja el menú y traduce la interacción del jugador en acciones."""

    def __init__(self, idiomas, progreso, configuracion, audio, pantalla):
        self.idiomas = idiomas
        self.progreso = progreso
        self.configuracion = configuracion
        self.audio = audio
        self.pantalla = pantalla

        self.seccion = SeccionMenu.PRINCIPAL
        self.indice_seleccionado = 0
        self.solicitud: Optional[SolicitudNoche] = None
        self.salir_solicitado = False
        self._deslizador_activo: Optional[str] = None  # clave del slider en arrastre

        self.dificultades_personalizadas = {
            config.nombre: config.dificultad for config in ELENCO_BASE
        }

        self._fondo = None
        self._fondos_variantes: List[pygame.Surface] = []
        self._titulo = None
        self._frames_estatica: List[pygame.Surface] = []
        self._imagenes_cargadas = False
        self._rects_actuales: List[pygame.Rect] = []

        # Fondo "jumpscare" animado: cada tanto se cambia a una variante al
        # azar por 1-3 segundos y siempre vuelve al fondo original.
        self._indice_variante_actual: Optional[int] = None
        self._tiempo_restante_variante = 0.0
        self._tiempo_hasta_proxima_variante = self._nuevo_intervalo_variante()

    @staticmethod
    def _nuevo_intervalo_variante() -> float:
        return random.uniform(MENU_FONDO_VARIANTE_INTERVALO_MIN, MENU_FONDO_VARIANTE_INTERVALO_MAX)

    def actualizar(self, dt: float):
        """Avanza el temporizador del fondo animado del menú."""
        if not self._fondos_variantes:
            return

        if self._indice_variante_actual is None:
            self._tiempo_hasta_proxima_variante -= dt
            if self._tiempo_hasta_proxima_variante <= 0:
                self._indice_variante_actual = random.randrange(len(self._fondos_variantes))
                self._tiempo_restante_variante = random.uniform(
                    MENU_FONDO_VARIANTE_DURACION_MIN, MENU_FONDO_VARIANTE_DURACION_MAX
                )
        else:
            self._tiempo_restante_variante -= dt
            if self._tiempo_restante_variante <= 0:
                self._indice_variante_actual = None
                self._tiempo_hasta_proxima_variante = self._nuevo_intervalo_variante()

    # ------------------------------------------------------------------
    # Construcción de las entradas de cada sección
    # ------------------------------------------------------------------
    def _entradas_principal(self) -> List[EntradaMenu]:
        entradas = [
            EntradaMenu("nuevo_juego", self.idiomas.t("menu_nuevo_juego")),
        ]

        if self.progreso.hay_partida_guardada:
            entradas.append(
                EntradaMenu(
                    "continuar",
                    self.idiomas.t("menu_continuar"),
                    self.idiomas.t("menu_continuar_noche", noche=self.progreso.proxima_noche),
                )
            )
        else:
            entradas.append(
                EntradaMenu(
                    "continuar",
                    self.idiomas.t("menu_continuar"),
                    self.idiomas.t("menu_sin_partida"),
                    habilitada=False,
                )
            )

        if self.progreso.noche_extra_desbloqueada:
            entradas.append(EntradaMenu("noche_6", self.idiomas.t("menu_noche_6")))
        if self.progreso.noche_personalizada_desbloqueada:
            entradas.append(
                EntradaMenu("noche_personalizada", self.idiomas.t("menu_noche_personalizada"))
            )

        entradas.append(EntradaMenu("ajustes", self.idiomas.t("menu_ajustes")))
        return entradas

    def _entradas_ajustes(self) -> List[EntradaMenu]:
        estado_streamer = self.idiomas.t(
            "activado" if self.configuracion.modo_streamer else "desactivado"
        )
        estado_pantalla_completa = self.idiomas.t(
            "activado" if self.pantalla.pantalla_completa else "desactivado"
        )
        ancho, alto = self.pantalla.resolucion
        # El selector de resolución solo cambia el tamaño de la ventana: en
        # pantalla completa se sigue mostrando (queda lista para cuando el
        # jugador vuelva a modo ventana), aclarado con un sufijo.
        sufijo_resolucion = (
            f" ({self.idiomas.t('ajustes_resolucion_ventana')})"
            if self.pantalla.pantalla_completa
            else ""
        )
        return [
            EntradaMenu(
                "idioma",
                f"{self.idiomas.t('ajustes_idioma')}: {self.idiomas.nombre_idioma_actual()}",
            ),
            EntradaMenu(
                "pantalla_completa",
                f"{self.idiomas.t('ajustes_pantalla_completa')}: {estado_pantalla_completa}",
            ),
            EntradaMenu(
                "resolucion",
                f"{self.idiomas.t('ajustes_resolucion')}: {ancho} x {alto}{sufijo_resolucion}",
            ),
            EntradaMenu("volumen_musica", self.idiomas.t("ajustes_volumen_musica")),
            EntradaMenu("volumen_efectos", self.idiomas.t("ajustes_volumen_efectos")),
            EntradaMenu(
                "modo_streamer",
                f"{self.idiomas.t('ajustes_modo_streamer')}: {estado_streamer}",
            ),
            EntradaMenu("volver", self.idiomas.t("ajustes_volver")),
        ]

    def _entradas_personalizada(self) -> List[EntradaMenu]:
        entradas = [
            EntradaMenu(f"dificultad::{nombre}", f"{nombre}: {nivel}")
            for nombre, nivel in self.dificultades_personalizadas.items()
        ]
        entradas.append(EntradaMenu("iniciar", self.idiomas.t("personalizada_iniciar")))
        entradas.append(EntradaMenu("volver", self.idiomas.t("personalizada_volver")))
        return entradas

    def _entradas_actuales(self) -> List[EntradaMenu]:
        if self.seccion is SeccionMenu.AJUSTES:
            return self._entradas_ajustes()
        if self.seccion is SeccionMenu.PERSONALIZADA:
            return self._entradas_personalizada()
        return self._entradas_principal()

    # ------------------------------------------------------------------
    # Interacción
    # ------------------------------------------------------------------
    def manejar_evento(self, evento: pygame.event.Event, posicion_raton=None):
        """`posicion_raton` llega ya convertida a coordenadas del lienzo, para
        que los clics acierten sea cual sea la resolución de la ventana."""
        entradas = self._entradas_actuales()
        self._ajustar_indice(len(entradas))

        if evento.type == pygame.KEYDOWN:
            self._manejar_tecla(evento.key, entradas)
        elif evento.type == pygame.MOUSEMOTION and posicion_raton is not None:
            if self._deslizador_activo is not None:
                self._fijar_valor_deslizador(self._deslizador_activo, posicion_raton[0])
            else:
                indice = self._indice_en_posicion(posicion_raton, entradas)
                if indice is not None:
                    self.indice_seleccionado = indice
        elif (
            evento.type == pygame.MOUSEBUTTONDOWN
            and evento.button == 1
            and posicion_raton is not None
        ):
            clave_deslizador = self._deslizador_en_posicion(posicion_raton, entradas)
            if clave_deslizador is not None:
                self.indice_seleccionado = [e.clave for e in entradas].index(clave_deslizador)
                self._deslizador_activo = clave_deslizador
                self._fijar_valor_deslizador(clave_deslizador, posicion_raton[0])
            else:
                indice = self._indice_en_posicion(posicion_raton, entradas)
                if indice is not None:
                    self.indice_seleccionado = indice
                    self._activar(entradas[indice])
        elif evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
            if self._deslizador_activo is not None:
                self._deslizador_activo = None
                self.configuracion.guardar()

    def _manejar_tecla(self, tecla, entradas: List[EntradaMenu]):
        if tecla in (pygame.K_UP, pygame.K_w):
            self.indice_seleccionado = (self.indice_seleccionado - 1) % len(entradas)
        elif tecla in (pygame.K_DOWN, pygame.K_s):
            self.indice_seleccionado = (self.indice_seleccionado + 1) % len(entradas)
        elif tecla in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self._activar(entradas[self.indice_seleccionado])
        elif tecla in (pygame.K_LEFT, pygame.K_a):
            self._ajustar_valor(entradas[self.indice_seleccionado], -1)
        elif tecla in (pygame.K_RIGHT, pygame.K_d):
            self._ajustar_valor(entradas[self.indice_seleccionado], 1)
        elif tecla == pygame.K_ESCAPE:
            if self.seccion is SeccionMenu.PRINCIPAL:
                self.salir_solicitado = True
            else:
                self._ir_a_seccion(SeccionMenu.PRINCIPAL)

    def _activar(self, entrada: EntradaMenu):
        if not entrada.habilitada:
            return

        if entrada.clave == "nuevo_juego":
            self.solicitud = SolicitudNoche(numero=1)
        elif entrada.clave == "continuar":
            self.solicitud = SolicitudNoche(numero=self.progreso.proxima_noche)
        elif entrada.clave == "noche_6":
            self.solicitud = SolicitudNoche(numero=NOCHE_EXTRA)
        elif entrada.clave == "noche_personalizada":
            self._ir_a_seccion(SeccionMenu.PERSONALIZADA)
        elif entrada.clave == "ajustes":
            self._ir_a_seccion(SeccionMenu.AJUSTES)
        elif entrada.clave == "volver":
            self._ir_a_seccion(SeccionMenu.PRINCIPAL)
        elif entrada.clave == "iniciar":
            self.solicitud = SolicitudNoche(
                numero=NOCHE_EXTRA + 1,
                personalizada=True,
                dificultades=dict(self.dificultades_personalizadas),
            )
        else:
            # El resto de opciones llevan un valor asociado: activarlas con
            # ENTER o con clic avanza al siguiente valor, dando la vuelta.
            self._ajustar_valor(entrada, 1, ciclico=True)

    def _ajustar_valor(self, entrada: EntradaMenu, delta: int, ciclico: bool = False):
        """Aplica las flechas izquierda/derecha sobre las opciones que tienen
        un valor asociado (idioma, resolución, volúmenes, modo streamer y
        dificultades de la noche personalizada)."""
        if entrada.clave == "idioma":
            self._cambiar_idioma()
        elif entrada.clave == "pantalla_completa":
            self._alternar_pantalla_completa()
        elif entrada.clave == "resolucion":
            self._cambiar_resolucion(delta)
        elif entrada.clave == "volumen_musica":
            self.configuracion.volumen_musica = self._nuevo_volumen(
                self.configuracion.volumen_musica, delta, ciclico
            )
            self.audio.establecer_volumen_musica(self.configuracion.volumen_musica)
            self.configuracion.guardar()
        elif entrada.clave == "volumen_efectos":
            self.configuracion.volumen_efectos = self._nuevo_volumen(
                self.configuracion.volumen_efectos, delta, ciclico
            )
            self.audio.establecer_volumen_efectos(self.configuracion.volumen_efectos)
            self.configuracion.guardar()
        elif entrada.clave == "modo_streamer":
            self._alternar_modo_streamer()
        elif entrada.clave.startswith("dificultad::"):
            nombre = entrada.clave.split("::", 1)[1]
            nivel = self.dificultades_personalizadas[nombre] + delta
            if ciclico and nivel > DIFICULTAD_MAXIMA:
                nivel = DIFICULTAD_MINIMA
            self.dificultades_personalizadas[nombre] = max(
                DIFICULTAD_MINIMA, min(DIFICULTAD_MAXIMA, nivel)
            )

    @staticmethod
    def _nuevo_volumen(actual: int, delta: int, ciclico: bool) -> int:
        nuevo = actual + delta * VOLUMEN_PASO
        if ciclico and nuevo > VOLUMEN_MAXIMO:
            return VOLUMEN_MINIMO
        return max(VOLUMEN_MINIMO, min(VOLUMEN_MAXIMO, nuevo))

    def _cambiar_idioma(self):
        self.configuracion.idioma = self.idiomas.siguiente_idioma()
        self.configuracion.guardar()

    def _cambiar_resolucion(self, delta: int):
        self.configuracion.resolucion = self.pantalla.siguiente_resolucion(delta or 1)
        self.configuracion.guardar()

    def _alternar_pantalla_completa(self):
        self.pantalla.alternar_pantalla_completa()
        self.configuracion.pantalla_completa = self.pantalla.pantalla_completa
        self.configuracion.guardar()

    def _alternar_modo_streamer(self):
        self.configuracion.modo_streamer = not self.configuracion.modo_streamer
        self.configuracion.guardar()
        self.audio.aplicar_modo_streamer(self.configuracion.modo_streamer)

    # ------------------------------------------------------------------
    # Barras deslizantes de volumen
    # ------------------------------------------------------------------
    def _fila_y_centro(self, indice: int) -> int:
        fuente = crear_fuente(FUENTE_TAMANO_MENU)
        return MENU_Y_PRIMERA_OPCION + indice * MENU_ALTO_LINEA + fuente.get_height() // 2

    def _rect_deslizador(self, indice: int) -> pygame.Rect:
        y_centro = self._fila_y_centro(indice)
        return pygame.Rect(
            MENU_DESLIZADOR_X, y_centro - MENU_DESLIZADOR_ALTO // 2,
            MENU_DESLIZADOR_ANCHO, MENU_DESLIZADOR_ALTO,
        )

    def _deslizador_en_posicion(self, posicion, entradas: List[EntradaMenu]) -> Optional[str]:
        for indice, entrada in enumerate(entradas):
            if entrada.clave in CLAVES_DESLIZABLES and self._rect_deslizador(indice).collidepoint(posicion):
                return entrada.clave
        return None

    def _valor_deslizador(self, clave: str) -> int:
        if clave == "volumen_musica":
            return self.configuracion.volumen_musica
        if clave == "volumen_efectos":
            return self.configuracion.volumen_efectos
        return 0

    def _fijar_valor_deslizador(self, clave: str, x_pixel: int):
        """Traduce la posición X del cursor (o del arrastre) dentro de la
        barra a un volumen 0-100. No guarda en disco en cada llamada: eso
        pasaría en cada MOUSEMOTION mientras se arrastra, que es demasiado
        seguido para escribir a disco; el guardado ocurre al soltar el botón."""
        entradas = self._entradas_actuales()
        indices = [indice for indice, e in enumerate(entradas) if e.clave == clave]
        if not indices:
            return
        rect = self._rect_deslizador(indices[0])
        proporcion = (x_pixel - rect.left) / rect.width if rect.width else 0.0
        valor = round(max(0.0, min(1.0, proporcion)) * VOLUMEN_MAXIMO)

        if clave == "volumen_musica":
            self.configuracion.volumen_musica = valor
            self.audio.establecer_volumen_musica(valor)
        elif clave == "volumen_efectos":
            self.configuracion.volumen_efectos = valor
            self.audio.establecer_volumen_efectos(valor)

    def _dibujar_deslizador(self, superficie: pygame.Surface, indice: int, valor: int, resaltada: bool):
        rect = self._rect_deslizador(indice)
        color_borde = COLOR_OPCION_RESALTADA if resaltada else COLOR_OPCION_NORMAL

        pygame.draw.rect(superficie, COLOR_GRIS_OSCURO, rect, border_radius=rect.height // 2)
        ancho_relleno = int(rect.width * valor / VOLUMEN_MAXIMO)
        if ancho_relleno > 0:
            relleno = pygame.Rect(rect.left, rect.top, ancho_relleno, rect.height)
            pygame.draw.rect(superficie, COLOR_VERDE_ENERGIA, relleno, border_radius=rect.height // 2)
        pygame.draw.rect(superficie, color_borde, rect, width=2, border_radius=rect.height // 2)
        pygame.draw.circle(superficie, COLOR_BLANCO, (rect.left + ancho_relleno, rect.centery), rect.height)

        fuente = crear_fuente(FUENTE_TAMANO_MENU)
        texto_valor = fuente.render(f"{valor}%", True, color_borde)
        superficie.blit(texto_valor, (rect.right + 18, rect.centery - texto_valor.get_height() // 2))

    def _ir_a_seccion(self, seccion: SeccionMenu):
        self.seccion = seccion
        self.indice_seleccionado = 0
        self._rects_actuales = []

    def volver_al_inicio(self):
        """Devuelve el menú a su estado inicial (al salir de una partida)."""
        self._ir_a_seccion(SeccionMenu.PRINCIPAL)
        self.solicitud = None

    def consumir_solicitud(self) -> Optional[SolicitudNoche]:
        solicitud, self.solicitud = self.solicitud, None
        return solicitud

    def _ajustar_indice(self, total: int):
        if total == 0:
            self.indice_seleccionado = 0
        elif self.indice_seleccionado >= total:
            self.indice_seleccionado = total - 1

    def _indice_en_posicion(self, posicion, entradas: List[EntradaMenu]):
        for indice, rect in enumerate(self._calcular_rects(entradas)):
            if rect.collidepoint(posicion):
                return indice
        return None

    def _calcular_rects(self, entradas: List[EntradaMenu]) -> List[pygame.Rect]:
        """El área sensible de cada opción se calcula con el texto más ancho
        entre su versión normal y la resaltada, para que el cursor no la
        pierda justo al pasar por encima. Las filas con barra deslizante se
        ensanchan hasta cubrir la barra y el porcentaje, para que el hover
        no se pierda al pasar del texto a la barra."""
        fuente = crear_fuente(FUENTE_TAMANO_MENU)
        rects = []
        for indice, entrada in enumerate(entradas):
            if entrada.clave in CLAVES_DESLIZABLES:
                ancho = (MENU_DESLIZADOR_X + MENU_DESLIZADOR_ANCHO + 90) - MENU_MARGEN_IZQUIERDO
            else:
                ancho = max(fuente.size(entrada.texto)[0], fuente.size(entrada.texto_resaltado)[0])
            rects.append(
                pygame.Rect(
                    MENU_MARGEN_IZQUIERDO,
                    MENU_Y_PRIMERA_OPCION + indice * MENU_ALTO_LINEA,
                    ancho,
                    fuente.get_height(),
                )
            )
        self._rects_actuales = rects
        return rects

    # ------------------------------------------------------------------
    # Dibujado
    # ------------------------------------------------------------------
    @staticmethod
    def _cargar_fondo_escalado(ruta) -> Optional[pygame.Surface]:
        if not ruta.exists():
            return None
        try:
            imagen = pygame.image.load(str(ruta)).convert()
        except pygame.error:
            return None
        if imagen.get_size() != (ANCHO_PANTALLA, ALTO_PANTALLA):
            imagen = pygame.transform.smoothscale(imagen, (ANCHO_PANTALLA, ALTO_PANTALLA))
        return imagen

    def _cargar_imagenes(self):
        if self._imagenes_cargadas:
            return
        self._imagenes_cargadas = True

        self._fondo = self._cargar_fondo_escalado(ARCHIVO_MENU_FONDO)
        self._fondos_variantes = [
            imagen
            for ruta in sorted(DIR_ASSETS_MENU.glob(PATRON_MENU_FONDO_VARIANTES))
            if (imagen := self._cargar_fondo_escalado(ruta)) is not None
        ]
        self._frames_estatica = [_generar_frame_estatica() for _ in range(MENU_ESTATICA_FRAMES)]

        if ARCHIVO_MENU_TITULO.exists():
            try:
                self._titulo = pygame.image.load(str(ARCHIVO_MENU_TITULO)).convert_alpha()
            except pygame.error:
                self._titulo = None

    def dibujar(self, superficie: pygame.Surface):
        self._cargar_imagenes()

        fondo_actual = self._fondo
        if self._indice_variante_actual is not None and self._fondos_variantes:
            fondo_actual = self._fondos_variantes[self._indice_variante_actual]

        if fondo_actual is not None:
            superficie.blit(fondo_actual, (0, 0))
        else:
            superficie.fill(COLOR_NEGRO)

        if self._frames_estatica:
            superficie.blit(random.choice(self._frames_estatica), (0, 0))

        if self.seccion is SeccionMenu.PRINCIPAL:
            self._dibujar_titulo(superficie)
        else:
            clave_titulo = (
                "ajustes_titulo"
                if self.seccion is SeccionMenu.AJUSTES
                else "personalizada_titulo"
            )
            fuente = crear_fuente(FUENTE_TAMANO_TITULO, negrita=True)
            texto = fuente.render(self.idiomas.t(clave_titulo), True, COLOR_AMARILLO_AVISO)
            superficie.blit(texto, (MENU_MARGEN_IZQUIERDO, MENU_TITULO_Y))

        self._dibujar_entradas(superficie)

    def _dibujar_titulo(self, superficie: pygame.Surface):
        if self._titulo is None:
            fuente = crear_fuente(FUENTE_TAMANO_TITULO, negrita=True)
            texto = fuente.render(TITULO_JUEGO, True, COLOR_OPCION_RESALTADA)
            superficie.blit(texto, texto.get_rect(midtop=(ANCHO_PANTALLA // 2, MENU_TITULO_Y)))
            return

        ancho_maximo = ANCHO_PANTALLA - MENU_MARGEN_IZQUIERDO * 2
        escala = min(
            ancho_maximo / self._titulo.get_width(),
            MENU_TITULO_ALTO_MAXIMO / self._titulo.get_height(),
            1.0,
        )
        tamano = (
            int(self._titulo.get_width() * escala),
            int(self._titulo.get_height() * escala),
        )
        imagen = pygame.transform.smoothscale(self._titulo, tamano)
        superficie.blit(imagen, imagen.get_rect(midtop=(ANCHO_PANTALLA // 2, MENU_TITULO_Y)))

    def _dibujar_entradas(self, superficie: pygame.Surface):
        entradas = self._entradas_actuales()
        self._ajustar_indice(len(entradas))
        rects = self._calcular_rects(entradas)
        fuente = crear_fuente(FUENTE_TAMANO_MENU)

        for indice, entrada in enumerate(entradas):
            resaltada = indice == self.indice_seleccionado
            if not entrada.habilitada:
                color = COLOR_OPCION_DESHABILITADA
            elif resaltada:
                color = COLOR_OPCION_RESALTADA
            else:
                color = COLOR_OPCION_NORMAL
            texto = entrada.texto_resaltado if resaltada else entrada.texto
            superficie.blit(fuente.render(texto, True, color), rects[indice].topleft)

            if entrada.clave in CLAVES_DESLIZABLES:
                self._dibujar_deslizador(superficie, indice, self._valor_deslizador(entrada.clave), resaltada)
