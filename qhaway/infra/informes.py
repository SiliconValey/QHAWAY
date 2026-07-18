"""Informes por plantilla HTML → PDF (AD-09).

Jinja2 para rellenar plantillas + WeasyPrint para convertir a PDF (motor validado
en la PoC de la Etapa 0.4). Las plantillas son configurables editando HTML/CSS
(CFG-09) sin tocar código: por defecto van las de acá (tema claro imprimible),
pero `renderizar_*` acepta un HTML de plantilla alternativo, y en producción se
leen de `plantillas/` del ciclo.

WeasyPrint se importa perezosamente: el resto del sistema no depende de él, y los
tests que solo verifican el HTML corren sin necesidad del motor PDF.
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, select_autoescape

_env = Environment(autoescape=select_autoescape(["html", "xml"]))


# ----------------------------------------------------------------------------
# Plantillas por defecto (tema claro imprimible; CFG-09 permite reemplazarlas)
# ----------------------------------------------------------------------------
_CSS_BASE = """
@page { size: A4; margin: 2cm; }
body { font-family: 'DejaVu Sans', sans-serif; color: #1a1a2e; font-size: 11pt; line-height: 1.5; }
h1 { color: #16213e; border-bottom: 3px solid #0f3460; padding-bottom: 6px; }
h2 { color: #0f3460; margin-top: 1.4em; border-bottom: 1px solid #ccc; padding-bottom: 3px; }
h3 { color: #533483; margin-bottom: 0.2em; }
.meta { color: #555; font-size: 10pt; margin-bottom: 1em; }
.nota { font-size: 22pt; font-weight: bold; color: #16213e; }
.nota-caja { background: #f0f0f5; border-left: 5px solid #0f3460; padding: 10px 16px; margin: 1em 0; }
.obs { margin: 0.4em 0 0.9em 0; }
.obs .ref { color: #777; font-size: 9pt; }
.hallazgo { color: #7a4a00; }
ul { margin: 0.3em 0; }
.pregunta { margin: 0.6em 0; padding-left: 0.6em; border-left: 3px solid #533483; }
.senal { margin: 0.5em 0; padding-left: 0.6em; border-left: 3px solid #999; color: #444; }
"""

# EXP-01: informe de devolución para el grupo. SIN señales, SIN cuestionario, SIN origen.
_PLANTILLA_GRUPO = """<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<style>{{ css }}</style></head><body>
<h1>Devolución — {{ proyecto }}</h1>
<div class="meta">Grupo {{ grupo }} · Exposición {{ exposicion }} · {{ fecha }}</div>
<div class="nota-caja">Nota final: <span class="nota">{{ nota_final }}</span></div>

{% for art in artefactos %}
<h2>{{ art.titulo }}</h2>
  {% if art.hallazgos %}
  <h3>Verificaciones automáticas</h3>
  <ul>{% for h in art.hallazgos %}<li class="hallazgo">{{ h }}</li>{% endfor %}</ul>
  {% endif %}
  {% for o in art.observaciones %}
  <div class="obs">{{ o.contenido }}
    {% if o.referencia %}<div class="ref">Referencia: {{ o.referencia }}</div>{% endif %}
  </div>
  {% endfor %}
{% endfor %}

{% if consistencia %}
<h2>Consistencia entre artefactos</h2>
{% for c in consistencia %}<div class="obs">{{ c.contenido }}
  {% if c.referencia %}<div class="ref">{{ c.referencia }}</div>{% endif %}</div>{% endfor %}
{% endif %}
</body></html>"""

# EXP-02: guía de defensa para el docente. Preguntas + señales aceptadas.
_PLANTILLA_DEFENSA = """<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<style>{{ css }}</style></head><body>
<h1>Guía de defensa</h1>
<div class="meta">Grupo {{ grupo }} · {{ proyecto }} · Exposición {{ exposicion }}</div>

<h2>Cuestionario de defensa</h2>
{% for p in preguntas %}
<div class="pregunta"><strong>{{ loop.index }}.</strong> {{ p.contenido }}
  {% if p.referencia %}<div class="ref">Sobre: {{ p.referencia }}</div>{% endif %}</div>
{% else %}<p>(sin preguntas validadas)</p>{% endfor %}

{% if senales %}
<h2>Señales para indagar</h2>
{% for s in senales %}<div class="senal">{{ s.contenido }}</div>{% endfor %}
{% endif %}
</body></html>"""


def renderizar_informe_grupo(contexto: dict, plantilla: str | None = None) -> str:
    """Renderiza el HTML del informe de devolución (EXP-01)."""
    tpl = _env.from_string(plantilla or _PLANTILLA_GRUPO)
    return tpl.render(css=_CSS_BASE, **contexto)


def renderizar_guia_defensa(contexto: dict, plantilla: str | None = None) -> str:
    """Renderiza el HTML de la guía de defensa (EXP-02)."""
    tpl = _env.from_string(plantilla or _PLANTILLA_DEFENSA)
    return tpl.render(css=_CSS_BASE, **contexto)


def html_a_pdf(html: str, ruta_salida: Path | str) -> Path:
    """Convierte HTML a PDF con WeasyPrint (AD-09). Importación perezosa."""
    from weasyprint import HTML  # perezoso: no todos los entornos lo necesitan

    ruta = Path(ruta_salida)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html).write_pdf(str(ruta))
    return ruta
