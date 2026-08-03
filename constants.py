"""Constantes globales: resolución de ventana, rutas de assets, tipografía,
colores y parámetros de tiempo/energía de la noche."""

import os
from pathlib import Path

# --- Ventana ---
# Todo el juego se dibuja sobre un lienzo fijo de ANCHO_PANTALLA x
# ALTO_PANTALLA y después se escala a la resolución elegida. Así las
# posiciones de la interfaz se calculan una sola vez y siguen siendo válidas
# en cualquier resolución.
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

# --- Rutas base ---
DIR_BASE = Path(__file__).resolve().parent
DIR_ASSETS = DIR_BASE / "assets"
DIR_ASSETS_CAMARAS = DIR_ASSETS / "camaras"
DIR_ASSETS_ANIMATRONICS = DIR_ASSETS / "animatronics"
# Alto al que se dibuja un personaje, en píxeles del lienzo base. Delante del
# jugador se ve mucho más grande que a través de una cámara.
ALTO_ANIMATRONIC_VISTA = 560
ALTO_ANIMATRONIC_CAMARA = 320
DIR_ASSETS_UI = DIR_ASSETS / "ui"
DIR_ASSETS_MENU = DIR_ASSETS / "menu"
DIR_ASSETS_FUENTES = DIR_ASSETS / "fuentes"
# assets/ui/ guarda además los fondos de las posiciones donde se para el
# jugador durante la noche (ver posiciones.py).

# Imágenes que el menú principal espera encontrar en assets/menu/.
# Si no existen todavía, el menú dibuja un respaldo sin fallar.
ARCHIVO_MENU_FONDO = DIR_ASSETS_MENU / "fondo.png"
ARCHIVO_MENU_TITULO = DIR_ASSETS_MENU / "titulo.png"

# Variantes "jumpscare" del fondo del menú: cualquier archivo que siga el
# patrón "fondo <n>.png" (fondo 2.png, fondo 3.png...) se toma como variante,
# así se pueden agregar o quitar sin tocar código.
PATRON_MENU_FONDO_VARIANTES = "fondo *.png"

# Cada tanto (segundos, elegido al azar en este rango) el fondo del menú
# cambia a una variante al azar durante un tiempo corto (también al azar) y
# siempre vuelve al fondo original.
MENU_FONDO_VARIANTE_INTERVALO_MIN = 3.0
MENU_FONDO_VARIANTE_INTERVALO_MAX = 10.0
MENU_FONDO_VARIANTE_DURACION_MIN = 1.0
MENU_FONDO_VARIANTE_DURACION_MAX = 3.0

# Ruido/estática que se mezcla sobre el fondo del menú (no hay asset para
# esto: se genera por código). Se precalculan varios cuadros de ruido a baja
# resolución y se escalan una sola vez al iniciar, para no regenerar ruido
# píxel a píxel en cada fotograma.
MENU_ESTATICA_FRAMES = 6
MENU_ESTATICA_OPACIDAD = 28  # 0-255: qué tan visible es el ruido sobre el fondo
MENU_ESTATICA_ANCHO = ANCHO_PANTALLA // 4
MENU_ESTATICA_ALTO = ALTO_PANTALLA // 4

# --- Audio ---
# El modo streamer decide de cuál de estas dos carpetas se lee TODO el audio
# (música, ambiente, efectos y sonidos de cámara). Ambas comparten la misma
# estructura interna y los mismos nombres de archivo.
DIR_SONIDOS = DIR_BASE / "sonidos"
DIR_SONIDOS_CON_COPYRIGHT = DIR_SONIDOS / "con_copyright"
DIR_SONIDOS_SIN_COPYRIGHT = DIR_SONIDOS / "sin_copyright"
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

# Volumen en porcentaje (0-100), como se muestra y se guarda.
VOLUMEN_MINIMO = 0
VOLUMEN_MAXIMO = 100
VOLUMEN_PASO = 10
VOLUMEN_MUSICA_POR_DEFECTO = 70
VOLUMEN_EFECTOS_POR_DEFECTO = 80

# --- Datos del jugador ---
# Se guardan fuera del proyecto para que sigan funcionando cuando el juego se
# empaquete como .exe y quede instalado en una carpeta de solo lectura.
DIR_DATOS_USUARIO = Path(os.getenv("APPDATA") or Path.home()) / "LaVecindadDelChavo"
ARCHIVO_PROGRESO = DIR_DATOS_USUARIO / "progreso.json"
ARCHIVO_CONFIGURACION = DIR_DATOS_USUARIO / "configuracion.json"

