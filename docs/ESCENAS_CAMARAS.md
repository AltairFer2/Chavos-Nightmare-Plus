# Escenas de cámara pendientes

Cada cámara muestra una imagen distinta según quién esté dentro. Este
documento lista qué archivos faltan por dibujar.

> Generado con `python tools/escenas_pendientes.py`. No editar a mano.

## Cómo se nombran

Dentro de la carpeta de cada cámara, junto a `cam N.png`:

- Los nombres cortos, separados por espacios y el último con ` y `:
  `ramon y chavo.png`, `ramon chilindrina y chavo.png`.
- **El orden da igual**: `quico y chavo.png` y `chavo y quico.png` son
  lo mismo. Las tildes, las mayúsculas y las comas tampoco importan,
  así que `florinda, chavo y ramón.png` también vale.
- `todos.png` es el atajo para la escena con los siete dentro.
- Para varias versiones del mismo grupo, sufijo numérico:
  `ramon y chilindrina 2.png`. Se elige una al azar y se mantiene
  mientras ese grupo no cambie.
- `cam N.png` es la habitación vacía, y es lo que se ve sin nadie dentro.

Nombres cortos válidos:

- **ramon** — Don Ramón
- **quico** — Quico
- **chilindrina** — La Chilindrina
- **florinda** — Doña Florinda
- **chavo** — El Chavo
- **jaimico** — Jaimico
- **clotilde** — Doña Clotilde

- **bruja** — otra forma de escribir `clotilde`
- **jaimito** — otra forma de escribir `jaimico`

## No hace falta dibujarlas todas

Si falta la imagen exacta de un grupo, el juego usa la del subconjunto
más grande que sí exista, y si no hay ninguna, la habitación vacía.
Nunca enseña a alguien que no esté: como mucho, enseña de menos. Por
eso conviene empezar por los personajes solos y seguir por las parejas.


## Paso 1: personajes solos y en pareja

**26 archivos.**

Con esto el juego se ve bien en casi todo momento: los grupos de tres
o más caen a la pareja que sí exista.

### Entrada

`assets/camaras/Cámara 3 - Entrada/` — 2 archivos

```
florinda y chavo.png
ramon y quico.png
```

### Primer Patio

`assets/camaras/Cámara 1 - Primer Patio/` — 8 archivos

```
clotilde.png
chavo y clotilde.png
chilindrina y clotilde.png
chilindrina y jaimico.png
quico y chilindrina.png
jaimico y clotilde.png
quico y clotilde.png
ramon y clotilde.png
```

### Casa de Jaimito el Cartero

`assets/camaras/Cámara 23 - Casa de Jaimito el Cartero/` — 1 archivos

```
quico y chavo.png
```

### Casa de Doña Florinda

`assets/camaras/Cámara 14 - Casa de Doña Florinda/` — 2 archivos

```
chavo.png
florinda.png
```

### Casa de Don Ramón

`assets/camaras/Cámara 72 - Casa de Don Ramón/` — 1 archivos

```
chavo.png
```

### Segundo Patio

`assets/camaras/Cámara 2 - Segundo Patio/` — 12 archivos

```
chavo y clotilde.png
florinda y chavo.png
chavo y jaimico.png
ramon y chavo.png
chilindrina y florinda.png
chilindrina y jaimico.png
quico y chilindrina.png
quico y clotilde.png
ramon y clotilde.png
quico y florinda.png
quico y jaimico.png
ramon y jaimico.png
```


## Paso 2: grupos de tres o más

**141 archivos.**

Opcional, y solo si se quiere que los cruces grandes se vean exactos.

### Entrada

`assets/camaras/Cámara 3 - Entrada/` — 3 archivos

```
ramon florinda y chavo.png
ramon quico y chavo.png
ramon quico y florinda.png
```

### Primer Patio

`assets/camaras/Cámara 1 - Primer Patio/` — 40 archivos

```
chilindrina chavo y clotilde.png
chilindrina chavo y jaimico.png
quico chilindrina y chavo.png
chavo jaimico y clotilde.png
quico chavo y clotilde.png
ramon chavo y clotilde.png
quico chavo y jaimico.png
ramon chavo y jaimico.png
ramon quico y chavo.png
chilindrina jaimico y clotilde.png
quico chilindrina y clotilde.png
ramon chilindrina y clotilde.png
quico chilindrina y jaimico.png
ramon chilindrina y jaimico.png
ramon quico y chilindrina.png
quico jaimico y clotilde.png
ramon jaimico y clotilde.png
ramon quico y clotilde.png
chilindrina chavo jaimico y clotilde.png
quico chilindrina chavo y clotilde.png
ramon chilindrina chavo y clotilde.png
quico chilindrina chavo y jaimico.png
ramon chilindrina chavo y jaimico.png
ramon quico chilindrina y chavo.png
quico chavo jaimico y clotilde.png
ramon chavo jaimico y clotilde.png
ramon quico chavo y clotilde.png
ramon quico chavo y jaimico.png
quico chilindrina jaimico y clotilde.png
ramon chilindrina jaimico y clotilde.png
ramon quico chilindrina y clotilde.png
ramon quico chilindrina y jaimico.png
ramon quico jaimico y clotilde.png
quico chilindrina chavo jaimico y clotilde.png
ramon chilindrina chavo jaimico y clotilde.png
ramon quico chilindrina chavo y clotilde.png
ramon quico chilindrina chavo y jaimico.png
ramon quico chavo jaimico y clotilde.png
ramon quico chilindrina jaimico y clotilde.png
ramon quico chilindrina chavo jaimico y clotilde.png
```

