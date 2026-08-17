"""Efectos visuales reutilizables: ruido de estática, líneas de barrido y
confeti.

La estática y las líneas de barrido se precalculan al iniciar y después solo
se blitean, así el coste de trabajar píxel a píxel ocurre una sola vez y no
en cada fotograma. Los usa tanto el menú principal como el panel de cámaras.

El confeti es distinto: son pocas partículas y baratas de dibujar (un
segmento de línea cada una), así que se actualizan y redibujan fotograma a
fotograma en vez de precalcularse. Lo usa el menú de noche superada.
"""

import math
import random
from dataclasses import dataclass
from typing import List, Sequence, Tuple

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


@dataclass
class Confeti:
    """Una tira de serpentina cayendo: un segmento de línea que gira sobre su
    propio centro mientras se balancea de lado a lado."""

    x: float
    y: float
    largo: float
    angulo: float
    velocidad_angular: float
    velocidad_caida: float
    fase_balanceo: float
    color: Tuple[int, int, int]


def generar_confeti(
    cantidad: int, ancho: int, alto: int, colores: Sequence[Tuple[int, int, int]],
    largo_minimo: int, largo_maximo: int,
    caida_minima: float, caida_maxima: float, giro_maximo: float,
) -> List[Confeti]:
    """Reparte las tiras por encima de la pantalla (y por dentro también, ya
    a distintas alturas) para que no arranquen todas alineadas arriba."""
    return [
        Confeti(
            x=random.uniform(0, ancho),
            y=random.uniform(-alto, alto),
            largo=random.uniform(largo_minimo, largo_maximo),
            angulo=random.uniform(0, 360),
            velocidad_angular=random.uniform(-giro_maximo, giro_maximo),
            velocidad_caida=random.uniform(caida_minima, caida_maxima),
            fase_balanceo=random.uniform(0, math.tau),
            color=random.choice(colores),
        )
        for _ in range(cantidad)
    ]


def actualizar_confeti(
    particulas: Sequence[Confeti], dt: float, ancho: int, alto: int, amplitud_balanceo: float,
):
    """Cae, gira y se balancea; al salir por abajo vuelve a aparecer arriba,
    así el número de tiras en pantalla no cambia con el tiempo."""
    for particula in particulas:
        particula.fase_balanceo += dt * 2.0
        particula.x += math.sin(particula.fase_balanceo) * amplitud_balanceo * dt
        particula.y += particula.velocidad_caida * dt
        particula.angulo += particula.velocidad_angular * dt
        if particula.y - particula.largo > alto:
            particula.y = -particula.largo
            particula.x = random.uniform(0, ancho)


def dibujar_confeti(superficie: pygame.Surface, particulas: Sequence[Confeti], grosor: int):
    for particula in particulas:
        radianes = math.radians(particula.angulo)
        mitad_x = math.cos(radianes) * particula.largo / 2
        mitad_y = math.sin(radianes) * particula.largo / 2
        inicio = (particula.x - mitad_x, particula.y - mitad_y)
        fin = (particula.x + mitad_x, particula.y + mitad_y)
        pygame.draw.line(superficie, particula.color, inicio, fin, grosor)
