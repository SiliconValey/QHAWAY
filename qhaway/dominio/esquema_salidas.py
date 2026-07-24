"""Esquema de salidas de la IA y su validación (EVA-13, esquema Etapa 0.1).

Lógica pura de dominio: valida un dict (lo que devuelve el modelo, ya parseado a
JSON) contra el contrato de la Etapa 0.1. No sabe nada del SDK ni de la red —por
eso se testea sin gastar un token—. El conector (infra) llama a estas funciones
antes de dar por buena una respuesta; una respuesta que no valida se rechaza y se
reintenta (IEX-02), nunca se persiste (EVA-13).

Las siete reglas de validación (esquema Etapa 0.1, sección 3) están numeradas en
el código donde se aplican.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from .niveles import NOMBRES_CANONICOS, Nivel

MAX_PALABRAS_CITA = 25
TIPOS_OBSERVACION = frozenset({"fortaleza", "mejora"})


# ----------------------------------------------------------------------------
# Modelo de la salida (dataclasses que reflejan el contrato)
# ----------------------------------------------------------------------------
@dataclass(frozen=True)
class RefObservacion:
    ubicacion: str
    pagina: int | None = None
    cita: str | None = None


@dataclass(frozen=True)
class ValoracionIA:
    criterio_id: str
    nivel: Nivel
    justificacion: str


@dataclass(frozen=True)
class ObservacionIA:
    criterio_id: str
    tipo: str                      # fortaleza | mejora
    contenido: str
    referencia: RefObservacion


@dataclass(frozen=True)
class ResultadoArtefacto:
    artefacto: str
    valoraciones: tuple[ValoracionIA, ...]
    observaciones: tuple[ObservacionIA, ...]


@dataclass(frozen=True)
class Consistencia:
    tipo: str
    elemento: str
    hallazgo: str
    referencias: tuple[dict, ...] = ()


@dataclass(frozen=True)
class PreguntaDefensa:
    pregunta: str
    elemento: str
    artefacto: str
    intencion: str = ""


@dataclass(frozen=True)
class Senal:
    descripcion: str
    artefacto: str
    sugerencia: str = ""


@dataclass(frozen=True)
class ResultadoTransversal:
    consistencias: tuple[Consistencia, ...]
    preguntas_defensa: tuple[PreguntaDefensa, ...]
    senales: tuple[Senal, ...]
    valoraciones: tuple[ValoracionIA, ...] = ()   # criterios de trazabilidad (TRZ)


@dataclass(frozen=True)
class Validacion:
    """Resultado de validar una respuesta: el objeto válido, o los errores."""

    resultado: object | None
    errores: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.errores and self.resultado is not None


# ----------------------------------------------------------------------------
# Parseo tolerante del JSON del modelo
# ----------------------------------------------------------------------------
def parsear_json(texto: str) -> tuple[dict | None, str | None]:
    """Parsea el JSON del modelo, tolerante con texto o markdown alrededor.

    Estrategia: (1) intenta parsear directo; (2) si falla, quita cercas ```json;
    (3) si aún falla, extrae el objeto entre la primera '{' y la última '}'. Esto
    absorbe respuestas reales que vienen con preámbulo ("Aquí está el análisis:")
    o comentarios finales, sin relajar la validación posterior del esquema.

    Devuelve (dict, None) o (None, mensaje_de_error).
    """
    candidatos = []
    limpio = texto.strip()
    candidatos.append(limpio)
    # Sin cercas de markdown
    sin_cercas = re.sub(r"^```(?:json)?|```$", "", limpio, flags=re.MULTILINE).strip()
    candidatos.append(sin_cercas)
    # Recorte al objeto más externo
    ini, fin = sin_cercas.find("{"), sin_cercas.rfind("}")
    if ini != -1 and fin != -1 and fin > ini:
        candidatos.append(sin_cercas[ini:fin + 1])

    ultimo_error = "respuesta vacía"
    for cand in candidatos:
        if not cand:
            continue
        try:
            data = json.loads(cand)
        except json.JSONDecodeError as e:
            ultimo_error = str(e)
            continue
        if not isinstance(data, dict):
            ultimo_error = "la respuesta no es un objeto JSON"
            continue
        return data, None
    return None, f"JSON inválido: {ultimo_error}"


# ----------------------------------------------------------------------------
# Validación de la unidad por artefacto
# ----------------------------------------------------------------------------
def _validar_valoraciones(
    data: dict, criterios_esperados: set[str]
) -> tuple[list[ValoracionIA], list[str]]:
    """Valida el array 'valoraciones' contra los criterios esperados (reglas 1, 2, 3).

    Compartido por artefacto y transversal: ambos exigen exactamente una
    valoración canónica por criterio de su sección.
    """
    errores: list[str] = []
    valoraciones: list[ValoracionIA] = []
    ids_valorados: list[str] = []
    for v in data.get("valoraciones", []):
        cid = v.get("criterio_id")
        ids_valorados.append(cid)
        if cid not in criterios_esperados:  # regla 2
            errores.append(f"Valoración con criterio desconocido: {cid!r}.")
        nivel_txt = v.get("nivel")
        if nivel_txt not in NOMBRES_CANONICOS:  # regla 1
            errores.append(f"Nivel fuera del enum canónico: {nivel_txt!r}.")
        else:
            valoraciones.append(ValoracionIA(cid, Nivel(nivel_txt), v.get("justificacion", "")))

    faltantes = criterios_esperados - set(ids_valorados)  # regla 3
    if faltantes:
        errores.append("Faltan valoraciones para: " + ", ".join(sorted(faltantes)) + ".")
    duplicados = [c for c in set(ids_valorados) if ids_valorados.count(c) > 1]
    if duplicados:
        errores.append("Valoraciones duplicadas para: " + ", ".join(sorted(duplicados)) + ".")
    return valoraciones, errores


def validar_artefacto(data: dict, criterios_esperados: set[str]) -> Validacion:
    """Valida una respuesta `analisis_artefacto` (reglas 1, 2, 3, 5)."""
    artefacto = data.get("artefacto", "")

    # --- Valoraciones (reglas 1, 2, 3) ---
    valoraciones, errores = _validar_valoraciones(data, criterios_esperados)

    # --- Observaciones (regla 5) ---
    observaciones: list[ObservacionIA] = []
    for o in data.get("observaciones", []):
        cid = o.get("criterio_id")
        if cid not in criterios_esperados:
            errores.append(f"Observación con criterio desconocido: {cid!r}.")
        tipo = o.get("tipo")
        if tipo not in TIPOS_OBSERVACION:
            errores.append(f"Observación con tipo inválido: {tipo!r}.")
        ref = o.get("referencia") or {}
        ubicacion = ref.get("ubicacion")
        # Regla 5: ubicacion obligatoria; cita opcional pero ≤ 25 palabras.
        if not ubicacion:
            errores.append(f"Observación de {cid!r} sin 'referencia.ubicacion'.")
        cita = ref.get("cita")
        if cita and len(str(cita).split()) > MAX_PALABRAS_CITA:
            errores.append(
                f"Cita de {cid!r} excede {MAX_PALABRAS_CITA} palabras."
            )
        observaciones.append(
            ObservacionIA(
                criterio_id=cid,
                tipo=tipo,
                contenido=o.get("contenido", ""),
                referencia=RefObservacion(
                    ubicacion=ubicacion or "",
                    pagina=ref.get("pagina"),
                    cita=cita,
                ),
            )
        )

    if errores:
        return Validacion(resultado=None, errores=tuple(errores))

    return Validacion(
        resultado=ResultadoArtefacto(
            artefacto=artefacto,
            valoraciones=tuple(valoraciones),
            observaciones=tuple(observaciones),
        )
    )


# ----------------------------------------------------------------------------
# Validación de la unidad transversal
# ----------------------------------------------------------------------------
def validar_transversal(
    data: dict, criterios_esperados: set[str] = frozenset()
) -> Validacion:
    """Valida una respuesta `analisis_transversal` (reglas 4, 6, y valoraciones TRZ).

    Si la sección transversal de la rúbrica tiene criterios (trazabilidad), también
    exige una valoración por cada uno (reglas 1, 2, 3), igual que un artefacto.
    """
    errores: list[str] = []

    # Valoraciones de trazabilidad (solo si la sección transversal tiene criterios).
    valoraciones: list[ValoracionIA] = []
    if criterios_esperados:
        valoraciones, errores_val = _validar_valoraciones(data, criterios_esperados)
        errores.extend(errores_val)

    consistencias = tuple(
        Consistencia(
            tipo=c.get("tipo", ""),
            elemento=c.get("elemento", ""),
            hallazgo=c.get("hallazgo", ""),
            referencias=tuple(c.get("referencias", []) or ()),
        )
        for c in data.get("consistencias", [])
    )

    # Regla 4: toda pregunta debe referenciar un elemento nombrado no vacío (EVA-08).
    preguntas: list[PreguntaDefensa] = []
    for p in data.get("preguntas_defensa", []):
        elemento = (p.get("elemento") or "").strip()
        if not elemento:
            errores.append(
                f"Pregunta sin 'elemento' nombrado: {p.get('pregunta', '')[:40]!r} "
                "(EVA-08: no puede ser aplicable a cualquier entrega)."
            )
            continue
        preguntas.append(
            PreguntaDefensa(
                pregunta=p.get("pregunta", ""),
                elemento=elemento,
                artefacto=p.get("artefacto", ""),
                intencion=p.get("intencion", ""),
            )
        )

    # Regla 6: una señal nunca lleva criterio_id ni valoración.
    senales: list[Senal] = []
    for s in data.get("senales", []):
        if "criterio_id" in s or "nivel" in s:
            errores.append(
                "Una señal no puede llevar 'criterio_id' ni 'nivel' (EVA-09): "
                f"{s.get('descripcion', '')[:40]!r}."
            )
            continue
        senales.append(
            Senal(
                descripcion=s.get("descripcion", ""),
                artefacto=s.get("artefacto", ""),
                sugerencia=s.get("sugerencia", ""),
            )
        )

    if errores:
        return Validacion(resultado=None, errores=tuple(errores))

    return Validacion(
        resultado=ResultadoTransversal(
            consistencias=consistencias,
            preguntas_defensa=tuple(preguntas),
            senales=tuple(senales),
            valoraciones=tuple(valoraciones),
        )
    )
