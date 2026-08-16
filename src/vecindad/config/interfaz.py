"""Todo lo que decide cómo se ve el juego: colores, tipografía y la
distribución de menú, HUD, monitor de cámaras y tablero de servicios.

Las medidas están en píxeles del lienzo base (ver config/ventana.py), no de
la ventana real, así que valen para cualquier resolución.
"""

from .ventana import ALTO_PANTALLA, ANCHO_PANTALLA

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

# --- Figuras de los animatrónicos ---
# Alto al que se dibuja un personaje, en píxeles del lienzo base. Delante del
# jugador se ve mucho más grande que a través de una cámara.
ALTO_ANIMATRONIC_VISTA = 560
ALTO_ANIMATRONIC_CAMARA = 320

# --- Iconos de objetos ---
# Lado del icono de un objeto tirado en el suelo y de los del inventario.
ICONO_OBJETO_SUELO = 64
ICONO_OBJETO_HUD = 52

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

# --- HUD ---
# Posición del bloque de noche/hora/batería. Con el monitor delante se mete
# dentro del marco y a la izquierda, porque las esquinas las ocupa el arte
# del marco y abajo a la derecha está el mapa.
POSICION_HUD_PATIO = (20, ALTO_PANTALLA - 62)
POSICION_HUD_CAMARAS = (62, 468)

# --- Panel de servicios ---
# Cuadrado, centrado y algo por encima de la franja del HUD, con los cuatro
# botones repartidos en cuadrantes sobre el arte.
PANEL_SERVICIOS_LADO = 520
PANEL_SERVICIOS_MARGEN_INFERIOR = 92

# --- Penumbra y haz de la linterna ---
# Qué tan oscuro queda todo lo que está fuera del círculo de luz.
OSCURIDAD_OPACIDAD = 238  # 0-255: 255 sería no ver absolutamente nada
# Dentro del barril no se puede encender la linterna, así que la penumbra
# tiene que dejar ver algo por sí sola: entra algo de luna por la boca.
OSCURIDAD_DENTRO_BARRIL = 105
# Luz que la linterna suma dentro del haz. Los fondos ya están pintados de
# noche, así que además de destapar la oscuridad hay que aclararlos para que
# el haz se lea como una linterna y no como un agujero.
LINTERNA_COLOR_LUZ = (96, 84, 58)

# --- Susto final (jumpscare) ---
# Al perder, si el personaje que atrapó al jugador tiene sus propios cuadros
# "jump N.png" en assets/animatronics/<carpeta>/, se reproducen en secuencia
# sobre el fondo de la posición donde estaba el jugador, antes de pasar a la
# pantalla de game over. Los últimos dos cuadros (el acercamiento final) se
# sostienen más tiempo que el resto para que se note el golpe. Estos dos
# tiempos son el ritmo "natural"; si hay un efecto de sonido para el susto,
# ambos se escalan para que la ráfaga completa dure lo mismo que el audio
# (ver GestorAudio.duracion_efecto).
SUSTO_SEGUNDOS_POR_FRAME = 0.05
SUSTO_SEGUNDOS_FRAME_FINAL = 0.5

# Cuánto se agranda cada cuadro respecto a ajustarlo solo por el alto de
# pantalla, para que ocupe más del escenario en vez de quedar como una tira
# angosta. Como los cuadros son retratos verticales, agrandar de más obliga a
# recortar mucho arriba y abajo; 1.5 es un punto medio que ya se probó y no
# corta cabeza ni manos en los cuadros existentes.
SUSTO_ZOOM = 1.5

# --- Botón de audio del monitor de cámaras ---
# Suena la grabación de Quico, que hace retroceder a Doña Florinda una cámara
# en su recorrido. Va abajo a la izquierda, en el hueco que queda entre la
# fecha del HUD y el mapa de la vecindad.
CAMARA_AUDIO_ANCHO = 250
CAMARA_AUDIO_ALTO = 62
CAMARA_AUDIO_MARGEN_IZQUIERDO = 350
CAMARA_AUDIO_MARGEN_INFERIOR = 56

# --- Menú de pausa ---
# No tiene fondo propio: usa las mismas medidas que el resto del menú
# (margen, alto de línea, tamaños de fuente) pero se dibuja encima de la
# última imagen de la partida, oscurecida con esta capa en vez de con una
# imagen de fondo.
PAUSA_OVERLAY_OPACIDAD = 190  # 0-255: qué tan oscura queda la partida detrás
