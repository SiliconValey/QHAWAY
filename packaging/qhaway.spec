# -*- mode: python ; coding: utf-8 -*-
"""
QHAWAY — especificación de PyInstaller (RNF-10).

Receta validada en la PoC de congelamiento (Etapa 0.5, Windows 11):
* --collect-all weasyprint  → arrastra sus submódulos (fontTools, tinycss2,
  cssselect2, pydyf) que PyInstaller no detecta solo.
* GTK embebido vía `binaries` → el usuario final NO instala GTK: viaja adentro.
* --onedir (no --onefile): la distribución es la CARPETA entera de dist/, no el
  .exe suelto (copiar solo el .exe da "Failed to load Python DLL").

Construir en Windows, en el venv del proyecto:
    pip install pyinstaller
    pyinstaller qhaway.spec

Resultado: dist/qhaway/  (carpeta completa = la app distribuible; zippearla).

Ajustá GTK_BIN a la ruta de tu GTK3-Runtime si difiere.
"""

import glob
from PyInstaller.utils.hooks import collect_all

GTK_BIN = r"C:\Program Files\GTK3-Runtime Win64\bin"

# WeasyPrint + su familia de dependencias que el análisis estático no ve.
datas, binaries, hiddenimports = [], [], []
for paquete in ("weasyprint", "fontTools", "tinycss2", "cssselect2", "pydyf"):
    d, b, h = collect_all(paquete)
    datas += d; binaries += b; hiddenimports += h

# GTK: empaquetar todas las DLL del runtime (solución al error 0x7E del PoC).
binaries += [(dll, ".") for dll in glob.glob(GTK_BIN + r"\*.dll")]

# Plantillas de config de ejemplo (opcional: acompañar al ejecutable).
datas += [("config-ejemplo", "config-ejemplo")]


a = Analysis(
    ["qhaway_app.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="qhaway",
    icon="packaging/qhaway.ico",   # ícono del ejecutable
    console=False,          # --windowed: sin consola
    disable_windowed_traceback=False,
)
coll = COLLECT(
    exe, a.binaries, a.datas,
    strip=False, upx=False,
    name="qhaway",          # -> dist/qhaway/
)
