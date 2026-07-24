"""Ícono de la aplicación, dibujado por código.

QHAWAY significa «observar» en quechua: el ícono es un ojo estilizado sobre el
navy de la identidad. Se genera con QPainter en vez de cargar un archivo, así no
hay que empaquetar recursos externos ni resolver rutas dentro del ejecutable
congelado (RNF-10).
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPixmap

from .tema import AZUL, INK


def _pixmap(lado: int) -> QPixmap:
    pm = QPixmap(lado, lado)
    pm.fill(Qt.GlobalColor.transparent)

    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Fondo redondeado navy
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(INK))
    radio = lado * 0.22
    p.drawRoundedRect(QRectF(0, 0, lado, lado), radio, radio)

    # Ojo: dos arcos opuestos formando una lente (almendra)
    cx, cy = lado / 2, lado / 2
    ancho = lado * 0.62
    alto = lado * 0.38
    ojo = QPainterPath()
    ojo.moveTo(cx - ancho / 2, cy)
    ojo.quadTo(cx, cy - alto, cx + ancho / 2, cy)
    ojo.quadTo(cx, cy + alto, cx - ancho / 2, cy)
    p.setBrush(QColor("#FFFFFF"))
    p.drawPath(ojo)

    # Iris y pupila
    r_iris = lado * 0.145
    p.setBrush(QColor(AZUL))
    p.drawEllipse(QPointF(cx, cy), r_iris, r_iris)
    p.setBrush(QColor(INK))
    p.drawEllipse(QPointF(cx, cy), r_iris * 0.45, r_iris * 0.45)

    # Brillo
    p.setBrush(QColor(255, 255, 255, 210))
    p.drawEllipse(QPointF(cx + r_iris * 0.35, cy - r_iris * 0.4), lado * 0.028, lado * 0.028)

    p.end()
    return pm


def icono_app() -> QIcon:
    """Ícono multi-resolución de la aplicación."""
    icono = QIcon()
    for lado in (16, 24, 32, 48, 64, 128, 256):
        icono.addPixmap(_pixmap(lado))
    return icono


def guardar_png(ruta, lado: int = 256) -> None:
    """Guarda el ícono como PNG (útil para el instalador o el README)."""
    _pixmap(lado).save(str(ruta))
