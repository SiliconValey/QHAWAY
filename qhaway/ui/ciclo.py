"""Vista de ciclo y ABM de grupos (GRP-01/02/08).

Capa delgada sobre `servicios.gestion`: la vista recolecta datos y delega. Sus
métodos públicos (`alta_grupo`, `archivar_grupo`) son testeables con pytest-qt.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..servicios import gestion
from .dialogos import confirmar


class VistaCiclo(QWidget):
    def __init__(self, ciclo, parent=None):
        super().__init__(parent)
        self.ciclo = ciclo

        layout = QVBoxLayout(self)

        # Fila de alta rápida
        fila = QHBoxLayout()
        self.in_codigo = QLineEdit(self); self.in_codigo.setPlaceholderText("Código (G01)")
        self.in_nombre = QLineEdit(self); self.in_nombre.setPlaceholderText("Nombre del grupo")
        self.in_proyecto = QLineEdit(self); self.in_proyecto.setPlaceholderText("Proyecto")
        self.btn_alta = QPushButton("Alta de grupo", self)
        self.btn_alta.setProperty("class", "primario")
        self.btn_alta.clicked.connect(self._alta_desde_form)
        for w in (self.in_codigo, self.in_nombre, self.in_proyecto, self.btn_alta):
            fila.addWidget(w)
        layout.addLayout(fila)

        self.tabla = QTableWidget(0, 4, self)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setHorizontalHeaderLabels(["Código", "Nombre", "Proyecto", "Integrantes"])
        layout.addWidget(self.tabla)

        botones = QHBoxLayout()
        self.btn_flujo = QPushButton("Abrir flujo del grupo →", self)
        self.btn_flujo.setProperty("class", "primario")
        self.btn_integrante = QPushButton("Agregar integrante", self)
        self.btn_archivar = QPushButton("Archivar grupo", self)
        self.btn_flujo.clicked.connect(self._abrir_flujo_seleccionado)
        self.btn_integrante.clicked.connect(self._agregar_integrante_seleccionado)
        self.btn_archivar.clicked.connect(self._archivar_seleccionado)
        botones.addWidget(self.btn_flujo)
        botones.addWidget(self.btn_integrante); botones.addWidget(self.btn_archivar)
        layout.addLayout(botones)
        self._ventana_flujo = None

        self._ids: list[int] = []
        self.confirmar = confirmar   # sustituible en tests
        self.refrescar()

    def refrescar(self) -> None:
        from datetime import date
        grupos = gestion.listar_grupos(self.ciclo)
        self._ids = [g.id for g in grupos]
        self.tabla.setRowCount(len(grupos))
        hoy = date.today().isoformat()
        for fila, g in enumerate(grupos):
            integrantes = ", ".join(gestion.composicion(self.ciclo, g.id, hoy))
            for col, val in enumerate([g.codigo, g.nombre, g.proyecto, integrantes]):
                self.tabla.setItem(fila, col, QTableWidgetItem(str(val)))

    def _grupo_seleccionado(self) -> int | None:
        fila = self.tabla.currentRow()
        return self._ids[fila] if 0 <= fila < len(self._ids) else None

    # --- Métodos públicos testeables ----------------------------------------
    def alta_grupo(self, codigo: str, nombre: str, proyecto: str = "",
                   integrantes: list[str] | None = None) -> int:
        gid = gestion.alta_grupo(self.ciclo, codigo, nombre, proyecto, integrantes=integrantes)
        self.refrescar()
        return gid

    def agregar_integrante(self, grupo_id: int, nombre: str) -> None:
        gestion.agregar_integrante(self.ciclo, grupo_id, nombre)
        self.refrescar()

    def archivar_grupo(self, grupo_id: int) -> None:
        gestion.archivar_grupo(self.ciclo, grupo_id)
        self.refrescar()

    # --- Handlers -----------------------------------------------------------
    def _alta_desde_form(self) -> None:
        codigo = self.in_codigo.text().strip()
        nombre = self.in_nombre.text().strip()
        if codigo and nombre:
            self.alta_grupo(codigo, nombre, self.in_proyecto.text().strip())
            self.in_codigo.clear(); self.in_nombre.clear(); self.in_proyecto.clear()

    def _agregar_integrante_seleccionado(self) -> None:
        gid = self._grupo_seleccionado()
        if gid is None:
            return
        nombre, ok = QInputDialog.getText(self, "Agregar integrante", "Nombre:")
        if ok and nombre.strip():
            self.agregar_integrante(gid, nombre.strip())

    def _archivar_seleccionado(self) -> None:
        gid = self._grupo_seleccionado()
        if gid is None:
            return
        grupo = self.ciclo.grupos.obtener(gid)
        if not self.confirmar(
            f"¿Archivar el grupo {grupo.codigo} — {grupo.nombre}?",
            titulo="Archivar grupo",
            detalle="Dejará de aparecer en la lista. Sus entregas y evaluaciones se "
                    "conservan: no se borra nada.",
            parent=self, texto_aceptar="Sí, archivar",
        ):
            return
        self.archivar_grupo(gid)

    def _abrir_flujo_seleccionado(self) -> None:
        from PySide6.QtWidgets import QMessageBox

        from ..servicios import configurar
        from .flujo import VentanaGrupo

        gid = self._grupo_seleccionado()
        if gid is None:
            return
        rubrica = configurar.rubrica_activa(self.ciclo)
        if rubrica is None:
            QMessageBox.warning(self, "Falta rúbrica",
                                "Cargá una rúbrica en la pestaña Configuración primero.")
            return
        grupo = self.ciclo.grupos.obtener(gid)
        self._ventana_flujo = VentanaGrupo(self.ciclo, grupo, rubrica)
        self._ventana_flujo.setWindowTitle(f"QHAWAY — {grupo.codigo}")
        self._ventana_flujo.resize(760, 640)
        self._ventana_flujo.show()