### Casa de Jaimito el Cartero

`assets/camaras/Cámara 23 - Casa de Jaimito el Cartero/` — 4 archivos

```
chilindrina chavo y jaimico.png
quico chilindrina y chavo.png
quico chavo y jaimico.png
quico chilindrina y jaimico.png
```

### Segundo Patio

`assets/camaras/Cámara 2 - Segundo Patio/` — 94 archivos

```
chilindrina chavo y clotilde.png
chilindrina florinda y chavo.png
chilindrina chavo y jaimico.png
quico chilindrina y chavo.png
florinda chavo y clotilde.png
chavo jaimico y clotilde.png
quico chavo y clotilde.png
ramon chavo y clotilde.png
florinda chavo y jaimico.png
quico florinda y chavo.png
ramon florinda y chavo.png
quico chavo y jaimico.png
ramon chavo y jaimico.png
chilindrina florinda y clotilde.png
chilindrina jaimico y clotilde.png
quico chilindrina y clotilde.png
ramon chilindrina y clotilde.png
chilindrina florinda y jaimico.png
quico chilindrina y florinda.png
ramon chilindrina y florinda.png
quico chilindrina y jaimico.png
ramon chilindrina y jaimico.png
ramon quico y chilindrina.png
quico florinda y clotilde.png
ramon florinda y clotilde.png
quico jaimico y clotilde.png
ramon jaimico y clotilde.png
ramon quico y clotilde.png
quico florinda y jaimico.png
ramon florinda y jaimico.png
ramon quico y florinda.png
ramon quico y jaimico.png
chilindrina florinda chavo y clotilde.png
chilindrina chavo jaimico y clotilde.png
quico chilindrina chavo y clotilde.png
ramon chilindrina chavo y clotilde.png
chilindrina florinda chavo y jaimico.png
quico chilindrina florinda y chavo.png
ramon chilindrina florinda y chavo.png
quico chilindrina chavo y jaimico.png
ramon chilindrina chavo y jaimico.png
ramon quico chilindrina y chavo.png
florinda chavo jaimico y clotilde.png
quico florinda chavo y clotilde.png
ramon florinda chavo y clotilde.png
quico chavo jaimico y clotilde.png
ramon chavo jaimico y clotilde.png
ramon quico chavo y clotilde.png
quico florinda chavo y jaimico.png
ramon florinda chavo y jaimico.png
ramon quico florinda y chavo.png
ramon quico chavo y jaimico.png
chilindrina florinda jaimico y clotilde.png
quico chilindrina florinda y clotilde.png
ramon chilindrina florinda y clotilde.png
quico chilindrina jaimico y clotilde.png
ramon chilindrina jaimico y clotilde.png
ramon quico chilindrina y clotilde.png
quico chilindrina florinda y jaimico.png
ramon chilindrina florinda y jaimico.png
ramon quico chilindrina y florinda.png
ramon quico chilindrina y jaimico.png
quico florinda jaimico y clotilde.png
ramon florinda jaimico y clotilde.png
ramon quico florinda y clotilde.png
ramon quico jaimico y clotilde.png
ramon quico florinda y jaimico.png
chilindrina florinda chavo jaimico y clotilde.png
quico chilindrina florinda chavo y clotilde.png
ramon chilindrina florinda chavo y clotilde.png
quico chilindrina chavo jaimico y clotilde.png
ramon chilindrina chavo jaimico y clotilde.png
ramon quico chilindrina chavo y clotilde.png
quico chilindrina florinda chavo y jaimico.png
ramon chilindrina florinda chavo y jaimico.png
ramon quico chilindrina chavo y jaimico.png
quico florinda chavo jaimico y clotilde.png
ramon florinda chavo jaimico y clotilde.png
ramon quico florinda chavo y clotilde.png
ramon quico chavo jaimico y clotilde.png
ramon quico florinda chavo y jaimico.png
quico chilindrina florinda jaimico y clotilde.png
ramon chilindrina florinda jaimico y clotilde.png
ramon quico chilindrina florinda y clotilde.png
ramon quico chilindrina jaimico y clotilde.png
ramon quico chilindrina florinda y jaimico.png
ramon quico florinda jaimico y clotilde.png
quico chilindrina florinda chavo jaimico y clotilde.png
ramon chilindrina florinda chavo jaimico y clotilde.png
ramon quico chilindrina florinda chavo y clotilde.png
ramon quico chilindrina chavo jaimico y clotilde.png
ramon quico chilindrina florinda chavo y jaimico.png
ramon quico florinda chavo jaimico y clotilde.png
ramon quico chilindrina florinda jaimico y clotilde.png
```
