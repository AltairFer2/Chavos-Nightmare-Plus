"""Panel de cámaras: monitor a pantalla completa con el mapa de la vecindad
abajo a la derecha haciendo de menú de selección.

Cómo se arma la pantalla, de atrás hacia adelante:

1. "cam N.png": lo que ve la cámara, a pantalla completa.
2. Los animatrónicos que estén en esa habitación.
3. Líneas de barrido y ruido de señal, para que parezca un monitor viejo.
4. Al cambiar de cámara, una ráfaga de estática que tapa el corte.
5. "Marco Cam N.png": el marco del monitor. Ya trae dibujado el rótulo de la
   cámara, el REC y la fecha, así que aquí no se escribe nada de eso.
6. El mapa de la vecindad como menú: cada recuadro con el número de cámara
   es un botón, y el propio arte del mapa viene con la cámara activa
   resaltada ("Cam N Selected.png"). Mientras dura la transición se muestra
   "Cam Unselected.png", el mapa sin nada resaltado.

La Casa del Chavo no tiene imagen porque solo tiene micrófono: ahí se
muestra la estática sola con el aviso de solo audio.
"""

from typing import Dict, Optional, Tuple

import pygame

from constants import (
    ALTO_ANIMATRONIC_CAMARA,
    ALTO_PANTALLA,
    ANCHO_PANTALLA,
    CAMARA_ESTATICA_ALTO,
    CAMARA_ESTATICA_ANCHO,
    CAMARA_ESTATICA_CAMBIO_FRAMES,
    CAMARA_ESTATICA_FRAMES,
    CAMARA_ESTATICA_OPACIDAD,
    CAMARA_LINEAS_OPACIDAD,
    CAMARA_LINEAS_SEPARACION,
    CAMARA_MAPA_ALTO,
    CAMARA_MAPA_ANCHO,
    CAMARA_MAPA_MARGEN_DERECHO,
    CAMARA_MAPA_MARGEN_INFERIOR,
    CAMARA_SABOTAJE_RECUPERACION,
    CAMARA_SABOTAJE_SEGUNDOS,
    CAMARA_TRANSICION_OPACIDAD,
    CAMARA_TRANSICION_SEGUNDOS,
    COLOR_BLANCO,
    COLOR_NEGRO,
    DIR_ASSETS_CAMARAS,
    RESOLUCION_BASE,
)
from efectos import crear_lineas_barrido, generar_frames_estatica
from habitaciones import HABITACIONES, obtener_habitacion
from recursos import CacheImagenes, quitar_fondo_negro

NOMBRE_MAPA_SIN_SELECCION = "Cam Unselected.png"

# Quien arruina las cámaras si se le observa demasiado tiempo seguido.
NOMBRE_SABOTEADOR = "El Chavo"

# Rectángulo del mapa dentro de la pantalla. Queda arriba de la franja del
# HUD para no taparle la batería ni la hora.
RECT_MAPA = pygame.Rect(
    ANCHO_PANTALLA - CAMARA_MAPA_ANCHO - CAMARA_MAPA_MARGEN_DERECHO,
    ALTO_PANTALLA - CAMARA_MAPA_ALTO - CAMARA_MAPA_MARGEN_INFERIOR,
    CAMARA_MAPA_ANCHO,
    CAMARA_MAPA_ALTO,
)

# Posición de cada recuadro del mapa, en fracciones del ancho y alto de la
# imagen. Están medidas sobre el arte, así que siguen valiendo aunque se
# cambie el tamaño con el que se dibuja el mapa en pantalla.
BOTONES_MAPA: Dict[str, Tuple[float, float, float, float]] = {
    "casa_paty": (0.153, 0.037, 0.115, 0.099),
    "segundo_patio": (0.445, 0.010, 0.108, 0.097),
    "casa_godinez": (0.735, 0.033, 0.118, 0.108),
    "casa_popis": (0.139, 0.214, 0.113, 0.105),
    "casa_chavo": (0.737, 0.222, 0.116, 0.099),
    "casa_jaimito": (0.084, 0.456, 0.119, 0.125),
    "casa_florinda": (0.806, 0.457, 0.115, 0.124),
    "casa_clotilde": (0.084, 0.650, 0.119, 0.145),
    "primer_patio": (0.796, 0.614, 0.122, 0.099),
    "casa_ramon": (0.806, 0.733, 0.115, 0.099),
    "entrada": (0.436, 0.907, 0.110, 0.076),
}

