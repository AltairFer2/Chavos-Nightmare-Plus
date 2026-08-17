"""Lo que se ve al ganar una noche, en dos pasos.

1. RelojVictoria: el reloj salta de las 5:59 a las 6:00 am, junto con el
   título de "sobreviviste la noche" y la serpentina cayendo (generada por
   código, sin assets). No se puede interactuar con él; termina solo y da
   paso al menú.
2. MenuVictoria: pregunta si se continúa a la siguiente noche o se vuelve al
   menú principal. Sigue con la misma serpentina que ya venía cayendo desde
   el reloj (no arranca una tanda nueva) y deja espacio para una imagen de
   fondo cuando exista. A propósito no ofrece salir del juego: ganar la
   noche no debería dar pie a cerrarlo por accidente.

El golpe de sonido de la noche superada no lo reproduce nada de este módulo:
suena una sola vez, justo cuando RelojVictoria.debe_sonar se pone en True
(ver Juego._actualizar), y no es música de fondo, así que nunca se repite en
bucle ni sigue sonando durante el menú.
"""

from typing import List, Optional

import pygame

from ..config.interfaz import (
    COLOR_GRIS,
    COLOR_NEGRO,
    COLOR_OPCION_NORMAL,
    COLOR_OPCION_RESALTADA,
    COLOR_VERDE_ENERGIA,
    CONFETI_BALANCEO_AMPLITUD,
    CONFETI_CANTIDAD,
    CONFETI_CAIDA_MAXIMA,
    CONFETI_CAIDA_MINIMA,
    CONFETI_COLORES,
    CONFETI_GIRO_MAXIMO,
    CONFETI_GROSOR,
    CONFETI_LARGO_MAXIMO,
    CONFETI_LARGO_MINIMO,
    FUENTE_TAMANO_CAMARA,
    FUENTE_TAMANO_MENU,
    FUENTE_TAMANO_RELOJ,
    FUENTE_TAMANO_TITULO,
    MENU_ALTO_LINEA,
    MENU_Y_PRIMERA_OPCION,
)
from ..config.partida import RELOJ_VICTORIA_SEGUNDOS_5_59, RELOJ_VICTORIA_SEGUNDOS_6_00
from ..config.rutas import DIR_ASSETS_UI
from ..config.ventana import ALTO_PANTALLA, ANCHO_PANTALLA, RESOLUCION_BASE
from ..infraestructura.fuentes import crear_fuente
from ..infraestructura.recursos import CacheImagenes
from .efectos import Confeti, actualizar_confeti, dibujar_confeti, generar_confeti
from .menu import SOLICITUD_MENU_PRINCIPAL

# Lo que la capa de aplicación puede leer tras manejar un evento del menú.
# SOLICITUD_MENU_PRINCIPAL se reutiliza de pausa.py: significa lo mismo ahí
# y aquí.
SOLICITUD_CONTINUAR = "continuar"

TECLAS_ARRIBA = (pygame.K_UP, pygame.K_w)
TECLAS_ABAJO = (pygame.K_DOWN, pygame.K_s)
TECLAS_ACTIVAR = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)

ARCHIVO_NOCHE_SUPERADA_FONDO = "noche superada.png"

# El título de la noche personalizada ("¡SOBREVIVISTE LA NOCHE
# PERSONALIZADA!") es bastante más largo que el normal; a tamaño fijo se
# salía de la pantalla. Se va reduciendo de a pasos hasta que entra, sin
# achicarlo más de la cuenta si el texto ya entraba de entrada.
TITULO_MARGEN_LATERAL = 60
TITULO_TAMANO_MINIMO = 34
TITULO_TAMANO_PASO = 4


def _fuente_titulo_ajustada(texto: str) -> pygame.font.Font:
    ancho_maximo = ANCHO_PANTALLA - TITULO_MARGEN_LATERAL * 2
    tamano = FUENTE_TAMANO_TITULO
    fuente = crear_fuente(tamano, negrita=True)
    while fuente.size(texto)[0] > ancho_maximo and tamano > TITULO_TAMANO_MINIMO:
        tamano -= TITULO_TAMANO_PASO
        fuente = crear_fuente(tamano, negrita=True)
    return fuente


