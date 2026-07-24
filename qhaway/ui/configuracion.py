"""Vista de configuración (CFG-01/07/08/09/10) — capa delgada.

Reúne: clave de API + prueba de conexión, carga de rúbrica validada, y parámetros
del ciclo. Delega en `infra.config_usuario` y `servicios.configurar`.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..infra.config_usuario import cargar_clave, guardar_clave, probar_conexion
from ..servicios import configurar


class VistaConfiguracion(QWidget):
    def __init__(self, ciclo, parent=None):
        super().__init__(parent)
        self.ciclo = ciclo
        layout = QVBoxLayout(self)

        # --- Clave de API + conexión (CFG-07/08) ---
        fila_clave = QHBoxLayout()
        self.in_clave = QLineEdit(self)
        self.in_clave.setEchoMode(QLineEdit.EchoMode.Password)
        self.in_clave.setPlaceholderText("Clave de API (se guarda fuera del repo)")
        self.btn_guardar_clave = QPushButton("Guardar clave", self)
        self.btn_probar = QPushButton("Probar conexión", self)
        self.btn_guardar_clave.clicked.connect(self._guardar_clave)
        self.btn_probar.clicked.connect(self._probar_conexion)
        for w in (self.in_clave, self.btn_guardar_clave, self.btn_probar):
            fila_clave.addWidget(w)
        layout.addLayout(fila_clave)
        self.lbl_conexion = QLabel("Clave: " + ("configurada" if cargar_clave() else "no configurada"), self)
        layout.addWidget(self.lbl_conexion)

        # --- Rúbrica (CFG-01) ---
        fila_rub = QHBoxLayout()
        self.btn_rubrica = QPushButton("Cargar rúbrica (.yaml)", self)
        self.btn_rubrica.clicked.connect(self._cargar_rubrica)
        self.lbl_rubrica = QLabel("(sin rúbrica cargada)", self)
        fila_rub.addWidget(self.btn_rubrica); fila_rub.addWidget(self.lbl_rubrica)
        layout.addLayout(fila_rub)

        # --- Parámetros del ciclo (CFG-10) ---
        form = QFormLayout()
        self.in_nombre = QLineEdit(self)
        self.in_preguntas = QSpinBox(self); self.in_preguntas.setRange(1, 50)
        ciclo_row = ciclo.ciclos.obtener(ciclo.ciclo_id)
        if ciclo_row:
            self.in_nombre.setText(ciclo_row.nombre)
            self.in_preguntas.setValue(ciclo_row.cantidad_preguntas)
        self.btn_guardar_params = QPushButton("Guardar parámetros", self)
        self.btn_guardar_params.clicked.connect(self._guardar_parametros)
        form.addRow("Nombre del ciclo:", self.in_nombre)
        form.addRow("Preguntas de defensa:", self.in_preguntas)
        form.addRow(self.btn_guardar_params)
        layout.addLayout(form)

        self.rubrica = None

    # --- Métodos públicos testeables ----------------------------------------
    def guardar_clave(self, clave: str) -> None:
        guardar_clave(clave)
        self.lbl_conexion.setText("Clave: configurada")

    def cargar_rubrica(self, ruta: Path | str) -> None:
        self.rubrica = configurar.cargar_rubrica(self.ciclo, ruta)
        self.lbl_rubrica.setText(f"Rúbrica: {self.rubrica.nombre} ✓")

    def guardar_parametros(self) -> None:
        configurar.actualizar_parametros(
            self.ciclo, nombre=self.in_nombre.text().strip() or None,
            cantidad_preguntas=self.in_preguntas.value(),
        )

    # --- Handlers -----------------------------------------------------------
    def _guardar_clave(self) -> None:
        if self.in_clave.text().strip():
            self.guardar_clave(self.in_clave.text().strip())
            self.in_clave.clear()

    def _probar_conexion(self) -> None:
        ok, mensaje = probar_conexion()
        self.lbl_conexion.setText(("✓ " if ok else "✗ ") + mensaje)

    def _cargar_rubrica(self) -> None:
        ruta, _ = QFileDialog.getOpenFileName(self, "Elegir rúbrica", "", "YAML (*.yaml *.yml)")
        if ruta:
            try:
                self.cargar_rubrica(ruta)
            except Exception as e:  # noqa: BLE001 - se muestra al docente
                self.lbl_rubrica.setText(f"Rúbrica inválida: {e}")

    def _guardar_parametros(self) -> None:
        self.guardar_parametros()
