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
# Comic Neue: la alternativa libre a Comic Sans (SIL Open Font License, ver
# assets/fuentes/OFL.txt), así que se puede distribuir con el juego. No
# trae flechas (←↑→↓): los textos usan las letras W/A/S/D en su lugar.
FUENTE_NOMBRE = "ComicNeue"
FUENTE_TAMANO_TITULO = 64
FUENTE_TAMANO_MENU = 34
FUENTE_TAMANO_TEXTO = 24
FUENTE_TAMANO_HUD = 18
FUENTE_TAMANO_CAMARA = 14
FUENTE_TAMANO_RELOJ = 110

# --- Figuras de los animatrónicos ---
# Alto al que se dibuja un personaje, en píxeles del lienzo base. Delante del
# jugador se ve mucho más grande que a través de una cámara.
ALTO_ANIMATRONIC_VISTA = 560
ALTO_ANIMATRONIC_CAMARA = 320

# --- Iconos de objetos ---
# Lado del icono de lo que se encuentra tirado en el suelo.
ICONO_OBJETO_SUELO = 64
# En sus últimos segundos tirado, el objeto parpadea para avisar de que está
# por irse. Parpadeos por segundo mientras dura el aviso.
OBJETO_PARPADEO_SEGUNDOS = 3.0
OBJETO_PARPADEOS_POR_SEGUNDO = 4

# --- Apariciones raras (easter eggs) ---
# Opacidad máxima (0-255) a la que se ven: muy baja, para que se note solo
# si se presta atención. APARICION_RARA_FUNDIDO es qué parte de su duración
# se va en entrar y otra igual en salir.
APARICION_RARA_OPACIDAD = 34
APARICION_RARA_FUNDIDO = 0.3

# --- Alerta de peligro (alguien en el Primer Patio) ---
# Con alguien acechando, la imagen va y viene entre color y un blanco y negro
# más oscuro, y tiembla. Cada par (llegada, ataque) se interpola con lo cerca
# que está el ataque más próximo: el vaivén se acelera (segundos de un ciclo
# completo) y el temblor crece (píxeles). PELIGRO_OSCURIDAD es la opacidad
# (0-255) del negro que se le pone encima en el punto más gris.
PELIGRO_PERIODO_SEGUNDOS = (1.6, 0.2)
PELIGRO_TEMBLOR_PIXELES = (1, 12)
PELIGRO_OSCURIDAD = 90

# --- Punto débil (espantar con la luz) ---
# Se dibuja debajo de la penumbra, como la figura: solo se ve con el haz
# encima. El halo late para leerse sobre cualquier ropa, y alrededor un arco
# va marcando lo sostenido.
PUNTO_DEBIL_COLOR = (255, 238, 160)
PUNTO_DEBIL_OPACIDAD_HALO = (70, 150)  # mínima y máxima del latido
PUNTO_DEBIL_LATIDOS_POR_SEGUNDO = 3.0
PUNTO_DEBIL_RADIO_NUCLEO = 6
PUNTO_DEBIL_COLOR_PROGRESO = (120, 225, 255)
PUNTO_DEBIL_GROSOR_PROGRESO = 5

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

# Mientras El Chavo está en la cámara que se mira, el monitor se vuelve
# errático (ver presentacion/monitor_erratico.py): la imagen tiembla a
# tirones y el mapa se va a saltos, con sus botones, para que escapar de su
# cámara cueste. La intensidad arranca en CAMARA_ERRATICO_INTENSIDAD_MINIMA
# nada más verlo y sube con la presión del sabotaje hasta 1.
# Amplitud en píxeles (x, y), cada cuánto cambia de destino (mín, máx) y
# qué tan rápido lo persigue, por segundo. Esos valores son los de El Chavo
# con nivel 20: con menos nivel se escalan por los factores *_POR_IA (nivel
# 1, nivel 20), la amplitud de los saltos y su ritmo.
CAMARA_ERRATICO_INTENSIDAD_MINIMA = 0.6
CAMARA_ERRATICO_AMPLITUD_POR_IA = (0.3, 1.0)
CAMARA_ERRATICO_RITMO_POR_IA = (0.35, 1.0)
CAMARA_ERRATICO_MAPA_AMPLITUD = (260, 170)
CAMARA_ERRATICO_MAPA_CAMBIO_SEGUNDOS = (0.18, 0.45)
CAMARA_ERRATICO_MAPA_PERSECUCION = 14.0
CAMARA_ERRATICO_VISTA_AMPLITUD = (45, 28)
CAMARA_ERRATICO_VISTA_CAMBIO_SEGUNDOS = (0.04, 0.12)
CAMARA_ERRATICO_VISTA_PERSECUCION = 30.0

