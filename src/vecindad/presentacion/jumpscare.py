"""El susto final: al atrapar al jugador, el personaje responsable se le echa
encima antes de que se muestre la pantalla de game over, al estilo del
género.

Tiene dos tiempos, y dura lo mismo que el efecto de sonido del susto:

1. El acercamiento: sus cuadros "jump N.png" pasan cada vez más deprisa,
   la cámara se va cerrando, tiembla y la luz parpadea.
2. El golpe: entra el último cuadro con un zoom brusco que se asienta, un
   temblor fuerte, un destello blanco muy corto y un velo rojo. La cara se
   queda encima y todo termina tapado por la estática.

Los cuadros se detectan por carpeta y, por defecto, se usan todos sus
"jump N.png" en orden. Una carpeta con receta en SUSTOS_COMPUESTOS
(config/interfaz.py) arma el susto distinto en cada muerte: sortea uno de
sus acercamientos, que salen de recortar una hoja de propuesta (una
cuadrícula de cuadros), y uno de sus "jump" como golpe. Los "jump"
horizontales ya son una pantalla entera y se muestran así, sin recortar.

Quien todavía no tiene los suyos se acerca con un primer plano de su sprite normal (cabeza
y pecho), que crece desde lejos hasta llenar la pantalla: así nadie se queda
sin susto mientras el arte está en producción, y en cuanto aparecen sus
"jump N.png" se usan sin tocar código.

Cada cuadro es un retrato vertical que se agranda más allá del alto de
pantalla (SUSTO_ZOOM) y se recorta al tamaño del lienzo. Sus bordes
izquierdo y derecho quedan sobre el fondo real de la posición donde estaba
el jugador, así que se difuminan con una máscara propia para que la costura
no se note; a diferencia de quitarle el fondo por color, esto no depende de
qué tan oscura sea la ropa del personaje.

Ese fondo se oscurece con la misma penumbra que tendría en la vista normal
del jugador (posicion.oscuridad), pero sin el haz de la linterna: nadie la
tiene encendida en pleno susto.

El guion (qué cuadro toca, cuánto zoom, cuánto temblor...) vive en
GuionSusto y es pura aritmética sobre el tiempo, para poder probarlo sin
abrir una ventana; Susto solo lo dibuja.
"""

import math
import random
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pygame

from ..config.interfaz import (
    ACERCAMIENTO_CON_JUMPS,
    SUSTO_DESTELLO_OPACIDAD,
    SUSTO_DESTELLO_SEGUNDOS,
    SUSTO_DURACION_NATURAL,
    SUSTO_ESTATICA_CIERRE_SEGUNDOS,
    SUSTO_ESTATICA_FONDO,
    SUSTO_ESTATICA_GOLPE,
    SUSTO_PARPADEO_OPACIDAD,
    SUSTO_PARPADEO_PROBABILIDAD,
    SUSTO_PROPORCION_CARA_SIN_CUADROS,
    SUSTO_PROPORCION_GOLPE,
    SUSTO_TEMBLOR_ACERCAMIENTO,
    SUSTO_TEMBLOR_FONDO,
    SUSTO_TEMBLOR_GOLPE,
    SUSTO_VELO_COLOR,
    SUSTO_VELO_OPACIDAD,
    SUSTO_VINETA_OPACIDAD,
    SUSTO_ZOOM,
    SUSTO_ZOOM_ACERCAMIENTO,
    SUSTO_ZOOM_GOLPE,
    SUSTO_ZOOM_INICIAL_SIN_CUADROS,
    SUSTO_ZOOM_PROPUESTA,
    SUSTO_ZOOM_REPOSO,
    SUSTOS_COMPUESTOS,
)
from ..config.rutas import DIR_ASSETS_ANIMATRONICS
from ..config.ventana import ALTO_PANTALLA, ANCHO_PANTALLA, RESOLUCION_BASE
from ..dominio.animatronicos import ELENCO, carpetas_de_atacantes
from ..infraestructura.recursos import CacheImagenes, cargar_imagen
from .efectos import generar_frame_estatica

PATRON_FRAMES_SUSTO = "jump *.png"
_NUMERO_EN_NOMBRE = re.compile(r"(\d+)")

