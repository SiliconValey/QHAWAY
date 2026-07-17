"""Modelo de rúbrica y su validación (CFG-01, CFG-02).

El dominio trabaja sobre estructuras ya parseadas: `Rubrica.desde_dict` recibe
un diccionario como el que produce `yaml.safe_load` sobre el archivo YAML. La
lectura del archivo en sí es infraestructura (Etapa 2) y no vive acá — así el
dominio se testea con dicts literales, sin tocar el sistema de archivos.

Estructura esperada del dict (SRS, Apéndice A):

    rubrica:
      nombre: "..."
      escala:
        tope_por_critico: 6
      secciones:
        - artefacto: srs
          criterios:
            - id: SRS-REQ
              descripcion: "..."
              peso: 3
              critico: true            # opcional
              niveles:
                Insuficiente: "..."
                Regular: "..."
                Bueno: "..."
                Excelente: "..."
      transversales:
        criterios: [...]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from numbers import Real

from .errores import RubricaInvalida
from .niveles import NOMBRES_CANONICOS

# Artefactos requeridos por la Exposición 1 del MVP (configurable por exposición).
ARTEFACTOS_EXPO1: frozenset[str] = frozenset({"presentacion", "srs", "fd", "ui"})

# Nombre interno de la sección transversal.
TRANSVERSAL = "transversal"

# Rango válido del tope por criterio crítico (CFG-01).
TOPE_MIN, TOPE_MAX = 1, 10


@dataclass(frozen=True)
class Criterio:
    """Un criterio de evaluación dentro de una sección."""

    id: str
    descripcion: str
    peso: Real
    critico: bool = False
    niveles: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Seccion:
    """Una sección de la rúbrica: un artefacto, o la sección transversal."""

    artefacto: str
    criterios: tuple[Criterio, ...]


@dataclass(frozen=True)
class Rubrica:
    """Rúbrica completa y ya validada.

    Construir siempre vía `desde_dict`, que valida antes de instanciar: si el
    objeto existe, es válido (una rúbrica inválida nunca llega a usarse, CFG-01).
    """

    nombre: str
    tope_por_critico: int
    secciones: tuple[Seccion, ...]

    def criterios(self) -> list[Criterio]:
        """Todos los criterios, de todas las secciones, en orden."""
        return [c for s in self.secciones for c in s.criterios]

    def seccion(self, artefacto: str) -> Seccion | None:
        for s in self.secciones:
            if s.artefacto == artefacto:
                return s
        return None

    @classmethod
    def desde_dict(
        cls,
        datos: dict,
        *,
        artefactos_requeridos: frozenset[str] = ARTEFACTOS_EXPO1,
    ) -> "Rubrica":
        """Valida y construye una rúbrica a partir de un dict parseado.

        Levanta RubricaInvalida con TODOS los problemas encontrados si algo no
        cumple CFG-01. No se detiene en el primer error a propósito.
        """
        problemas: list[str] = []

        raiz = datos.get("rubrica") if isinstance(datos, dict) else None
        if not isinstance(raiz, dict):
            raise RubricaInvalida(["Falta la clave raíz 'rubrica' o no es un mapa."])

        nombre = raiz.get("nombre", "")

        # --- Tope por criterio crítico: entero dentro de [1, 10] ---
        escala = raiz.get("escala", {}) or {}
        tope = escala.get("tope_por_critico", 6)
        if not isinstance(tope, int) or isinstance(tope, bool):
            problemas.append(
                f"tope_por_critico debe ser un entero; se recibió {tope!r}."
            )
            tope = 6  # valor tentativo para poder seguir validando
        elif not (TOPE_MIN <= tope <= TOPE_MAX):
            problemas.append(
                f"tope_por_critico fuera de rango [{TOPE_MIN}, {TOPE_MAX}]: {tope}."
            )

        # --- Secciones por artefacto + transversales ---
        secciones: list[Seccion] = []
        artefactos_presentes: set[str] = set()
        ids_vistos: set[str] = set()

        crudas = list(raiz.get("secciones", []) or [])

        # La sección transversal viene en su propia clave; se normaliza a Seccion.
        transversales = raiz.get("transversales")
        if isinstance(transversales, dict):
            crudas.append({"artefacto": TRANSVERSAL, **transversales})

        for i, sec in enumerate(crudas):
            if not isinstance(sec, dict):
                problemas.append(f"La sección #{i + 1} no es un mapa.")
                continue
            artefacto = sec.get("artefacto", f"<sin-artefacto #{i + 1}>")
            artefactos_presentes.add(artefacto)

            criterios_crudos = sec.get("criterios", []) or []
            criterios: list[Criterio] = []
            for crit in criterios_crudos:
                c = cls._validar_criterio(crit, artefacto, ids_vistos, problemas)
                if c is not None:
                    criterios.append(c)
            secciones.append(Seccion(artefacto=artefacto, criterios=tuple(criterios)))

        # --- Artefactos requeridos por la exposición ---
        faltantes = artefactos_requeridos - artefactos_presentes
        if faltantes:
            problemas.append(
                "Faltan secciones para artefactos requeridos: "
                + ", ".join(sorted(faltantes))
                + "."
            )

        # --- La rúbrica debe tener al menos un criterio ---
        if not ids_vistos:
            problemas.append("La rúbrica no define ningún criterio.")

        if problemas:
            raise RubricaInvalida(problemas)

        return cls(
            nombre=nombre,
            tope_por_critico=tope,
            secciones=tuple(secciones),
        )

    @staticmethod
    def _validar_criterio(
        crit: object,
        artefacto: str,
        ids_vistos: set[str],
        problemas: list[str],
    ) -> Criterio | None:
        """Valida un criterio individual; acumula problemas y devuelve el
        Criterio si es estructuralmente construible, o None si no lo es."""
        if not isinstance(crit, dict):
            problemas.append(f"[{artefacto}] Un criterio no es un mapa: {crit!r}.")
            return None

        cid = crit.get("id")
        etiqueta = cid if cid else f"<sin-id en {artefacto}>"

        if not cid or not isinstance(cid, str):
            problemas.append(f"[{artefacto}] Criterio sin 'id' válido.")
        elif cid in ids_vistos:
            problemas.append(f"ID de criterio duplicado: {cid!r}.")
        else:
            ids_vistos.add(cid)

        # Peso: numérico y > 0 (los booleanos NO cuentan como numéricos).
        peso = crit.get("peso")
        if isinstance(peso, bool) or not isinstance(peso, Real):
            problemas.append(f"[{etiqueta}] 'peso' debe ser numérico; es {peso!r}.")
        elif peso <= 0:
            problemas.append(f"[{etiqueta}] 'peso' debe ser mayor que 0; es {peso}.")

        # Niveles: las claves deben ser EXACTAMENTE los cuatro canónicos.
        niveles = crit.get("niveles", {}) or {}
        if not isinstance(niveles, dict):
            problemas.append(f"[{etiqueta}] 'niveles' debe ser un mapa.")
            niveles = {}
        else:
            claves = set(niveles.keys())
            if claves != set(NOMBRES_CANONICOS):
                sobran = claves - NOMBRES_CANONICOS
                faltan = NOMBRES_CANONICOS - claves
                detalle = []
                if faltan:
                    detalle.append("faltan: " + ", ".join(sorted(faltan)))
                if sobran:
                    detalle.append("sobran: " + ", ".join(sorted(sobran)))
                problemas.append(
                    f"[{etiqueta}] Niveles no canónicos ({'; '.join(detalle)})."
                )

        critico = bool(crit.get("critico", False))

        return Criterio(
            id=cid if isinstance(cid, str) else "",
            descripcion=crit.get("descripcion", ""),
            peso=peso if (isinstance(peso, Real) and not isinstance(peso, bool)) else 0,
            critico=critico,
            niveles=dict(niveles),
        )
