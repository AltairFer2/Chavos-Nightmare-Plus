"""Gestión de la ventana, la resolución y el modo pantalla completa.

El juego dibuja siempre sobre un lienzo de tamaño fijo (RESOLUCION_BASE) y
este módulo lo escala a la ventana real (ventana normal o pantalla
completa), centrándolo y dejando franjas negras si la proporción no
coincide. De esta forma cambiar de resolución o de modo no obliga a
recalcular ninguna posición de la interfaz.

En pantalla completa se usa siempre la resolución nativa del monitor
(pygame.display.set_mode((0, 0), FULLSCREEN)) en vez de forzar un cambio de
modo de video a una resolución exacta, que es más propenso a fallar según
el monitor o los drivers. El selector de "Resolución" del menú controla
únicamente el tamaño de la ventana cuando el modo pantalla completa está
desactivado.

También traduce las coordenadas del ratón de la ventana al lienzo, para que
los clics sigan cayendo donde corresponde sea cual sea el modo o el tamaño, y
aplica el brillo elegido al volcar la imagen: es lo último que pasa antes de
enseñar el fotograma, así que corrige la escena entera de una sola vez.
"""

import pygame

from ..config.interfaz import COLOR_NEGRO
from ..config.ventana import (
    ALTO_PANTALLA,
    ANCHO_PANTALLA,
    BRILLO_MAXIMO,
    BRILLO_MINIMO,
    BRILLO_NEUTRO,
    BRILLO_PASO,
    BRILLO_POR_DEFECTO,
    RESOLUCION_BASE,
    RESOLUCIONES_DISPONIBLES,
    TITULO_JUEGO,
)

# Cuánto se aclara como máximo al subir el brillo al tope. Aclarar sumando
# luz a cada píxel se nota mucho más que oscurecer multiplicando, así que el
# tramo de arriba se aplica a media fuerza: con 255 la escena se lavaría
# entera y el juego dejaría de dar miedo.
SUMA_MAXIMA_BRILLO = 110


