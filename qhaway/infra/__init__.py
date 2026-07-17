"""Infraestructura de QHAWAY (Etapa 2): persistencia SQLite + carpetas (AD-03).

Esta capa depende del dominio (importa la máquina de estados y, más adelante, el
cálculo de nota), pero el dominio NO depende de ésta: la flecha va en un solo
sentido (AD-02).
"""

from __future__ import annotations

from .ciclo import Ciclo, abrir_ciclo, crear_ciclo
from .almacen import ReporteIntegridad, Rutas
from .reconstruccion import ReporteReconstruccion, reconstruir_desde_carpetas
from .extraccion import FORMATOS_SOPORTADOS, ResultadoExtraccion, extraer
from .config import (
    CHECKLIST_DEFECTO,
    NOMENCLATURA_DEFECTO,
    cargar_checklist,
    cargar_nomenclatura,
)
from .conector_ia import (
    Conector,
    ConectorAnthropic,
    ConectorFalso,
    ErrorTransitorio,
    PoliticaReintentos,
    RegistroConsumo,
    RespuestaCruda,
    ResultadoLlamada,
    TablaPrecios,
)
from .config_usuario import (
    cargar_clave,
    dir_config_usuario,
    guardar_clave,
    probar_conexion,
)
from .prompts import (
    PLANTILLAS,
    PlantillaPrompt,
    PromptEnsamblado,
    VariableFaltante,
)

__all__ = [
    "Ciclo",
    "crear_ciclo",
    "abrir_ciclo",
    "Rutas",
    "ReporteIntegridad",
    "ReporteReconstruccion",
    "reconstruir_desde_carpetas",
    "FORMATOS_SOPORTADOS",
    "ResultadoExtraccion",
    "extraer",
    "CHECKLIST_DEFECTO",
    "NOMENCLATURA_DEFECTO",
    "cargar_checklist",
    "cargar_nomenclatura",
    "Conector",
    "ConectorAnthropic",
    "ConectorFalso",
    "ErrorTransitorio",
    "PoliticaReintentos",
    "RegistroConsumo",
    "RespuestaCruda",
    "ResultadoLlamada",
    "TablaPrecios",
    "cargar_clave",
    "dir_config_usuario",
    "guardar_clave",
    "probar_conexion",
    "PLANTILLAS",
    "PlantillaPrompt",
    "PromptEnsamblado",
    "VariableFaltante",
]
