# -*- mode: python ; coding: utf-8 -*-
"""Receta de PyInstaller para generar el .exe standalone.

    pyinstaller vecindad.spec

Deja el ejecutable en dist/. Los assets y los sonidos se empaquetan dentro
del propio .exe y se extraen a una carpeta temporal al arrancar; el juego
los encuentra porque config/rutas.py consulta sys._MEIPASS antes que la ruta
del código fuente.

Los datos del jugador (progreso y preferencias) NO van aquí: se guardan en
%APPDATA%/LaVecindadDelChavo para que sigan funcionando aunque el juego
quede instalado en una carpeta de solo lectura.
"""

# Todo el árbol de assets y sonidos, tal cual está en el repositorio.
DATOS = [
    ("assets", "assets"),
    ("sonidos", "sonidos"),
]

a = Analysis(
    ["run.py"],
    pathex=["src"],
    binaries=[],
    datas=DATOS,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # pygame arrastra estos por dependencias del sistema y no se usan.
    excludes=["tkinter", "unittest", "pydoc", "doctest"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Chaves Nightmare Plus",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    # Sin ventana de consola detrás del juego.
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Es un PNG: PyInstaller lo convierte a .ico por su cuenta si Pillow
    # está instalado (pip install pillow). El mismo logo es el icono de la
    # ventana (config/rutas.py, ARCHIVO_ICONO).
    icon="assets/logo/Vecindad Macabra bajo la Luna.png",
)
