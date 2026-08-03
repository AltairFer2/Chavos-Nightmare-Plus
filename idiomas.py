"""Textos de la interfaz en español, inglés y portugués.

Todo texto visible para el jugador debe pedirse aquí mediante
GestorIdiomas.t(clave) en lugar de escribirse directamente en pantalla, para
que el cambio de idioma desde Ajustes se refleje en todo el juego.
"""

IDIOMA_POR_DEFECTO = "es"
IDIOMAS_DISPONIBLES = ("es", "en", "pt")

NOMBRES_IDIOMAS = {
    "es": "Español",
    "en": "English",
    "pt": "Português",
}

TEXTOS = {
    "es": {
        # Menú principal
        "menu_nuevo_juego": "Nuevo Juego",
        "menu_continuar": "Continuar",
        "menu_continuar_noche": "Continuar - Noche {noche}",
        "menu_sin_partida": "Continuar - Sin partida",
        "menu_noche_6": "Noche 6",
        "menu_noche_personalizada": "Noche Personalizada",
        "menu_ajustes": "Ajustes",
        # Ajustes
        "ajustes_titulo": "Ajustes",
        "ajustes_idioma": "Idioma",
        "ajustes_pantalla_completa": "Pantalla Completa",
        "ajustes_resolucion": "Resolución",
        "ajustes_resolucion_ventana": "modo ventana",
        "ajustes_volumen_musica": "Volumen Música",
        "ajustes_volumen_efectos": "Volumen Efectos",
        "ajustes_modo_streamer": "Modo Streamer",
        "ajustes_volver": "Volver",
        "activado": "Activado",
        "desactivado": "Desactivado",
        # Noche personalizada
        "personalizada_titulo": "Noche Personalizada",
        "personalizada_iniciar": "Iniciar Noche",
        "personalizada_volver": "Volver",
        # Partida
        "hud_noche": "Noche {noche}",
        "hud_bateria": "BATERIA",
        "camara_solo_audio": "SOLO AUDIO - SIN VIDEO",
        "camara_sin_imagen": "SIN IMAGEN CARGADA",
        # Hub del jugador
        "posicion_barril": "Barril",
        "posicion_entrada": "Entrada",
        "posicion_lavaderos": "Lavaderos",
        "posicion_dentro_barril": "Dentro del Barril",
        "vista_sin_fondo": "SIN FONDO CARGADO: {posicion}",
        "linterna_agotada": "LINTERNA SIN BATERIA",
        "linterna_cambiar": "LINTERNA SIN BATERIA - R PARA CAMBIARLA",
        "objeto_recoger": "E - Recoger {objeto}",
        "objeto_bateria": "Batería",
        "objeto_paleta": "Paleta",
        "objeto_pelota_cuadrada": "Pelota cuadrada",
        "objeto_pelota_redonda": "Pelota redonda",
        "objeto_balero": "Balero",
        "objeto_chipote": "Chipote chillón",
        "objeto_churrumino": "Churrumino",
        "objeto_cafe": "Café",
        "objeto_cafe_churrumino": "Café con churrumino",
        # Arrojar objetos y reacciones
        "arrojo_elimina": "{objeto} se llevó a {nombre}.",
        "arrojo_retrasa": "{nombre} se entretuvo con el churrumino.",
        "arrojo_perdido": "Arrojaste {objeto} y no le sirvió a nadie.",
        "clotilde_pide": "Doña Clotilde busca: {objeto}",
        "cafe_preparado": "Preparaste el café con churrumino.",
        # Servicios del barril
        "tira_camaras": "CÁMARAS",
        "tira_servicios": "SERVICIOS",
        "camara_averiada": "CÁMARAS AVERIADAS - RESTABLÉCELAS",
        "servicio_ocupado": "Todavía estás ocupado con eso.",
        "servicio_sin_usos": "El audio de Quico se agotó: restablece todo.",
        "servicio_en_marcha": "Trabajando...",
        "servicio_ahuyentado": "Funcionó.",
        "ayuda_patio": "A/D - Caminar   S - Meterse al barril   Clic - Linterna   E - Recoger   1-7 - Arrojar   C - Combinar café   R - Cambiar batería",
        "ayuda_camaras": "Clic - Elegir cámara   ESPACIO - Bajar cámaras",
        "ayuda_servicios": "Clic - Usar servicio   TAB - Cerrar el tablero",
        # Fin de partida
        "game_over_titulo": "HAS SIDO ATRAPADO",
        "game_over_motivo": "{nombre} llegó hasta ti.",
        "game_over_luz": "Alumbraste a {nombre}.",
        "game_over_barriga": "Llamaste al Señor Barriga sin necesidad y vino a cobrar.",
        "victoria_titulo": "¡SOBREVIVISTE LA NOCHE!",
        "victoria_personalizada": "¡SOBREVIVISTE LA NOCHE PERSONALIZADA!",
        "ayuda_fin": "ENTER - Volver al menú   ESC - Salir",
    },
    "en": {
        "menu_nuevo_juego": "New Game",
        "menu_continuar": "Continue",
        "menu_continuar_noche": "Continue - Night {noche}",
        "menu_sin_partida": "Continue - No save",
        "menu_noche_6": "Night 6",
        "menu_noche_personalizada": "Custom Night",
        "menu_ajustes": "Settings",
        "ajustes_titulo": "Settings",
        "ajustes_idioma": "Language",
        "ajustes_pantalla_completa": "Fullscreen",
        "ajustes_resolucion": "Resolution",
        "ajustes_resolucion_ventana": "windowed mode",
        "ajustes_volumen_musica": "Music Volume",
        "ajustes_volumen_efectos": "SFX Volume",
        "ajustes_modo_streamer": "Streamer Mode",
        "ajustes_volver": "Back",
        "activado": "On",
        "desactivado": "Off",
        "personalizada_titulo": "Custom Night",
        "personalizada_iniciar": "Start Night",
        "personalizada_volver": "Back",
        "hud_noche": "Night {noche}",
        "hud_bateria": "BATTERY",
        "camara_solo_audio": "AUDIO ONLY - NO VIDEO",
        "camara_sin_imagen": "NO IMAGE LOADED",
        "posicion_barril": "Barrel",
        "posicion_entrada": "Entrance",
        "posicion_lavaderos": "Washbasins",
        "posicion_dentro_barril": "Inside the Barrel",
        "vista_sin_fondo": "NO BACKGROUND LOADED: {posicion}",
        "linterna_agotada": "FLASHLIGHT OUT OF BATTERY",
        "linterna_cambiar": "FLASHLIGHT DEAD - PRESS R TO SWAP BATTERY",
        "objeto_recoger": "E - Pick up {objeto}",
        "objeto_bateria": "Battery",
        "objeto_paleta": "Lollipop",
        "objeto_pelota_cuadrada": "Square ball",
        "objeto_pelota_redonda": "Round ball",
        "objeto_balero": "Cup-and-ball",
        "objeto_chipote": "Squeaky hammer",
        "objeto_churrumino": "Churrumino",
        "objeto_cafe": "Coffee",
        "objeto_cafe_churrumino": "Coffee with churrumino",
        "arrojo_elimina": "The {objeto} drove {nombre} off.",
        "arrojo_retrasa": "{nombre} got distracted by the churrumino.",
        "arrojo_perdido": "You threw the {objeto} and nobody cared.",
        "clotilde_pide": "Doña Clotilde is after: {objeto}",
        "cafe_preparado": "You brewed the coffee with churrumino.",
        "tira_camaras": "CAMERAS",
        "tira_servicios": "SERVICES",
        "camara_averiada": "CAMERAS DOWN - RESET THEM",
        "servicio_ocupado": "You are still busy with that.",
        "servicio_sin_usos": "Quico's audio ran out: reset everything.",
        "servicio_en_marcha": "Working...",
        "servicio_ahuyentado": "It worked.",
        "ayuda_patio": "A/D - Walk   S - Hide in barrel   Click - Flashlight   E - Pick up   1-7 - Throw   C - Brew coffee   R - Swap battery",
        "ayuda_camaras": "Click - Pick camera   SPACE - Lower cameras",
        "ayuda_servicios": "Click - Use service   TAB - Close the board",
        "game_over_titulo": "YOU WERE CAUGHT",
        "game_over_motivo": "{nombre} reached you.",
        "game_over_luz": "You shone the light on {nombre}.",
        "game_over_barriga": "You called Señor Barriga for nothing and he came to collect.",
        "victoria_titulo": "YOU SURVIVED THE NIGHT!",
        "victoria_personalizada": "YOU SURVIVED THE CUSTOM NIGHT!",
        "ayuda_fin": "ENTER - Back to menu   ESC - Quit",
    },
    "pt": {
        "menu_nuevo_juego": "Novo Jogo",
        "menu_continuar": "Continuar",
        "menu_continuar_noche": "Continuar - Noite {noche}",
        "menu_sin_partida": "Continuar - Sem jogo salvo",
        "menu_noche_6": "Noite 6",
        "menu_noche_personalizada": "Noite Personalizada",
        "menu_ajustes": "Configurações",
        "ajustes_titulo": "Configurações",
        "ajustes_idioma": "Idioma",
        "ajustes_pantalla_completa": "Tela Cheia",
        "ajustes_resolucion": "Resolução",
        "ajustes_resolucion_ventana": "modo janela",
        "ajustes_volumen_musica": "Volume da Música",
        "ajustes_volumen_efectos": "Volume dos Efeitos",
        "ajustes_modo_streamer": "Modo Streamer",
        "ajustes_volver": "Voltar",
        "activado": "Ativado",
        "desactivado": "Desativado",
        "personalizada_titulo": "Noite Personalizada",
        "personalizada_iniciar": "Iniciar Noite",
        "personalizada_volver": "Voltar",
        "hud_noche": "Noite {noche}",
        "hud_bateria": "BATERIA",
        "camara_solo_audio": "SOMENTE ÁUDIO - SEM VÍDEO",
        "camara_sin_imagen": "SEM IMAGEM CARREGADA",
        "posicion_barril": "Barril",
        "posicion_entrada": "Entrada",
        "posicion_lavaderos": "Lavanderia",
        "posicion_dentro_barril": "Dentro do Barril",
        "vista_sin_fondo": "SEM FUNDO CARREGADO: {posicion}",
        "linterna_agotada": "LANTERNA SEM BATERIA",
        "linterna_cambiar": "LANTERNA SEM BATERIA - R PARA TROCAR",
        "objeto_recoger": "E - Pegar {objeto}",
        "objeto_bateria": "Bateria",
        "objeto_paleta": "Pirulito",
        "objeto_pelota_cuadrada": "Bola quadrada",
        "objeto_pelota_redonda": "Bola redonda",
        "objeto_balero": "Bilboquê",
        "objeto_chipote": "Martelinho",
        "objeto_churrumino": "Churrumino",
        "objeto_cafe": "Café",
        "objeto_cafe_churrumino": "Café com churrumino",
        "arrojo_elimina": "{objeto} tirou {nombre} de cena.",
        "arrojo_retrasa": "{nombre} se distraiu com o churrumino.",
        "arrojo_perdido": "Você jogou {objeto} e não serviu para ninguém.",
        "clotilde_pide": "Dona Clotilde procura: {objeto}",
        "cafe_preparado": "Você preparou o café com churrumino.",
        "tira_camaras": "CÂMERAS",
        "tira_servicios": "SERVIÇOS",
        "camara_averiada": "CÂMERAS QUEBRADAS - RESTABELEÇA",
        "servicio_ocupado": "Você ainda está ocupado com isso.",
        "servicio_sin_usos": "O áudio do Quico acabou: restabeleça tudo.",
        "servicio_en_marcha": "Trabalhando...",
        "servicio_ahuyentado": "Funcionou.",
        "ayuda_patio": "A/D - Andar   S - Entrar no barril   Clique - Lanterna   E - Pegar   1-7 - Jogar   C - Preparar café   R - Trocar bateria",
        "ayuda_camaras": "Clique - Escolher câmera   ESPAÇO - Baixar câmeras",
        "ayuda_servicios": "Clique - Usar serviço   TAB - Fechar o painel",
        "game_over_titulo": "VOCÊ FOI PEGO",
        "game_over_motivo": "{nombre} chegou até você.",
        "game_over_luz": "Você iluminou {nombre}.",
        "game_over_barriga": "Você chamou o Senhor Barriga à toa e ele veio cobrar.",
        "victoria_titulo": "VOCÊ SOBREVIVEU À NOITE!",
        "victoria_personalizada": "VOCÊ SOBREVIVEU À NOITE PERSONALIZADA!",
        "ayuda_fin": "ENTER - Voltar ao menu   ESC - Sair",
    },
}


