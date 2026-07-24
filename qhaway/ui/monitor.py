"""Vista de monitoreo (MON-02/03/04, REV-06) — capa delgada, ahora con gráficos.

Muestra el estado de presupuesto como medidor, el histórico por mes como barras, y
las métricas puntuales (costo de la evaluación, retrabajo) como texto. La lógica
vive en los servicios `monitor` y `revision`. Nunca bloquea: solo informa (MON-03).
"""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from ..servicios import monitor, revision
from .graficos import BarraPresupuesto, GraficoHistorico


class VistaMonitor(QWidget):
    def __init__(self, ciclo, evaluacion_id: int | None = None, parent=None):
        super().__init__(parent)
        self.ciclo = ciclo
        self.evaluacion_id = evaluacion_id

        layout = QVBoxLayout(self)

        self.barra = BarraPresupuesto(self)
        layout.addWidget(self.barra)

        self.lbl_alerta = QLabel(self)
        layout.addWidget(self.lbl_alerta)

        self.grafico = GraficoHistorico(self)
        layout.addWidget(self.grafico, stretch=1)

        self.lbl_costo_eval = QLabel(self)
        self.lbl_retrabajo = QLabel(self)
        for w in (self.lbl_costo_eval, self.lbl_retrabajo):
            layout.addWidget(w)

        self.refrescar()

    def refrescar(self) -> None:
        est = monitor.estado_presupuesto(self.ciclo)
        self.barra.actualizar(est.acumulado, est.presupuesto, est.umbral, est.alerta)
        if est.alerta:
            self.lbl_alerta.setText("\u26a0 El consumo del mes super\u00f3 el umbral de aviso.")
            self.lbl_alerta.setStyleSheet("color: #C0392B; font-weight: 600;")
        else:
            self.lbl_alerta.setText("")

        self.grafico.actualizar(monitor.historico(self.ciclo))

        if self.evaluacion_id is not None:
            costo = monitor.costo_evaluacion(self.ciclo, self.evaluacion_id)
            self.lbl_costo_eval.setText(f"Costo de esta evaluaci\u00f3n: USD {costo:.4f}")
            self.lbl_retrabajo.setText(
                revision.metricas_retrabajo(self.ciclo, self.evaluacion_id).resumen()
            )
