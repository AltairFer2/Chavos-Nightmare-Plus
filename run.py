"""Arranque directo del juego sin instalar el paquete: `python run.py`.

Añade src/ al path y llama al mismo main() que usa el comando `vecindad`
instalado y `python -m vecindad`, así que las tres formas hacen lo mismo.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from vecindad.app.juego import main  # noqa: E402  (después de ajustar el path)

if __name__ == "__main__":
    main()
