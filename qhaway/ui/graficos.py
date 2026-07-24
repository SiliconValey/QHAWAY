"""Gráficos de consumo dibujados con QPainter (MON-02/03/04).

Sin dependencias externas: se pintan a mano, así viajan dentro del ejecutable
congelado (coherente con RNF-10, el usuario final no instala nada). Reciben datos
ya calculados por `servicios.monitor`; no tienen lógica de negocio.
"""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

from .tema import AZUL, BORDE, INK, TENUE

_ROJO = "#C0392B"       # alerta de presupuesto (MON-03)
_PISTA = "#E3E8F0"      # fondo de las barras


class BarraPresupuesto(QWidget):
    """Medidor horizontal: consumo del mes vs presupuesto, con umbral marcado."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(72)
        self._acumulado = 0.0
        self._presupuesto = 20.0
        self._umbral = 0.80
        self._alerta = False

    def actualizar(self, acumulado, presupuesto, umbral, alerta) -> None:
        self._acumulado = acumulado
        self._presupuesto = max(presupuesto, 0.0001)
        self._umbral = umbral
        self._alerta = alerta
        self.update()

    def paintEvent(self, _evento) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        m = 12
        ancho = self.width() - 2 * m
        alto_barra = 22
        y = 34

        # Etiqueta superior
        p.setPen(QColor(INK))
        f = QFont(); f.setPointSize(10); f.setBold(True); p.setFont(f)
        prop = self._acumulado / self._presupuesto
        color = _ROJO if self._alerta else AZUL
        p.drawText(m, 8, ancho, 20, Qt.AlignmentFlag.AlignLeft,
                   f"Presupuesto del mes")
        p.setPen(QColor(color))
        p.drawText(m, 8, ancho, 20, Qt.AlignmentFlag.AlignRight,
                   f"USD {self._acumulado:.2f} / {self._presupuesto:.2f}  ({prop:.0%})")

        # Pista
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(_PISTA))
        p.drawRoundedRect(QRectF(m, y, ancho, alto_barra), 8, 8)

        # Relleno (clamp visual a 100%)
        relleno = min(prop, 1.0) * ancho
        if relleno > 0:
            p.setBrush(QColor(color))
            p.drawRoundedRect(QRectF(m, y, max(relleno, 8), alto_barra), 8, 8)

        # Marca del umbral
        x_umbral = m + self._umbral * ancho
        p.setPen(QPen(QColor(INK), 2, Qt.PenStyle.DashLine))
        p.drawLine(int(x_umbral), y - 4, int(x_umbral), y + alto_barra + 4)
        p.setPen(QColor(TENUE))
        f2 = QFont(); f2.setPointSize(8); p.setFont(f2)
        p.drawText(int(x_umbral) - 30, y + alto_barra + 6, 60, 14,
                   Qt.AlignmentFlag.AlignCenter, f"umbral {self._umbral:.0%}")
        p.end()


class GraficoHistorico(QWidget):
    """Barras verticales del costo por mes (MON-04)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(200)
        self._datos: list[dict] = []

    def actualizar(self, historico: list[dict]) -> None:
        self._datos = historico
        self.update()

    def paintEvent(self, _evento) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        m = 16
        ancho = self.width() - 2 * m
        alto = self.height() - 2 * m
        base_y = self.height() - m - 18

        # Título
        p.setPen(QColor(INK))
        f = QFont(); f.setPointSize(10); f.setBold(True); p.setFont(f)
        p.drawText(m, 4, ancho, 18, Qt.AlignmentFlag.AlignLeft, "Consumo por mes")

        if not self._datos:
            p.setPen(QColor(TENUE))
            f2 = QFont(); f2.setPointSize(9); p.setFont(f2)
            p.drawText(QRectF(m, m, ancho, alto), Qt.AlignmentFlag.AlignCenter,
                       "Todavía no hay consumo registrado.")
            p.end()
            return

        datos = self._datos[-12:]  # últimos 12 meses
        maximo = max(d["costo"] for d in datos) or 1.0
        n = len(datos)
        sep = 10
        ancho_barra = max((ancho - sep * (n + 1)) / n, 8)
        alto_util = base_y - 28

        f3 = QFont(); f3.setPointSize(8)
        for i, d in enumerate(datos):
            x = m + sep + i * (ancho_barra + sep)
            h = (d["costo"] / maximo) * alto_util
            y = base_y - h
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(AZUL))
            p.drawRoundedRect(QRectF(x, y, ancho_barra, h), 5, 5)
            # Valor encima
            p.setPen(QColor(INK)); p.setFont(f3)
            p.drawText(QRectF(x - 6, y - 16, ancho_barra + 12, 14),
                       Qt.AlignmentFlag.AlignCenter, f"{d['costo']:.2f}")
            # Mes debajo
            p.setPen(QColor(TENUE))
            p.drawText(QRectF(x - 6, base_y + 2, ancho_barra + 12, 16),
                       Qt.AlignmentFlag.AlignCenter, d["mes"][-2:] if len(d["mes"]) >= 2 else d["mes"])

        # Eje base
        p.setPen(QPen(QColor(BORDE), 1))
        p.drawLine(m, base_y, self.width() - m, base_y)
        p.end()
