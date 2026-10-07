"""El elenco de la vecindad: la ficha de cada uno de los siete personajes.

Cada personaje tiene su propio grafo de cámaras (ver definicion.py): de dónde
sale y, para cada cámara, a cuáles puede pasar. Los números que aparecen en
los comentarios son los de las cámaras tal como se rotulan en el juego:

    1  Primer Patio (donde está el jugador)   23  Casa de Jaimito
    2  Segundo Patio                          71  Casa de Doña Clotilde
    3  Entrada (la reja)                      72  Casa de Don Ramón
    8  Casa del Chavo (solo micrófono)        82  Casa de Godínez
    14 Casa de Doña Florinda                  84  Casa de Paty
                                              97  Casa de la Popis

Los recorridos son autorales y no todos van en línea recta hacia el jugador:
hay callejones sin salida, vueltas atrás y ciclos completos. Eso hace que la
distancia hasta el Primer Patio no sea fija, así que el ritmo real de una
noche no se lee de la tabla de niveles: se mide simulando (ver
tests/test_progresion.py).

Cada cruce posible entre personajes necesita su propia imagen de cámara (ver
presentacion/escenas_camara.py), así que ampliar un grafo multiplica el arte
pendiente: conviene hacerlo a la vez que se dibuja.

Don Ramón se va con el Sr. Barriga y Doña Florinda retrocede con el audio
de Quico; al resto se le espanta con la linterna (ver dominio/espanto.py).
PENDIENTE: las contramedidas propias que faltan de cada personaje (la escoba
de Doña Clotilde, la irrupción de El Chavo al romper las cámaras).
"""

from typing import Dict, FrozenSet, List, Sequence, Tuple

from ...mundo.habitaciones import (
    HABITACION_JUGADOR,
    HABITACIONES,
    normalizar_nombre_corto,
)
from ...mundo.posiciones import POSICION_BARRIL, POSICION_LAVADEROS, POSICIONES
from . import nombres
from .definicion import POSES_POR_PERSONAJE, ConfiguracionAnimatronic, Destinos


def _deambular(habitaciones: Sequence[str]) -> Dict[str, Destinos]:
    """Grafo donde desde cualquiera de esas cámaras se puede ir a cualquier
    otra. Es el recorrido de El Chavo, que no sigue ninguna ruta."""
    return {
        origen: tuple(destino for destino in habitaciones if destino != origen)
        for origen in habitaciones
    }


# Atajo con el que se nombra la escena en la que salen los siete a la vez,
# para no escribir los siete nombres cortos seguidos en el archivo.
NOMBRE_TODO_EL_ELENCO = "todos"

# Sitios desde los que el jugador mira el patio. Todo el que llegue a la
# cámara 1 tiene que tener su punto en los dos: son el mismo patio visto
# desde dos ángulos, así que desde ninguno de los dos puede volverse
# invisible.
VISTAS_DEL_PATIO: Tuple[str, ...] = (POSICION_BARRIL, POSICION_LAVADEROS)

# Las nueve cámaras por las que El Chavo deambula. No entra a la de Doña
# Clotilde, y al Primer Patio solo llega si el jugador lo mira demasiado
# rato seguido, nunca por su propio dado.
CAMARAS_DEL_CHAVO: Tuple[str, ...] = (
    "casa_chavo",      # 8, donde empieza y donde se le oye
    "casa_ramon",      # 72
    "casa_florinda",   # 14
    "casa_jaimito",    # 23
    "casa_paty",       # 84
    "casa_godinez",    # 82
    "casa_popis",      # 97
    "segundo_patio",   # 2
    "entrada",         # 3
)


