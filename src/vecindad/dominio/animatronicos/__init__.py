"""Los animatrónicos: el elenco de la vecindad avanzando por su recorrido
hasta llegar al Primer Patio, donde está el jugador.

El módulo está partido por responsabilidad:

- nombres.py        -> el nombre de cada personaje, para no repetir literales
- definicion.py     -> ConfiguracionAnimatronic: la ficha fija de un personaje
- entidad.py        -> Animatronic: su estado vivo durante la noche y la IA 0-20
- elenco.py         -> los siete grafos de recorrido y su validación
- progresion.py     -> qué nivel tiene cada uno en cada noche de la campaña
- enfrentamiento.py -> qué pasa cara a cara: luz mortal y objetos arrojados

Este archivo reexporta lo que usa el resto del juego, así que basta con
`from vecindad.dominio.animatronicos import crear_elenco_noche`.
"""

from . import nombres
from .definicion import POSES_POR_PERSONAJE, ConfiguracionAnimatronic, Destinos
from .elenco import (
    ELENCO,
    NOMBRE_TODO_EL_ELENCO,
    VISTAS_DEL_PATIO,
    carpetas_de_atacantes,
    grupos_de_escena,
    habitaciones_posibles,
    habitaciones_que_se_dibujan,
    nombres_del_elenco,
    nombres_reconocidos_en_escenas,
    prefijos_por_nombre,
    validar_elenco,
)
from .enfrentamiento import (
    ResultadoArrojo,
    acechando,
    acechando_en,
    detectar_luz_mortal,
    detectar_luz_que_descarga,
    esta_en_tregua,
    iluminados_en,
    resolver_arrojo,
)
from .entidad import Animatronic, limitar_nivel_ia
from .progresion import (
    HORA_ARRANQUE_POR_NOCHE,
    INTERVALO_POR_NOCHE,
    NIVELES_POR_NOCHE,
    crear_elenco_noche,
    crear_elenco_personalizado,
    hora_de_arranque,
    intervalo_de_movimiento,
    niveles_iniciales_personalizada,
)

__all__ = [
    "nombres",
    "Animatronic",
    "ConfiguracionAnimatronic",
    "Destinos",
    "ELENCO",
    "HORA_ARRANQUE_POR_NOCHE",
    "INTERVALO_POR_NOCHE",
    "NIVELES_POR_NOCHE",
    "NOMBRE_TODO_EL_ELENCO",
    "VISTAS_DEL_PATIO",
    "acechando",
    "grupos_de_escena",
    "POSES_POR_PERSONAJE",
    "ResultadoArrojo",
    "acechando_en",
    "carpetas_de_atacantes",
    "crear_elenco_noche",
    "crear_elenco_personalizado",
    "detectar_luz_mortal",
    "detectar_luz_que_descarga",
    "esta_en_tregua",
    "habitaciones_posibles",
    "habitaciones_que_se_dibujan",
    "hora_de_arranque",
    "iluminados_en",
    "intervalo_de_movimiento",
    "limitar_nivel_ia",
    "nombres_del_elenco",
    "nombres_reconocidos_en_escenas",
    "niveles_iniciales_personalizada",
    "prefijos_por_nombre",
    "resolver_arrojo",
    "tiene_respuesta_para",
    "validar_elenco",
]
