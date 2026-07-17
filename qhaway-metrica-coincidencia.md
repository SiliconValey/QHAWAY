# QHAWAY — Métrica de Coincidencia (Etapa 0.7)

**Versión:** 1.0-rc (valores pendientes de validación del docente) · **Fecha:** Julio 2026
**Realiza:** Plan Etapa 0.7 · gobierna los criterios de salida de las Etapas 3, 6 y 9
**Principio:** los umbrales se deciden acá, ANTES de iterar prompts, para que el sesgo nunca sea "seguir iterando hasta que dé".

## Qué se compara

Cada entrega del set de calibración tiene una **evaluación docente de referencia** hecha a mano con la rúbrica real vigente (Etapa 0.6): nivel por criterio, nota final y lista de observaciones. La salida agregada del sistema (ver disciplina de corridas) se compara contra esa referencia en cuatro componentes.

## Los cuatro componentes

**C1 — Nota.** La nota sugerida está dentro de ±1 de la nota docente.
*Medición:* por entrega, pasa/no pasa. *Umbral:* pasa en ≥ 80% de las entregas del set (con sets de 4-6, esto tolera exactamente una desviación).

**C2 — Cobertura de hallazgos.** De las observaciones que el docente hizo a mano, ¿cuántas detectó también el sistema?
*Medición:* apareamiento manual del docente — una observación del sistema "coincide" con una suya si señala el mismo problema sobre el mismo elemento (mismo criterio + misma sección/requisito/objeto referenciado; la redacción no importa). *Umbral:* cobertura promedio ≥ 70%. Las observaciones del docente marcadas por él como "críticas" deben cubrirse al 100%.

**C3 — Valoración por criterio.** ¿Los niveles del sistema coinciden con los del docente?
*Medición:* por criterio, distancia en la escala ordinal (Insuficiente=1 … Excelente=4). *Umbral:* ≥ 85% de los criterios con distancia ≤ 1 (igual o adyacente), y **cero casos de distancia 3** (Insuficiente↔Excelente): una inversión total de juicio es descalificante aunque el promedio dé bien.

**C4 — Ruido.** ¿Cuánto de lo que el sistema propone es basura que el docente descartaría?
*Medición:* % de observaciones del sistema que el docente descartaría de plano (no las editables: las descartables). *Umbral:* ≤ 25%. Este componente anticipa la métrica de retrabajo de producción (REV-06) y evita el truco de inflar C2 generando observaciones a mansalva.

**Regla de aceptación global:** los cuatro componentes deben cumplir su umbral simultáneamente sobre el subconjunto de iteración (Etapa 6) y, una única vez, sobre las entregas reservadas (Etapa 9).

## Disciplina de corridas

- **Temperatura 0** en calibración y en producción: un evaluador quiere el mínimo de varianza disponible.
- **3 corridas por entrega** aun así (la varianza residual existe): el nivel por criterio se agrega por **moda** (el valor mayoritario de las 3); las observaciones se toman de la corrida mediana en cantidad.
- Se reporta además el **peor caso** de las 3 corridas: si la moda pasa pero una corrida individual tuvo una distancia 3 en algún criterio, se registra como inestabilidad y cuenta como falla de C3.
- La varianza observada entre corridas se documenta en cada ronda de calibración: si dos rondas con el mismo prompt difieren más que dos corridas del mismo prompt, la iteración está midiendo ruido.

## Qué NO mide esta métrica (y se evalúa aparte, a ojo del docente)

La calidad de redacción de las observaciones, la utilidad de las preguntas de defensa y la pertinencia de las señales no son reducibles a números con un set de este tamaño: se auditan cualitativamente en cada ronda (como se hizo en el spike 0.3) y su vara es "¿lo firmaría como devolución de mi cátedra?".

## Conexión con el esquema (0.1)

La métrica es computable porque el esquema lo garantiza: C1 sale de la composición de valoraciones; C2 y C4 se aparean por `criterio_id` + `referencia.ubicacion`; C3 compara el campo `nivel` contra el enum ordinal. Ningún componente requiere interpretación del texto libre.
