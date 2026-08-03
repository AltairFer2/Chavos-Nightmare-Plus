"""Lo que el jugador lleva encima durante la noche.

Solo guarda cuántos ejemplares tiene de cada objeto. De los defensivos nunca
habrá más de uno por noche (así están repartidos en el suelo), pero las
baterías sí se acumulan, de modo que el inventario cuenta unidades en vez de
marcar presencias.

El café y el churrumino se combinan a mano, no solos: juntarlos gasta los
dos y produce el café con churrumino, lo único que calma a Jaimico. Como el
churrumino suelto también sirve para entretener a El Chavo, la decisión de
cuándo combinarlos es del jugador.
"""

from typing import Dict, List

from objetos import ID_CAFE, ID_CAFE_CHURRUMINO, ID_CHURRUMINO, CATALOGO, obtener_objeto

# Orden en que se numeran y se muestran los objetos que se pueden arrojar.
# Es el orden del HUD y el de las teclas 1..N.
ORDEN_ARROJABLES: List[str] = [
    id_objeto for id_objeto, objeto in CATALOGO.items() if objeto.arrojable
]


class Inventario:
    """Cuenta lo que carga el jugador."""

    def __init__(self):
        self._cantidades: Dict[str, int] = {}

    def cantidad(self, id_objeto: str) -> int:
        return self._cantidades.get(id_objeto, 0)

    def tiene(self, id_objeto: str) -> bool:
        return self.cantidad(id_objeto) > 0

    def guardar(self, id_objeto: str):
        obtener_objeto(id_objeto)  # valida que el id exista
        self._cantidades[id_objeto] = self.cantidad(id_objeto) + 1

    def gastar(self, id_objeto: str) -> bool:
        """Quita una unidad. False si no había."""
        if not self.tiene(id_objeto):
            return False
        self._cantidades[id_objeto] -= 1
        return True

    def puede_combinar_cafe(self) -> bool:
        return self.tiene(ID_CAFE) and self.tiene(ID_CHURRUMINO)

    def combinar_cafe(self) -> bool:
        """Prepara el café con churrumino gastando los dos ingredientes."""
        if not self.puede_combinar_cafe():
            return False
        self.gastar(ID_CAFE)
        self.gastar(ID_CHURRUMINO)
        self.guardar(ID_CAFE_CHURRUMINO)
        return True

    def arrojables(self) -> List[str]:
        """Objetos que se pueden arrojar ahora mismo, en el orden del HUD."""
        return [id_objeto for id_objeto in ORDEN_ARROJABLES if self.tiene(id_objeto)]

    def reiniciar(self):
        self._cantidades.clear()
