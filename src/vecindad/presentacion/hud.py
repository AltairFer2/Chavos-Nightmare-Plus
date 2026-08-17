"""Interfaz durante la partida: HUD (noche, hora, batería, posición) y
pantallas de fin de partida.

El HUD se dibuja por encima de la oscuridad de la vista, así que siempre es
legible aunque la linterna esté apagada. Con el panel de cámaras delante se
oculta el nombre de la posición, porque ese rótulo ya lo pone el marco del
monitor.

El menú principal vive en presentacion/menu/ y el panel de cámaras en
presentacion/camaras.py; aquí solo queda lo que se dibuja con una noche en
curso o al terminarla.
"""

from dataclasses import dataclass

# pyrefly: ignore [missing-import]
import pygame

from ..config.interfaz import (
    COLOR_AMARILLO_AVISO,
    COLOR_BLANCO,
    COLOR_GRIS,
    COLOR_GRIS_OSCURO,
    COLOR_NEGRO,
    COLOR_ROJO_ALERTA,
    COLOR_VERDE_ENERGIA,
    FUENTE_TAMANO_CAMARA,
    FUENTE_TAMANO_HUD,
    FUENTE_TAMANO_TEXTO,
    FUENTE_TAMANO_TITULO,
    ICONO_OBJETO_HUD,
    POSICION_HUD_CAMARAS,
    POSICION_HUD_PATIO,
)
from ..config.rutas import DIR_ASSETS_UI
from ..config.ventana import ALTO_PANTALLA, ANCHO_PANTALLA, RESOLUCION_BASE
from ..dominio.inventario import ORDEN_ARROJABLES
from ..infraestructura.fuentes import crear_fuente
from ..infraestructura.recursos import CacheImagenes
from .iconos import IconosObjetos

# Fondo de la pantalla de derrota. Si el archivo no existe todavía se cae al
# relleno negro de siempre, como el resto del arte opcional del proyecto.
ARCHIVO_GAME_OVER_FONDO = "game over.png"

COLOR_FRANJA_GAME_OVER = (0, 0, 0, 150)

# Fila de objetos del inventario, encima de la franja de ayuda.
SEPARACION_INVENTARIO = 10
Y_INVENTARIO = ALTO_PANTALLA - 130

# Pestañas de abajo que levantan el monitor y el tablero de servicios. Basta
# con pasarles el ratón por encima, al estilo del género.
ANCHO_TIRA = 240
ALTO_TIRA = 34
RECT_TIRA_SERVICIOS = pygame.Rect(
    ANCHO_PANTALLA // 2 - ANCHO_TIRA - 10, ALTO_PANTALLA - ALTO_TIRA - 8,
    ANCHO_TIRA, ALTO_TIRA,
)
RECT_TIRA_CAMARAS = pygame.Rect(
    ANCHO_PANTALLA // 2 + 10, ALTO_PANTALLA - ALTO_TIRA - 8, ANCHO_TIRA, ALTO_TIRA,
)

COLOR_FONDO_RANURA = (0, 0, 0, 140)
COLOR_TIRA = (0, 0, 0, 150)
COLOR_TIRA_RESALTADA = (235, 225, 180, 225)


@dataclass
class EstadoHud:
    """Lo que el HUD necesita saber de la partida para dibujarse."""

    numero_noche: int = 1
    en_camaras: bool = False
    en_servicios: bool = False
    objeto_a_recoger: str = ""
    peticion: str = ""  # nombre visible de lo que pide Doña Clotilde
    id_peticion: str = ""  # su id, para el icono
    tira_resaltada: str = ""  # "camaras", "servicios" o vacío
    aviso: str = ""  # mensaje corto tras usar un servicio o arrojar algo


