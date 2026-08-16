"""Efectos visuales reutilizables: ruido de estática y líneas de barrido.

Los dos se precalculan al iniciar y después solo se blitean, así el coste de
trabajar píxel a píxel ocurre una sola vez y no en cada fotograma. Los usan
tanto el menú principal como el panel de cámaras.
"""

import random
from typing import List, Tuple

import pygame


def generar_frame_estatica(tamano_ruido: Tuple[int, int], tamano_destino: Tuple[int, int],
                           opacidad: int) -> pygame.Surface:
    """Un cuadro de ruido translúcido en escala de grises.

    El buffer de píxeles se arma con slicing de bytearray (resuelto en C, no
    con un bucle Python por píxel) y se genera a baja resolución para
    escalarlo después.
    """
    ancho, alto = tamano_ruido
    total = ancho * alto
    grises = random.randbytes(total)
    pixeles = bytearray(total * 4)
    pixeles[0::4] = grises
    pixeles[1::4] = grises
    pixeles[2::4] = grises
    pixeles[3::4] = bytes((opacidad,)) * total
    frame = pygame.image.frombuffer(bytes(pixeles), (ancho, alto), "RGBA").convert_alpha()
    return pygame.transform.scale(frame, tamano_destino)


def generar_frames_estatica(cantidad: int, tamano_ruido: Tuple[int, int],
                            tamano_destino: Tuple[int, int],
                            opacidad: int) -> List[pygame.Surface]:
    """Varios cuadros de ruido para poder alternarlos y que la estática se
    vea en movimiento."""
    return [
        generar_frame_estatica(tamano_ruido, tamano_destino, opacidad)
        for _ in range(cantidad)
    ]


def crear_lineas_barrido(tamano: Tuple[int, int], separacion: int,
                         opacidad: int) -> pygame.Surface:
    """Rejilla de líneas horizontales oscuras, como las de un monitor viejo."""
    ancho, alto = tamano
    lineas = pygame.Surface(tamano, pygame.SRCALPHA)
    for y in range(0, alto, separacion):
        pygame.draw.line(lineas, (0, 0, 0, opacidad), (0, y), (ancho, y))
    return lineas
