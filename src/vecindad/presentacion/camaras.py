"""Panel de cámaras: el monitor a pantalla completa.

Cómo se arma la pantalla, de atrás hacia adelante:

1. La imagen de la habitación: si hay alguien dentro, la escena ya dibujada
   con esa gente (ver escenas_camara.py); si no, "cam N.png", que es la
   habitación vacía.
2. Líneas de barrido y ruido de señal, para que parezca un monitor viejo.
3. Al cambiar de cámara, una ráfaga de estática que tapa el corte.
4. "Marco Cam N.png": el marco del monitor. Ya trae dibujado el rótulo de la
   cámara, el REC y la fecha, así que aquí no se escribe nada de eso.
5. El mapa de la vecindad como menú de selección (ver mapa_camaras.py).

Los personajes ya no se pegan como figuras sueltas encima del fondo: cada
combinación tiene su propia imagen dibujada aparte, y aquí solo se elige cuál
toca.

La Casa del Chavo no tiene imagen porque solo tiene micrófono: ahí se
muestra la estática sola con el aviso de solo audio.

Cuándo se rompen las cámaras es una regla de juego y vive en
dominio/sabotaje.py; este módulo solo le informa de si el saboteador está en
la vista que se está mirando.
"""

from typing import Optional

import pygame

from ..config.interfaz import (
    CAMARA_ESTATICA_ALTO,
    CAMARA_ESTATICA_ANCHO,
    CAMARA_ESTATICA_CAMBIO_FRAMES,
    CAMARA_ESTATICA_FRAMES,
    CAMARA_ESTATICA_OPACIDAD,
    CAMARA_LINEAS_OPACIDAD,
    CAMARA_LINEAS_SEPARACION,
    CAMARA_TRANSICION_OPACIDAD,
    CAMARA_TRANSICION_SEGUNDOS,
    COLOR_BLANCO,
    COLOR_NEGRO,
)
from ..config.ventana import ALTO_PANTALLA, ANCHO_PANTALLA, RESOLUCION_BASE
from ..dominio.animatronicos import nombres
from ..dominio.sabotaje import ControlSabotaje
from ..infraestructura.recursos import CacheImagenes
from ..mundo.habitaciones import HABITACIONES, obtener_habitacion
from .boton_audio import BotonAudio
from .efectos import crear_lineas_barrido, generar_frames_estatica
from .escenas_camara import EscenasCamara
from .mapa_camaras import MapaVecindad