# Forma de las curvas del guion. Los valores que se ajustan a ojo están en
# config/interfaz.py; estos solo dicen cómo de rápido cae cada efecto.
ACELERACION_CUADROS = 1.6   # >1: los primeros cuadros duran más que los últimos
CAIDA_ZOOM_GOLPE = 14.0     # qué tan rápido se asienta el zoom del golpe
VAIVEN_ZOOM = 0.015         # leve respiración de la cara ya encima
VAIVEN_ZOOM_VELOCIDAD = 9.0
CAIDA_TEMBLOR_GOLPE = 5.0
CAIDA_VELO = 2.5
CAIDA_ESTATICA_GOLPE = 10.0
SUBIDA_ESTATICA_CIERRE = 0.2  # segundos que tarda la estática final en tapar todo

# Difuminado de los bordes izquierdo y derecho del cuadro (ya recortado al
# alto de pantalla, así que arriba y abajo no hace falta tocarlo). Fracción
# del ancho que se desvanece en cada lado y con qué curva: por debajo de 1 la
# mayor parte del margen se mantiene opaca y la caída se concentra pegada al
# borde, para no comerse al personaje.
BORDE_DIFUMINADO_FRACCION = 0.12
BORDE_DIFUMINADO_PASOS = 24
BORDE_DIFUMINADO_CAIDA = 0.5

# La viñeta y la estática se precalculan a baja resolución y se escalan una
# sola vez al crear el susto.
VINETA_RESOLUCION = (64, 36)

# Desde qué opacidad un píxel de un sprite cuenta como parte de la figura al
# buscar dónde empieza la cabeza (el resto es el margen transparente).
ALFA_MINIMO_FIGURA = 40

# Recorte de las hojas de propuesta: colores que puede tener un separador
# (con cuánto se puede alejar cada canal de ese color), qué parte de la línea
# tiene que ser de ese color, tamaño mínimo de un cuadro y margen que se le
# quita a cada uno junto al separador.
COLORES_SEPARADOR = (((255, 255, 255), 56), ((0, 0, 0), 26))
PROPORCION_SEPARADOR = 0.97
ANCHO_MINIMO_CUADRO = 20
MARGEN_SEPARADOR = 2

# Paso de tiempo máximo que avanza el susto en un fotograma (ver actualizar).
DT_MAXIMO = 1.0 / 30.0
VINETA_CURVA = 2.2
ESTATICA_CUADROS = 6

# Alto al que se cargan los cuadros antes de recortarlos al de pantalla:
# agrandarlos de más (SUSTO_ZOOM) implica recortar más arriba y abajo.
_ALTO_CARGA = round(ALTO_PANTALLA * SUSTO_ZOOM)


def _numero_de(ruta: Path) -> int:
    coincidencia = _NUMERO_EN_NOMBRE.search(ruta.stem)
    return int(coincidencia.group(1)) if coincidencia else 0


