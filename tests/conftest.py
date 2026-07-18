"""Configuración de pytest: Qt en modo offscreen para los tests de UI.

Debe fijarse antes de que se cree cualquier QApplication (pytest carga conftest
antes que los módulos de test), para que pytest-qt corra sin servidor gráfico.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
