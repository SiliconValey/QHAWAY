# QHAWAY — Esquema de Salidas Estructuradas (Etapa 0.1)

**Versión:** 1.0 · **Fecha:** Julio 2026
**Realiza:** Arquitectura §7/§13.1 · EVA-01/07/08/09/13 · Métrica de coincidencia (Etapa 0.7)

Principio de diseño: cada campo existe porque un requisito lo exige o porque la métrica de coincidencia lo necesita. Los IDs internos los asigna el sistema, nunca el modelo. Toda respuesta se valida contra este esquema antes de persistirse (EVA-13); respuesta que no valida = respuesta rechazada.

---

## 1. Salida de unidad por artefacto (`analisis_artefacto`)

```json
{
  "artefacto": "presentacion | srs | fd | ui",
  "valoraciones": [
    {
      "criterio_id": "string — ID exacto de la rúbrica de la sección",
      "nivel": "Insuficiente | Regular | Bueno | Excelente",
      "justificacion": "string breve — el porqué de este nivel (alimenta la composición trazable, EVA-05)"
    }
  ],
  "observaciones": [
    {
      "criterio_id": "string — ID de la rúbrica",
      "tipo": "fortaleza | mejora",
      "contenido": "string — la observación completa, redactada para el informe",
      "referencia": {
        "ubicacion": "string — sección o elemento identificable (en UI: nombre del objeto)",
        "pagina": "int | null — número de página cuando aplica",
        "cita": "string | null — fragmento textual ≤ 25 palabras cuando es citable"
      }
    }
  ]
}
```

## 2. Salida de unidad transversal (`analisis_transversal`)

```json
{
  "consistencias": [
    {
      "tipo": "srs_fd | fd_ui | srs_ui",
      "elemento": "string — el requisito/pantalla/objeto involucrado",
      "hallazgo": "string — la inconsistencia, redactada para el informe",
      "referencias": [
        { "artefacto": "...", "ubicacion": "...", "pagina": "int | null" }
      ]
    }
  ],
  "preguntas_defensa": [
    {
      "pregunta": "string — redactada para hacerse en la exposición",
      "elemento": "string — OBLIGATORIO: el elemento nombrado de la entrega (regla EVA-08)",
      "artefacto": "presentacion | srs | fd | ui | transversal",
      "intencion": "string — qué comprensión testea (visible solo para el docente, en REV)"
    }
  ],
  "senales": [
    {
      "descripcion": "string — el aspecto llamativo, en lenguaje de sugerencia (EVA-09)",
      "artefacto": "...",
      "sugerencia": "string — cómo indagarlo en la defensa"
    }
  ]
}
```

## 3. Reglas de validación (EVA-13)

1. `nivel` estrictamente dentro del enum de cuatro valores canónicos.
2. Todo `criterio_id` debe existir en la sección de rúbrica enviada en el contexto; ID desconocido = respuesta inválida.
3. Cada criterio de la sección debe recibir exactamente una valoración (ni faltantes ni duplicadas).
4. `pregunta` sin `elemento` no nulo y no vacío = inválida (materializa el criterio de aceptación de EVA-08).
5. `referencia.ubicacion` obligatoria en toda observación; `pagina` y `cita` opcionales (tablas, diagramas y el `.ui` pueden no ser citables); `cita` ≤ 25 palabras.
6. `senal` nunca lleva `criterio_id` ni valoración: las señales no influyen en la nota (EVA-09).
7. Respuesta que no valida → reintento (IEX-02); agotados → unidad `pendiente` (EVA-13). Nunca se persiste contenido inválido.

## 4. Decisiones registradas

- **`tipo: fortaleza | mejora`**: el informe al grupo incluye fortalezas, no solo defectos; el docente decide en REV cuáles sobreviven.
- **`cita` corta y opcional**: verificación instantánea cuando el contenido es citable; ubicación+página como respaldo cuando no.
- **`intencion` en preguntas**: metadato para el docente (criterio de aceptación/descarte en REV); jamás se exporta al grupo.
- **`justificacion` separada de las observaciones**: es el porqué del nivel, no una observación más; alimenta la vista de composición de la nota.
- Los hallazgos DET **no** viajan en este esquema: son entrada del prompt (hechos verificados, EVA-04), no salida del modelo.

## 5. Pendiente de validación empírica

El spike (Etapa 0.3) debe confirmar contra el modelo real: que las referencias llegan con la granularidad pedida en PDFs reales de alumnos, y que ningún campo induce invención (especialmente `pagina` — si el modelo no la sabe, debe poder devolver `null`, y el prompt lo dirá explícitamente).
