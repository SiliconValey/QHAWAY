"""Vista de revisión (REV) — la más compleja del sistema (IEX-01).

Capa delgada sobre `servicios.revision`: la vista NO tiene lógica de negocio, solo
presenta el borrador y delega cada acción en el servicio, luego refresca. Por eso
sus métodos públicos (`aceptar`, `editar`, `descartar`, `validar`) son directamente
testeables con pytest-qt, sin simular clics.

Diseño deliberadamente sobrio: esta vista está pensada para **evolucionar usándola
con borradores reales** (plan, Etapa 7), no para quedar fija ahora.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..servicios import revision


class VistaRevision(QWidget):
    """Presenta el borrador de una evaluación y permite validarlo (REV-01/02/07)."""

    def __init__(self, ciclo, entrega_id: int, evaluacion_id: int, rubrica, parent=None):
        super().__init__(parent)
        self.ciclo = ciclo
        self.entrega_id = entrega_id
        self.evaluacion_id = evaluacion_id
        self.rubrica = rubrica

        layout = QVBoxLayout(self)

        self.tabla = QTableWidget(0, 4, self)
        self.tabla.setHorizontalHeaderLabels(["Tipo", "Contenido", "Estado", "Origen"])
        layout.addWidget(self.tabla)

        botones = QHBoxLayout()
        self.btn_aceptar = QPushButton("Aceptar", self)
        self.btn_editar = QPushButton("Editar", self)
        self.btn_descartar = QPushButton("Descartar", self)
        self.btn_aceptar.clicked.connect(self._aceptar_seleccionado)
        self.btn_editar.clicked.connect(self._editar_seleccionado)
        self.btn_descartar.clicked.connect(self._descartar_seleccionado)
        for b in (self.btn_aceptar, self.btn_editar, self.btn_descartar):
            botones.addWidget(b)
        layout.addLayout(botones)

        self.lbl_estado = QLabel(self)
        layout.addWidget(self.lbl_estado)

        self.btn_validar = QPushButton("Validar evaluación", self)
        self.btn_validar.clicked.connect(self._validar)
        layout.addWidget(self.btn_validar)

        self._ids: list[int] = []
        self.refrescar()

    # --- Refresco de la vista ------------------------------------------------
    def refrescar(self) -> None:
        elementos = self.ciclo.elementos.de_evaluacion(self.evaluacion_id)
        self._ids = [e["id"] for e in elementos]
        self.tabla.setRowCount(len(elementos))
        for fila, e in enumerate(elementos):
            contenido = e["contenido_final"] or e["contenido_original"]
            valores = [e["tipo"], contenido, e["estado_revision"], e["origen"] or ""]
            for col, val in enumerate(valores):
                self.tabla.setItem(fila, col, QTableWidgetItem(str(val)))

        ok, motivo = revision.puede_validar(self.ciclo, self.evaluacion_id)
        self.btn_validar.setEnabled(ok)
        pendientes = self.ciclo.elementos.pendientes(self.evaluacion_id)
        self.lbl_estado.setText(f"Pendientes: {pendientes} — {motivo}")

    def _elemento_seleccionado(self) -> int | None:
        fila = self.tabla.currentRow()
        if 0 <= fila < len(self._ids):
            return self._ids[fila]
        return None

    # --- Métodos públicos testeables (la lógica ya está en el servicio) ------
    def aceptar(self, elemento_id: int) -> None:
        revision.aceptar(self.ciclo, elemento_id)
        self.refrescar()

    def editar(self, elemento_id: int, nuevo_contenido: str) -> None:
        revision.editar(self.ciclo, elemento_id, nuevo_contenido)
        self.refrescar()

    def descartar(self, elemento_id: int) -> None:
        revision.descartar(self.ciclo, elemento_id)
        self.refrescar()

    def fijar_nota_final(self, nota: int, fecha: str) -> None:
        revision.fijar_nota_final(self.ciclo, self.evaluacion_id, nota, fecha)
        self.refrescar()

    def validar(self) -> None:
        revision.validar(self.ciclo, self.entrega_id, self.evaluacion_id)
        self.refrescar()

    # --- Handlers de botones (leen selección / abren diálogos) ---------------
    def _aceptar_seleccionado(self) -> None:
        eid = self._elemento_seleccionado()
        if eid is not None:
            self.aceptar(eid)

    def _editar_seleccionado(self) -> None:
        eid = self._elemento_seleccionado()
        if eid is None:
            return
        actual = self.ciclo.elementos.obtener(eid)
        texto, ok = QInputDialog.getMultiLineText(
            self, "Editar elemento", "Contenido:",
            actual["contenido_final"] or actual["contenido_original"],
        )
        if ok:
            self.editar(eid, texto)

    def _descartar_seleccionado(self) -> None:
        eid = self._elemento_seleccionado()
        if eid is not None:
            self.descartar(eid)

    def _validar(self) -> None:
        try:
            self.validar()
            QMessageBox.information(self, "QHAWAY", "Evaluación validada.")
        except Exception as e:  # noqa: BLE001 - se muestra al docente
            QMessageBox.warning(self, "No se puede validar", str(e))
