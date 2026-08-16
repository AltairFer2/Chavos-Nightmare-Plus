"""Catálogos de texto, un archivo por idioma.

Para agregar un idioma nuevo basta con crear su módulo con un diccionario
TEXTOS y registrarlo en CATALOGOS y NOMBRES_IDIOMAS; el resto del juego no
necesita ningún cambio.
"""

from . import en, es, pt

IDIOMA_POR_DEFECTO = "es"

# El orden decide el ciclo del selector de idioma en Ajustes.
CATALOGOS = {
    "es": es.TEXTOS,
    "en": en.TEXTOS,
    "pt": pt.TEXTOS,
}

IDIOMAS_DISPONIBLES = tuple(CATALOGOS)

NOMBRES_IDIOMAS = {
    "es": "Español",
    "en": "English",
    "pt": "Português",
}

__all__ = [
    "CATALOGOS",
    "IDIOMA_POR_DEFECTO",
    "IDIOMAS_DISPONIBLES",
    "NOMBRES_IDIOMAS",
]
