"""Servicios de utilidad que el jugador maneja desde dentro del barril.

Son cuatro y cada uno tarda lo suyo: mientras un servicio está en marcha no
se puede lanzar otro, y ese rato de espera es justo lo que hace peligroso
usarlos con alguien encima.

1. Llamar al Señor Barriga. Es lo único que quita a Don Ramón de encima,
   pero llamarlo cuando Don Ramón no está acechando le cuesta la vida al
   jugador: el Sr. Barriga viene a cobrar la renta, aunque no de inmediato,
   sino entre 5 y 15 segundos después (al azar), así que la partida sigue
   corriendo mientras se acerca. Dentro del barril no puede alcanzar al
   jugador: si el plazo se cumple estando escondido, se queda esperando
   afuera y lo atrapa en el instante en que el jugador vuelve a asomarse.
   Queda en espera unos segundos tras cada llamada.
2. Reponer el audio de Quico. Ojo: aquí no suena nada, se repara la cinta.
   Quien gasta las reproducciones es el botón de audio del monitor (ver
   `sonar_audio`), y cuando se acaban hay que venir al barril a reponerlas.
3. Restablecer cámaras. Necesario cuando El Chavo las arruina por mirarlo
   demasiado rato.
4. Restablecer todo. Repone de una vez el audio de Quico y las cámaras, a
   cambio de dejar al jugador ocupado bastante más tiempo.

Aparte de los cuatro está `sonar_audio()`, que no es un servicio del panel:
se dispara desde el monitor de cámaras, gasta una reproducción y hace
retroceder a Doña Florinda. No deja al jugador ocupado, porque se usa
mientras está mirando las cámaras y tiene que poder encadenarse.
"""

import random
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

from ..config.jugabilidad import (
    BARRIGA_COOLDOWN_SEGUNDOS,
    BARRIGA_LLEGADA_MAXIMA_SEGUNDOS,
    BARRIGA_LLEGADA_MINIMA_SEGUNDOS,
    NOCHE_AUDIO_LIMITADO,
    SERVICIO_AUDIO_SEGUNDOS,
    SERVICIO_CAMARAS_SEGUNDOS,
    SERVICIO_TODO_SEGUNDOS,
    USOS_AUDIO_POR_NOCHE,
    USOS_AUDIO_QUICO,
)
from .animatronicos import nombres


def usos_de_audio(numero_noche: int) -> int:
    """Reproducciones del audio de Quico con las que arranca esa noche. En la
    noche 1 el contador no se mira (el audio es ilimitado), pero se deja con
    un número igual para que el panel tenga siempre algo que enseñar."""
    return USOS_AUDIO_POR_NOCHE.get(numero_noche, USOS_AUDIO_QUICO)


class Servicio(Enum):
    BARRIGA = auto()
    REPONER_AUDIO = auto()
    CAMARAS = auto()
    TODO = auto()


class Resultado(Enum):
    """Qué salió de intentar usar un servicio."""

    OCUPADO = auto()  # hay otro servicio en marcha, o este está en espera
    SIN_USOS = auto()  # el audio de Quico se agotó
    EN_MARCHA = auto()  # arrancó y tardará sus segundos
    LLAMADA_EN_VANO = auto()  # se llamó al Sr. Barriga sin Don Ramón delante
    AHUYENTADO = auto()  # el servicio se llevó a quien tenía que llevarse
    SONO = auto()  # el audio sonó pero no le quitó terreno a nadie


# Cuánto tarda cada servicio en completarse.
DURACIONES = {
    Servicio.BARRIGA: 0.0,  # la llamada es inmediata; lo que queda es la espera
    Servicio.REPONER_AUDIO: SERVICIO_AUDIO_SEGUNDOS,
    Servicio.CAMARAS: SERVICIO_CAMARAS_SEGUNDOS,
    Servicio.TODO: SERVICIO_TODO_SEGUNDOS,
}


@dataclass
class EstadoServicios:
    """Lo que el panel necesita saber para dibujarse."""

    en_marcha: Optional[Servicio] = None
    restante: float = 0.0
    total: float = 0.0
    espera_barriga: float = 0.0
    usos_audio: int = 0
    usos_totales: int = 0  # con cuántos arrancó la noche, para dibujar el contador
    audio_ilimitado: bool = False


