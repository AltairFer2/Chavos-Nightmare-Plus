"""Las opciones de la pantalla de derrota: reintentar la noche o volver al
menú principal.

Reintentar va primero y viene marcada: tras un susto, lo normal es querer
volver a intentarlo sin pasar por el menú. Se maneja igual que el menú de
noche superada (flechas y ENTER, o el ratón). El fondo, el título y el
motivo los sigue dibujando InterfazJuego.dibujar_game_over.
"""

from typing import List, Optional

import pygame

from ..config.interfaz import (
    COLOR_OPCION_NORMAL,
    COLOR_OPCION_RESALTADA,
    FUENTE_TAMANO_MENU,
)
from ..config.ventana import ANCHO_PANTALLA
from ..infraestructura.fuentes import crear_fuente
from .menu import SOLICITUD_MENU_PRINCIPAL

SOLICITUD_REINTENTAR = "reintentar"

OPCIONES = (SOLICITUD_REINTENTAR, SOLICITUD_MENU_PRINCIPAL)
CLAVES_TEXTO = {
    SOLICITUD_REINTENTAR: "derrota_reintentar",
    SOLICITUD_MENU_PRINCIPAL: "pausa_menu_principal",
}

# Debajo del motivo de la derrota, dentro de la franja oscura de la pantalla.
Y_PRIMERA_OPCION = 375
ALTO_LINEA = 46

TECLAS_ARRIBA = (pygame.K_UP, pygame.K_w)
TECLAS_ABAJO = (pygame.K_DOWN, pygame.K_s)
TECLAS_ACTIVAR = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)


class MenuDerrota:
    """Reintentar o volver al menú tras perder una noche."""

    def __init__(self, idiomas):
        self.idiomas = idiomas
        self._fuente = crear_fuente(FUENTE_TAMANO_MENU)
        self.indice_seleccionado = 0
        self.solicitud: Optional[str] = None

    def abrir(self):
        """Cada derrota arranca con Reintentar marcado y sin nada pedido."""
        self.indice_seleccionado = 0
        self.solicitud = None

    def manejar_evento(self, evento: pygame.event.Event, posicion_raton=None):
        if evento.type == pygame.KEYDOWN:
            self._manejar_tecla(evento.key)
        elif evento.type == pygame.MOUSEMOTION and posicion_raton is not None:
            indice = self._indice_en_posicion(posicion_raton)
            if indice is not None:
                self.indice_seleccionado = indice
        elif (
            evento.type == pygame.MOUSEBUTTONDOWN
            and evento.button == 1
            and posicion_raton is not None
        ):
            indice = self._indice_en_posicion(posicion_raton)
            if indice is not None:
                self.indice_seleccionado = indice
                self.solicitud = OPCIONES[indice]

    def _manejar_tecla(self, tecla):
        if tecla in TECLAS_ARRIBA:
            self.indice_seleccionado = (self.indice_seleccionado - 1) % len(OPCIONES)
        elif tecla in TECLAS_ABAJO:
            self.indice_seleccionado = (self.indice_seleccionado + 1) % len(OPCIONES)
        elif tecla in TECLAS_ACTIVAR:
            self.solicitud = OPCIONES[self.indice_seleccionado]

    def consumir_solicitud(self) -> Optional[str]:
        solicitud, self.solicitud = self.solicitud, None
        return solicitud

    def _texto(self, opcion: str) -> str:
        return self.idiomas.t(CLAVES_TEXTO[opcion])

    def _rects(self) -> List[pygame.Rect]:
        rects = []
        for indice, opcion in enumerate(OPCIONES):
            ancho, alto = self._fuente.size(self._texto(opcion))
            rects.append(pygame.Rect(
                ANCHO_PANTALLA // 2 - ancho // 2,
                Y_PRIMERA_OPCION + indice * ALTO_LINEA,
                ancho, alto,
            ))
        return rects

    def _indice_en_posicion(self, posicion) -> Optional[int]:
        for indice, rect in enumerate(self._rects()):
            if rect.collidepoint(posicion):
                return indice
        return None

    def dibujar(self, superficie: pygame.Surface):
        for indice, rect in enumerate(self._rects()):
            resaltada = indice == self.indice_seleccionado
            color = COLOR_OPCION_RESALTADA if resaltada else COLOR_OPCION_NORMAL
            texto = self._fuente.render(self._texto(OPCIONES[indice]), True, color)
            superficie.blit(texto, rect.topleft)
