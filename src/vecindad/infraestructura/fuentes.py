"""Creación centralizada de fuentes de la interfaz.

La tipografía se configura en config/interfaz.py (FUENTE_NOMBRE y los tamaños).
Si en assets/fuentes/ existe un archivo con ese nombre (.ttf u .otf, o con
los sufijos -Regular y -Bold de cada variante) se usa ese archivo; si no, se
busca una fuente instalada en el sistema. Así se
puede cambiar a una tipografía propia solo copiando el archivo y editando
FUENTE_NOMBRE, sin tocar el resto del código.
"""

import pygame

from ..config.interfaz import FUENTE_NOMBRE
from ..config.rutas import DIR_ASSETS_FUENTES

EXTENSIONES_FUENTE = (".ttf", ".otf")

_cache_fuentes = {}


def _buscar_archivo_fuente(nombre: str, negrita: bool = False):
    """El archivo de la familia, prefiriendo la variante pedida: con
    "<nombre>-Bold" la negrita es la de verdad y no una engrosada a mano.
    Devuelve también si el archivo ya es negrita, para no engrosarlo dos
    veces."""
    variantes = (
        ((f"{nombre}-Bold", True), (f"{nombre}-Regular", False), (nombre, False))
        if negrita else
        ((f"{nombre}-Regular", False), (nombre, False))
    )
    for base, es_negrita in variantes:
        for extension in EXTENSIONES_FUENTE:
            ruta = DIR_ASSETS_FUENTES / f"{base}{extension}"
            if ruta.exists():
                return ruta, es_negrita
    return None, False


def crear_fuente(tamano: int, negrita: bool = False) -> pygame.font.Font:
    """Devuelve una fuente del tamaño pedido, reutilizando las ya creadas."""
    clave = (FUENTE_NOMBRE, tamano, negrita)
    if clave in _cache_fuentes:
        return _cache_fuentes[clave]

    if not pygame.font.get_init():
        pygame.font.init()

    ruta_archivo, ya_es_negrita = _buscar_archivo_fuente(FUENTE_NOMBRE, negrita)
    if ruta_archivo is not None:
        fuente = pygame.font.Font(str(ruta_archivo), tamano)
        fuente.set_bold(negrita and not ya_es_negrita)
    else:
        fuente = pygame.font.SysFont(FUENTE_NOMBRE, tamano, bold=negrita)

    _cache_fuentes[clave] = fuente
    return fuente
