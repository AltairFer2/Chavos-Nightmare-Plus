"""Mapa de habitaciones (grafo de cámaras) de la vecindad.

El grafo refleja la distribución física real: el Primer Patio conecta con
la Entrada y con las cuatro casas de su grupo, y sube por una escalera al
Segundo Patio, que a su vez conecta con las casas de su propio grupo.
"Casa del Chavo" no tiene lente de cámara, solo micrófono (solo_audio=True).

El jugador se ubica físicamente en el Primer Patio (HABITACION_JUGADOR),
junto a la reja de la Entrada.

Cada habitación guarda su propio nombre de carpeta dentro de
assets/camaras/, siguiendo la nomenclatura "Cámara <número> - <Nombre>"
definida por el propietario del proyecto. Dentro de esa carpeta se espera
un archivo "Cam <número> Selected.png" con la vista de esa cámara.
"""

from dataclasses import dataclass, field
from typing import Dict, List

from constants import DIR_ASSETS_CAMARAS


@dataclass(frozen=True)
class Habitacion:
    id: str
    nombre: str
    numero_camara: str
    carpeta_camara: str
    conexiones: List[str] = field(default_factory=list)
    solo_audio: bool = False

    @property
    def carpeta_assets(self):
        return DIR_ASSETS_CAMARAS / self.carpeta_camara

    @property
    def archivo_seleccionada(self) -> str:
        return f"Cam {self.numero_camara} Selected.png"


HABITACIONES: Dict[str, Habitacion] = {
    "entrada": Habitacion(
        id="entrada",
        nombre="Entrada",
        numero_camara="3",
        carpeta_camara="Cámara 3 - Entrada",
        conexiones=["primer_patio"],
    ),
    "primer_patio": Habitacion(
        id="primer_patio",
        nombre="Primer Patio",
        numero_camara="1",
        carpeta_camara="Cámara 1 - Primer Patio",
        conexiones=[
            "entrada",
            "casa_jaimito",
            "casa_clotilde",
            "casa_florinda",
            "casa_ramon",
            "segundo_patio",
        ],
    ),
    "casa_jaimito": Habitacion(
        id="casa_jaimito",
        nombre="Casa de Jaimito el Cartero",
        numero_camara="23",
        carpeta_camara="Cámara 23 - Casa de Jaimito el Cartero",
        conexiones=["primer_patio"],
    ),
    "casa_clotilde": Habitacion(
        id="casa_clotilde",
        nombre="Casa de Doña Clotilde (Bruja del 71)",
        numero_camara="71",
        carpeta_camara="Cámara 71 - Casa de Doña Clotilde",
        conexiones=["primer_patio"],
    ),
    "casa_florinda": Habitacion(
        id="casa_florinda",
        nombre="Casa de Doña Florinda",
        numero_camara="14",
        carpeta_camara="Cámara 14 - Casa de Doña Florinda",
        conexiones=["primer_patio"],
    ),
    "casa_ramon": Habitacion(
        id="casa_ramon",
        nombre="Casa de Don Ramón",
        numero_camara="72",
        carpeta_camara="Cámara 72 - Casa de Don Ramón",
        conexiones=["primer_patio"],
    ),
    "segundo_patio": Habitacion(
        id="segundo_patio",
        nombre="Segundo Patio",
        numero_camara="2",
        carpeta_camara="Cámara 2 - Segundo Patio",
        conexiones=[
            "primer_patio",
            "casa_paty",
            "casa_godinez",
            "casa_popis",
            "casa_chavo",
        ],
    ),
    "casa_paty": Habitacion(
        id="casa_paty",
        nombre="Casa de Paty",
        numero_camara="84",
        carpeta_camara="Cámara 84 - Casa de Paty",
        conexiones=["segundo_patio"],
    ),
    "casa_godinez": Habitacion(
        id="casa_godinez",
        nombre="Casa de Godínez",
        numero_camara="82",
        carpeta_camara="Cámara 82 - Casa de Godinez",
        conexiones=["segundo_patio"],
    ),
    "casa_popis": Habitacion(
        id="casa_popis",
        nombre="Casa de la Popis",
        numero_camara="97",
        carpeta_camara="Cámara 97 - Casa de la Popis",
        conexiones=["segundo_patio"],
    ),
    "casa_chavo": Habitacion(
        id="casa_chavo",
        nombre="Casa del Chavo",
        numero_camara="8",
        carpeta_camara="Cámara 8 - Casa del Chavo",
        conexiones=["segundo_patio"],
        solo_audio=True,
    ),
}

# Habitación donde se encuentra físicamente el jugador (el barril, junto a la
# reja de la Entrada, dentro del Primer Patio). No es una cámara en sí misma,
# pero sirve de referencia para la IA de los animatrónicos y las condiciones
# de victoria/derrota.
HABITACION_JUGADOR = "primer_patio"


def obtener_habitacion(id_habitacion: str) -> Habitacion:
    try:
        return HABITACIONES[id_habitacion]
    except KeyError as error:
        raise ValueError(f"Habitación desconocida: {id_habitacion}") from error


def son_adyacentes(id_a: str, id_b: str) -> bool:
    return id_b in obtener_habitacion(id_a).conexiones
