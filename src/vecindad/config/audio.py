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
}

# Efecto que suena al saltar de una cámara a otra (subcarpeta camaras/).
EFECTO_CAMBIO_CAMARA = "cambio"

# Chasquido del tubo al levantar el monitor (subcarpeta camaras/). Acompaña a
# la animación del monitor bajando: suena una vez al abrir el panel, no cada
# vez que se cambia de cámara.
EFECTO_ENCENDIDO_CAMARAS = "encendido"

# Corte de señal de una cámara cuando alguien se mueve justo mientras se le
# está mirando (subcarpeta camaras/). Es el aviso de que esa vista se acaba
# de caer: sin él, la interferencia parecería un fallo del juego.
EFECTO_INTERFERENCIA = "interferencia"

# Efecto del golpe del susto final, al perder (subcarpeta efectos/).
EFECTO_SUSTO = "jumpscare"

# Efecto al llamar al Sr. Barriga, salga bien o mal la llamada (subcarpeta
# efectos/).
EFECTO_LLAMADA_BARRIGA = "llamada barriga"

# Don Ramón yéndose cuando el Sr. Barriga se lo lleva (subcarpeta efectos/).
# Ocupa el sitio del aviso escrito que había antes: enterarse de que la
# llamada sirvió es cosa de oírlo, no de leerlo. Suena una de las diez
# variantes al azar; si el árbol activo no tiene ninguna (el modo streamer),
# suena EFECTO_RAMON_SE_VA.
EFECTOS_SALIDA_RAMON = tuple(f"salida_ramon_{numero}" for numero in range(1, 11))
EFECTO_RAMON_SE_VA = "ramon se va"

# El Chavo plantándose en el patio después de romper las cámaras (subcarpeta
# efectos/).
EFECTO_LLEGA_CHAVO = "llega chavo"

# La aparición rara (easter egg) que se cuela de vez en cuando en la partida
# (subcarpeta efectos/).
EFECTO_EASTER_EGG = "easter_egg"

# Efecto al reponer el audio de Quico desde el panel del barril (subcarpeta
# efectos/). Es el sonido de reparar la cinta, no la grabación en sí: esa
# suena desde el monitor de cámaras, con EFECTOS_LLAMADA_FLORINDA.
EFECTO_REPARACION = "reparacion"

# El sobresalto del jugador al toparse con alguien en el patio (subcarpeta
# efectos/). Es su reacción, no la del personaje: suena una vez por
# encuentro, cuando pasa de no tener a nadie delante a tenerlo.
EFECTO_SORPRESA = "sorprendido"

# Pasos con los que un personaje anuncia que acaba de plantarse en el Primer
# Patio (subcarpeta efectos/). Son dos grabaciones del mismo paso, una por
# lado: suena la que corresponde a la mitad del patio donde apareció, así el
# aviso además dice hacia dónde mirar. Es la única pista que tiene el jugador
# cuando está dentro del barril con un panel levantado.
EFECTO_PASOS_IZQUIERDA = "cambio left"
EFECTO_PASOS_DERECHA = "cambio right"

# Alerta de que hay alguien en el Primer Patio (subcarpeta ambiente/). Suena
# en bucle mientras alguien acecha, se oiga desde donde se oiga (asomado, en
# el barril o mirando las cámaras), y se calla en cuanto el patio se vacía.
# Su volumen sube con lo cerca que está el ataque más próximo: de
# ALERTA_PATIO_VOLUMEN[0] al llegar a ALERTA_PATIO_VOLUMEN[1] al atacar.
EFECTO_ALERTA_PATIO = "mono cerca"
ALERTA_PATIO_VOLUMEN = (0.45, 1.0)

# Grabaciones de Quico con las que se llama a Doña Florinda (subcarpeta
# efectos/). Suena una al azar cada vez, para que usar el audio varias veces
# en una noche no se oiga siempre igual. Las que no existan en el árbol
# activo se descartan solas, así que el modo streamer puede tener menos
# variantes, o ninguna, sin que nada falle.
EFECTOS_LLAMADA_FLORINDA = ("audio 1", "audio 2", "audio 3")

# Efecto de la noche superada (subcarpeta efectos/). Suena una sola vez,
# justo en el instante en que el reloj salta de 5:59 a 6:00 am; no es
# música de fondo, así que no se repite en bucle ni sigue sonando después.
EFECTO_NOCHE_SUPERADA = "noche superada"

# Volumen en porcentaje (0-100), como se muestra y se guarda.
VOLUMEN_MINIMO = 0
VOLUMEN_MAXIMO = 100
VOLUMEN_PASO = 10
VOLUMEN_MUSICA_POR_DEFECTO = 70
VOLUMEN_EFECTOS_POR_DEFECTO = 80

# Cuánto del volumen elegido se oye con la partida en pausa. No cambia las
# preferencias del jugador: es una atenuación temporal que se deshace al
# reanudar, para poder hablar o atender algo sin bajar nada a mano.
PROPORCION_VOLUMEN_EN_PAUSA = 0.5
