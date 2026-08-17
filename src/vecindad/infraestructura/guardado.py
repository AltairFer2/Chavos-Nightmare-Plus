"""Persistencia en disco del progreso del jugador y de sus preferencias.

Se usan dos archivos JSON separados dentro de DIR_DATOS_USUARIO:
- progreso.json: hasta qué noche llegó el jugador (define los desbloqueos).
- configuracion.json: idioma, modo streamer, pantalla completa, resolución,
  brillo y volúmenes.

Están separados a propósito: borrar o corromper el progreso no debe hacer
que el jugador pierda también sus preferencias, ni al revés. Si un archivo
no existe o está dañado, se parte de valores por defecto en lugar de fallar.
"""

import json
from pathlib import Path

from ..config.audio import (
    VOLUMEN_EFECTOS_POR_DEFECTO,
    VOLUMEN_MAXIMO,
    VOLUMEN_MINIMO,
    VOLUMEN_MUSICA_POR_DEFECTO,
)
from ..config.partida import NOCHES_HISTORIA, ULTIMA_NOCHE
from ..config.rutas import (
    ARCHIVO_CONFIGURACION,
    ARCHIVO_PROGRESO,
    DIR_DATOS_USUARIO,
)
from ..config.ventana import (
    BRILLO_MAXIMO,
    BRILLO_MINIMO,
    BRILLO_POR_DEFECTO,
    PANTALLA_COMPLETA_POR_DEFECTO,
    RESOLUCION_BASE,
    RESOLUCIONES_DISPONIBLES,
)
from ..i18n import IDIOMA_POR_DEFECTO, IDIOMAS_DISPONIBLES


