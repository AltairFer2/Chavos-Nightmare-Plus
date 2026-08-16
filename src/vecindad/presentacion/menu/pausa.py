"""Menú de pausa: se abre con ESC durante la noche y congela la partida.

A diferencia del menú principal, no tiene fondo propio: se dibuja encima de
la última imagen de la partida (que la capa de aplicación deja de actualizar
mientras está abierto), oscurecida con una capa translúcida. Solo ofrece
reanudar, ajustar el sonido y volver al menú principal; el resto de los
ajustes (idioma, resolución, pantalla completa, modo streamer) siguen
viviendo únicamente en el menú principal.
"""

from enum import Enum, auto
from typing import List, Optional

import pygame

from ...config.audio import VOLUMEN_MAXIMO, VOLUMEN_MINIMO, VOLUMEN_PASO
from ...config.interfaz import (
    COLOR_AMARILLO_AVISO,
    COLOR_GRIS,
    COLOR_OPCION_NORMAL,
    COLOR_OPCION_RESALTADA,
    FUENTE_TAMANO_CAMARA,
    FUENTE_TAMANO_MENU,
    FUENTE_TAMANO_TITULO,
    MENU_ALTO_LINEA,
    MENU_MARGEN_IZQUIERDO,
    MENU_TITULO_Y,
    MENU_Y_PRIMERA_OPCION,
    PAUSA_OVERLAY_OPACIDAD,
)
from ...config.ventana import ALTO_PANTALLA, ANCHO_PANTALLA, RESOLUCION_BASE
from ...infraestructura.fuentes import crear_fuente
from .deslizador import dibujar_deslizador, rect_deslizador, volumen_en
from .modelo import EntradaMenu

TECLAS_ARRIBA = (pygame.K_UP, pygame.K_w)
TECLAS_ABAJO = (pygame.K_DOWN, pygame.K_s)
TECLAS_ACTIVAR = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)
TECLAS_IZQUIERDA = (pygame.K_LEFT, pygame.K_a)
TECLAS_DERECHA = (pygame.K_RIGHT, pygame.K_d)

# Lo que la capa de aplicación puede leer tras manejar un evento.
SOLICITUD_REANUDAR = "reanudar"
SOLICITUD_MENU_PRINCIPAL = "menu_principal"


class SeccionPausa(Enum):
    PRINCIPAL = auto()
    SONIDO = auto()


