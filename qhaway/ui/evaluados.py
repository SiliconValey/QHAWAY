"""Vista de grupos ya evaluados (leer evaluaciones validadas).

Lista las evaluaciones validadas del ciclo y permite reabrirlas en modo lectura o
reexportar sus PDF, sin recargar la entrega. Delega en `servicios.consulta` y
`servicios.exportar`.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..servicios import configurar, consulta, exportar


class VistaEvaluados(QWidget):
    def __init__(self, ciclo, parent=None):
        super().__init__(parent)
        self.ciclo = ciclo
        layout = QVBoxLayout(self)

        titulo = QLabel("Grupos ya evaluados", self)
        titulo.setProperty("class", "titulo")
        layout.addWidget(titulo)
        sub = QLabel("Evaluaciones validadas: consultá el detalle o reexportá los PDF.", self)
        sub.setProperty("class", "subtitulo")
        layout.addWidget(sub)

        self.tabla = QTableWidget(0, 5, self)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setHorizontalHeaderLabels(
            ["Grupo", "Proyecto", "Exposición", "Nota", "Validado"])
        layout.addWidget(self.tabla)

        botones = QHBoxLayout()
        self.btn_detalle = QPushButton("Ver detalle", self)
        self.btn_reexportar = QPushButton("Reexportar informe + guía", self)
        self.btn_reexportar.setProperty("class", "primario")
        self.btn_actualizar = QPushButton("Actualizar", self)
        self.btn_detalle.clicked.connect(self._ver_detalle)
        self.btn_reexportar.clicked.connect(self._reexportar)
        self.btn_actualizar.clicked.connect(self.refrescar)
        for b in (self.btn_detalle, self.btn_reexportar, self.btn_actualizar):
            botones.addWidget(b)
        layout.addLayout(botones)

        self.lbl_estado = QLabel("", self)
        layout.addWidget(self.lbl_estado)

        self._filas: list = []
        self._detalle = None
        self.refrescar()

    def refrescar(self) -> None:
        self._filas = consulta.listar_evaluados(self.ciclo)
        self.tabla.setRowCount(len(self._filas))
        for i, ev in enumerate(self._filas):
            valores = [
                f"{ev.grupo_codigo} · {ev.grupo_nombre}",
                ev.proyecto,
                str(ev.exposicion),
                str(ev.nota_final if ev.nota_final is not None else "—"),
                ev.fecha_validacion or "—",
            ]
            for col, val in enumerate(valores):
                self.tabla.setItem(i, col, QTableWidgetItem(val))
        estado = (f"{len(self._filas)} evaluación(es) validada(s)."
                  if self._filas else "Todavía no hay evaluaciones validadas.")
        self.lbl_estado.setText(estado)

    def _seleccion(self):
        fila = self.tabla.currentRow()
        return self._filas[fila] if 0 <= fila < len(self._filas) else None

    # --- Métodos públicos testeables ----------------------------------------
    def ver_detalle(self, seleccion):
        """Abre la evaluación en modo solo lectura."""
        from .revision import VistaRevision
        rubrica = configurar.rubrica_activa(self.ciclo)
        self._detalle = VistaRevision(
            self.ciclo, seleccion.entrega_id, seleccion.evaluacion_id, rubrica,
            solo_lectura=True)
        self._detalle.setWindowTitle(f"Detalle — {seleccion.grupo_codigo}")
        self._detalle.resize(820, 560)
        self._detalle.show()
        return self._detalle

    def reexportar(self, seleccion):
        """Regenera el informe y la guía de la evaluación."""
        rubrica = configurar.rubrica_activa(self.ciclo)
        entrega = consulta.entrega_de(self.ciclo, seleccion.entrega_id)
        grupo = self.ciclo.grupos.obtener(seleccion.grupo_id)
        informe = exportar.exportar_informe_grupo(
            self.ciclo, grupo, entrega, seleccion.evaluacion_id, rubrica,
            fecha=seleccion.fecha_validacion or "")
        guia = exportar.exportar_guia_defensa(
            self.ciclo, grupo, entrega, seleccion.evaluacion_id)
        return informe, guia

    # --- Handlers -----------------------------------------------------------
    def _ver_detalle(self) -> None:
        sel = self._seleccion()
        if sel is None:
            return
        if configurar.rubrica_activa(self.ciclo) is None:
            QMessageBox.warning(self, "Falta rúbrica",
                                "Cargá la rúbrica del ciclo para ver el detalle.")
            return
        self.ver_detalle(sel)

    def _reexportar(self) -> None:
        sel = self._seleccion()
        if sel is None:
            return
        try:
            informe, guia = self.reexportar(sel)
            QMessageBox.information(self, "QHAWAY",
                                    f"Reexportado:\n{informe.name}\n{guia.name}")
        except Exception as e:  # noqa: BLE001
            QMessageBox.warning(self, "Error al exportar", str(e))
