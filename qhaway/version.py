"""Identidad y metadatos de QHAWAY.

Un único lugar para la versión y los datos del proyecto: los usan la ventana
principal, la pestaña "Acerca de" y el empaquetado. Evita que la versión quede
desperdigada y desactualizada en varios archivos.
"""

from __future__ import annotations

__version__ = "1.0.0"

NOMBRE = "QHAWAY"
DESCRIPCION = "Asistente de corrección de proyectos grupales"
SIGNIFICADO = "«qhaway» en quechua: observar, mirar con atención."
PRINCIPIO = "La IA propone, el docente decide."

AUTOR = "Duarte, Christian Héctor"
INSTITUCION = "ISFT N.º 179"
MATERIA = "Algoritmos y Estructuras de Datos II"
LICENCIA = "MIT"
MODELO_IA = "claude-sonnet-4-6"


def titulo_ventana(nombre_ciclo: str = "") -> str:
    """Título de ventana consistente: 'QHAWAY 1.0.0 — <ciclo>'."""
    base = f"{NOMBRE} {__version__}"
    return f"{base} — {nombre_ciclo}" if nombre_ciclo else base
