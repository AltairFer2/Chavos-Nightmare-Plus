"""Qué opciones muestra cada sección del menú.

Son funciones sueltas que reciben lo que necesitan leer y devuelven la lista
de líneas. Así la lista de opciones se puede revisar de un vistazo (y probar)
sin montar el menú entero.
"""

from typing import Dict, List

from .modelo import PREFIJO_NIVEL_IA, EntradaMenu


def entradas_principal(idiomas, progreso) -> List[EntradaMenu]:
    """Las noches disponibles según lo que el jugador lleve desbloqueado."""
    entradas = [EntradaMenu("nuevo_juego", idiomas.t("menu_nuevo_juego"))]

    if progreso.hay_partida_guardada:
        entradas.append(
            EntradaMenu(
                "continuar",
                idiomas.t("menu_continuar"),
                idiomas.t("menu_continuar_noche", noche=progreso.proxima_noche),
            )
        )
    else:
        entradas.append(
            EntradaMenu(
                "continuar",
                idiomas.t("menu_continuar"),
                idiomas.t("menu_sin_partida"),
                habilitada=False,
            )
        )

    if progreso.noche_extra_desbloqueada:
        entradas.append(EntradaMenu("noche_6", idiomas.t("menu_noche_6")))
    if progreso.noche_personalizada_desbloqueada:
        entradas.append(
            EntradaMenu("noche_personalizada", idiomas.t("menu_noche_personalizada"))
        )

    entradas.append(EntradaMenu("ajustes", idiomas.t("menu_ajustes")))
    return entradas


def entradas_ajustes(idiomas, configuracion, pantalla) -> List[EntradaMenu]:
    """Preferencias del jugador, con su valor actual escrito en la etiqueta."""
    estado_streamer = idiomas.t(
        "activado" if configuracion.modo_streamer else "desactivado"
    )
    estado_pantalla_completa = idiomas.t(
        "activado" if pantalla.pantalla_completa else "desactivado"
    )
    ancho, alto = pantalla.resolucion
    # El selector de resolución solo cambia el tamaño de la ventana: en
    # pantalla completa se sigue mostrando (queda lista para cuando el
    # jugador vuelva a modo ventana), aclarado con un sufijo.
    sufijo_resolucion = (
        f" ({idiomas.t('ajustes_resolucion_ventana')})"
        if pantalla.pantalla_completa
        else ""
    )
    return [
        EntradaMenu(
            "idioma",
            f"{idiomas.t('ajustes_idioma')}: {idiomas.nombre_idioma_actual()}",
        ),
        EntradaMenu(
            "pantalla_completa",
            f"{idiomas.t('ajustes_pantalla_completa')}: {estado_pantalla_completa}",
        ),
        EntradaMenu(
            "resolucion",
            f"{idiomas.t('ajustes_resolucion')}: {ancho} x {alto}{sufijo_resolucion}",
        ),
        EntradaMenu("brillo", f"{idiomas.t('ajustes_brillo')}: {pantalla.brillo}%"),
        EntradaMenu("volumen_musica", idiomas.t("ajustes_volumen_musica")),
        EntradaMenu("volumen_efectos", idiomas.t("ajustes_volumen_efectos")),
        EntradaMenu(
            "modo_streamer",
            f"{idiomas.t('ajustes_modo_streamer')}: {estado_streamer}",
        ),
        EntradaMenu("volver", idiomas.t("ajustes_volver")),
    ]


def entradas_personalizada(idiomas, niveles: Dict[str, int]) -> List[EntradaMenu]:
    """Una fila por personaje con su nivel de IA, más iniciar y volver."""
    entradas = [
        EntradaMenu(f"{PREFIJO_NIVEL_IA}{nombre}", f"{nombre}: {nivel}")
        for nombre, nivel in niveles.items()
    ]
    entradas.append(EntradaMenu("iniciar", idiomas.t("personalizada_iniciar")))
    entradas.append(EntradaMenu("volver", idiomas.t("personalizada_volver")))
    return entradas
