"""Modelo de contenido extraído (ING-04) — contrato puro entre capas.

`infra.extraccion` produce estas estructuras a partir de archivos reales; el
dominio (`deteccion`) las consume sin saber nada de PyMuPDF, python-docx ni XML.
El dominio define el contrato; la infraestructura lo implementa (AD-02: la flecha
de dependencia va de infra hacia dominio, nunca al revés).

Modelo de referencia (Etapa 0.2):
* `ubicacion`: sección/encabezado ("3 Requerimientos funcionales") o, para el
  `.ui`, el nombre del objeto.
* `pagina`: en PDF siempre existe (respaldo universal); en .docx no hay concepto
  de página, así que va `None`.
* `objeto`: nombre del widget, solo para hallazgos del `.ui`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Iterator


@dataclass(frozen=True)
class Referencia:
    """Ubicación verificable de un hallazgo o una observación."""

    ubicacion: str
    pagina: int | None = None
    objeto: str | None = None


@dataclass(frozen=True)
class Seccion:
    """Una sección detectada en un documento."""

    numero: str | None   # "3", "3.1"... None si el encabezado no está numerado
    titulo: str
    pagina: int | None
    texto: str = ""

    @property
    def numerada(self) -> bool:
        return self.numero is not None


@dataclass(frozen=True)
class ContenidoDocumento:
    """Contenido normalizado de un PDF o .docx (ING-04)."""

    tipo_artefacto: str          # presentacion|srs|fd|ui
    texto: str                   # texto completo normalizado
    secciones: tuple[Seccion, ...] = ()
    paginas: int | None = None   # None en .docx (no hay páginas hasta renderizar)
    texto_primera_pagina: str = ""  # para detectar carátula (DET-03)


@dataclass(frozen=True)
class NodoUI:
    """Un widget del árbol de objetos de un archivo .ui."""

    clase: str                   # p. ej. "QPushButton"
    nombre: str | None           # objectName; None si el widget no lo declara
    hijos: tuple["NodoUI", ...] = field(default_factory=tuple)

    def recorrer(self) -> Iterator["NodoUI"]:
        """Recorre el árbol en orden (depth-first, determinístico)."""
        yield self
        for h in self.hijos:
            yield from h.recorrer()


@dataclass(frozen=True)
class ArbolUI:
    """Contenido extraído de un archivo .ui (ING-04)."""

    tipo_artefacto: str
    raiz: NodoUI | None

    def widgets(self) -> Iterator[NodoUI]:
        if self.raiz is not None:
            yield from self.raiz.recorrer()
