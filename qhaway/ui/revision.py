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
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..servicios import revision
from .dialogos import confirmar


class VistaRevision(QWidget):
    """Presenta el borrador de una evaluación y permite validarlo (REV-01/02/07)."""

    def __init__(self, ciclo, entrega_id: int, evaluacion_id: int, rubrica, parent=None,
                 *, solo_lectura: bool = False):
        super().__init__(parent)
        self.ciclo = ciclo
        self.entrega_id = entrega_id
        self.evaluacion_id = evaluacion_id
        self.rubrica = rubrica
        self.solo_lectura = solo_lectura

        layout = QVBoxLayout(self)

        self.tabla = QTableWidget(0, 4, self)
        self.tabla.setAlternatingRowColors(True)
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

        # Nota final (REV-04): el docente confirma la nota antes de validar (EXP-03).
        fila_nota = QHBoxLayout()
        fila_nota.addWidget(QLabel("Nota final:", self))
        self.spin_nota = QSpinBox(self)
        self.spin_nota.setRange(1, 10)
        self.btn_fijar_nota = QPushButton("Fijar nota final", self)
        self.btn_fijar_nota.clicked.connect(self._fijar_nota)
        fila_nota.addWidget(self.spin_nota)
        fila_nota.addWidget(self.btn_fijar_nota)
        layout.addLayout(fila_nota)

        self.btn_validar = QPushButton("Validar evaluación", self)
        self.btn_validar.setProperty("class", "exito")
        self.btn_validar.clicked.connect(self._validar)
        layout.addWidget(self.btn_validar)

        self._ids: list[int] = []
        self.confirmar = confirmar   # sustituible en tests
        if self.solo_lectura:
            for w in (self.btn_aceptar, self.btn_editar, self.btn_descartar,
                      self.spin_nota, self.btn_fijar_nota, self.btn_validar):
                w.setEnabled(False)
                w.setVisible(False)
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

        # Inicializar el spin con la nota final ya fijada o, si no, la sugerida.
        ev = self.ciclo.evaluaciones.obtener(self.evaluacion_id)
        if ev is not None and not getattr(self, "_nota_tocada", False):
            nota = ev.nota_final if ev.nota_final is not None else ev.nota_sugerida
            if nota is not None:
                self.spin_nota.setValue(int(nota))

    def _fijar_nota(self) -> None:
        from datetime import date
        self._nota_tocada = True
        self.fijar_nota_final(self.spin_nota.value(), date.today().isoformat())
        self.lbl_estado.setText(f"Nota final fijada en {self.spin_nota.value()}.")

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
        nota = self.ciclo.evaluaciones.obtener(self.evaluacion_id)
        nota_txt = f" con nota {nota.nota_final}" if nota and nota.nota_final is not None else ""
        if not self.confirmar(
            f"¿Validar esta evaluación{nota_txt}?",
            titulo="Validar evaluación",
            detalle="Queda cerrada para edición y habilita la exportación de los "
                    "informes. Vas a poder consultarla desde la pestaña «Evaluados».",
            parent=self, texto_aceptar="Sí, validar",
        ):
            return
        try:
            self.validar()
            QMessageBox.information(self, "QHAWAY", "Evaluación validada.")
        except Exception as e:  # noqa: BLE001 - se muestra al docente
            QMessageBox.warning(self, "No se puede validar", str(e))
