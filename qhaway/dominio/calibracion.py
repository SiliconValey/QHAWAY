"""Métrica de coincidencia para la calibración de EVA (Etapa 0.7, sección 11).

Compara la salida del pipeline contra la evaluación docente conocida de una
entrega del ciclo anterior. Es el instrumento que responde la pregunta de la
Etapa 6: *¿QHAWAY evalúa como el docente?* Lógica pura: no corre el pipeline, solo
mide dos salidas ya producidas.

Qué mide:
* **Distancia de nota**: |nota_ia − nota_docente|.
* **Coincidencia de valoraciones**: por criterio, la distancia entre niveles en
  la escala ordinal (Insuficiente=0 … Excelente=3). Exactas (distancia 0),
  adyacentes (1) y lejanas (≥2) — las lejanas son las que importan revisar.

El umbral es configurable; el criterio de salida de la Etapa 6 es que la primera
pasada del subconjunto de iteración quede "a distancia razonable" del umbral.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from .niveles import Nivel

# Escala ordinal de los niveles, para medir distancia entre valoraciones.
ORDEN_NIVEL: dict[Nivel, int] = {
    Nivel.INSUFICIENTE: 0,
    Nivel.REGULAR: 1,
    Nivel.BUENO: 2,
    Nivel.EXCELENTE: 3,
}


def moda_nivel(niveles: list[Nivel]) -> Nivel:
    """Nivel mayoritario de una lista (agregación por moda, disciplina de corridas).

    En caso de empate, devuelve el de menor orden (criterio conservador: ante la
    duda, el nivel más bajo). Determinístico.
    """
    if not niveles:
        raise ValueError("No hay niveles para agregar.")
    conteo = Counter(niveles)
    tope = max(conteo.values())
    candidatos = [n for n, c in conteo.items() if c == tope]
    return min(candidatos, key=lambda n: ORDEN_NIVEL[n])


def agregar_corridas(corridas: list[dict[str, Nivel]]) -> dict[str, Nivel]:
    """Agrega N corridas por moda, criterio por criterio (Etapa 0.7)."""
    criterios = {cid for c in corridas for cid in c}
    return {
        cid: moda_nivel([c[cid] for c in corridas if cid in c])
        for cid in criterios
    }


@dataclass(frozen=True)
class CasoCalibracion:
    """La evaluación docente conocida de una entrega (la 'verdad' a comparar)."""

    id: str
    nota_docente: int
    valoraciones_docente: dict[str, Nivel]


@dataclass(frozen=True)
class Coincidencia:
    """Resultado de comparar una evaluación de IA contra el caso docente."""

    caso_id: str
    diferencia_nota: int
    exactas: int
    adyacentes: int
    lejanas: int
    distancia_3: int                     # inversión total de juicio (descalificante, C3)
    criterios_comparados: int
    distancia_promedio: float
    criterios_lejanos: tuple[str, ...]  # los que conviene revisar

    @property
    def proporcion_exactas(self) -> float:
        return self.exactas / self.criterios_comparados if self.criterios_comparados else 0.0

    @property
    def c1_nota_ok(self) -> bool:
        """C1: nota sugerida dentro de ±1 de la nota docente."""
        return self.diferencia_nota <= 1

    @property
    def proporcion_distancia_leq1(self) -> float:
        """Proporción de criterios con distancia ≤ 1 (igual o adyacente)."""
        if not self.criterios_comparados:
            return 0.0
        return (self.exactas + self.adyacentes) / self.criterios_comparados

    def c3_valoracion_ok(self, *, umbral: float = 0.85) -> bool:
        """C3: ≥ umbral de criterios con distancia ≤ 1 y CERO distancia 3."""
        return self.proporcion_distancia_leq1 >= umbral and self.distancia_3 == 0

    def dentro_umbral(self, *, umbral_nota: int = 1, umbral_distancia: float = 0.5) -> bool:
        return (
            self.diferencia_nota <= umbral_nota
            and self.distancia_promedio <= umbral_distancia
        )


def medir(
    caso: CasoCalibracion,
    nota_ia: int,
    valoraciones_ia: dict[str, Nivel],
) -> Coincidencia:
    """Compara una salida de IA contra el caso docente conocido."""
    exactas = adyacentes = lejanas = distancia_3 = 0
    suma_distancias = 0
    comparados = 0
    lejanos: list[str] = []

    # Solo se comparan los criterios presentes en ambos lados.
    for cid, nivel_doc in caso.valoraciones_docente.items():
        if cid not in valoraciones_ia:
            continue
        comparados += 1
        d = abs(ORDEN_NIVEL[valoraciones_ia[cid]] - ORDEN_NIVEL[nivel_doc])
        suma_distancias += d
        if d == 0:
            exactas += 1
        elif d == 1:
            adyacentes += 1
        else:
            lejanas += 1
            lejanos.append(cid)
            if d == 3:
                distancia_3 += 1  # Insuficiente↔Excelente: descalificante (C3)

    distancia_promedio = suma_distancias / comparados if comparados else 0.0

    return Coincidencia(
        caso_id=caso.id,
        diferencia_nota=abs(nota_ia - caso.nota_docente),
        exactas=exactas,
        adyacentes=adyacentes,
        lejanas=lejanas,
        distancia_3=distancia_3,
        criterios_comparados=comparados,
        distancia_promedio=distancia_promedio,
        criterios_lejanos=tuple(lejanos),
    )


@dataclass(frozen=True)
class ResumenCalibracion:
    """Agregado de la métrica sobre un conjunto de casos."""

    casos: int
    diferencia_nota_promedio: float
    proporcion_exactas: float
    distancia_promedio: float
    dentro_umbral: int

    def resumen(self) -> str:
        return (
            f"Calibración sobre {self.casos} caso(s): "
            f"Δnota promedio {self.diferencia_nota_promedio:.2f}, "
            f"valoraciones exactas {self.proporcion_exactas:.0%}, "
            f"distancia promedio {self.distancia_promedio:.2f}, "
            f"dentro del umbral {self.dentro_umbral}/{self.casos}."
        )


def resumir(
    coincidencias: list[Coincidencia],
    *,
    umbral_nota: int = 1,
    umbral_distancia: float = 0.5,
) -> ResumenCalibracion:
    """Agrega varias coincidencias en un resumen del subconjunto de calibración."""
    n = len(coincidencias)
    if n == 0:
        return ResumenCalibracion(0, 0.0, 0.0, 0.0, 0)
    total_criterios = sum(c.criterios_comparados for c in coincidencias)
    total_exactas = sum(c.exactas for c in coincidencias)
    return ResumenCalibracion(
        casos=n,
        diferencia_nota_promedio=sum(c.diferencia_nota for c in coincidencias) / n,
        proporcion_exactas=(total_exactas / total_criterios) if total_criterios else 0.0,
        distancia_promedio=sum(c.distancia_promedio for c in coincidencias) / n,
        dentro_umbral=sum(
            1 for c in coincidencias
            if c.dentro_umbral(umbral_nota=umbral_nota, umbral_distancia=umbral_distancia)
        ),
    )
