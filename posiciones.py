"""Posiciones donde puede pararse el jugador durante la noche.

No son cámaras: son los cuatro sitios físicos por los que se mueve el jugador
dentro del Primer Patio. El mapa es una línea horizontal con un nivel
inferior (el interior del barril):

    Lavaderos  <->  Barril  <->  Entrada
                      |
                 Dentro del Barril

Desde el Barril el jugador ve el patio asomado por fuera; puede caminar a un
lado o a otro para buscar objetos, o bajar a esconderse dentro del barril,
que es el único sitio desde el que se usan las cámaras y los servicios.

Cada posición nombra su propio archivo de fondo dentro de assets/ui/. Si el
archivo todavía no existe, la vista dibuja un respaldo sin fallar (igual que
el sistema de cámaras).
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from constants import DIR_ASSETS_UI, OSCURIDAD_DENTRO_BARRIL, OSCURIDAD_OPACIDAD

POSICION_LAVADEROS = "lavaderos"
POSICION_BARRIL = "barril"
POSICION_ENTRADA = "entrada"
POSICION_DENTRO_BARRIL = "dentro_barril"

# Posición en la que arranca la noche: asomado por fuera del barril.
POSICION_INICIAL = POSICION_BARRIL


@dataclass(frozen=True)
class PosicionJugador:
    id: str
    nombre: str
    archivo_fondo: str
    izquierda: Optional[str] = None
    derecha: Optional[str] = None
    abajo: Optional[str] = None
    arriba: Optional[str] = None
    permite_buscar: bool = False
    es_refugio: bool = False
    # Punto del lienzo donde se dibuja el objeto tirado en esta posición.
    # Solo se usa cuando permite_buscar es True.
    punto_objeto: Tuple[int, int] = (640, 540)
    # Cuánta penumbra tapa la escena. Fuera del barril es casi total y solo
    # la linterna abre hueco; dentro, como la linterna no se puede encender,
    # tiene que entrar algo de luna por la boca del barril.
    oscuridad: int = OSCURIDAD_OPACIDAD

    @property
    def ruta_fondo(self):
        return DIR_ASSETS_UI / self.archivo_fondo


POSICIONES: Dict[str, PosicionJugador] = {
    POSICION_LAVADEROS: PosicionJugador(
        id=POSICION_LAVADEROS,
        nombre="Lavaderos",
        archivo_fondo="lavadero.png",
        derecha=POSICION_BARRIL,
        permite_buscar=True,
        punto_objeto=(520, 545),
    ),
    POSICION_BARRIL: PosicionJugador(
        id=POSICION_BARRIL,
        nombre="Barril",
        # Vista asomado por fuera del barril, mirando el Primer Patio.
        archivo_fondo="inicio.png",
        izquierda=POSICION_LAVADEROS,
        derecha=POSICION_ENTRADA,
        abajo=POSICION_DENTRO_BARRIL,
    ),
    POSICION_ENTRADA: PosicionJugador(
        id=POSICION_ENTRADA,
        nombre="Entrada",
        archivo_fondo="entrada.png",
        izquierda=POSICION_BARRIL,
        permite_buscar=True,
        punto_objeto=(760, 545),
    ),
    POSICION_DENTRO_BARRIL: PosicionJugador(
        id=POSICION_DENTRO_BARRIL,
        nombre="Dentro del Barril",
        # Vista desde el fondo del barril, con la boca arriba.
        archivo_fondo="barril.png",
        arriba=POSICION_BARRIL,
        es_refugio=True,
        oscuridad=OSCURIDAD_DENTRO_BARRIL,
    ),
}

# Sitios donde pueden aparecer objetos tirados para que el jugador los
# recoja. Se deriva del mapa para no repetir la lista a mano.
POSICIONES_CON_OBJETOS = tuple(
    posicion.id for posicion in POSICIONES.values() if posicion.permite_buscar
)


def obtener_posicion(id_posicion: str) -> PosicionJugador:
    try:
        return POSICIONES[id_posicion]
    except KeyError as error:
        raise ValueError(f"Posición de jugador desconocida: {id_posicion}") from error
