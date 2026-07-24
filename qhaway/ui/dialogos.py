"""Confirmaciones para acciones que no tienen vuelta atrás.

`confirmar` es la única puerta: las vistas la guardan como atributo
(`self.confirmar`), así los tests pueden sustituirla por una función que devuelve
True o False sin abrir ventanas.
"""

from __future__ import annotations


def confirmar(
    mensaje: str,
    *,
    titulo: str = "Confirmar",
    detalle: str = "",
    parent=None,
    texto_aceptar: str = "Sí, continuar",
) -> bool:
    """Pregunta al docente antes de una acción irreversible. Devuelve True si acepta.

    El botón por defecto es «Cancelar»: si alguien presiona Enter por reflejo, no
    ejecuta la acción.
    """
    from PySide6.QtWidgets import QApplication, QMessageBox

    if QApplication.instance() is None:  # sin GUI (tests puros): no bloquear
        return True

    caja = QMessageBox(parent)
    caja.setIcon(QMessageBox.Icon.Question)
    caja.setWindowTitle(titulo)
    caja.setText(mensaje)
    if detalle:
        caja.setInformativeText(detalle)
    aceptar = caja.addButton(texto_aceptar, QMessageBox.ButtonRole.AcceptRole)
    cancelar = caja.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
    caja.setDefaultButton(cancelar)   # el default seguro es no hacer nada
    caja.exec()
    return caja.clickedButton() is aceptar
