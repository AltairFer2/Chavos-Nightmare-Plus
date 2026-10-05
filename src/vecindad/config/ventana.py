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

# Brillo de la imagen final, en porcentaje: 100 es la imagen tal cual, por
# debajo se oscurece y por encima se aclara. Es un ajuste de comodidad, no
# una mecánica: el juego es oscuro a propósito, pero cada monitor lo muestra
# distinto y una escena de noche puede quedar ilegible. El tope se queda en
# 150 para que subirlo no borre del todo la penumbra.
BRILLO_MINIMO = 50
BRILLO_MAXIMO = 150
BRILLO_NEUTRO = 100
BRILLO_POR_DEFECTO = BRILLO_NEUTRO
BRILLO_PASO = 10

FPS = 60
TITULO_JUEGO = "Chaves Nightmare Plus +"
# Con qué nombre se presenta el juego a Windows para que la barra de tareas
# lo trate como una aplicación propia y no como Python (ver
# infraestructura/pantalla.py). Formato Empresa.Producto, sin espacios.
ID_APLICACION_WINDOWS = "LaVecindadDelChavo.ChavesNightmarePlus"
