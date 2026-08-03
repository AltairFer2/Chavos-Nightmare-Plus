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
        "hud_energia": "ENERGIA",
        "hud_noche": "Noche {noche}",
        "camara_solo_audio": "SOLO AUDIO - SIN VIDEO",
        "camara_sin_imagen": "SIN IMAGEN CARGADA",
        # Fin de partida
        "game_over_titulo": "HAS SIDO ATRAPADO",
        "game_over_motivo": "{nombre} llegó hasta ti.",
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
        "hud_energia": "POWER",
        "hud_noche": "Night {noche}",
        "camara_solo_audio": "AUDIO ONLY - NO VIDEO",
        "camara_sin_imagen": "NO IMAGE LOADED",
        "game_over_titulo": "YOU WERE CAUGHT",
        "game_over_motivo": "{nombre} reached you.",
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
        "hud_energia": "ENERGIA",
        "hud_noche": "Noite {noche}",
        "camara_solo_audio": "SOMENTE ÁUDIO - SEM VÍDEO",
        "camara_sin_imagen": "SEM IMAGEM CARREGADA",
        "game_over_titulo": "VOCÊ FOI PEGO",
        "game_over_motivo": "{nombre} chegou até você.",
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
