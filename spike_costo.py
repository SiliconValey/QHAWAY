"""
QHAWAY — Etapa 0.3: Spike de costo + viabilidad del contrato
=============================================================
Hace UNA evaluación real de un SRS contra la API de Anthropic, pidiendo
la salida en el esquema JSON de la Etapa 0.1, y responde tres preguntas:

  1. ¿Cuánto cuesta evaluar un artefacto? (→ proyección a 13 grupos)
  2. ¿El modelo puede producir el contrato? (validación del esquema)
  3. ¿Cuánto ahorra el caché? (segunda llamada inmediata para medir)

Uso:
  pip install anthropic pymupdf
  set ANTHROPIC_API_KEY=sk-ant-...   (Windows)  |  export ANTHROPIC_API_KEY=... (Linux)
  python spike_costo.py ruta/al/SRS-grupo.pdf ruta/al/simi-ers-modelo.pdf
"""
import sys, os, json, re
import fitz  # PyMuPDF
from anthropic import Anthropic

# ── Configuración ────────────────────────────────────────────────────────────
MODELO = "claude-sonnet-4-6"   # candidato por defecto; probar también claude-haiku-4-5-20251001

# Tabla de precios USD por millón de tokens (verificada jul-2026 en docs.claude.com;
# en QHAWAY esta tabla será configurable, MON-01)
PRECIOS = {
    "claude-sonnet-4-6":          dict(entrada=3.00, salida=15.00, cache_escritura=3.75, cache_lectura=0.30),
    "claude-haiku-4-5-20251001":  dict(entrada=1.00, salida=5.00,  cache_escritura=1.25, cache_lectura=0.10),
}

# Mini-rúbrica de prueba (sección SRS del Apéndice A del SRS de QHAWAY)
RUBRICA_SRS = """
criterios de la sección SRS:
- SRS-REQ (peso 3, CRÍTICO): Los requisitos funcionales son completos, no ambiguos y verificables.
  Insuficiente: requisitos ausentes, vagos o no verificables. Regular: presentes pero con
  ambigüedades o vacíos importantes. Bueno: claros y verificables, con omisiones menores.
  Excelente: completos, precisos y verificables en su totalidad.
- SRS-EST (peso 1): El documento respeta la estructura IEEE 830 exigida.
  Insuficiente: no sigue la estructura. Regular: estructura parcial o desordenada.
  Bueno: estructura correcta con detalles menores. Excelente: completa y prolija.
- SRS-RNF (peso 2): Los requisitos no funcionales son medibles y tienen métrica asociada.
  Insuficiente: ausentes o sin métrica. Regular: pocos con métrica real.
  Bueno: mayoría medibles. Excelente: todos medibles con métricas claras.
"""

ESQUEMA = """
Respondé ÚNICAMENTE con un JSON válido (sin backticks, sin texto antes ni después) con esta estructura:
{
  "artefacto": "srs",
  "valoraciones": [
    {"criterio_id": "...", "nivel": "Insuficiente|Regular|Bueno|Excelente", "justificacion": "..."}
  ],
  "observaciones": [
    {"criterio_id": "...", "tipo": "fortaleza|mejora", "contenido": "...",
     "referencia": {"ubicacion": "encabezado de la sección", "pagina": null_o_numero, "cita": "≤25 palabras o null"}}
  ]
}
Reglas: exactamente una valoración por cada criterio de la rúbrica. Si no conocés el número
de página con certeza, usá null — NUNCA lo inventes. La cita debe ser textual del documento.
"""

INSTRUCCIONES = """Sos el asistente de evaluación de un docente de ingeniería de software.
Evaluás la entrega de un grupo de estudiantes contra la rúbrica dada, usando el proyecto
modelo SOLO como referencia del nivel de calidad esperado — NO como plantilla: las soluciones
distintas pero correctas no se penalizan por diferir del modelo.
Generá observaciones fundamentadas (fortalezas y mejoras) con referencia verificable al documento."""

NIVELES = {"Insuficiente", "Regular", "Bueno", "Excelente"}
CRITERIOS = {"SRS-REQ", "SRS-EST", "SRS-RNF"}

# ── Extracción ───────────────────────────────────────────────────────────────
def extraer_texto(ruta):
    doc = fitz.open(ruta)
    paginas = []
    for i, page in enumerate(doc, 1):
        paginas.append(f"[página {i}]\n{page.get_text()}")
    return "\n".join(paginas)

