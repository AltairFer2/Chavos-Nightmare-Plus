"""La capa de aplicación: el bucle principal y el estado global.

Es la única que conoce a todas las demás y la que las conecta entre sí.
Coordina, no decide: las reglas están en dominio/ y el dibujo en presentacion/.

- juego.py   -> la clase Juego: composición, bucle y orquestación
- estados.py -> menú, jugando, game over y victoria
- noche.py   -> el estado de la noche en curso y cómo terminó
- entrada.py -> qué tecla hace qué
- aviso.py   -> el mensaje corto que aparece y se borra solo
"""

from .estados import EstadoJuego, GestorEstados
from .juego import Juego, main
from .noche import Noche

__all__ = ["EstadoJuego", "GestorEstados", "Juego", "Noche", "main"]
