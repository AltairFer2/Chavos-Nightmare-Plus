"""Regenera docs/ESCENAS_CAMARAS.md con las escenas de cámara que faltan.

    python tools/escenas_pendientes.py

Compara lo que ya hay dibujado en assets/camaras/ contra lo que los recorridos
del elenco permiten que ocurra, y escribe la lista de archivos pendientes.
Conviene volver a lanzarlo cada vez que se dibujen escenas nuevas o se toque
un recorrido en dominio/animatronicos/elenco.py.
"""

import os
import sys
from itertools import combinations
from pathlib import Path

# Sin ventana ni audio: solo se leen nombres de archivo.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from vecindad.dominio.animatronicos import (  # noqa: E402
    habitaciones_que_se_dibujan,
    nombres,
    prefijos_por_nombre,
)
from vecindad.mundo.habitaciones import HABITACIONES, nombre_de_escena  # noqa: E402
from vecindad.presentacion.escenas_camara import CatalogoEscenas  # noqa: E402

DESTINO = RAIZ / "docs" / "ESCENAS_CAMARAS.md"


def main() -> int:
    catalogo = CatalogoEscenas()
    prefijos = prefijos_por_nombre()
    posibles = habitaciones_que_se_dibujan()
    orden = list(prefijos.values())

    def ordenar(grupo):
        return [p for p in orden if p in grupo]

    def faltantes(habitacion, tamanos):
        pueden = {prefijos[n] for n in posibles.get(habitacion.id, [])}
        hechas = set(catalogo.grupos_de(habitacion.id))
        return [
            frozenset(combo)
            for k in tamanos
            if k <= len(pueden)
            for combo in combinations(sorted(pueden), k)
            if frozenset(combo) not in hechas
        ]

    def seccion(titulo, tamanos, nota):
        lineas, total = [], 0
        cuerpo = []
        for habitacion in HABITACIONES.values():
            if habitacion.solo_audio:
                continue
            pendientes = faltantes(habitacion, tamanos)
            if not pendientes:
                continue
            cuerpo.append(f"### {habitacion.nombre}\n")
            cuerpo.append(
                f"`assets/camaras/{habitacion.carpeta_camara}/` — "
                f"{len(pendientes)} archivos\n"
            )
            cuerpo.append("```")
            for grupo in sorted(pendientes, key=lambda g: (len(g), sorted(g))):
                cuerpo.append(f"{nombre_de_escena(ordenar(grupo))}.png")
                total += 1
            cuerpo.append("```\n")
        lineas.append(f"\n## {titulo}\n")
        lineas.append(f"**{total} archivos.**\n")
        lineas.append(nota + "\n")
        return lineas + cuerpo, total

    doc = [
        "# Escenas de cámara pendientes\n",
        "Cada cámara muestra una imagen distinta según quién esté dentro. Este",
        "documento lista qué archivos faltan por dibujar.\n",
        "> Generado con `python tools/escenas_pendientes.py`. No editar a mano.\n",
        "## Cómo se nombran\n",
        "Dentro de la carpeta de cada cámara, junto a `cam N.png`:\n",
        "- Los nombres cortos, separados por espacios y el último con ` y `:",
        "  `ramon y chavo.png`, `ramon chilindrina y chavo.png`.",
        "- **El orden da igual**: `quico y chavo.png` y `chavo y quico.png` son",
        "  lo mismo. Las tildes, las mayúsculas y las comas tampoco importan,",
        "  así que `florinda, chavo y ramón.png` también vale.",
        "- `todos.png` es el atajo para la escena con los siete dentro.",
        "- Para varias versiones del mismo grupo, sufijo numérico:",
        "  `ramon y chilindrina 2.png`. Se elige una al azar y se mantiene",
        "  mientras ese grupo no cambie.",
        "- `cam N.png` es la habitación vacía, y es lo que se ve sin nadie dentro.\n",
        "Nombres cortos válidos:\n",
    ]
    doc += [f"- **{p}** — {n}" for n, p in prefijos.items()]
    doc.append("")
    doc += [
        f"- **{alias}** — otra forma de escribir `{oficial}`"
        for alias, oficial in sorted(nombres.ALIAS_EN_ESCENAS.items())
    ]
    doc += [
        "\n## No hace falta dibujarlas todas\n",
        "Si falta la imagen exacta de un grupo, el juego usa la del subconjunto",
        "más grande que sí exista, y si no hay ninguna, la habitación vacía.",
        "Nunca enseña a alguien que no esté: como mucho, enseña de menos. Por",
        "eso conviene empezar por los personajes solos y seguir por las parejas.\n",
    ]

    paso1, total1 = seccion(
        "Paso 1: personajes solos y en pareja",
        (1, 2),
        "Con esto el juego se ve bien en casi todo momento: los grupos de tres\n"
        "o más caen a la pareja que sí exista.",
    )
    paso2, total2 = seccion(
        "Paso 2: grupos de tres o más",
        range(3, len(prefijos) + 1),
        "Opcional, y solo si se quiere que los cruces grandes se vean exactos.",
    )
    doc += paso1 + paso2

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text("\n".join(doc), encoding="utf-8")
    print(f"{DESTINO.relative_to(RAIZ)}: {total1} del paso 1, {total2} del paso 2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