class GuionSusto:
    """Qué pasa en cada instante del susto. Solo cuentas sobre el tiempo:
    no dibuja ni sabe nada de pygame."""

    def __init__(self, cuadros: int, duracion: float, tiene_cuadros_propios: bool = True):
        self.cuadros = cuadros
        self.duracion = duracion
        self.golpe = duracion * SUSTO_PROPORCION_GOLPE
        # Sin cuadros de acercamiento, el sprite tiene que venir desde lejos.
        self._zoom_inicial = 1.0 if tiene_cuadros_propios else SUSTO_ZOOM_INICIAL_SIN_CUADROS

    def llego(self, t: float) -> bool:
        return t >= self.golpe

    def _avance(self, t: float) -> float:
        """De 0 al empezar a 1 al llegar el golpe."""
        return min(1.0, max(0.0, t / self.golpe)) if self.golpe > 0 else 1.0

    def indice_cuadro(self, t: float) -> int:
        """El último es el del golpe; los anteriores se reparten el
        acercamiento cada vez más deprisa."""
        if self.llego(t) or self.cuadros <= 1:
            return self.cuadros - 1
        avance = self._avance(t) ** ACELERACION_CUADROS
        return min(self.cuadros - 2, int(avance * (self.cuadros - 1)))

    def zoom(self, t: float) -> float:
        if not self.llego(t):
            final = 1.0 + SUSTO_ZOOM_ACERCAMIENTO
            return self._zoom_inicial + (final - self._zoom_inicial) * self._avance(t) ** 2
        desde = t - self.golpe
        golpe = SUSTO_ZOOM_REPOSO + SUSTO_ZOOM_GOLPE * math.exp(-desde * CAIDA_ZOOM_GOLPE)
        return golpe + VAIVEN_ZOOM * math.sin(desde * VAIVEN_ZOOM_VELOCIDAD)

    def temblor(self, t: float) -> float:
        """Amplitud del temblor en píxeles."""
        if not self.llego(t):
            return SUSTO_TEMBLOR_FONDO / 2 + SUSTO_TEMBLOR_ACERCAMIENTO * self._avance(t) ** 2
        caida = math.exp(-(t - self.golpe) * CAIDA_TEMBLOR_GOLPE)
        return SUSTO_TEMBLOR_FONDO + SUSTO_TEMBLOR_GOLPE * caida

    def destello(self, t: float) -> int:
        if not self.llego(t):
            return 0
        restante = 1.0 - (t - self.golpe) / SUSTO_DESTELLO_SEGUNDOS
        return int(SUSTO_DESTELLO_OPACIDAD * max(0.0, restante))

    def velo(self, t: float) -> int:
        if not self.llego(t):
            return 0
        return int(SUSTO_VELO_OPACIDAD * math.exp(-(t - self.golpe) * CAIDA_VELO))

    def estatica(self, t: float) -> int:
        cierre = self.duracion - SUSTO_ESTATICA_CIERRE_SEGUNDOS
        if t > cierre:
            return int(255 * min(1.0, (t - cierre) / SUBIDA_ESTATICA_CIERRE))
        if not self.llego(t):
            return SUSTO_ESTATICA_FONDO
        golpe = SUSTO_ESTATICA_GOLPE * math.exp(-(t - self.golpe) * CAIDA_ESTATICA_GOLPE)
        return max(SUSTO_ESTATICA_FONDO, int(golpe))

    def parpadea(self, t: float) -> bool:
        """Si la luz puede fallar en este instante: solo mientras se acerca."""
        return not self.llego(t)


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


def _tramos(es_separador, total: int) -> List[Tuple[int, int]]:
    """Los tramos [inicio, fin) entre separadores, sin los demasiado finos
    para ser un cuadro (el antialias pegado a un separador, por ejemplo)."""
    tramos, inicio = [], 0
    for i in range(total + 1):
        if i == total or es_separador(i):
            if i - inicio >= ANCHO_MINIMO_CUADRO:
                tramos.append((inicio, i))
            inicio = i + 1
    return tramos


def _es_separador(hoja: pygame.Surface, rect: pygame.Rect) -> bool:
    """Si esa línea entera de la hoja es separador: casi todos sus píxeles
    son blanco puro o negro puro. Se mira la proporción y no el color medio
    porque una columna de una escena de noche puede ser oscura en promedio
    sin ser negra de punta a punta. Las máscaras de pygame lo cuentan en C."""
    linea = hoja.subsurface(rect)
    minimo = rect.width * rect.height * PROPORCION_SEPARADOR
    return any(
        pygame.mask.from_threshold(linea, color, (tolerancia,) * 3 + (255,)).count() >= minimo
        for color, tolerancia in COLORES_SEPARADOR
    )


def cuadros_de_hoja(hoja: pygame.Surface) -> List[pygame.Rect]:
    """Dónde está cada cuadro de una hoja de propuesta, en orden de lectura:
    de izquierda a derecha y de arriba abajo.

    Los separadores son columnas y filas enteras blancas o negras (ver
    _es_separador). A cada cuadro se le quita un margen para no arrastrar el
    antialias del separador."""
    ancho, alto = hoja.get_size()
    columnas = _tramos(lambda x: _es_separador(hoja, pygame.Rect(x, 0, 1, alto)), ancho)
    filas = _tramos(lambda y: _es_separador(hoja, pygame.Rect(0, y, ancho, 1)), alto)
    margen = MARGEN_SEPARADOR
    return [
        pygame.Rect(x0 + margen, y0 + margen, x1 - x0 - 2 * margen, y1 - y0 - 2 * margen)
        for y0, y1 in filas
        for x0, x1 in columnas
    ]


def _recortado(rect: pygame.Rect, recorte) -> pygame.Rect:
    """`rect` menos esos píxeles por (izquierda, arriba, derecha, abajo)."""
    izquierda, arriba, derecha, abajo = recorte
    return pygame.Rect(
        rect.x + izquierda,
        rect.y + arriba,
        max(1, rect.width - izquierda - derecha),
        max(1, rect.height - arriba - abajo),
    )


