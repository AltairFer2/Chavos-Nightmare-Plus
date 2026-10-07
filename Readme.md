# Chaves Nightmare Plus +

Survival horror de vigilancia nocturna ambientado en la vecindad de El Chavo
del Ocho. El jugador pasa la noche escondido junto al barril del Primer
Patio: aguanta de las 12 a las 6 de la mañana vigilando las cámaras,
racionando la batería de la linterna y respondiendo a cada vecino con el
objeto que le corresponde.

Hecho en Python con pygame.

## Cómo se juega

Cada vecino sale de su casa y avanza por su propio recorrido hasta llegar al
Primer Patio. Cuando uno llega, se planta delante del jugador y empieza una
cuenta atrás: hay unos segundos para reaccionar antes de que ataque.

| Mecánica | En qué consiste |
|---|---|
| **Linterna** | Único recurso limitado de la noche, y también el arma. Ilumina un círculo alrededor del cursor; fuera de él no se ve nada. |
| **Luz mortal** | A Don Ramón y Doña Florinda **no se les puede alumbrar de cerca**: se van con el Sr. Barriga y con el audio de Quico. Cuanto más alto su nivel, más lejos es fatal el haz. |
| **Espantar con la luz** | A Quico, La Chilindrina, El Chavo, Jaimico y Doña Clotilde se les ve un **punto débil** que se mueve a tirones por el cuerpo. Hay que sostener el centro del haz encima hasta llenar su barra; perderlo la va vaciando. Cuanto más alto su nivel, más chico, rápido y nervioso es el punto, y más rato hay que sostenerlo. A La Chilindrina, alumbrarle el cuerpo fuera del punto más de un momento le descarga la batería al jugador. |
| **Baterías** | Lo único que se encuentra tirado: una a la vez, siempre en el mismo sitio de los Lavaderos y con tiempos fijos por noche (sin sorteo). Si nadie la recoge, parpadea y se va. Caben dos de repuesto en el bolsillo. |
| **Cámaras** | Solo se abren desde dentro del barril, y el monitor tarda un momento en bajar. Mirar a El Chavo 2 s (noches 3-4) o 1 s (el resto) hace que arruine todas las cámaras; los vistazos cortos se van sumando y el monitor falla cuando está a punto. Mientras está en pantalla la imagen tiembla y el mapa se mueve a saltos, botones incluidos, así que salir de su cámara cuesta. Al romperlas, **El Chavo aparece de golpe en el patio** y hay que enfrentarlo. |
| **Interferencia** | Si alguien entra o sale de la cámara que se está mirando, esa cámara se cae unos segundos: se oye que alguien se movió, pero no se ve quién ni hacia dónde. Cuando Doña Florinda se mueve, la cámara que se esté mirando da un tirón, sea cual sea. |
| **Audio de Quico** | Suena en la cámara que se está mirando (se ven ondas en ella) y Doña Florinda va hacia allá **solo si es vecina de la suya**: puesto detrás la aleja, puesto delante la acerca. Desde la reja ya no hace caso. Hay 3 s de espera entre usos. |
| **Apariciones raras** | De vez en cuando (1 entre 10 000 por segundo en la noche 1, hasta 1 entre 5 000 en la 5 y la 6) se cuela una imagen casi transparente con su sonido. No afecta al juego. |
| **Servicios del barril** | Llamar al Sr. Barriga (lo único que quita a Don Ramón, pero llamarlo sin necesidad es mortal), el audio de Quico, restablecer cámaras y restablecer todo. Mientras uno trabaja no se puede bajar el tablero, cambiar a las cámaras ni asomarse. |

**Progresión:** noches 1 a 5 de campaña, la 6 se desbloquea al terminar la 5,
y la Noche Personalizada (nivel de IA 0-20 por personaje) al terminar la 6.

## Controles

| Tecla | Acción |
|---|---|
| `A` / `D` o `←` / `→` | Caminar entre Lavaderos, Barril y Entrada |
| `S` / `↓` | Meterse al barril |
| `W` / `↑` | Asomarse |
| Clic | Encender y apagar la linterna (sostener el cursor sobre el punto débil espanta) |
| `E` | Recoger la batería que se tenga iluminada |
| `R` | Cambiar la batería de la linterna |
| `ESPACIO` | Subir y bajar las cámaras (solo dentro del barril) |
| `TAB` | Abrir el tablero de servicios (solo dentro del barril) |
| `ESC` | Salir |

También se pueden levantar las cámaras y el tablero pasando el ratón por las
pestañas de la parte de abajo.

## Instalación y arranque

Requiere **Python 3.10 o superior**.

```bash
pip install -r requirements.txt
python run.py
```

O instalando el paquete, que además deja el comando `vecindad`:

```bash
pip install -e .
vecindad
```

Las tres formas de arrancar hacen lo mismo:

```bash
python run.py          # sin instalar nada
python -m vecindad     # como módulo
vecindad               # comando instalado
```

## Pruebas

```bash
pip install -e ".[dev]"
pytest
```

Las pruebas cubren la capa de dominio, que no usa pygame, así que corren sin
abrir ninguna ventana. `tests/test_arquitectura.py` comprueba además que las
capas siguen respetando sus dependencias.

## Generar el .exe

```bash
pip install pyinstaller pillow
pyinstaller vecindad.spec
```

Pillow hace falta para que PyInstaller convierta el logo de
`assets/logo/` en el icono del .exe.

El ejecutable queda en `dist/`. Los assets y sonidos se empaquetan dentro; el
progreso y las preferencias del jugador se guardan aparte, en
`%APPDATA%/LaVecindadDelChavo/`, para que sobrevivan a una reinstalación.

## Estructura

```
src/vecindad/       código, organizado en capas (ver docs/ARQUITECTURA.md)
assets/             arte: cámaras, animatrónicos, interfaz y menú
sonidos/            audio, en dos árboles: con_copyright/ y sin_copyright/
tests/              pruebas de la lógica de juego
docs/               documentación de arquitectura
```

El **modo streamer** de Ajustes cambia de qué árbol de `sonidos/` se lee todo
el audio, para poder transmitir sin música con derechos.

## Añadir contenido

| Quiero... | Dónde se toca |
|---|---|
| Cambiar la dificultad de una noche | `src/vecindad/dominio/animatronicos/progresion.py` |
| Cambiar el recorrido de un personaje | `src/vecindad/dominio/animatronicos/elenco.py` |
| Equilibrar linterna, objetos o servicios | `src/vecindad/config/jugabilidad.py` |
| Mover algo de la interfaz o cambiar colores | `src/vecindad/config/interfaz.py` |
| Traducir o corregir un texto | `src/vecindad/i18n/textos/` |
| Añadir una cámara | `src/vecindad/mundo/habitaciones.py` |
| Añadir un objeto | `src/vecindad/dominio/objetos.py` |
| Cambiar los controles | `src/vecindad/app/entrada.py` |

Los assets se generan con herramientas externas; el código solo los carga. Si
un archivo todavía no existe, la pantalla que lo necesita dibuja un respaldo
y el juego sigue corriendo.
