"""Flujo completo por grupo (IEX-01): cargar → analizar → revisar → exportar.

Orquesta las cuatro etapas del trabajo del docente sobre un grupo, en una sola
ventana. El análisis corre en el worker de Qt (no bloquea la UI); el resto delega
en los servicios ya existentes. Los métodos públicos (`ejecutar_analisis`,
`exportar`) son testeables de forma síncrona con un conector falso.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..servicios import analizar_entrega, configurar, exportar
from .entrega import VistaEntrega
from .revision import VistaRevision


class VentanaGrupo(QWidget):
    def __init__(self, ciclo, grupo, rubrica, exposicion: int = 1, parent=None):
        super().__init__(parent)
        self.ciclo = ciclo
        self.grupo = grupo
        self.rubrica = rubrica
        self.exposicion = exposicion
        self.evaluacion_id: int | None = None
        self._worker = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            f"<b>{grupo.codigo}</b> — {grupo.nombre} ({grupo.proyecto}) · "
            f"Exposición {exposicion}", self))

        # Etapa 1: carga de entrega
        self.vista_entrega = VistaEntrega(ciclo, grupo, exposicion, self)
        layout.addWidget(self.vista_entrega)

        # Etapa 2: análisis
        fila = QHBoxLayout()
        self.btn_analizar = QPushButton("Analizar entrega vigente", self)
        self.btn_analizar.setProperty("class", "primario")
        self.btn_analizar.clicked.connect(self._analizar_real)
        fila.addWidget(self.btn_analizar)
        layout.addLayout(fila)

        self.barra = QProgressBar(self); self.barra.setRange(0, 5); self.barra.setValue(0)
        layout.addWidget(self.barra)
        self.lbl_progreso = QLabel("", self)
        layout.addWidget(self.lbl_progreso)

        # Etapa 3-4: revisión y exportación (aparecen tras el análisis)
        self.btn_revisar = QPushButton("Abrir revisión", self)
        self.btn_exportar = QPushButton("Exportar informe + guía", self)
        self.btn_exportar.setProperty("class", "primario")
        self.btn_revisar.clicked.connect(self.abrir_revision)
        self.btn_exportar.clicked.connect(self._exportar)
        self.btn_revisar.setEnabled(False)
        self.btn_exportar.setEnabled(False)
        layout.addWidget(self.btn_revisar)
        layout.addWidget(self.btn_exportar)

        self._vista_revision = None
        self._cargar_evaluacion_existente()

    def _cargar_evaluacion_existente(self) -> None:
        """Si ya hay una evaluación para la entrega vigente, la retoma (reabrir app)."""
        entrega = self._entrega_vigente()
        if entrega is None:
            return
        fila = self.ciclo.con.execute(
            "SELECT id FROM evaluacion WHERE entrega_id = ? ORDER BY id DESC LIMIT 1",
            (entrega.id,),
        ).fetchone()
        if fila is not None:
            self.evaluacion_id = fila["id"]
            self._habilitar_post_analisis()
            self.lbl_progreso.setText("Hay una evaluación en curso: «Abrir revisión» la retoma.")

    def _entrega_vigente(self):
        return self.ciclo.entregas.vigente(self.grupo.id, self.exposicion)

    # --- Métodos públicos testeables ----------------------------------------
    def ejecutar_analisis(self, conector) -> int:
        """Corre el pipeline de forma síncrona (para tests / uso sin hilo)."""
        entrega = self._entrega_vigente()
        if entrega is None:
            raise ValueError("No hay una entrega vigente para analizar.")
        contexto = configurar.cargar_contexto(self.ciclo, self.rubrica)
        resultado = analizar_entrega(self.ciclo, self.grupo, entrega, contexto, conector)
        self.evaluacion_id = resultado.evaluacion_id
        self._habilitar_post_analisis()
        return resultado.evaluacion_id

    def abrir_revision(self):
        """Abre la vista de revisión de la evaluación actual."""
        if self.evaluacion_id is None:
            return None
        entrega = self._entrega_vigente()
        self._vista_revision = VistaRevision(
            self.ciclo, entrega.id, self.evaluacion_id, self.rubrica)
        self._vista_revision.setWindowTitle(f"Revisión — {self.grupo.codigo}")
        self._vista_revision.resize(800, 600)
        self._vista_revision.show()
        return self._vista_revision

    def exportar(self):
        """Exporta el informe de grupo y la guía de defensa (requiere validación)."""
        entrega = self._entrega_vigente()
        informe = exportar.exportar_informe_grupo(
            self.ciclo, self.grupo, entrega, self.evaluacion_id, self.rubrica)
        guia = exportar.exportar_guia_defensa(
            self.ciclo, self.grupo, entrega, self.evaluacion_id)
        return informe, guia

    # --- Uso real: análisis en el worker ------------------------------------
    def _analizar_real(self) -> None:
        entrega = self._entrega_vigente()
        if entrega is None:
            QMessageBox.warning(self, "QHAWAY", "Cargá una entrega primero.")
            return
        try:
            conector = self._conector()
        except Exception as e:  # noqa: BLE001
            QMessageBox.warning(self, "Sin conexión", str(e))
            return

        from .worker import crear_worker
        contexto = configurar.cargar_contexto(self.ciclo, self.rubrica)
        Worker = crear_worker()
        self._worker = Worker(self.ciclo, self.grupo, entrega, contexto, conector)
        self._worker.progreso.connect(self._on_progreso)
        self._worker.terminado.connect(self._on_terminado)
        self._worker.error.connect(lambda m: QMessageBox.warning(self, "Error", m))
        self.btn_analizar.setEnabled(False)
        self._worker.start()

    def _conector(self):
        from ..infra.config_usuario import cargar_clave
        from ..infra.conector_ia import ConectorAnthropic
        clave = cargar_clave()
        if not clave:
            raise RuntimeError("No hay clave de API configurada (pestaña Configuración).")
        return ConectorAnthropic(clave)

    def _on_progreso(self, unidad: str, estado: str) -> None:
        self.lbl_progreso.setText(f"{unidad}: {estado}")
        if estado == "completado":
            self.barra.setValue(self.barra.value() + 1)

    def _on_terminado(self, resultado) -> None:
        self.evaluacion_id = resultado.evaluacion_id
        self.btn_analizar.setEnabled(True)
        self._habilitar_post_analisis()
        if resultado.estado_final == "analisis_interrumpido":
            unidad = resultado.unidad_fallida or "una unidad"
            motivo = "\n".join(resultado.errores) or "sin detalle"
            self.lbl_progreso.setText(
                f"Interrumpido en '{unidad}'. Reanudá con «Analizar» para retomar."
            )
            QMessageBox.warning(
                self, "Análisis interrumpido",
                f"La unidad '{unidad}' no pudo completarse tras los reintentos.\n\n"
                f"Motivo:\n{motivo}\n\n"
                "El progreso se guardó: «Analizar entrega vigente» reanuda desde ahí "
                "sin repagar lo ya hecho.",
            )
        else:
            self.lbl_progreso.setText(
                f"Análisis {resultado.estado_final} · nota sugerida: {resultado.nota}")

    def _habilitar_post_analisis(self) -> None:
        self.btn_revisar.setEnabled(True)
        self.btn_exportar.setEnabled(True)

    def _exportar(self) -> None:
        try:
            informe, guia = self.exportar()
            QMessageBox.information(self, "QHAWAY",
                                    f"Exportado:\n{informe.name}\n{guia.name}")
        except exportar.NoValidada:
            QMessageBox.warning(self, "Falta validar",
                                "Validá la evaluación en la revisión antes de exportar (EXP-03).")
        except Exception as e:  # noqa: BLE001
            QMessageBox.warning(self, "Error al exportar", str(e))