class GestorIdiomas:
    """Traduce claves de texto al idioma activo."""

    def __init__(self, idioma: str = IDIOMA_POR_DEFECTO):
        self.idioma = idioma if idioma in IDIOMAS_DISPONIBLES else IDIOMA_POR_DEFECTO

    def cambiar(self, idioma: str):
        if idioma in IDIOMAS_DISPONIBLES:
            self.idioma = idioma

    def siguiente_idioma(self) -> str:
        indice = IDIOMAS_DISPONIBLES.index(self.idioma)
        self.idioma = IDIOMAS_DISPONIBLES[(indice + 1) % len(IDIOMAS_DISPONIBLES)]
        return self.idioma

    def nombre_idioma_actual(self) -> str:
        return NOMBRES_IDIOMAS[self.idioma]

    def t(self, clave: str, **formato) -> str:
        """Devuelve el texto traducido. Si falta en el idioma activo cae al
        español, y si tampoco existe devuelve la clave entre corchetes para
        que el faltante sea evidente en pantalla."""
        texto = TEXTOS[self.idioma].get(clave)
        if texto is None:
            texto = TEXTOS[IDIOMA_POR_DEFECTO].get(clave)
        if texto is None:
            return f"[{clave}]"
        return texto.format(**formato) if formato else texto
