"""Reglas de la noche: reloj, ticks de IA y progresión de la campaña."""

# --- Noche / temporizador ---
HORA_INICIO_NOCHE = 0  # 12:00 am
HORA_FIN_NOCHE = 6  # 6:00 am
DURACION_NOCHE_SEGUNDOS = 540   # duración real de una noche completa (9 min)
HORAS_DE_NOCHE = (HORA_FIN_NOCHE - HORA_INICIO_NOCHE) % 12 or 12
SEGUNDOS_POR_HORA_NOCHE = DURACION_NOCHE_SEGUNDOS / HORAS_DE_NOCHE

# Cada cuántos segundos reales se abre una ronda de movimiento: en cada ronda,
# todo animatrónico activo tira su dado y decide si avanza una etapa. Es la
# palanca de ritmo de la noche, y cada noche tiene el suyo (ver
# dominio/animatronicos/progresion.py). Este valor solo se usa cuando no se
# indica ninguno, como en la Noche Personalizada.
#
# Cuidado al tocarlo: el intervalo y el nivel de IA se multiplican. Acortar el
# intervalo a la mitad tiene el mismo efecto que duplicar el nivel de todos, y
# eso se nota mucho más en las noches con el elenco completo.
INTERVALO_MOVIMIENTO_POR_DEFECTO = 20.0

# --- Progresión de noches ---
NOCHES_HISTORIA = 5  # noches 1 a 5: campaña principal
NOCHE_EXTRA = 6  # se desbloquea al completar la noche 5
ULTIMA_NOCHE = NOCHE_EXTRA

# --- Inteligencia artificial de los animatrónicos ---
# Escala estilo FNAF: en cada tick se tira random.randint(1, 20) y el
# animatrónico avanza si el resultado es menor o igual a su nivel_ia.
# Nivel 0 = nunca se mueve; nivel 20 = se mueve en todos los ticks.
NIVEL_IA_MINIMO = 0
NIVEL_IA_MAXIMO = 20