class SistemaCamaras:
    """Qué cámara está activa y cómo se dibuja el monitor."""

    def __init__(self, camara_inicial: str = "primer_patio"):
        self.camara_actual = camara_inicial
        self.activo = False

        self._vistas = CacheImagenes(tamano=RESOLUCION_BASE)
        self._marcos = CacheImagenes(con_alfa=True, tamano=RESOLUCION_BASE)
        self._escenas = EscenasCamara()
        self._mapa = MapaVecindad()
        self._boton_audio = BotonAudio()

        self._frames_estatica = generar_frames_estatica(
            CAMARA_ESTATICA_FRAMES,
            (CAMARA_ESTATICA_ANCHO, CAMARA_ESTATICA_ALTO),
            RESOLUCION_BASE,
            CAMARA_ESTATICA_OPACIDAD,
        )
        self._estatica_transicion = generar_frames_estatica(
            CAMARA_ESTATICA_FRAMES,
            (CAMARA_ESTATICA_ANCHO, CAMARA_ESTATICA_ALTO),
            RESOLUCION_BASE,
            CAMARA_TRANSICION_OPACIDAD,
        )
        self._lineas = crear_lineas_barrido(
            RESOLUCION_BASE, CAMARA_LINEAS_SEPARACION, CAMARA_LINEAS_OPACIDAD
        )

        self._indice_estatica = 0
        self._contador_estatica = 0
        self._transicion_restante = 0.0
        self._sabotaje = ControlSabotaje()

    # ------------------------------------------------------------------
    # Estado
    # ------------------------------------------------------------------
    @property
    def averiadas(self) -> bool:
        return self._sabotaje.averiadas

    def alternar_panel(self):
        self.activo = not self.activo

    def cambiar_camara(self, id_habitacion: str) -> bool:
        """Salta a otra cámara. Devuelve False si es la que ya se está viendo
        o si el id no existe, para no relanzar la transición por gusto."""
        if id_habitacion not in HABITACIONES or id_habitacion == self.camara_actual:
            return False
        self.camara_actual = id_habitacion
        self._transicion_restante = CAMARA_TRANSICION_SEGUNDOS
        return True

    def boton_en(self, posicion) -> Optional[str]:
        """Habitación cuyo recuadro del mapa contiene ese punto, o None."""
        return self._mapa.boton_en(posicion)

    def audio_en(self, posicion) -> bool:
        """Si ese punto cae en el botón de audio del monitor."""
        return self._boton_audio.contiene(posicion)

    def reparar(self):
        self._sabotaje.reparar()

    def actualizar(self, dt: float, animatronics=()):
        self._contador_estatica += 1
        if self._contador_estatica >= CAMARA_ESTATICA_CAMBIO_FRAMES:
            self._contador_estatica = 0
            self._indice_estatica = (self._indice_estatica + 1) % len(self._frames_estatica)
        if self._transicion_restante > 0.0:
            self._transicion_restante = max(0.0, self._transicion_restante - dt)
        self._sabotaje.actualizar(
            dt, self.activo and self._saboteador_a_la_vista(animatronics)
        )

    def _saboteador_a_la_vista(self, animatronics) -> bool:
        return any(
            animatronic.nombre == nombres.SABOTEADOR
            and animatronic.activo
            and animatronic.habitacion_actual == self.camara_actual
            for animatronic in animatronics
        )

    # ------------------------------------------------------------------
    # Dibujado
    # ------------------------------------------------------------------
    def dibujar(self, superficie: pygame.Surface, animatronics=(), fuente=None,
                idiomas=None, posicion_raton=None, estado_servicios=None):
        habitacion = obtener_habitacion(self.camara_actual)

        self._dibujar_vista(superficie, habitacion, animatronics, fuente, idiomas)

        superficie.blit(self._lineas, (0, 0))
        superficie.blit(self._frames_estatica[self._indice_estatica], (0, 0))
        if self._transicion_restante > 0.0:
            superficie.blit(self._estatica_transicion[self._indice_estatica], (0, 0))

        marco = self._marcos.obtener(habitacion.id, habitacion.ruta_marco)
        if marco is not None:
            superficie.blit(marco, (0, 0))

        self._mapa.dibujar(
            superficie, habitacion, self.camara_actual, posicion_raton,
            en_transicion=self._transicion_restante > 0.0,
        )
        if estado_servicios is not None:
            self._boton_audio.dibujar(
                superficie, estado_servicios, fuente, idiomas, posicion_raton
            )

    def _dibujar_vista(self, superficie, habitacion, animatronics, fuente, idiomas):
        superficie.fill(COLOR_NEGRO)
        if self.averiadas:
            # Sin señal en ninguna cámara hasta restablecerlas desde el barril.
            superficie.blit(self._estatica_transicion[self._indice_estatica], (0, 0))
            self._escribir_al_centro(superficie, fuente, idiomas, "camara_averiada")
            return

        if habitacion.solo_audio:
            self._escribir_al_centro(superficie, fuente, idiomas, "camara_solo_audio")
            return

        imagen = self._escena_o_vacia(habitacion, animatronics)
        if imagen is not None:
            superficie.blit(imagen, (0, 0))
        else:
            self._escribir_al_centro(superficie, fuente, idiomas, "camara_sin_imagen")

    def _escena_o_vacia(self, habitacion, animatronics):
        """La escena con quien esté dentro; si no hay ninguna dibujada para
        ese grupo, la habitación vacía."""
        presentes = [
            animatronic.nombre for animatronic in animatronics
            if animatronic.activo and animatronic.habitacion_actual == habitacion.id
        ]
        escena = self._escenas.imagen_para(habitacion, presentes) if presentes else None
        if escena is not None:
            return escena
        return self._vistas.obtener(habitacion.id, habitacion.ruta_vista)

    @staticmethod
    def _escribir_al_centro(superficie, fuente, idiomas, clave: str):
        """Los avisos del monitor (sin señal, solo audio, averiadas) van todos
        centrados en pantalla. Sin fuente o sin idiomas no se dibuja nada."""
        if not fuente or not idiomas:
            return
        texto = fuente.render(idiomas.t(clave), True, COLOR_BLANCO)
        superficie.blit(
            texto, texto.get_rect(center=(ANCHO_PANTALLA // 2, ALTO_PANTALLA // 2))
        )
