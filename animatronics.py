"""Animatrónicos: el elenco de la vecindad avanzando por su recorrido hasta
llegar al Primer Patio, donde está el jugador.

Sistema de IA (escala 0-20, estilo FNAF)
---------------------------------------
En cada tick que dispara el TemporizadorNoche, cada animatrónico tira
random.randint(1, 20) y avanza una etapa de su recorrido si el resultado es
menor o igual a su nivel_ia. Nivel 0 = nunca se mueve; nivel 20 = avanza en
todos los ticks.

Recorridos
----------
El recorrido de cada personaje es una lista de etapas, y cada etapa es el
conjunto de habitaciones posibles para ese paso. Un recorrido fijo tiene una
sola habitación por etapa; uno parcialmente aleatorio ofrece varias y se
elige al azar al llegar. La última etapa siempre es el Primer Patio: al
alcanzarla el personaje deja de moverse y pasa a acechar al jugador desde su
puesto, con una cuenta regresiva antes de atacar.

El recorrido es autoral y no se deriva de las conexiones del grafo de
habitaciones: describe el camino que hace el personaje, no la geometría de
la vecindad (que sigue documentada en habitaciones.py).
"""

import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from constants import (
    ALTO_ANIMATRONIC_VISTA,
    DIR_ASSETS_ANIMATRONICS,
    HORA_INICIO_NOCHE,
    LUZ_RADIO_PELIGRO_MAXIMO,
    LUZ_RADIO_PELIGRO_MINIMO,
    NIVEL_IA_MAXIMO,
    NIVEL_IA_MINIMO,
)
from habitaciones import HABITACIONES, HABITACION_JUGADOR
from linterna import esta_iluminado
from objetos import (
    OBJETOS_DEFENSIVOS,
    SEGUNDOS_RETRASO_CHURRUMINO,
    ID_CHURRUMINO,
    obtener_objeto,
)
from posiciones import POSICION_BARRIL, POSICION_ENTRADA, POSICION_LAVADEROS, POSICIONES

Etapa = Tuple[str, ...]

# Poses de acercamiento que tiene cada personaje: 1 quieto, 2 encorvado y
# 3 lanzado. El Chavo tiene además sprites sujetando cada objeto, que entran
# en juego cuando se puedan arrojar objetos.
POSES_POR_PERSONAJE = 3


@dataclass(frozen=True)
class ConfiguracionAnimatronic:
    """Datos fijos de un personaje: por dónde va, dónde acecha, con qué arte
    se dibuja y cómo reacciona el jugador ante él. El nivel_ia no vive aquí
    porque cambia en cada noche y en la Noche Personalizada."""

    nombre: str
    recorrido: Tuple[Etapa, ...]
    puesto_acecho: str  # id de posiciones.py donde se le puede ver e iluminar
    punto_acecho: Tuple[int, int]  # dónde pisa, en el lienzo base
    espera_ataque_lenta: float  # segundos de margen con nivel_ia 1
    espera_ataque_rapida: float  # segundos de margen con nivel_ia 20
    # Arte: assets/animatronics/<carpeta>/<prefijo> <n>.png. La carpeta y el
    # prefijo no siempre coinciden (bruja/clotilde, don ramon/ramon).
    carpeta_sprite: str = ""
    prefijo_sprite: str = ""
    luz_mortal: bool = False  # iluminarlo de cerca mata al instante
    # Quico y Jaimico solo hacen caso de lo que se les arroja si están
    # alumbrados; El Chavo y los demás lo recogen de todos modos.
    necesita_luz_para_recibir: bool = False
    # Doña Clotilde: al llegar dice qué objeto anda buscando.
    pide_objeto: bool = False

    def ruta_pose(self, numero: int):
        return (
            DIR_ASSETS_ANIMATRONICS / self.carpeta_sprite
            / f"{self.prefijo_sprite} {numero}.png"
        )