def _escalado_al_alto(imagen: pygame.Surface, alto: int) -> pygame.Surface:
    escala = alto / imagen.get_height()
    return pygame.transform.smoothscale(imagen, (round(imagen.get_width() * escala), alto))


def _cubriendo_la_pantalla(imagen: pygame.Surface) -> pygame.Surface:
    """Escalada lo justo para cubrir el lienzo entero sin deformarse."""
    ancho, alto = imagen.get_size()
    escala = max(ANCHO_PANTALLA / ancho, ALTO_PANTALLA / alto)
    return pygame.transform.smoothscale(
        imagen, (round(ancho * escala), round(alto * escala))
    ).convert_alpha()


def _vineta() -> pygame.Surface:
    """Bordes oscuros y centro limpio. Se calcula a baja resolución píxel a
    píxel (unos pocos miles) y se escala una sola vez."""
    ancho, alto = VINETA_RESOLUCION
    chica = pygame.Surface(VINETA_RESOLUCION, pygame.SRCALPHA)
    for y in range(alto):
        for x in range(ancho):
            dx = (x + 0.5) / ancho * 2 - 1
            dy = (y + 0.5) / alto * 2 - 1
            distancia = min(1.0, math.hypot(dx, dy) / math.sqrt(2))
            chica.set_at((x, y), (0, 0, 0, int(SUSTO_VINETA_OPACIDAD * distancia ** VINETA_CURVA)))
    return pygame.transform.smoothscale(chica, RESOLUCION_BASE)


def _capa_de_color(color) -> pygame.Surface:
    capa = pygame.Surface(RESOLUCION_BASE)
    capa.fill(color)
    return capa


