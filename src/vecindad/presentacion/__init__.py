"""Todo lo que se dibuja en pantalla.

Lee el estado del dominio y lo pinta; nunca decide reglas de juego. Si algo
tiene que ver con "qué pasa" y no con "cómo se ve", su sitio es dominio/.

- menu/             -> menú principal, ajustes, noche personalizada y pausa
- camaras.py        -> el monitor de vigilancia a pantalla completa
- animacion_monitor.py-> el monitor entrando y saliendo de la vista
- mapa_camaras.py   -> el mapa de la vecindad que hace de selector de cámara
- vista.py          -> lo que el jugador ve desde su posición, con la linterna
- hud.py            -> noche, hora, batería, inventario y pantallas de final
- panel_servicios.py-> el tablero de servicios del barril
- iconos.py         -> los iconos de objetos recortados de su hoja
- efectos.py        -> estática y líneas de barrido, precalculadas
"""

from .camaras import SistemaCamaras
from .hud import EstadoHud, InterfazJuego
from .iconos import IconosObjetos
from .menu import MenuPausa, MenuPrincipal, SolicitudNoche
from .panel_servicios import PanelServicios
from .vista import VistaJugador

__all__ = [
    "EstadoHud",
    "IconosObjetos",
    "InterfazJuego",
    "MenuPausa",
    "MenuPrincipal",
    "PanelServicios",
    "SistemaCamaras",
    "SolicitudNoche",
    "VistaJugador",
]
