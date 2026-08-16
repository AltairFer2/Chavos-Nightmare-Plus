"""Configuración del juego, repartida por área temática.

Es la capa base: no depende de ninguna otra parte del paquete (ni de pygame),
y cualquier capa puede importar de aquí.

- ventana.py     -> lienzo base, resoluciones, FPS y título
- rutas.py       -> dónde están los assets y los datos del jugador
- audio.py       -> carpetas de audio, mapa de pistas y volúmenes
- partida.py     -> reloj de la noche, ticks de IA y progresión de noches
- jugabilidad.py -> linterna, objetos, servicios y sabotaje (equilibrio)
- interfaz.py    -> colores, tipografía y distribución de la interfaz

Se importa siempre por módulo (`from vecindad.config import jugabilidad` o
`from vecindad.config.jugabilidad import LINTERNA_RADIO`) para que en cada
archivo se vea de qué área viene cada número.
"""