# Objetos que se buscan en las cámaras (la escoba y el café): alto con que se
# dibujan, en píxeles, y cuánto se apagan (0-255, 255 es tal cual) para que
# no brillen sobre la penumbra de las cámaras. Dónde quedan es una regla de
# juego y vive en config/jugabilidad.py.
OBJETO_BUSCADO_ALTO = {"escoba": 170, "cafe": 90}
OBJETO_BUSCADO_BRILLO = 175

# Ruido de señal sobre la imagen de la cámara.
CAMARA_ESTATICA_FRAMES = 6
CAMARA_ESTATICA_OPACIDAD = 15
CAMARA_ESTATICA_ANCHO = ANCHO_PANTALLA // 4
CAMARA_ESTATICA_ALTO = ALTO_PANTALLA // 4
CAMARA_ESTATICA_CAMBIO_FRAMES = 4  # cada cuántos fotogramas se cambia de cuadro

# Ráfaga de estática al saltar de una cámara a otra.
CAMARA_TRANSICION_SEGUNDOS = 0.3
CAMARA_TRANSICION_OPACIDAD = 200

# Lo que dura la animación de encender el monitor (los cuadros "pos N.png":
# el aparato bajando del techo hasta quedar delante de la cara). Es tiempo en
# el que el jugador no ve ni el patio ni las cámaras, así que se mantiene
# corta a propósito: el efecto de sonido dura bastante más y sigue oyéndose
# con la imagen ya puesta, como el zumbido del tubo al calentarse.
CAMARA_ENCENDIDO_SEGUNDOS = 0.6

# Bajarlo no repite la ráfaga entera al revés: se enseña un solo cuadro del
# aparato ya despegado de la cara y desaparece. Volver al patio es lo que se
# hace cuando algo va mal, y ahí no puede haber medio segundo de monitor
# tapando la vista.
CAMARA_SALIDA_SEGUNDOS = 0.12

