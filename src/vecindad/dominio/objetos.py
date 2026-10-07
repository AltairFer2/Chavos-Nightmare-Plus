"""Lo que se encuentra tirado en los Lavaderos: baterías de linterna.

Antes había objetos para arrojar; ya no. La defensa contra quien no es Don
Ramón ni Doña Florinda es la propia linterna (ver animatronicos/espanto.py),
así que lo único que hace falta buscar es con qué mantenerla encendida.

Nada sale por sorteo: la batería aparece siempre en el mismo sitio y con
tiempos fijos por noche. El suelo queda vacío un rato, aparece una y, si
nadie la recoge, se va al cabo de su permanencia y vuelve a correr la espera.

Cada objeto conoce su celda dentro de la rejilla de assets/ui/objetos.png
(ver presentacion/iconos.py).
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from ..config.jugabilidad import (
    BATERIA_ESPERA_POR_NOCHE,
    BATERIA_ESPERA_SEGUNDOS,
    BATERIA_PERMANENCIA_POR_NOCHE,
    BATERIA_PERMANENCIA_SEGUNDOS,
)
from ..mundo.posiciones import POSICIONES_CON_OBJETOS

ID_BATERIA = "bateria"


@dataclass(frozen=True)
class Objeto:
    id: str
    clave_texto: str  # clave de idiomas.py con el nombre visible
    celda: Tuple[int, int]  # columna y fila dentro de la rejilla de iconos
    # Dónde aparece siempre en los Lavaderos, en píxeles del lienzo base.
    punto_suelo: Tuple[int, int]


CATALOGO: Dict[str, Objeto] = {
    ID_BATERIA: Objeto(
        id=ID_BATERIA, clave_texto="objeto_bateria", celda=(1, 2),
        punto_suelo=(1000, 530),
    ),
}

# Todo lo que el jugador puede encontrar tirado, en el orden del catálogo.
OBJETOS_QUE_APARECEN: Tuple[str, ...] = tuple(CATALOGO)


def obtener_objeto(id_objeto: str) -> Objeto:
    try:
        return CATALOGO[id_objeto]
    except KeyError as error:
        raise ValueError(f"Objeto desconocido: {id_objeto}") from error


def espera_de_la_noche(numero_noche: int) -> float:
    """Segundos que pasa el suelo vacío antes de que aparezca una batería."""
    return BATERIA_ESPERA_POR_NOCHE.get(numero_noche, BATERIA_ESPERA_SEGUNDOS)


def permanencia_de_la_noche(numero_noche: int) -> float:
    """Segundos que se queda tirada una batería si nadie la recoge."""
    return BATERIA_PERMANENCIA_POR_NOCHE.get(numero_noche, BATERIA_PERMANENCIA_SEGUNDOS)


class ObjetosEnElSuelo:
    """La batería que hay tirada ahora mismo, si hay alguna, y cuánto falta
    para que aparezca la siguiente o para que esta se vaya.

    La noche arranca con el suelo vacío. Pasada la espera aparece una; se va
    al recogerla o al cumplirse su permanencia, y entonces vuelve a correr la
    espera. Los tiempos son fijos: el jugador puede aprenderse el ritmo.
    """

    def __init__(self, numero_noche: int):
        self.espera = espera_de_la_noche(numero_noche)
        self.permanencia = permanencia_de_la_noche(numero_noche)
        self._actual: Optional[str] = None
        self._para_aparecer = self.espera
        self._para_irse = 0.0

    @property
    def actual(self) -> Optional[str]:
        """Lo que hay tirado ahora mismo, o None si el suelo está vacío."""
        return self._actual

    def actualizar(self, dt: float):
        if self._actual is None:
            self._para_aparecer -= dt
            if self._para_aparecer <= 0.0:
                self._actual = ID_BATERIA
                self._para_irse = self.permanencia
            return
        self._para_irse -= dt
        if self._para_irse <= 0.0:
            self._vaciar()

    def _vaciar(self):
        self._actual = None
        self._para_aparecer = self.espera
        self._para_irse = 0.0

    def esta(self, id_objeto: str) -> bool:
        """Si ese objeto está ahora mismo en su sitio."""
        return self._actual is not None and self._actual == id_objeto

    def segundos_para_irse(self) -> float:
        """Lo que le queda tirado a lo actual; 0 con el suelo vacío."""
        return self._para_irse if self._actual is not None else 0.0

    def segundos_para_aparecer(self) -> float:
        """Lo que falta para que salga la siguiente; 0 si ya hay una."""
        return self._para_aparecer if self._actual is None else 0.0

    def objetos_en(self, id_posicion: str) -> Tuple[str, ...]:
        """Lo que hay tirado, si ese es un sitio donde se busca. En el resto
        no hay nada."""
        if id_posicion not in POSICIONES_CON_OBJETOS or self._actual is None:
            return ()
        return (self._actual,)

    def recoger(self, id_objeto: str) -> bool:
        """Lo levanta del suelo y arranca la espera de la siguiente. False si
        no estaba."""
        if not self.esta(id_objeto):
            return False
        self._vaciar()
        return True
