Proyecto: Juego tipo Five Nights at Freddy's con temática de "El Chavo del Ocho"



LENGUAJE Y HERRAMIENTAS

\- Lenguaje: Python 3

\- Librería principal: pygame

\- Empaquetado final: pyinstaller (generar .exe standalone)



TEMÁTICA

\- Personajes del elenco de El Chavo del Ocho como animatrónicos (ej. Señor Barriga, Don Ramón, etc.)

\- Arte, diseño de escenarios, personajes y animaciones: generados con herramientas externas (no en código); el código solo los carga y reproduce.



ARQUITECTURA / ESTRUCTURA DEL PROYECTO (propuesta)

\- main.py            -> loop principal del juego, inicialización de pygame

\- game\_state.py       -> máquina de estados global (menú, jugando, game over, victoria)

\- camaras.py          -> lógica del sistema de cámaras (cambio de vista, estática/ruido)

\- animatronics.py     -> clase base Animatronic + subclases por personaje (IA, movimiento entre habitaciones)

\- habitaciones.py     -> definición del mapa/grafo de habitaciones y conexiones entre cámaras

\- temporizador.py     -> manejo de energía/tiempo límite (ej. noche de 12am-6am)

\- sprites/            -> carpeta de assets gráficos (imágenes, spritesheets)

\- sonidos/            -> carpeta de assets de audio

\- ui.py               -> interfaz (pantalla de cámaras, botones, energía, power)



MECÁNICAS PRINCIPALES A DESARROLLAR

\- Sistema de cámaras (cambiar entre vistas de habitaciones)

\- Temporizador de energía/tiempo (recurso limitado que se agota)

\- Máquina de estados por personaje (idle, moviéndose, atacando)

\- Manejo de sprites y animaciones (carga de spritesheets, control de frames)

\- Detección de eventos (ej. personaje llega a la puerta -> jugador debe reaccionar)



FLUJO DE TRABAJO

\- Claude ayuda a escribir/estructurar el código.

\- Altair genera arte y assets con herramientas externas y los provee.

\- Altair ejecuta y prueba cada avance de forma iterativa.

