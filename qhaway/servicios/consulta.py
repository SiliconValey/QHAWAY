"""Consulta de evaluaciones ya validadas (leer grupos evaluados).

Permite reabrir una evaluación validada sin recargar la entrega: listar las que
están validadas o exportadas, y reunir los datos para reexportar sus PDF. La
base ya guarda todo (tabla elemento, valoracion, evaluacion); esto es la lectura.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..dominio.estados import EstadoEvaluacion


@dataclass(frozen=True)
class EvaluacionValidada:
    """Fila de resumen de una evaluación ya validada."""

    evaluacion_id: int
    entrega_id: int
    grupo_id: int
    grupo_codigo: str
    grupo_nombre: str
    proyecto: str
    exposicion: int
    version: int
    nota_final: int | None
    fecha_validacion: str | None
    estado_entrega: str


_ESTADOS_EVALUADOS = (
    EstadoEvaluacion.EVALUACION_VALIDADA.value,
    EstadoEvaluacion.INFORME_EXPORTADO.value,
)


def listar_evaluados(ciclo) -> list[EvaluacionValidada]:
    """Lista las evaluaciones validadas/exportadas del ciclo, más recientes primero."""
    filas = ciclo.con.execute(
        """
        SELECT ev.id AS ev_id, ev.entrega_id, ev.nota_final, ev.fecha_validacion,
               en.grupo_id, en.exposicion, en.version, en.estado AS estado_entrega,
               g.codigo, g.nombre, g.proyecto
        FROM evaluacion ev
        JOIN entrega en ON en.id = ev.entrega_id
        JOIN grupo   g  ON g.id  = en.grupo_id
        WHERE en.estado IN (?, ?)
        ORDER BY ev.fecha_validacion DESC, ev.id DESC
        """,
        _ESTADOS_EVALUADOS,
    ).fetchall()
    return [
        EvaluacionValidada(
            evaluacion_id=f["ev_id"], entrega_id=f["entrega_id"], grupo_id=f["grupo_id"],
            grupo_codigo=f["codigo"], grupo_nombre=f["nombre"], proyecto=f["proyecto"] or "",
            exposicion=f["exposicion"], version=f["version"], nota_final=f["nota_final"],
            fecha_validacion=f["fecha_validacion"], estado_entrega=f["estado_entrega"],
        )
        for f in filas
    ]


def entrega_de(ciclo, entrega_id: int):
    """Reconstruye el objeto Entrega desde la base (para exportar)."""
    row = ciclo.con.execute("SELECT * FROM entrega WHERE id = ?", (entrega_id,)).fetchone()
    if row is None:
        return None

    class _Entrega:
        pass

    e = _Entrega()
    for k in row.keys():
        setattr(e, k, row[k])
    return e