def _leer_json(ruta: Path) -> dict:
    """Lee un JSON de disco. Devuelve {} si no existe o no es legible; un
    guardado dañado no debe impedir que el juego arranque."""
    try:
        with ruta.open("r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
    except (OSError, json.JSONDecodeError):
        return {}
    return datos if isinstance(datos, dict) else {}


def _escribir_json(ruta: Path, datos: dict) -> bool:
    """Escribe el JSON creando la carpeta si hace falta. Devuelve si tuvo
    éxito, para que quien llame pueda avisar en vez de asumir que guardó."""
    try:
        DIR_DATOS_USUARIO.mkdir(parents=True, exist_ok=True)
        with ruta.open("w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, indent=2, ensure_ascii=False)
    except OSError:
        return False
    return True


class ProgresoJugador:
    """Noche más avanzada que el jugador ha superado, más el dato de si
    llegó a empezar una partida. De ahí se derivan los desbloqueos del menú.

    Hacen falta los dos: recién empezada una partida nueva no hay ninguna
    noche superada todavía, pero Continuar tiene que ofrecer la noche 1 en
    vez de decir que no hay partida.
    """

    def __init__(self, noches_completadas: int = 0, partida_iniciada: bool = False):
        self.noches_completadas = self._sanear(noches_completadas)
        # Haber superado noches implica haber empezado, aunque el archivo
        # venga de una versión anterior que no guardaba este dato.
        self.partida_iniciada = bool(partida_iniciada) or self.noches_completadas > 0

    @staticmethod
    def _sanear(valor) -> int:
        if not isinstance(valor, int) or isinstance(valor, bool):
            return 0
        return max(0, min(ULTIMA_NOCHE, valor))

    @property
    def hay_partida_guardada(self) -> bool:
        return self.partida_iniciada

    @property
    def proxima_noche(self) -> int:
        """Noche que ofrece la opción Continuar."""
        return min(self.noches_completadas + 1, ULTIMA_NOCHE)

    @property
    def noche_extra_desbloqueada(self) -> bool:
        """La Noche 6 aparece al completar la noche 5."""
        return self.noches_completadas >= NOCHES_HISTORIA

    @property
    def noche_personalizada_desbloqueada(self) -> bool:
        """La Noche Personalizada aparece al completar la noche 6."""
        return self.noches_completadas >= ULTIMA_NOCHE

    def registrar_noche_completada(self, numero_noche: int) -> bool:
        """Guarda el avance solo si supera la marca anterior. Devuelve si
        hubo progreso nuevo que persistir."""
        if numero_noche <= self.noches_completadas:
            return False
        self.noches_completadas = self._sanear(numero_noche)
        self.partida_iniciada = True
        self.guardar()
        return True

    def empezar_de_cero(self) -> bool:
        """Borra el avance: es lo que hace Nuevo Juego.

        A partir de aquí Continuar vuelve a ofrecer la noche 1, y la Noche 6
        y la Personalizada se cierran hasta volver a ganárselas. Se persiste
        al momento, así que sigue así aunque el jugador cierre el juego sin
        terminar la noche que acaba de empezar.
        """
        self.noches_completadas = 0
        self.partida_iniciada = True
        return self.guardar()

    @classmethod
    def cargar(cls) -> "ProgresoJugador":
        datos = _leer_json(ARCHIVO_PROGRESO)
        return cls(
            noches_completadas=datos.get("noches_completadas", 0),
            partida_iniciada=datos.get("partida_iniciada", False),
        )

    def guardar(self) -> bool:
        return _escribir_json(
            ARCHIVO_PROGRESO,
            {
                "noches_completadas": self.noches_completadas,
                "partida_iniciada": self.partida_iniciada,
            },
        )


def existe_configuracion_guardada() -> bool:
    """Si ya hay un configuracion.json en disco. Sirve para distinguir la
    primera vez que corre el juego (arranca en pantalla completa) de una
    partida donde el jugador ya eligió sus preferencias."""
    return ARCHIVO_CONFIGURACION.exists()


class Configuracion:
    """Preferencias del jugador: idioma, modo streamer, resolución, brillo y
    volúmenes."""

    def __init__(
        self,
        idioma: str = IDIOMA_POR_DEFECTO,
        modo_streamer: bool = False,
        pantalla_completa: bool = PANTALLA_COMPLETA_POR_DEFECTO,
        resolucion=RESOLUCION_BASE,
        brillo: int = BRILLO_POR_DEFECTO,
        volumen_musica: int = VOLUMEN_MUSICA_POR_DEFECTO,
        volumen_efectos: int = VOLUMEN_EFECTOS_POR_DEFECTO,
    ):
        self.idioma = idioma if idioma in IDIOMAS_DISPONIBLES else IDIOMA_POR_DEFECTO
        self.modo_streamer = bool(modo_streamer)
        self.pantalla_completa = bool(pantalla_completa)
        self.resolucion = self._sanear_resolucion(resolucion)
        self.brillo = self._sanear_brillo(brillo)
        self.volumen_musica = self._sanear_volumen(volumen_musica, VOLUMEN_MUSICA_POR_DEFECTO)
        self.volumen_efectos = self._sanear_volumen(volumen_efectos, VOLUMEN_EFECTOS_POR_DEFECTO)

    @staticmethod
    def _sanear_resolucion(valor):
        """Solo se aceptan resoluciones de la lista soportada: un valor
        editado a mano no debe dejar la ventana en un tamaño imposible."""
        try:
            candidata = (int(valor[0]), int(valor[1]))
        except (TypeError, ValueError, IndexError, KeyError):
            return RESOLUCION_BASE
        return candidata if candidata in RESOLUCIONES_DISPONIBLES else RESOLUCION_BASE

    @staticmethod
    def _sanear_brillo(valor) -> int:
        """Un brillo fuera de rango dejaría la pantalla negra o en blanco."""
        if not isinstance(valor, int) or isinstance(valor, bool):
            return BRILLO_POR_DEFECTO
        return max(BRILLO_MINIMO, min(BRILLO_MAXIMO, valor))

    @staticmethod
    def _sanear_volumen(valor, por_defecto: int) -> int:
        if not isinstance(valor, int) or isinstance(valor, bool):
            return por_defecto
        return max(VOLUMEN_MINIMO, min(VOLUMEN_MAXIMO, valor))

    @classmethod
    def cargar(cls) -> "Configuracion":
        datos = _leer_json(ARCHIVO_CONFIGURACION)
        return cls(
            idioma=datos.get("idioma", IDIOMA_POR_DEFECTO),
            modo_streamer=datos.get("modo_streamer", False),
            pantalla_completa=datos.get("pantalla_completa", PANTALLA_COMPLETA_POR_DEFECTO),
            resolucion=datos.get("resolucion", RESOLUCION_BASE),
            brillo=datos.get("brillo", BRILLO_POR_DEFECTO),
            volumen_musica=datos.get("volumen_musica", VOLUMEN_MUSICA_POR_DEFECTO),
            volumen_efectos=datos.get("volumen_efectos", VOLUMEN_EFECTOS_POR_DEFECTO),
        )

    def guardar(self) -> bool:
        return _escribir_json(
            ARCHIVO_CONFIGURACION,
            {
                "idioma": self.idioma,
                "modo_streamer": self.modo_streamer,
                "pantalla_completa": self.pantalla_completa,
                "resolucion": list(self.resolucion),
                "brillo": self.brillo,
                "volumen_musica": self.volumen_musica,
                "volumen_efectos": self.volumen_efectos,
            },
        )
