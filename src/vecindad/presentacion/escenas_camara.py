"""Qué imagen le toca a una cámara según quién esté dentro.

Antes cada personaje se dibujaba como una figura recortada encima del fondo
de la habitación. Ahora cada combinación de personajes tiene su propia imagen
ya compuesta, dibujada aparte, que se muestra entera.

Cómo se eligen
--------------
Al arrancar se lee una vez el contenido de cada carpeta de assets/camaras/ y
se apunta qué escenas hay: de "ramon y chilindrina 2.png" se deduce que
existe el grupo {ramon, chilindrina} en su segunda versión. Se guarda la ruta
tal cual está en disco, sin recomponerla, porque el orden de los nombres
dentro del archivo no es constante: conviven "quico y chavo.png" y
"chavo quico y florinda.png". Lo único que importa es quiénes salen.

Respaldo por subconjuntos
-------------------------
Dibujar todas las combinaciones posibles son cientos de imágenes, así que el
juego no da por hecho que existan. Cuando falta la escena exacta se usa la
del subconjunto más grande que sí exista, y si no hay ninguna, la habitación
vacía. En la práctica: si están Don Ramón y Quico pero solo se dibujó
"ramon.png", se ve a Don Ramón solo. Se pierde a Quico, pero la partida sigue
y el arte se puede ir completando sin tocar código.

Cuando un grupo tiene varias versiones (" 2", " 3"), se elige una al azar y
se mantiene mientras ese grupo no cambie, para que la imagen no parpadee
entre versiones fotograma a fotograma.
"""

import random
from pathlib import Path
from typing import Dict, FrozenSet, List, Optional, Tuple

from ..config.ventana import RESOLUCION_BASE
from ..dominio.animatronicos import (
    grupos_de_escena,
    nombres_reconocidos_en_escenas,
    prefijos_por_nombre,
)
from ..infraestructura.recursos import CacheImagenes
from ..mundo.habitaciones import HABITACIONES, leer_nombre_de_escena

EXTENSION_ESCENA = ".png"

# Una escena dibujada: qué número de versión es y dónde está su archivo.
Version = Tuple[int, Path]


class CatalogoEscenas:
    """Qué escenas hay dibujadas en disco para cada habitación."""

    def __init__(self):
        self._prefijos = prefijos_por_nombre()
        self._reconocidos = nombres_reconocidos_en_escenas()
        self._grupos = grupos_de_escena()
        # {id_habitacion: {grupo: [versiones]}}
        self._por_habitacion: Dict[str, Dict[FrozenSet[str], List[Version]]] = {
            id_habitacion: self._escenas_en(habitacion)
            for id_habitacion, habitacion in HABITACIONES.items()
        }

    def _escenas_en(self, habitacion) -> Dict[FrozenSet[str], List[Version]]:
        """Lee la carpeta de una cámara. Solo se hace al construir."""
        encontradas: Dict[FrozenSet[str], List[Version]] = {}
        carpeta = habitacion.carpeta_assets
        if not carpeta.is_dir():
            return encontradas

        for archivo in sorted(carpeta.glob(f"*{EXTENSION_ESCENA}")):
            leido = leer_nombre_de_escena(
                archivo.stem, self._reconocidos, self._grupos
            )
            if leido is None:
                continue  # archivo base: cam N, Marco Cam N o Cam N Selected
            grupo, numero = leido
            encontradas.setdefault(grupo, []).append((numero, archivo))
        return encontradas

    def grupo_de(self, nombres_presentes) -> FrozenSet[str]:
        """Traduce los nombres completos de los personajes a nombres cortos.
        Quien no esté en el elenco se ignora."""
        return frozenset(
            self._prefijos[nombre]
            for nombre in nombres_presentes
            if nombre in self._prefijos
        )

    def mejor_coincidencia(
        self, id_habitacion: str, grupo: FrozenSet[str]
    ) -> Optional[Tuple[FrozenSet[str], List[Version]]]:
        """La escena dibujada que mejor representa a ese grupo.

        Primero se busca el grupo exacto; si no está, el subconjunto más
        grande que sí exista. Nunca se elige un grupo con alguien que no esté
        realmente en la habitación: como mucho se enseña de menos, nunca de
        más. Devuelve None si no hay nada que sirva.
        """
        disponibles = self._por_habitacion.get(id_habitacion)
        if not disponibles or not grupo:
            return None

        exacto = disponibles.get(grupo)
        if exacto is not None:
            return grupo, exacto

        mejor: Optional[FrozenSet[str]] = None
        for candidato in disponibles:
            if not candidato.issubset(grupo):
                continue
            if mejor is None or len(candidato) > len(mejor):
                mejor = candidato
        if mejor is None:
            return None
        return mejor, disponibles[mejor]

    def grupos_de(self, id_habitacion: str) -> List[FrozenSet[str]]:
        """Los grupos que ya tienen imagen dibujada en esa habitación."""
        return list(self._por_habitacion.get(id_habitacion, {}))


class EscenasCamara:
    """Entrega la imagen que toca dibujar en una cámara."""

    def __init__(self, catalogo: Optional[CatalogoEscenas] = None):
        self._catalogo = catalogo if catalogo is not None else CatalogoEscenas()
        self._imagenes = CacheImagenes(tamano=RESOLUCION_BASE)
        # Qué versión se está enseñando de cada grupo, para no volver a
        # sortearla en cada fotograma. Se olvida en cuanto el grupo cambia.
        self._version_elegida: Dict[Tuple[str, FrozenSet[str]], Version] = {}

    def imagen_para(self, habitacion, nombres_presentes):
        """Imagen ya compuesta de esa habitación con esa gente dentro.

        Devuelve None si no hay ninguna escena que encaje; quien llame decide
        entonces qué enseñar (normalmente, la habitación vacía).
        """
        grupo = self._catalogo.grupo_de(nombres_presentes)
        coincidencia = self._catalogo.mejor_coincidencia(habitacion.id, grupo)
        if coincidencia is None:
            return None

        dibujado, versiones = coincidencia
        numero, ruta = self._version_para(habitacion.id, dibujado, versiones)
        return self._imagenes.obtener(f"{habitacion.id}|{ruta.stem}|{numero}", ruta)

    def _version_para(self, id_habitacion, grupo, versiones: List[Version]) -> Version:
        """Sortea una versión la primera vez y la mantiene mientras el grupo
        siga siendo el mismo, para que la cámara no parpadee."""
        if len(versiones) == 1:
            return versiones[0]
        clave = (id_habitacion, grupo)
        elegida = self._version_elegida.get(clave)
        if elegida not in versiones:
            elegida = random.choice(versiones)
            self._version_elegida[clave] = elegida
        return elegida