# ── Validación del contrato (las reglas de EVA-13 aplicables) ────────────────
def validar(texto_respuesta):
    errores = []
    limpio = re.sub(r"^```(json)?|```$", "", texto_respuesta.strip(), flags=re.M).strip()
    try:
        data = json.loads(limpio)
    except json.JSONDecodeError as e:
        return None, [f"JSON inválido: {e}"]
    vistos = [v.get("criterio_id") for v in data.get("valoraciones", [])]
    if sorted(vistos) != sorted(CRITERIOS):
        errores.append(f"Valoraciones esperadas {CRITERIOS}, recibidas {vistos}")
    for v in data.get("valoraciones", []):
        if v.get("nivel") not in NIVELES:
            errores.append(f"Nivel fuera del enum: {v.get('nivel')!r}")
    for o in data.get("observaciones", []):
        if o.get("criterio_id") not in CRITERIOS:
            errores.append(f"Observación con criterio desconocido: {o.get('criterio_id')!r}")
        ref = o.get("referencia") or {}
        if not ref.get("ubicacion"):
            errores.append("Observación sin referencia.ubicacion")
        cita = ref.get("cita")
        if cita and len(cita.split()) > 25:
            errores.append(f"Cita de {len(cita.split())} palabras (máx 25)")
    return data, errores

# ── Costo ────────────────────────────────────────────────────────────────────
def costo(uso, modelo):
    p = PRECIOS[modelo]
    ent = getattr(uso, "input_tokens", 0)
    sal = getattr(uso, "output_tokens", 0)
    cw  = getattr(uso, "cache_creation_input_tokens", 0) or 0
    cr  = getattr(uso, "cache_read_input_tokens", 0) or 0
    usd = (ent*p["entrada"] + sal*p["salida"] + cw*p["cache_escritura"] + cr*p["cache_lectura"]) / 1e6
    return dict(entrada=ent, salida=sal, cache_esc=cw, cache_lec=cr, usd=usd)

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    entrega = extraer_texto(sys.argv[1])
    modelo_ref = extraer_texto(sys.argv[2])
    print(f"Entrega: ~{len(entrega)//4} tokens estimados | Modelo ref: ~{len(modelo_ref)//4}")

    cliente = Anthropic()  # lee ANTHROPIC_API_KEY del entorno

    # Bloques ESTABLES (cacheables) primero; la entrega VARIABLE al final (AD del §7)
    system = [
        {"type": "text", "text": INSTRUCCIONES},
        {"type": "text", "text": f"RÚBRICA:\n{RUBRICA_SRS}"},
        {"type": "text", "text": f"PROYECTO MODELO (referencia de calidad, no plantilla):\n{modelo_ref}",
         "cache_control": {"type": "ephemeral"}},   # marca de caché al final del bloque estable
    ]
    mensaje = f"ENTREGA DEL GRUPO A EVALUAR:\n{entrega}\n\n{ESQUEMA}"

    resultados = []
    for corrida in (1, 2):   # la 2ª mide el ahorro real del caché
        resp = cliente.messages.create(
            model=MODELO, max_tokens=4000, system=system,
            messages=[{"role": "user", "content": mensaje}],
        )
        texto = "".join(b.text for b in resp.content if b.type == "text")
        data, errores = validar(texto)
        c = costo(resp.usage, MODELO)
        resultados.append((c, data, errores, texto))
        print(f"\n── Corrida {corrida} ──")
        print(f"  tokens: entrada={c['entrada']} salida={c['salida']} "
              f"cache_escritura={c['cache_esc']} cache_lectura={c['cache_lec']}")
        print(f"  costo: USD {c['usd']:.4f}")
        print(f"  contrato: {'✓ VÁLIDO' if data and not errores else '✗ ERRORES: ' + '; '.join(errores)}")

    # Guardar la respuesta para inspección manual
    with open("spike_respuesta.json", "w", encoding="utf-8") as f:
        f.write(resultados[0][3])
    print("\nRespuesta completa guardada en spike_respuesta.json — revisala a ojo:")
    print("¿las citas existen en el documento? ¿las páginas son correctas? ¿las observaciones tienen sentido?")

    # Proyección: 4 unidades de artefacto + 1 transversal (~2x por recibir todo) por entrega
    c1, c2 = resultados[0][0], resultados[1][0]
    por_entrega_frio  = c1["usd"] * 4 + c1["usd"] * 2      # sin caché (un grupo por sesión)
    por_entrega_tanda = c1["usd"] + c2["usd"] * 3 + c2["usd"] * 2  # 1ª escribe caché, resto lee
    print(f"\n── Proyección (aproximada; la transversal se estima como 2x una unidad) ──")
    print(f"  Escenario TANDA (13 grupos seguidos):   USD {por_entrega_tanda:.3f}/entrega → USD {por_entrega_tanda*13:.2f} por exposición")
    print(f"  Escenario SUELTO (un grupo por sesión): USD {por_entrega_frio:.3f}/entrega → USD {por_entrega_frio*13:.2f} por exposición")
    print(f"  Presupuesto de referencia: USD 20/mes (Visión §10)")

if __name__ == "__main__":
    main()