ELENCO: Tuple[ConfiguracionAnimatronic, ...] = (
    ConfiguracionAnimatronic(
        nombre=nombres.DON_RAMON,
        # El más directo: de su casa baja por la Popis o por el Segundo Patio
        # y se planta en dos movimientos. Meterse en casa de la bruja (71) es
        # su único desvío, y le cuesta el viaje de vuelta. Cuando el Sr.
        # Barriga se lo lleva, sale por la reja o vuelve a su casa.
        habitacion_inicial="casa_ramon",
        transiciones={
            "casa_ramon":     ("casa_popis", "segundo_patio", "casa_clotilde"),
            "casa_popis":     ("segundo_patio", HABITACION_JUGADOR),
            "segundo_patio":  (HABITACION_JUGADOR,),
            "casa_clotilde":  ("casa_ramon",),
            HABITACION_JUGADOR: ("entrada", "casa_ramon"),
            "entrada":        (HABITACION_JUGADOR, "casa_ramon"),
        },
        puntos_acecho={
            POSICION_BARRIL: (390, 655),
            POSICION_LAVADEROS: (250, 650),
        },
        # El diseño fija su margen: 14 segundos para llamar al Sr. Barriga
        # cuando está en su nivel más bajo.
        espera_ataque_lenta=14.0,
        espera_ataque_rapida=5.0,
        carpeta_sprite="don ramon",
        prefijo_sprite="ramon",
        luz_mortal=True,
        alcanza_escondido=True,
    ),
    ConfiguracionAnimatronic(
        nombre=nombres.QUICO,
        # Sale de casa de su mamá buscando a sus amigos. Al irse del Primer
        # Patio se va por la reja y desde ahí vuelve a empezar.
        habitacion_inicial="casa_florinda",
        transiciones={
            "casa_florinda":  ("casa_paty", "casa_jaimito"),
            "casa_paty":      ("casa_jaimito", "segundo_patio"),
            "casa_jaimito":   (HABITACION_JUGADOR, "segundo_patio"),
            "segundo_patio":  (HABITACION_JUGADOR,),
            HABITACION_JUGADOR: ("entrada",),
            "entrada":        ("casa_florinda", "casa_paty"),
        },
        puntos_acecho={
            POSICION_BARRIL: (900, 660),
            POSICION_LAVADEROS: (900, 655),
        },
        espera_ataque_lenta=14.0,
        espera_ataque_rapida=6.0,
        carpeta_sprite="quico",
        prefijo_sprite="quico",
        se_espanta_con_luz=True,
    ),
    ConfiguracionAnimatronic(
        nombre=nombres.CHILINDRINA,
        # La que más vueltas da: recorre las casas del vecindario en círculo y
        # puede volver sobre sus pasos, así que tarda pero llega desde
        # cualquier lado. Al espantarla se va a su casa.
        habitacion_inicial="casa_ramon",
        transiciones={
            "casa_ramon":     ("casa_clotilde", "casa_paty"),
            "casa_clotilde":  ("casa_paty", "casa_jaimito"),
            "casa_paty":      ("casa_jaimito", "casa_clotilde"),
            "casa_jaimito":   ("segundo_patio", "casa_chavo"),
            "casa_chavo":     ("segundo_patio", "casa_clotilde"),
            "segundo_patio":  (HABITACION_JUGADOR, "casa_ramon"),
            HABITACION_JUGADOR: ("casa_ramon",),
        },
        puntos_acecho={
            POSICION_BARRIL: (760, 650),
            POSICION_LAVADEROS: (330, 645),
        },
        espera_ataque_lenta=14.0,
        espera_ataque_rapida=6.0,
        carpeta_sprite="chilindrina",
        prefijo_sprite="chilindrina",
        # A ella la luz no la mata y se espanta como los demás, pero no
        # perdona fallar: alumbrarle el cuerpo fuera del punto débil se lleva
        # la batería entera.
        se_espanta_con_luz=True,
        luz_descarga_linterna=True,
    ),
    ConfiguracionAnimatronic(
        nombre=nombres.FLORINDA,
        # La única con recorrido en fila: 14 -> 82 -> 97 -> 2 -> 3 -> 1, sin
        # atajos. El audio de Quico la lleva a la cámara donde suena si es
        # vecina de la suya (su recorrido de ida y vuelta, más retrocesos:
        # desde el Segundo Patio linda con las dos casas de arriba). Al
        # llegar a la reja el audio deja de servir.
        habitacion_inicial="casa_florinda",
        transiciones={
            "casa_florinda":  ("casa_godinez",),
            "casa_godinez":   ("casa_popis",),
            "casa_popis":     ("segundo_patio",),
            "segundo_patio":  ("entrada",),
            "entrada":        (HABITACION_JUGADOR,),
            HABITACION_JUGADOR: (),
        },
        retrocesos={
            "casa_godinez":   ("casa_florinda",),
            "casa_popis":     ("casa_godinez",),
            "segundo_patio":  ("casa_godinez", "casa_popis"),
        },
        sorda_en=("entrada",),
        puntos_acecho={
            POSICION_BARRIL: (520, 658),
            POSICION_LAVADEROS: (720, 660),
        },
        espera_ataque_lenta=12.0,
        espera_ataque_rapida=5.0,
        carpeta_sprite="florinda",
        prefijo_sprite="florinda",
        luz_mortal=True,
        alcanza_escondido=True,
        llegada_mortal=True,
    ),
    ConfiguracionAnimatronic(
        nombre=nombres.CHAVO,
        # No tiene ruta: salta de cualquier cámara a cualquier otra. Al Primer
        # Patio no llega tirando el dado, solo si el jugador lo mira demasiado
        # rato seguido; por eso la 1 aparece aquí sin que nada apunte a ella.
        habitacion_inicial="casa_chavo",
        transiciones={
            **_deambular(CAMARAS_DEL_CHAVO),
            HABITACION_JUGADOR: ("casa_chavo",),
        },
        puntos_acecho={
            POSICION_BARRIL: (640, 665),
            POSICION_LAVADEROS: (560, 662),
        },
        espera_ataque_lenta=18.0,
        espera_ataque_rapida=8.0,
        carpeta_sprite="chavo",
        prefijo_sprite="chavo",
        se_espanta_con_luz=True,
    ),
    ConfiguracionAnimatronic(
        nombre=nombres.JAIMICO,
        # El más corto de todos: casa, patio y encima. Desde el Segundo Patio
        # decide si baja o se devuelve, y vigilarlo por cámara lo frena.
        habitacion_inicial="casa_jaimito",
        transiciones={
            "casa_jaimito":   ("segundo_patio",),
            "segundo_patio":  ("casa_jaimito", HABITACION_JUGADOR),
            HABITACION_JUGADOR: ("segundo_patio",),
        },
        puntos_acecho={
            POSICION_BARRIL: (200, 645),
            POSICION_LAVADEROS: (1040, 652),
        },
        espera_ataque_lenta=40.0,
        espera_ataque_rapida=20.0,
        carpeta_sprite="jaimico",
        prefijo_sprite="jaimico",
        se_espanta_con_luz=True,
    ),
    ConfiguracionAnimatronic(
        nombre=nombres.CLOTILDE,
        # Sale de su casa al Segundo Patio y ahí se queda esperando a Don
        # Ramón: no se mueve a ningún lado mientras él no esté donde ella
        # necesita. Si él anda por la reja, ella baja sobre el jugador; si
        # está metido en su casa, se vuelve. Al espantarla regresa a la 71.
        habitacion_inicial="casa_clotilde",
        transiciones={
            "casa_clotilde":  ("segundo_patio",),
            "segundo_patio":  (HABITACION_JUGADOR, "casa_clotilde"),
            HABITACION_JUGADOR: ("casa_clotilde",),
        },
        condiciones_de_paso={
            ("segundo_patio", HABITACION_JUGADOR): (nombres.DON_RAMON, "entrada"),
            ("segundo_patio", "casa_clotilde"): (nombres.DON_RAMON, "casa_clotilde"),
        },
        puntos_acecho={
            POSICION_BARRIL: (1080, 668),
            POSICION_LAVADEROS: (1160, 665),
        },
        espera_ataque_lenta=15.0,
        espera_ataque_rapida=7.0,
        carpeta_sprite="bruja",
        prefijo_sprite="clotilde",
        se_espanta_con_luz=True,
    ),
)


