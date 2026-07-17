"""Plantillas de prompts como artefactos versionados (AD-07, sección 8).

Principios de diseño (arquitectura §8):
* Cada plantilla declara **qué variables recibe** (contrato explícito, verificable
  en tests): renderizar con una variable faltante es un error, no un hueco
  silencioso.
* Las instrucciones de comportamiento del SRS (EVA-03 calibración-no-plantilla,
  EVA-04 hallazgos no contradecibles, EVA-08 elemento nombrado, EVA-09 lenguaje
  de sugerencia) viven en el **texto** del prompt y son inspeccionables.
* El contexto se ensambla en el orden que maximiza el cacheo (EVA-12): primero lo
  **estable** (instrucciones, rúbrica, modelo), al final lo **variable** (la
  entrega del grupo). El conector marca los bloques estables para caché.
* Cada plantilla tiene **versión** en su encabezado; se incluye en el snapshot de
  cada evaluación (CFG-11). Un cambio de prompt exige re-correr la calibración.

Este módulo vive en `infra` porque produce el texto que consume el conector, pero
no conoce el SDK. Las plantillas de texto se guardan en `prompts/` del ciclo
(AD-07); acá están los defaults versionados y el ensamblador.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class VariableFaltante(Exception):
    """Se intentó renderizar una plantilla sin una variable declarada."""


@dataclass(frozen=True)
class BloquePrompt:
    """Un bloque del prompt, con marca de si es cacheable (estable)."""

    texto: str
    cacheable: bool  # True = estable entre unidades/entregas (se marca para caché)


@dataclass(frozen=True)
class PromptEnsamblado:
    """Resultado de renderizar una plantilla: bloques ordenados + texto plano."""

    bloques: tuple[BloquePrompt, ...]

    @property
    def texto(self) -> str:
        return "\n\n".join(b.texto for b in self.bloques)

    def bloques_cacheables(self) -> list[str]:
        return [b.texto for b in self.bloques if b.cacheable]


@dataclass(frozen=True)
class PlantillaPrompt:
    """Plantilla versionada con contrato de variables explícito."""

    nombre: str
    version: str
    variables: tuple[str, ...]           # el contrato: qué se debe pasar
    construir: object                    # Callable[[dict], tuple[BloquePrompt, ...]]

    def render(self, contexto: dict) -> PromptEnsamblado:
        faltantes = [v for v in self.variables if v not in contexto]
        if faltantes:
            raise VariableFaltante(
                f"Plantilla '{self.nombre}' v{self.version}: faltan variables "
                f"{', '.join(faltantes)}."
            )
        return PromptEnsamblado(bloques=tuple(self.construir(contexto)))


# ----------------------------------------------------------------------------
# Texto de instrucciones (las reglas del SRS en lenguaje natural, inspeccionables)
# ----------------------------------------------------------------------------
_ROL_EVALUADOR = (
    "Sos el asistente de evaluación de un docente de ingeniería de software. "
    "Evaluás la entrega de un grupo contra la rúbrica dada. Devolvés únicamente "
    "JSON válido en el esquema indicado, sin texto fuera del JSON."
)

_CALIBRACION_NO_PLANTILLA = (  # EVA-03
    "El proyecto modelo es SOLO referencia del nivel de calidad esperado, NO una "
    "plantilla: una solución distinta pero correcta no se penaliza por diferir "
    "del modelo. Evaluás cumplimiento de criterios, no parecido al modelo."
)

_HALLAZGOS_DET = (  # EVA-04
    "Los hallazgos determinísticos que siguen son hechos ya verificados: NO los "
    "contradigas ni los vuelvas a detectar. Podés elaborarlos (p. ej. explicar el "
    "impacto de un bloque faltante), pero no negarlos."
)

_REFERENCIAS = (  # EVA-01
    "Toda observación debe incluir una referencia con 'ubicacion' (sección o "
    "elemento identificable; en UI, el nombre del objeto). 'pagina' y 'cita' son "
    "opcionales: si NO conocés la página con certeza, poné null — NUNCA la "
    "inventes. La 'cita' debe ser textual y de ≤ 25 palabras."
)

_REGLA_PREGUNTAS = (  # EVA-08
    "Generá {cantidad_preguntas} preguntas de defensa, cada una referida a un "
    "elemento NOMBRADO de la entrega de ESTE grupo (un requisito concreto, una "
    "pantalla, un objeto de la UI, una decisión documentada). Una pregunta "
    "aplicable a cualquier entrega NO es válida: el campo 'elemento' es obligatorio."
)

_REGLA_SENALES = (  # EVA-09
    "Podés marcar señales para indagar: aspectos llamativos, en lenguaje de "
    "SUGERENCIA y nunca de veredicto o acusación. Las señales no llevan criterio "
    "ni nivel y no influyen en la nota."
)


# ----------------------------------------------------------------------------
# Constructores de las plantillas
# ----------------------------------------------------------------------------
def _formatear_rubrica(seccion_criterios: list[dict]) -> str:
    lineas = ["Rúbrica de la sección (criterios y descripciones por nivel):"]
    for c in seccion_criterios:
        lineas.append(f"- {c['id']}: {c.get('descripcion', '')}")
        for nivel, desc in (c.get("niveles") or {}).items():
            lineas.append(f"    {nivel}: {desc}")
    return "\n".join(lineas)


def _formatear_hallazgos(hallazgos: list[dict]) -> str:
    if not hallazgos:
        return "(sin hallazgos determinísticos para este artefacto)"
    return "\n".join(f"- [{h.get('tipo')}] {h.get('detalle')}" for h in hallazgos)


def _construir_artefacto(ctx: dict) -> tuple[BloquePrompt, ...]:
    """analisis_artefacto: estable primero (rol, rúbrica, modelo), variable al final."""
    return (
        # --- Bloques estables (cacheables): se repiten entre grupos ---
        BloquePrompt(_ROL_EVALUADOR, cacheable=True),
        BloquePrompt(_CALIBRACION_NO_PLANTILLA, cacheable=True),
        BloquePrompt(_REFERENCIAS, cacheable=True),
        BloquePrompt(_formatear_rubrica(ctx["criterios"]), cacheable=True),
        BloquePrompt(f"Proyecto modelo (referencia de calidad):\n{ctx['modelo']}", cacheable=True),
        BloquePrompt(
            "Formato de salida OBLIGATORIO: objeto JSON 'analisis_artefacto' con "
            "'artefacto', 'valoraciones' (una por criterio, con nivel canónico y "
            "justificacion) y 'observaciones' (con referencia).",
            cacheable=True,
        ),
        # --- Bloques variables (no cacheables): cambian con cada grupo ---
        BloquePrompt(f"{_HALLAZGOS_DET}\n{_formatear_hallazgos(ctx['hallazgos_det'])}", cacheable=False),
        BloquePrompt(f"Artefacto '{ctx['artefacto']}' del grupo a evaluar:\n{ctx['entrega']}", cacheable=False),
    )


def _construir_transversal(ctx: dict) -> tuple[BloquePrompt, ...]:
    """analisis_transversal: instrucciones estables, entrega y resultados variables."""
    entrega = "\n\n".join(f"[{t}]\n{txt}" for t, txt in ctx["entrega"].items())
    return (
        BloquePrompt(_ROL_EVALUADOR, cacheable=True),
        BloquePrompt(
            "Verificá la trazabilidad entre artefactos (EVA-07): cada requisito "
            "del SRS reflejado en el diseño funcional; cada pantalla del diseño "
            "presente en la UI. Reportá cada inconsistencia con sus elementos.",
            cacheable=True,
        ),
        BloquePrompt(_REGLA_PREGUNTAS.format(cantidad_preguntas=ctx["cantidad_preguntas"]), cacheable=True),
        BloquePrompt(_REGLA_SENALES, cacheable=True),
        BloquePrompt(
            "Formato de salida OBLIGATORIO: objeto JSON 'analisis_transversal' con "
            "'consistencias', 'preguntas_defensa' (con 'elemento' nombrado) y 'senales'.",
            cacheable=True,
        ),
        BloquePrompt(f"Entrega completa del grupo:\n{entrega}", cacheable=False),
    )


# ----------------------------------------------------------------------------
# Plantillas versionadas (defaults; en producción se leen de prompts/ del ciclo)
# ----------------------------------------------------------------------------
PLANTILLA_ARTEFACTO = PlantillaPrompt(
    nombre="analisis_artefacto",
    version="1.0",
    variables=("artefacto", "criterios", "modelo", "hallazgos_det", "entrega"),
    construir=_construir_artefacto,
)

PLANTILLA_TRANSVERSAL = PlantillaPrompt(
    nombre="analisis_transversal",
    version="1.0",
    variables=("entrega", "cantidad_preguntas"),
    construir=_construir_transversal,
)

PLANTILLAS = {
    "analisis_artefacto": PLANTILLA_ARTEFACTO,
    "analisis_transversal": PLANTILLA_TRANSVERSAL,
}
