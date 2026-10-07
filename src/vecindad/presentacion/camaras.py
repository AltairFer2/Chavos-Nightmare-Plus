"""Panel de cámaras: el monitor a pantalla completa.

Al levantar el panel y al bajarlo, antes de todo esto, va la animación del
monitor acercándose o retirándose (ver animacion_monitor.py). Mientras dura no
se ve ninguna cámara, y como sus cuadros son transparentes alrededor del
aparato, quien la dibuja tiene que pintar el patio primero.

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

Cuándo se rompen las cámaras es una regla de juego y vive en el dominio; este
módulo solo le informa de lo que está pasando en pantalla. Son dos averías
distintas: el sabotaje de El Chavo (dominio/sabotaje.py), que tumba todo el
circuito hasta restablecerlo desde el barril, y la interferencia de una sola
cámara al moverse alguien delante (dominio/interferencia.py), que se arregla
sola a los pocos segundos.

Con El Chavo en la cámara que se mira, además, el monitor se vuelve
errático (monitor_erratico.py): la imagen tiembla y el mapa se va a saltos
con sus botones, para que escapar de su cámara antes de que la rompa cueste.
"""

from typing import Optional

import pygame

from ..config.interfaz import (
    CAMARA_AUDIO_EFECTO_SEGUNDOS,
    CAMARA_AUDIO_ONDA_COLOR,
    CAMARA_AUDIO_ONDA_GROSOR,
    CAMARA_AUDIO_ONDA_PERIODO,
    CAMARA_AUDIO_ONDA_RADIO_MAXIMO,
    CAMARA_AUDIO_ONDAS,
    CAMARA_DISTORSION_DESPLAZAMIENTO,
    CAMARA_DISTORSION_SEGUNDOS,
    CAMARA_ERRATICO_INTENSIDAD_MINIMA,
    CAMARA_ERRATICO_MAPA_AMPLITUD,
    CAMARA_ERRATICO_MAPA_CAMBIO_SEGUNDOS,
    CAMARA_ERRATICO_MAPA_PERSECUCION,
    CAMARA_ERRATICO_VISTA_AMPLITUD,
    CAMARA_ERRATICO_VISTA_CAMBIO_SEGUNDOS,
    CAMARA_ERRATICO_VISTA_PERSECUCION,
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
from ..dominio.interferencia import InterferenciaCamaras
from ..dominio.sabotaje import ControlSabotaje
from ..infraestructura.recursos import CacheImagenes
from ..mundo.habitaciones import HABITACIONES, obtener_habitacion
from .animacion_monitor import AnimacionMonitor
from .boton_audio import BotonAudio
from .efectos import crear_lineas_barrido, generar_frames_estatica
from .escenas_camara import EscenasCamara
from .mapa_camaras import MapaVecindad
from .monitor_erratico import DesplazamientoErratico


class SistemaCamaras:
    """Qué cámara está activa y cómo se dibuja el monitor."""

    def __init__(self, camara_inicial: str = "primer_patio"):
        self.camara_actual = camara_inicial
        self._activo = False
        self.animacion = AnimacionMonitor()

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
        # Dónde está sonando el audio de Quico y cuánto le queda a sus ondas.
        self._camara_con_audio: Optional[str] = None
        self._audio_restante = 0.0
        # El tirón que da el monitor cuando Doña Florinda se mueve.
        self._distorsion_restante = 0.0
        self._sabotaje = ControlSabotaje()
        self._interferencia = InterferenciaCamaras()
        # Lo errático que se pone el monitor con El Chavo en pantalla.
        self._erratico_mapa = DesplazamientoErratico(
            CAMARA_ERRATICO_MAPA_AMPLITUD,
            CAMARA_ERRATICO_MAPA_CAMBIO_SEGUNDOS,
            CAMARA_ERRATICO_MAPA_PERSECUCION,
        )
        self._erratico_vista = DesplazamientoErratico(
            CAMARA_ERRATICO_VISTA_AMPLITUD,
            CAMARA_ERRATICO_VISTA_CAMBIO_SEGUNDOS,
            CAMARA_ERRATICO_VISTA_PERSECUCION,
        )

    # ------------------------------------------------------------------
    # Estado
    # ------------------------------------------------------------------
    @property
    def averiadas(self) -> bool:
        return self._sabotaje.averiadas

    @property
    def activo(self) -> bool:
        """Si el monitor está levantado delante del jugador."""
        return self._activo

    @activo.setter
    def activo(self, levantado: bool):
        """Levantarlo lo trae a la vista y bajarlo lo retira, cada uno con su
        animación. Va en el descriptor y no en un método aparte porque el
        panel se sube y se baja desde varios sitios (la pestaña, la tecla, el
        tablero de servicios), y ninguno debería tener que acordarse."""
        levantado = bool(levantado)
        if levantado == self._activo:
            return
        self._activo = levantado
        if levantado:
            self.animacion.entrar()
        else:
            self.animacion.salir()

    @property
    def a_la_vista(self) -> bool:
        """El monitor ya acomodado delante de la cara. Mientras entra o sale
        todavía no hay cámara que mirar: lo que se ve es el patio con el
        aparato moviéndose por encima."""
        return self._activo and not self.animacion.en_marcha

    def abrir(self) -> bool:
        """Levanta el monitor. Devuelve si acaba de encenderse ahora, para
        que el bucle sepa cuándo suena el chasquido del tubo."""
        if self._activo:
            return False
        self.activo = True
        return True

    def reiniciar(self, camara_inicial: str, numero_noche: int = 1):
        """Lo deja como al empezar una noche: bajado, sin animación a medias,
        en la primera cámara y con todo el circuito en pie. Lo que aguanta
        El Chavo siendo observado depende de la noche."""
        self._activo = False
        self.animacion.cancelar()
        self.camara_actual = camara_inicial
        self._sabotaje = ControlSabotaje(numero_noche)
        self._erratico_mapa.reiniciar()
        self._erratico_vista.reiniciar()
        self._mapa.desplazamiento = (0, 0)
        self._camara_con_audio = None
        self._audio_restante = 0.0
        self._distorsion_restante = 0.0
        self.reparar()

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
        """Devuelve la imagen a todo el circuito: tanto el sabotaje como los
        cortes de señal que estuvieran corriendo."""
        self._sabotaje.reparar()
        self._interferencia.limpiar()

    def perder_senal(self, id_camara: str) -> bool:
        """Tumba esa cámara unos segundos. Devuelve si el corte empezó ahora,
        para que solo entonces suene la interferencia."""
        return self._interferencia.cortar(id_camara) > 0.0

    def sin_senal(self, id_camara: str) -> bool:
        return self._interferencia.sin_senal(id_camara)

    def sonar_audio_en(self, id_camara: str):
        """Marca que el audio de Quico está sonando en esa cámara: mientras
        dure, quien la mire ve las ondas."""
        self._camara_con_audio = id_camara
        self._audio_restante = CAMARA_AUDIO_EFECTO_SEGUNDOS

    def suena_audio_en(self, id_camara: str) -> bool:
        return self._audio_restante > 0.0 and self._camara_con_audio == id_camara

    def distorsionar(self):
        """Un tirón breve en la cámara que se esté mirando, sea cual sea.
        Es la señal de que Doña Florinda se acaba de mover."""
        self._distorsion_restante = CAMARA_DISTORSION_SEGUNDOS

    @property
    def distorsionada(self) -> bool:
        return self._distorsion_restante > 0.0

    def actualizar(self, dt: float, animatronics=()):
        self._contador_estatica += 1
        if self._contador_estatica >= CAMARA_ESTATICA_CAMBIO_FRAMES:
            self._contador_estatica = 0
            self._indice_estatica = (self._indice_estatica + 1) % len(self._frames_estatica)
        if self._transicion_restante > 0.0:
            self._transicion_restante = max(0.0, self._transicion_restante - dt)
        if self._audio_restante > 0.0:
            self._audio_restante = max(0.0, self._audio_restante - dt)
        if self._distorsion_restante > 0.0:
            self._distorsion_restante = max(0.0, self._distorsion_restante - dt)
        self.animacion.actualizar(dt)
        self._interferencia.actualizar(dt)
        # Solo cuenta lo que de verdad se ve: mientras el monitor sube no hay
        # cámara en pantalla, y con un aguante de un segundo esa animación se
        # comería el margen para reaccionar.
        observado = self.a_la_vista and self._saboteador_a_la_vista(animatronics)
        self._sabotaje.actualizar(dt, observado)
        intensidad = self._intensidad_erratica(observado)
        self._erratico_mapa.actualizar(dt, intensidad)
        self._erratico_vista.actualizar(dt, intensidad)
        self._mapa.desplazamiento = self._desplazamiento_del_mapa()

    def _desplazamiento_del_mapa(self):
        """El mapa está pegado a la esquina de abajo a la derecha, así que
        los saltos hacia allá chocarían con el borde. Se mueve alrededor de un
        centro corrido hacia arriba a la izquierda: nada más ver a El Chavo
        el mapa ya pega un salto, y desde ahí tiene sitio para ir y venir."""
        dx, dy = self._erratico_mapa.desplazamiento
        intensidad = self._erratico_mapa.intensidad
        ancho, alto = CAMARA_ERRATICO_MAPA_AMPLITUD
        return (dx - round(ancho * intensidad), dy - round(alto * intensidad))

    def _intensidad_erratica(self, observado: bool) -> float:
        """Nada más verlo el monitor ya se descontrola, y va a peor conforme
        se acerca a romperlo. Rotas ya no hay cámara que mover."""
        if not observado or self.averiadas:
            return 0.0
        return max(CAMARA_ERRATICO_INTENSIDAD_MINIMA, self._sabotaje.proporcion)

    @property
    def erratico(self) -> bool:
        """Si el monitor se está moviendo por culpa de El Chavo."""
        return self._erratico_mapa.intensidad > 0.0

    @property
    def desplazamiento_mapa(self):
        return self._mapa.desplazamiento

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

        if self.suena_audio_en(habitacion.id) and not self.averiadas:
            self._dibujar_ondas(superficie)

        superficie.blit(self._lineas, (0, 0))
        superficie.blit(self._frames_estatica[self._indice_estatica], (0, 0))
        if self._transicion_restante > 0.0 or self._fallando() or self.distorsionada:
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

    def _dibujar_ondas(self, superficie: pygame.Surface):
        """Ondas que se abren desde el centro de la cámara donde suena el
        audio, cada una apagándose conforme crece."""
        transcurrido = CAMARA_AUDIO_EFECTO_SEGUNDOS - self._audio_restante
        centro = (ANCHO_PANTALLA // 2, ALTO_PANTALLA // 2)
        for onda in range(CAMARA_AUDIO_ONDAS):
            fase = (transcurrido / CAMARA_AUDIO_ONDA_PERIODO + onda / CAMARA_AUDIO_ONDAS) % 1.0
            radio = int(CAMARA_AUDIO_ONDA_RADIO_MAXIMO * fase)
            if radio <= CAMARA_AUDIO_ONDA_GROSOR:
                continue
            brillo = 1.0 - fase
            color = tuple(int(canal * brillo) for canal in CAMARA_AUDIO_ONDA_COLOR)
            pygame.draw.circle(superficie, color, centro, radio, CAMARA_AUDIO_ONDA_GROSOR)

    def _desplazamiento_de_la_vista(self):
        """Lo errático de El Chavo más, si toca, el tirón de Doña Florinda,
        que corre la imagen a un lado y al otro."""
        dx, dy = self._erratico_vista.desplazamiento
        if self.distorsionada:
            lado = 1 if self._indice_estatica % 2 == 0 else -1
            dx += lado * CAMARA_DISTORSION_DESPLAZAMIENTO
        return (dx, dy)

    def _fallando(self) -> bool:
        """El aviso de que El Chavo está a punto de romperlas: la estática
        fuerte entra y sale, un cuadro sí y otro no."""
        return self._sabotaje.a_punto and self._indice_estatica % 2 == 0

    def _dibujar_vista(self, superficie, habitacion, animatronics, fuente, idiomas):
        superficie.fill(COLOR_NEGRO)
        if self.averiadas:
            # Sin señal en ninguna cámara hasta restablecerlas desde el barril.
            superficie.blit(self._estatica_transicion[self._indice_estatica], (0, 0))
            self._escribir_al_centro(superficie, fuente, idiomas, "camara_averiada")
            return

        if self.sin_senal(habitacion.id):
            # Se movió alguien mientras se le miraba y esta vista se cayó. Se
            # arregla sola: por eso el aviso no pide restablecer nada.
            superficie.blit(self._estatica_transicion[self._indice_estatica], (0, 0))
            self._escribir_al_centro(superficie, fuente, idiomas, "camara_sin_senal")
            return

        if habitacion.solo_audio:
            self._escribir_al_centro(superficie, fuente, idiomas, "camara_solo_audio")
            return

        imagen = self._escena_o_vacia(habitacion, animatronics)
        if imagen is not None:
            # Con El Chavo en pantalla la imagen tiembla a tirones; lo que
            # queda al descubierto por los bordes se ve negro, como un tubo
            # que pierde el enganche.
            superficie.blit(imagen, self._desplazamiento_de_la_vista())
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