COLOR_HOVER = (255, 255, 255, 46)
COLOR_BORDE_HOVER = (210, 235, 255)
# Silueta de respaldo mientras no hay sprite del personaje: translúcida, para
# que se lea como una figura entre la penumbra y no como un bloque pegado.
# Separación horizontal cuando hay varios personajes en la misma habitación.
SEPARACION_FIGURAS = 190
# Los personajes se reparten centrados en la franja que el mapa deja libre,
# para que nunca queden por debajo de él.
CENTRO_FIGURAS_X = RECT_MAPA.left // 2
# Altura a la que quedan sus pies dentro de la imagen de la cámara.
SUELO_FIGURAS_Y = int(ALTO_PANTALLA * 0.82)


class SistemaCamaras:
    """Qué cámara está activa, cómo se dibuja el monitor y qué botón del mapa
    cae bajo el ratón."""

    def __init__(self, camara_inicial: str = "primer_patio"):
        self.camara_actual = camara_inicial
        self.activo = False

        self._vistas = CacheImagenes(tamano=RESOLUCION_BASE)
        self._marcos = CacheImagenes(con_alfa=True, tamano=RESOLUCION_BASE)
        # El mapa viene dibujado sobre fondo negro: se le quita el fondo para
        # que flote sobre la imagen de la cámara en vez de taparla con un
        # recuadro negro.
        self._mapas = CacheImagenes(
            tamano=RECT_MAPA.size, transformacion=quitar_fondo_negro
        )
        self._figuras = CacheImagenes(con_alfa=True, alto=ALTO_ANIMATRONIC_CAMARA)
        self._mapa_sin_seleccion = self._mapas.obtener(
            NOMBRE_MAPA_SIN_SELECCION, DIR_ASSETS_CAMARAS / NOMBRE_MAPA_SIN_SELECCION
        )

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
        self._botones = self._calcular_botones()

        # El Chavo arruina las cámaras si se le mira demasiado rato seguido.
        # La presión sube mientras se le tiene en pantalla y baja sola en
        # cuanto se cambia de vista.
        self.averiadas = False
        self.presion_sabotaje = 0.0

    @staticmethod
    def _calcular_botones() -> Dict[str, pygame.Rect]:
        """Pasa los recuadros del mapa de fracciones a píxeles de pantalla."""
        return {
            id_habitacion: pygame.Rect(
                RECT_MAPA.x + int(x * RECT_MAPA.width),
                RECT_MAPA.y + int(y * RECT_MAPA.height),
                int(ancho * RECT_MAPA.width),
                int(alto * RECT_MAPA.height),
            )
            for id_habitacion, (x, y, ancho, alto) in BOTONES_MAPA.items()
        }

    # ------------------------------------------------------------------
    # Estado
    # ------------------------------------------------------------------
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
        if posicion is None:
            return None
        for id_habitacion, rect in self._botones.items():
            if rect.collidepoint(posicion):
                return id_habitacion
        return None

    def reparar(self):
        self.averiadas = False
        self.presion_sabotaje = 0.0

    def actualizar(self, dt: float, animatronics=()):
        self._contador_estatica += 1
        if self._contador_estatica >= CAMARA_ESTATICA_CAMBIO_FRAMES:
            self._contador_estatica = 0
            self._indice_estatica = (self._indice_estatica + 1) % len(self._frames_estatica)
        if self._transicion_restante > 0.0:
            self._transicion_restante = max(0.0, self._transicion_restante - dt)
        self._actualizar_sabotaje(dt, animatronics)

    def _actualizar_sabotaje(self, dt: float, animatronics):
        if self.averiadas:
            return
        if self.activo and self._chavo_a_la_vista(animatronics):
            self.presion_sabotaje += dt
            if self.presion_sabotaje >= CAMARA_SABOTAJE_SEGUNDOS:
                self.averiadas = True
                self.presion_sabotaje = CAMARA_SABOTAJE_SEGUNDOS
        else:
            self.presion_sabotaje = max(
                0.0, self.presion_sabotaje - dt * CAMARA_SABOTAJE_RECUPERACION
            )

    def _chavo_a_la_vista(self, animatronics) -> bool:
        return any(
            animatronic.nombre == NOMBRE_SABOTEADOR
            and animatronic.activo
            and animatronic.habitacion_actual == self.camara_actual
            for animatronic in animatronics
        )

    # ------------------------------------------------------------------
    # Dibujado
    # ------------------------------------------------------------------
    def dibujar(self, superficie: pygame.Surface, animatronics=(), fuente=None,
                idiomas=None, posicion_raton=None):
        habitacion = obtener_habitacion(self.camara_actual)

        self._dibujar_vista(superficie, habitacion, fuente, idiomas)
        if not habitacion.solo_audio and not self.averiadas:
            self._dibujar_animatronics(superficie, habitacion, animatronics)

        superficie.blit(self._lineas, (0, 0))
        superficie.blit(self._frames_estatica[self._indice_estatica], (0, 0))
        if self._transicion_restante > 0.0:
            superficie.blit(self._estatica_transicion[self._indice_estatica], (0, 0))

        marco = self._marcos.obtener(habitacion.id, habitacion.ruta_marco)
        if marco is not None:
            superficie.blit(marco, (0, 0))

        self._dibujar_mapa(superficie, habitacion, posicion_raton)

    def _dibujar_vista(self, superficie, habitacion, fuente, idiomas):
        superficie.fill(COLOR_NEGRO)
        if self.averiadas:
            # Sin señal en ninguna cámara hasta restablecerlas desde el barril.
            superficie.blit(self._estatica_transicion[self._indice_estatica], (0, 0))
            if fuente and idiomas:
                texto = fuente.render(idiomas.t("camara_averiada"), True, COLOR_BLANCO)
                superficie.blit(
                    texto, texto.get_rect(center=(ANCHO_PANTALLA // 2, ALTO_PANTALLA // 2))
                )
            return

        if habitacion.solo_audio:
            if fuente and idiomas:
                texto = fuente.render(idiomas.t("camara_solo_audio"), True, COLOR_BLANCO)
                superficie.blit(
                    texto, texto.get_rect(center=(ANCHO_PANTALLA // 2, ALTO_PANTALLA // 2))
                )
            return

        vista = self._vistas.obtener(habitacion.id, habitacion.ruta_vista)
        if vista is not None:
            superficie.blit(vista, (0, 0))
        elif fuente and idiomas:
            texto = fuente.render(idiomas.t("camara_sin_imagen"), True, COLOR_BLANCO)
            superficie.blit(
                texto, texto.get_rect(center=(ANCHO_PANTALLA // 2, ALTO_PANTALLA // 2))
            )

    def _dibujar_animatronics(self, superficie, habitacion, animatronics):
        presentes = [
            animatronic for animatronic in animatronics
            if animatronic.habitacion_actual == habitacion.id
        ]
        desplazamiento = -(len(presentes) - 1) * SEPARACION_FIGURAS // 2

        for indice, animatronic in enumerate(presentes):
            x = CENTRO_FIGURAS_X + desplazamiento + indice * SEPARACION_FIGURAS
            figura = self._figuras.obtener(
                animatronic.clave_sprite(), animatronic.ruta_sprite()
            )
            if figura is not None:
                superficie.blit(
                    figura, figura.get_rect(midbottom=(x, SUELO_FIGURAS_Y))
                )

    def _dibujar_mapa(self, superficie, habitacion, posicion_raton):
        # Durante la transición se enseña el mapa sin nada resaltado, como si
        # el monitor todavía no hubiera enganchado la señal nueva.
        mapa = None
        if self._transicion_restante <= 0.0:
            mapa = self._mapas.obtener(habitacion.id, habitacion.ruta_mapa)
        if mapa is None:
            mapa = self._mapa_sin_seleccion
        if mapa is None:
            return

        # Dos pasadas: al venir el trazo suavizado, buena parte del mapa
        # queda a medio alfa y sobre la imagen de la cámara se leería muy
        # flojo. Superponerlo consigo mismo lo refuerza sin devolverle el
        # fondo negro.
        superficie.blit(mapa, RECT_MAPA)
        superficie.blit(mapa, RECT_MAPA)

        id_hover = self.boton_en(posicion_raton)
        if id_hover is None or id_hover == self.camara_actual:
            return
        rect = self._botones[id_hover]
        resaltado = pygame.Surface(rect.size, pygame.SRCALPHA)
        resaltado.fill(COLOR_HOVER)
        superficie.blit(resaltado, rect)
        pygame.draw.rect(superficie, COLOR_BORDE_HOVER, rect, width=2)
