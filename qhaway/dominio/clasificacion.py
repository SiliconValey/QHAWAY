"""Clasificación de artefactos por contenido (ING-03) — lógica pura.

Sugiere el tipo de un documento (presentacion / srs / fd) a partir de señales de
su texto, para que el docente confirme en vez de adivinar. El `.ui` no pasa por
acá: se detecta por extensión (es inequívoco).

Filosofía: son heurísticas de SUGERENCIA, no un veredicto. Devuelven un ranking
con puntajes; la decisión final es del docente (la vista muestra la sugerencia
pero deja cambiarla). La lección de QuipuIA/SIMI: un documento titulado "Diseño
Funcional" puede ser en realidad un SRS —por eso se puntúa por señales de
contenido, no por el título—.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .deteccion import normalizar

# Señales por tipo: (patrón regex sobre texto normalizado, peso).
_SENALES: dict[str, list[tuple[str, int]]] = {
    "srs": [
        (r"\brf-?\d", 3),                       # RF-01, RF 01...
        (r"\brnf-?\d", 3),                      # RNF-01...
        (r"requerimientos? funcionales", 3),
        (r"requerimientos? no funcionales", 3),
        (r"requisitos? funcionales", 3),
        (r"especificacion de requisitos", 3),
        (r"ieee ?830", 2),
        (r"criterios? de aceptacion", 1),
        (r"restricciones", 1),
    ],
    "fd": [
        (r"diseno funcional", 3),
        (r"pantalla", 2),
        (r"flujo de (estados|procesamiento|navegacion)", 2),
        (r"maquina de estados", 2),
        (r"nomenclatura", 1),
        (r"objectname|widget|qpushbutton|qlabel", 2),  # habla de componentes de UI
        (r"comportamiento de (cada|los) control", 2),
        (r"trazad[oa] a (los )?requerimientos", 1),
    ],
    "presentacion": [
        (r"mision", 2),
        (r"vision", 2),
        (r"quienes somos", 3),
        (r"a que nos dedicamos", 3),
        (r"nuestros servicios", 3),
        (r"contacto", 1),
        (r"empresa|organizacion", 1),
    ],
}

# Umbral mínimo de puntaje para animarse a sugerir un tipo.
_UMBRAL_SUGERENCIA = 3


@dataclass(frozen=True)
class Clasificacion:
    """Sugerencia de tipo con su puntaje y el ranking completo."""

    tipo_sugerido: str | None            # None si ninguna señal supera el umbral
    puntajes: dict[str, int] = field(default_factory=dict)
    confiable: bool = False              # el líder supera al segundo con holgura

    @property
    def motivo(self) -> str:
        if self.tipo_sugerido is None:
            return "Sin señales claras: elegí el tipo manualmente."
        return f"Sugerido '{self.tipo_sugerido}' (puntaje {self.puntajes.get(self.tipo_sugerido, 0)})."


def clasificar_texto(texto: str) -> Clasificacion:
    """Clasifica un documento por su texto. Puro y determinístico (ING-03)."""
    norm = normalizar(texto)
    puntajes: dict[str, int] = {}
    for tipo, senales in _SENALES.items():
        total = 0
        for patron, peso in senales:
            if re.search(patron, norm):
                total += peso
        puntajes[tipo] = total

    ordenados = sorted(puntajes.items(), key=lambda kv: kv[1], reverse=True)
    lider, punt_lider = ordenados[0]
    segundo = ordenados[1][1] if len(ordenados) > 1 else 0

    if punt_lider < _UMBRAL_SUGERENCIA:
        return Clasificacion(tipo_sugerido=None, puntajes=puntajes, confiable=False)

    # Confiable si el líder le saca al menos 3 puntos al segundo.
    return Clasificacion(
        tipo_sugerido=lider,
        puntajes=puntajes,
        confiable=(punt_lider - segundo) >= 3,
    )
