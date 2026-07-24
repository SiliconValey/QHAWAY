"""Ventana principal de QHAWAY (IEX-01).

Hospeda las vistas en pestañas sobre un ciclo abierto. Las vistas que dependen de
un grupo/evaluación puntual (entrega, revisión) se abren desde la vista de ciclo
o vía las funciones `abrir_*`.
"""

from __future__ import annotations

import sys


def crear_ventana(ciclo):
    """Construye la ventana principal para un ciclo abierto (requiere PySide6)."""
    from PySide6.QtWidgets import QMainWindow, QTabWidget

    from ..version import titulo_ventana
    from .ayuda import VistaAcercaDe, VistaAyuda
    from .ciclo import VistaCiclo
    from .configuracion import VistaConfiguracion
    from .evaluados import VistaEvaluados
    from .icono import icono_app
    from .monitor import VistaMonitor

    ventana = QMainWindow()
    ventana.setWindowTitle(titulo_ventana(ciclo.ciclos.obtener(ciclo.ciclo_id).nombre))
    ventana.setWindowIcon(icono_app())
    tabs = QTabWidget()
    tabs.addTab(VistaCiclo(ciclo), "Grupos")
    tabs.addTab(VistaConfiguracion(ciclo), "Configuración")
    tabs.addTab(VistaEvaluados(ciclo), "Evaluados")
    tabs.addTab(VistaMonitor(ciclo), "Consumo")
    tabs.addTab(VistaAyuda(), "Ayuda")
    tabs.addTab(VistaAcercaDe(), "Acerca de")
    ventana.setCentralWidget(tabs)
    ventana.resize(1000, 640)
    return ventana


def abrir_ciclo_ui(ciclo) -> int:
    """Abre la ventana principal y corre el loop de Qt. Bloquea hasta cerrarla."""
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    from .tema import aplicar_tema
    aplicar_tema(app)
    ventana = crear_ventana(ciclo)
    ventana.show()
    return app.exec()


def abrir_revision(ciclo, entrega_id: int, evaluacion_id: int, rubrica) -> int:
    """Abre la ventana de revisión para una evaluación puntual."""
    from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget

    from .monitor import VistaMonitor
    from .revision import VistaRevision

    app = QApplication.instance() or QApplication(sys.argv)
    from .tema import aplicar_tema
    aplicar_tema(app)
    ventana = QMainWindow()
    ventana.setWindowTitle("QHAWAY — Revisión")
    tabs = QTabWidget()
    tabs.addTab(VistaRevision(ciclo, entrega_id, evaluacion_id, rubrica), "Revisión")
    tabs.addTab(VistaMonitor(ciclo, evaluacion_id), "Consumo")
    ventana.setCentralWidget(tabs)
    ventana.resize(900, 600)
    ventana.show()
    return app.exec()