class Susto:
    """Dibuja el susto del personaje que atrapó al jugador, sobre el fondo de
    la posición donde estaba parado."""

    def __init__(self):
        self._carpetas: Dict[str, str] = carpetas_de_atacantes()
        self._sprites = {config.nombre: config.ruta_pose(1) for config in ELENCO}
        # Cuadros ya listos para dibujar (por ruta) y hojas de propuesta ya
        # recortadas. Los originales no se guardan: son enormes y solo hacen
        # falta para prepararlos una vez.
        self._preparados: Dict[str, Optional[pygame.Surface]] = {}
        self._hojas: Dict[str, List[pygame.Surface]] = {}
        self._fondos = CacheImagenes(con_alfa=True, tamano=RESOLUCION_BASE)
        self._mascaras: Dict[Tuple[int, int], pygame.Surface] = {}
        # Capas fijas de los efectos: se hacen una vez y en cada fotograma
        # solo se les cambia la opacidad.
        self._vineta = _vineta()
        self._estatica = [
            generar_frame_estatica(
                (ANCHO_PANTALLA // 4, ALTO_PANTALLA // 4), RESOLUCION_BASE, 255
            )
            for _ in range(ESTATICA_CUADROS)
        ]
        self._blanco = _capa_de_color((255, 255, 255))
        self._velo = _capa_de_color(SUSTO_VELO_COLOR)
        self._sombra = _capa_de_color((0, 0, 0))
        self._azar = random.Random()

        self._frames: List[pygame.Surface] = []
        self._guion: Optional[GuionSusto] = None
        self._fondo: Optional[pygame.Surface] = None
        self._t = 0.0
        self._fotograma = 0
        self.activo = False
        self.termino = False

    def _recortado_y_difuminado(self, base: pygame.Surface) -> pygame.Surface:
        """Recorta al alto de pantalla (centrado verticalmente) y difumina
        sus bordes izquierdo y derecho. Devuelve siempre una superficie
        nueva: no toca la que queda cacheada."""
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

    # ------------------------------------------------------------------
    # Preparación de los cuadros. Cada uno se prepara una sola vez, la
    # primera vez que hace falta, y se guarda ya listo para dibujar.
    # ------------------------------------------------------------------
    def _preparado(self, clave: str, preparar) -> Optional[pygame.Surface]:
        if clave not in self._preparados:
            self._preparados[clave] = preparar()
        return self._preparados[clave]

    def _listo_para_dibujar(self, imagen: pygame.Surface, alto_vertical: int) -> pygame.Surface:
        """Los cuadros horizontales ya son una pantalla entera y se ajustan a
        cubrirla. Los verticales se agrandan a `alto_vertical` y se recortan
        con los bordes difuminados, sobre el fondo de la posición."""
        if imagen.get_width() > imagen.get_height():
            return _cubriendo_la_pantalla(imagen)
        return self._recortado_y_difuminado(_escalado_al_alto(imagen, alto_vertical))

    def _cuadro_de(self, ruta: Path) -> Optional[pygame.Surface]:
        """Un "jump N.png" listo para dibujar."""
        def preparar():
            base = cargar_imagen(ruta)
            return None if base is None else self._listo_para_dibujar(base, _ALTO_CARGA)

        return self._preparado(str(ruta), preparar)

    def _cuadros_de_hoja(self, ruta: Path, recorte=(0, 0, 0, 0)) -> List[pygame.Surface]:
        """Todos los cuadros de una hoja de propuesta, en orden de lectura,
        quitándole a cada uno `recorte` píxeles por (izquierda, arriba,
        derecha, abajo)."""
        clave = f"{ruta}:{recorte}"
        if clave not in self._hojas:
            hoja = cargar_imagen(ruta)
            alto = round(ALTO_PANTALLA * SUSTO_ZOOM_PROPUESTA)
            self._hojas[clave] = [] if hoja is None else [
                self._listo_para_dibujar(hoja.subsurface(_recortado(rect, recorte)), alto)
                for rect in cuadros_de_hoja(hoja)
            ]
        return self._hojas[clave]

    def _acercamiento(self, directorio: Path, origen: str, numeros, receta) -> List[pygame.Surface]:
        """Los cuadros de uno de los acercamientos de la receta: de una hoja
        de propuesta o de los "jump N.png" sueltos."""
        if origen == ACERCAMIENTO_CON_JUMPS:
            cuadros = (self._cuadro_de(directorio / f"jump {n}.png") for n in numeros)
            return [c for c in cuadros if c is not None]
        ruta = directorio / origen
        if not ruta.exists():
            return []
        recorte = receta.get("recortes", {}).get(origen, (0, 0, 0, 0))
        return self._elegidos(self._cuadros_de_hoja(ruta, recorte), numeros)

    def _sprite_de(self, nombre_atacante: str) -> List[pygame.Surface]:
        """Un primer plano de su sprite normal como único cuadro, para quien
        no tiene susto propio todavía: la parte de arriba de la figura (sin
        el margen transparente del archivo), ampliada al alto de pantalla."""
        ruta = self._sprites.get(nombre_atacante)
        if ruta is None:
            return []

        def preparar():
            base = cargar_imagen(ruta, con_alfa=True)
            if base is None:
                return None
            figura = base.get_bounding_rect(min_alpha=ALFA_MINIMO_FIGURA)
            if figura.width == 0 or figura.height == 0:
                return None
            figura.height = max(1, int(figura.height * SUSTO_PROPORCION_CARA_SIN_CUADROS))
            cara = _escalado_al_alto(base.subsurface(figura), ALTO_PANTALLA)
            return self._recortado_y_difuminado(cara)

        cuadro = self._preparado(f"sprite:{ruta}", preparar)
        return [] if cuadro is None else [cuadro]

    # ------------------------------------------------------------------
    # Qué cuadros salen en este susto
    # ------------------------------------------------------------------
    def _cuadros_para(self, nombre_atacante: str) -> List[pygame.Surface]:
        """Los cuadros de este susto en concreto, el golpe al final.

        Por defecto son todos sus "jump N.png" en orden. Si su carpeta tiene
        receta en SUSTOS_COMPUESTOS, se sortea uno de sus acercamientos y uno
        de sus golpes, así que cada muerte puede verse distinta."""
        carpeta = self._carpetas.get(nombre_atacante)
        if carpeta is None:
            return []
        directorio = DIR_ASSETS_ANIMATRONICS / carpeta
        saltos = sorted(directorio.glob(PATRON_FRAMES_SUSTO), key=_numero_de)
        receta = SUSTOS_COMPUESTOS.get(carpeta)
        if receta is None:
            return [c for c in map(self._cuadro_de, saltos) if c is not None]

        acercamientos = [
            self._acercamiento(directorio, origen, numeros, receta)
            for origen, numeros in receta["acercamientos"].items()
        ]
        acercamientos = [cuadros for cuadros in acercamientos if cuadros]
        acercamiento = self._azar.choice(acercamientos) if acercamientos else []

        permitidos = receta["golpes"]
        golpes = [r for r in saltos if permitidos is None or _numero_de(r) in permitidos]
        golpe = self._cuadro_de(self._azar.choice(golpes)) if golpes else None
        return acercamiento + ([golpe] if golpe is not None else [])

    @staticmethod
    def _elegidos(cuadros: List[pygame.Surface], numeros) -> List[pygame.Surface]:
        """Los cuadros con esos números (desde 1). Los que la hoja no tenga
        se ignoran, para que una hoja con menos cuadros no rompa el susto."""
        return [cuadros[n - 1] for n in numeros if 1 <= n <= len(cuadros)]

    def iniciar(self, nombre_atacante: str, posicion, duracion_audio: Optional[float] = None) -> bool:
        """Arranca el susto de ese personaje sobre el fondo de `posicion`
        (la que ocupaba el jugador al perder). Si se indica `duracion_audio`
        (los segundos que dura el efecto de sonido del susto), dura eso; si
        no, SUSTO_DURACION_NATURAL. Devuelve False sin hacer nada más si no
        hay ni cuadros ni sprite que enseñar, para que quien llama pase
        directo a game over."""
        self._frames = self._cuadros_para(nombre_atacante) or self._sprite_de(nombre_atacante)
        self.activo = bool(self._frames)
        self.termino = False
        if not self.activo:
            return False
        fondo = self._fondos.obtener(posicion.id, posicion.ruta_fondo)
        self._fondo = (
            self._fondo_oscurecido(fondo, posicion.oscuridad) if fondo is not None else None
        )
        duracion = duracion_audio if duracion_audio and duracion_audio > 0.0 else SUSTO_DURACION_NATURAL
        # Con un solo cuadro no hay acercamiento dibujado: lo hace el zoom.
        self._guion = GuionSusto(len(self._frames), duracion, len(self._frames) > 1)
        self._t = 0.0
        self._fotograma = 0
        return True

    def actualizar(self, dt: float):
        if not self.activo:
            return
        # Preparar los cuadros la primera vez puede tardar un fotograma
        # largo; sin este tope, ese salto se comería el principio del susto.
        self._t += min(dt, DT_MAXIMO)
        self._fotograma += 1
        if self._t >= self._guion.duracion:
            self.activo = False
            self.termino = True

    def dibujar(self, superficie: pygame.Surface):
        superficie.fill((0, 0, 0))
        if not self._frames or self._guion is None:
            return
        guion, t = self._guion, self._t
        amplitud = guion.temblor(t)
        dx = self._azar.uniform(-amplitud, amplitud)
        dy = self._azar.uniform(-amplitud, amplitud)

        if self._fondo is not None:
            superficie.blit(self._fondo, (dx, dy))

        # Se escala solo la figura, no la escena entera: es más barato y el
        # fondo está casi a oscuras de todas formas. Es la única superficie
        # nueva por fotograma, y solo mientras dura el susto.
        frame = self._frames[guion.indice_cuadro(t)]
        zoom = guion.zoom(t)
        tamano = (round(frame.get_width() * zoom), round(frame.get_height() * zoom))
        ampliado = pygame.transform.smoothscale(frame, tamano)
        centro = (ANCHO_PANTALLA // 2 + dx, ALTO_PANTALLA // 2 + dy)
        superficie.blit(ampliado, ampliado.get_rect(center=centro))

        if guion.parpadea(t) and self._azar.random() < SUSTO_PARPADEO_PROBABILIDAD:
            self._sombra.set_alpha(self._azar.randint(*SUSTO_PARPADEO_OPACIDAD))
            superficie.blit(self._sombra, (0, 0))
        self._capa(superficie, self._blanco, guion.destello(t))
        self._capa(superficie, self._velo, guion.velo(t))
        superficie.blit(self._vineta, (0, 0))
        estatica = self._estatica[self._fotograma % len(self._estatica)]
        self._capa(superficie, estatica, guion.estatica(t))

    @staticmethod
    def _capa(superficie, capa: pygame.Surface, opacidad: int):
        if opacidad <= 0:
            return
        capa.set_alpha(opacidad)
        superficie.blit(capa, (0, 0))