# Rato que las pestañas de abajo se quedan muertas después de bajar un panel.
# El monitor se baja con el ratón justo encima de esa franja, así que sin esta
# pausa el más leve movimiento vuelve a levantarlo antes de que al jugador le
# dé tiempo a apartar la mano.
TIRAS_BLOQUEO_SEGUNDOS = 0.5

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
# Al perder, el personaje que atrapó al jugador se le echa encima antes de la
# pantalla de game over (ver presentacion/jumpscare.py). Dura lo mismo que el
# efecto de sonido del susto; sin audio, SUSTO_DURACION_NATURAL.
SUSTO_DURACION_NATURAL = 3.3
# En qué punto de esa duración llega el golpe (el último cuadro). Antes, los
# cuadros del acercamiento se aceleran; después, la cara se queda encima.
SUSTO_PROPORCION_GOLPE = 0.53
# Cuánto se acerca la cámara mientras viene, y el zoom de más con el que
# entra el golpe antes de asentarse en SUSTO_ZOOM_REPOSO.
SUSTO_ZOOM_ACERCAMIENTO = 0.12
SUSTO_ZOOM_GOLPE = 0.22
SUSTO_ZOOM_REPOSO = 1.18
# Quien no tiene cuadros de susto propios se acerca con su sprite normal,
# que arranca a este tamaño y crece hasta ocupar la pantalla. Del sprite se
# usa solo esta parte de arriba de la figura (cabeza y pecho), para que el
# golpe sea un primer plano de la cara y no el cuerpo entero.
SUSTO_ZOOM_INICIAL_SIN_CUADROS = 0.55
SUSTO_PROPORCION_CARA_SIN_CUADROS = 0.45
# Temblor en píxeles: crece hasta el máximo del acercamiento, da un golpe
# fuerte al llegar y se queda en un temblor de fondo.
SUSTO_TEMBLOR_ACERCAMIENTO = 9
SUSTO_TEMBLOR_GOLPE = 30
SUSTO_TEMBLOR_FONDO = 4
# Parpadeo de luz durante el acercamiento: con qué probabilidad se apaga en
# cada fotograma y cuánto.
SUSTO_PARPADEO_PROBABILIDAD = 0.18
SUSTO_PARPADEO_OPACIDAD = (90, 170)
# Destello blanco del golpe: corto, para no tapar la cara que llega.
SUSTO_DESTELLO_OPACIDAD = 170
SUSTO_DESTELLO_SEGUNDOS = 0.07
SUSTO_VELO_COLOR = (170, 0, 0)
SUSTO_VELO_OPACIDAD = 110
# Estática: leve durante todo el susto, un golpe en el impacto y al final
# tapa la imagen entera durante SUSTO_ESTATICA_CIERRE_SEGUNDOS.
SUSTO_ESTATICA_FONDO = 12
SUSTO_ESTATICA_GOLPE = 60
SUSTO_ESTATICA_CIERRE_SEGUNDOS = 0.35
# Oscurecimiento de los bordes (0-255 en las esquinas).
SUSTO_VINETA_OPACIDAD = 150

# Cómo se arma el susto de quien no sigue la regla por defecto, que es poner
# todos sus "jump N.png" en orden y usar el último como golpe. Va por carpeta
# de assets/animatronics/:
#
# - "acercamientos": de dónde sale el acercamiento; en cada muerte se sortea
#   uno. Cada entrada es una hoja de propuesta (una cuadrícula de cuadros con
#   separadores blancos o negros) con los cuadros que se usan, numerados de
#   izquierda a derecha y de arriba abajo empezando en 1. La entrada
#   ACERCAMIENTO_CON_JUMPS usa en cambio esos "jump N.png" sueltos.
# - "golpes": qué "jump N.png" pueden ser el golpe final; sale uno al azar.
#   None son todos los de la carpeta.
# - "recortes" (opcional): píxeles que se le quitan a cada cuadro de una hoja
#   por (izquierda, arriba, derecha, abajo), para tapar lo que no es arte.
ACERCAMIENTO_CON_JUMPS = "jump"
SUSTOS_COMPUESTOS = {
    "florinda": {
        "acercamientos": {
            "propuesta 1.png": (1, 2, 3, 4, 5, 6, 7),
            # El 6 la aleja otra vez (levanta el palo de lejos) y rompe el
            # acercamiento, así que se salta.
            "propuesta 2.png": (1, 2, 3, 4, 5, 7),
        },
        "golpes": None,
    },
    "chavo": {
        "acercamientos": {
            # Mismo caso que la propuesta 2 de Florinda: el 6 lo aleja.
            "propuesta 1.png": (1, 2, 3, 4, 5, 7),
        },
        # Sus "jump" son una secuencia: del 1 al 4 todavía viene de lejos y
        # el 9 y el 10 son el después. Para el golpe solo sirven los de
        # encima.
        "golpes": (5, 6, 7, 8),
    },
    "jaimico": {
        "acercamientos": {
            # El 9 es un grito aún más cerca que el golpe: se deja fuera
            # para no restarle fuerza.
            "propuesta 1.png": (1, 2, 3, 4, 5, 6, 7, 8),
            # El 6 es cuando lanza la bolsa contra el jugador.
            ACERCAMIENTO_CON_JUMPS: (1, 2, 3, 4, 5, 6),
        },
        # El 8 y el 9 son el después; el golpe es el grito del 7.
        "golpes": (7,),
        "recortes": {
            # Cada cuadro de la hoja trae su número en un círculo arriba a la
            # izquierda; quitando esa franja el número no sale en el susto.
            "propuesta 1.png": (52, 0, 0, 0),
        },
    },
    "bruja": {
        "acercamientos": {
            # Como en la de Jaimico, el 9 es más de cerca que el golpe.
            "propuesta 1.png": (1, 2, 3, 4, 5, 6, 7, 8),
            # El 6 la aleja otra vez (se abalanza desde más lejos).
            ACERCAMIENTO_CON_JUMPS: (1, 2, 3, 4, 5),
        },
        # El 7 es la carcajada encima y el 8 el estallido rojo; el 9 es el
        # después.
        "golpes": (7, 8),
        "recortes": {
            # Cada cuadro trae un marco gris fino y su número escrito arriba
            # a la izquierda.
            "propuesta 1.png": (30, 4, 4, 4),
        },
    },
}
# Los cuadros de una propuesta son pequeños: se agrandan menos que los "jump"
# verticales (SUSTO_ZOOM) para que no se vean tan borrosos.
SUSTO_ZOOM_PROPUESTA = 1.2

