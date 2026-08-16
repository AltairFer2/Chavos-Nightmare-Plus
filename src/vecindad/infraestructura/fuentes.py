"""Creación centralizada de fuentes de la interfaz.

La tipografía se configura en config/interfaz.py (FUENTE_NOMBRE y los tamaños).
Si en assets/fuentes/ existe un archivo con ese nombre (.ttf u .otf) se usa
ese archivo; si no, se busca una fuente instalada en el sistema. Así se
puede cambiar a una tipografía propia solo copiando el archivo y editando
FUENTE_NOMBRE, sin tocar el resto del código.
"""

import pygame

from ..config.interfaz import FUENTE_NOMBRE
from ..config.rutas import DIR_ASSETS_FUENTES

EXTENSIONES_FUENTE = (".ttf", ".otf")

_cache_fuentes = {}


def _buscar_archivo_fuente(nombre: str):
    for extension in EXTENSIONES_FUENTE:
        ruta = DIR_ASSETS_FUENTES / f"{nombre}{extension}"
        if ruta.exists():
            return ruta
    return None


def crear_fuente(tamano: int, negrita: bool = False) -> pygame.font.Font:
    """Devuelve una fuente del tamaño pedido, reutilizando las ya creadas."""
    clave = (FUENTE_NOMBRE, tamano, negrita)
    if clave in _cache_fuentes:
        return _cache_fuentes[clave]

    if not pygame.font.get_init():
        pygame.font.init()

    ruta_archivo = _buscar_archivo_fuente(FUENTE_NOMBRE)
    if ruta_archivo is not None:
        fuente = pygame.font.Font(str(ruta_archivo), tamano)
        fuente.set_bold(negrita)
    else:
        fuente = pygame.font.SysFont(FUENTE_NOMBRE, tamano, bold=negrita)

    _cache_fuentes[clave] = fuente
    return fuente
