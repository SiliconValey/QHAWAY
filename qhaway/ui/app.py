"""Ventana principal de QHAWAY (IEX-01) — andamiaje inicial.

Hospeda las vistas en pestañas. Por ahora enchufa `revision` y `monitor`, que son
las de esta etapa; las vistas de ABM (ciclo, configuración, entrega) se suman como
pestañas del mismo modo a medida que se construyen — son formularios y tablas
sobre los servicios ya existentes.

Punto de entrada para revisar un borrador real de punta a punta:

    from qhaway.infra import abrir_ciclo
    from qhaway.ui.app import abrir_revision
    ciclo = abrir_ciclo("ruta/al/ciclo")
    abrir_revision(ciclo, entrega_id=1, evaluacion_id=1, rubrica=rubrica)
"""

from __future__ import annotations

import sys


def abrir_revision(ciclo, entrega_id: int, evaluacion_id: int, rubrica) -> int:
    """Abre la ventana de revisión para una evaluación. Bloquea hasta cerrarla."""
    from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget

    from .monitor import VistaMonitor
    from .revision import VistaRevision

    app = QApplication.instance() or QApplication(sys.argv)

    ventana = QMainWindow()
    ventana.setWindowTitle("QHAWAY — Revisión")
    tabs = QTabWidget()
    tabs.addTab(VistaRevision(ciclo, entrega_id, evaluacion_id, rubrica), "Revisión")
    tabs.addTab(VistaMonitor(ciclo, evaluacion_id), "Consumo")
    ventana.setCentralWidget(tabs)
    ventana.resize(900, 600)
    ventana.show()
    return app.exec()
