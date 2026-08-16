"""Mapa de habitaciones (grafo de cámaras) de la vecindad.

El grafo refleja la distribución física real: el Primer Patio conecta con
la Entrada y con las cuatro casas de su grupo, y sube por una escalera al
Segundo Patio, que a su vez conecta con las casas de su propio grupo.
"Casa del Chavo" no tiene lente de cámara, solo micrófono (solo_audio=True).

El jugador se ubica físicamente en el Primer Patio (HABITACION_JUGADOR),
junto a la reja de la Entrada.

Cada habitación guarda su propio nombre de carpeta dentro de
assets/camaras/, siguiendo la nomenclatura "Cámara <número> - <Nombre>"
definida por el propietario del proyecto. Dentro de esa carpeta van tres
archivos base:

- "cam <número>.png": la habitación vacía, sin nadie dentro.
- "Marco Cam <número>.png": el marco del monitor (rótulo, REC y fecha), con
  transparencia, que se superpone a la imagen.
- "Cam <número> Selected.png": el mapa de la vecindad con esa cámara
  resaltada, que es el menú de selección del panel.

Además, junto a ellos van las **escenas**: una imagen ya dibujada por cada
grupo de personajes que puede aparecer en esa habitación, nombrada con sus
nombres cortos ("ramon y chilindrina.png", "chavo quico y florinda.png"). El
orden de los nombres dentro del archivo da igual, y se puede añadir " 2",
" 3"... para tener varias versiones del mismo grupo y que se elija una al
azar. Quién puede aparecer en cada habitación se deriva de los recorridos
(ver dominio/animatronicos/elenco.py).

La Casa del Chavo no tiene "cam 8.png" ni escenas porque solo tiene micrófono.
"""

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Mapping, Optional, Sequence, Tuple

from ..config.rutas import DIR_ASSETS_CAMARAS

# Cómo se unen los nombres cortos dentro del nombre de archivo de una escena:
# los primeros con espacios y el último con " y ".
SEPARADOR_FINAL = " y "

# Sufijo de variante al final del nombre: "ramon y chavo 2".
_PATRON_VARIANTE = re.compile(r"^(?P<base>.+?)\s+(?P<numero>\d+)$")


def normalizar_nombre_corto(texto: str) -> str:
    """Deja un nombre corto en su forma comparable: minúsculas y sin tildes.

    Los archivos de assets alternan "ramon" y "ramón" para el mismo personaje,
    a veces dentro de la misma carpeta, así que la tilde no puede decidir si
    dos archivos son el mismo grupo o no.
    """
    descompuesto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")


def nombre_de_escena(prefijos: Sequence[str], variante: int = 1) -> str:
    """Nombre de archivo (sin extensión) de la escena con esos personajes.

    >>> nombre_de_escena(["ramon"])
    'ramon'
    >>> nombre_de_escena(["ramon", "chilindrina", "chavo"])
    'ramon chilindrina y chavo'
    >>> nombre_de_escena(["quico", "chavo"], variante=2)
    'quico y chavo 2'

    La primera variante no lleva número, igual que los archivos ya dibujados.
    """
    if not prefijos:
        return ""
    if len(prefijos) == 1:
        base = prefijos[0]
    else:
        base = f"{' '.join(prefijos[:-1])}{SEPARADOR_FINAL}{prefijos[-1]}"
    return base if variante <= 1 else f"{base} {variante}"


def leer_nombre_de_escena(
    nombre_archivo: str,
    nombres_conocidos: Mapping[str, str],
    grupos_conocidos: Optional[Mapping[str, FrozenSet[str]]] = None,
) -> Optional[Tuple[FrozenSet[str], int]]:
    """Lo contrario: de "chavo quico y florinda 2" saca el grupo y la variante.

    `nombres_conocidos` traduce cada forma que puede aparecer en un archivo,
    ya normalizada, al nombre corto oficial del personaje: sirve tanto para el
    nombre propio ("clotilde") como para sus alias ("bruja").

    `grupos_conocidos` son atajos que valen por varios personajes de una vez,
    como "todos", para no tener que escribir los siete nombres seguidos.

    Devuelve el conjunto de nombres cortos oficiales y el número de variante,
    o None si el archivo no es una escena (por ejemplo "cam 72" o
    "Marco Cam 72").

    Se devuelve un conjunto y no una lista a propósito: en los assets el orden
    de los nombres no es constante ("quico y chavo" y "chavo quico y florinda"
    conviven), así que lo único fiable es *quiénes* salen, no en qué orden se
    escribieron.
    """
    texto = normalizar_nombre_corto(nombre_archivo.strip())
    variante = 1

    coincidencia = _PATRON_VARIANTE.match(texto)
    if coincidencia is not None:
        # Ojo: "cam 72" también encaja aquí, pero se descarta más abajo al no
        # ser "72" un nombre de personaje conocido.
        texto = coincidencia.group("base")
        variante = int(coincidencia.group("numero"))

    # La coma es opcional: "florinda, chavo y ramon" es como se escribe una
    # enumeración en español y conviven archivos con ella y sin ella.
    partes = texto.replace(",", " ").replace(SEPARADOR_FINAL, " ").split()
    if not partes:
        return None

    if grupos_conocidos and len(partes) == 1 and partes[0] in grupos_conocidos:
        return grupos_conocidos[partes[0]], variante

    if any(parte not in nombres_conocidos for parte in partes):
        return None

    grupo = frozenset(nombres_conocidos[parte] for parte in partes)
    if len(grupo) != len(partes):  # un personaje repetido no es una escena
        return None
    return grupo, variante


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
    def ruta_vista(self):
        """La habitación vacía: lo que se ve cuando no hay nadie dentro."""
        return self.carpeta_assets / f"cam {self.numero_camara}.png"

    def ruta_escena(self, prefijos: Sequence[str], variante: int = 1):
        """Imagen de esta habitación con ese grupo de personajes dentro."""
        return self.carpeta_assets / f"{nombre_de_escena(prefijos, variante)}.png"

    @property
    def ruta_marco(self):
        """Marco del monitor con el rótulo de esta cámara."""
        return self.carpeta_assets / f"Marco Cam {self.numero_camara}.png"

    @property
    def ruta_mapa(self):
        """Mapa de la vecindad con esta cámara resaltada."""
        return self.carpeta_assets / f"Cam {self.numero_camara} Selected.png"


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
