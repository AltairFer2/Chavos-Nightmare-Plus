"""Estructura de las carpetas de audio, mapa de pistas y rango de volumen."""

SUBCARPETA_MUSICA = "musica"
SUBCARPETA_AMBIENTE = "ambiente"
SUBCARPETA_EFECTOS = "efectos"
SUBCARPETA_CAMARAS = "camaras"
EXTENSIONES_AUDIO = (".ogg", ".mp3", ".wav")

# Carpeta y nombre de archivo real de cada pista. El juego pide la pista por
# su nombre lógico ("menu", "noche"...) y aquí se traduce al archivo que
# existe en disco, para no tener que renombrar los assets. No todas viven en
# musica/: el fondo de la noche es una pista de ambiente. Si el archivo
# mapeado no está en la carpeta activa se busca como respaldo uno que se
# llame como la pista lógica dentro de musica/, así el árbol sin copyright
# puede usar sus propios nombres.
PISTAS_MUSICA = {
    "menu": (SUBCARPETA_MUSICA, "el-chavo-intro"),
    "noche": (SUBCARPETA_AMBIENTE, "fondo game"),
    "game_over": (SUBCARPETA_MUSICA, "game_over"),
    "victoria": (SUBCARPETA_MUSICA, "victoria"),
}

# Efecto que suena al saltar de una cámara a otra (subcarpeta camaras/).
EFECTO_CAMBIO_CAMARA = "cambio"

# Efecto del golpe del susto final, al perder (subcarpeta efectos/).
EFECTO_SUSTO = "jumpscare"

# Efecto al llamar al Sr. Barriga, salga bien o mal la llamada (subcarpeta
# efectos/).
EFECTO_LLAMADA_BARRIGA = "llamada barriga"

# Efecto de que Don Ramón se va cuando el Sr. Barriga se lo lleva (subcarpeta
# efectos/). Ocupa el sitio del aviso escrito que había antes: enterarse de
# que la llamada sirvió es cosa de oírlo, no de leerlo.
EFECTO_RAMON_SE_VA = "ramon se va"

# Efecto al reponer el audio de Quico desde el panel del barril (subcarpeta
# efectos/). Es el sonido de reparar la cinta, no la grabación en sí: esa
# suena desde el monitor de cámaras, con EFECTOS_LLAMADA_FLORINDA.
EFECTO_REPARACION = "reparacion"

# Grabaciones de Quico con las que se llama a Doña Florinda (subcarpeta
# efectos/). Suena una al azar cada vez, para que usar el audio varias veces
# en una noche no se oiga siempre igual. Las que no existan en el árbol
# activo se descartan solas, así que el modo streamer puede tener menos
# variantes, o ninguna, sin que nada falle.
EFECTOS_LLAMADA_FLORINDA = ("audio 1", "audio 2", "audio 3")

# Volumen en porcentaje (0-100), como se muestra y se guarda.
VOLUMEN_MINIMO = 0
VOLUMEN_MAXIMO = 100
VOLUMEN_PASO = 10
VOLUMEN_MUSICA_POR_DEFECTO = 70
VOLUMEN_EFECTOS_POR_DEFECTO = 80