class GestorPantalla:
    """Ventana, lienzo de dibujo y conversión de coordenadas."""

    def __init__(
        self,
        resolucion=None,
        pantalla_completa: bool = False,
        brillo: int = BRILLO_POR_DEFECTO,
    ):
        self.lienzo = pygame.Surface(RESOLUCION_BASE)
        self.resolucion = self._validar(resolucion)
        self.pantalla_completa = bool(pantalla_completa)
        self.brillo = self._validar_brillo(brillo)
        self.ventana = None
        self._area_destino = pygame.Rect(0, 0, *RESOLUCION_BASE)
        # Capa con la que se corrige el brillo, y con qué mezcla se aplica.
        # Se guarda hecha para no crear una superficie por fotograma.
        self._capa_brillo = None
        self._mezcla_brillo = 0
        self._aplicar_modo_video()
        pygame.display.set_caption(TITULO_JUEGO)

    @staticmethod
    def _validar(resolucion):
        if resolucion is None:
            return RESOLUCION_BASE
        candidata = tuple(resolucion)
        return candidata if candidata in RESOLUCIONES_DISPONIBLES else RESOLUCION_BASE

    @staticmethod
    def _validar_brillo(brillo: int) -> int:
        return max(BRILLO_MINIMO, min(BRILLO_MAXIMO, int(brillo)))

    def _aplicar_modo_video(self):
        if self.pantalla_completa:
            # (0, 0) le pide a SDL que use la resolución nativa del monitor
            # en vez de forzar un modo de video específico.
            self.ventana = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.ventana = pygame.display.set_mode(self.resolucion)
        self._recalcular_area()

    def _recalcular_area(self):
        """Calcula el rectángulo donde cabe el lienzo dentro de la ventana
        real, conservando su proporción."""
        ancho_ventana, alto_ventana = self.ventana.get_size()
        escala = min(ancho_ventana / ANCHO_PANTALLA, alto_ventana / ALTO_PANTALLA)
        ancho = int(ANCHO_PANTALLA * escala)
        alto = int(ALTO_PANTALLA * escala)
        self._area_destino = pygame.Rect(
            (ancho_ventana - ancho) // 2, (alto_ventana - alto) // 2, ancho, alto
        )
        self._preparar_capa_brillo()

    def aplicar_resolucion(self, resolucion) -> bool:
        """Cambia la resolución de la ventana (modo no pantalla completa).
        Si el modo pantalla completa está activo, solo queda guardada como
        preferencia para cuando el jugador vuelva a modo ventana."""
        nueva = self._validar(resolucion)
        if nueva == self.resolucion:
            return False
        self.resolucion = nueva
        if not self.pantalla_completa:
            self._aplicar_modo_video()
        return True

    def siguiente_resolucion(self, delta: int = 1):
        indice = RESOLUCIONES_DISPONIBLES.index(self.resolucion)
        nueva = RESOLUCIONES_DISPONIBLES[(indice + delta) % len(RESOLUCIONES_DISPONIBLES)]
        self.aplicar_resolucion(nueva)
        return nueva

    def aplicar_pantalla_completa(self, activo: bool) -> bool:
        """Activa o desactiva el modo pantalla completa. Devuelve si hubo
        cambio real de modo de video."""
        activo = bool(activo)
        if activo == self.pantalla_completa:
            return False
        self.pantalla_completa = activo
        self._aplicar_modo_video()
        return True

    def alternar_pantalla_completa(self) -> bool:
        self.aplicar_pantalla_completa(not self.pantalla_completa)
        return self.pantalla_completa

    def aplicar_brillo(self, brillo: int) -> int:
        """Cambia el brillo de la imagen final. Devuelve el valor aplicado,
        ya recortado a su rango."""
        self.brillo = self._validar_brillo(brillo)
        self._preparar_capa_brillo()
        return self.brillo

    def siguiente_brillo(self, delta: int = 1, paso: int = BRILLO_PASO) -> int:
        """Sube o baja un escalón, sin dar la vuelta: pasarse de largo con la
        flecha no debe saltar de la pantalla más oscura a la más clara."""
        return self.aplicar_brillo(self.brillo + delta * paso)

    def _preparar_capa_brillo(self):
        """Deja lista la capa con la que se corrige el brillo, del tamaño
        exacto de la imagen ya escalada. Con el brillo neutro no hay capa y
        `presentar` no hace trabajo de más."""
        if self.brillo == BRILLO_NEUTRO or self._area_destino.size == (0, 0):
            self._capa_brillo = None
            return
        capa = pygame.Surface(self._area_destino.size)
        if self.brillo < BRILLO_NEUTRO:
            # Multiplicar por un gris apaga la imagen conservando el color.
            tono = round(255 * self.brillo / BRILLO_NEUTRO)
            self._mezcla_brillo = pygame.BLEND_RGB_MULT
        else:
            tramo = (self.brillo - BRILLO_NEUTRO) / (BRILLO_MAXIMO - BRILLO_NEUTRO)
            tono = round(SUMA_MAXIMA_BRILLO * tramo)
            self._mezcla_brillo = pygame.BLEND_RGB_ADD
        capa.fill((tono, tono, tono))
        self._capa_brillo = capa

    def presentar(self):
        """Vuelca el lienzo escalado a la ventana y actualiza la imagen."""
        if self._area_destino.size == RESOLUCION_BASE and self.ventana.get_size() == RESOLUCION_BASE:
            self.ventana.blit(self.lienzo, self._area_destino.topleft)
        else:
            self.ventana.fill(COLOR_NEGRO)
            escalado = pygame.transform.smoothscale(self.lienzo, self._area_destino.size)
            self.ventana.blit(escalado, self._area_destino.topleft)
        if self._capa_brillo is not None:
            # Solo sobre la imagen: las franjas negras de los lados se quedan
            # negras aunque se suba el brillo.
            self.ventana.blit(
                self._capa_brillo, self._area_destino.topleft,
                special_flags=self._mezcla_brillo,
            )
        pygame.display.flip()

    def posicion_en_lienzo(self, posicion):
        """Convierte una coordenada de la ventana a coordenada del lienzo."""
        x, y = posicion
        area = self._area_destino
        if area.width == 0 or area.height == 0:
            return (0, 0)
        return (
            int((x - area.x) * ANCHO_PANTALLA / area.width),
            int((y - area.y) * ALTO_PANTALLA / area.height),
        )
