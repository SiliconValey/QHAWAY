"""Vista de monitoreo (MON-02/03/04, REV-06) — capa delgada.

Muestra el estado de presupuesto y las métricas de retrabajo que calculan los
servicios `monitor` y `revision`. Nunca bloquea: solo informa (MON-03).
"""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from ..servicios import monitor, revision


class VistaMonitor(QWidget):
    def __init__(self, ciclo, evaluacion_id: int | None = None, parent=None):
        super().__init__(parent)
        self.ciclo = ciclo
        self.evaluacion_id = evaluacion_id

        layout = QVBoxLayout(self)
        self.lbl_presupuesto = QLabel(self)
        self.lbl_costo_eval = QLabel(self)
        self.lbl_retrabajo = QLabel(self)
        for w in (self.lbl_presupuesto, self.lbl_costo_eval, self.lbl_retrabajo):
            layout.addWidget(w)
        self.refrescar()

    def refrescar(self) -> None:
        est = monitor.estado_presupuesto(self.ciclo)
        self.lbl_presupuesto.setText(est.resumen())
        # Resaltar en rojo si se superó el umbral (MON-03).
        color = "#c0392b" if est.alerta else "#2c3e50"
        self.lbl_presupuesto.setStyleSheet(f"color: {color};")

        if self.evaluacion_id is not None:
            costo = monitor.costo_evaluacion(self.ciclo, self.evaluacion_id)
            self.lbl_costo_eval.setText(f"Costo de esta evaluación: USD {costo:.4f}")
            self.lbl_retrabajo.setText(
                revision.metricas_retrabajo(self.ciclo, self.evaluacion_id).resumen()
            )
