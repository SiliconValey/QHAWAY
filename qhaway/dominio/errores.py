"""Excepciones propias del dominio.

Son errores de reglas de negocio, independientes de cualquier infraestructura
(no hay errores de IO, de red ni de la API acá: eso vive en las capas externas).
"""

from __future__ import annotations


class ErrorDominio(Exception):
    """Raíz de todos los errores del dominio."""


class RubricaInvalida(ErrorDominio):
    """La rúbrica no cumple las reglas de validación de CFG-01.

    Acumula todos los problemas encontrados en `problemas`, para que el docente
    pueda corregirlos de una sola vez en lugar de uno por corrida.
    """

    def __init__(self, problemas: list[str]) -> None:
        self.problemas = list(problemas)
        detalle = "; ".join(self.problemas)
        super().__init__(f"Rúbrica inválida ({len(self.problemas)}): {detalle}")


class ValoracionFaltante(ErrorDominio):
    """Falta la valoración de un criterio al calcular la nota.

    Cada criterio de la rúbrica debe recibir exactamente una valoración
    (esquema de salidas, regla 3; EVA-05).
    """


class TransicionInvalida(ErrorDominio):
    """Se intentó una transición de estado no permitida por la máquina."""
