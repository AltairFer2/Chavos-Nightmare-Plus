"""Chaves Nightmare Plus + : un survival horror de vigilancia nocturna
ambientado en la vecindad de El Chavo del Ocho.

El paquete está organizado en capas, y cada una solo puede importar de las
que tiene por debajo:

    app             bucle principal, estados y entrada
     ├── presentacion   todo lo que se dibuja (pygame)
     ├── infraestructura disco, audio y ventana (pygame)
     ├── dominio        las reglas del juego (SIN pygame)
     ├── mundo          el mapa: habitaciones y posiciones
     ├── i18n           textos en español, inglés y portugués
     └── config         constantes; no depende de nada

La regla que sostiene el resto: en dominio/ no se importa pygame. Eso permite
probar las mecánicas sin abrir una ventana y mantiene separado "qué pasa" de
"cómo se ve".

Ver docs/ARQUITECTURA.md para el detalle.
"""

__version__ = "0.1.0"
