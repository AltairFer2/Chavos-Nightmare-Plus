"""Nombre de cada personaje del elenco, en un único sitio.

Varios módulos necesitan referirse a un personaje concreto: el audio que
empuja a Doña Florinda, el servicio que se lleva a Don Ramón, quién arruina las
cámaras. Tenerlos aquí evita repartir el mismo literal por medio proyecto y
que una tilde mal puesta rompa una mecánica en silencio.

Este módulo no importa nada a propósito: cualquier capa puede usarlo sin
arrastrar consigo el elenco completo (que al cargarse valida los sprites).
"""

DON_RAMON = "Don Ramón"
FLORINDA = "Doña Florinda"
CHILINDRINA = "La Chilindrina"
QUICO = "Quico"
CHAVO = "El Chavo"
JAIMICO = "Jaimico"
CLOTILDE = "Doña Clotilde"

# No forma parte del elenco que recorre la vecindad: solo aparece si se le
# llama desde el barril, y si no había a quién cobrarle, se cobra con el
# jugador.
BARRIGA = "Señor Barriga"

# Personaje que arruina las cámaras si se le observa demasiado rato seguido.
SABOTEADOR = CHAVO

# Otras formas de llamar a un personaje en los nombres de archivo de las
# escenas de cámara (ver presentacion/escenas_camara.py). A Doña Clotilde se
# la conoce como "la bruja del 71" y a Jaimico se le escribe como el Jaimito
# de la serie, así que los assets usan indistintamente unos u otros.
#
# La clave es el nombre corto tal cual aparece en el archivo; el valor, el
# nombre corto oficial del personaje (su prefijo_sprite). Añadir aquí una
# forma nueva es todo lo que hace falta para que esos archivos se reconozcan.
ALIAS_EN_ESCENAS = {
    "bruja": "clotilde",
    "jaimito": "jaimico",
}