class InterfazJuego:
    """Agrupa el dibujado de las pantallas de partida."""

    def __init__(self, idiomas, iconos: IconosObjetos):
        self.idiomas = idiomas
        self.iconos = iconos
        self.fuente_titulo = crear_fuente(FUENTE_TAMANO_TITULO, negrita=True)
        self.fuente_texto = crear_fuente(FUENTE_TAMANO_TEXTO)
        self.fuente_hud = crear_fuente(FUENTE_TAMANO_HUD)
        self.fuente_camara = crear_fuente(FUENTE_TAMANO_CAMARA, negrita=True)
        self._fondos_fin = CacheImagenes(tamano=RESOLUCION_BASE)

    def dibujar_hud(self, superficie: pygame.Surface, temporizador, jugador, linterna,
                    inventario, estado: "EstadoHud"):
        # Con el monitor delante el HUD se mete dentro del marco, a la
        # izquierda: en las esquinas está el arte del marco y abajo a la
        # derecha, el mapa.
        en_panel = estado.en_camaras or estado.en_servicios
        x, y_noche = (POSICION_HUD_CAMARAS if en_panel else POSICION_HUD_PATIO)

        texto_noche = self.fuente_hud.render(
            self.idiomas.t("hud_noche", noche=estado.numero_noche), True, COLOR_BLANCO
        )
        superficie.blit(texto_noche, (x, y_noche))

        texto_hora = self.fuente_hud.render(
            f"{temporizador.hora_actual()}:00 AM", True, COLOR_BLANCO
        )
        superficie.blit(texto_hora, (x, y_noche + 22))

        if not en_panel:
            texto_posicion = self.fuente_hud.render(
                self.idiomas.t(f"posicion_{jugador.posicion}"), True, COLOR_AMARILLO_AVISO
            )
            superficie.blit(texto_posicion, (x, 20))

        self._dibujar_bateria(superficie, linterna, en_panel)
        if not jugador.esta_escondido:
            self._dibujar_inventario(superficie, inventario)
        self._dibujar_peticion(superficie, estado)
        if jugador.esta_escondido and not en_panel:
            self._dibujar_tiras(superficie, estado)
        self._dibujar_ayuda(superficie, jugador, estado)

    def _dibujar_inventario(self, superficie: pygame.Surface, inventario):
        """Fila de objetos que el jugador puede arrojar. El número de cada
        uno es fijo aunque falten los de en medio, para que la tecla siga
        siendo la misma toda la noche."""
        llevados = inventario.arrojables()
        if not llevados:
            return

        paso = ICONO_OBJETO_HUD + SEPARACION_INVENTARIO
        inicio = (ANCHO_PANTALLA - (len(llevados) * paso - SEPARACION_INVENTARIO)) // 2
        for indice, id_objeto in enumerate(llevados):
            x = inicio + indice * paso
            recuadro = pygame.Rect(x, Y_INVENTARIO, ICONO_OBJETO_HUD, ICONO_OBJETO_HUD)
            self._pintar(superficie, recuadro, COLOR_FONDO_RANURA)
            pygame.draw.rect(superficie, COLOR_GRIS, recuadro, width=1)

            icono = self.iconos.obtener(id_objeto, ICONO_OBJETO_HUD)
            if icono is not None:
                superficie.blit(icono, recuadro)

            numero = ORDEN_ARROJABLES.index(id_objeto) + 1
            texto = self.fuente_camara.render(str(numero), True, COLOR_AMARILLO_AVISO)
            superficie.blit(texto, (recuadro.x + 3, recuadro.y + 1))

    def _dibujar_peticion(self, superficie: pygame.Surface, estado: "EstadoHud"):
        """Lo que Doña Clotilde reclama mientras está delante."""
        if not estado.id_peticion:
            return
        aviso = self.idiomas.t("clotilde_pide", objeto=estado.peticion)
        texto = self.fuente_texto.render(aviso, True, COLOR_AMARILLO_AVISO)
        rect = texto.get_rect(center=(ANCHO_PANTALLA // 2, 110))
        superficie.blit(texto, rect)
        icono = self.iconos.obtener(estado.id_peticion, ICONO_OBJETO_HUD)
        if icono is not None:
            superficie.blit(icono, icono.get_rect(midleft=(rect.right + 10, rect.centery)))

    def _dibujar_tiras(self, superficie: pygame.Surface, estado: "EstadoHud"):
        """Las dos pestañas de abajo. Basta con pasarles el ratón por encima
        para levantar el monitor o el tablero de servicios."""
        for rect, clave, resaltada in (
            (RECT_TIRA_SERVICIOS, "tira_servicios", estado.tira_resaltada == "servicios"),
            (RECT_TIRA_CAMARAS, "tira_camaras", estado.tira_resaltada == "camaras"),
        ):
            self._pintar(superficie, rect, COLOR_TIRA_RESALTADA if resaltada else COLOR_TIRA)
            pygame.draw.rect(superficie, COLOR_GRIS, rect, width=1)
            color = COLOR_NEGRO if resaltada else COLOR_BLANCO
            texto = self.fuente_camara.render(self.idiomas.t(clave), True, color)
            superficie.blit(texto, texto.get_rect(center=rect.center))

    @staticmethod
    def _pintar(superficie: pygame.Surface, rect: pygame.Rect, color):
        capa = pygame.Surface(rect.size, pygame.SRCALPHA)
        capa.fill(color)
        superficie.blit(capa, rect)

    def _dibujar_bateria(self, superficie: pygame.Surface, linterna, en_panel: bool):
        ancho_barra = 200
        if en_panel:
            x, y = POSICION_HUD_CAMARAS[0], POSICION_HUD_CAMARAS[1] + 66
        else:
            x, y = ANCHO_PANTALLA - ancho_barra - 20, ALTO_PANTALLA - 40

        color_barra = COLOR_VERDE_ENERGIA if linterna.carga > 0.25 else COLOR_ROJO_ALERTA
        pygame.draw.rect(superficie, COLOR_GRIS_OSCURO, (x, y, ancho_barra, 18))
        pygame.draw.rect(
            superficie, color_barra, (x, y, int(ancho_barra * linterna.carga), 18)
        )

        etiqueta = (
            f"{self.idiomas.t('hud_bateria')} {int(linterna.carga * 100)}%"
            f"   +{linterna.baterias_repuesto}"
        )
        texto = self.fuente_hud.render(etiqueta, True, COLOR_BLANCO)
        superficie.blit(texto, (x, y - 22))

        if linterna.agotada:
            aviso = self.idiomas.t(
                "linterna_cambiar" if linterna.baterias_repuesto > 0 else "linterna_agotada"
            )
            texto_aviso = self.fuente_texto.render(aviso, True, COLOR_ROJO_ALERTA)
            superficie.blit(
                texto_aviso, texto_aviso.get_rect(center=(ANCHO_PANTALLA // 2, 60))
            )

    def _dibujar_ayuda(self, superficie: pygame.Surface, jugador, estado: "EstadoHud"):
        if estado.objeto_a_recoger:
            aviso = self.idiomas.t("objeto_recoger", objeto=estado.objeto_a_recoger)
            texto = self.fuente_texto.render(aviso, True, COLOR_AMARILLO_AVISO)
            superficie.blit(
                texto, texto.get_rect(center=(ANCHO_PANTALLA // 2, ALTO_PANTALLA - 168))
            )

        if estado.aviso:
            texto = self.fuente_texto.render(estado.aviso, True, COLOR_BLANCO)
            superficie.blit(
                texto, texto.get_rect(center=(ANCHO_PANTALLA // 2, 60))
            )

        if estado.en_camaras:
            clave = "ayuda_camaras"
        elif estado.en_servicios:
            clave = "ayuda_servicios"
        elif jugador.esta_escondido:
            return  # las pestañas ya dicen lo que hay que hacer
        else:
            clave = "ayuda_patio"
        texto_ayuda = self.fuente_camara.render(self.idiomas.t(clave), True, COLOR_GRIS)
        superficie.blit(
            texto_ayuda, texto_ayuda.get_rect(center=(ANCHO_PANTALLA // 2, ALTO_PANTALLA - 24))
        )

    def dibujar_game_over(self, superficie: pygame.Surface, nombre_animatronic: str,
                          clave_motivo: str = "game_over_motivo"):
        fondo = self._fondos_fin.obtener(
            ARCHIVO_GAME_OVER_FONDO, DIR_ASSETS_UI / ARCHIVO_GAME_OVER_FONDO
        )
        if fondo is not None:
            superficie.blit(fondo, (0, 0))
        else:
            superficie.fill(COLOR_NEGRO)

        # Franja oscura detrás del bloque de texto: la imagen de fondo tiene
        # zonas claras (la luna, la ventana iluminada) que sin esto podrían
        # dejar el texto poco legible según dónde caigan.
        self._pintar(superficie, pygame.Rect(0, 210, ANCHO_PANTALLA, 240), COLOR_FRANJA_GAME_OVER)

        texto = self.fuente_titulo.render(
            self.idiomas.t("game_over_titulo"), True, COLOR_ROJO_ALERTA
        )
        superficie.blit(texto, texto.get_rect(center=(ANCHO_PANTALLA // 2, 260)))

        if nombre_animatronic:
            motivo = self.idiomas.t(clave_motivo, nombre=nombre_animatronic)
            subtexto = self.fuente_texto.render(motivo, True, COLOR_BLANCO)
            superficie.blit(subtexto, subtexto.get_rect(center=(ANCHO_PANTALLA // 2, 330)))

        ayuda = self.fuente_texto.render(self.idiomas.t("ayuda_fin"), True, COLOR_BLANCO)
        superficie.blit(ayuda, ayuda.get_rect(center=(ANCHO_PANTALLA // 2, 410)))
