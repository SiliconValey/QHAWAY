"""Dominio puro de QHAWAY (Etapa 1).

Sin dependencias de infraestructura: nada de Qt, SDK de IA, red ni sistema de
archivos. Todo lo de acá se testea con pytest sin mocks (Arquitectura §11, AD-02).
"""

from __future__ import annotations

from .errores import (
    ErrorDominio,
    RubricaInvalida,
    TransicionInvalida,
    ValoracionFaltante,
)
from .estados import (
    Evaluacion,
    EstadoEvaluacion,
    puede_transicionar,
    transicionar,
    transiciones_validas,
)
from .niveles import (
    NOMBRES_CANONICOS,
    VALOR_POR_NIVEL,
    Nivel,
    nivel_desde_texto,
    valor_de,
)
from .nota import (
    AporteCriterio,
    ComposicionNota,
    calcular_nota,
    valoraciones_con_ausentes,
)
from .rubrica import ARTEFACTOS_EXPO1, Criterio, Rubrica, Seccion
from .contenido import ArbolUI, ContenidoDocumento, NodoUI, Referencia
from .deteccion import (
    CATEGORIA_DET,
    Bloque,
    ChecklistDocumento,
    ConvencionNomenclatura,
    HallazgoDET,
    ejecutar_det_documento,
    ejecutar_det_ui,
    verificar_completitud,
    verificar_elementos_formales,
    verificar_nomenclatura,
)
from .esquema_salidas import (
    ObservacionIA,
    PreguntaDefensa,
    ResultadoArtefacto,
    ResultadoTransversal,
    Senal,
    Validacion,
    ValoracionIA,
    parsear_json,
    validar_artefacto,
    validar_transversal,
)
from .clasificacion import Clasificacion, clasificar_texto
from .calibracion import (
    CasoCalibracion,
    Coincidencia,
    ResumenCalibracion,
    medir,
    resumir,
)

__all__ = [
    "ErrorDominio",
    "RubricaInvalida",
    "TransicionInvalida",
    "ValoracionFaltante",
    "Evaluacion",
    "EstadoEvaluacion",
    "puede_transicionar",
    "transicionar",
    "transiciones_validas",
    "NOMBRES_CANONICOS",
    "VALOR_POR_NIVEL",
    "Nivel",
    "nivel_desde_texto",
    "valor_de",
    "AporteCriterio",
    "ComposicionNota",
    "calcular_nota",
    "valoraciones_con_ausentes",
    "ARTEFACTOS_EXPO1",
    "Criterio",
    "Rubrica",
    "Seccion",
    "ArbolUI",
    "ContenidoDocumento",
    "NodoUI",
    "Referencia",
    "CATEGORIA_DET",
    "Bloque",
    "ChecklistDocumento",
    "ConvencionNomenclatura",
    "HallazgoDET",
    "ejecutar_det_documento",
    "ejecutar_det_ui",
    "verificar_completitud",
    "verificar_elementos_formales",
    "verificar_nomenclatura",
    "ObservacionIA",
    "PreguntaDefensa",
    "ResultadoArtefacto",
    "ResultadoTransversal",
    "Senal",
    "Validacion",
    "ValoracionIA",
    "parsear_json",
    "validar_artefacto",
    "validar_transversal",
    "CasoCalibracion",
    "Coincidencia",
    "ResumenCalibracion",
    "medir",
    "resumir",
    "Clasificacion",
    "clasificar_texto",
]