class Animatronic:
    """Estado vivo de un personaje durante la noche."""

    def __init__(self, configuracion: ConfiguracionAnimatronic, nivel_ia: int):
        self.configuracion = configuracion
        self.nombre = configuracion.nombre
        self.nivel_ia = limitar_nivel_ia(nivel_ia)
        self.activo = self.nivel_ia > NIVEL_IA_MINIMO
        self.indice_etapa = 0
        self.habitacion_actual = random.choice(configuracion.recorrido[0])
        self.segundos_para_atacar = 0.0
        # Solo lo usa Doña Clotilde: el objeto que reclama en esta visita.
        self.objeto_pedido: Optional[str] = None

    # ------------------------------------------------------------------
    # Movimiento (una llamada por tick del temporizador)
    # ------------------------------------------------------------------
    def intentar_mover(self) -> bool:
        """Tira el dado de la IA: True si le toca avanzar en este tick."""
        if not self.activo:
            return False
        return random.randint(1, NIVEL_IA_MAXIMO) <= self.nivel_ia

    def actualizar(self):
        """Tick de IA: si el dado lo permite, avanza una etapa del recorrido."""
        if self.esta_acechando():
            return
        if self.intentar_mover():
            self._avanzar_etapa()

    def _avanzar_etapa(self):
        self.indice_etapa += 1
        self.habitacion_actual = random.choice(
            self.configuracion.recorrido[self.indice_etapa]
        )
        if self.esta_acechando():
            self.segundos_para_atacar = self.espera_de_ataque()
            if self.configuracion.pide_objeto:
                self.objeto_pedido = random.choice(OBJETOS_DEFENSIVOS)

    def esta_acechando(self) -> bool:
        """True cuando ya llegó al Primer Patio y está sobre el jugador."""
        return self.indice_etapa >= len(self.configuracion.recorrido) - 1

    # ------------------------------------------------------------------
    # Acecho (una llamada por fotograma: la espera corre en tiempo real)
    # ------------------------------------------------------------------
    def descontar_espera(self, dt: float) -> bool:
        """Consume el margen que le queda al jugador para reaccionar.
        Devuelve True el fotograma en que el personaje ataca."""
        if not self.activo or not self.esta_acechando():
            return False
        self.segundos_para_atacar -= dt
        return self.segundos_para_atacar <= 0.0

    def ahuyentar(self):
        """Lo manda de vuelta al principio de su recorrido. Es lo que hacen
        los objetos que le corresponden y los servicios del barril: no se
        elimina del elenco, vuelve a empezar el camino."""
        self.indice_etapa = 0
        self.habitacion_actual = random.choice(self.configuracion.recorrido[0])
        self.segundos_para_atacar = 0.0
        self.objeto_pedido = None

    def retrasar(self, segundos: float):
        """Le da al jugador un respiro sin quitarlo de encima."""
        if self.esta_acechando():
            self.segundos_para_atacar += segundos

    def acepta_objeto(self, iluminado: bool) -> bool:
        """Si hace caso de lo que se le arroja. Quico solo investiga lo que
        cae si está alumbrado, y a Jaimico hay que alumbrarlo para poder
        acercarle su café."""
        return iluminado or not self.configuracion.necesita_luz_para_recibir

    def espera_de_ataque(self) -> float:
        """Segundos que espera antes de atacar, interpolados por nivel_ia:
        cuanto más alto el nivel, menos margen deja."""
        lenta = self.configuracion.espera_ataque_lenta
        rapida = self.configuracion.espera_ataque_rapida
        return lenta + (rapida - lenta) * self._factor_ia()

    def radio_peligro(self) -> int:
        """Distancia a la que apuntarle con la linterna resulta mortal. Crece
        con el nivel_ia, achicando el margen seguro. 0 si la luz no le hace
        nada."""
        if not self.configuracion.luz_mortal:
            return 0
        rango = LUZ_RADIO_PELIGRO_MAXIMO - LUZ_RADIO_PELIGRO_MINIMO
        return int(LUZ_RADIO_PELIGRO_MINIMO + rango * self._factor_ia())

    def _factor_ia(self) -> float:
        """Posición del nivel_ia dentro de su rango útil (1-20), de 0.0 a 1.0."""
        return max(0.0, (self.nivel_ia - 1) / (NIVEL_IA_MAXIMO - 1))

    # ------------------------------------------------------------------
    # Presentación
    # ------------------------------------------------------------------
    def indice_pose(self) -> int:
        """Pose que le toca según lo lejos que haya llegado: de pie cuando
        recién sale de su casa, encorvado a medio camino y lanzado encima del
        jugador al final del recorrido."""
        etapas = len(self.configuracion.recorrido) - 1
        if etapas <= 0:
            return POSES_POR_PERSONAJE
        progreso = self.indice_etapa / etapas
        return 1 + round(progreso * (POSES_POR_PERSONAJE - 1))

    def ruta_sprite(self):
        return self.configuracion.ruta_pose(self.indice_pose())

    def clave_sprite(self) -> str:
        """Identifica la pose concreta dentro del caché de imágenes."""
        return f"{self.nombre} {self.indice_pose()}"

    @property
    def puesto_acecho(self) -> str:
        return self.configuracion.puesto_acecho

    @property
    def punto_acecho(self) -> Tuple[int, int]:
        """Dónde pisa el personaje, que es por donde se ancla su figura."""
        return self.configuracion.punto_acecho

    @property
    def punto_torso(self) -> Tuple[int, int]:
        """Centro del cuerpo. Es el punto contra el que se mide la linterna:
        el jugador apunta al personaje, no a sus pies."""
        x, y = self.configuracion.punto_acecho
        return (x, y - ALTO_ANIMATRONIC_VISTA // 2)


def limitar_nivel_ia(nivel: int) -> int:
    return max(NIVEL_IA_MINIMO, min(NIVEL_IA_MAXIMO, int(nivel)))


# ----------------------------------------------------------------------
# Elenco
# ----------------------------------------------------------------------
# Cada personaje parte de su casa y termina en el Primer Patio. Las etapas
# con varias habitaciones son los tramos donde el recorrido se vuelve
# impredecible.
#
# PENDIENTE DE AJUSTE: los recorridos, los puestos de acecho y las esperas de
# ataque de todos los personajes salvo Jaimico y Doña Clotilde son
# provisionales; el diseño solo fija los tiempos de esos dos (20-40 s y
# 7-15 s respectivamente).
ELENCO: Tuple[ConfiguracionAnimatronic, ...] = (
    ConfiguracionAnimatronic(
        nombre="Don Ramón",
        recorrido=(("casa_ramon",), ("entrada",), (HABITACION_JUGADOR,)),
        puesto_acecho=POSICION_ENTRADA,
        punto_acecho=(390, 655),
        espera_ataque_lenta=12.0,
        espera_ataque_rapida=5.0,
        carpeta_sprite="don ramon",
        prefijo_sprite="ramon",
        luz_mortal=True,
    ),
    ConfiguracionAnimatronic(
        nombre="Doña Florinda",
        recorrido=(
            ("casa_florinda",),
            ("segundo_patio",),
            ("casa_popis",),
            (HABITACION_JUGADOR,),
        ),
        puesto_acecho=POSICION_LAVADEROS,
        punto_acecho=(720, 660),
        espera_ataque_lenta=12.0,
        espera_ataque_rapida=5.0,
        carpeta_sprite="florinda",
        prefijo_sprite="florinda",
        luz_mortal=True,
    ),
    ConfiguracionAnimatronic(
        nombre="La Chilindrina",
        recorrido=(
            ("casa_ramon",),
            ("segundo_patio",),
            ("casa_paty", "casa_popis"),
            (HABITACION_JUGADOR,),
        ),
        puesto_acecho=POSICION_LAVADEROS,
        punto_acecho=(330, 645),
        espera_ataque_lenta=14.0,
        espera_ataque_rapida=6.0,
        carpeta_sprite="chilindrina",
        prefijo_sprite="chilindrina",
        luz_mortal=True,
    ),
    ConfiguracionAnimatronic(
        nombre="Quico",
        recorrido=(
            ("casa_florinda",),
            ("segundo_patio", "casa_godinez"),
            ("entrada",),
            (HABITACION_JUGADOR,),
        ),
        puesto_acecho=POSICION_ENTRADA,
        punto_acecho=(900, 660),
        espera_ataque_lenta=14.0,
        espera_ataque_rapida=6.0,
        carpeta_sprite="quico",
        prefijo_sprite="quico",
        necesita_luz_para_recibir=True,
    ),
    ConfiguracionAnimatronic(
        nombre="El Chavo",
        recorrido=(
            ("casa_chavo",),
            ("segundo_patio", "casa_godinez", "casa_popis"),
            (HABITACION_JUGADOR,),
        ),
        puesto_acecho=POSICION_BARRIL,
        punto_acecho=(640, 665),
        espera_ataque_lenta=18.0,
        espera_ataque_rapida=8.0,
        carpeta_sprite="chavo",
        prefijo_sprite="chavo",
    ),
    ConfiguracionAnimatronic(
        nombre="Jaimico",
        recorrido=(("casa_jaimito",), ("entrada",), (HABITACION_JUGADOR,)),
        puesto_acecho=POSICION_ENTRADA,
        punto_acecho=(640, 640),
        espera_ataque_lenta=40.0,
        espera_ataque_rapida=20.0,
        carpeta_sprite="jaimico",
        prefijo_sprite="jaimico",
        necesita_luz_para_recibir=True,
    ),
    ConfiguracionAnimatronic(
        nombre="Doña Clotilde",
        recorrido=(
            ("casa_clotilde",),
            ("segundo_patio", "casa_paty"),
            ("entrada",),
            (HABITACION_JUGADOR,),
        ),
        puesto_acecho=POSICION_ENTRADA,
        punto_acecho=(1120, 670),
        espera_ataque_lenta=15.0,
        espera_ataque_rapida=7.0,
        carpeta_sprite="bruja",
        prefijo_sprite="clotilde",
        pide_objeto=True,
    ),
)

# Hora de la noche a partir de la cual el elenco empieza a moverse. En la
# noche 1 nadie se mueve hasta las 2 AM, para que el jugador tenga tiempo de
# hacerse a los controles. Las noches que no aparezcan arrancan a las 12.
HORA_ARRANQUE_POR_NOCHE: Dict[int, int] = {1: 2}


def hora_de_arranque(numero_noche: int) -> int:
    """Horas de noche que deben pasar antes de que el elenco se mueva."""
    return HORA_ARRANQUE_POR_NOCHE.get(numero_noche, HORA_INICIO_NOCHE)

# Nivel de IA de cada personaje en cada noche de la campaña. La noche 1 es la
# definida por el diseño (solo Don Ramón, Quico y La Chilindrina activos);
# PENDIENTE DE AJUSTE: las noches 2 a 6 son una progresión provisional.
NIVELES_POR_NOCHE: Dict[int, Dict[str, int]] = {
    1: {"Don Ramón": 4, "Quico": 3, "La Chilindrina": 3},
    2: {"Don Ramón": 6, "Quico": 5, "La Chilindrina": 5, "Doña Florinda": 4},
    3: {
        "Don Ramón": 8, "Quico": 7, "La Chilindrina": 7,
        "Doña Florinda": 6, "El Chavo": 5,
    },
    4: {
        "Don Ramón": 10, "Quico": 9, "La Chilindrina": 9,
        "Doña Florinda": 8, "El Chavo": 7, "Jaimico": 6,
    },
    5: {
        "Don Ramón": 12, "Quico": 11, "La Chilindrina": 11,
        "Doña Florinda": 10, "El Chavo": 9, "Jaimico": 8, "Doña Clotilde": 7,
    },
    6: {
        "Don Ramón": 16, "Quico": 15, "La Chilindrina": 15,
        "Doña Florinda": 14, "El Chavo": 13, "Jaimico": 12, "Doña Clotilde": 11,
    },
}


def nombres_del_elenco() -> List[str]:
    return [config.nombre for config in ELENCO]


def niveles_iniciales_personalizada() -> Dict[str, int]:
    """Todos los personajes en 0, como arranca cualquier noche personalizada
    antes de que el jugador suba a alguien."""
    return {config.nombre: NIVEL_IA_MINIMO for config in ELENCO}


def crear_elenco_noche(numero_noche: int) -> List[Animatronic]:
    """Crea el elenco de una noche de la campaña. Los personajes que no
    aparecen en la tabla de esa noche quedan en nivel 0 (inactivos)."""
    niveles = NIVELES_POR_NOCHE.get(numero_noche, {})
    return crear_elenco_personalizado(niveles)


def crear_elenco_personalizado(niveles: Dict[str, int]) -> List[Animatronic]:
    """Crea el elenco con el nivel de IA elegido para cada personaje."""
    return [
        Animatronic(config, niveles.get(config.nombre, NIVEL_IA_MINIMO))
        for config in ELENCO
    ]


def acechando_en(animatronics, id_posicion: str) -> List[Animatronic]:
    """Personajes que ya llegaron y acechan desde la posición indicada, o sea
    los que el jugador puede ver e iluminar estando ahí parado."""
    return [
        animatronic for animatronic in animatronics
        if animatronic.activo
        and animatronic.esta_acechando()
        and animatronic.puesto_acecho == id_posicion
    ]


def iluminados_en(animatronics, id_posicion: str, punto_luz, encendida: bool):
    """Nombres de los personajes que el jugador tiene dentro del haz."""
    if not encendida:
        return set()
    return {
        animatronic.nombre
        for animatronic in acechando_en(animatronics, id_posicion)
        if esta_iluminado(animatronic.punto_torso, punto_luz)
    }


def detectar_luz_mortal(animatronics, id_posicion: str, punto_luz):
    """Devuelve el personaje al que la linterna está apuntando lo bastante
    cerca como para que sea mortal, o None si no hay ninguno."""
    if punto_luz is None:
        return None
    x, y = punto_luz
    for animatronic in acechando_en(animatronics, id_posicion):
        radio = animatronic.radio_peligro()
        if radio <= 0:
            continue
        distancia_x = x - animatronic.punto_torso[0]
        distancia_y = y - animatronic.punto_torso[1]
        if distancia_x * distancia_x + distancia_y * distancia_y <= radio * radio:
            return animatronic
    return None


@dataclass
class ResultadoArrojo:
    """Qué pasó al arrojar un objeto: a quién se llevó por delante, a quién
    solo entretuvo, y si el objeto se gastó."""

    eliminado: Optional[Animatronic] = None
    retrasado: Optional[Animatronic] = None

    @property
    def sirvio(self) -> bool:
        return self.eliminado is not None or self.retrasado is not None


def resolver_arrojo(presentes, id_objeto: str, iluminados) -> ResultadoArrojo:
    """Decide a quién le toca el objeto que se acaba de arrojar.

    Primero se atiende a Doña Clotilde si pidió justo eso, porque el objeto
    va dirigido a ella. Después se recorre la lista del objeto en orden: el
    primero de esa lista que esté delante y lo acepte es el que se va. El
    churrumino suelto es el caso aparte: no elimina a nadie, solo entretiene
    a El Chavo un rato.
    """
    objeto = obtener_objeto(id_objeto)

    for animatronic in presentes:
        if animatronic.objeto_pedido == id_objeto:
            animatronic.ahuyentar()
            return ResultadoArrojo(eliminado=animatronic)

    if id_objeto == ID_CHURRUMINO:
        for animatronic in presentes:
            if animatronic.nombre == "El Chavo":
                animatronic.retrasar(SEGUNDOS_RETRASO_CHURRUMINO)
                return ResultadoArrojo(retrasado=animatronic)
        return ResultadoArrojo()

    por_nombre = {animatronic.nombre: animatronic for animatronic in presentes}
    for nombre in objeto.elimina:
        animatronic = por_nombre.get(nombre)
        if animatronic is None:
            continue
        if not animatronic.acepta_objeto(nombre in iluminados):
            continue
        animatronic.ahuyentar()
        return ResultadoArrojo(eliminado=animatronic)
    return ResultadoArrojo()


def _validar_elenco():
    """Comprueba al importar que los recorridos apuntan a habitaciones y
    puestos que existen, para que un id mal escrito falle de inmediato y no a
    mitad de una partida."""
    for config in ELENCO:
        if len(config.recorrido) < 2:
            raise ValueError(f"{config.nombre}: el recorrido necesita al menos 2 etapas")
        if config.recorrido[-1] != (HABITACION_JUGADOR,):
            raise ValueError(
                f"{config.nombre}: el recorrido debe terminar en {HABITACION_JUGADOR}"
            )
        for etapa in config.recorrido:
            for id_habitacion in etapa:
                if id_habitacion not in HABITACIONES:
                    raise ValueError(f"{config.nombre}: habitación desconocida {id_habitacion}")
        if config.puesto_acecho not in POSICIONES:
            raise ValueError(f"{config.nombre}: puesto de acecho desconocido {config.puesto_acecho}")
        for pose in range(1, POSES_POR_PERSONAJE + 1):
            if not config.ruta_pose(pose).exists():
                raise ValueError(f"{config.nombre}: falta el sprite {config.ruta_pose(pose)}")


_validar_elenco()
