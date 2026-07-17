"""Niveles de valoración canónicos y su mapeo a valores numéricos.

Los cuatro niveles son FIJOS en el MVP (SRS, Apéndice A y CFG-01): una rúbrica
o una respuesta de IA que valore fuera de estos cuatro es inválida.

El mapeo nivel -> valor proviene del ejemplo del SRS (Apéndice B / EVA-05):
Insuficiente=2, Regular=5, Bueno=8, Excelente=10. Es fijo en el MVP; su
parametrización por rúbrica queda para la Fase 3.
"""

from __future__ import annotations

from enum import Enum


class Nivel(str, Enum):
    """Los cuatro niveles cualitativos canónicos."""

    INSUFICIENTE = "Insuficiente"
    REGULAR = "Regular"
    BUENO = "Bueno"
    EXCELENTE = "Excelente"


# Mapeo fijo nivel -> valor en la escala interna (SRS, Apéndice B).
VALOR_POR_NIVEL: dict[Nivel, int] = {
    Nivel.INSUFICIENTE: 2,
    Nivel.REGULAR: 5,
    Nivel.BUENO: 8,
    Nivel.EXCELENTE: 10,
}

# Conjunto de nombres canónicos, para validación (CFG-01, EVA-13).
NOMBRES_CANONICOS: frozenset[str] = frozenset(n.value for n in Nivel)


def nivel_desde_texto(texto: str) -> Nivel:
    """Convierte un texto al Nivel canónico correspondiente.

    Levanta ValueError si el texto no es uno de los cuatro niveles canónicos.
    La comparación es exacta (sensible a mayúsculas): la rúbrica y las salidas
    de la IA deben usar los nombres canónicos tal cual.
    """
    try:
        return Nivel(texto)
    except ValueError as exc:
        raise ValueError(
            f"Nivel no canónico: {texto!r}. "
            f"Los válidos son: {', '.join(n.value for n in Nivel)}."
        ) from exc


def valor_de(nivel: Nivel) -> int:
    """Devuelve el valor numérico asociado a un nivel."""
    return VALOR_POR_NIVEL[nivel]
