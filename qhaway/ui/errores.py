"""Manejo de errores no previstos (RNF-06).

Objetivo: que un fallo inesperado **nunca cierre la aplicación en silencio**. Se
muestra un diálogo con una explicación en lenguaje del docente, el detalle
técnico disponible para copiar, y se deja registro en un archivo de log.

La traducción de la excepción a mensaje es una función pura (`formatear_excepcion`),
testeable sin Qt; la parte gráfica es delgada.
"""

from __future__ import annotations

import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class InformeError:
    """Un error listo para mostrar: qué pasó, qué hacer, y el detalle técnico."""

    titulo: str
    mensaje: str          # en lenguaje del docente
    sugerencia: str       # qué puede intentar
    detalle: str          # traceback completo, para copiar/reportar

    def texto_completo(self) -> str:
        return f"{self.titulo}\n\n{self.mensaje}\n\n{self.sugerencia}\n\n---\n{self.detalle}"


# Traducciones de fallas frecuentes a lenguaje claro.
# (fragmento a buscar en el tipo o el mensaje) -> (mensaje, sugerencia)
_TRADUCCIONES: tuple[tuple[str, str, str], ...] = (
    (
        "ConnectionError",
        "No se pudo conectar con el servicio de IA.",
        "Revisá tu conexión a internet y volvé a intentar. El progreso del análisis "
        "quedó guardado: al reanudar, no se repite lo ya hecho.",
    ),
    (
        "Timeout",
        "El servicio de IA tardó demasiado en responder.",
        "Puede ser una demora pasajera. Volvé a intentar en unos minutos; el análisis "
        "se reanuda desde donde quedó.",
    ),
    (
        "PermissionError",
        "No se pudo acceder a un archivo porque el sistema lo tiene bloqueado.",
        "Cerrá el archivo si lo tenés abierto en otro programa (por ejemplo, un PDF "
        "abierto en el visor) y volvé a intentar.",
    ),
    (
        "FileNotFoundError",
        "No se encontró un archivo que la aplicación esperaba usar.",
        "Verificá que el archivo siga en su lugar y no haya sido movido o renombrado.",
    ),
    (
        "OperationalError",
        "Hubo un problema al leer o escribir en los datos del ciclo.",
        "Cerrá la aplicación y volvé a abrirla. Si el problema sigue, verificá que la "
        "carpeta del ciclo no esté abierta en otro programa.",
    ),
    (
        "JSONDecodeError",
        "Una respuesta del servicio de IA llegó incompleta o mal formada.",
        "Volvé a ejecutar el análisis: la aplicación reintenta automáticamente y "
        "retoma desde la unidad que falló.",
    ),
    (
        "MemoryError",
        "La aplicación se quedó sin memoria disponible.",
        "Cerrá otros programas y volvé a intentar. Si el documento es muy extenso, "
        "puede ayudar dividirlo.",
    ),
)

_GENERICO = (
    "Ocurrió un error inesperado.",
    "El trabajo guardado no se perdió. Si el problema se repite, copiá el detalle "
    "técnico y reportalo para poder corregirlo.",
)


def formatear_excepcion(exc_type, exc, tb) -> InformeError:
    """Traduce una excepción a un informe comprensible. Puro y testeable."""
    detalle = "".join(traceback.format_exception(exc_type, exc, tb)).strip()
    nombre = getattr(exc_type, "__name__", str(exc_type))
    firma = f"{nombre}: {exc}"

    for clave, mensaje, sugerencia in _TRADUCCIONES:
        if clave.lower() in firma.lower():
            return InformeError("QHAWAY — Error", mensaje, sugerencia, detalle)

    mensaje, sugerencia = _GENERICO
    return InformeError("QHAWAY — Error", mensaje, sugerencia, detalle)


def ruta_log() -> Path:
    """Archivo de registro de errores, junto a la configuración de usuario."""
    from ..infra.config_usuario import dir_config_usuario

    return dir_config_usuario() / "errores.log"


def registrar(informe: InformeError, *, ruta: Path | None = None) -> Path | None:
    """Agrega el error al log. Nunca levanta: registrar no debe romper nada."""
    try:
        destino = ruta or ruta_log()
        destino.parent.mkdir(parents=True, exist_ok=True)
        with destino.open("a", encoding="utf-8") as f:
            f.write(f"\n===== {datetime.now().isoformat(timespec='seconds')} =====\n")
            f.write(informe.detalle + "\n")
        return destino
    except Exception:  # noqa: BLE001 - el registro es best-effort
        return None


def mostrar(informe: InformeError, parent=None) -> None:
    """Muestra el error en un diálogo con el detalle técnico desplegable."""
    from PySide6.QtWidgets import QApplication, QMessageBox

    if QApplication.instance() is None:  # sin GUI, no hay nada que mostrar
        return
    caja = QMessageBox(parent)
    caja.setIcon(QMessageBox.Icon.Warning)
    caja.setWindowTitle(informe.titulo)
    caja.setText(informe.mensaje)
    caja.setInformativeText(informe.sugerencia)
    caja.setDetailedText(informe.detalle)
    caja.setStandardButtons(QMessageBox.StandardButton.Ok)
    caja.exec()


def instalar_manejador_global() -> None:
    """Instala el capturador de excepciones no manejadas (RNF-06).

    Sin esto, un fallo imprevisto cierra la ventana sin explicación. Con esto, el
    docente ve qué pasó, qué puede intentar, y queda registro para diagnóstico.
    """
    import sys

    anterior = sys.excepthook

    def _manejador(exc_type, exc, tb):
        if issubclass(exc_type, KeyboardInterrupt):  # Ctrl+C sigue funcionando
            anterior(exc_type, exc, tb)
            return
        informe = formatear_excepcion(exc_type, exc, tb)
        registrar(informe)
        try:
            mostrar(informe)
        except Exception:  # noqa: BLE001 - nunca dejar que el manejador falle
            anterior(exc_type, exc, tb)

    sys.excepthook = _manejador
