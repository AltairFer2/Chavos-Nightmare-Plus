"""Fondo animado del menú principal.

Cada tanto el fondo salta a una de las variantes "jumpscare" durante un rato
corto y siempre vuelve al original. Encima va una capa de estática generada
por código, para que la imagen nunca quede del todo quieta.

Las imágenes se cargan la primera vez que se dibuja el menú, no al construir
el objeto: así el arranque no se traba y el juego sigue funcionando aunque
todavía no exista ningún archivo de fondo.
"""

import random
from typing import List, Optional

import pygame

from ...config.interfaz import (
    MENU_ESTATICA_ALTO,
    MENU_ESTATICA_ANCHO,
    MENU_ESTATICA_FRAMES,
    MENU_ESTATICA_OPACIDAD,
    MENU_FONDO_VARIANTE_DURACION_MAX,
    MENU_FONDO_VARIANTE_DURACION_MIN,
    MENU_FONDO_VARIANTE_INTERVALO_MAX,
    MENU_FONDO_VARIANTE_INTERVALO_MIN,
)
from ...config.rutas import (
    ARCHIVO_MENU_FONDO,
    DIR_ASSETS_MENU,
    PATRON_MENU_FONDO_VARIANTES,
)
from ...config.ventana import ANCHO_PANTALLA, RESOLUCION_BASE
from ..efectos import generar_frames_estatica


def _cargar_escalado(ruta) -> Optional[pygame.Surface]:
    """Carga una imagen de fondo al tamaño del lienzo. None si no existe o si
    pygame no puede decodificarla."""
    if not ruta.exists():
        return None
    try:
        imagen = pygame.image.load(str(ruta)).convert()
    except pygame.error:
        return None
    if imagen.get_size() != RESOLUCION_BASE:
        imagen = pygame.transform.smoothscale(imagen, RESOLUCION_BASE)
    return imagen


class FondoMenu:
    """Fondo del menú con sus variantes y la capa de estática."""

    def __init__(self):
        self._fondo: Optional[pygame.Surface] = None
        self._variantes: List[pygame.Surface] = []
        self._frames_estatica: List[pygame.Surface] = []
        self._cargado = False

        self._indice_variante: Optional[int] = None
        self._restante_variante = 0.0
        self._hasta_proxima_variante = self._nuevo_intervalo()

    @staticmethod
    def _nuevo_intervalo() -> float:
        return random.uniform(
            MENU_FONDO_VARIANTE_INTERVALO_MIN, MENU_FONDO_VARIANTE_INTERVALO_MAX
        )

    def cargar(self):
        """Lee las imágenes del disco una sola vez."""
        if self._cargado:
            return
        self._cargado = True

        self._fondo = _cargar_escalado(ARCHIVO_MENU_FONDO)
        self._variantes = [
            imagen
            for ruta in sorted(DIR_ASSETS_MENU.glob(PATRON_MENU_FONDO_VARIANTES))
            if (imagen := _cargar_escalado(ruta)) is not None
        ]
        self._frames_estatica = generar_frames_estatica(
            MENU_ESTATICA_FRAMES,
            (MENU_ESTATICA_ANCHO, MENU_ESTATICA_ALTO),
            RESOLUCION_BASE,
            MENU_ESTATICA_OPACIDAD,
        )

    def actualizar(self, dt: float):
        """Alterna entre el fondo original y una variante al azar."""
        if not self._variantes:
            return

        if self._indice_variante is None:
            self._hasta_proxima_variante -= dt
            if self._hasta_proxima_variante <= 0:
                self._indice_variante = random.randrange(len(self._variantes))
                self._restante_variante = random.uniform(
                    MENU_FONDO_VARIANTE_DURACION_MIN, MENU_FONDO_VARIANTE_DURACION_MAX
                )
            return

        self._restante_variante -= dt
        if self._restante_variante <= 0:
            self._indice_variante = None
            self._hasta_proxima_variante = self._nuevo_intervalo()

    def dibujar(self, superficie: pygame.Surface, color_respaldo):
        self.cargar()

        actual = self._fondo
        if self._indice_variante is not None and self._variantes:
            actual = self._variantes[self._indice_variante]

        if actual is not None:
            superficie.blit(actual, (0, 0))
        else:
            superficie.fill(color_respaldo)

        if self._frames_estatica:
            superficie.blit(random.choice(self._frames_estatica), (0, 0))


class TituloMenu:
    """Logotipo del menú principal, con respaldo de texto si falta el arte."""

    def __init__(self, ruta, alto_maximo: int, margen_lateral: int, y: int):
        self._ruta = ruta
        self._alto_maximo = alto_maximo
        self._margen_lateral = margen_lateral
        self._y = y
        self._imagen: Optional[pygame.Surface] = None
        self._cargado = False

    def _cargar(self):
        if self._cargado:
            return
        self._cargado = True
        if not self._ruta.exists():
            return
        try:
            self._imagen = pygame.image.load(str(self._ruta)).convert_alpha()
        except pygame.error:
            self._imagen = None

    def dibujar(self, superficie: pygame.Surface, fuente, texto_respaldo: str, color):
        self._cargar()
        if self._imagen is None:
            texto = fuente.render(texto_respaldo, True, color)
            superficie.blit(
                texto, texto.get_rect(midtop=(ANCHO_PANTALLA // 2, self._y))
            )
            return

        ancho_maximo = ANCHO_PANTALLA - self._margen_lateral * 2
        escala = min(
            ancho_maximo / self._imagen.get_width(),
            self._alto_maximo / self._imagen.get_height(),
            1.0,
        )
        tamano = (
            int(self._imagen.get_width() * escala),
            int(self._imagen.get_height() * escala),
        )
        imagen = pygame.transform.smoothscale(self._imagen, tamano)
        superficie.blit(imagen, imagen.get_rect(midtop=(ANCHO_PANTALLA // 2, self._y)))
