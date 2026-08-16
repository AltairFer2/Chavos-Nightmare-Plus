"""Revisa las escenas de cámara que hay dibujadas en assets/camaras/.

No comprueba que estén todas (el arte se va completando poco a poco y el
juego funciona igual gracias al respaldo por subconjuntos), sino que las que
existen sean utilizables: que el nombre se entienda y que ese grupo pueda
darse de verdad según los recorridos. Un archivo mal nombrado no rompe nada,
pero se queda mudo para siempre, y eso es difícil de notar jugando.
"""

import pytest

from vecindad.dominio.animatronicos import (
    grupos_de_escena,
    habitaciones_posibles,
    nombres_reconocidos_en_escenas,
    prefijos_por_nombre,
)
from vecindad.mundo.habitaciones import HABITACIONES, leer_nombre_de_escena

RECONOCIDOS = nombres_reconocidos_en_escenas()
GRUPOS = grupos_de_escena()
PREFIJOS = prefijos_por_nombre()

# Los tres archivos que toda carpeta de cámara tiene y que no son escenas.
def _es_archivo_base(nombre: str, numero_camara: str) -> bool:
    return nombre.lower() in {
        f"cam {numero_camara}".lower(),
        f"marco cam {numero_camara}".lower(),
        f"cam {numero_camara} selected".lower(),
        "cam unselected",
    }


def escenas_en_disco():
    """Todos los .png de cada carpeta de cámara que no son archivos base."""
    for habitacion in HABITACIONES.values():
        carpeta = habitacion.carpeta_assets
        if not carpeta.is_dir():
            continue
        for archivo in sorted(carpeta.glob("*.png")):
            if _es_archivo_base(archivo.stem, habitacion.numero_camara):
                continue
            yield habitacion, archivo


CASOS = list(escenas_en_disco())
IDS = [f"{h.numero_camara}/{a.stem}" for h, a in CASOS]


@pytest.mark.skipif(not CASOS, reason="todavía no hay escenas dibujadas")
@pytest.mark.parametrize("habitacion,archivo", CASOS, ids=IDS)
def test_el_nombre_de_cada_escena_se_entiende(habitacion, archivo):
    """Si el nombre no se puede leer, el archivo nunca se mostrará. Suele ser
    una errata en un nombre corto o un personaje sin alias registrado."""
    leido = leer_nombre_de_escena(archivo.stem, RECONOCIDOS, GRUPOS)
    assert leido is not None, (
        f"'{archivo.name}' no se reconoce como escena. Los nombres válidos "
        f"son {sorted(RECONOCIDOS)}"
    )


@pytest.mark.skipif(not CASOS, reason="todavía no hay escenas dibujadas")
@pytest.mark.parametrize("habitacion,archivo", CASOS, ids=IDS)
def test_cada_escena_puede_ocurrir_de_verdad(habitacion, archivo):
    """Una escena con alguien que nunca pasa por esa habitación es trabajo de
    dibujo perdido: hay que ampliar su recorrido en elenco.py o mover la
    imagen a otra cámara."""
    leido = leer_nombre_de_escena(archivo.stem, RECONOCIDOS, GRUPOS)
    if leido is None:
        pytest.skip("el nombre no se entiende; lo cubre la otra prueba")

    grupo, _ = leido
    pueden_estar = {
        PREFIJOS[nombre] for nombre in habitaciones_posibles().get(habitacion.id, [])
    }
    sobran = grupo - pueden_estar
    assert not sobran, (
        f"'{archivo.name}' en {habitacion.nombre}: {sorted(sobran)} no pasa "
        f"nunca por ahí. Ahí solo pueden estar {sorted(pueden_estar)}"
    )


@pytest.mark.skipif(not CASOS, reason="todavía no hay escenas dibujadas")
def test_ninguna_camara_con_solo_audio_tiene_escenas():
    """La Casa del Chavo solo tiene micrófono: nunca se enseña su imagen."""
    con_escenas = {
        habitacion.nombre
        for habitacion, _ in CASOS
        if habitacion.solo_audio
    }
    assert not con_escenas, f"tienen escenas pero no se ven nunca: {con_escenas}"