# --- Tipografía ---
# Si existe un archivo con este nombre (.ttf/.otf) dentro de assets/fuentes/
# se usa ese archivo; si no, se busca una fuente instalada en el sistema.
# Cambiar aquí el nombre y los tamaños afecta a toda la interfaz.
FUENTE_NOMBRE = "Comic Sans"
FUENTE_TAMANO_TITULO = 64
FUENTE_TAMANO_MENU = 34
FUENTE_TAMANO_TEXTO = 24
FUENTE_TAMANO_HUD = 18
FUENTE_TAMANO_CAMARA = 14

# --- Distribución del menú ---
MENU_MARGEN_IZQUIERDO = 120
MENU_Y_PRIMERA_OPCION = 300
MENU_ALTO_LINEA = 48
MENU_TITULO_Y = 60
MENU_TITULO_ALTO_MAXIMO = 220

# Barra deslizante de volumen (Ajustes). X es fija en vez de calcularse a
# partir del ancho del texto para que los tres idiomas alineen sus barras
# en la misma columna sin importar cuánto midan las etiquetas traducidas.
MENU_DESLIZADOR_X = MENU_MARGEN_IZQUIERDO + 430
MENU_DESLIZADOR_ANCHO = 240
MENU_DESLIZADOR_ALTO = 16

# --- Colores (RGB) ---
COLOR_NEGRO = (0, 0, 0)
COLOR_BLANCO = (255, 255, 255)
COLOR_GRIS_OSCURO = (30, 30, 30)
COLOR_GRIS = (90, 90, 90)
COLOR_VERDE_ENERGIA = (80, 200, 120)
COLOR_ROJO_ALERTA = (200, 40, 40)
COLOR_AMARILLO_AVISO = (230, 200, 60)
COLOR_OPCION_NORMAL = (190, 190, 190)
COLOR_OPCION_RESALTADA = (255, 255, 255)
COLOR_OPCION_DESHABILITADA = (95, 95, 95)

# --- Panel de cámaras ---
# La vista de la cámara ocupa la pantalla completa y encima va su marco
# ("Marco Cam N.png", que ya trae el rótulo, el REC y la fecha). El mapa de
# la vecindad hace de menú de selección abajo a la derecha: cada recuadro de
# ese mapa es un botón y el propio arte trae la variante con la cámara
# activa resaltada ("Cam N Selected.png").
CAMARA_MAPA_ANCHO = 420
CAMARA_MAPA_ALTO = 315  # conserva la proporción 4:3 del arte del mapa
CAMARA_MAPA_MARGEN_DERECHO = 24
CAMARA_MAPA_MARGEN_INFERIOR = 78  # deja libre la franja del HUD

# Posición del bloque de noche/hora/batería del HUD. Con el monitor delante
# se mete dentro del marco y a la izquierda, porque las esquinas las ocupa el
# arte del marco y abajo a la derecha está el mapa.
POSICION_HUD_PATIO = (20, ALTO_PANTALLA - 62)
POSICION_HUD_CAMARAS = (62, 468)

# Ruido de señal sobre la imagen de la cámara.
CAMARA_ESTATICA_FRAMES = 6
CAMARA_ESTATICA_OPACIDAD = 15
CAMARA_ESTATICA_ANCHO = ANCHO_PANTALLA // 4
CAMARA_ESTATICA_ALTO = ALTO_PANTALLA // 4
CAMARA_ESTATICA_CAMBIO_FRAMES = 4  # cada cuántos fotogramas se cambia de cuadro

# Ráfaga de estática al saltar de una cámara a otra.
CAMARA_TRANSICION_SEGUNDOS = 0.3
CAMARA_TRANSICION_OPACIDAD = 200

# Líneas de barrido del monitor.
CAMARA_LINEAS_SEPARACION = 4
CAMARA_LINEAS_OPACIDAD = 26

# Segundos seguidos que aguanta El Chavo siendo observado antes de arruinar
# las cámaras. El contador baja solo si se deja de mirarlo.
CAMARA_SABOTAJE_SEGUNDOS = 8.0
CAMARA_SABOTAJE_RECUPERACION = 0.5  # cuánto se enfría por segundo sin mirarlo

# --- Servicios de utilidad del barril ---
SERVICIO_AUDIO_SEGUNDOS = 5.0
SERVICIO_CAMARAS_SEGUNDOS = 7.0
SERVICIO_TODO_SEGUNDOS = 20.0
BARRIGA_COOLDOWN_SEGUNDOS = 5.0
USOS_AUDIO_QUICO = 4
NOCHE_AUDIO_LIMITADO = 2  # desde esta noche el audio deja de ser ilimitado

