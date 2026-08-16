"""Menú principal: dibuja las opciones y traduce la interacción en acciones.

No arranca partidas por sí mismo: cuando el jugador elige una noche deja una
SolicitudNoche en `solicitud`, que la capa de aplicación consume. Así el menú
no necesita conocer la clase Juego.

Las tres secciones (principal, ajustes y noche personalizada) comparten el
mismo esqueleto: una lista de EntradaMenu que se recorre con el teclado o con
el ratón, se activa con ENTER o clic, y ajusta su valor con las flechas.
"""

from typing import List, Optional

import pygame

from ...config.audio import VOLUMEN_MAXIMO, VOLUMEN_MINIMO, VOLUMEN_PASO
from ...config.interfaz import (
    COLOR_AMARILLO_AVISO,
    COLOR_NEGRO,
    COLOR_OPCION_DESHABILITADA,
    COLOR_OPCION_NORMAL,
    COLOR_OPCION_RESALTADA,
    FUENTE_TAMANO_MENU,
    FUENTE_TAMANO_TITULO,
    MENU_ALTO_LINEA,
    MENU_MARGEN_IZQUIERDO,
    MENU_TITULO_ALTO_MAXIMO,
    MENU_TITULO_Y,
    MENU_Y_PRIMERA_OPCION,
)
from ...config.partida import NIVEL_IA_MAXIMO, NIVEL_IA_MINIMO, NOCHE_EXTRA
from ...config.rutas import ARCHIVO_MENU_TITULO
from ...config.ventana import TITULO_JUEGO
from ...dominio.animatronicos import niveles_iniciales_personalizada
from ...infraestructura.fuentes import crear_fuente
from . import secciones
from .deslizador import (
    ANCHO_FILA_DESLIZABLE,
    dibujar_deslizador,
    rect_deslizador,
    volumen_en,
)
from .fondo import FondoMenu, TituloMenu
from .modelo import EntradaMenu, SeccionMenu, SolicitudNoche

TECLAS_ARRIBA = (pygame.K_UP, pygame.K_w)
TECLAS_ABAJO = (pygame.K_DOWN, pygame.K_s)
TECLAS_ACTIVAR = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)
TECLAS_IZQUIERDA = (pygame.K_LEFT, pygame.K_a)
TECLAS_DERECHA = (pygame.K_RIGHT, pygame.K_d)


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

        # Nivel de IA (0-20) elegido para cada personaje en la Noche
        # Personalizada. Arrancan todos en 0, como en el género.
        self.niveles_personalizados = niveles_iniciales_personalizada()

        self._fondo = FondoMenu()
        self._titulo = TituloMenu(
            ARCHIVO_MENU_TITULO,
            MENU_TITULO_ALTO_MAXIMO,
            MENU_MARGEN_IZQUIERDO,
            MENU_TITULO_Y,
        )

    def actualizar(self, dt: float):
        self._fondo.actualizar(dt)

    # ------------------------------------------------------------------
    # Entradas de la sección activa
    # ------------------------------------------------------------------
    def _entradas_actuales(self) -> List[EntradaMenu]:
        if self.seccion is SeccionMenu.AJUSTES:
            return secciones.entradas_ajustes(
                self.idiomas, self.configuracion, self.pantalla
            )
        if self.seccion is SeccionMenu.PERSONALIZADA:
            return secciones.entradas_personalizada(
                self.idiomas, self.niveles_personalizados
            )
        return secciones.entradas_principal(self.idiomas, self.progreso)

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
                niveles_ia=dict(self.niveles_personalizados),
            )
        else:
            # El resto de opciones llevan un valor asociado: activarlas con
            # ENTER o con clic avanza al siguiente valor, dando la vuelta.
            self._ajustar_valor(entrada, 1, ciclico=True)

    def _ajustar_valor(self, entrada: EntradaMenu, delta: int, ciclico: bool = False):
        """Aplica las flechas izquierda/derecha sobre las opciones que tienen
        un valor asociado (idioma, resolución, volúmenes, modo streamer y
        niveles de IA de la noche personalizada)."""
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
        elif entrada.nombre_personaje:
            self._ajustar_nivel_ia(entrada.nombre_personaje, delta, ciclico)

    def _ajustar_nivel_ia(self, nombre: str, delta: int, ciclico: bool):
        nivel = self.niveles_personalizados[nombre] + delta
        if ciclico and nivel > NIVEL_IA_MAXIMO:
            nivel = NIVEL_IA_MINIMO
        self.niveles_personalizados[nombre] = max(
            NIVEL_IA_MINIMO, min(NIVEL_IA_MAXIMO, nivel)
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
        """Traduce la posición X del cursor (o del arrastre) dentro de la
        barra a un volumen 0-100."""
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
    def _ir_a_seccion(self, seccion: SeccionMenu):
        self.seccion = seccion
        self.indice_seleccionado = 0

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

    @staticmethod
    def _calcular_rects(entradas: List[EntradaMenu]) -> List[pygame.Rect]:
        """El área sensible de cada opción se calcula con el texto más ancho
        entre su versión normal y la resaltada, para que el cursor no la
        pierda justo al pasar por encima. Las filas con barra deslizante se
        ensanchan hasta cubrir la barra y el porcentaje."""
        fuente = crear_fuente(FUENTE_TAMANO_MENU)
        rects = []
        for indice, entrada in enumerate(entradas):
            if entrada.es_deslizable:
                ancho = ANCHO_FILA_DESLIZABLE
            else:
                ancho = max(
                    fuente.size(entrada.texto)[0],
                    fuente.size(entrada.texto_resaltado)[0],
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
        self._fondo.dibujar(superficie, COLOR_NEGRO)

        if self.seccion is SeccionMenu.PRINCIPAL:
            self._titulo.dibujar(
                superficie,
                crear_fuente(FUENTE_TAMANO_TITULO, negrita=True),
                TITULO_JUEGO,
                COLOR_OPCION_RESALTADA,
            )
        else:
            self._dibujar_titulo_seccion(superficie)

        self._dibujar_entradas(superficie)

    def _dibujar_titulo_seccion(self, superficie: pygame.Surface):
        clave = (
            "ajustes_titulo"
            if self.seccion is SeccionMenu.AJUSTES
            else "personalizada_titulo"
        )
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
            color = self._color_de(entrada, resaltada)
            texto = entrada.texto_resaltado if resaltada else entrada.texto
            superficie.blit(fuente.render(texto, True, color), rects[indice].topleft)

            if entrada.es_deslizable:
                dibujar_deslizador(
                    superficie, indice, self._valor_deslizador(entrada.clave), resaltada
                )

    @staticmethod
    def _color_de(entrada: EntradaMenu, resaltada: bool):
        if not entrada.habilitada:
            return COLOR_OPCION_DESHABILITADA
        return COLOR_OPCION_RESALTADA if resaltada else COLOR_OPCION_NORMAL