def nombres_del_elenco() -> List[str]:
    return [config.nombre for config in ELENCO]


def prefijos_por_nombre() -> Dict[str, str]:
    """Nombre completo -> nombre corto con el que se le llama en los archivos
    de assets ("Don Ramón" -> "ramon"). Es el mismo prefijo que ya usan sus
    sprites, para no tener dos nomenclaturas distintas del mismo personaje."""
    return {config.nombre: config.prefijo_sprite for config in ELENCO}


def nombres_reconocidos_en_escenas() -> Dict[str, str]:
    """Cada forma que puede tomar un personaje dentro del nombre de archivo de
    una escena de cámara, ya normalizada, apuntando a su nombre corto oficial.

    Incluye su propio nombre corto y los alias de nombres.ALIAS_EN_ESCENAS, de
    modo que "clotilde" y "bruja" (o "ramon" y "ramón") lleven al mismo sitio.
    """
    reconocidos = {
        normalizar_nombre_corto(prefijo): prefijo
        for prefijo in prefijos_por_nombre().values()
    }
    for alias, oficial in nombres.ALIAS_EN_ESCENAS.items():
        reconocidos[normalizar_nombre_corto(alias)] = oficial
    return reconocidos


def grupos_de_escena() -> Dict[str, FrozenSet[str]]:
    """Atajos que valen por un grupo entero dentro del nombre de archivo de
    una escena. "todos.png" es la escena con los siete dentro, que si no
    habría que nombrar escribiendo los siete nombres cortos seguidos."""
    return {
        NOMBRE_TODO_EL_ELENCO: frozenset(prefijos_por_nombre().values()),
    }