# Panel de servicios: cuadrado, centrado y algo por encima de la franja del
# HUD, con los cuatro botones repartidos en cuadrantes sobre el arte.
PANEL_SERVICIOS_LADO = 520
PANEL_SERVICIOS_MARGEN_INFERIOR = 92

# --- Noche / temporizador ---
HORA_INICIO_NOCHE = 0  # 12:00 am
HORA_FIN_NOCHE = 6  # 6:00 am
DURACION_NOCHE_SEGUNDOS = 540   # duración real de una noche completa (9 min)
HORAS_DE_NOCHE = (HORA_FIN_NOCHE - HORA_INICIO_NOCHE) % 12 or 12
SEGUNDOS_POR_HORA_NOCHE = DURACION_NOCHE_SEGUNDOS / HORAS_DE_NOCHE

# Cada hora in-game se divide en TICKS_POR_HORA intentos de movimiento. En
# cada tick, todo animatrónico activo tira un dado y decide si avanza. Bajar
# este número hace la noche más lenta y predecible; subirlo, más frenética.
TICKS_POR_HORA = 18
SEGUNDOS_POR_TICK = SEGUNDOS_POR_HORA_NOCHE / TICKS_POR_HORA

# --- Progresión de noches ---
NOCHES_HISTORIA = 5  # noches 1 a 5: campaña principal
NOCHE_EXTRA = 6  # se desbloquea al completar la noche 5
ULTIMA_NOCHE = NOCHE_EXTRA

# --- Inteligencia artificial de los animatrónicos ---
# Escala estilo FNAF: en cada tick se tira random.randint(1, 20) y el
# animatrónico avanza si el resultado es menor o igual a su nivel_ia.
# Nivel 0 = nunca se mueve; nivel 20 = se mueve en todos los ticks.
NIVEL_IA_MINIMO = 0
NIVEL_IA_MAXIMO = 20

# --- Linterna ---
# Segundos de luz que da una batería con la linterna encendida sin parar.
LINTERNA_DURACION_BATERIA_SEGUNDOS = 120.0
# Radio (en píxeles del lienzo base) del círculo iluminado alrededor del
# puntero, y qué tan oscuro queda todo lo que está fuera de él.
LINTERNA_RADIO = 220
OSCURIDAD_OPACIDAD = 238  # 0-255: 255 sería no ver absolutamente nada
# Dentro del barril no se puede encender la linterna, así que la penumbra
# tiene que dejar ver algo por sí sola: entra algo de luna por la boca.
OSCURIDAD_DENTRO_BARRIL = 105
# Luz que la linterna suma dentro del haz. Los fondos ya están pintados de
# noche, así que además de destapar la oscuridad hay que aclararlos para que
# el haz se lea como una linterna y no como un agujero.
LINTERNA_COLOR_LUZ = (96, 84, 58)

# Radio dentro del cual apuntar la luz a un animatrónico sensible a ella es
# mortal. Crece con su nivel_ia: a nivel bajo se le puede rozar con el borde
# del haz sin morir; a nivel alto casi cualquier destello lo activa.
LUZ_RADIO_PELIGRO_MINIMO = 70
LUZ_RADIO_PELIGRO_MAXIMO = 210

# --- Baterías y objetos del suelo ---
# Noches 1 a 3 el jugador arranca con baterías de repuesto dentro del barril;
# a partir de NOCHE_SIN_BATERIAS_FIJAS ya no hay ninguna y todas hay que
# buscarlas fuera.
BATERIAS_INICIALES_EN_BARRIL = 2
NOCHE_SIN_BATERIAS_FIJAS = 4

# Cada cuánto se revisa si aparece un objeto nuevo en un sitio vacío
# (Entrada o Lavaderos) y con qué probabilidad aparece. La probabilidad baja
# una vez que desaparecen las baterías fijas del barril.
OBJETO_INTERVALO_APARICION_SEGUNDOS = 20.0
# Lado del icono de un objeto tirado en el suelo y de los del inventario.
ICONO_OBJETO_SUELO = 64
ICONO_OBJETO_HUD = 52
OBJETO_PROBABILIDAD_BASE = 0.55
OBJETO_PROBABILIDAD_MINIMA = 0.15
OBJETO_REDUCCION_POR_NOCHE = 0.08
