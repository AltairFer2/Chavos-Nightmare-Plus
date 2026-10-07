"""Números que definen las mecánicas: linterna, baterías del suelo, espantar
con la luz, objetos que se buscan en las cámaras, servicios del barril y
sabotaje de las cámaras.

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

# Repuestos que caben en el bolsillo. Con el bolsillo lleno la batería del
# suelo no se puede recoger, así que acaparar no sirve de nada: hay que
# gastar para poder llevarse otra. Las primeras noches se arranca justo con
# el tope puesto (BATERIAS_INICIALES_EN_BARRIL).
LINTERNA_BATERIAS_MAXIMAS = 2

# Lo único que se encuentra tirado son baterías, siempre en el mismo sitio de
# los Lavaderos y con tiempos fijos, sin sorteo (ver dominio/objetos.py). El
# suelo queda vacío BATERIA_ESPERA_* segundos, aparece una y, si nadie la
# recoge en BATERIA_PERMANENCIA_* segundos, se va y vuelve a correr la espera.
# Como la linterna es también el arma, cada batería cuenta: conforme avanzan
# las noches salen más espaciadas y duran menos tiradas. Las noches que no
# aparezcan (la personalizada) usan los valores por defecto.
BATERIA_ESPERA_POR_NOCHE = {1: 20.0, 2: 25.0, 3: 30.0, 4: 35.0, 5: 40.0, 6: 45.0}
BATERIA_ESPERA_SEGUNDOS = 35.0
BATERIA_PERMANENCIA_POR_NOCHE = {1: 12.0, 2: 11.0, 3: 10.0, 4: 9.0, 5: 8.0, 6: 7.0}
BATERIA_PERMANENCIA_SEGUNDOS = 9.0

# --- Espantar con la luz (ver dominio/espanto.py) ---
# A quien se espanta con la luz se le ve un punto débil que se mueve a
# tirones por su cuerpo. Hay que sostener el centro del haz (el cursor)
# encima hasta llenar la barra; si se pierde, la barra baja. Todo escala con
# el nivel_ia, del primer valor (nivel 1) al segundo (nivel 20).
#
# Por dónde se mueve el punto: una elipse centrada en el torso, de la cabeza
# a las rodillas.
PUNTO_DEBIL_SEMIANCHO = 80
PUNTO_DEBIL_SEMIALTO = ALTURA_TORSO - 90
# Distancia del cursor al punto dentro de la cual cuenta como sostenido.
PUNTO_DEBIL_RADIO = (50, 28)
# Segundos sostenidos sin perderlo que hacen falta para espantarlo.
PUNTO_DEBIL_SEGUNDOS = (1.5, 3.0)
# Píxeles por segundo a los que corre el punto hacia su siguiente destino.
PUNTO_DEBIL_VELOCIDAD = (120.0, 320.0)
# Cada cuánto cambia de destino (mínimo, máximo), en segundos.
PUNTO_DEBIL_CAMBIO_SEGUNDOS = ((0.8, 1.6), (0.3, 0.8))
# Qué parte de la barra se pierde por cada segundo fuera del punto.
PUNTO_DEBIL_DRENADO = 0.4
# La Chilindrina castiga fallar: alumbrarle el cuerpo fuera del punto más de
# este rato seguido le descarga la batería entera al jugador.
CHILINDRINA_GRACIA_SEGUNDOS = 0.6
# Jaimico es el más difícil de espantar: su punto débil se porta siempre
# como el de este punto de la escala (0.0 es nivel 1 y 1.0 nivel 20), sea
# cual sea su nivel. Ojo, la dificultad no sube pareja: por encima de ~0.5
# el punto corre más de lo que el jugador tarda en reaccionar y se vuelve
# casi imposible (medido con un jugador simulado: con 0.5 tarda ~7 s y falla
# 1 de cada 14 intentos; con 1.0 no lo logra nunca).
PUNTO_DEBIL_FACTOR_MAS_DIFICIL = 0.5

# --- Objetos que se buscan en las cámaras (ver dominio/busqueda.py) ---
# Al aparecer Doña Clotilde (escoba) o Jaimico (café), su objeto se esconde
# en una cámara al azar, nunca en la del Chavo (8, solo tiene micrófono), y
# hay que encontrarlo y hacerle clic antes de que se acabe el tiempo.
# Doña Clotilde: el tiempo depende de lo lejos del Primer Patio que haya
# aparecido: BUSQUEDA_SEGUNDOS_MINIMOS en las cámaras que dan al patio y
# BUSQUEDA_SEGUNDOS_POR_PASO más por cada paso extra (las del Segundo
# Patio). Jaimico: depende de su nivel (ver su ficha en elenco.py).
BUSQUEDA_SEGUNDOS_MINIMOS = 10.0
BUSQUEDA_SEGUNDOS_POR_PASO = 5.0
# Sitios del monitor (lienzo de 1280x720) donde puede quedar el objeto. Están
# lejos del mapa, del botón de audio, del HUD y de los rótulos del marco.
SITIOS_OBJETOS_BUSCADOS = (
    (380, 470), (430, 300), (620, 480), (760, 250),
    (290, 540), (560, 380), (200, 300), (700, 400),
)
# Distancia del clic al centro del objeto dentro de la cual se encuentra.
OBJETO_BUSCADO_RADIO_CLIC = 70

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
# Segundos tras sonar el audio de Quico antes de poder sonarlo otra vez,
# en esa cámara o en cualquier otra: no se puede arrear a Doña Florinda a
# fuerza de clics.
AUDIO_QUICO_ESPERA_SEGUNDOS = 3.0

# Cuánto tarda en llegar el Sr. Barriga cuando se le llama sin necesidad (Don
# Ramón no acechando): un rango al azar, no un golpe inmediato, para que la
# espera se sienta como una amenaza suelta por ahí y no como un error de
# clic. Una vez arrancada la cuenta no se reinicia aunque se vuelva a llamar.
BARRIGA_LLEGADA_MINIMA_SEGUNDOS = 5.0
BARRIGA_LLEGADA_MAXIMA_SEGUNDOS = 15.0

# --- Sabotaje de las cámaras ---
# Segundos que aguanta El Chavo siendo observado antes de arruinar las
# cámaras: 2 s en las noches 3 y 4 y 1 s en el resto (y en la personalizada,
# CAMARA_SABOTAJE_SEGUNDOS). Con 8 s bastaba con cambiar de cámara al verlo.
CAMARA_SABOTAJE_POR_NOCHE = {3: 2.0, 4: 2.0}
CAMARA_SABOTAJE_SEGUNDOS = 1.0
# Cuánto se enfría la presión por cada segundo sin mirarlo. Es lento a
# propósito: los vistazos cortos se van sumando, así que volver a su cámara
# una y otra vez también las rompe.
CAMARA_SABOTAJE_RECUPERACION = 0.2
# A partir de esta proporción de la presión el monitor empieza a fallar, para
# que el jugador sepa que tiene que quitar la vista ya.
CAMARA_SABOTAJE_AVISO = 0.5

# --- Apariciones raras (easter eggs) ---
# Cada segundo de partida se tira 1 entre N a que se cuele una de las
# imágenes de assets/eggs/. N baja conforme avanza la campaña (más
# probable): 1 entre 10000 la noche 1 y 1 entre 5000 la 5 y la 6. Las noches
# que no aparezcan (la personalizada) usan APARICION_RARA_UNO_ENTRE.
APARICION_RARA_UNO_ENTRE_POR_NOCHE = {
    1: 10000, 2: 8750, 3: 7500, 4: 6250, 5: 5000, 6: 5000,
}
APARICION_RARA_UNO_ENTRE = 5000
# Cuánto dura a la vista, contando la entrada y la salida.
APARICION_RARA_SEGUNDOS = 3.0

# --- Interferencia por movimiento ---
# Cuánto se queda sin señal una cámara cuando alguien se mueve justo mientras
# el jugador la está mirando. Sale un tiempo al azar dentro de este rango, así
# que no se puede contar los segundos de memoria para saber cuándo vuelve.
# Esta avería se arregla sola: no es el sabotaje de El Chavo, que deja todo el
# circuito caído hasta ir a restablecerlo al barril.
CAMARA_INTERFERENCIA_MINIMA_SEGUNDOS = 3.0
CAMARA_INTERFERENCIA_MAXIMA_SEGUNDOS = 6.0
