# QHAWAY — Spike de Costo y Viabilidad del Contrato (Etapa 0.3)

**Versión:** 1.0 · **Fecha:** Julio 2026
**Realiza:** Arquitectura §13.3 · Plan Etapa 0.3
**Ejecutado:** llamada real a la API con la entrega EstacionAR (SRS de grupo, ~2.041 tokens) + SIMI como proyecto modelo (~1.877 tokens) + mini-rúbrica de 3 criterios, en dos corridas idénticas para medir caché.

## Resultados

| Medición | Corrida 1 (caché frío) | Corrida 2 (caché caliente) |
|---|---|---|
| Tokens entrada / salida | 3.248 / 2.502 | 3.248 / 2.492 |
| Caché escritura / lectura | 2.790 / 0 | 0 / 2.790 |
| Costo | **USD 0,0577** | **USD 0,0480** |
| Contrato (esquema 0.1) | ✓ VÁLIDO, sin reintentos | ✓ VÁLIDO, sin reintentos |

**Proyección por exposición (13 grupos, 4 unidades + transversal estimada a 2x):**
- Escenario tanda: **USD 3,87** · Escenario suelto: **USD 4,50**
- Contra presupuesto de USD 20/mes (Visión §10): **validado con margen de ~4-5x**, incluso asumiendo que la rúbrica completa y los cuatro artefactos multipliquen el costo por unidad.

## Decisiones tomadas

1. **Modelo por defecto del MVP: `claude-sonnet-4-6`** ($3/$15 por MTok, verificado jul-2026). La calidad del análisis justifica el nivel: detectó una contradicción interna real cruzando secciones (RNF-04 "sin capacitación externa" vs. §2.3 "8 horas de capacitación") — el tipo de hallazgo que define el valor del producto. No se requiere degradar a Haiku por costo.
2. **El esquema JSON 0.1 es viable sin cambios**: valoraciones completas (una por criterio), niveles canónicos, referencias con ubicación y página correctas (verificadas contra el PDF), y `null` usado correctamente dos veces cuando no había cita — la instrucción anti-invención funcionó.
3. **Caché confirmado** (~17% de ahorro con un bloque cacheado chico; crecerá con rúbrica completa + 4 artefactos del modelo). El orden estable-primero/variable-al-final queda ratificado.

## Validación de calidad (informal, pre-métrica)

El docente auditó la respuesta completa contra la entrega real y **coincide con las tres valoraciones (Regular × 3) y con las observaciones**. Hallazgos destacados del modelo: la contradicción interna RNF-04↔§2.3, el título mentiroso del documento ("Diseño Funcional" siendo un SRS, coincidente con el hallazgo del laboratorio 0.2), y el análisis criterio por criterio de las métricas no medibles de los RNF. Citas verificadas como textuales; páginas correctas, no inventadas.

## Refinamientos anotados para los prompts (Etapa 6)

1. Exigir que `cita` sea **un único fragmento verbatim** (el modelo devolvió una vez un rango "RF-01 a RF-15" y una vez dos celdas concatenadas "95% ... / 99% ..." — válidos según el esquema pero no citas puras).
2. Mantener la instrucción explícita de `pagina: null` ante incertidumbre — demostrada efectiva.

## Riesgo residual

La transversal se estimó como 2x una unidad, no se midió: recibe la entrega completa (contenido variable sin caché). Con el margen actual (4-5x) el riesgo es bajo; se mide con datos reales al construirla (Etapa 5/6) y MON la vigilará desde la primera corrida.
