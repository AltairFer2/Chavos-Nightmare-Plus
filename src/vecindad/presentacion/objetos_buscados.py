"""Cómo se ven en el monitor la escoba y el café que hay que encontrar.

El arte vive en assets/ui/<id del objeto>.png. Se oscurece un poco al
cargarlo para que no brille sobre unas cámaras que son casi todas penumbra:
hay que buscarlo, no que salte a la vista.
"""

from typing import Dict, Iterable, Optional, Tuple

import pygame

from ..config.interfaz import OBJETO_BUSCADO_ALTO, OBJETO_BUSCADO_BRILLO
from ..config.rutas import DIR_ASSETS_UI
from ..infraestructura.recursos import CacheImagenes

EXTENSION = ".png"


def _apagar(imagen: pygame.Surface) -> pygame.Surface:
    apagada = imagen.copy()
    brillo = (OBJETO_BUSCADO_BRILLO,) * 3
    apagada.fill(brillo, special_flags=pygame.BLEND_RGB_MULT)
    return apagada


class ImagenesObjetosBuscados:
    """Carga cada objeto una sola vez, ya escalado y apagado."""

    def __init__(self):
        self._caches: Dict[str, CacheImagenes] = {
            id_objeto: CacheImagenes(con_alfa=True, alto=alto, transformacion=_apagar)
            for id_objeto, alto in OBJETO_BUSCADO_ALTO.items()
        }

    def obtener(self, id_objeto: str) -> Optional[pygame.Surface]:
        cache = self._caches.get(id_objeto)
        if cache is None:
            return None
        return cache.obtener(id_objeto, DIR_ASSETS_UI / f"{id_objeto}{EXTENSION}")

    def dibujar(self, superficie: pygame.Surface,
                objetos: Iterable[Tuple[str, Tuple[int, int]]],
                desplazamiento=(0, 0)):
        """`objetos` son pares (id del objeto, centro en el monitor). Se
        corren con la imagen de la cámara, que tiembla con El Chavo."""
        dx, dy = desplazamiento
        for id_objeto, (x, y) in objetos:
            imagen = self.obtener(id_objeto)
            if imagen is not None:
                superficie.blit(imagen, imagen.get_rect(center=(x + dx, y + dy)))
