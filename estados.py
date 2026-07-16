"""Máquina de estados de una evaluación (GRP-06, Arquitectura §6).

Cadena de estados:

    sin_entrega -> entrega_cargada -> analizando
        -> [analisis_interrumpido <-> analizando]
        -> borrador_en_revision -> evaluacion_validada -> informe_exportado

Reglas codificadas:
* `analizando -> analisis_interrumpido`: falla agotados los reintentos (IEX-02)
  o cierre de la aplicación. Reanudable: `analisis_interrumpido -> analizando`.
* `borrador_en_revision -> evaluacion_validada`: exige cero elementos pendientes
  y nota final confirmada (EXP-03). Ese guard se valida acá mismo.

Nota: un re-análisis sobre una evaluación en revisión crea una EVALUACIÓN NUEVA
(GRP-04); eso lo maneja el servicio, no esta máquina, que gobierna el ciclo de
vida de UNA evaluación y es siempre hacia adelante.
"""

from __future__ import annotations

from enum import Enum

from .errores import TransicionInvalida


class EstadoEvaluacion(str, Enum):
    SIN_ENTREGA = "sin_entrega"
    ENTREGA_CARGADA = "entrega_cargada"
    ANALIZANDO = "analizando"
    ANALISIS_INTERRUMPIDO = "analisis_interrumpido"
    BORRADOR_EN_REVISION = "borrador_en_revision"
    EVALUACION_VALIDADA = "evaluacion_validada"
    INFORME_EXPORTADO = "informe_exportado"


_E = EstadoEvaluacion

# Transiciones permitidas: desde -> conjunto de destinos válidos.
_TRANSICIONES: dict[EstadoEvaluacion, frozenset[EstadoEvaluacion]] = {
    _E.SIN_ENTREGA: frozenset({_E.ENTREGA_CARGADA}),
    _E.ENTREGA_CARGADA: frozenset({_E.ANALIZANDO}),
    _E.ANALIZANDO: frozenset({_E.ANALISIS_INTERRUMPIDO, _E.BORRADOR_EN_REVISION}),
    _E.ANALISIS_INTERRUMPIDO: frozenset({_E.ANALIZANDO}),
    _E.BORRADOR_EN_REVISION: frozenset({_E.EVALUACION_VALIDADA}),
    _E.EVALUACION_VALIDADA: frozenset({_E.INFORME_EXPORTADO}),
    _E.INFORME_EXPORTADO: frozenset(),
}


def transiciones_validas(desde: EstadoEvaluacion) -> frozenset[EstadoEvaluacion]:
    """Destinos permitidos desde un estado dado."""
    return _TRANSICIONES[desde]


def puede_transicionar(desde: EstadoEvaluacion, hasta: EstadoEvaluacion) -> bool:
    """True si la transición está permitida estructuralmente (sin evaluar guards)."""
    return hasta in _TRANSICIONES[desde]


def transicionar(
    desde: EstadoEvaluacion,
    hasta: EstadoEvaluacion,
    *,
    elementos_pendientes: int | None = None,
    nota_final_confirmada: bool | None = None,
) -> EstadoEvaluacion:
    """Ejecuta una transición, validando estructura y guards.

    Para `borrador_en_revision -> evaluacion_validada` se exige (EXP-03):
    `elementos_pendientes == 0` y `nota_final_confirmada is True`. Si faltan esos
    datos o no se cumplen, se levanta TransicionInvalida.

    Devuelve el nuevo estado (== `hasta`) si todo es válido.
    """
    if not puede_transicionar(desde, hasta):
        permitidas = ", ".join(sorted(e.value for e in _TRANSICIONES[desde])) or "—"
        raise TransicionInvalida(
            f"Transición no permitida: {desde.value} -> {hasta.value}. "
            f"Desde {desde.value} solo se puede ir a: {permitidas}."
        )

    if desde is EstadoEvaluacion.BORRADOR_EN_REVISION and (
        hasta is EstadoEvaluacion.EVALUACION_VALIDADA
    ):
        if elementos_pendientes is None or nota_final_confirmada is None:
            raise TransicionInvalida(
                "Validar una evaluación exige informar 'elementos_pendientes' y "
                "'nota_final_confirmada' (guard EXP-03)."
            )
        if elementos_pendientes != 0:
            raise TransicionInvalida(
                f"No se puede validar: quedan {elementos_pendientes} elemento(s) "
                f"pendiente(s) de revisión (EXP-03)."
            )
        if not nota_final_confirmada:
            raise TransicionInvalida(
                "No se puede validar: falta confirmar la nota final (EXP-03)."
            )

    return hasta


class Evaluacion:
    """Envoltura opcional con estado mutable, útil para el arnés CLI y la UI.

    El estado siempre pasa por `transicionar`, así que los invariantes valen
    igual que en la función pura.
    """

    def __init__(self, estado: EstadoEvaluacion = EstadoEvaluacion.SIN_ENTREGA) -> None:
        self.estado = estado

    def a(self, hasta: EstadoEvaluacion, **guards) -> EstadoEvaluacion:
        self.estado = transicionar(self.estado, hasta, **guards)
        return self.estado

    def __repr__(self) -> str:  # pragma: no cover - conveniencia
        return f"Evaluacion(estado={self.estado.value!r})"
