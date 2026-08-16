"""Traducción de las claves de texto al idioma activo.

Todo texto visible para el jugador debe pedirse con GestorIdiomas.t(clave)
en lugar de escribirse directamente en pantalla, para que el cambio de
idioma desde Ajustes se refleje en todo el juego.
"""

from .textos import (
    CATALOGOS,
    IDIOMA_POR_DEFECTO,
    IDIOMAS_DISPONIBLES,
    NOMBRES_IDIOMAS,
)


class GestorIdiomas:
    """Traduce claves de texto al idioma activo."""

    def __init__(self, idioma: str = IDIOMA_POR_DEFECTO):
        self.idioma = idioma if idioma in IDIOMAS_DISPONIBLES else IDIOMA_POR_DEFECTO

    def cambiar(self, idioma: str):
        if idioma in IDIOMAS_DISPONIBLES:
            self.idioma = idioma

    def siguiente_idioma(self) -> str:
        indice = IDIOMAS_DISPONIBLES.index(self.idioma)
        self.idioma = IDIOMAS_DISPONIBLES[(indice + 1) % len(IDIOMAS_DISPONIBLES)]
        return self.idioma

    def nombre_idioma_actual(self) -> str:
        return NOMBRES_IDIOMAS[self.idioma]

    def t(self, clave: str, **formato) -> str:
        """Devuelve el texto traducido. Si falta en el idioma activo cae al
        español, y si tampoco existe devuelve la clave entre corchetes para
        que el faltante sea evidente en pantalla."""
        texto = CATALOGOS[self.idioma].get(clave)
        if texto is None:
            texto = CATALOGOS[IDIOMA_POR_DEFECTO].get(clave)
        if texto is None:
            return f"[{clave}]"
        return texto.format(**formato) if formato else texto
