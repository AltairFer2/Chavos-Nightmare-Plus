"""Las reglas del juego, independientes de cómo se dibujen o se oigan.

Regla de la capa: **aquí no se importa pygame**. Nada de este paquete puede
depender de una superficie, una fuente, un sonido ni un evento de teclado.
A cambio, todo lo de aquí se puede probar sin abrir una ventana (ver tests/).

- animatronicos/ -> el elenco, su IA 0-20, el cara a cara y espantar con la luz
- jugador.py     -> por dónde se mueve el jugador dentro del hub
- linterna.py    -> batería, haz de luz y qué queda iluminado
- objetos.py     -> las baterías que aparecen en el suelo de los Lavaderos
- servicios.py   -> los cuatro servicios de utilidad del barril
- sabotaje.py    -> El Chavo arruinando las cámaras si se le mira de más
- interferencia.py-> cámaras que pierden la señal al moverse alguien delante
- temporizador.py-> el reloj de la noche y los ticks que mueven al elenco
"""
