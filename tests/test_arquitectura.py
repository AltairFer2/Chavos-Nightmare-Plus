"""Comprueba que las capas siguen respetando sus dependencias.

Es la prueba que convierte la arquitectura de docs/ARQUITECTURA.md en algo
verificable: si alguien importa pygame dentro del dominio o hace que config
dependa del juego, esto falla y se ve en el momento, no tres meses después.
"""

import ast
from pathlib import Path

import pytest

RAIZ_PAQUETE = Path(__file__).resolve().parents[1] / "src" / "vecindad"

# Qué puede importar cada capa, además de sí misma y de la librería estándar.
DEPENDENCIAS_PERMITIDAS = {
    "config": set(),
    "i18n": {"config"},
    "mundo": {"config"},
    "dominio": {"config", "mundo"},
    "infraestructura": {"config", "i18n"},
    "presentacion": {"config", "i18n", "mundo", "dominio", "infraestructura"},
    "app": {
        "config", "i18n", "mundo", "dominio", "infraestructura", "presentacion",
    },
}

# Capas que no pueden tocar pygame bajo ningún concepto.
CAPAS_SIN_PYGAME = ("config", "i18n", "mundo", "dominio")


def modulos_de(capa: str):
    """Todos los .py de una capa, con su ruta relativa para los mensajes."""
    carpeta = RAIZ_PAQUETE / capa
    return sorted(carpeta.rglob("*.py"))


def imports_de(archivo: Path):
    """Los módulos que importa un archivo, como cadenas tal cual aparecen.

    Los imports relativos se devuelven normalizados a la capa a la que
    apuntan, para poder compararlos con DEPENDENCIAS_PERMITIDAS.
    """
    arbol = ast.parse(archivo.read_text(encoding="utf-8"))
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                yield alias.name.split(".")[0]
        elif isinstance(nodo, ast.ImportFrom):
            if nodo.level == 0:
                yield (nodo.module or "").split(".")[0]
            else:
                # Relativo: se resuelve contra la posición real del archivo
                # para saber a qué capa apunta.
                partes = archivo.relative_to(RAIZ_PAQUETE).parts[:-1]
                base = partes[: len(partes) - (nodo.level - 1)]
                destino = list(base) + ((nodo.module or "").split(".") if nodo.module else [])
                yield destino[0] if destino else ""


@pytest.mark.parametrize("capa", CAPAS_SIN_PYGAME)
def test_las_capas_puras_no_importan_pygame(capa):
    """La regla que sostiene todo lo demás: sin pygame, el dominio se puede
    probar sin abrir una ventana."""
    culpables = [
        archivo.relative_to(RAIZ_PAQUETE).as_posix()
        for archivo in modulos_de(capa)
        if "pygame" in set(imports_de(archivo))
    ]
    assert not culpables, f"{capa}/ no puede importar pygame: {culpables}"


@pytest.mark.parametrize("capa", sorted(DEPENDENCIAS_PERMITIDAS))
def test_cada_capa_solo_importa_de_las_de_abajo(capa):
    permitidas = DEPENDENCIAS_PERMITIDAS[capa] | {capa}
    capas = set(DEPENDENCIAS_PERMITIDAS)
    infracciones = []

    for archivo in modulos_de(capa):
        for importado in imports_de(archivo):
            if importado in capas and importado not in permitidas:
                infracciones.append(
                    f"{archivo.relative_to(RAIZ_PAQUETE).as_posix()} -> {importado}"
                )

    assert not infracciones, (
        f"{capa}/ solo puede importar de {sorted(permitidas)}: {infracciones}"
    )


def test_todas_las_capas_declaradas_existen():
    """Si se añade una carpeta de capa nueva hay que declararla arriba, para
    que no quede fuera de la comprobación sin que nadie se entere."""
    en_disco = {
        carpeta.name
        for carpeta in RAIZ_PAQUETE.iterdir()
        if carpeta.is_dir() and not carpeta.name.startswith("__")
    }
    assert en_disco == set(DEPENDENCIAS_PERMITIDAS)
