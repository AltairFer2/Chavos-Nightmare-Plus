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
"""

import random
from typing import Optional, Sequence, Tuple

from ...config.jugabilidad import (
    ALTURA_TORSO,
    LUZ_RADIO_PELIGRO_MAXIMO,
    LUZ_RADIO_PELIGRO_MINIMO,
)
from ...config.partida import NIVEL_IA_MAXIMO, NIVEL_IA_MINIMO
from ...mundo.habitaciones import HABITACION_JUGADOR
from ..objetos import OBJETOS_DEFENSIVOS
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
        self.habitacion_actual = configuracion.habitacion_inicial
        self.segundos_para_atacar = 0.0
        # Cuál de sus diseños se le ve mientras acecha. Se sortea al llegar.
        self.pose = 1
        # Se pone en True al alumbrarlo: deja de respetar el barril.
        self.activado = False
        # Solo lo usa Doña Clotilde: el objeto que reclama en esta visita.
        self.objeto_pedido: Optional[str] = None

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

    def actualizar(self, elenco: Sequence["Animatronic"] = ()):
        """Ronda de IA: si el dado lo permite, cambia de cámara."""
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
        if self.configuracion.pide_objeto:
            self.objeto_pedido = random.choice(OBJETOS_DEFENSIVOS)

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

    def ahuyentar(self):
        """Lo saca de encima del jugador. Es lo que hacen los objetos que le
        corresponden y los servicios del barril: no se elimina del elenco, se
        va por donde su recorrido diga y vuelve a acercarse desde ahí."""
        salidas = self.configuracion.transiciones.get(HABITACION_JUGADOR, ())
        self.habitacion_actual = (
            random.choice(salidas) if salidas else self.configuracion.habitacion_inicial
        )
        self.segundos_para_atacar = 0.0
        self.objeto_pedido = None
        self.activado = False

    def retroceder(self) -> bool:
        """Le quita una cámara de terreno sin mandarlo a su casa. Es lo que
        hace el audio con Doña Florinda. Devuelve False si desde donde está
        ya no se le puede empujar: al llegar a la reja el audio deja de
        servir y hay que aguantarla ahí."""
        destinos = self.configuracion.retrocesos.get(self.habitacion_actual, ())
        if not destinos:
            return False
        self.habitacion_actual = random.choice(destinos)
        self.segundos_para_atacar = 0.0
        self.objeto_pedido = None
        return True

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
