"""Objetos del juego: catálogo, contrarrestos y aparición en el suelo.

Hay tres clases de objeto:

- Los seis defensivos (paleta, pelota cuadrada, pelota redonda, balero,
  chipote chillón y churrumino). Hay un único ejemplar de cada uno por
  noche: se encuentra tirado en la Entrada o en los Lavaderos y, una vez
  arrojado, ya no vuelve a aparecer. Gastar el equivocado deja al jugador
  sin respuesta para quien sí lo necesitaba: ese es el riesgo central.
- El café, que no se arroja: se combina con el churrumino para preparar el
  café con churrumino, lo único que calma a Jaimico.
- Las baterías de linterna, que sí reaparecen durante toda la noche.

Cada objeto conoce su celda dentro de la rejilla de assets/ui/objetos.png
(ver presentacion/iconos.py) y a quién elimina al arrojarse.
"""

import random
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from ..config.jugabilidad import (
    NOCHE_SIN_BATERIAS_FIJAS,
    OBJETO_INTERVALO_APARICION_SEGUNDOS,
    OBJETO_PROBABILIDAD_BASE,
    OBJETO_PROBABILIDAD_MINIMA,
    OBJETO_REDUCCION_POR_NOCHE,
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
    # A quién elimina si se le arroja, en orden de prioridad: se resuelve
    # sobre el primero de la lista que esté presente y lo acepte.
    elimina: Tuple[str, ...] = ()
    arrojable: bool = False


CATALOGO: Dict[str, Objeto] = {
    ID_PALETA: Objeto(
        id=ID_PALETA, clave_texto="objeto_paleta", celda=(0, 0),
        elimina=("La Chilindrina", "El Chavo"), arrojable=True,
    ),
    ID_PELOTA_CUADRADA: Objeto(
        id=ID_PELOTA_CUADRADA, clave_texto="objeto_pelota_cuadrada", celda=(1, 0),
        elimina=("Quico", "El Chavo"), arrojable=True,
    ),
    ID_PELOTA_REDONDA: Objeto(
        id=ID_PELOTA_REDONDA, clave_texto="objeto_pelota_redonda", celda=(2, 0),
        elimina=("Quico", "El Chavo"), arrojable=True,
    ),
    ID_BALERO: Objeto(
        id=ID_BALERO, clave_texto="objeto_balero", celda=(0, 1),
        elimina=("La Chilindrina", "El Chavo"), arrojable=True,
    ),
    ID_CHIPOTE: Objeto(
        id=ID_CHIPOTE, clave_texto="objeto_chipote", celda=(1, 1),
        elimina=("El Chavo",), arrojable=True,
    ),
    # Arrojado solo no mata a nadie: únicamente El Chavo lo detecta y se
    # entretiene con él unos segundos.
    ID_CHURRUMINO: Objeto(
        id=ID_CHURRUMINO, clave_texto="objeto_churrumino", celda=(2, 1),
        arrojable=True,
    ),
    ID_CAFE: Objeto(id=ID_CAFE, clave_texto="objeto_cafe", celda=(0, 2)),
    ID_BATERIA: Objeto(id=ID_BATERIA, clave_texto="objeto_bateria", celda=(1, 2)),
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

# Objetos de los que solo hay uno por noche: cuando aparecen, se retiran de
# la bolsa y ya no vuelven a salir.
OBJETOS_UNICOS: Tuple[str, ...] = OBJETOS_DEFENSIVOS + (ID_CAFE,)


def obtener_objeto(id_objeto: str) -> Objeto:
    try:
        return CATALOGO[id_objeto]
    except KeyError as error:
        raise ValueError(f"Objeto desconocido: {id_objeto}") from error


class ObjetosEnElSuelo:
    """Qué hay tirado en cada sitio y cuándo aparece algo nuevo.

    Cada sitio sostiene un objeto a la vez. Cada cierto rato, un sitio vacío
    tira su probabilidad; si sale, aparece un objeto de la bolsa de únicos
    que queden por salir o, si ya salieron todos, una batería.
    """

    def __init__(self, numero_noche: int):
        self.probabilidad = self._probabilidad_de_la_noche(numero_noche)
        self._objetos: Dict[str, Optional[str]] = {
            id_posicion: None for id_posicion in POSICIONES_CON_OBJETOS
        }
        self._por_aparecer = list(OBJETOS_UNICOS)
        random.shuffle(self._por_aparecer)
        self._tiempo_para_sorteo = OBJETO_INTERVALO_APARICION_SEGUNDOS

    @staticmethod
    def _probabilidad_de_la_noche(numero_noche: int) -> float:
        noches_de_escasez = max(0, numero_noche - (NOCHE_SIN_BATERIAS_FIJAS - 1))
        return max(
            OBJETO_PROBABILIDAD_MINIMA,
            OBJETO_PROBABILIDAD_BASE - OBJETO_REDUCCION_POR_NOCHE * noches_de_escasez,
        )

    def actualizar(self, dt: float):
        self._tiempo_para_sorteo -= dt
        if self._tiempo_para_sorteo > 0.0:
            return
        self._tiempo_para_sorteo = OBJETO_INTERVALO_APARICION_SEGUNDOS
        for id_posicion, objeto in self._objetos.items():
            if objeto is None and random.random() < self.probabilidad:
                self._objetos[id_posicion] = self._siguiente_objeto()

    def _siguiente_objeto(self) -> str:
        """Saca un único de la bolsa mientras queden; después, baterías."""
        if self._por_aparecer:
            return self._por_aparecer.pop()
        return ID_BATERIA

    def objeto_en(self, id_posicion: str) -> Optional[str]:
        return self._objetos.get(id_posicion)

    def recoger(self, id_posicion: str) -> Optional[str]:
        """Levanta lo que haya en ese sitio y lo deja vacío."""
        objeto = self._objetos.get(id_posicion)
        if objeto is not None:
            self._objetos[id_posicion] = None
        return objeto