def habitaciones_posibles() -> Dict[str, List[str]]:
    """Por cada habitación, qué personajes pueden llegar a estar en ella.

    Se deriva de los grafos, así que siempre refleja el elenco real: es lo
    que dice qué imágenes de cámara tiene sentido dibujar y cuáles nunca se
    verían.
    """
    posibles: Dict[str, List[str]] = {}
    for config in ELENCO:
        for id_habitacion in config.habitaciones():
            nombres_ahi = posibles.setdefault(id_habitacion, [])
            if config.nombre not in nombres_ahi:
                nombres_ahi.append(config.nombre)
    return posibles


def habitaciones_que_se_dibujan() -> Dict[str, List[str]]:
    """Como habitaciones_posibles(), pero sin los casos que nunca llegan a
    verse: quien acaba la noche nada más llegar al Primer Patio no necesita
    imagen ahí, porque la partida termina antes de que esa cámara se enseñe.

    Es lo que decide qué arte tiene sentido pedir (ver tools/).
    """
    mortales = {c.nombre for c in ELENCO if c.llegada_mortal}
    return {
        id_habitacion: [
            nombre for nombre in nombres_ahi
            if not (id_habitacion == HABITACION_JUGADOR and nombre in mortales)
        ]
        for id_habitacion, nombres_ahi in habitaciones_posibles().items()
    }


def carpetas_de_atacantes() -> Dict[str, str]:
    """Carpeta de assets/animatronics/ de cada personaje que puede acabar con
    la noche: los siete del elenco, con su carpeta_sprite, más el Sr.
    Barriga, que no recorre la vecindad pero también puede atrapar al
    jugador si se le llama sin necesidad (ver dominio/servicios.py)."""
    carpetas = {config.nombre: config.carpeta_sprite for config in ELENCO}
    carpetas[nombres.BARRIGA] = "barriga"
    return carpetas


