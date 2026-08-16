"""Iconos de los objetos, recortados de la rejilla assets/ui/objetos.png.

La hoja trae los nueve objetos en una rejilla de 3x3 con transparencia. Cada
objeto sabe qué celda le toca (ver dominio/objetos.py) y aquí se recorta y escala
una sola vez por tamaño pedido: el HUD los quiere pequeños y el suelo algo
más grandes, así que se guarda una copia de cada tamaño.
"""

from typing import Dict, Optional, Tuple

import pygame

from ..config.rutas import DIR_ASSETS_UI
from ..dominio.objetos import obtener_objeto
from ..infraestructura.recursos import cargar_imagen

ARCHIVO_HOJA = "objetos.png"
COLUMNAS = 3
FILAS = 3


class IconosObjetos:
    """Recorta y cachea los iconos de la hoja de objetos."""

    def __init__(self):
        self._hoja = cargar_imagen(DIR_ASSETS_UI / ARCHIVO_HOJA, con_alfa=True)
        self._celdas: Dict[str, Optional[pygame.Surface]] = {}
        self._escalados: Dict[Tuple[str, int], Optional[pygame.Surface]] = {}

    def _celda_de(self, id_objeto: str) -> Optional[pygame.Surface]:
        if self._hoja is None:
            return None
        if id_objeto not in self._celdas:
            ancho = self._hoja.get_width() // COLUMNAS
            alto = self._hoja.get_height() // FILAS
            columna, fila = obtener_objeto(id_objeto).celda
            recorte = pygame.Rect(columna * ancho, fila * alto, ancho, alto)
            self._celdas[id_objeto] = self._hoja.subsurface(recorte).copy()
        return self._celdas[id_objeto]

    def obtener(self, id_objeto: str, lado: int) -> Optional[pygame.Surface]:
        """Icono cuadrado del objeto, del lado pedido en píxeles."""
        clave = (id_objeto, lado)
        if clave not in self._escalados:
            celda = self._celda_de(id_objeto)
            self._escalados[clave] = (
                None if celda is None
                else pygame.transform.smoothscale(celda, (lado, lado))
            )
        return self._escalados[clave]
