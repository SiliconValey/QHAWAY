"""Verificación determinística — Capa 1 (DET-01..05).

Lógica pura: opera sobre el contenido ya extraído (`dominio.contenido`) más la
configuración (checklist, nomenclatura). Sin archivos, sin IA, sin red. Se testea
con estructuras literales.

Propiedad central (DET-05): **reproducible**. Mismas entradas + misma config →
exactamente el mismo reporte. Por eso todo recorrido es en orden estable (la
config se recorre en orden; el árbol `.ui`, en profundidad) y no se usan
estructuras cuyo orden de iteración sea incidental.

Los hallazgos se marcan con categoría propia, distinguible de las observaciones
de IA (DET-05).
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field

from .contenido import ArbolUI, ContenidoDocumento, Referencia

CATEGORIA_DET = "deterministico"


# ----------------------------------------------------------------------------
# Configuración (CFG-05, CFG-06) — el dominio la recibe ya parseada
# ----------------------------------------------------------------------------
@dataclass(frozen=True)
class Bloque:
    """Un bloque obligatorio del checklist, con sus sinónimos de título."""

    id: str
    palabras_clave: tuple[str, ...]   # sinónimos; se matchea por cualquiera (no por título exacto)


@dataclass(frozen=True)
class ChecklistDocumento:
    """Checklist de completitud para un tipo de artefacto (CFG-05, DET-02/03)."""

    tipo_artefacto: str
    bloques: tuple[Bloque, ...] = ()
    requiere_caratula: bool = False
    requiere_indice: bool = False
    requiere_secciones_numeradas: bool = False
    # Palabras que delatan una carátula en la primera página (DET-03).
    palabras_caratula: tuple[str, ...] = (
        "integrantes", "profesor", "materia", "instituto", "universidad", "comision",
    )
    palabras_indice: tuple[str, ...] = ("indice", "tabla de contenido", "contenido")


@dataclass(frozen=True)
class ConvencionNomenclatura:
    """Prefijos esperados por tipo de widget para el `.ui` (CFG-06, DET-04)."""

    prefijos: dict[str, str]                 # "QPushButton" -> "btn"
    # Clases estructurales que no se verifican (layouts, spacers, el form raíz).
    ignorar: frozenset[str] = frozenset({
        "QWidget", "QMainWindow", "QDialog", "QFrame",
        "QVBoxLayout", "QHBoxLayout", "QGridLayout", "QFormLayout", "QSpacerItem",
    })


# ----------------------------------------------------------------------------
# Hallazgo
# ----------------------------------------------------------------------------
@dataclass(frozen=True)
class HallazgoDET:
    """Un hallazgo de la capa determinística (categoría propia, DET-05)."""

    tipo: str                       # bloque_ausente|elemento_formal_ausente|nomenclatura_no_conforme
    artefacto: str
    detalle: str
    referencia: Referencia | None = None
    datos: dict = field(default_factory=dict)   # p. ej. nombre_actual/tipo_widget/prefijo_esperado
    categoria: str = CATEGORIA_DET


# ----------------------------------------------------------------------------
# Normalización de texto (acentos + mayúsculas) para el matcheo
# ----------------------------------------------------------------------------
def normalizar(texto: str) -> str:
    """Minúsculas, sin acentos, espacios colapsados — para matcheo robusto."""
    sin_acentos = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    return " ".join(sin_acentos.lower().split())


def _contiene_alguna(texto_norm: str, palabras: tuple[str, ...]) -> str | None:
    """Devuelve la primera palabra clave encontrada (normalizada), o None."""
    for p in palabras:
        if normalizar(p) in texto_norm:
            return p
    return None


# ----------------------------------------------------------------------------
# DET-02 — Completitud documental
# ----------------------------------------------------------------------------
def verificar_completitud(
    contenido: ContenidoDocumento, checklist: ChecklistDocumento
) -> list[HallazgoDET]:
    """Reporta cada bloque obligatorio ausente (DET-02).

    Un bloque está presente si alguno de sus sinónimos aparece en un título de
    sección; como respaldo, si aparece en el texto completo. Nunca se exige el
    título exacto (lección de la Etapa 0.2: los títulos varían).
    """
    titulos_norm = " || ".join(normalizar(s.titulo) for s in contenido.secciones)
    texto_norm = normalizar(contenido.texto)
    hallazgos: list[HallazgoDET] = []

    for bloque in checklist.bloques:
        en_titulo = _contiene_alguna(titulos_norm, bloque.palabras_clave)
        en_texto = en_titulo or _contiene_alguna(texto_norm, bloque.palabras_clave)
        if en_texto is None:
            hallazgos.append(
                HallazgoDET(
                    tipo="bloque_ausente",
                    artefacto=contenido.tipo_artefacto,
                    detalle=(
                        f"No se encontró el bloque obligatorio '{bloque.id}' "
                        f"(sinónimos buscados: {', '.join(bloque.palabras_clave)})."
                    ),
                    datos={"bloque": bloque.id},
                )
            )
    return hallazgos


# ----------------------------------------------------------------------------
# DET-03 — Elementos formales
# ----------------------------------------------------------------------------
def verificar_elementos_formales(
    contenido: ContenidoDocumento, checklist: ChecklistDocumento
) -> list[HallazgoDET]:
    """Verifica carátula, índice y secciones numeradas (DET-03)."""
    hallazgos: list[HallazgoDET] = []

    if checklist.requiere_caratula:
        base = normalizar(contenido.texto_primera_pagina or contenido.texto[:1500])
        if _contiene_alguna(base, checklist.palabras_caratula) is None:
            hallazgos.append(
                HallazgoDET(
                    tipo="elemento_formal_ausente",
                    artefacto=contenido.tipo_artefacto,
                    detalle="No se detectó carátula (faltan datos identificatorios en la primera página).",
                    datos={"elemento": "caratula"},
                )
            )

    if checklist.requiere_indice:
        texto_norm = normalizar(contenido.texto)
        titulos_norm = " || ".join(normalizar(s.titulo) for s in contenido.secciones)
        if (
            _contiene_alguna(titulos_norm, checklist.palabras_indice) is None
            and _contiene_alguna(texto_norm, checklist.palabras_indice) is None
        ):
            hallazgos.append(
                HallazgoDET(
                    tipo="elemento_formal_ausente",
                    artefacto=contenido.tipo_artefacto,
                    detalle="No se detectó índice ni tabla de contenido.",
                    datos={"elemento": "indice"},
                )
            )

    if checklist.requiere_secciones_numeradas:
        if not any(s.numerada for s in contenido.secciones):
            hallazgos.append(
                HallazgoDET(
                    tipo="elemento_formal_ausente",
                    artefacto=contenido.tipo_artefacto,
                    detalle="No se detectaron secciones numeradas.",
                    datos={"elemento": "secciones_numeradas"},
                )
            )
    return hallazgos


# ----------------------------------------------------------------------------
# DET-04 — Nomenclatura del .ui
# ----------------------------------------------------------------------------
def verificar_nomenclatura(
    arbol: ArbolUI, convencion: ConvencionNomenclatura
) -> list[HallazgoDET]:
    """Reporta cada objeto del `.ui` cuyo nombre no respeta el prefijo esperado (DET-04).

    Por cada no conforme informa: nombre actual, tipo de widget y prefijo esperado.
    """
    hallazgos: list[HallazgoDET] = []
    for nodo in arbol.widgets():
        if nodo.clase in convencion.ignorar:
            continue
        prefijo = convencion.prefijos.get(nodo.clase)
        if prefijo is None:
            continue  # clase sin convención definida: no se juzga
        nombre = nodo.nombre or ""
        if not nombre.startswith(prefijo):
            hallazgos.append(
                HallazgoDET(
                    tipo="nomenclatura_no_conforme",
                    artefacto=arbol.tipo_artefacto,
                    detalle=(
                        f"El objeto '{nombre or '(sin nombre)'}' ({nodo.clase}) "
                        f"no usa el prefijo esperado '{prefijo}'."
                    ),
                    referencia=Referencia(ubicacion=nombre or "(sin nombre)", objeto=nombre or None),
                    datos={
                        "nombre_actual": nombre,
                        "tipo_widget": nodo.clase,
                        "prefijo_esperado": prefijo,
                    },
                )
            )
    return hallazgos


# ----------------------------------------------------------------------------
# Orquestación por artefacto
# ----------------------------------------------------------------------------
def ejecutar_det_documento(
    contenido: ContenidoDocumento, checklist: ChecklistDocumento
) -> list[HallazgoDET]:
    """DET completo para un documento (completitud + elementos formales)."""
    return (
        verificar_completitud(contenido, checklist)
        + verificar_elementos_formales(contenido, checklist)
    )


def ejecutar_det_ui(
    arbol: ArbolUI, convencion: ConvencionNomenclatura
) -> list[HallazgoDET]:
    """DET completo para el `.ui` (nomenclatura)."""
    return verificar_nomenclatura(arbol, convencion)
