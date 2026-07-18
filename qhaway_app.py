"""Punto de entrada de QHAWAY (para el empaquetado, RNF-10).

Registra las DLL de GTK en Windows (para corridas sin congelar; en el .exe las
DLL viajan adentro vía --add-binary) y lanza la aplicación. La ventana completa
(selección de ciclo, ABM, entrega, análisis, revisión) se arma sobre las vistas
y servicios ya existentes; este archivo es el arranque que PyInstaller congela.
"""

from __future__ import annotations

import os
import sys


def _registrar_gtk_windows() -> None:
    """En Windows sin congelar, ayuda a encontrar el runtime GTK de WeasyPrint."""
    if os.name != "nt":
        return
    gtk = r"C:\Program Files\GTK3-Runtime Win64\bin"
    if hasattr(os, "add_dll_directory") and os.path.isdir(gtk):
        os.add_dll_directory(gtk)


def main() -> int:
    _registrar_gtk_windows()

    from PySide6.QtWidgets import QApplication, QLabel, QMainWindow

    app = QApplication.instance() or QApplication(sys.argv)
    ventana = QMainWindow()
    ventana.setWindowTitle("QHAWAY")
    # Arranque mínimo: la ventana real (pestañas de ciclo/config/entrega/revisión)
    # se compone con las vistas de qhaway.ui. Este stub confirma que el stack
    # congelado (PySide6) arranca; abrir_revision() abre el flujo de revisión.
    ventana.setCentralWidget(QLabel("QHAWAY — asistente de corrección\n\nListo."))
    ventana.resize(640, 400)
    ventana.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
