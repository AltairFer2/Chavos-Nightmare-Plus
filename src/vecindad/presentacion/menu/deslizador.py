"""Barras deslizantes de volumen de la pantalla de Ajustes.

Se controlan con las flechas igual que el resto de opciones, pero además se
pueden arrastrar con el ratón, así que necesitan geometría propia: dónde cae
la barra de cada fila y qué volumen corresponde a una posición X del cursor.
"""

import pygame

from ...config.audio import VOLUMEN_MAXIMO
from ...config.interfaz import (
    COLOR_BLANCO,
    COLOR_GRIS_OSCURO,
    COLOR_OPCION_NORMAL,
    COLOR_OPCION_RESALTADA,
    COLOR_VERDE_ENERGIA,
    FUENTE_TAMANO_MENU,
    MENU_ALTO_LINEA,
    MENU_DESLIZADOR_ALTO,
    MENU_DESLIZADOR_ANCHO,
    MENU_DESLIZADOR_X,
    MENU_MARGEN_IZQUIERDO,
    MENU_Y_PRIMERA_OPCION,
)
from ...infraestructura.fuentes import crear_fuente

# Hasta dónde llega el área sensible de una fila con barra: cubre el texto,
# la barra y el porcentaje, para que el hover no se pierda al pasar de uno a
# otro.
MARGEN_PORCENTAJE = 90
ANCHO_FILA_DESLIZABLE = (
    MENU_DESLIZADOR_X + MENU_DESLIZADOR_ANCHO + MARGEN_PORCENTAJE
) - MENU_MARGEN_IZQUIERDO

SEPARACION_TEXTO_VALOR = 18


def rect_deslizador(indice: int) -> pygame.Rect:
    """Barra de la fila que ocupa esa posición en la lista de opciones."""
    fuente = crear_fuente(FUENTE_TAMANO_MENU)
    y_centro = (
        MENU_Y_PRIMERA_OPCION + indice * MENU_ALTO_LINEA + fuente.get_height() // 2
    )
    return pygame.Rect(
        MENU_DESLIZADOR_X,
        y_centro - MENU_DESLIZADOR_ALTO // 2,
        MENU_DESLIZADOR_ANCHO,
        MENU_DESLIZADOR_ALTO,
    )


def volumen_en(rect: pygame.Rect, x_pixel: int) -> int:
    """Traduce la posición X del cursor dentro de la barra a un 0-100."""
    proporcion = (x_pixel - rect.left) / rect.width if rect.width else 0.0
    return round(max(0.0, min(1.0, proporcion)) * VOLUMEN_MAXIMO)


def dibujar_deslizador(superficie: pygame.Surface, indice: int, valor: int,
                       resaltada: bool):
    rect = rect_deslizador(indice)
    color_borde = COLOR_OPCION_RESALTADA if resaltada else COLOR_OPCION_NORMAL
    radio = rect.height // 2

    pygame.draw.rect(superficie, COLOR_GRIS_OSCURO, rect, border_radius=radio)
    ancho_relleno = int(rect.width * valor / VOLUMEN_MAXIMO)
    if ancho_relleno > 0:
        relleno = pygame.Rect(rect.left, rect.top, ancho_relleno, rect.height)
        pygame.draw.rect(superficie, COLOR_VERDE_ENERGIA, relleno, border_radius=radio)
    pygame.draw.rect(superficie, color_borde, rect, width=2, border_radius=radio)
    pygame.draw.circle(
        superficie, COLOR_BLANCO, (rect.left + ancho_relleno, rect.centery), rect.height
    )

    fuente = crear_fuente(FUENTE_TAMANO_MENU)
    texto_valor = fuente.render(f"{valor}%", True, color_borde)
    superficie.blit(
        texto_valor,
        (
            rect.right + SEPARACION_TEXTO_VALOR,
            rect.centery - texto_valor.get_height() // 2,
        ),
    )
