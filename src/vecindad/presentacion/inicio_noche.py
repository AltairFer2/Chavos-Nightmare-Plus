"""Lo que se ve antes de empezar a jugar, en dos pasos.

1. PeriodicoInicial: el recorte de "Se busca" con el anuncio del puesto de
   velador. Solo aparece al empezar una partida nueva, porque es lo que
   explica qué hace el jugador ahí; en las noches siguientes ya lo sabe.
2. TarjetaNoche: "Noche N" y las 12:00 am, como en el género. Esa sale antes
   de cada noche.

Las dos son pantallas muertas: fondo negro, sin nada que tocar y con su
propio reloj, igual que el RelojVictoria del final. Sirven de transición
entre el menú y el patio, para que la noche no empiece de golpe.

Si el arte del periódico todavía no está, esa pantalla se salta sola en vez
de dejar veinte segundos de negro: una imagen que falta no debe convertirse
en una espera sin explicación.
"""

import pygame

from ..config.interfaz import (
    COLOR_AMARILLO_AVISO,
    COLOR_BLANCO,
    COLOR_NEGRO,
    FUENTE_TAMANO_MENU,
    FUENTE_TAMANO_RELOJ,
)
from ..config.partida import PERIODICO_SEGUNDOS, TARJETA_NOCHE_SEGUNDOS
from ..config.rutas import DIR_ASSETS_UI
from ..config.ventana import ALTO_PANTALLA, ANCHO_PANTALLA, RESOLUCION_BASE
from ..infraestructura.fuentes import crear_fuente
from ..infraestructura.recursos import CacheImagenes

ARCHIVO_PERIODICO = "nuevo juego.png"

# La hora que marca la tarjeta. Siempre es la misma: toda noche empieza a las
# 12, y el reloj de verdad no arranca hasta que el jugador está en el patio.
HORA_DE_ARRANQUE = "12:00 AM"

# Separación entre la hora y el nombre de la noche, medida desde el centro.
SEPARACION_TARJETA = 90


class PeriodicoInicial:
    """El anuncio del periódico con el que arranca una partida nueva."""

    def __init__(self):
        # Se estira al lienzo entero, como el resto de los fondos del juego
        # (el patio, el game over): la pantalla de arranque ocupa todo y no
        # deja franjas negras a los lados. Ojo: el recorte es vertical, así
        # que si el archivo no viene ya en 16:9 se nota la deformación.
        self._recortes = CacheImagenes(tamano=RESOLUCION_BASE)
        self._restante = 0.0
        self.termino = True

    @property
    def imagen(self):
        return self._recortes.obtener(ARCHIVO_PERIODICO, DIR_ASSETS_UI / ARCHIVO_PERIODICO)

    def hay_recorte(self) -> bool:
        """Si el arte existe. Sin él no tiene sentido mostrar la pantalla."""
        return self.imagen is not None

    def iniciar(self) -> bool:
        """Arranca la cuenta atrás. Devuelve si de verdad hay algo que
        enseñar; si no, quien llame debe seguir de largo."""
        if not self.hay_recorte():
            self.termino = True
            return False
        self._restante = PERIODICO_SEGUNDOS
        self.termino = False
        return True

    def actualizar(self, dt: float):
        if self.termino:
            return
        self._restante -= dt
        if self._restante <= 0.0:
            self.termino = True

    def dibujar(self, superficie: pygame.Surface):
        recorte = self.imagen
        if recorte is None:
            superficie.fill(COLOR_NEGRO)
            return
        superficie.blit(recorte, (0, 0))


class TarjetaNoche:
    """La tarjeta de "Noche N - 12:00 AM" que abre cada noche."""

    def __init__(self, idiomas):
        self.idiomas = idiomas
        self._restante = 0.0
        self.termino = True
        self.numero_noche = 1
        self.personalizada = False

    def iniciar(self, numero_noche: int, personalizada: bool = False):
        self.numero_noche = numero_noche
        self.personalizada = personalizada
        self._restante = TARJETA_NOCHE_SEGUNDOS
        self.termino = False

    def actualizar(self, dt: float):
        if self.termino:
            return
        self._restante -= dt
        if self._restante <= 0.0:
            self.termino = True

    def texto_noche(self) -> str:
        """La noche personalizada no lleva número: el suyo está fuera de la
        campaña y "Noche 7" no le diría nada al jugador."""
        if self.personalizada:
            return self.idiomas.t("menu_noche_personalizada")
        return self.idiomas.t("hud_noche", noche=self.numero_noche)

    def dibujar(self, superficie: pygame.Surface):
        superficie.fill(COLOR_NEGRO)

        fuente_hora = crear_fuente(FUENTE_TAMANO_RELOJ, negrita=True)
        hora = fuente_hora.render(HORA_DE_ARRANQUE, True, COLOR_BLANCO)
        superficie.blit(
            hora,
            hora.get_rect(
                center=(ANCHO_PANTALLA // 2, ALTO_PANTALLA // 2 - SEPARACION_TARJETA // 2)
            ),
        )

        fuente_noche = crear_fuente(FUENTE_TAMANO_MENU, negrita=True)
        noche = fuente_noche.render(self.texto_noche(), True, COLOR_AMARILLO_AVISO)
        superficie.blit(
            noche,
            noche.get_rect(
                center=(ANCHO_PANTALLA // 2, ALTO_PANTALLA // 2 + SEPARACION_TARJETA)
            ),
        )
