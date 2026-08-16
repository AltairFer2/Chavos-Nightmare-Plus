"""Reproducción de música y efectos, con soporte para el modo streamer.

El modo streamer decide de qué árbol de carpetas se lee TODO el audio:
- desactivado -> sonidos/con_copyright/
- activado    -> sonidos/sin_copyright/

Ambos árboles comparten estructura y nombres de archivo, así que el juego
pide siempre "musica/menu" y este módulo resuelve la ruta según el modo.
Si falta un archivo o no hay dispositivo de audio, la reproducción se omite
en silencio: la ausencia de assets no debe impedir jugar.
"""

import random
from typing import Optional

import pygame

from ..config.audio import (
    EXTENSIONES_AUDIO,
    PISTAS_MUSICA,
    SUBCARPETA_CAMARAS,
    SUBCARPETA_EFECTOS,
    SUBCARPETA_MUSICA,
    VOLUMEN_EFECTOS_POR_DEFECTO,
    VOLUMEN_MAXIMO,
    VOLUMEN_MUSICA_POR_DEFECTO,
)
from ..config.rutas import DIR_SONIDOS_CON_COPYRIGHT, DIR_SONIDOS_SIN_COPYRIGHT


class GestorAudio:
    """Resuelve las rutas de audio según el modo streamer y reproduce."""

    def __init__(
        self,
        modo_streamer: bool = False,
        volumen_musica: int = VOLUMEN_MUSICA_POR_DEFECTO,
        volumen_efectos: int = VOLUMEN_EFECTOS_POR_DEFECTO,
    ):
        self.modo_streamer = bool(modo_streamer)
        self.volumen_musica = volumen_musica
        self.volumen_efectos = volumen_efectos
        self.disponible = self._inicializar_mezclador()
        self._pista_actual = None
        self._efectos_cache = {}
        if self.disponible:
            pygame.mixer.music.set_volume(self._proporcion(self.volumen_musica))

    @staticmethod
    def _inicializar_mezclador() -> bool:
        try:
            pygame.mixer.init()
        except pygame.error:
            return False
        return True

    @property
    def carpeta_base(self):
        if self.modo_streamer:
            return DIR_SONIDOS_SIN_COPYRIGHT
        return DIR_SONIDOS_CON_COPYRIGHT

    @staticmethod
    def _proporcion(volumen: int) -> float:
        """Convierte el volumen en porcentaje (0-100) al 0.0-1.0 de pygame."""
        return max(0.0, min(1.0, volumen / VOLUMEN_MAXIMO))

    def _buscar_archivo(self, subcarpeta: str, nombre: str):
        carpeta = self.carpeta_base / subcarpeta
        for extension in EXTENSIONES_AUDIO:
            ruta = carpeta / f"{nombre}{extension}"
            if ruta.exists():
                return ruta
        return None

    def _buscar_musica(self, nombre_logico: str):
        """Busca primero la carpeta y el archivo mapeados en PISTAS_MUSICA y,
        si no están en el árbol activo, un archivo que se llame como la pista
        lógica dentro de musica/."""
        mapeado = PISTAS_MUSICA.get(nombre_logico)
        if mapeado is not None:
            ruta = self._buscar_archivo(*mapeado)
            if ruta is not None:
                return ruta
        return self._buscar_archivo(SUBCARPETA_MUSICA, nombre_logico)

    def establecer_volumen_musica(self, volumen: int):
        self.volumen_musica = volumen
        if self.disponible:
            pygame.mixer.music.set_volume(self._proporcion(volumen))

    def establecer_volumen_efectos(self, volumen: int):
        self.volumen_efectos = volumen
        for efecto in self._efectos_cache.values():
            if efecto is not None:
                efecto.set_volume(self._proporcion(volumen))

    def reproducir_musica(self, nombre: str, repetir: bool = True):
        """Reproduce una pista de la carpeta musica/. Si ya está sonando esa
        misma pista no la reinicia; si el archivo no existe deja el silencio
        en lugar de arrastrar la pista anterior."""
        if not self.disponible or self._pista_actual == nombre:
            return

        # Se recuerda el nombre aunque falte el archivo, para no repetir la
        # búsqueda en disco en cada fotograma mientras dure ese estado.
        self._pista_actual = nombre
        ruta = self._buscar_musica(nombre)
        if ruta is None:
            pygame.mixer.music.stop()
            return
        try:
            pygame.mixer.music.load(str(ruta))
            pygame.mixer.music.set_volume(self._proporcion(self.volumen_musica))
            pygame.mixer.music.play(-1 if repetir else 0)
        except pygame.error:
            pygame.mixer.music.stop()

    def detener_musica(self):
        if not self.disponible:
            return
        pygame.mixer.music.stop()
        self._pista_actual = None

    def _obtener_efecto(self, nombre: str, subcarpeta: str) -> Optional[pygame.mixer.Sound]:
        clave = (self.modo_streamer, subcarpeta, nombre)
        if clave not in self._efectos_cache:
            ruta = self._buscar_archivo(subcarpeta, nombre)
            try:
                self._efectos_cache[clave] = pygame.mixer.Sound(str(ruta)) if ruta else None
            except pygame.error:
                self._efectos_cache[clave] = None
        return self._efectos_cache[clave]

    def reproducir_efecto(self, nombre: str, subcarpeta: str = SUBCARPETA_EFECTOS):
        if not self.disponible:
            return
        efecto = self._obtener_efecto(nombre, subcarpeta)
        if efecto is not None:
            efecto.set_volume(self._proporcion(self.volumen_efectos))
            efecto.play()

    def reproducir_efecto_al_azar(
        self, nombres, subcarpeta: str = SUBCARPETA_EFECTOS
    ) -> Optional[str]:
        """Suena uno de esos efectos, elegido al azar entre los que de verdad
        existan en el árbol activo. Devuelve cuál sonó, o None si no había
        ninguno: así una lista de variantes puede estar completa en un árbol
        de audio e incompleta en el otro sin quedarse muda ni fallar."""
        if not self.disponible:
            return None
        disponibles = [
            nombre for nombre in nombres
            if self._obtener_efecto(nombre, subcarpeta) is not None
        ]
        if not disponibles:
            return None
        elegido = random.choice(disponibles)
        self.reproducir_efecto(elegido, subcarpeta)
        return elegido

    def duracion_efecto(
        self, nombre: str, subcarpeta: str = SUBCARPETA_EFECTOS
    ) -> Optional[float]:
        """Segundos que dura un efecto, o None si no hay dispositivo de audio
        o el archivo no existe. Sirve para sincronizar una animación con su
        sonido (el susto final con jumpscare.mp3, por ejemplo)."""
        if not self.disponible:
            return None
        efecto = self._obtener_efecto(nombre, subcarpeta)
        return efecto.get_length() if efecto is not None else None

    def reproducir_efecto_camara(self, nombre: str):
        """Sonidos del monitor de vigilancia (subcarpeta camaras/)."""
        self.reproducir_efecto(nombre, subcarpeta=SUBCARPETA_CAMARAS)

    def aplicar_modo_streamer(self, activo: bool):
        """Cambia el árbol de audio en caliente y vuelve a lanzar la pista
        actual desde la nueva carpeta, para que el cambio se note al momento."""
        if bool(activo) == self.modo_streamer:
            return
        self.modo_streamer = bool(activo)
        pista = self._pista_actual
        self.detener_musica()
        if pista is not None:
            self.reproducir_musica(pista)
