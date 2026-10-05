"""Objetos del juego: catálogo, contrarrestos y su sitio en el suelo.

Hay tres clases de objeto:

- Los seis defensivos (paleta, pelota cuadrada, pelota redonda, balero,
  chipote chillón y churrumino), que se arrojan a quien corresponda.
- El café, que no se arroja: se combina con el churrumino para preparar el
  café con churrumino, lo único que calma a Jaimico.
- Las baterías de linterna.

Nada sale por sorteo. Cada objeto tiene su sitio fijo en los Lavaderos, la
noche arranca con todos puestos y, al recogerlo, su sitio se queda vacío un
tiempo conocido antes de que vuelva a estar ahí. Lo que castiga usar el
equivocado (o fallar el tiro) es tener que esperar a que vuelva con alguien
delante, y eso el jugador lo puede calcular.

Cada objeto conoce su celda dentro de la rejilla de assets/ui/objetos.png
(ver presentacion/iconos.py) y a quién elimina al arrojarse.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from ..config.jugabilidad import (
    OBJETO_REAPARICION_POR_NOCHE,
    OBJETO_REAPARICION_SEGUNDOS,
)
from ..mundo.posiciones import POSICIONES_CON_OBJETOS

ID_PALETA = "paleta"
ID_PELOTA_CUADRADA = "pelota_cuadrada"
ID_PELOTA_REDONDA = "pelota_redonda"
ID_BALERO = "balero"
ID_CHIPOTE = "chipote"
ID_CHURRUMINO = "churrumino"
ID_CAFE = "cafe"
ID_BATERIA = "bateria"
ID_CAFE_CHURRUMINO = "cafe_churrumino"


@dataclass(frozen=True)
class Objeto:
    id: str
    clave_texto: str  # clave de idiomas.py con el nombre visible
    celda: Tuple[int, int]  # columna y fila dentro de la rejilla de iconos
    # A quién elimina si se le arroja y le da.
    elimina: Tuple[str, ...] = ()
    arrojable: bool = False
    # Dónde aparece siempre en los Lavaderos, en píxeles del lienzo base.
    # None para lo que no se encuentra tirado (el café ya preparado).
    punto_suelo: Optional[Tuple[int, int]] = None


# Los sitios van repartidos por el suelo de los Lavaderos, separados lo
# bastante como para alumbrar uno sin tener encima el de al lado.
CATALOGO: Dict[str, Objeto] = {
    ID_PALETA: Objeto(
        id=ID_PALETA, clave_texto="objeto_paleta", celda=(0, 0),
        elimina=("La Chilindrina", "El Chavo"), arrojable=True,
        punto_suelo=(245, 500),
    ),
    ID_PELOTA_CUADRADA: Objeto(
        id=ID_PELOTA_CUADRADA, clave_texto="objeto_pelota_cuadrada", celda=(1, 0),
        elimina=("Quico", "El Chavo"), arrojable=True,
        punto_suelo=(400, 600),
    ),
    ID_PELOTA_REDONDA: Objeto(
        id=ID_PELOTA_REDONDA, clave_texto="objeto_pelota_redonda", celda=(2, 0),
        elimina=("Quico", "El Chavo"), arrojable=True,
        punto_suelo=(560, 470),
    ),
    ID_BALERO: Objeto(
        id=ID_BALERO, clave_texto="objeto_balero", celda=(0, 1),
        elimina=("La Chilindrina", "El Chavo"), arrojable=True,
        punto_suelo=(640, 620),
    ),
    ID_CHIPOTE: Objeto(
        id=ID_CHIPOTE, clave_texto="objeto_chipote", celda=(1, 1),
        elimina=("El Chavo",), arrojable=True,
        punto_suelo=(760, 470),
    ),
    # Arrojado solo no mata a nadie: únicamente El Chavo lo detecta y se
    # entretiene con él unos segundos.
    ID_CHURRUMINO: Objeto(
        id=ID_CHURRUMINO, clave_texto="objeto_churrumino", celda=(2, 1),
        arrojable=True,
        punto_suelo=(880, 610),
    ),
    ID_CAFE: Objeto(
        id=ID_CAFE, clave_texto="objeto_cafe", celda=(0, 2),
        punto_suelo=(1100, 445),
    ),
    ID_BATERIA: Objeto(
        id=ID_BATERIA, clave_texto="objeto_bateria", celda=(1, 2),
        punto_suelo=(1000, 530),
    ),
    ID_CAFE_CHURRUMINO: Objeto(
        id=ID_CAFE_CHURRUMINO, clave_texto="objeto_cafe_churrumino", celda=(2, 2),
        elimina=("Jaimico",), arrojable=True,
    ),
}

# Los seis defensivos, en el orden en que se muestran y se numeran en el HUD.
OBJETOS_DEFENSIVOS: Tuple[str, ...] = (
    ID_PALETA, ID_PELOTA_CUADRADA, ID_PELOTA_REDONDA,
    ID_BALERO, ID_CHIPOTE, ID_CHURRUMINO,
)

# Todo lo que el jugador puede encontrar tirado: lo que tiene sitio en el
# suelo, en el orden del catálogo.
OBJETOS_QUE_APARECEN: Tuple[str, ...] = tuple(
    id_objeto for id_objeto, objeto in CATALOGO.items()
    if objeto.punto_suelo is not None
)


def obtener_objeto(id_objeto: str) -> Objeto:
    try:
        return CATALOGO[id_objeto]
    except KeyError as error:
        raise ValueError(f"Objeto desconocido: {id_objeto}") from error


def reaparicion_de_la_noche(numero_noche: int) -> float:
    """Segundos que tarda un objeto recogido en volver a su sitio esa noche."""
    return OBJETO_REAPARICION_POR_NOCHE.get(numero_noche, OBJETO_REAPARICION_SEGUNDOS)


class ObjetosEnElSuelo:
    """Qué objetos están ahora mismo en su sitio y cuánto le falta a cada
    uno de los que no para volver.

    La noche arranca con todos puestos. Recoger uno arranca su cuenta; al
    llegar a cero vuelve a estar ahí. Cada objeto lleva su propia cuenta, así
    que gastar la paleta no retrasa al balero.
    """

    def __init__(self, numero_noche: int):
        self.reaparicion = reaparicion_de_la_noche(numero_noche)
        # Segundos que le faltan a cada objeto para volver; 0 es que está.
        self._faltan: Dict[str, float] = {
            id_objeto: 0.0 for id_objeto in OBJETOS_QUE_APARECEN
        }

    def actualizar(self, dt: float):
        for id_objeto, faltan in self._faltan.items():
            if faltan > 0.0:
                self._faltan[id_objeto] = max(0.0, faltan - dt)

    def esta(self, id_objeto: str) -> bool:
        """Si ese objeto está ahora mismo en su sitio."""
        return self._faltan.get(id_objeto) == 0.0

    def segundos_para_volver(self, id_objeto: str) -> float:
        return self._faltan.get(id_objeto, 0.0)

    def objetos_en(self, id_posicion: str) -> Tuple[str, ...]:
        """Los que están en su sitio, si ese es un sitio donde se busca. En
        el resto no hay nada tirado."""
        if id_posicion not in POSICIONES_CON_OBJETOS:
            return ()
        return tuple(
            id_objeto for id_objeto in OBJETOS_QUE_APARECEN if self.esta(id_objeto)
        )

    def recoger(self, id_objeto: str) -> bool:
        """Lo levanta de su sitio y arranca la cuenta para que vuelva. False
        si no estaba."""
        if not self.esta(id_objeto):
            return False
        self._faltan[id_objeto] = self.reaparicion
        return True
