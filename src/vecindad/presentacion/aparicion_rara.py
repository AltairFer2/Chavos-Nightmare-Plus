"""Cómo se ven las apariciones raras (easter eggs).

Las imágenes son assets/eggs/rare N.png. Se dibujan a pantalla completa,
encima de lo que se esté viendo (el patio o el monitor) pero por debajo del
HUD, con una opacidad muy baja: entran y salen suaves y no tapan nada de lo
que el jugador necesita ver. Cuándo salen lo decide dominio/aparicion_rara.py.

Cada imagen se carga la primera vez que aparece: son grandes y la mayoría de
las noches no sale ninguna.
"""

import re
from typing import List

import pygame

from ..config.interfaz import APARICION_RARA_FUNDIDO, APARICION_RARA_OPACIDAD
from ..config.rutas import DIR_ASSETS_EGGS
from ..config.ventana import RESOLUCION_BASE
from ..infraestructura.recursos import CacheImagenes

PATRON_ARCHIVO = re.compile(r"rare (\d+)\.png$", re.IGNORECASE)


def rutas_de_las_apariciones() -> List:
    """Las imágenes raras que hay en disco, en orden por su número."""
    if not DIR_ASSETS_EGGS.exists():
        return []
    numeradas = []
    for ruta in DIR_ASSETS_EGGS.iterdir():
        coincidencia = PATRON_ARCHIVO.match(ruta.name)
        if coincidencia:
            numeradas.append((int(coincidencia.group(1)), ruta))
    return [ruta for _, ruta in sorted(numeradas)]


def opacidad_en(progreso: float) -> int:
    """Entra y sale fundiéndose; en medio se queda en la opacidad máxima,
    que ya es muy baja."""
    if progreso < APARICION_RARA_FUNDIDO:
        factor = progreso / APARICION_RARA_FUNDIDO
    elif progreso > 1.0 - APARICION_RARA_FUNDIDO:
        factor = (1.0 - progreso) / APARICION_RARA_FUNDIDO
    else:
        factor = 1.0
    return round(APARICION_RARA_OPACIDAD * max(0.0, min(1.0, factor)))


class ImagenesRaras:
    """Carga y dibuja las imágenes de las apariciones raras."""

    def __init__(self):
        self._rutas = rutas_de_las_apariciones()
        self._imagenes = CacheImagenes(tamano=RESOLUCION_BASE)

    @property
    def cantidad(self) -> int:
        return len(self._rutas)

    def dibujar(self, superficie: pygame.Surface, indice: int, progreso: float):
        if not 0 <= indice < len(self._rutas):
            return
        ruta = self._rutas[indice]
        imagen = self._imagenes.obtener(ruta.name, ruta)
        if imagen is None:
            return
        imagen.set_alpha(opacidad_en(progreso))
        superficie.blit(imagen, (0, 0))