# Cuánto se agranda cada cuadro respecto a ajustarlo solo por el alto de
# pantalla, para que ocupe más del escenario en vez de quedar como una tira
# angosta. Como los cuadros son retratos verticales, agrandar de más obliga a
# recortar mucho arriba y abajo; 1.5 es un punto medio que ya se probó y no
# corta cabeza ni manos en los cuadros existentes.
SUSTO_ZOOM = 1.5

# --- Botón de audio del monitor de cámaras ---
# Suena la grabación de Quico en la cámara que se mira, y Doña Florinda va
# hacia allá si es vecina de la suya. Va abajo a la izquierda, en el hueco que queda entre la
# fecha del HUD y el mapa de la vecindad.
# Mientras suena, la cámara donde se puso muestra ondas que se abren desde
# el centro: así se ve en qué cámara se está oyendo.
CAMARA_AUDIO_EFECTO_SEGUNDOS = 2.0
CAMARA_AUDIO_ONDAS = 3
CAMARA_AUDIO_ONDA_PERIODO = 0.9  # segundos que tarda una onda en abrirse
CAMARA_AUDIO_ONDA_RADIO_MAXIMO = 280
CAMARA_AUDIO_ONDA_GROSOR = 4
CAMARA_AUDIO_ONDA_COLOR = (170, 225, 255)
# Cuando Doña Florinda se mueve, la cámara que se esté mirando (sea cual
# sea) da un tirón breve: estática y la imagen corrida unos píxeles.
CAMARA_DISTORSION_SEGUNDOS = 0.4
CAMARA_DISTORSION_DESPLAZAMIENTO = 10
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

# --- Menú de noche superada (serpentina) ---
# Tiras de colores cayendo, generadas por código (no hay asset para esto).
# Cada una es un segmento de línea que gira mientras cae y se balancea de
# lado a lado; al salir por abajo reaparece arriba, así que la cantidad de
# tiras en pantalla se mantiene constante durante todo el menú.
CONFETI_CANTIDAD = 70
CONFETI_LARGO_MINIMO = 10
CONFETI_LARGO_MAXIMO = 22
CONFETI_GROSOR = 4
CONFETI_CAIDA_MINIMA = 60   # píxeles por segundo
CONFETI_CAIDA_MAXIMA = 140
CONFETI_GIRO_MAXIMO = 120   # grados por segundo, en cualquier sentido
CONFETI_BALANCEO_AMPLITUD = 30  # píxeles que se desplaza de lado a lado
CONFETI_COLORES = (
    (230, 200, 60),   # amarillo aviso, el mismo tono que ya usa la interfaz
    (200, 60, 60),
    (80, 200, 120),   # verde energía, el mismo tono que "sobreviviste"
    (90, 150, 230),
    (230, 230, 230),
)
