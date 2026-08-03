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
TITULO_JUEGO = "La Vecindad del Chavo"

# --- Rutas base ---
DIR_BASE = Path(__file__).resolve().parent
DIR_ASSETS = DIR_BASE / "assets"
DIR_ASSETS_CAMARAS = DIR_ASSETS / "camaras"
DIR_ASSETS_ANIMATRONICS = DIR_ASSETS / "animatronics"
DIR_ASSETS_UI = DIR_ASSETS / "ui"
DIR_ASSETS_MENU = DIR_ASSETS / "menu"
DIR_ASSETS_FUENTES = DIR_ASSETS / "fuentes"

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

# Nombre de archivo real de cada pista. El juego pide la pista por su nombre
# lógico ("menu", "noche"...) y aquí se traduce al archivo que existe en
# disco, para no tener que renombrar los assets. Si el archivo mapeado no
# está en la carpeta activa, se busca como respaldo un archivo con el nombre
# lógico: así el árbol sin copyright puede usar sus propios nombres.
PISTAS_MUSICA = {
    "menu": "el-chavo-intro",
    "noche": "noche",
    "game_over": "game_over",
    "victoria": "victoria",
}

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

# --- Parpadeo de cámaras ---
# Cada cuántos frames renderizados se alterna entre la imagen de la cámara
# seleccionada y "Cam Unselected.png" (efecto de estática tipo CCTV viejo).
INTERVALO_PARPADEO_FRAMES = 20

# --- Noche / temporizador ---
HORA_INICIO_NOCHE = 0  # 12:00 am
HORA_FIN_NOCHE = 6  # 6:00 am
DURACION_NOCHE_SEGUNDOS = 540   # duración real de una noche completa (9 min)

# --- Progresión de noches ---
NOCHES_HISTORIA = 5  # noches 1 a 5: campaña principal
NOCHE_EXTRA = 6  # se desbloquea al completar la noche 5
ULTIMA_NOCHE = NOCHE_EXTRA
DIFICULTAD_MINIMA = 1
DIFICULTAD_MAXIMA = 5

# --- Energía ---
ENERGIA_MAXIMA = 100.0
CONSUMO_ENERGIA_POR_SEGUNDO = ENERGIA_MAXIMA / DURACION_NOCHE_SEGUNDOS
CONSUMO_EXTRA_CAMARAS_POR_SEGUNDO = CONSUMO_ENERGIA_POR_SEGUNDO * 1.5
