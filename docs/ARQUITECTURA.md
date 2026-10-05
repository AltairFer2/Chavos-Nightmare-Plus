# Arquitectura

El código está organizado en **capas**. Cada capa solo puede importar de las
que tiene por debajo, nunca de las de arriba ni de sus hermanas por encima.

```
┌─────────────────────────────────────────────────────────┐
│  app              bucle principal, estados, entrada     │
├─────────────────────────────────────────────────────────┤
│  presentacion     todo lo que se dibuja        [pygame] │
├─────────────────────────────────────────────────────────┤
│  infraestructura  disco, audio, ventana        [pygame] │
├─────────────────────────────────────────────────────────┤
│  dominio          LAS REGLAS DEL JUEGO       [sin pygame]│
├─────────────────────────────────────────────────────────┤
│  mundo            el mapa: habitaciones y posiciones    │
│  i18n             textos en es / en / pt                │
├─────────────────────────────────────────────────────────┤
│  config           constantes; no depende de nada        │
└─────────────────────────────────────────────────────────┘
```

## La regla que sostiene todo lo demás

> **En `dominio/` no se importa pygame.**

De ahí salen las demás ventajas:

- Las mecánicas se pueden probar **sin abrir una ventana**: la suite corre
  entera en menos de un segundo y funcionaría igual en un servidor sin
  pantalla.
- Queda separado **qué pasa** (dominio) de **cómo se ve** (presentación). Si
  mañana el juego cambiara de motor gráfico, `dominio/` no se toca.
- Obliga a decidir dónde va cada cosa. El sabotaje de las cámaras, por
  ejemplo, vivía dentro del renderer aunque es una regla de juego: ahora está
  en `dominio/sabotaje.py` y el panel solo le informa de si El Chavo está a la
  vista.

`tests/test_arquitectura.py` comprueba esto automáticamente, junto con el
resto de dependencias permitidas entre capas. Si alguien las rompe, falla una
prueba en vez de descubrirse meses después.

## Qué hay en cada capa

### `config/` — constantes

No depende de nada, ni siquiera de pygame. Partido por área para que se vea
de dónde viene cada número:

| Módulo | Qué contiene |
|---|---|
| `ventana.py` | Lienzo base, resoluciones, FPS, título |
| `rutas.py` | Dónde están assets, sonidos y los datos del jugador |
| `audio.py` | Carpetas de audio, mapa de pistas, volúmenes |
| `partida.py` | Reloj de la noche, ticks de IA, progresión de noches |
| `jugabilidad.py` | **Equilibrio**: linterna, objetos, servicios, sabotaje |
| `interfaz.py` | Colores, tipografía, distribución de la interfaz |

Para equilibrar el juego se toca `jugabilidad.py`; para mover algo en
pantalla, `interfaz.py`.

### `mundo/` — el mapa

Dos sistemas de lugares distintos, a propósito:

- **`habitaciones.py`**: el grafo de cámaras de la vecindad, por donde se
  mueven los animatrónicos.
- **`posiciones.py`**: los cuatro sitios del Primer Patio por los que camina
  el jugador (Lavaderos, Barril, Entrada y dentro del barril).

El jugador no recorre la vecindad entera, solo su rincón; los animatrónicos no
se paran en sus posiciones, llegan a acecharlo desde ellas.

### `i18n/` — textos

`textos/` tiene un archivo por idioma con un diccionario `TEXTOS`. Para añadir
un idioma basta con crear su módulo y registrarlo en `textos/__init__.py`.
`GestorIdiomas.t(clave)` resuelve al idioma activo y cae al español si falta
la clave.

### `dominio/` — las reglas

El corazón del juego. Sin pygame, sin disco, sin pantalla.

```
dominio/
├── animatronicos/
│   ├── nombres.py        el nombre de cada personaje, sin dependencias
│   ├── definicion.py     la ficha fija de un personaje
│   ├── entidad.py        su estado vivo y la IA 0-20
│   ├── elenco.py         las siete fichas concretas + validación
│   ├── progresion.py     qué nivel tiene cada uno en cada noche
│   └── enfrentamiento.py cara a cara: luz mortal y a quién le da un objeto
├── jugador.py            por dónde se mueve dentro del hub
├── linterna.py           batería y haz de luz
├── inventario.py         lo que carga encima y el café
├── objetos.py            catálogo y el sitio fijo de cada objeto en el suelo
├── arrojo.py             el objeto arrojado mientras va por el aire
├── servicios.py          los cuatro servicios del barril
├── sabotaje.py           El Chavo arruinando las cámaras
├── interferencia.py      cámaras sin señal al moverse alguien delante
└── temporizador.py       el reloj y los ticks que mueven al elenco
```

**Sistema de IA (estilo FNAF).** Cada hora in-game se divide en
`TICKS_POR_HORA` intentos de movimiento. En cada tick, todo animatrónico
activo tira `random.randint(1, 20)` y avanza una etapa de su recorrido si sale
menor o igual a su `nivel_ia`. Nivel 0 = nunca se mueve; nivel 20 = avanza
siempre.

**Recorridos.** El recorrido de cada personaje es una lista de etapas, y cada
etapa es el conjunto de habitaciones posibles para ese paso. Una etapa con
varias habitaciones es un tramo impredecible. La última etapa siempre es el
Primer Patio: al llegar, el personaje deja de moverse y acecha.

Los recorridos son autorales: describen el camino que hace el personaje, no la
geometría de la vecindad. Por eso no se derivan del grafo de `habitaciones.py`.

`elenco.py` se valida al importarse: si un recorrido apunta a una habitación
que no existe o falta un sprite, falla en el arranque y no a mitad de partida.

