"""Sistema de cámaras: selección de vista, cambio entre habitaciones y
dibujado del panel de vigilancia (imagen de la cámara, animatrónicos
visibles, indicador de solo-audio y parpadeo estilo CCTV).

Convención de assets:
- Cada carpeta assets/camaras/<Cámara N - Nombre>/ contiene un archivo
  "Cam N Selected.png" con la vista de esa cámara.
- assets/camaras/Cam Unselected.png es una imagen compartida por todas las
  cámaras: la vista alterna cada INTERVALO_PARPADEO_FRAMES fotogramas entre
  esta imagen y la de la cámara seleccionada, simulando el parpadeo de un
  monitor de vigilancia viejo.
"""

import pygame

from constants import COLOR_BLANCO, COLOR_GRIS, COLOR_NEGRO, COLOR_VERDE_ENERGIA, DIR_ASSETS_CAMARAS, INTERVALO_PARPADEO_FRAMES
from habitaciones import HABITACIONES, obtener_habitacion

NOMBRE_IMAGEN_NO_SELECCIONADA = "Cam Unselected.png"

# Orden de despliegue en el panel de selección (agrupado por patio, igual
# que la distribución física de la vecindad).
ORDEN_PANEL = [
    "casa_jaimito", "casa_clotilde", "primer_patio", "entrada",
    "casa_florinda", "casa_ramon", "casa_paty", "casa_popis",
    "segundo_patio", "casa_godinez", "casa_chavo",
]


class SistemaCamaras:
    """Controla qué cámara está activa y la dibuja en pantalla."""

    def __init__(self, camara_inicial: str = "primer_patio"):
        self.camara_actual = camara_inicial
        self.activo = False
        self._imagenes_cache = {}
        self._imagen_no_seleccionada = self._cargar_imagen(
            DIR_ASSETS_CAMARAS / NOMBRE_IMAGEN_NO_SELECCIONADA
        )
        self._contador_parpadeo = 0
        self._mostrar_seleccionada = True

    def alternar_panel(self):
        self.activo = not self.activo

    def cambiar_camara(self, id_habitacion: str):
        if id_habitacion not in HABITACIONES:
            return
        self.camara_actual = id_habitacion

    def actualizar(self):
        """Avanza el contador de parpadeo un fotograma (efecto CCTV)."""
        self._contador_parpadeo += 1
        if self._contador_parpadeo >= INTERVALO_PARPADEO_FRAMES:
            self._contador_parpadeo = 0
            self._mostrar_seleccionada = not self._mostrar_seleccionada

    @staticmethod
    def _cargar_imagen(ruta):
        if not ruta.exists():
            return None
        try:
            return pygame.image.load(str(ruta)).convert()
        except pygame.error:
            return None

    def _imagen_seleccionada(self, habitacion):
        if habitacion.id in self._imagenes_cache:
            return self._imagenes_cache[habitacion.id]
        imagen = self._cargar_imagen(habitacion.carpeta_assets / habitacion.archivo_seleccionada)
        self._imagenes_cache[habitacion.id] = imagen
        return imagen

    def dibujar(self, superficie: pygame.Surface, rect: pygame.Rect,
                animatronics_presentes=None, fuente=None, idiomas=None):
        habitacion = obtener_habitacion(self.camara_actual)
        superficie.fill(COLOR_NEGRO, rect)

        imagen = (
            self._imagen_seleccionada(habitacion)
            if self._mostrar_seleccionada
            else self._imagen_no_seleccionada
        )
        if imagen is not None:
            imagen_escalada = pygame.transform.smoothscale(imagen, rect.size)
            superficie.blit(imagen_escalada, rect)
        else:
            pygame.draw.rect(superficie, COLOR_GRIS, rect, width=2)
            if fuente and idiomas:
                texto = fuente.render(idiomas.t("camara_sin_imagen"), True, COLOR_GRIS)
                superficie.blit(texto, texto.get_rect(center=rect.center))

        if habitacion.solo_audio:
            if fuente and idiomas:
                texto = fuente.render(idiomas.t("camara_solo_audio"), True, COLOR_BLANCO)
                superficie.blit(texto, texto.get_rect(center=(rect.centerx, rect.top + 30)))
        elif animatronics_presentes:
            presentes = [
                animatronic for animatronic in animatronics_presentes
                if animatronic.habitacion_actual == habitacion.id
            ]
            for indice, animatronic in enumerate(presentes):
                self._dibujar_animatronic(superficie, rect, animatronic, fuente, indice)

        if fuente:
            etiqueta = f"CAM {habitacion.numero_camara} - {habitacion.nombre.upper()}"
            texto = fuente.render(etiqueta, True, COLOR_VERDE_ENERGIA)
            superficie.blit(texto, (rect.left + 10, rect.top + 10))

    def _dibujar_animatronic(self, superficie: pygame.Surface, rect: pygame.Rect,
                              animatronic, fuente, indice: int = 0):
        color = (220, 60, 60)
        centro = (rect.centerx + indice * 50 - 25, rect.centery)
        pygame.draw.circle(superficie, color, centro, 18)
        if fuente:
            texto = fuente.render(animatronic.nombre, True, COLOR_BLANCO)
            superficie.blit(texto, texto.get_rect(midtop=(centro[0], centro[1] + 22)))
