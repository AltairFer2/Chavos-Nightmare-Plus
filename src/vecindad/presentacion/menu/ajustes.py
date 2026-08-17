"""Qué hace cada opción de la pantalla de Ajustes.

Vive aparte porque hay dos sitios desde donde se llega a ella: el menú
principal y el de pausa. Antes solo el principal podía tocarlas, y el de
pausa repetía a mano la parte del sonido; ahora los dos usan este control y
ofrecen lo mismo, así que un ajuste nuevo aparece en ambos sin tener que
acordarse de copiarlo.

No dibuja nada: recibe la fila que el jugador está tocando y aplica el
cambio sobre la configuración, el gestor de pantalla y el de audio. La lista
de filas la arma secciones.entradas_ajustes.
"""

from typing import List, Optional

from ...config.audio import VOLUMEN_MAXIMO, VOLUMEN_MINIMO, VOLUMEN_PASO
from . import secciones
from .deslizador import rect_deslizador, volumen_en
from .modelo import EntradaMenu

# Claves de las filas que este control sabe aplicar. Cualquier otra (las
# noches, los niveles de IA, "volver") es de quien lo llama.
CLAVES = (
    "idioma",
    "pantalla_completa",
    "resolucion",
    "brillo",
    "volumen_musica",
    "volumen_efectos",
    "modo_streamer",
)


class ControlAjustes:
    """Aplica los cambios de Ajustes y los guarda en disco."""

    def __init__(self, idiomas, configuracion, audio, pantalla):
        self.idiomas = idiomas
        self.configuracion = configuracion
        self.audio = audio
        self.pantalla = pantalla

    def entradas(self) -> List[EntradaMenu]:
        return secciones.entradas_ajustes(
            self.idiomas, self.configuracion, self.pantalla
        )

    # ------------------------------------------------------------------
    # Flechas, ENTER y clic
    # ------------------------------------------------------------------
    def ajustar(self, entrada: EntradaMenu, delta: int, ciclico: bool = False) -> bool:
        """Aplica un cambio sobre esa fila. Devuelve False si la fila no es
        de Ajustes, para que quien llama siga buscando qué hacer con ella."""
        if entrada.clave == "idioma":
            self.configuracion.idioma = self.idiomas.siguiente_idioma()
        elif entrada.clave == "pantalla_completa":
            self.pantalla.alternar_pantalla_completa()
            self.configuracion.pantalla_completa = self.pantalla.pantalla_completa
        elif entrada.clave == "resolucion":
            self.configuracion.resolucion = self.pantalla.siguiente_resolucion(delta or 1)
        elif entrada.clave == "brillo":
            self.configuracion.brillo = self.pantalla.siguiente_brillo(delta or 1)
        elif entrada.clave == "volumen_musica":
            self.configuracion.volumen_musica = self._nuevo_volumen(
                self.configuracion.volumen_musica, delta, ciclico
            )
            self.audio.establecer_volumen_musica(self.configuracion.volumen_musica)
        elif entrada.clave == "volumen_efectos":
            self.configuracion.volumen_efectos = self._nuevo_volumen(
                self.configuracion.volumen_efectos, delta, ciclico
            )
            self.audio.establecer_volumen_efectos(self.configuracion.volumen_efectos)
        elif entrada.clave == "modo_streamer":
            self.configuracion.modo_streamer = not self.configuracion.modo_streamer
            self.audio.aplicar_modo_streamer(self.configuracion.modo_streamer)
        else:
            return False

        self.configuracion.guardar()
        return True

    @staticmethod
    def _nuevo_volumen(actual: int, delta: int, ciclico: bool) -> int:
        nuevo = actual + delta * VOLUMEN_PASO
        if ciclico and nuevo > VOLUMEN_MAXIMO:
            return VOLUMEN_MINIMO
        return max(VOLUMEN_MINIMO, min(VOLUMEN_MAXIMO, nuevo))

    # ------------------------------------------------------------------
    # Barras deslizantes de volumen
    # ------------------------------------------------------------------
    def deslizador_en(self, posicion, entradas: List[EntradaMenu]) -> Optional[str]:
        """Clave de la barra que hay bajo el cursor, o None."""
        for indice, entrada in enumerate(entradas):
            if entrada.es_deslizable and rect_deslizador(indice).collidepoint(posicion):
                return entrada.clave
        return None

    def valor_deslizador(self, clave: str) -> int:
        if clave == "volumen_musica":
            return self.configuracion.volumen_musica
        if clave == "volumen_efectos":
            return self.configuracion.volumen_efectos
        return 0

    def fijar_deslizador(self, clave: str, entradas: List[EntradaMenu], x_pixel: int):
        """Traduce la posición X del cursor (o del arrastre) dentro de la
        barra a un volumen 0-100. No guarda: escribir a disco en cada
        MOUSEMOTION sería demasiado seguido, así que el guardado ocurre al
        soltar el botón."""
        indices = [indice for indice, e in enumerate(entradas) if e.clave == clave]
        if not indices:
            return
        valor = volumen_en(rect_deslizador(indices[0]), x_pixel)
        if clave == "volumen_musica":
            self.configuracion.volumen_musica = valor
            self.audio.establecer_volumen_musica(valor)
        elif clave == "volumen_efectos":
            self.configuracion.volumen_efectos = valor
            self.audio.establecer_volumen_efectos(valor)

    def guardar(self):
        self.configuracion.guardar()
