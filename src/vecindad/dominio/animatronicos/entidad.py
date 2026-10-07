"""Estado vivo de un personaje durante la noche.

Sistema de IA (escala 0-20, estilo FNAF)
---------------------------------------
Cada `intervalo_movimiento` segundos el TemporizadorNoche abre una ronda. En
cada ronda, todo animatrónico activo tira random.randint(1, 20) y se mueve si
el resultado es menor o igual a su nivel_ia. Nivel 0 = nunca se mueve; nivel
20 = se mueve en todas las rondas.

A dónde se mueve lo decide su grafo de transiciones (ver definicion.py): de
la cámara donde está, uno de sus destinos al azar. Una vez en el Primer Patio
deja de tirar el dado: de ahí solo lo saca su contramedida.

Quien no está en ninguna cámara (habitacion_actual en None) usa el mismo
dado para aparecer en una de las suyas.
"""

import random
from typing import Optional, Sequence, Tuple

from ...config.jugabilidad import (
    ALTURA_TORSO,
    LUZ_RADIO_PELIGRO_MAXIMO,
    LUZ_RADIO_PELIGRO_MINIMO,
    PUNTO_DEBIL_CAMBIO_SEGUNDOS,
    PUNTO_DEBIL_FACTOR_MAS_DIFICIL,
    PUNTO_DEBIL_RADIO,
    PUNTO_DEBIL_SEGUNDOS,
    PUNTO_DEBIL_VELOCIDAD,
)
from ...config.partida import NIVEL_IA_MAXIMO, NIVEL_IA_MINIMO
from ...mundo.habitaciones import HABITACION_JUGADOR
from .definicion import POSES_POR_PERSONAJE, ConfiguracionAnimatronic


def limitar_nivel_ia(nivel: int) -> int:
    return max(NIVEL_IA_MINIMO, min(NIVEL_IA_MAXIMO, int(nivel)))


