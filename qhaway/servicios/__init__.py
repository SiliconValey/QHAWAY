"""Servicios de aplicación de QHAWAY (orquestación de casos de uso, AD-02).

Esta capa coordina dominio + infraestructura para ejecutar casos de uso
completos. No contiene reglas de negocio (esas viven en `dominio`) ni detalles de
persistencia (esos viven en `infra`): las orquesta.
"""

from __future__ import annotations

from .analizar_entrega import (
    ContextoAnalisis,
    ResultadoPipeline,
    analizar_entrega,
)
from . import revision, monitor

__all__ = [
    "ContextoAnalisis",
    "ResultadoPipeline",
    "analizar_entrega",
    "revision",
    "monitor",
]
