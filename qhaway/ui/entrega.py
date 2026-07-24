"""Vista de carga de entrega (ING-01/03) — capa delgada.

El docente elige archivos y confirma el tipo de cada uno; delega en
`servicios.cargar_entrega`.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..servicios import cargar_entrega
from .dialogos import confirmar
from ..servicios.cargar_entrega import ArchivoACargar, clasificar_por_extension

TIPOS = ["presentacion", "srs", "fd", "ui"]


class VistaEntrega(QWidget):
    def __init__(self, ciclo, grupo, exposicion: int = 1, parent=None):
        super().__init__(parent)
        self.ciclo = ciclo
        self.grupo = grupo
        self.exposicion = exposicion
        self._pendientes: list[ArchivoACargar] = []

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Cargar entrega — {grupo.codigo} · Exposición {exposicion}", self))

        fila = QHBoxLayout()
        self.btn_elegir = QPushButton("Elegir archivos…", self)
        self.btn_cargar = QPushButton("Cargar entrega", self)
        self.btn_cargar.setProperty("class", "primario")
        self.btn_elegir.clicked.connect(self._elegir_archivos)
        self.btn_cargar.clicked.connect(self._cargar)
        fila.addWidget(self.btn_elegir); fila.addWidget(self.btn_cargar)
        layout.addLayout(fila)

        self.tabla = QTableWidget(0, 2, self)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setHorizontalHeaderLabels(["Archivo", "Tipo"])
        layout.addWidget(self.tabla)

        self.lbl_estado = QLabel("", self)
        layout.addWidget(self.lbl_estado)
        self.confirmar = confirmar   # sustituible en tests

    def _refrescar_tabla(self) -> None:
        self.tabla.setRowCount(len(self._pendientes))
        for fila, a in enumerate(self._pendientes):
            self.tabla.setItem(fila, 0, QTableWidgetItem(a.ruta.name))
            combo = QComboBox(); combo.addItems(TIPOS)
            combo.setCurrentText(a.tipo_artefacto)
            combo.currentTextChanged.connect(lambda t, i=fila: self._set_tipo(i, t))
            self.tabla.setCellWidget(fila, 1, combo)

    def _set_tipo(self, indice: int, tipo: str) -> None:
        a = self._pendientes[indice]
        self._pendientes[indice] = ArchivoACargar(a.ruta, tipo)

    # --- Métodos públicos testeables ----------------------------------------
    def agregar_archivo(self, ruta: Path | str, tipo: str | None = None) -> None:
        ruta = Path(ruta)
        if tipo is None:
            sugerido, motivo = cargar_entrega.sugerir_tipo(ruta)
            tipo = sugerido or "srs"     # si no hay señal clara, un default editable
            self.lbl_estado.setText(f"{ruta.name}: {motivo}")
        self._pendientes.append(ArchivoACargar(ruta, tipo))
        self._refrescar_tabla()

    def cargar(self):
        entrega = cargar_entrega.cargar_entrega(
            self.ciclo, self.grupo, self.exposicion, list(self._pendientes)
        )
        self.lbl_estado.setText(f"Entrega cargada: versión {entrega.version}, "
                                f"{len(self._pendientes)} archivo(s).")
        self._pendientes.clear()
        self._refrescar_tabla()
        return entrega

    # --- Handlers -----------------------------------------------------------
    def _elegir_archivos(self) -> None:
        rutas, _ = QFileDialog.getOpenFileNames(
            self, "Elegir archivos de la entrega", "",
            "Entregas (*.pdf *.docx *.ui)")
        for r in rutas:
            self.agregar_archivo(r)

    def _cargar(self) -> None:
        if not self._pendientes:
            return
        from PySide6.QtWidgets import QMessageBox

        from ..servicios.cargar_entrega import TipoDuplicado

        # Si ya hay una entrega para esta exposición, se crea una versión nueva.
        vigente = self.ciclo.entregas.vigente(self.grupo.id, self.exposicion)
        if vigente is not None and not self.confirmar(
            f"Este grupo ya tiene una entrega cargada (versión {vigente.version}).",
            titulo="Nueva versión de entrega",
            detalle="Se cargará como una versión nueva. La anterior y su evaluación "
                    "quedan en el historial.",
            parent=self, texto_aceptar="Sí, cargar versión nueva",
        ):
            return
        try:
            self.cargar()
        except TipoDuplicado as e:
            QMessageBox.warning(self, "Tipos repetidos", str(e))
        except Exception as e:  # noqa: BLE001
            self.lbl_estado.setText(f"Error: {e}")
