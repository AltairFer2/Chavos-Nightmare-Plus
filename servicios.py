"""Servicios de utilidad que el jugador maneja desde dentro del barril.

Son cuatro y cada uno tarda lo suyo: mientras un servicio está en marcha no
se puede lanzar otro, y ese rato de espera es justo lo que hace peligroso
usarlos con alguien encima.

1. Llamar al Señor Barriga. Es lo único que quita a Don Ramón de encima,
   pero llamarlo cuando Don Ramón no está acechando le cuesta la vida al
   jugador: el Sr. Barriga viene a cobrar la renta y no se anda con rodeos.
   Queda en espera unos segundos tras cada llamada.
2. Audio de Quico. Ahuyenta a Doña Florinda. La primera noche se puede usar
   sin límite; a partir de la segunda solo quedan cuatro reproducciones y,
   una vez gastadas, hay que reponerlas con "Restablecer todo".
3. Restablecer cámaras. Necesario cuando El Chavo las arruina por mirarlo
   demasiado rato.
4. Restablecer todo. Repone de una vez el audio de Quico y las cámaras, a
   cambio de dejar al jugador ocupado bastante más tiempo.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

from constants import (
    BARRIGA_COOLDOWN_SEGUNDOS,
    NOCHE_AUDIO_LIMITADO,
    SERVICIO_AUDIO_SEGUNDOS,
    SERVICIO_CAMARAS_SEGUNDOS,
    SERVICIO_TODO_SEGUNDOS,
    USOS_AUDIO_QUICO,
)


class Servicio(Enum):
    BARRIGA = auto()
    AUDIO_QUICO = auto()
    CAMARAS = auto()
    TODO = auto()


class Resultado(Enum):
    """Qué salió de intentar usar un servicio."""

    OCUPADO = auto()  # hay otro servicio en marcha, o este está en espera
    SIN_USOS = auto()  # el audio de Quico se agotó
    EN_MARCHA = auto()  # arrancó y tardará sus segundos
    LLAMADA_EN_VANO = auto()  # se llamó al Sr. Barriga sin Don Ramón delante
    AHUYENTADO = auto()  # el servicio se llevó a quien tenía que llevarse


# Cuánto tarda cada servicio en completarse.
DURACIONES = {
    Servicio.BARRIGA: 0.0,  # la llamada es inmediata; lo que queda es la espera
    Servicio.AUDIO_QUICO: SERVICIO_AUDIO_SEGUNDOS,
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
    audio_ilimitado: bool = False


class ServiciosUtilidad:
    """Estado de los cuatro servicios durante una noche."""

    def __init__(self, numero_noche: int = 1):
        self.audio_ilimitado = numero_noche < NOCHE_AUDIO_LIMITADO
        self.usos_audio = USOS_AUDIO_QUICO
        self._en_marcha: Optional[Servicio] = None
        self._restante = 0.0
        self._total = 0.0
        self._espera_barriga = 0.0

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
        if servicio is Servicio.AUDIO_QUICO:
            return self.audio_ilimitado or self.usos_audio > 0
        return True

    def estado(self) -> EstadoServicios:
        return EstadoServicios(
            en_marcha=self._en_marcha,
            restante=self._restante,
            total=self._total,
            espera_barriga=self._espera_barriga,
            usos_audio=self.usos_audio,
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
        if servicio is Servicio.AUDIO_QUICO:
            return self._sonar_audio(animatronics)
        if servicio is Servicio.CAMARAS:
            return self._arrancar(servicio)
        return self._restablecer_todo()

    def _llamar_barriga(self, animatronics) -> Resultado:
        if self._espera_barriga > 0.0:
            return Resultado.OCUPADO

        self._espera_barriga = BARRIGA_COOLDOWN_SEGUNDOS
        ramon = self._acechando(animatronics, "Don Ramón")
        if ramon is None:
            return Resultado.LLAMADA_EN_VANO
        ramon.ahuyentar()
        return Resultado.AHUYENTADO

    def _sonar_audio(self, animatronics) -> Resultado:
        if not self.audio_ilimitado:
            if self.usos_audio <= 0:
                return Resultado.SIN_USOS
            self.usos_audio -= 1

        self._arrancar(Servicio.AUDIO_QUICO)
        florinda = self._acechando(animatronics, "Doña Florinda")
        if florinda is None:
            return Resultado.EN_MARCHA
        florinda.ahuyentar()
        return Resultado.AHUYENTADO

    def _restablecer_todo(self) -> Resultado:
        self.usos_audio = USOS_AUDIO_QUICO
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

    # ------------------------------------------------------------------
    # Paso del tiempo
    # ------------------------------------------------------------------
    def actualizar(self, dt: float) -> Optional[Servicio]:
        """Descuenta esperas. Devuelve el servicio que acaba de terminar, si
        alguno, para que quien corresponda aplique su efecto (arreglar las
        cámaras, por ejemplo)."""
        if self._espera_barriga > 0.0:
            self._espera_barriga = max(0.0, self._espera_barriga - dt)

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
        self.usos_audio = USOS_AUDIO_QUICO
        self._en_marcha = None
        self._restante = 0.0
        self._total = 0.0
        self._espera_barriga = 0.0
