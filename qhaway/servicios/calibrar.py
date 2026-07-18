"""Arnés de calibración (Etapa 9, disciplina de corridas de la Etapa 0.7).

Un evaluador no determinístico corrido una vez da un punto, no una medición. Este
arnés implementa la disciplina que definiste en la métrica 0.7:

* **N corridas por entrega** (por defecto 3), a temperatura 0.
* Agregación del nivel por criterio **por moda** (el mayoritario de las N).
* La métrica (C1 nota ±1, C3 valoración) se mide sobre el **agregado**.
* Se reporta el **peor caso** entre las corridas: si el agregado pasa pero una
  corrida individual tuvo una distancia 3, se registra como inestabilidad (falla
  de C3), porque el sistema no es confiable aunque en promedio acierte.

Nota de alcance: C2 (cobertura de hallazgos) y C4 (ruido) requieren el apareamiento
manual del docente y las métricas de revisión (REV-06); no se automatizan acá. El
arnés cubre C1 y C3, que sí son computables desde el esquema.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..dominio.calibracion import CasoCalibracion, Coincidencia, agregar_corridas, medir
from ..dominio.niveles import Nivel
from ..dominio.nota import calcular_nota
from ..dominio.rubrica import Rubrica
from .analizar_entrega import ContextoAnalisis, analizar_entrega


@dataclass(frozen=True)
class ResultadoCorrida:
    """Una corrida individual del pipeline sobre una entrega."""

    nota: int
    valoraciones: dict[str, Nivel]


@dataclass(frozen=True)
class ReporteEntrega:
    """Resultado de calibrar una entrega con N corridas."""

    caso_id: str
    corridas: int
    nota_agregada: int
    coincidencia: Coincidencia          # medida sobre el agregado por moda
    peor_distancia_3: int               # máxima distancia 3 en cualquier corrida
    inestable: bool                     # el agregado pasa C3 pero una corrida no

    def c1_ok(self) -> bool:
        return self.coincidencia.c1_nota_ok

    def c3_ok(self, *, umbral: float = 0.85) -> bool:
        # C3 exige el umbral en el agregado Y cero inestabilidad por peor caso.
        return self.coincidencia.c3_valoracion_ok(umbral=umbral) and not self.inestable

    def resumen(self) -> str:
        estado = "OK" if (self.c1_ok() and self.c3_ok()) else "REVISAR"
        inest = " · inestable (peor caso con distancia 3)" if self.inestable else ""
        return (
            f"[{estado}] {self.caso_id}: nota {self.nota_agregada} "
            f"(Δ{self.coincidencia.diferencia_nota}), "
            f"valoraciones ≤1: {self.coincidencia.proporcion_distancia_leq1:.0%}"
            f"{inest}"
        )


def agregar_y_medir(
    caso: CasoCalibracion, corridas: list[ResultadoCorrida], rubrica: Rubrica
) -> ReporteEntrega:
    """Agrega N corridas por moda y mide contra el caso docente (0.7)."""
    if not corridas:
        raise ValueError("No hay corridas para agregar.")

    # Agregación por moda del nivel por criterio.
    agregadas = agregar_corridas([c.valoraciones for c in corridas])
    nota_agregada = calcular_nota(rubrica, agregadas).nota
    coincidencia = medir(caso, nota_agregada, agregadas)

    # Peor caso: la mayor distancia 3 en cualquier corrida individual.
    peor = 0
    for corr in corridas:
        c = medir(caso, corr.nota, corr.valoraciones)
        peor = max(peor, c.distancia_3)

    inestable = peor > 0 and coincidencia.distancia_3 == 0

    return ReporteEntrega(
        caso_id=caso.id,
        corridas=len(corridas),
        nota_agregada=nota_agregada,
        coincidencia=coincidencia,
        peor_distancia_3=peor,
        inestable=inestable,
    )


@dataclass(frozen=True)
class ReporteSet:
    """Aceptación global sobre el subconjunto de calibración (regla 0.7)."""

    entregas: int
    c1_pasan: int                # cuántas entregas cumplen C1
    c3_pasan: int
    hay_distancia_3: bool        # alguna distancia 3 en cualquier lado = descalificante
    reportes: tuple[ReporteEntrega, ...] = field(default_factory=tuple)

    def aceptado(self, *, umbral_c1_set: float = 0.80) -> bool:
        """C1 en ≥80% de las entregas, C3 en todas, y cero distancia 3."""
        if self.entregas == 0:
            return False
        c1_ok = (self.c1_pasan / self.entregas) >= umbral_c1_set
        c3_ok = self.c3_pasan == self.entregas
        return c1_ok and c3_ok and not self.hay_distancia_3

    def resumen(self) -> str:
        veredicto = "ACEPTADO" if self.aceptado() else "NO ACEPTADO"
        return (
            f"Set de {self.entregas} entrega(s) — {veredicto}: "
            f"C1 {self.c1_pasan}/{self.entregas}, C3 {self.c3_pasan}/{self.entregas}"
            + (" · hay distancia 3 (descalificante)" if self.hay_distancia_3 else "")
        )


def resumir_set(reportes: list[ReporteEntrega]) -> ReporteSet:
    return ReporteSet(
        entregas=len(reportes),
        c1_pasan=sum(1 for r in reportes if r.c1_ok()),
        c3_pasan=sum(1 for r in reportes if r.c3_ok()),
        hay_distancia_3=any(r.coincidencia.distancia_3 > 0 or r.peor_distancia_3 > 0
                            for r in reportes),
        reportes=tuple(reportes),
    )


# ----------------------------------------------------------------------------
# Integración: correr el pipeline N veces sobre una entrega real
# ----------------------------------------------------------------------------
def correr_n_corridas(
    ciclo, grupo, entrega, contexto: ContextoAnalisis, conector, *, n: int = 3
) -> list[ResultadoCorrida]:
    """Corre el pipeline `n` veces (independientes) sobre una entrega.

    Usa `forzar_nueva` para que cada corrida sea una evaluación separada; no altera
    el estado de la entrega (es medición, no el flujo del docente).
    """
    resultados: list[ResultadoCorrida] = []
    for _ in range(n):
        r = analizar_entrega(ciclo, grupo, entrega, contexto, conector, forzar_nueva=True)
        almacenadas = ciclo.valoraciones.de_evaluacion(r.evaluacion_id)
        valoraciones = {
            cid: Nivel(v["nivel_ia"]) for cid, v in almacenadas.items() if v["nivel_ia"]
        }
        resultados.append(ResultadoCorrida(nota=r.nota, valoraciones=valoraciones))
    return resultados