### `infraestructura/` — el mundo exterior

Aísla al resto del juego de que falte un archivo, no haya tarjeta de sonido o
el monitor tenga otra resolución. **Cuando algo no está, devuelve `None` o se
queda en silencio en vez de reventar**, para que se pueda seguir jugando
mientras el arte está en producción.

| Módulo | Qué resuelve |
|---|---|
| `recursos.py` | Carga de imágenes con caché; escalado una sola vez |
| `fuentes.py` | Tipografías con caché, del archivo o del sistema |
| `audio.py` | Música y efectos; resuelve el modo streamer |
| `pantalla.py` | Ventana, escalado del lienzo, coordenadas del ratón |
| `guardado.py` | Progreso y preferencias en JSON, con saneado |

**El lienzo fijo.** Todo se dibuja sobre una superficie de 1280x720 que se
escala a la ventana al presentar el fotograma. Así las posiciones de la
interfaz se calculan una sola vez y valen para cualquier resolución.

### `presentacion/` — lo que se ve

Lee el estado del dominio y lo pinta. Nunca decide reglas.

```
presentacion/
├── menu/                 menú principal, ajustes, pausa y noche personalizada
│   ├── modelo.py         SolicitudNoche, EntradaMenu, secciones
│   ├── secciones.py      qué opciones muestra cada sección
│   ├── ajustes.py        ControlAjustes: qué hace cada opción de Ajustes
│   ├── deslizador.py     las barras de volumen
│   ├── fondo.py          fondo animado y logotipo
│   ├── principal.py      MenuPrincipal, que junta lo anterior
│   └── pausa.py          MenuPausa, con los mismos Ajustes que el principal
├── camaras.py            el monitor a pantalla completa
├── animacion_monitor.py  el monitor entrando y saliendo de la vista
├── mapa_camaras.py       el mapa que hace de selector de cámara
├── vista.py              lo que el jugador ve, con la linterna
├── hud.py                noche, hora, batería, inventario, finales
├── panel_servicios.py    el tablero del barril
├── inicio_noche.py       el periódico y la tarjeta de "Noche N - 12:00 AM"
├── noche_superada.py     el reloj de las 6:00 y el menú de continuar
├── iconos.py             iconos recortados de su hoja
└── efectos.py            estática y líneas de barrido, precalculadas

```

**Rendimiento.** El ruido de estática, las líneas de barrido y el degradado
del haz se calculan **una sola vez al iniciar** y después solo se blitean.
Trabajar píxel a píxel en cada fotograma sería inviable a 60 FPS.

### `app/` — el pegamento

La única capa que conoce a todas las demás. Coordina, no decide.

| Módulo | Qué hace |
|---|---|
| `juego.py` | Compone las piezas y corre el bucle |
| `estados.py` | Menú, jugando, game over, victoria |
| `noche.py` | Estado de la noche en curso y cómo terminó |
| `entrada.py` | Qué tecla hace qué |
| `aviso.py` | El mensaje corto que aparece y se borra solo |

**El menú no arranca partidas.** Cuando el jugador elige una noche, el menú
deja una `SolicitudNoche` que `app` consume. Así el menú no necesita conocer
la clase `Juego`, y se evita la dependencia circular.

## Decisiones y por qué

**Los nombres de los personajes están en `nombres.py`.** Varios sitios
necesitan referirse a un personaje concreto: el objeto que ahuyenta a Quico,
el servicio que se lleva a Don Ramón, quién sabotea las cámaras. Antes eran
literales repartidos por cuatro archivos, donde una tilde mal puesta rompía
una mecánica en silencio. El módulo no importa nada, así que cualquiera puede
usarlo sin arrastrar el elenco (que al cargarse valida sprites en disco).

**`config/` es capa 0 y la puede importar cualquiera.** Es una capa de datos,
no de comportamiento. El dominio importa de `config/jugabilidad.py` (números
de equilibrio) pero nunca de `config/interfaz.py`: cuando necesitó la altura
del torso para medir la linterna, se definió `ALTURA_TORSO` en `jugabilidad`
derivándola del alto de la figura, en vez de que el dominio leyera una
constante de dibujo.

**Los datos del jugador viven fuera del proyecto.** En
`%APPDATA%/LaVecindadDelChavo/`, y en dos archivos separados: borrar el
progreso no debe hacer perder también las preferencias.

**`config/rutas.py` consulta `sys._MEIPASS`.** Es lo que permite que el mismo
código encuentre los assets corriendo desde el código fuente y desde el .exe
empaquetado.

## Cómo añadir cosas

| Quiero... | Dónde |
|---|---|
| Un personaje nuevo | Añadir su nombre a `nombres.py`, su ficha a `elenco.py` y sus niveles a `progresion.py` |
| Una cámara nueva | `mundo/habitaciones.py` + su carpeta en `assets/camaras/` + su recuadro en `presentacion/mapa_camaras.py` |
| Un objeto nuevo | `dominio/objetos.py` (catálogo, a quién elimina y su `punto_suelo`) + su celda en la hoja de iconos |
| Un idioma nuevo | Un módulo en `i18n/textos/` y registrarlo en su `__init__.py` |
| Cambiar los controles | `app/entrada.py`, y solo ahí |
| Equilibrar la dificultad | `config/jugabilidad.py` y `dominio/animatronicos/progresion.py` |

Al añadir una carpeta de capa nueva hay que declararla en
`tests/test_arquitectura.py`; hay una prueba que lo exige, para que ninguna
capa quede fuera de la comprobación sin que nadie se entere.
