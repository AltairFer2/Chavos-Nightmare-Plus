"""Los datos con los que trabaja el menú: en qué sección está, qué opción es
cada línea y qué partida se pidió.

Son estructuras puras, sin pygame: el menú no arranca partidas por sí mismo,
deja una SolicitudNoche que la capa de aplicación consume. Así el menú no
necesita conocer la clase Juego.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict

# Claves de EntradaMenu que se controlan con una barra deslizante en vez de
# con texto cíclico. Sus getters/setters viven en Configuracion y GestorAudio.
CLAVES_DESLIZABLES = ("volumen_musica", "volumen_efectos")

# Prefijo de las opciones de la Noche Personalizada, una por personaje:
# "nivel_ia::Don Ramón". El nombre va en la propia clave para no depender de
# la posición de la fila.
PREFIJO_NIVEL_IA = "nivel_ia::"


class SeccionMenu(Enum):
    PRINCIPAL = auto()
    AJUSTES = auto()
    PERSONALIZADA = auto()


@dataclass
class SolicitudNoche:
    """Petición de iniciar una noche, generada al elegir una opción."""

    numero: int
    personalizada: bool = False
    niveles_ia: Dict[str, int] = field(default_factory=dict)


@dataclass
class EntradaMenu:
    """Una línea del menú: su texto normal, el que se muestra al estar
    resaltada y si se puede activar."""

    clave: str
    texto: str
    texto_resaltado: str = ""
    habilitada: bool = True

    def __post_init__(self):
        if not self.texto_resaltado:
            self.texto_resaltado = self.texto

    @property
    def es_deslizable(self) -> bool:
        return self.clave in CLAVES_DESLIZABLES

    @property
    def nombre_personaje(self) -> str:
        """Personaje al que corresponde esta fila en la Noche Personalizada,
        o cadena vacía si no es una de esas filas."""
        if not self.clave.startswith(PREFIJO_NIVEL_IA):
            return ""
        return self.clave[len(PREFIJO_NIVEL_IA):]
