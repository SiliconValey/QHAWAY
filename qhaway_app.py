"""Punto de entrada de QHAWAY (RNF-10).

Registra las DLL de GTK en Windows (para WeasyPrint sin congelar; en el .exe
viajan adentro vía --add-binary), deja crear o abrir un ciclo, y abre la ventana
principal.
"""

from __future__ import annotations

import os
import sys


def _registrar_gtk_windows() -> None:
    if os.name != "nt":
        return
    gtk = r"C:\Program Files\GTK3-Runtime Win64\bin"
    if hasattr(os, "add_dll_directory") and os.path.isdir(gtk):
        os.add_dll_directory(gtk)


def _elegir_ciclo(app):
    """Diálogo de inicio: abrir un ciclo existente o crear uno nuevo."""
    from pathlib import Path

    from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox

    from qhaway.infra import abrir_ciclo, crear_ciclo

    resp = QMessageBox.question(
        None, "QHAWAY", "¿Abrir un ciclo existente?\n\nSí = abrir · No = crear uno nuevo",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
    )
    if resp == QMessageBox.StandardButton.Yes:
        carpeta = QFileDialog.getExistingDirectory(None, "Elegí la carpeta del ciclo")
        if not carpeta:
            return None
        if not (Path(carpeta) / "qhaway.db").exists():
            QMessageBox.warning(None, "QHAWAY", "Esa carpeta no contiene un ciclo (qhaway.db).")
            return None
        return abrir_ciclo(carpeta)

    carpeta = QFileDialog.getExistingDirectory(None, "Elegí dónde crear el ciclo")
    if not carpeta:
        return None
    nombre, ok = QInputDialog.getText(None, "Nuevo ciclo", "Nombre (ej: AED II — 2027):")
    if not ok or not nombre.strip():
        return None
    return crear_ciclo(Path(carpeta) / nombre.strip().replace(" ", "_"), nombre.strip())


def main() -> int:
    _registrar_gtk_windows()

    from PySide6.QtWidgets import QApplication

    from qhaway.ui.app import crear_ventana

    app = QApplication.instance() or QApplication(sys.argv)
    from qhaway.ui.errores import instalar_manejador_global
    from qhaway.ui.icono import icono_app
    from qhaway.ui.tema import aplicar_tema

    instalar_manejador_global()   # RNF-06: ningún fallo cierra la app en silencio
    aplicar_tema(app)
    app.setWindowIcon(icono_app())
    ciclo = _elegir_ciclo(app)
    if ciclo is None:
        return 0
    ventana = crear_ventana(ciclo)
    ventana.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