class ServiciosUtilidad:
    """Estado de los cuatro servicios durante una noche."""

    def __init__(self, numero_noche: int = 1):
        self.audio_ilimitado = numero_noche < NOCHE_AUDIO_LIMITADO
        self.usos_audio = usos_de_audio(numero_noche)
        self._usos_de_la_noche = self.usos_audio
        self._en_marcha: Optional[Servicio] = None
        self._restante = 0.0
        self._total = 0.0
        self._espera_barriga = 0.0
        # Cuenta regresiva hasta que el Sr. Barriga llega a cobrar tras una
        # llamada en vano. 0 significa que no hay ninguno en camino.
        self._barriga_por_llegar = 0.0
        # True desde que se cumple ese plazo hasta que atrapa al jugador:
        # dentro del barril no puede tocarlo, así que se queda merodeando
        # hasta que se vuelva a asomar.
        self._barriga_esperando = False
        # Se pone en True un único fotograma: el que lo atrapa. Quien orquesta
        # la partida lo revisa después de cada actualizar() y decide ahí el
        # game over, en vez de que este módulo conozca a Juego.
        self.barriga_letal = False

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------
    @property
    def ocupado(self) -> bool:
        return self._en_marcha is not None

    def disponible(self, servicio: Servicio) -> bool:
        if self.ocupado:
            return False
        if servicio is Servicio.BARRIGA:
            return self._espera_barriga <= 0.0
        if servicio is Servicio.REPONER_AUDIO:
            # Reponer una cinta que está entera no tiene sentido.
            return not self.audio_ilimitado and self.usos_audio < self._usos_de_la_noche
        return True

    def audio_disponible(self) -> bool:
        """Si queda alguna reproducción para sonar desde el monitor."""
        return self.audio_ilimitado or self.usos_audio > 0

    def estado(self) -> EstadoServicios:
        return EstadoServicios(
            en_marcha=self._en_marcha,
            restante=self._restante,
            total=self._total,
            espera_barriga=self._espera_barriga,
            usos_audio=self.usos_audio,
            usos_totales=self._usos_de_la_noche,
            audio_ilimitado=self.audio_ilimitado,
        )

    # ------------------------------------------------------------------
    # Uso
    # ------------------------------------------------------------------
    def usar(self, servicio: Servicio, animatronics=()) -> Resultado:
        """Lanza un servicio. Los efectos sobre el elenco (ahuyentar a Don
        Ramón o a Doña Florinda) son inmediatos; lo que tarda es que el
        jugador vuelva a tener las manos libres."""
        if self.ocupado:
            return Resultado.OCUPADO

        if servicio is Servicio.BARRIGA:
            return self._llamar_barriga(animatronics)
        if servicio is Servicio.REPONER_AUDIO:
            return self._reponer_audio()
        if servicio is Servicio.CAMARAS:
            return self._arrancar(servicio)
        return self._restablecer_todo()

    def _llamar_barriga(self, animatronics) -> Resultado:
        if self._espera_barriga > 0.0:
            return Resultado.OCUPADO

        self._espera_barriga = BARRIGA_COOLDOWN_SEGUNDOS
        ramon = self._acechando(animatronics, nombres.DON_RAMON)
        if ramon is None:
            # Si ya venía uno en camino de una llamada anterior, o si ya
            # llegó y está esperando a que el jugador se asome, repetir la
            # llamada no cambia nada: solo se arranca la cuenta una vez, para
            # que no se pueda posponer la muerte llamando de nuevo cada vez
            # que se acaba el cooldown.
            if self._barriga_por_llegar <= 0.0 and not self._barriga_esperando:
                self._barriga_por_llegar = random.uniform(
                    BARRIGA_LLEGADA_MINIMA_SEGUNDOS, BARRIGA_LLEGADA_MAXIMA_SEGUNDOS
                )
            return Resultado.LLAMADA_EN_VANO
        ramon.ahuyentar()
        return Resultado.AHUYENTADO

    def _reponer_audio(self) -> Resultado:
        """Repara la cinta: aquí no suena nada ni se mueve nadie. Solo deja el
        contador lleno para poder volver a usar el audio desde el monitor."""
        if self.audio_ilimitado or self.usos_audio >= self._usos_de_la_noche:
            return Resultado.OCUPADO
        self.usos_audio = self._usos_de_la_noche
        return self._arrancar(Servicio.REPONER_AUDIO)

    def sonar_audio(self, animatronics=()) -> Resultado:
        """Reproduce el audio de Quico desde el monitor de cámaras.

        No manda a Doña Florinda de vuelta a su casa: le quita una cámara de
        terreno, esté donde esté. Por eso hay que usarlo varias veces, y por
        eso deja de servir cuando ella ya llegó a la reja, que es desde donde
        su recorrido ya no retrocede.

        A diferencia de los cuatro servicios del panel, no deja al jugador
        ocupado: se usa desde las cámaras y tiene que poder encadenarse.
        """
        if not self.audio_ilimitado:
            if self.usos_audio <= 0:
                return Resultado.SIN_USOS
            self.usos_audio -= 1

        florinda = self._buscar(animatronics, nombres.FLORINDA)
        if florinda is None or not florinda.retroceder():
            return Resultado.SONO
        return Resultado.AHUYENTADO

    def _restablecer_todo(self) -> Resultado:
        self.usos_audio = self._usos_de_la_noche
        return self._arrancar(Servicio.TODO)

    def _arrancar(self, servicio: Servicio) -> Resultado:
        self._en_marcha = servicio
        self._total = DURACIONES[servicio]
        self._restante = self._total
        return Resultado.EN_MARCHA

    @staticmethod
    def _acechando(animatronics, nombre: str):
        for animatronic in animatronics:
            if animatronic.nombre == nombre and animatronic.esta_acechando():
                return animatronic
        return None

    @staticmethod
    def _buscar(animatronics, nombre: str):
        """El del elenco que se llame así, esté donde esté. El audio de Quico
        alcanza a Doña Florinda en cualquier cámara, no solo encima."""
        for animatronic in animatronics:
            if animatronic.nombre == nombre and animatronic.activo:
                return animatronic
        return None

    # ------------------------------------------------------------------
    # Paso del tiempo
    # ------------------------------------------------------------------
    def actualizar(self, dt: float, jugador_escondido: bool) -> Optional[Servicio]:
        """Descuenta esperas. Devuelve el servicio que acaba de terminar, si
        alguno, para que quien corresponda aplique su efecto (arreglar las
        cámaras, por ejemplo).

        `jugador_escondido` dice si está dentro del barril en este preciso
        fotograma: el Sr. Barriga no puede tocarlo ahí, así que si el plazo
        se cumple estando escondido se queda esperando en vez de atraparlo,
        y solo lo atrapa el fotograma en que deja de estarlo."""
        self.barriga_letal = False
        if self._espera_barriga > 0.0:
            self._espera_barriga = max(0.0, self._espera_barriga - dt)

        if self._barriga_por_llegar > 0.0:
            self._barriga_por_llegar = max(0.0, self._barriga_por_llegar - dt)
            if self._barriga_por_llegar <= 0.0:
                self._barriga_esperando = True

        if self._barriga_esperando and not jugador_escondido:
            self.barriga_letal = True
            self._barriga_esperando = False

        if self._en_marcha is None:
            return None

        self._restante -= dt
        if self._restante > 0.0:
            return None

        terminado = self._en_marcha
        self._en_marcha = None
        self._restante = 0.0
        self._total = 0.0
        return terminado

    def reiniciar(self, numero_noche: int):
        self.audio_ilimitado = numero_noche < NOCHE_AUDIO_LIMITADO
        self.usos_audio = usos_de_audio(numero_noche)
        self._usos_de_la_noche = self.usos_audio
        self._en_marcha = None
        self._restante = 0.0
        self._total = 0.0
        self._espera_barriga = 0.0
        self._barriga_por_llegar = 0.0
        self._barriga_esperando = False
        self.barriga_letal = False
