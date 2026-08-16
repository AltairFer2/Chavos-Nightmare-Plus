"""Menú principal y sus dos subpantallas, más el menú de pausa.

- modelo.py     -> SolicitudNoche, EntradaMenu y en qué sección se está
- secciones.py  -> qué opciones muestra cada sección del menú principal
- deslizador.py -> las barras de volumen de Ajustes
- fondo.py      -> el fondo animado y el logotipo
- principal.py  -> MenuPrincipal, que junta todo lo anterior
- pausa.py      -> MenuPausa: reanudar, sonido o volver al menú principal
"""

from .modelo import EntradaMenu, SeccionMenu, SolicitudNoche
from .pausa import SOLICITUD_MENU_PRINCIPAL, SOLICITUD_REANUDAR, MenuPausa
from .principal import MenuPrincipal

__all__ = [
    "EntradaMenu",
    "MenuPausa",
    "MenuPrincipal",
    "SeccionMenu",
    "SOLICITUD_MENU_PRINCIPAL",
    "SOLICITUD_REANUDAR",
    "SolicitudNoche",
]
