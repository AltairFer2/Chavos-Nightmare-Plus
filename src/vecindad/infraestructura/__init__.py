"""Todo lo que habla con el mundo exterior: disco, tarjeta de sonido y ventana.

Aísla al resto del juego de que un archivo falte, de que no haya dispositivo
de audio o de que el monitor tenga otra resolución. Cuando algo no está, estos
módulos devuelven None o se quedan en silencio en vez de reventar, para que
el juego siga corriendo mientras el arte está en producción.

- recursos.py -> carga de imágenes con caché
- fuentes.py  -> creación de tipografías con caché
- audio.py    -> música y efectos, con el modo streamer
- pantalla.py -> ventana, escalado del lienzo y coordenadas del ratón
- guardado.py -> progreso y preferencias en JSON
"""

from .audio import GestorAudio
from .fuentes import crear_fuente
from .guardado import (
    Configuracion,
    ProgresoJugador,
    existe_configuracion_guardada,
)
from .pantalla import GestorPantalla
from .recursos import CacheImagenes, cargar_imagen, quitar_fondo_negro

__all__ = [
    "CacheImagenes",
    "Configuracion",
    "GestorAudio",
    "GestorPantalla",
    "ProgresoJugador",
    "cargar_imagen",
    "crear_fuente",
    "existe_configuracion_guardada",
    "quitar_fondo_negro",
]
