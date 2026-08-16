"""El susto final: al atrapar al jugador, el personaje responsable lanza una
ráfaga de cuadros "jump N.png" antes de que se muestre la pantalla de game
over, al estilo del género.

Los cuadros son opcionales y se detectan por carpeta: si un personaje
todavía no tiene sus "jump 1.png", "jump 2.png"... el susto no arranca y el
juego pasa directo a game over, como antes de que existiera esta pantalla.
Así se pueden ir agregando personaje por personaje sin tocar código. De
todos los que haya, solo se usan los últimos CUADROS_MAXIMOS_SUSTO (el final
del acercamiento): si un personaje trae 10, se toman el 7, 8, 9 y 10; si
trae 9, el 6, 7, 8 y 9, y así siempre con los últimos, sin importar cuántos
existan.

Cada cuadro es un retrato vertical opaco (no trae transparencia) que se
agranda más allá del alto de pantalla (SUSTO_ZOOM) y se recorta centrado
al tamaño del lienzo, para que ocupe más del escenario que si solo se
ajustara por el alto. Lo que queda expuesto son sus bordes izquierdo y
derecho sobre el fondo real de la posición donde estaba el jugador, así que
esos dos bordes se difuminan con una máscara propia para que la costura no
se note; a diferencia de quitarle el fondo por color, esto no depende de qué
tan oscura sea la ropa del personaje, así que un traje negro no se vuelve
transparente por error.

Ese fondo se oscurece con la misma penumbra que tendría en la vista normal
del jugador (posicion.oscuridad), pero sin el haz de la linterna: nadie la
tiene encendida en pleno susto. Si se viera con su brillo real delataría de
más el lugar donde perdió.

Si hay un efecto de sonido para el susto, la ráfaga completa se estira o
encoge para durar lo mismo que ese audio (ver `iniciar`).
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pygame

from ..config.interfaz import (
    SUSTO_SEGUNDOS_FRAME_FINAL,
    SUSTO_SEGUNDOS_POR_FRAME,
    SUSTO_ZOOM,
)
from ..config.rutas import DIR_ASSETS_ANIMATRONICS
from ..config.ventana import ALTO_PANTALLA, ANCHO_PANTALLA, RESOLUCION_BASE
from ..dominio.animatronicos import carpetas_de_atacantes
from ..infraestructura.recursos import CacheImagenes

PATRON_FRAMES_SUSTO = "jump *.png"
_NUMERO_EN_NOMBRE = re.compile(r"(\d+)")

# De todos los "jump N.png" que tenga un personaje, cuántos de los últimos
# se usan en la ráfaga (siempre los de mayor número, el tramo final del
# acercamiento). Si tiene menos que esto, se usan todos los que haya.
CUADROS_MAXIMOS_SUSTO = 4

# Cuántos de los últimos cuadros de la ráfaga se sostienen el tiempo largo
# (SUSTO_SEGUNDOS_FRAME_FINAL) en vez del ritmo rápido del resto, para que el
# golpe final se note y no pase en un parpadeo.
CUADROS_FINALES_SOSTENIDOS = 2

# Difuminado de los bordes izquierdo y derecho del cuadro (ya recortado al
# alto de pantalla, así que arriba y abajo no hace falta tocarlo). Fracción
# del ancho que se desvanece en cada lado y con qué curva: por debajo de 1 la
# mayor parte del margen se mantiene opaca y la caída se concentra pegada al
# borde, para no comerse al personaje.
BORDE_DIFUMINADO_FRACCION = 0.12
BORDE_DIFUMINADO_PASOS = 24
BORDE_DIFUMINADO_CAIDA = 0.5

# Alto al que se cargan los cuadros antes de recortarlos al de pantalla:
# agrandarlos de más (SUSTO_ZOOM) implica recortar más arriba y abajo.
_ALTO_CARGA = round(ALTO_PANTALLA * SUSTO_ZOOM)


def _numero_de(ruta: Path) -> int:
    coincidencia = _NUMERO_EN_NOMBRE.search(ruta.stem)
    return int(coincidencia.group(1)) if coincidencia else 0


def _mascara_borde(tamano: Tuple[int, int]) -> pygame.Surface:
    """Máscara blanca con alfa 0 en los bordes izquierdo/derecho que sube a
    255 hacia el centro. Multiplicada sobre un cuadro (BLEND_RGBA_MULT) deja
    su color intacto y solo recorta su alfa, así que un personaje vestido de
    negro no se confunde con un borde que hay que desvanecer."""
    ancho, alto = tamano
    mascara = pygame.Surface(tamano, pygame.SRCALPHA)
    margen = ancho * BORDE_DIFUMINADO_FRACCION
    for paso in range(1, BORDE_DIFUMINADO_PASOS + 1):
        proporcion = paso / BORDE_DIFUMINADO_PASOS
        alfa = int(255 * proporcion ** BORDE_DIFUMINADO_CAIDA)
        inset = int(margen * proporcion)
        ancho_rect = max(0, ancho - 2 * inset)
        pygame.draw.rect(mascara, (255, 255, 255, alfa), (inset, 0, ancho_rect, alto))
    return mascara


class Susto:
    """Reproduce, cuadro a cuadro, el susto del personaje que atrapó al
    jugador, sobre el fondo de la posición donde estaba parado."""

    def __init__(self):
        self._carpetas: Dict[str, str] = carpetas_de_atacantes()
        self._arte = CacheImagenes(alto=_ALTO_CARGA)
        self._fondos = CacheImagenes(con_alfa=True, tamano=RESOLUCION_BASE)
        self._mascaras: Dict[Tuple[int, int], pygame.Surface] = {}
        self._frames: List[pygame.Surface] = []
        self._duraciones: List[float] = []
        self._fondo: Optional[pygame.Surface] = None
        self._indice = 0
        self._restante = 0.0
        self.activo = False
        self.termino = False

    def _recortado_y_difuminado(self, base: pygame.Surface) -> pygame.Surface:
        """Recorta al alto de pantalla (centrado verticalmente) y difumina
        sus bordes izquierdo/derecho. Devuelve siempre una superficie nueva:
        no toca la que queda cacheada en self._arte."""
        ancho, alto_cargado = base.get_size()
        y0 = max(0, (alto_cargado - ALTO_PANTALLA) // 2)
        alto_recorte = min(ALTO_PANTALLA, alto_cargado)
        recorte = pygame.Rect(0, y0, ancho, alto_recorte)
        cuadro = base.subsurface(recorte).convert_alpha()

        tamano = cuadro.get_size()
        if tamano not in self._mascaras:
            self._mascaras[tamano] = _mascara_borde(tamano)
        cuadro.blit(self._mascaras[tamano], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        return cuadro

    def _fondo_oscurecido(self, fondo: pygame.Surface, nivel: int) -> pygame.Surface:
        """Copia del fondo con la misma penumbra que la vista normal del
        jugador, sin haz de linterna. Se calcula una sola vez al iniciar, no
        por fotograma."""
        oscurecido = fondo.copy()
        velo = pygame.Surface(oscurecido.get_size(), pygame.SRCALPHA)
        velo.fill((0, 0, 0, nivel))
        oscurecido.blit(velo, (0, 0))
        return oscurecido

    def _frames_de(self, nombre_atacante: str) -> List[pygame.Surface]:
        carpeta = self._carpetas.get(nombre_atacante)
        if carpeta is None:
            return []
        rutas = sorted(
            (DIR_ASSETS_ANIMATRONICS / carpeta).glob(PATRON_FRAMES_SUSTO),
            key=_numero_de,
        )[-CUADROS_MAXIMOS_SUSTO:]
        frames = []
        for ruta in rutas:
            base = self._arte.obtener(str(ruta), ruta)
            if base is not None:
                frames.append(self._recortado_y_difuminado(base))
        return frames

    def _duracion_natural(self, indice: int, total: int) -> float:
        """Ritmo antes de ajustarlo a la duración del audio: los últimos
        CUADROS_FINALES_SOSTENIDOS cuadros se quedan en pantalla más tiempo
        que el resto, para que el acercamiento final se alcance a ver en vez
        de solo destellar."""
        if indice >= total - CUADROS_FINALES_SOSTENIDOS:
            return SUSTO_SEGUNDOS_FRAME_FINAL
        return SUSTO_SEGUNDOS_POR_FRAME

    def _calcular_duraciones(self, duracion_audio: Optional[float]) -> List[float]:
        total = len(self._frames)
        base = [self._duracion_natural(indice, total) for indice in range(total)]
        if not duracion_audio or duracion_audio <= 0.0:
            return base
        factor = duracion_audio / sum(base)
        return [duracion * factor for duracion in base]

    def iniciar(self, nombre_atacante: str, posicion, duracion_audio: Optional[float] = None) -> bool:
        """Arranca el susto de ese personaje sobre el fondo de `posicion`
        (la que ocupaba el jugador al perder). Si se indica `duracion_audio`
        (los segundos que dura el efecto de sonido del susto), toda la
        ráfaga se reparte para durar exactamente eso; si no, usa su ritmo
        natural. Devuelve False sin hacer nada más si el personaje todavía
        no tiene cuadros, para que quien llama decida pasar directo a game
        over."""
        self._frames = self._frames_de(nombre_atacante)
        self.activo = bool(self._frames)
        self.termino = False
        if not self.activo:
            return False
        fondo = self._fondos.obtener(posicion.id, posicion.ruta_fondo)
        self._fondo = (
            self._fondo_oscurecido(fondo, posicion.oscuridad) if fondo is not None else None
        )
        self._duraciones = self._calcular_duraciones(duracion_audio)
        self._indice = 0
        self._restante = self._duraciones[0]
        return True

    def actualizar(self, dt: float):
        if not self.activo:
            return
        self._restante -= dt
        if self._restante > 0.0:
            return
        if self._indice >= len(self._frames) - 1:
            self.activo = False
            self.termino = True
            return
        self._indice += 1
        self._restante = self._duraciones[self._indice]

    def dibujar(self, superficie: pygame.Surface):
        if self._fondo is not None:
            superficie.blit(self._fondo, (0, 0))
        else:
            superficie.fill((0, 0, 0))
        if not self._frames:
            return
        frame = self._frames[self._indice]
        superficie.blit(
            frame, frame.get_rect(center=(ANCHO_PANTALLA // 2, ALTO_PANTALLA // 2))
        )
