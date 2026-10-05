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
| **Linterna** | Único recurso limitado de la noche. Ilumina un círculo alrededor del cursor; fuera de él no se ve nada. Las baterías de repuesto se buscan a oscuras. |
| **Luz mortal** | A Don Ramón, Doña Florinda y La Chilindrina **no se les puede alumbrar de cerca**. Cuanto más alto su nivel, más lejos es fatal el haz. |
| **Objetos** | Seis objetos defensivos, además del café y la batería. Cada uno tiene su sitio fijo en los Lavaderos: la noche empieza con todos puestos y, al recogerlo, vuelve a su sitio tras un tiempo fijo (más largo cuanto más avanzada la campaña). No se lleva más de uno de cada a la vez. |
| **Puntería** | El objeto se arroja hacia el cursor y solo sirve si le da al vecino que corresponde. Cuanto más alto su nivel, más fino hay que apuntar. Fallar o darle a quien no era lo gasta igual. |
| **Café con churrumino** | Lo único que calma a Jaimico. Se prepara combinando café y churrumino, pero el churrumino suelto también entretiene a El Chavo: la decisión es del jugador. |
| **Cámaras** | Solo se abren desde dentro del barril, y el monitor tarda un momento en bajar. Mirar a El Chavo demasiado rato seguido hace que arruine todas las cámaras. |
| **Interferencia** | Si alguien se mueve justo mientras se le está mirando, esa cámara se cae unos segundos: se oye que se fue, pero no se ve hacia dónde. |
| **Servicios del barril** | Llamar al Sr. Barriga (lo único que quita a Don Ramón, pero llamarlo sin necesidad es mortal), el audio de Quico, restablecer cámaras y restablecer todo. |
| **Doña Clotilde** | Al llegar reclama uno de los seis objetos al azar. Si no se tiene, hay que salir a buscarlo. |

**Progresión:** noches 1 a 5 de campaña, la 6 se desbloquea al terminar la 5,
y la Noche Personalizada (nivel de IA 0-20 por personaje) al terminar la 6.

## Controles

| Tecla | Acción |
|---|---|
| `A` / `D` o `←` / `→` | Caminar entre Lavaderos, Barril y Entrada |
| `S` / `↓` | Meterse al barril |
| `W` / `↑` | Asomarse |
| Clic | Encender y apagar la linterna |
| `E` | Recoger el objeto que se tenga iluminado |
| `1`-`7` | Arrojar el objeto de esa ranura hacia el cursor |
| `C` | Combinar café con churrumino |
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
