"""Tema visual de QHAWAY (IEX-01).

Una sola hoja de estilos Qt (QSS) aplicada a la QApplication, para dar identidad
profesional sin tocar cada vista. La paleta es la misma de los informes PDF
(navy profundo, azul, púrpura sobrio) para que la app y su salida se sientan un
único producto.

Uso:
    from .tema import aplicar_tema
    aplicar_tema(app)
"""

from __future__ import annotations

# Paleta (coherente con infra/informes.py).
INK = "#16213E"        # navy profundo: títulos, acción primaria
AZUL = "#0F3460"       # acento: selección, foco, progreso
PURPURA = "#533483"    # secundario, muy sobrio
FONDO = "#EEF1F6"      # fondo general, frío y calmo
SUPERFICIE = "#FFFFFF"  # tablas, campos, tarjetas
BORDE = "#D5DCE6"
TENUE = "#6B7280"
EXITO = "#2F7D5D"      # validar
EXITO_HOVER = "#276B4F"

_QSS = f"""
* {{
    font-family: "Segoe UI", "Inter", "Helvetica Neue", Arial, sans-serif;
    font-size: 10pt;
    color: {INK};
}}
QMainWindow, QDialog, QWidget {{ background: {FONDO}; }}

/* Pestañas */
QTabWidget::pane {{
    background: {SUPERFICIE};
    border: 1px solid {BORDE};
    border-radius: 10px;
    top: -1px;
}}
QTabBar::tab {{
    background: transparent;
    color: {TENUE};
    padding: 9px 18px;
    margin-right: 2px;
    border: none;
    font-weight: 500;
}}
QTabBar::tab:selected {{
    color: {INK};
    border-bottom: 2px solid {AZUL};
    font-weight: 600;
}}
QTabBar::tab:hover {{ color: {INK}; }}

/* Botones: por defecto discreto; primario y de éxito con relleno */
QPushButton {{
    background: {SUPERFICIE};
    border: 1px solid {BORDE};
    border-radius: 8px;
    padding: 8px 16px;
    color: {INK};
    font-weight: 500;
}}
QPushButton:hover {{ border-color: {AZUL}; background: #F4F8FF; }}
QPushButton:pressed {{ background: #E7EEFA; }}
QPushButton:disabled {{ color: #A9B0BD; background: #F1F3F7; border-color: #E4E8EF; }}

QPushButton[class="primario"] {{
    background: {INK}; color: #FFFFFF; border: none;
}}
QPushButton[class="primario"]:hover {{ background: {AZUL}; }}
QPushButton[class="primario"]:pressed {{ background: #0B2749; }}
QPushButton[class="primario"]:disabled {{ background: #B9C0CE; color: #EEF1F6; }}

QPushButton[class="exito"] {{ background: {EXITO}; color: #FFFFFF; border: none; }}
QPushButton[class="exito"]:hover {{ background: {EXITO_HOVER}; }}
QPushButton[class="exito"]:disabled {{ background: #AEC7BB; color: #EEF5F1; }}

/* Campos de entrada */
QLineEdit, QSpinBox, QComboBox {{
    background: {SUPERFICIE};
    border: 1px solid {BORDE};
    border-radius: 6px;
    padding: 6px 8px;
    selection-background-color: {AZUL};
    selection-color: #FFFFFF;
}}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{ border: 1px solid {AZUL}; }}
QComboBox::drop-down {{ border: none; width: 20px; }}

/* Tablas */
QTableWidget, QTableView {{
    background: {SUPERFICIE};
    border: 1px solid {BORDE};
    border-radius: 10px;
    gridline-color: #EDF0F5;
    alternate-background-color: #F7F9FC;
    selection-background-color: #DCE7FA;
    selection-color: {INK};
}}
QHeaderView::section {{
    background: #F0F3F8;
    color: {INK};
    padding: 7px 8px;
    border: none;
    border-bottom: 2px solid {AZUL};
    font-weight: 600;
}}
QTableWidget::item {{ padding: 4px 6px; }}
QTableCornerButton::section {{ background: #F0F3F8; border: none; }}

/* Barra de progreso */
QProgressBar {{
    border: none;
    background: #E3E8F0;
    border-radius: 8px;
    height: 16px;
    text-align: center;
    color: {INK};
    font-size: 8.5pt;
}}
QProgressBar::chunk {{ background: {AZUL}; border-radius: 8px; }}

QLabel {{ background: transparent; }}
QLabel[class="titulo"] {{ font-size: 14pt; font-weight: 700; color: {INK}; }}
QLabel[class="subtitulo"] {{ color: {TENUE}; font-size: 10.5pt; }}

QScrollBar:vertical {{ background: transparent; width: 12px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: #C4CCDA; border-radius: 6px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: #AAB4C6; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
"""


def aplicar_tema(app) -> None:
    """Aplica el tema global a la aplicación Qt."""
    app.setStyleSheet(_QSS)


def marcar_primario(boton) -> None:
    """Marca un botón como acción primaria (relleno navy)."""
    boton.setProperty("class", "primario")


def marcar_exito(boton) -> None:
    """Marca un botón como acción de confirmación (relleno verde)."""
    boton.setProperty("class", "exito")
