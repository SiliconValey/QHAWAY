"""Exportación de informes (EXP-01..04).

Reúne los datos de una evaluación **validada**, aplica los filtros de cada
informe, renderiza el HTML (infra.informes) y lo convierte a PDF, archivándolo en
la carpeta de la versión (EXP-04).

Filtros clave (EXP-01): el informe al grupo se presenta como devolución unificada
de la cátedra — **sin** señales para indagar, **sin** cuestionario de defensa y
**sin** marcas de origen (REV-05). Todo eso va, por separado, en la guía de
defensa del docente (EXP-02).

Guard (EXP-03): solo se exporta desde una evaluación validada.
"""

from __future__ import annotations

from pathlib import Path

from ..dominio.estados import EstadoEvaluacion
from ..dominio.rubrica import Rubrica
from ..infra.informes import html_a_pdf, renderizar_guia_defensa, renderizar_informe_grupo

# Estados de revisión que sí se incluyen en las salidas (REV-02).
_VALIDADOS = ("aceptado", "editado")

_TITULOS = {
    "presentacion": "Presentación de empresa",
    "srs": "Especificación de requisitos (SRS)",
    "fd": "Diseño funcional",
    "ui": "Interfaz de usuario",
}


class NoValidada(Exception):
    """Se intentó exportar una evaluación que no está validada (EXP-03)."""


# ----------------------------------------------------------------------------
# Informe de devolución para el grupo (EXP-01)
# ----------------------------------------------------------------------------
def exportar_informe_grupo(
    ciclo, grupo, entrega, evaluacion_id: int, rubrica: Rubrica, *, fecha: str = ""
) -> Path:
    _verificar_validada(ciclo, entrega, evaluacion_id)
    contexto = _contexto_grupo(ciclo, grupo, entrega, evaluacion_id, rubrica, fecha)
    html = renderizar_informe_grupo(contexto)
    ruta = _ruta_informe(ciclo, grupo, entrega, "informe-grupo.pdf")
    return html_a_pdf(html, ruta)


def _contexto_grupo(ciclo, grupo, entrega, evaluacion_id, rubrica, fecha) -> dict:
    ev = ciclo.evaluaciones.obtener(evaluacion_id)
    elementos = ciclo.elementos.de_evaluacion(evaluacion_id)

    # Solo observaciones aceptadas/editadas. NUNCA señales ni preguntas (EXP-01).
    observaciones = [
        e for e in elementos
        if e["tipo"] == "observacion" and e["estado_revision"] in _VALIDADOS
    ]

    # criterio_id presente -> observación de artefacto; ausente -> consistencia.
    crit_a_artefacto = {
        c.id: s.artefacto for s in rubrica.secciones for c in s.criterios
    }
    hallazgos_por_art = _hallazgos_por_artefacto(ciclo, evaluacion_id)

    artefactos = []
    for seccion in rubrica.secciones:
        if seccion.artefacto == "transversal":
            continue
        obs_art = [
            {"contenido": _texto(o), "referencia": o["referencia"]}
            for o in observaciones
            if o["criterio_id"] and crit_a_artefacto.get(o["criterio_id"]) == seccion.artefacto
        ]
        halls = hallazgos_por_art.get(seccion.artefacto, [])
        if obs_art or halls:
            artefactos.append({
                "titulo": _TITULOS.get(seccion.artefacto, seccion.artefacto),
                "observaciones": obs_art,
                "hallazgos": halls,
            })

    consistencia = [
        {"contenido": _texto(o), "referencia": o["referencia"]}
        for o in observaciones if not o["criterio_id"]
    ]

    return {
        "grupo": grupo.codigo,
        "proyecto": grupo.proyecto or grupo.nombre,
        "exposicion": entrega.exposicion,
        "fecha": fecha,
        "nota_final": ev.nota_final if ev else "",
        "artefactos": artefactos,
        "consistencia": consistencia,
    }


# ----------------------------------------------------------------------------
# Guía de defensa para el docente (EXP-02)
# ----------------------------------------------------------------------------
def exportar_guia_defensa(
    ciclo, grupo, entrega, evaluacion_id: int, *, fecha: str = ""
) -> Path:
    _verificar_validada(ciclo, entrega, evaluacion_id)
    elementos = ciclo.elementos.de_evaluacion(evaluacion_id)

    preguntas = [
        {"contenido": _texto(e), "referencia": e["referencia"]}
        for e in elementos
        if e["tipo"] == "pregunta_defensa" and e["estado_revision"] in _VALIDADOS
    ]
    senales = [
        {"contenido": _texto(e)}
        for e in elementos
        if e["tipo"] == "senal" and e["estado_revision"] in _VALIDADOS
    ]

    contexto = {
        "grupo": grupo.codigo,
        "proyecto": grupo.proyecto or grupo.nombre,
        "exposicion": entrega.exposicion,
        "preguntas": preguntas,
        "senales": senales,
    }
    html = renderizar_guia_defensa(contexto)
    ruta = _ruta_informe(ciclo, grupo, entrega, "guia-defensa.pdf")
    return html_a_pdf(html, ruta)


# ----------------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------------
def _verificar_validada(ciclo, entrega, evaluacion_id) -> None:
    estado = ciclo.con.execute(
        "SELECT estado FROM entrega WHERE id = ?", (entrega.id,)
    ).fetchone()["estado"]
    if estado != EstadoEvaluacion.EVALUACION_VALIDADA.value:
        raise NoValidada(
            "Solo se puede exportar desde una evaluación validada (EXP-03); "
            f"la entrega está en estado '{estado}'."
        )


def _hallazgos_por_artefacto(ciclo, evaluacion_id) -> dict[str, list[str]]:
    resultado: dict[str, list[str]] = {}
    for h in ciclo.hallazgos.de_evaluacion(evaluacion_id):
        resultado.setdefault(h["artefacto"], []).append(h["detalle"])
    return resultado


def _texto(elemento) -> str:
    return elemento["contenido_final"] or elemento["contenido_original"]


def _ruta_informe(ciclo, grupo, entrega, nombre: str) -> Path:
    cv = ciclo.carpeta_version(grupo, entrega.exposicion, entrega.version)
    return cv / "informes" / nombre   # EXP-04: archivado en la versión
