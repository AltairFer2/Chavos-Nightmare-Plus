"""Internacionalización: español, inglés y portugués.

Los catálogos de texto viven en textos/ (un archivo por idioma) y GestorIdiomas
resuelve una clave al idioma activo, con respaldo al español.
"""

from .gestor import GestorIdiomas
from .textos import IDIOMA_POR_DEFECTO, IDIOMAS_DISPONIBLES, NOMBRES_IDIOMAS

__all__ = [
    "GestorIdiomas",
    "IDIOMA_POR_DEFECTO",
    "IDIOMAS_DISPONIBLES",
    "NOMBRES_IDIOMAS",
]
