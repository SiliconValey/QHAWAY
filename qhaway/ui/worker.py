"""Worker de análisis en hilo trabajador (AD-08, IEX-01).

El pipeline (`analizar_entrega`) corre en un `QThread` para no bloquear la UI; el
worker traduce el callback `on_progreso` del servicio en **señales de Qt**. La UI
solo reacciona a esas señales — nunca al revés, y el worker NUNCA toca widgets
(disciplina estricta de AD-08).

PySide6 se importa perezosamente: el resto del sistema (dominio, infra, servicios,
tests) no depende de Qt. Este archivo solo se activa cuando existe la UI (Etapa
7). La lógica que importa ya está testeada en el servicio con el callback; acá el
worker es un adaptador delgado hacia el mundo de Qt.
"""

from __future__ import annotations

from ..servicios import ContextoAnalisis, analizar_entrega


def crear_worker():
    """Devuelve la clase AnalisisWorker (requiere PySide6).

    Se construye dinámicamente para que importar este módulo no falle si PySide6
    no está instalado; la clase se define solo cuando la UI la pide.
    """
    from PySide6.QtCore import QThread, Signal  # perezoso

    class AnalisisWorker(QThread):
        # Señales hacia la UI (thread-safe por diseño de Qt).
        progreso = Signal(str, str)        # (unidad, estado)
        terminado = Signal(object)         # ResultadoPipeline
        error = Signal(str)

        def __init__(self, ciclo, grupo, entrega, contexto: ContextoAnalisis, conector):
            super().__init__()
            self._args = (ciclo, grupo, entrega, contexto, conector)

        def run(self) -> None:  # corre en el hilo trabajador
            ciclo, grupo, entrega, contexto, conector = self._args
            try:
                resultado = analizar_entrega(
                    ciclo, grupo, entrega, contexto, conector,
                    on_progreso=lambda unidad, estado: self.progreso.emit(unidad, estado),
                )
                self.terminado.emit(resultado)
            except Exception as e:  # noqa: BLE001 - se reporta a la UI vía señal
                self.error.emit(str(e))

    return AnalisisWorker