class Animatronic:
    """Estado vivo de un personaje durante la noche."""

    def __init__(self, configuracion: ConfiguracionAnimatronic, nivel_ia: int):
        self.configuracion = configuracion
        self.nombre = configuracion.nombre
        self.nivel_ia = limitar_nivel_ia(nivel_ia)
        self.activo = self.nivel_ia > NIVEL_IA_MINIMO
        # None mientras no esté en ninguna cámara (los que aparecen).
        self.habitacion_actual: Optional[str] = configuracion.habitacion_inicial
        self.segundos_para_atacar = 0.0
        # Cuál de sus diseños se le ve mientras acecha. Se sortea al llegar.
        self.pose = 1
        # Se pone en True al alumbrarlo: deja de respetar el barril.
        self.activado = False

    # ------------------------------------------------------------------
    # Movimiento (una llamada por ronda del temporizador)
    # ------------------------------------------------------------------
    def destinos_posibles(self, elenco: Sequence["Animatronic"] = ()) -> Tuple[str, ...]:
        """Cámaras a las que puede pasar ahora mismo. Puede quedar vacía: hay
        aristas que dependen de dónde esté otro personaje, y mientras no se
        cumpla esa condición el personaje se queda donde está."""
        destinos = self.configuracion.transiciones.get(self.habitacion_actual, ())
        condiciones = self.configuracion.condiciones_de_paso
        if not condiciones:
            return tuple(destinos)
        return tuple(
            destino for destino in destinos
            if self._cumple(condiciones.get((self.habitacion_actual, destino)), elenco)
        )

    @staticmethod
    def _cumple(condicion, elenco) -> bool:
        if condicion is None:
            return True
        nombre, id_habitacion = condicion
        return any(
            otro.activo
            and otro.nombre == nombre
            and otro.habitacion_actual == id_habitacion
            for otro in elenco
        )

    def intentar_mover(self) -> bool:
        """Tira el dado de la IA: True si le toca moverse en esta ronda."""
        if not self.activo:
            return False
        return random.randint(1, NIVEL_IA_MAXIMO) <= self.nivel_ia

    def intentar_aparecer(self) -> bool:
        """El dado de la IA, rebajado por su probabilidad_aparicion: a más
        nivel, más probable que aparezca en esta ronda."""
        if not self.intentar_mover():
            return False
        probabilidad = self.configuracion.probabilidad_aparicion
        return probabilidad >= 1.0 or random.random() < probabilidad

    def actualizar(self, elenco: Sequence["Animatronic"] = ()):
        """Ronda de IA: si el dado lo permite, cambia de cámara, o aparece
        si no estaba en ninguna."""
        if not self.presente:
            if self.configuracion.aparece_en and self.intentar_aparecer():
                self.aparecer()
            return
        if self.esta_acechando():
            return
        destinos = self.destinos_posibles(elenco)
        if not destinos:
            return
        if self.intentar_mover():
            self._ir_a(random.choice(destinos))

    def _ir_a(self, id_habitacion: str):
        self.habitacion_actual = id_habitacion
        self.activado = False
        if not self.esta_acechando():
            return
        self.pose = random.randint(1, POSES_POR_PERSONAJE)
        self.segundos_para_atacar = self.espera_de_ataque()

    @property
    def presente(self) -> bool:
        """Si está en alguna cámara. Los que aparecen empiezan sin estarlo y
        vuelven a no estarlo cuando se les quita de encima."""
        return self.habitacion_actual is not None

    def aparecer(self):
        """Se presenta en una de sus cámaras de aparición, al azar."""
        self.habitacion_actual = random.choice(self.configuracion.aparece_en)
        self.segundos_para_atacar = 0.0
        self.activado = False

    def desaparecer(self):
        """Deja de estar en ninguna cámara: encontraron su objeto. Si es de
        los que aparecen, la ronda siguiente puede volver a intentarlo."""
        self.habitacion_actual = None
        self.segundos_para_atacar = 0.0
        self.activado = False

    def irrumpir(self):
        """Lo planta encima del jugador sin pasar por su recorrido.

        No todos llegan caminando: El Chavo no tiene ninguna arista hacia el
        Primer Patio y aparece ahí de golpe cuando se le mira demasiado rato
        seguido. Es la operación inversa de ahuyentar()."""
        self._ir_a(HABITACION_JUGADOR)

    def esta_acechando(self) -> bool:
        """True cuando está en el Primer Patio, encima del jugador."""
        return self.habitacion_actual == HABITACION_JUGADOR

    # ------------------------------------------------------------------
    # Acecho (una llamada por fotograma: la espera corre en tiempo real)
    # ------------------------------------------------------------------
    def puede_alcanzar_escondido(self) -> bool:
        """Si puede acabar con el jugador metido en el barril.

        Don Ramón y Doña Florinda pueden desde que llegan: son los que hacen
        que esconderse no sea una respuesta a todo. Del resto se está a salvo
        dentro del barril, incluso mirando las cámaras, hasta que el jugador
        cometa el error de alumbrarlos."""
        return self.configuracion.alcanza_escondido or self.activado

    def alumbrar(self):
        """Darle con la linterna. A quien no mata, lo activa: a partir de ahí
        ya no vale con meterse al barril."""
        if self.esta_acechando():
            self.activado = True

    def descontar_espera(self, dt: float, jugador_escondido: bool = False) -> bool:
        """Consume el margen que le queda al jugador para reaccionar.
        Devuelve True el fotograma en que el personaje ataca.

        Escondido en el barril el margen ni siquiera corre para quien no
        puede alcanzarle ahí: el jugador está a salvo de ese, no contra
        reloj."""
        if not self.activo or not self.esta_acechando():
            return False
        if jugador_escondido and not self.puede_alcanzar_escondido():
            return False
        self.segundos_para_atacar -= dt
        return self.segundos_para_atacar <= 0.0

    def inminencia(self) -> float:
        """Qué tan cerca está de atacar: 0.0 al plantarse en el patio y 1.0
        en el instante del ataque. Fuera del patio, 0.0. Mientras su espera
        no corre (el jugador a salvo en el barril) se queda donde estaba."""
        if not self.activo or not self.esta_acechando():
            return 0.0
        espera = self.espera_de_ataque()
        if espera <= 0.0:
            return 1.0
        return max(0.0, min(1.0, 1.0 - self.segundos_para_atacar / espera))

    def ahuyentar(self):
        """Lo saca de encima del jugador. Es lo que hacen espantarlo con la
        luz y los servicios del barril: no se elimina del elenco, se va por
        donde su recorrido diga y vuelve a acercarse desde ahí. Si su
        recorrido no tiene salida, vuelve a donde empezó la noche, que para
        los que aparecen es no estar en ninguna cámara."""
        salidas = self.configuracion.transiciones.get(HABITACION_JUGADOR, ())
        self.habitacion_actual = (
            random.choice(salidas) if salidas else self.configuracion.habitacion_inicial
        )
        self.segundos_para_atacar = 0.0
        self.activado = False

    def camaras_vecinas(self) -> Tuple[str, ...]:
        """Las cámaras que lindan con la suya por su propio recorrido, de
        ida o de vuelta, más los retrocesos. El Primer Patio no cuenta: ahí
        no se le puede llevar con un audio."""
        actual = self.habitacion_actual
        vecinas = []
        for aristas in (self.configuracion.transiciones, self.configuracion.retrocesos):
            for origen, destinos in aristas.items():
                if origen == actual:
                    vecinas.extend(destinos)
                elif actual in destinos:
                    vecinas.append(origen)
        return tuple(
            dict.fromkeys(c for c in vecinas if c not in (actual, HABITACION_JUGADOR))
        )

    def atraer_a(self, id_habitacion: str) -> bool:
        """El audio de Quico sonando en esa cámara. Si es vecina de la suya,
        va hacia allá; si queda lejos, no lo oye. Puede hacerla retroceder o,
        si se pone el audio del lado equivocado, acercarla. Devuelve si se
        movió. Desde la reja (sorda_en) ya no hace caso."""
        if not self.activo or self.esta_acechando():
            return False
        if self.habitacion_actual in self.configuracion.sorda_en:
            return False
        if id_habitacion not in self.camaras_vecinas():
            return False
        self.habitacion_actual = id_habitacion
        self.segundos_para_atacar = 0.0
        return True

    def espera_de_ataque(self) -> float:
        """Segundos que espera antes de atacar, interpolados por nivel_ia:
        cuanto más alto el nivel, menos margen deja."""
        lenta = self.configuracion.espera_ataque_lenta
        rapida = self.configuracion.espera_ataque_rapida
        return lenta + (rapida - lenta) * self._factor_ia()

    @property
    def reacciona_a_la_luz(self) -> bool:
        """Si apuntarle con la linterna tiene alguna consecuencia. A unos les
        mata y a otra se le va la batería del jugador, pero el radio dentro
        del cual se dan cuenta es el mismo."""
        return (
            self.configuracion.luz_mortal
            or self.configuracion.luz_descarga_linterna
        )

    def radio_peligro(self) -> int:
        """Distancia a la que apuntarle con la linterna tiene consecuencias.
        Crece con el nivel_ia, achicando el margen seguro. 0 si la luz no le
        hace nada."""
        if not self.reacciona_a_la_luz:
            return 0
        rango = LUZ_RADIO_PELIGRO_MAXIMO - LUZ_RADIO_PELIGRO_MINIMO
        return int(LUZ_RADIO_PELIGRO_MINIMO + rango * self._factor_ia())

    # ------------------------------------------------------------------
    # Punto débil (ver dominio/espanto.py): cuanto más nivel, más chico,
    # más rápido, más nervioso y más rato hay que sostenerlo.
    # ------------------------------------------------------------------
    def radio_punto_debil(self) -> float:
        return self._segun_punto_debil(PUNTO_DEBIL_RADIO)

    def segundos_para_espantar(self) -> float:
        return self._segun_punto_debil(PUNTO_DEBIL_SEGUNDOS)

    def velocidad_punto_debil(self) -> float:
        return self._segun_punto_debil(PUNTO_DEBIL_VELOCIDAD)

    def cambio_punto_debil(self) -> Tuple[float, float]:
        """Cada cuánto (mínimo, máximo) su punto débil cambia de destino."""
        lento, rapido = PUNTO_DEBIL_CAMBIO_SEGUNDOS
        return (
            self._segun_punto_debil((lento[0], rapido[0])),
            self._segun_punto_debil((lento[1], rapido[1])),
        )

    def _segun_punto_debil(self, extremos: Tuple[float, float]) -> float:
        """Como segun_ia, con dos salvedades: el más difícil de espantar
        (Jaimico) usa siempre el mismo punto de la escala, sea cual sea su
        nivel, y a quien tiene punto_debil_escala se le cuenta solo esa
        parte de su nivel (La Chilindrina)."""
        config = self.configuracion
        if config.punto_debil_mas_dificil:
            factor = PUNTO_DEBIL_FACTOR_MAS_DIFICIL
        else:
            factor = self._factor_ia() * config.punto_debil_escala
        bajo, alto = extremos
        return bajo + (alto - bajo) * factor

    def segun_ia(self, extremos: Tuple[float, float]) -> float:
        """Interpola entre el valor de nivel 1 y el de nivel 20. Es público
        porque el monitor también escala con el nivel (lo errático que se
        pone con El Chavo en pantalla)."""
        bajo, alto = extremos
        return bajo + (alto - bajo) * self._factor_ia()

    def _factor_ia(self) -> float:
        """Posición del nivel_ia dentro de su rango útil (1-20), de 0.0 a 1.0."""
        return max(0.0, (self.nivel_ia - 1) / (NIVEL_IA_MAXIMO - 1))

    # ------------------------------------------------------------------
    # Presentación
    # ------------------------------------------------------------------
    def indice_pose(self) -> int:
        """Cuál de sus diseños se está usando. Se sortea al llegar al Primer
        Patio y no cambia mientras siga ahí."""
        return self.pose

    def ruta_sprite(self):
        return self.configuracion.ruta_pose(self.indice_pose())

    def clave_sprite(self) -> str:
        """Identifica la pose concreta dentro del caché de imágenes."""
        return f"{self.nombre} {self.indice_pose()}"

    def punto_acecho_en(self, id_posicion: str) -> Optional[Tuple[int, int]]:
        """Dónde pisa el personaje visto desde ese sitio, que es por donde se
        ancla su figura. None si desde ahí no se le ve."""
        return self.configuracion.puntos_acecho.get(id_posicion)

    def punto_torso_en(self, id_posicion: str) -> Optional[Tuple[int, int]]:
        """Centro del cuerpo visto desde ese sitio. Es el punto contra el que
        se mide la linterna: el jugador apunta al personaje, no a sus pies."""
        punto = self.punto_acecho_en(id_posicion)
        if punto is None:
            return None
        return (punto[0], punto[1] - ALTURA_TORSO)