def _generar_confeti_inicial() -> List[Confeti]:
    return generar_confeti(
        CONFETI_CANTIDAD, ANCHO_PANTALLA, ALTO_PANTALLA, CONFETI_COLORES,
        CONFETI_LARGO_MINIMO, CONFETI_LARGO_MAXIMO,
        CONFETI_CAIDA_MINIMA, CONFETI_CAIDA_MAXIMA, CONFETI_GIRO_MAXIMO,
    )


def _dibujar_titulo(superficie: pygame.Surface, idiomas, noche_personalizada: bool):
    clave = "victoria_personalizada" if noche_personalizada else "victoria_titulo"
    texto = idiomas.t(clave)
    fuente = _fuente_titulo_ajustada(texto)
    render = fuente.render(texto, True, COLOR_VERDE_ENERGIA)
    superficie.blit(render, render.get_rect(center=(ANCHO_PANTALLA // 2, 220)))


class RelojVictoria:
    """El reloj final: salta de 5:59 a 6:00, con el título y la serpentina
    ya en pantalla desde el primer momento."""

    def __init__(self, idiomas):
        self.idiomas = idiomas
        self._restante = 0.0
        self.termino = False
        # Un único fotograma en True: el que cruza de 5:59 a 6:00. Quien
        # orquesta la partida lo revisa después de cada actualizar() para
        # disparar el efecto de sonido ahí y solo ahí.
        self.debe_sonar = False
        self.noche_personalizada = False
        self.particulas: List[Confeti] = []

    def iniciar(self, noche_personalizada: bool):
        self._restante = RELOJ_VICTORIA_SEGUNDOS_5_59 + RELOJ_VICTORIA_SEGUNDOS_6_00
        self.termino = False
        self.debe_sonar = False
        self.noche_personalizada = noche_personalizada
        self.particulas = _generar_confeti_inicial()

    def actualizar(self, dt: float):
        self.debe_sonar = False
        if self.termino:
            return
        mostraba_6_00 = self._mostrando_6_00
        self._restante -= dt
        actualizar_confeti(
            self.particulas, dt, ANCHO_PANTALLA, ALTO_PANTALLA, CONFETI_BALANCEO_AMPLITUD
        )
        if self._restante <= 0.0:
            self.termino = True
        elif not mostraba_6_00 and self._mostrando_6_00:
            self.debe_sonar = True

    @property
    def _mostrando_6_00(self) -> bool:
        return self._restante <= RELOJ_VICTORIA_SEGUNDOS_6_00

    def dibujar(self, superficie: pygame.Surface):
        superficie.fill(COLOR_NEGRO)
        dibujar_confeti(superficie, self.particulas, CONFETI_GROSOR)
        _dibujar_titulo(superficie, self.idiomas, self.noche_personalizada)

        texto = "6:00 AM" if self._mostrando_6_00 else "5:59 AM"
        fuente = crear_fuente(FUENTE_TAMANO_RELOJ, negrita=True)
        render = fuente.render(texto, True, (255, 255, 255))
        superficie.blit(
            render, render.get_rect(center=(ANCHO_PANTALLA // 2, ALTO_PANTALLA // 2))
        )


class MenuVictoria:
    """Continuar a la siguiente noche o volver al menú principal."""

    def __init__(self, idiomas):
        self.idiomas = idiomas
        self._fondos = CacheImagenes(tamano=RESOLUCION_BASE)
        self._particulas: List[Confeti] = []
        self.noche_personalizada = False
        self.proxima_noche = 1
        self.indice_seleccionado = 0
        self.solicitud: Optional[str] = None

    def abrir(self, noche_personalizada: bool, proxima_noche: int, particulas: List[Confeti]):
        """`particulas` es la misma serpentina que ya venía cayendo desde
        RelojVictoria: seguir con ella, en vez de arrancar una tanda nueva,
        es lo que hace que el efecto se sienta continuo entre las dos
        pantallas."""
        self.noche_personalizada = noche_personalizada
        self.proxima_noche = proxima_noche
        self.indice_seleccionado = 0
        self.solicitud = None
        self._particulas = particulas

    def _opciones(self):
        # La noche personalizada no forma parte de la campaña: no hay una
        # "siguiente" definida a la que continuar, así que solo queda volver.
        if self.noche_personalizada:
            return (SOLICITUD_MENU_PRINCIPAL,)
        return (SOLICITUD_CONTINUAR, SOLICITUD_MENU_PRINCIPAL)

    def _texto_opcion(self, clave: str) -> str:
        if clave == SOLICITUD_CONTINUAR:
            return self.idiomas.t("menu_continuar_noche", noche=self.proxima_noche)
        return self.idiomas.t("pausa_menu_principal")

    # ------------------------------------------------------------------
    # Actualización
    # ------------------------------------------------------------------
    def actualizar(self, dt: float):
        actualizar_confeti(
            self._particulas, dt, ANCHO_PANTALLA, ALTO_PANTALLA, CONFETI_BALANCEO_AMPLITUD
        )

    # ------------------------------------------------------------------
    # Interacción
    # ------------------------------------------------------------------
    def manejar_evento(self, evento: pygame.event.Event, posicion_raton=None):
        opciones = self._opciones()
        if self.indice_seleccionado >= len(opciones):
            self.indice_seleccionado = len(opciones) - 1

        if evento.type == pygame.KEYDOWN:
            self._manejar_tecla(evento.key, opciones)
        elif evento.type == pygame.MOUSEMOTION and posicion_raton is not None:
            indice = self._indice_en_posicion(posicion_raton, opciones)
            if indice is not None:
                self.indice_seleccionado = indice
        elif (
            evento.type == pygame.MOUSEBUTTONDOWN
            and evento.button == 1
            and posicion_raton is not None
        ):
            indice = self._indice_en_posicion(posicion_raton, opciones)
            if indice is not None:
                self.indice_seleccionado = indice
                self.solicitud = opciones[indice]

    def _manejar_tecla(self, tecla, opciones):
        if tecla in TECLAS_ARRIBA:
            self.indice_seleccionado = (self.indice_seleccionado - 1) % len(opciones)
        elif tecla in TECLAS_ABAJO:
            self.indice_seleccionado = (self.indice_seleccionado + 1) % len(opciones)
        elif tecla in TECLAS_ACTIVAR:
            self.solicitud = opciones[self.indice_seleccionado]
        # A propósito no hay tecla para salir del juego desde aquí.

    def _rects(self, opciones) -> List[pygame.Rect]:
        fuente = crear_fuente(FUENTE_TAMANO_MENU)
        rects = []
        for indice, clave in enumerate(opciones):
            ancho = fuente.size(self._texto_opcion(clave))[0]
            rects.append(pygame.Rect(
                ANCHO_PANTALLA // 2 - ancho // 2,
                MENU_Y_PRIMERA_OPCION + indice * MENU_ALTO_LINEA,
                ancho, fuente.get_height(),
            ))
        return rects

    def _indice_en_posicion(self, posicion, opciones):
        for indice, rect in enumerate(self._rects(opciones)):
            if rect.collidepoint(posicion):
                return indice
        return None

    def consumir_solicitud(self) -> Optional[str]:
        solicitud, self.solicitud = self.solicitud, None
        return solicitud

    # ------------------------------------------------------------------
    # Dibujado
    # ------------------------------------------------------------------
    def dibujar(self, superficie: pygame.Surface):
        fondo = self._fondos.obtener(
            ARCHIVO_NOCHE_SUPERADA_FONDO, DIR_ASSETS_UI / ARCHIVO_NOCHE_SUPERADA_FONDO
        )
        if fondo is not None:
            superficie.blit(fondo, (0, 0))
        else:
            superficie.fill(COLOR_NEGRO)

        dibujar_confeti(superficie, self._particulas, CONFETI_GROSOR)
        _dibujar_titulo(superficie, self.idiomas, self.noche_personalizada)

        opciones = self._opciones()
        fuente = crear_fuente(FUENTE_TAMANO_MENU)
        for indice, rect in enumerate(self._rects(opciones)):
            resaltada = indice == self.indice_seleccionado
            color = COLOR_OPCION_RESALTADA if resaltada else COLOR_OPCION_NORMAL
            texto = fuente.render(self._texto_opcion(opciones[indice]), True, color)
            superficie.blit(texto, rect.topleft)

        fuente_ayuda = crear_fuente(FUENTE_TAMANO_CAMARA, negrita=True)
        ayuda = fuente_ayuda.render(self.idiomas.t("noche_superada_ayuda"), True, COLOR_GRIS)
        superficie.blit(
            ayuda, ayuda.get_rect(center=(ANCHO_PANTALLA // 2, ALTO_PANTALLA - 24))
        )
