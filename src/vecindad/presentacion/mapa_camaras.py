"""El mapa de la vecindad que hace de menú de selección de cámaras.

Va abajo a la derecha del monitor, encima de la franja del HUD. Cada recuadro
con número de cámara es un botón, y el propio arte trae ya la variante con la
cámara activa resaltada ("Cam N Selected.png"), así que aquí no se pinta la
selección: solo el resaltado del recuadro que está bajo el ratón.
"""

from typing import Dict, Optional, Tuple

import pygame

from ..config.interfaz import (
    CAMARA_MAPA_ALTO,
    CAMARA_MAPA_ANCHO,
    CAMARA_MAPA_MARGEN_DERECHO,
    CAMARA_MAPA_MARGEN_INFERIOR,
)
from ..config.rutas import DIR_ASSETS_CAMARAS
from ..config.ventana import ALTO_PANTALLA, ANCHO_PANTALLA
from ..infraestructura.recursos import CacheImagenes, quitar_fondo_negro

NOMBRE_MAPA_SIN_SELECCION = "Cam Unselected.png"

# Rectángulo del mapa dentro de la pantalla. Queda arriba de la franja del
# HUD para no taparle la batería ni la hora.
RECT_MAPA = pygame.Rect(
    ANCHO_PANTALLA - CAMARA_MAPA_ANCHO - CAMARA_MAPA_MARGEN_DERECHO,
    ALTO_PANTALLA - CAMARA_MAPA_ALTO - CAMARA_MAPA_MARGEN_INFERIOR,
    CAMARA_MAPA_ANCHO,
    CAMARA_MAPA_ALTO,
)

# Posición de cada recuadro del mapa, en fracciones del ancho y alto de la
# imagen. Están medidas sobre el arte, así que siguen valiendo aunque se
# cambie el tamaño con el que se dibuja el mapa en pantalla.
BOTONES_MAPA: Dict[str, Tuple[float, float, float, float]] = {
    "casa_paty": (0.153, 0.037, 0.115, 0.099),
    "segundo_patio": (0.445, 0.010, 0.108, 0.097),
    "casa_godinez": (0.735, 0.033, 0.118, 0.108),
    "casa_popis": (0.139, 0.214, 0.113, 0.105),
    "casa_chavo": (0.737, 0.222, 0.116, 0.099),
    "casa_jaimito": (0.084, 0.456, 0.119, 0.125),
    "casa_florinda": (0.806, 0.457, 0.115, 0.124),
    "casa_clotilde": (0.084, 0.650, 0.119, 0.145),
    "primer_patio": (0.796, 0.614, 0.122, 0.099),
    "casa_ramon": (0.806, 0.733, 0.115, 0.099),
    "entrada": (0.436, 0.907, 0.110, 0.076),
}

COLOR_HOVER = (255, 255, 255, 46)
COLOR_BORDE_HOVER = (210, 235, 255)

# Por dónde se puede mover el mapa cuando se vuelve errático: nunca más abajo
# de su sitio, para no meterse en la franja de las pestañas (pasar por ahí
# baja el monitor), ni fuera de la pantalla.
AREA_MOVIMIENTO_MAPA = pygame.Rect(0, 0, ANCHO_PANTALLA, RECT_MAPA.bottom)


class MapaVecindad:
    """Menú de cámaras: sabe qué recuadro cae bajo el ratón y se dibuja."""

    def __init__(self):
        # El mapa viene dibujado sobre fondo negro: se le quita el fondo para
        # que flote sobre la imagen de la cámara en vez de taparla con un
        # recuadro negro.
        self._mapas = CacheImagenes(
            tamano=RECT_MAPA.size, transformacion=quitar_fondo_negro
        )
        self._sin_seleccion = self._mapas.obtener(
            NOMBRE_MAPA_SIN_SELECCION, DIR_ASSETS_CAMARAS / NOMBRE_MAPA_SIN_SELECCION
        )
        self._botones = self._calcular_botones()
        self._desplazamiento = (0, 0)

    @property
    def desplazamiento(self):
        return self._desplazamiento

    @desplazamiento.setter
    def desplazamiento(self, desplazamiento):
        """Corre el mapa entero, botones incluidos, sin salirse de su área.
        Lo dibujado y lo que responde al clic se mueven siempre juntos."""
        movido = RECT_MAPA.move(desplazamiento).clamp(AREA_MOVIMIENTO_MAPA)
        self._desplazamiento = (movido.x - RECT_MAPA.x, movido.y - RECT_MAPA.y)

    @property
    def rect(self) -> pygame.Rect:
        """Dónde está el mapa ahora mismo."""
        return RECT_MAPA.move(self._desplazamiento)

    @staticmethod
    def _calcular_botones() -> Dict[str, pygame.Rect]:
        """Pasa los recuadros del mapa de fracciones a píxeles de pantalla."""
        return {
            id_habitacion: pygame.Rect(
                RECT_MAPA.x + int(x * RECT_MAPA.width),
                RECT_MAPA.y + int(y * RECT_MAPA.height),
                int(ancho * RECT_MAPA.width),
                int(alto * RECT_MAPA.height),
            )
            for id_habitacion, (x, y, ancho, alto) in BOTONES_MAPA.items()
        }

    def boton_en(self, posicion) -> Optional[str]:
        """Habitación cuyo recuadro del mapa contiene ese punto, o None."""
        if posicion is None:
            return None
        # Se mueve el punto al revés en vez de mover cada recuadro.
        x = posicion[0] - self._desplazamiento[0]
        y = posicion[1] - self._desplazamiento[1]
        for id_habitacion, rect in self._botones.items():
            if rect.collidepoint(x, y):
                return id_habitacion
        return None

    def dibujar(self, superficie: pygame.Surface, habitacion, id_activa: str,
                posicion_raton=None, en_transicion: bool = False):
        # Durante la transición se enseña el mapa sin nada resaltado, como si
        # el monitor todavía no hubiera enganchado la señal nueva.
        mapa = None
        if not en_transicion:
            mapa = self._mapas.obtener(habitacion.id, habitacion.ruta_mapa)
        if mapa is None:
            mapa = self._sin_seleccion
        if mapa is None:
            return

        # Dos pasadas: al venir el trazo suavizado, buena parte del mapa
        # queda a medio alfa y sobre la imagen de la cámara se leería muy
        # flojo. Superponerlo consigo mismo lo refuerza sin devolverle el
        # fondo negro.
        superficie.blit(mapa, self.rect)
        superficie.blit(mapa, self.rect)

        self._dibujar_hover(superficie, id_activa, posicion_raton)

    def _dibujar_hover(self, superficie, id_activa: str, posicion_raton):
        id_hover = self.boton_en(posicion_raton)
        if id_hover is None or id_hover == id_activa:
            return
        rect = self._botones[id_hover].move(self._desplazamiento)
        resaltado = pygame.Surface(rect.size, pygame.SRCALPHA)
        resaltado.fill(COLOR_HOVER)
        superficie.blit(resaltado, rect)
        pygame.draw.rect(superficie, COLOR_BORDE_HOVER, rect, width=2)
