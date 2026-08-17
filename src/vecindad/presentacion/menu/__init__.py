"""Menú principal y sus dos subpantallas, más el menú de pausa.

- modelo.py     -> SolicitudNoche, EntradaMenu y en qué sección se está
- secciones.py  -> qué opciones muestra cada sección del menú principal
- ajustes.py    -> ControlAjustes: qué hace cada opción de Ajustes
- deslizador.py -> las barras de volumen de Ajustes
- fondo.py      -> el fondo animado y el logotipo
- principal.py  -> MenuPrincipal, que junta todo lo anterior
- pausa.py      -> MenuPausa: reanudar, ajustes o volver al menú principal

Los dos menús comparten ControlAjustes, así que ofrecen exactamente las
mismas preferencias.
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
