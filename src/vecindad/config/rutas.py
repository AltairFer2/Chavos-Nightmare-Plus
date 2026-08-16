"""Rutas a los assets y a los datos del jugador.

DIR_RAIZ apunta a la raíz del proyecto (tres niveles por encima de este
archivo: config/ -> vecindad/ -> src/ -> raíz), donde viven assets/ y
sonidos/. Al empaquetar con PyInstaller esas dos carpetas se copian junto al
ejecutable y sys._MEIPASS pasa a ser la raíz, de ahí que se consulte primero.
"""

import os
import sys
from pathlib import Path


def _dir_raiz() -> Path:
    """Carpeta que contiene assets/ y sonidos/, tanto corriendo desde el
    código fuente como desde el .exe empaquetado."""
    empaquetado = getattr(sys, "_MEIPASS", None)
    if empaquetado is not None:
        return Path(empaquetado)
    return Path(__file__).resolve().parents[3]


DIR_RAIZ = _dir_raiz()

# --- Assets gráficos ---
DIR_ASSETS = DIR_RAIZ / "assets"
DIR_ASSETS_CAMARAS = DIR_ASSETS / "camaras"
DIR_ASSETS_ANIMATRONICS = DIR_ASSETS / "animatronics"
DIR_ASSETS_UI = DIR_ASSETS / "ui"
DIR_ASSETS_MENU = DIR_ASSETS / "menu"
DIR_ASSETS_FUENTES = DIR_ASSETS / "fuentes"
# assets/ui/ guarda además los fondos de las posiciones donde se para el
# jugador durante la noche (ver mundo/posiciones.py).

# Imágenes que el menú principal espera encontrar en assets/menu/.
# Si no existen todavía, el menú dibuja un respaldo sin fallar.
ARCHIVO_MENU_FONDO = DIR_ASSETS_MENU / "fondo.png"
ARCHIVO_MENU_TITULO = DIR_ASSETS_MENU / "titulo.png"

# Variantes "jumpscare" del fondo del menú: cualquier archivo que siga el
# patrón "fondo <n>.png" (fondo 2.png, fondo 3.png...) se toma como variante,
# así se pueden agregar o quitar sin tocar código.
PATRON_MENU_FONDO_VARIANTES = "fondo *.png"

# --- Audio ---
# El modo streamer decide de cuál de estas dos carpetas se lee TODO el audio
# (música, ambiente, efectos y sonidos de cámara). Ambas comparten la misma
# estructura interna y los mismos nombres de archivo.
DIR_SONIDOS = DIR_RAIZ / "sonidos"
DIR_SONIDOS_CON_COPYRIGHT = DIR_SONIDOS / "con_copyright"
DIR_SONIDOS_SIN_COPYRIGHT = DIR_SONIDOS / "sin_copyright"

# --- Datos del jugador ---
# Se guardan fuera del proyecto para que sigan funcionando cuando el juego se
# empaquete como .exe y quede instalado en una carpeta de solo lectura.
DIR_DATOS_USUARIO = Path(os.getenv("APPDATA") or Path.home()) / "LaVecindadDelChavo"
ARCHIVO_PROGRESO = DIR_DATOS_USUARIO / "progreso.json"
ARCHIVO_CONFIGURACION = DIR_DATOS_USUARIO / "configuracion.json"
