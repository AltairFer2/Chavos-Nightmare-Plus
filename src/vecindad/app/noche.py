"""La noche en curso: qué elenco salió, desde qué hora se mueve y, si el
jugador pierde, quién lo atrapó y por qué.

Separa el estado de "esta partida concreta" del bucle principal, que se queda
solo con la orquestación.
"""

from dataclasses import dataclass, field
from typing import List

from ..config.partida import INTERVALO_MOVIMIENTO_POR_DEFECTO
from ..dominio.animatronicos import (
    Animatronic,
    crear_elenco_noche,
    crear_elenco_personalizado,
    hora_de_arranque,
    intervalo_de_movimiento,
)

# Motivo de derrota por defecto: el personaje simplemente llegó hasta el
# jugador. Los demás casos (la luz, el Señor Barriga) lo sustituyen.
MOTIVO_ATRAPADO = "game_over_motivo"


@dataclass
class Derrota:
    """Quién acabó con la noche y con qué texto se explica."""

    nombre_atacante: str = ""
    clave_motivo: str = MOTIVO_ATRAPADO


@dataclass
class Noche:
    """Estado de la noche que se está jugando."""

    numero: int = 1
    personalizada: bool = False
    animatronics: List[Animatronic] = field(default_factory=list)
    # Horas de noche que tienen que pasar antes de que el elenco se mueva.
    hora_arranque: int = 0
    # Segundos entre rondas de movimiento: el ritmo de esta noche.
    intervalo_movimiento: float = INTERVALO_MOVIMIENTO_POR_DEFECTO
    derrota: Derrota = field(default_factory=Derrota)

    @classmethod
    def desde_solicitud(cls, solicitud) -> "Noche":
        """Arma la noche que pidió el menú. La personalizada usa los niveles
        que eligió el jugador, arranca de inmediato y corre al ritmo por
        defecto: ahí la dificultad la pone el propio jugador con los niveles."""
        if solicitud.personalizada:
            return cls(
                numero=solicitud.numero,
                personalizada=True,
                animatronics=crear_elenco_personalizado(solicitud.niveles_ia),
                hora_arranque=0,
                intervalo_movimiento=INTERVALO_MOVIMIENTO_POR_DEFECTO,
            )
        return cls(
            numero=solicitud.numero,
            personalizada=False,
            animatronics=crear_elenco_noche(solicitud.numero),
            hora_arranque=hora_de_arranque(solicitud.numero),
            intervalo_movimiento=intervalo_de_movimiento(solicitud.numero),
        )

    def elenco_en_movimiento(self, horas_transcurridas: int):
        """Los animatrónicos que ya tienen permiso de moverse. Algunas noches
        arrancan más tarde: en la noche 1 nadie se mueve hasta las 2 AM."""
        if horas_transcurridas < self.hora_arranque:
            return ()
        return self.animatronics

    def registrar_derrota(self, nombre: str, clave_motivo: str):
        self.derrota = Derrota(nombre, clave_motivo)
