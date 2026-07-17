"""Cálculo de la nota sugerida (EVA-05, EVA-06).

Propiedades de diseño:

* **Exacto y reproducible.** Se usa `fractions.Fraction`, no `float`: pesos y
  valores son enteros, así que el promedio ponderado es un racional exacto y la
  detección de "mitad exacta" no depende de la representación en punto flotante.
  Esto sostiene la reproducibilidad que el sistema promete (DET-05 la exige para
  la capa determinística; la nota hereda la misma garantía).

* **Redondeo de mitades hacia arriba.** Fijado en EVA-05 (v1.1): 6,5 -> 7. NO se
  usa `round()` de Python, que redondea al par ("bankers' rounding") y daría
  6,5 -> 6.

* **Trazable.** Devuelve `ComposicionNota` con el aporte de cada criterio, el
  peso efectivo normalizado (CFG-03) y si se aplicó el tope por crítico, para
  que el docente vea cómo se llega al número (EVA-05).
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from .errores import ValoracionFaltante
from .niveles import Nivel, valor_de
from .rubrica import Rubrica

# Escala institucional de la nota final (SRS 2.4: enteros de 1 a 10).
NOTA_MIN, NOTA_MAX = 1, 10


@dataclass(frozen=True)
class AporteCriterio:
    """El aporte de un criterio a la nota, para la vista de composición."""

    criterio_id: str
    nivel: Nivel
    valor: int
    peso: Fraction
    peso_efectivo: Fraction  # peso normalizado sobre el total (CFG-03)
    critico: bool


@dataclass(frozen=True)
class ComposicionNota:
    """Resultado trazable del cálculo de la nota sugerida."""

    nota: int
    promedio_ponderado: Fraction
    aportes: tuple[AporteCriterio, ...]
    tope_aplicado: bool
    tope: int
    criticos_insuficientes: tuple[str, ...]

    def explicacion(self) -> str:
        """Texto legible de cómo se compuso la nota (para el arnés CLI/REV)."""
        prom = float(self.promedio_ponderado)
        lineas = [
            f"Promedio ponderado: {prom:.4f}  ->  nota {self.nota}"
            + (" (redondeo de mitades hacia arriba)" if self._es_mitad() else "")
        ]
        if self.tope_aplicado:
            lineas.append(
                f"Tope por crítico aplicado: nota acotada a {self.tope} "
                f"por criterio(s) crítico(s) Insuficiente: "
                f"{', '.join(self.criticos_insuficientes)}."
            )
        for a in self.aportes:
            lineas.append(
                f"  {a.criterio_id}: {a.nivel.value} (valor {a.valor}) "
                f"× peso efectivo {float(a.peso_efectivo):.3f}"
                + ("  [crítico]" if a.critico else "")
            )
        return "\n".join(lineas)

    def _es_mitad(self) -> bool:
        resto = self.promedio_ponderado - int(self.promedio_ponderado)
        return resto == Fraction(1, 2)


def _redondear_mitad_arriba(x: Fraction) -> int:
    """Redondea un Fraction al entero más próximo, con las mitades hacia arriba.

    Para x >= 0 (el único caso posible: los valores están en [2, 10]):
    floor(x) + (1 si la parte fraccionaria es >= 1/2).
    """
    piso = x.numerator // x.denominator  # floor exacto para x >= 0
    resto = x - piso
    return piso + 1 if resto >= Fraction(1, 2) else piso


def valoraciones_con_ausentes(
    rubrica: Rubrica,
    valoraciones: dict[str, Nivel],
    artefactos_ausentes: set[str],
) -> dict[str, Nivel]:
    """Completa las valoraciones forzando Insuficiente en los artefactos ausentes.

    EVA-05: si un artefacto requerido está ausente (entrega parcial confirmada,
    ING-05), TODOS los criterios de su sección se valoran Insuficiente —incluidos
    los críticos— y nunca se excluyen del promedio. Los criterios transversales
    NO se tocan: no pertenecen a un artefacto único.
    """
    resultado = dict(valoraciones)
    for seccion in rubrica.secciones:
        if seccion.artefacto in artefactos_ausentes:
            for criterio in seccion.criterios:
                resultado[criterio.id] = Nivel.INSUFICIENTE
    return resultado


def calcular_nota(
    rubrica: Rubrica,
    valoraciones: dict[str, Nivel],
) -> ComposicionNota:
    """Calcula la nota sugerida como suma ponderada de las valoraciones.

    `valoraciones` mapea criterio_id -> Nivel y debe cubrir EXACTAMENTE los
    criterios de la rúbrica (ni faltantes ni sobrantes de más). Para artefactos
    ausentes, pasar las valoraciones ya completadas con
    `valoraciones_con_ausentes`.

    Levanta ValoracionFaltante si algún criterio de la rúbrica no tiene nivel.
    """
    criterios = rubrica.criterios()

    faltantes = [c.id for c in criterios if c.id not in valoraciones]
    if faltantes:
        raise ValoracionFaltante(
            "Faltan valoraciones para: " + ", ".join(faltantes) + "."
        )

    peso_total = sum((Fraction(c.peso) for c in criterios), Fraction(0))
    if peso_total <= 0:
        # No debería ocurrir con una rúbrica válida (pesos > 0), pero se
        # defiende el invariante para no dividir por cero.
        raise ValoracionFaltante("La suma de pesos de la rúbrica es cero.")

    suma = Fraction(0)
    aportes: list[AporteCriterio] = []
    criticos_insuf: list[str] = []

    for c in criterios:
        nivel = valoraciones[c.id]
        valor = valor_de(nivel)
        peso = Fraction(c.peso)
        suma += peso * valor
        aportes.append(
            AporteCriterio(
                criterio_id=c.id,
                nivel=nivel,
                valor=valor,
                peso=peso,
                peso_efectivo=peso / peso_total,
                critico=c.critico,
            )
        )
        if c.critico and nivel is Nivel.INSUFICIENTE:
            criticos_insuf.append(c.id)

    promedio = suma / peso_total
    nota = _redondear_mitad_arriba(promedio)
    nota = max(NOTA_MIN, min(NOTA_MAX, nota))  # acotar a la escala 1-10

    # Regla de criterio crítico (EVA-06): al menos un crítico Insuficiente
    # acota la nota al tope, independientemente de la suma ponderada.
    tope_aplicado = False
    if criticos_insuf and nota > rubrica.tope_por_critico:
        nota = rubrica.tope_por_critico
        tope_aplicado = True

    return ComposicionNota(
        nota=nota,
        promedio_ponderado=promedio,
        aportes=tuple(aportes),
        tope_aplicado=tope_aplicado,
        tope=rubrica.tope_por_critico,
        criticos_insuficientes=tuple(criticos_insuf),
    )
