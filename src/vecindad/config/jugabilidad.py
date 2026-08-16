"""Números que definen las mecánicas: linterna, objetos del suelo, servicios
del barril y sabotaje de las cámaras.

Es el archivo que se toca para equilibrar el juego. No contiene nada de
render: lo visual vive en config/interfaz.py.
"""

from .interfaz import ALTO_ANIMATRONIC_VISTA

# --- Linterna ---
# Segundos de luz que da una batería con la linterna encendida sin parar.
LINTERNA_DURACION_BATERIA_SEGUNDOS = 120.0
# Radio (en píxeles del lienzo base) del círculo iluminado alrededor del
# puntero. Decide qué alcanza a ver el jugador, así que es una regla de
# juego y no solo un parámetro de dibujo.
LINTERNA_RADIO = 220

# Radio dentro del cual apuntar la luz a un animatrónico sensible a ella es
# mortal. Crece con su nivel_ia: a nivel bajo se le puede rozar con el borde
# del haz sin morir; a nivel alto casi cualquier destello lo activa.
LUZ_RADIO_PELIGRO_MINIMO = 70
LUZ_RADIO_PELIGRO_MAXIMO = 210

# Altura del torso de un personaje sobre el punto donde pisa. Es el punto
# contra el que se mide la linterna: el jugador apunta al cuerpo, no a los
# pies. Se deriva del alto con que se dibuja la figura para que ambos sigan
# cuadrando si se cambia el tamaño del arte.
ALTURA_TORSO = ALTO_ANIMATRONIC_VISTA // 2

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
OBJETO_PROBABILIDAD_BASE = 0.55
OBJETO_PROBABILIDAD_MINIMA = 0.15
OBJETO_REDUCCION_POR_NOCHE = 0.08

# El churrumino arrojado solo entretiene a El Chavo este rato, en vez de
# ahuyentarlo como hacen los demás objetos.
SEGUNDOS_RETRASO_CHURRUMINO = 5.0

# --- Servicios de utilidad del barril ---
SERVICIO_AUDIO_SEGUNDOS = 5.0
SERVICIO_CAMARAS_SEGUNDOS = 7.0
SERVICIO_TODO_SEGUNDOS = 20.0
BARRIGA_COOLDOWN_SEGUNDOS = 5.0
NOCHE_AUDIO_LIMITADO = 2  # desde esta noche el audio deja de ser ilimitado
# Reproducciones del audio de Quico que trae cada noche. La primera es
# ilimitada (es donde se aprende a usarlo) y de ahí en adelante se van
# racionando. Al agotarse hay que reponerlas con "Restablecer todo" desde el
# panel del barril. Las noches que no aparezcan usan USOS_AUDIO_QUICO.
USOS_AUDIO_POR_NOCHE = {2: 5, 3: 4, 4: 3, 5: 3}
USOS_AUDIO_QUICO = 3

# Cuánto tarda en llegar el Sr. Barriga cuando se le llama sin necesidad (Don
# Ramón no acechando): un rango al azar, no un golpe inmediato, para que la
# espera se sienta como una amenaza suelta por ahí y no como un error de
# clic. Una vez arrancada la cuenta no se reinicia aunque se vuelva a llamar.
BARRIGA_LLEGADA_MINIMA_SEGUNDOS = 5.0
BARRIGA_LLEGADA_MAXIMA_SEGUNDOS = 15.0

# --- Sabotaje de las cámaras ---
# Segundos seguidos que aguanta El Chavo siendo observado antes de arruinar
# las cámaras. El contador baja solo si se deja de mirarlo.
CAMARA_SABOTAJE_SEGUNDOS = 8.0
CAMARA_SABOTAJE_RECUPERACION = 0.5  # cuánto se enfría por segundo sin mirarlo
