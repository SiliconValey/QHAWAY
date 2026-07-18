"""Revisión y validación docente (REV-02..07, EXP-03).

Toda la lógica del flujo "la IA propone, el docente decide" vive acá, en la capa
de servicios, **sin Qt**: la UI (Etapa 7) es una capa delgada que llama a estas
funciones y refleja su resultado. Consecuencia directa: los flujos
aceptar/editar/descartar se testean con pytest normal, y la UI solo agrega los
tests de humo de que los botones llaman a lo correcto.

Estados de un elemento (REV-07, persistentes): pendiente → aceptado | editado |
descartado. Origen (REV-05, interno): ia_aceptado | ia_editado | docente.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..dominio.estados import EstadoEvaluacion, transicionar
from ..dominio.niveles import Nivel
from ..dominio.nota import calcular_nota
from ..dominio.rubrica import Rubrica
from ..infra.db import transaccion


# ----------------------------------------------------------------------------
# Operaciones sobre elementos (REV-02)
# ----------------------------------------------------------------------------
def aceptar(ciclo, elemento_id: int) -> None:
    """Acepta un elemento sin cambios: sobrevive tal cual (REV-02, origen ia_aceptado)."""
    el = ciclo.elementos.obtener(elemento_id)
    if el is None:
        raise KeyError(f"No existe el elemento {elemento_id}")
    with transaccion(ciclo.con):
        ciclo.elementos.actualizar_revision(
            elemento_id, "aceptado",
            contenido_final=el["contenido_original"], origen="ia_aceptado",
        )


def editar(ciclo, elemento_id: int, nuevo_contenido: str) -> None:
    """Edita un elemento: se conserva el original y se marca el origen (REV-02/05)."""
    if ciclo.elementos.obtener(elemento_id) is None:
        raise KeyError(f"No existe el elemento {elemento_id}")
    with transaccion(ciclo.con):
        ciclo.elementos.actualizar_revision(
            elemento_id, "editado", contenido_final=nuevo_contenido, origen="ia_editado",
        )


def descartar(ciclo, elemento_id: int) -> None:
    """Descarta un elemento: no aparece en las salidas (REV-02)."""
    if ciclo.elementos.obtener(elemento_id) is None:
        raise KeyError(f"No existe el elemento {elemento_id}")
    with transaccion(ciclo.con):
        ciclo.elementos.actualizar_revision(elemento_id, "descartado")


def agregar_elemento_docente(
    ciclo, evaluacion_id: int, tipo: str, contenido: str, *,
    criterio_id: str | None = None, referencia: str = "",
) -> int:
    """El docente agrega una observación o pregunta propia (REV-03, origen docente)."""
    with transaccion(ciclo.con):
        eid = ciclo.elementos.crear(
            evaluacion_id, tipo, criterio_id=criterio_id,
            contenido_original=contenido, origen="docente", referencia=referencia,
        )
        # Nace ya aceptado: es una decisión explícita del docente.
        ciclo.elementos.actualizar_revision(eid, "aceptado", contenido_final=contenido)
    return eid


# ----------------------------------------------------------------------------
# Ajuste de valoraciones y nota (REV-04)
# ----------------------------------------------------------------------------
def ajustar_valoracion(
    ciclo, evaluacion_id: int, criterio_id: str, nivel_final: Nivel, rubrica: Rubrica
) -> int:
    """Fija el nivel final de un criterio y recalcula la nota sugerida (REV-04).

    Devuelve la nueva nota sugerida. Se conserva el nivel de la IA (nivel_ia).
    """
    with transaccion(ciclo.con):
        ciclo.valoraciones.fijar_nivel_final(evaluacion_id, criterio_id, nivel_final.value)
    return _recalcular_nota_sugerida(ciclo, evaluacion_id, rubrica)


def _recalcular_nota_sugerida(ciclo, evaluacion_id: int, rubrica: Rubrica) -> int:
    """Recompone la nota usando el nivel_final donde exista, si no el nivel_ia."""
    almacenadas = ciclo.valoraciones.de_evaluacion(evaluacion_id)
    valoraciones = {
        cid: Nivel(v["nivel_final"] or v["nivel_ia"])
        for cid, v in almacenadas.items()
        if (v["nivel_final"] or v["nivel_ia"])
    }
    comp = calcular_nota(rubrica, valoraciones)
    with transaccion(ciclo.con):
        ciclo.evaluaciones.fijar_nota_sugerida(evaluacion_id, comp.nota)
    return comp.nota


def fijar_nota_final(ciclo, evaluacion_id: int, nota: int, fecha: str) -> None:
    """Fija la nota final del docente, distinta o no de la sugerida (REV-04).

    Registra ambas (la sugerida por composición ya está; esta es la decidida).
    No valida todavía: eso exige además cero pendientes (EXP-03).
    """
    with transaccion(ciclo.con):
        ciclo.con.execute(
            "UPDATE evaluacion SET nota_final = ?, fecha_validacion = ? WHERE id = ?",
            (nota, fecha, evaluacion_id),
        )


# ----------------------------------------------------------------------------
# Validación (EXP-03) — el guard que ya vive en la máquina de estados
# ----------------------------------------------------------------------------
def puede_validar(ciclo, evaluacion_id: int) -> tuple[bool, str]:
    """¿Se puede validar? Cero pendientes + nota final fijada (EXP-03)."""
    pendientes = ciclo.elementos.pendientes(evaluacion_id)
    if pendientes > 0:
        return False, f"Quedan {pendientes} elemento(s) pendiente(s) de revisión."
    fila = ciclo.evaluaciones.obtener(evaluacion_id)
    if fila is None or fila.nota_final is None:
        return False, "Falta confirmar la nota final."
    return True, "Lista para validar."


def validar(ciclo, entrega_id: int, evaluacion_id: int) -> None:
    """Valida la evaluación: transición borrador_en_revision → evaluacion_validada.

    El guard de EXP-03 lo aplica la propia máquina de estados del dominio.
    """
    pendientes = ciclo.elementos.pendientes(evaluacion_id)
    fila = ciclo.evaluaciones.obtener(evaluacion_id)
    nota_confirmada = fila is not None and fila.nota_final is not None

    estado_entrega = ciclo.con.execute(
        "SELECT estado FROM entrega WHERE id = ?", (entrega_id,)
    ).fetchone()["estado"]

    # La máquina levanta TransicionInvalida si el guard no se cumple.
    nuevo = transicionar(
        EstadoEvaluacion(estado_entrega),
        EstadoEvaluacion.EVALUACION_VALIDADA,
        elementos_pendientes=pendientes,
        nota_final_confirmada=nota_confirmada,
    )
    with transaccion(ciclo.con):
        ciclo.entregas.actualizar_estado(entrega_id, nuevo.value)
        ciclo.evaluaciones.actualizar_estado(evaluacion_id, nuevo.value)


# ----------------------------------------------------------------------------
# Métricas de retrabajo (REV-06)
# ----------------------------------------------------------------------------
@dataclass(frozen=True)
class MetricasRetrabajo:
    total: int
    aceptados_sin_cambios: int
    editados: int
    descartados: int
    agregados_docente: int

    def _pct(self, n: int) -> float:
        return (n / self.total) if self.total else 0.0

    def resumen(self) -> str:
        return (
            f"Retrabajo sobre {self.total} elemento(s): "
            f"aceptados {self._pct(self.aceptados_sin_cambios):.0%}, "
            f"editados {self._pct(self.editados):.0%}, "
            f"descartados {self._pct(self.descartados):.0%}, "
            f"agregados por el docente {self._pct(self.agregados_docente):.0%}."
        )


def metricas_retrabajo(ciclo, evaluacion_id: int) -> MetricasRetrabajo:
    """Porcentajes de aceptado/editado/descartado/agregado (REV-06).

    Es el instrumento de medición del criterio de éxito del MVP (calidad del
    borrador): cuanto menos retrabajo, mejor propone la IA.
    """
    conteo = ciclo.elementos.conteo_por_estado(evaluacion_id)
    total = sum(conteo.values())

    def suma(pred) -> int:
        return sum(n for clave, n in conteo.items() for est, ori in [clave.split("|")] if pred(est, ori))

    return MetricasRetrabajo(
        total=total,
        aceptados_sin_cambios=suma(lambda est, ori: est == "aceptado" and ori == "ia_aceptado"),
        editados=suma(lambda est, ori: est == "editado"),
        descartados=suma(lambda est, ori: est == "descartado"),
        agregados_docente=suma(lambda est, ori: ori == "docente"),
    )