class MenuPausa:
    """Reanudar, ajustar el sonido o volver al menú principal."""

    def __init__(self, idiomas, configuracion, audio):
        self.idiomas = idiomas
        self.configuracion = configuracion
        self.audio = audio

        self.seccion = SeccionPausa.PRINCIPAL
        self.indice_seleccionado = 0
        self.solicitud: Optional[str] = None
        self._deslizador_activo: Optional[str] = None

    def abrir(self):
        """Vuelve siempre a la pantalla principal de la pausa, para no
        dejarla abierta en Sonido de la última vez que se usó."""
        self.seccion = SeccionPausa.PRINCIPAL
        self.indice_seleccionado = 0
        self._deslizador_activo = None
        self.solicitud = None

    # ------------------------------------------------------------------
    # Entradas de la sección activa
    # ------------------------------------------------------------------
    def _entradas_actuales(self) -> List[EntradaMenu]:
        if self.seccion is SeccionPausa.SONIDO:
            return [
                EntradaMenu("volumen_musica", self.idiomas.t("ajustes_volumen_musica")),
                EntradaMenu("volumen_efectos", self.idiomas.t("ajustes_volumen_efectos")),
                EntradaMenu("volver", self.idiomas.t("ajustes_volver")),
            ]
        return [
            EntradaMenu("reanudar", self.idiomas.t("pausa_reanudar")),
            EntradaMenu("sonido", self.idiomas.t("pausa_sonido")),
            EntradaMenu("menu_principal", self.idiomas.t("pausa_menu_principal")),
        ]

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
            self._manejar_movimiento(posicion_raton, entradas)
        elif (
            evento.type == pygame.MOUSEBUTTONDOWN
            and evento.button == 1
            and posicion_raton is not None
        ):
            self._manejar_clic(posicion_raton, entradas)
        elif evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
            self._soltar_deslizador()

    def _manejar_movimiento(self, posicion_raton, entradas: List[EntradaMenu]):
        if self._deslizador_activo is not None:
            self._fijar_valor_deslizador(self._deslizador_activo, posicion_raton[0])
            return
        indice = self._indice_en_posicion(posicion_raton, entradas)
        if indice is not None:
            self.indice_seleccionado = indice

    def _manejar_clic(self, posicion_raton, entradas: List[EntradaMenu]):
        clave_deslizador = self._deslizador_en_posicion(posicion_raton, entradas)
        if clave_deslizador is not None:
            self.indice_seleccionado = [e.clave for e in entradas].index(clave_deslizador)
            self._deslizador_activo = clave_deslizador
            self._fijar_valor_deslizador(clave_deslizador, posicion_raton[0])
            return
        indice = self._indice_en_posicion(posicion_raton, entradas)
        if indice is not None:
            self.indice_seleccionado = indice
            self._activar(entradas[indice])

    def _soltar_deslizador(self):
        """El guardado ocurre al soltar, no durante el arrastre: escribir a
        disco en cada MOUSEMOTION sería demasiado seguido."""
        if self._deslizador_activo is None:
            return
        self._deslizador_activo = None
        self.configuracion.guardar()

    def _manejar_tecla(self, tecla, entradas: List[EntradaMenu]):
        if tecla in TECLAS_ARRIBA:
            self.indice_seleccionado = (self.indice_seleccionado - 1) % len(entradas)
        elif tecla in TECLAS_ABAJO:
            self.indice_seleccionado = (self.indice_seleccionado + 1) % len(entradas)
        elif tecla in TECLAS_ACTIVAR:
            self._activar(entradas[self.indice_seleccionado])
        elif tecla in TECLAS_IZQUIERDA:
            self._ajustar_valor(entradas[self.indice_seleccionado], -1)
        elif tecla in TECLAS_DERECHA:
            self._ajustar_valor(entradas[self.indice_seleccionado], 1)
        elif tecla == pygame.K_ESCAPE:
            if self.seccion is SeccionPausa.PRINCIPAL:
                self.solicitud = SOLICITUD_REANUDAR
            else:
                self._ir_a_seccion(SeccionPausa.PRINCIPAL)

    def _activar(self, entrada: EntradaMenu):
        if entrada.clave == "reanudar":
            self.solicitud = SOLICITUD_REANUDAR
        elif entrada.clave == "sonido":
            self._ir_a_seccion(SeccionPausa.SONIDO)
        elif entrada.clave == "menu_principal":
            self.solicitud = SOLICITUD_MENU_PRINCIPAL
        elif entrada.clave == "volver":
            self._ir_a_seccion(SeccionPausa.PRINCIPAL)
        else:
            # Las barras de volumen también se activan con ENTER o con clic:
            # avanzan al siguiente valor, dando la vuelta.
            self._ajustar_valor(entrada, 1, ciclico=True)

    def _ajustar_valor(self, entrada: EntradaMenu, delta: int, ciclico: bool = False):
        if entrada.clave == "volumen_musica":
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

    @staticmethod
    def _nuevo_volumen(actual: int, delta: int, ciclico: bool) -> int:
        nuevo = actual + delta * VOLUMEN_PASO
        if ciclico and nuevo > VOLUMEN_MAXIMO:
            return VOLUMEN_MINIMO
        return max(VOLUMEN_MINIMO, min(VOLUMEN_MAXIMO, nuevo))

    # ------------------------------------------------------------------
    # Barras deslizantes de volumen (misma geometría que en Ajustes)
    # ------------------------------------------------------------------
    def _deslizador_en_posicion(self, posicion, entradas: List[EntradaMenu]) -> Optional[str]:
        for indice, entrada in enumerate(entradas):
            if entrada.es_deslizable and rect_deslizador(indice).collidepoint(posicion):
                return entrada.clave
        return None

    def _valor_deslizador(self, clave: str) -> int:
        if clave == "volumen_musica":
            return self.configuracion.volumen_musica
        if clave == "volumen_efectos":
            return self.configuracion.volumen_efectos
        return 0

    def _fijar_valor_deslizador(self, clave: str, x_pixel: int):
        entradas = self._entradas_actuales()
        indices = [indice for indice, e in enumerate(entradas) if e.clave == clave]
        if not indices:
            return
        valor = volumen_en(rect_deslizador(indices[0]), x_pixel)
        if clave == "volumen_musica":
            self.configuracion.volumen_musica = valor
            self.audio.establecer_volumen_musica(valor)
        elif clave == "volumen_efectos":
            self.configuracion.volumen_efectos = valor
            self.audio.establecer_volumen_efectos(valor)

    # ------------------------------------------------------------------
    # Navegación
    # ------------------------------------------------------------------
    def _ir_a_seccion(self, seccion: SeccionPausa):
        self.seccion = seccion
        self.indice_seleccionado = 0

    def consumir_solicitud(self) -> Optional[str]:
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

    @staticmethod
    def _calcular_rects(entradas: List[EntradaMenu]) -> List[pygame.Rect]:
        fuente = crear_fuente(FUENTE_TAMANO_MENU)
        rects = []
        for indice, entrada in enumerate(entradas):
            ancho = max(
                fuente.size(entrada.texto)[0], fuente.size(entrada.texto_resaltado)[0]
            )
            rects.append(
                pygame.Rect(
                    MENU_MARGEN_IZQUIERDO,
                    MENU_Y_PRIMERA_OPCION + indice * MENU_ALTO_LINEA,
                    ancho,
                    fuente.get_height(),
                )
            )
        return rects

    # ------------------------------------------------------------------
    # Dibujado
    # ------------------------------------------------------------------
    def dibujar(self, superficie: pygame.Surface):
        self._dibujar_oscurecido(superficie)
        self._dibujar_titulo(superficie)
        self._dibujar_entradas(superficie)
        self._dibujar_ayuda(superficie)

    @staticmethod
    def _dibujar_oscurecido(superficie: pygame.Surface):
        """Atenúa la partida congelada que quedó dibujada detrás, para que
        el menú se lea encima sin taparla del todo."""
        capa = pygame.Surface(RESOLUCION_BASE, pygame.SRCALPHA)
        capa.fill((0, 0, 0, PAUSA_OVERLAY_OPACIDAD))
        superficie.blit(capa, (0, 0))

    def _dibujar_titulo(self, superficie: pygame.Surface):
        clave = "pausa_sonido" if self.seccion is SeccionPausa.SONIDO else "pausa_titulo"
        fuente = crear_fuente(FUENTE_TAMANO_TITULO, negrita=True)
        texto = fuente.render(self.idiomas.t(clave), True, COLOR_AMARILLO_AVISO)
        superficie.blit(texto, (MENU_MARGEN_IZQUIERDO, MENU_TITULO_Y))

    def _dibujar_entradas(self, superficie: pygame.Surface):
        entradas = self._entradas_actuales()
        self._ajustar_indice(len(entradas))
        rects = self._calcular_rects(entradas)
        fuente = crear_fuente(FUENTE_TAMANO_MENU)

        for indice, entrada in enumerate(entradas):
            resaltada = indice == self.indice_seleccionado
            color = COLOR_OPCION_RESALTADA if resaltada else COLOR_OPCION_NORMAL
            texto = entrada.texto_resaltado if resaltada else entrada.texto
            superficie.blit(fuente.render(texto, True, color), rects[indice].topleft)

            if entrada.es_deslizable:
                dibujar_deslizador(
                    superficie, indice, self._valor_deslizador(entrada.clave), resaltada
                )

    def _dibujar_ayuda(self, superficie: pygame.Surface):
        fuente = crear_fuente(FUENTE_TAMANO_CAMARA, negrita=True)
        texto = fuente.render(self.idiomas.t("pausa_ayuda"), True, COLOR_GRIS)
        superficie.blit(
            texto, texto.get_rect(center=(ANCHO_PANTALLA // 2, ALTO_PANTALLA - 24))
        )
