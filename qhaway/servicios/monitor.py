"""Monitoreo de consumo y presupuesto (MON-02/03/04).

Lógica de presupuesto y alerta, sin Qt: la vista `ui.monitor` solo la muestra.
Principio de MON-03: el sistema **advierte** al superar el umbral, pero **nunca
bloquea** un análisis por presupuesto — la decisión es del docente.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class EstadoPresupuesto:
    mes: str
    acumulado: float
    presupuesto: float
    umbral: float           # proporción (0.80 = 80%)
    alerta: bool
    proporcion: float

    def resumen(self) -> str:
        aviso = "  ⚠ supera el umbral" if self.alerta else ""
        return (
            f"{self.mes}: USD {self.acumulado:.2f} / {self.presupuesto:.2f} "
            f"({self.proporcion:.0%}){aviso}"
        )


def costo_evaluacion(ciclo, evaluacion_id: int) -> float:
    """Costo total estimado de una evaluación (MON-02)."""
    return ciclo.consumos.costo_de_evaluacion(evaluacion_id)


def estado_presupuesto(
    ciclo,
    *,
    presupuesto: float | None = None,
    umbral: float = 0.80,
    mes: str | None = None,
) -> EstadoPresupuesto:
    """Consumo del mes vs presupuesto, con alerta al superar el umbral (MON-03).

    NO bloquea: solo informa. Si no se pasa presupuesto, usa el del ciclo.
    """
    mes = mes or date.today().strftime("%Y-%m")
    if presupuesto is None:
        ciclo_row = ciclo.ciclos.obtener(ciclo.ciclo_id)
        presupuesto = ciclo_row.presupuesto_mensual if ciclo_row else 20.0

    acumulado = ciclo.consumos.costo_del_mes(mes)
    proporcion = (acumulado / presupuesto) if presupuesto > 0 else 0.0
    return EstadoPresupuesto(
        mes=mes,
        acumulado=acumulado,
        presupuesto=presupuesto,
        umbral=umbral,
        alerta=proporcion >= umbral,
        proporcion=proporcion,
    )


def historico(ciclo) -> list[dict]:
    """Histórico de consumo por mes (MON-04, exportable)."""
    return [
        {"mes": f["mes"], "costo": float(f["costo"]), "llamadas": f["llamadas"]}
        for f in ciclo.consumos.historico_por_mes()
    ]
