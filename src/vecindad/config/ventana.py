"""Lienzo base, resoluciones y modo de video.

Todo el juego se dibuja sobre un lienzo fijo de ANCHO_PANTALLA x
ALTO_PANTALLA y después se escala a la resolución elegida. Así las
posiciones de la interfaz se calculan una sola vez y siguen siendo válidas
en cualquier resolución.
"""

ANCHO_PANTALLA = 1280
ALTO_PANTALLA = 720
RESOLUCION_BASE = (ANCHO_PANTALLA, ALTO_PANTALLA)
RESOLUCIONES_DISPONIBLES = (
    (1024, 576),
    (1280, 720),
    (1600, 900),
    (1920, 1080),
)

# La primera vez que el juego corre (sin configuracion.json todavía) arranca
# en pantalla completa. Una vez el jugador guarda una preferencia distinta,
# esa preferencia es la que manda.
PANTALLA_COMPLETA_POR_DEFECTO = True

FPS = 60
TITULO_JUEGO = "Chaves Nightmare Plus +"