def _validar_grafo(config: ConfiguracionAnimatronic):
    """El grafo tiene que ser recorrible: toda cámara a la que se puede
    llegar debe tener su propia entrada en transiciones, o el personaje se
    quedaría encerrado ahí para el resto de la noche."""
    if config.habitacion_inicial not in config.transiciones:
        raise ValueError(
            f"{config.nombre}: empieza en {config.habitacion_inicial}, que no "
            f"tiene transiciones"
        )
    if HABITACION_JUGADOR not in config.transiciones:
        raise ValueError(
            f"{config.nombre}: le falta la entrada de {HABITACION_JUGADOR}, que "
            f"es por donde se va cuando el jugador se lo quita de encima"
        )
    for origen, destinos in config.transiciones.items():
        if origen not in HABITACIONES:
            raise ValueError(f"{config.nombre}: habitación desconocida {origen}")
        for destino in destinos:
            if destino not in config.transiciones:
                raise ValueError(
                    f"{config.nombre}: puede llegar a {destino} pero de ahí no "
                    f"sale a ningún lado"
                )


def _validar_condiciones(config: ConfiguracionAnimatronic, del_elenco: Sequence[str]):
    for (origen, destino), (nombre, id_habitacion) in config.condiciones_de_paso.items():
        if destino not in config.transiciones.get(origen, ()):
            raise ValueError(
                f"{config.nombre}: condiciona el paso {origen} -> {destino}, que "
                f"no existe en su recorrido"
            )
        if nombre not in del_elenco:
            raise ValueError(f"{config.nombre}: condición sobre un desconocido {nombre}")
        if id_habitacion not in HABITACIONES:
            raise ValueError(
                f"{config.nombre}: condición sobre la habitación desconocida "
                f"{id_habitacion}"
            )


def _validar_puntos_acecho(config: ConfiguracionAnimatronic):
    """Sin punto para una de las vistas, el personaje llegaría al patio y el
    jugador no podría verlo ni acertarle desde ahí, que es justo el fallo que
    hace que una contramedida parezca rota."""
    for id_posicion in config.puntos_acecho:
        if id_posicion not in POSICIONES:
            raise ValueError(
                f"{config.nombre}: punto de acecho en un sitio desconocido "
                f"{id_posicion}"
            )
    faltan = [v for v in VISTAS_DEL_PATIO if v not in config.puntos_acecho]
    if faltan:
        raise ValueError(
            f"{config.nombre}: le falta su punto de acecho en {faltan}, así que "
            f"sería invisible desde ahí"
        )


def _validar_retrocesos(config: ConfiguracionAnimatronic):
    for origen, destinos in config.retrocesos.items():
        if origen not in config.transiciones:
            raise ValueError(
                f"{config.nombre}: retrocede desde {origen}, donde nunca está"
            )
        for destino in destinos:
            if destino not in config.transiciones:
                raise ValueError(
                    f"{config.nombre}: retrocede a {destino}, que no es suya"
                )


def validar_elenco(comprobar_sprites: bool = True):
    """Comprueba que los grafos son recorribles y que apuntan a habitaciones,
    puestos y personajes que existen, para que un id mal escrito falle de
    inmediato y no a mitad de una partida.

    Se ejecuta al importar el módulo. `comprobar_sprites` permite saltarse la
    revisión de archivos en disco cuando solo interesa validar los datos.
    """
    del_elenco = nombres_del_elenco()
    for config in ELENCO:
        _validar_grafo(config)
        _validar_condiciones(config, del_elenco)
        _validar_retrocesos(config)
        _validar_puntos_acecho(config)
        if not comprobar_sprites:
            continue
        for pose in range(1, POSES_POR_PERSONAJE + 1):
            if not config.ruta_pose(pose).exists():
                raise ValueError(
                    f"{config.nombre}: falta el sprite {config.ruta_pose(pose)}"
                )


validar_elenco()
