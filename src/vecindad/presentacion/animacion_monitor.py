"""El monitor de vigilancia entrando y saliendo de la vista del jugador.

Los cuadros ("pos 1.png", "pos 2.png"... en assets/camaras/) son el aparato
descolgándose del techo hasta quedar delante de la cara, con la pantalla
todavía apagada. Se reproducen en orden al levantar el panel.

Al bajarlo no se repiten al revés: se enseña uno solo, el del monitor ya
despegado de la cara, y se quita. Levantarlo es un gesto que el jugador
decide y puede disfrutar; bajarlo suele ser una urgencia, y ahí lo que hace
falta es ver el patio cuanto antes.

Los cuadros vienen dibujados sobre negro, y ese negro se recorta al cargarlos
(ver quitar_fondo_alrededor): alrededor del aparato la lámina es transparente
y deja ver el patio de detrás, mientras que la pantalla del propio monitor
sigue siendo negra hasta que la animación termina. Por eso el juego pinta
primero lo que hay detrás y luego suelta el cuadro encima.

Si los cuadros no están en disco no hay animación y el panel se abre de golpe:
como con el resto del arte, una imagen que falta no impide jugar.
"""

from typing import Optional, Tuple

import pygame

from ..config.interfaz import CAMARA_ENCENDIDO_SEGUNDOS, CAMARA_SALIDA_SEGUNDOS
from ..config.rutas import DIR_ASSETS_CAMARAS, PATRON_CAMARAS_ENCENDIDO
from ..config.ventana import RESOLUCION_BASE
from ..infraestructura.recursos import CacheImagenes, quitar_fondo_alrededor


def cargar_cuadros() -> Tuple[pygame.Surface, ...]:
    """Lee "pos 1.png", "pos 2.png"... hasta el primero que no exista.

    Se cargan todos de una vez al montar el panel y no la primera vez que se
    abre: son imágenes de pantalla completa y hay que recortarles el fondo,
    así que hacerlo a mitad de la noche daría un tirón en el peor momento.
    """
    cache = CacheImagenes(
        con_alfa=True, tamano=RESOLUCION_BASE, transformacion=quitar_fondo_alrededor
    )
    cuadros = []
    numero = 1
    while True:
        nombre = PATRON_CAMARAS_ENCENDIDO.format(numero=numero)
        imagen = cache.obtener(nombre, DIR_ASSETS_CAMARAS / nombre)
        if imagen is None:
            return tuple(cuadros)
        cuadros.append(imagen)
        numero += 1


class AnimacionMonitor:
    """La ráfaga de cuadros del monitor acercándose o retirándose."""

    def __init__(self):
        self._cuadros = cargar_cuadros()
        self._transcurrido = 0.0
        self._duracion = CAMARA_ENCENDIDO_SEGUNDOS
        self._saliendo = False
        self.en_marcha = False

    @property
    def hay_animacion(self) -> bool:
        return bool(self._cuadros)

    def entrar(self) -> bool:
        """El monitor baja hasta delante de la cara del jugador. Devuelve si
        de verdad hay algo que reproducir."""
        return self._arrancar(CAMARA_ENCENDIDO_SEGUNDOS, saliendo=False)

    def salir(self) -> bool:
        """Y se retira: un solo cuadro y fuera."""
        return self._arrancar(CAMARA_SALIDA_SEGUNDOS, saliendo=True)

    def _arrancar(self, duracion: float, saliendo: bool) -> bool:
        if not self.hay_animacion:
            return False
        self._transcurrido = 0.0
        self._duracion = duracion
        self._saliendo = saliendo
        self.en_marcha = True
        return True

    def cancelar(self):
        """Quita el monitor de en medio sin animación. Es lo que hace empezar
        una noche: ahí no hay gesto que enseñar, solo un estado que dejar
        limpio."""
        self.en_marcha = False

    def actualizar(self, dt: float):
        if not self.en_marcha:
            return
        self._transcurrido += dt
        if self._transcurrido >= self._duracion:
            self.en_marcha = False

    def cuadro_actual(self) -> Optional[pygame.Surface]:
        """El cuadro que toca según lo que lleve corrido. None si no hay
        animación en marcha.

        Retirándose siempre es el mismo: el de en medio de la secuencia, que
        es el aparato ya separado de la cara pero todavía a la vista. No se
        recorre la ráfaga entera, así que es un parpadeo y no un trayecto.
        """
        if not self.en_marcha or not self._cuadros:
            return None
        if self._saliendo:
            return self._cuadros[len(self._cuadros) // 2]
        avance = self._transcurrido / self._duracion
        return self._cuadros[min(int(avance * len(self._cuadros)), len(self._cuadros) - 1)]

    def dibujar(self, superficie: pygame.Surface) -> bool:
        """Suelta el cuadro actual sobre lo que ya hubiera dibujado. Devuelve
        si había algo que soltar."""
        cuadro = self.cuadro_actual()
        if cuadro is None:
            return False
        superficie.blit(cuadro, (0, 0))
        return True
