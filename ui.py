"""Interfaz durante la partida: HUD (noche, hora, energía), selector de
cámaras y pantallas de fin de partida.

El menú principal vive en menu.py; aquí solo queda lo que se dibuja con una
noche en curso o al terminarla.
"""

import pygame

from camaras import ORDEN_PANEL
from constants import (
    ALTO_PANTALLA,
    ANCHO_PANTALLA,
    COLOR_AMARILLO_AVISO,
    COLOR_BLANCO,
    COLOR_GRIS_OSCURO,
    COLOR_NEGRO,
    COLOR_ROJO_ALERTA,
    COLOR_VERDE_ENERGIA,
    FUENTE_TAMANO_CAMARA,
    FUENTE_TAMANO_HUD,
    FUENTE_TAMANO_TEXTO,
    FUENTE_TAMANO_TITULO,
)
from fuentes import crear_fuente
from habitaciones import HABITACIONES


class InterfazJuego:
    """Agrupa el dibujado de las pantallas de partida."""

    def __init__(self, idiomas):
        self.idiomas = idiomas
        self.fuente_titulo = crear_fuente(FUENTE_TAMANO_TITULO, negrita=True)
        self.fuente_texto = crear_fuente(FUENTE_TAMANO_TEXTO)
        self.fuente_hud = crear_fuente(FUENTE_TAMANO_HUD)
        self.fuente_camara = crear_fuente(FUENTE_TAMANO_CAMARA, negrita=True)

    def dibujar_hud(self, superficie: pygame.Surface, temporizador, camara_activa: str,
                    numero_noche: int):
        habitacion = HABITACIONES[camara_activa]

        texto_noche = self.fuente_hud.render(
            self.idiomas.t("hud_noche", noche=numero_noche), True, COLOR_BLANCO
        )
        superficie.blit(texto_noche, (20, ALTO_PANTALLA - 62))

        texto_hora = self.fuente_hud.render(f"{temporizador.hora_actual()}:00 AM", True, COLOR_BLANCO)
        superficie.blit(texto_hora, (20, ALTO_PANTALLA - 40))

        porcentaje = temporizador.porcentaje_energia()
        color_barra = COLOR_VERDE_ENERGIA if porcentaje > 0.25 else COLOR_ROJO_ALERTA
        ancho_barra = 200
        pygame.draw.rect(
            superficie, COLOR_GRIS_OSCURO,
            (ANCHO_PANTALLA - ancho_barra - 20, ALTO_PANTALLA - 40, ancho_barra, 18),
        )
        pygame.draw.rect(
            superficie, color_barra,
            (ANCHO_PANTALLA - ancho_barra - 20, ALTO_PANTALLA - 40, int(ancho_barra * porcentaje), 18),
        )
        texto_energia = self.fuente_hud.render(
            f"{self.idiomas.t('hud_energia')} {int(porcentaje * 100)}%", True, COLOR_BLANCO
        )
        superficie.blit(texto_energia, (ANCHO_PANTALLA - ancho_barra - 20, ALTO_PANTALLA - 62))

        texto_camara = self.fuente_hud.render(
            f"CAM {habitacion.numero_camara} - {habitacion.nombre}", True, COLOR_AMARILLO_AVISO
        )
        superficie.blit(texto_camara, (20, 20))

    def dibujar_panel_selector(self, superficie: pygame.Surface, camara_activa: str,
                               rect: pygame.Rect):
        pygame.draw.rect(superficie, COLOR_GRIS_OSCURO, rect)
        columnas = 4
        margen = 8
        ancho_boton = (rect.width - margen * (columnas + 1)) // columnas
        alto_boton = 34
        botones = {}

        for indice, id_habitacion in enumerate(ORDEN_PANEL):
            fila = indice // columnas
            columna = indice % columnas
            x = rect.left + margen + columna * (ancho_boton + margen)
            y = rect.top + margen + fila * (alto_boton + margen)
            boton_rect = pygame.Rect(x, y, ancho_boton, alto_boton)
            habitacion = HABITACIONES[id_habitacion]

            es_activa = id_habitacion == camara_activa
            color_fondo = COLOR_VERDE_ENERGIA if es_activa else COLOR_GRIS_OSCURO
            color_texto = COLOR_NEGRO if es_activa else COLOR_BLANCO
            pygame.draw.rect(superficie, color_fondo, boton_rect, border_radius=4)
            pygame.draw.rect(superficie, COLOR_BLANCO, boton_rect, width=1, border_radius=4)

            etiqueta = f"{habitacion.numero_camara} {habitacion.nombre}"
            texto = self.fuente_camara.render(etiqueta, True, color_texto)
            while texto.get_width() > ancho_boton - 8 and len(etiqueta) > 4:
                etiqueta = etiqueta[:-2]
                texto = self.fuente_camara.render(etiqueta + ".", True, color_texto)
            superficie.blit(texto, texto.get_rect(center=boton_rect.center))

            botones[id_habitacion] = boton_rect

        return botones

    def dibujar_game_over(self, superficie: pygame.Surface, nombre_animatronic: str):
        superficie.fill(COLOR_NEGRO)
        texto = self.fuente_titulo.render(
            self.idiomas.t("game_over_titulo"), True, COLOR_ROJO_ALERTA
        )
        superficie.blit(texto, texto.get_rect(center=(ANCHO_PANTALLA // 2, 260)))

        if nombre_animatronic:
            motivo = self.idiomas.t("game_over_motivo", nombre=nombre_animatronic)
            subtexto = self.fuente_texto.render(motivo, True, COLOR_BLANCO)
            superficie.blit(subtexto, subtexto.get_rect(center=(ANCHO_PANTALLA // 2, 330)))

        ayuda = self.fuente_texto.render(self.idiomas.t("ayuda_fin"), True, COLOR_BLANCO)
        superficie.blit(ayuda, ayuda.get_rect(center=(ANCHO_PANTALLA // 2, 410)))

    def dibujar_victoria(self, superficie: pygame.Surface, noche_personalizada: bool = False):
        superficie.fill(COLOR_NEGRO)
        clave = "victoria_personalizada" if noche_personalizada else "victoria_titulo"
        texto = self.fuente_titulo.render(self.idiomas.t(clave), True, COLOR_VERDE_ENERGIA)
        superficie.blit(texto, texto.get_rect(center=(ANCHO_PANTALLA // 2, 260)))
        ayuda = self.fuente_texto.render(self.idiomas.t("ayuda_fin"), True, COLOR_BLANCO)
        superficie.blit(ayuda, ayuda.get_rect(center=(ANCHO_PANTALLA // 2, 350)))
