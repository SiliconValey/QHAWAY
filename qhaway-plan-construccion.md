# QHAWAY — Plan de Construcción y Estudio

**Versión:** 1.0
**Fecha:** Julio 2026
**Documentos base:** Visión 1.0 · SRS 1.0 · Arquitectura 1.0

---

## Modo de trabajo

El principio del plan es el mismo del producto: **el que construye aprende**. Christian escribe el código; la IA guía, revisa y desbloquea. Cada etapa define: qué se construye, qué requisitos cubre, qué habilidad nueva se incorpora y el criterio de salida (cuándo está terminada). El orden es el de riesgo y dependencias propuesto en la revisión de arquitectura: primero lo puro, después lo que persiste, después lo que da valor sin costo, recién entonces la IA — y la vista más compleja al final, alimentada con datos reales.

La estimación de referencia es **8-10 semanas de trabajo efectivo** concentrado; a ritmo de horas sueltas entre cursadas, pensarlo como etapas y no como calendario. Cada etapa cierra con algo que funciona.

---

## Etapa 0 — Matar los riesgos (antes de escribir el sistema)

**Límite temporal: dos semanas.** Esta etapa no produce nada que "funcione" y por eso es la más propensa a estirarse; regla anti-pantano: si el PoC de congelamiento en Linux se traba, se difiere a la Etapa 9 y se sigue — Windows alcanza para validar el riesgo principal.

**Se hace:**
1. **Diseño del esquema JSON de salidas** (Arquitectura §13.1): los campos exactos de observación, valoración, pregunta y señal. Sesión de diseño, no de código. El esquema debe diseñarse para que la métrica del punto 7 sea computable.
2. **Estrategia de referencias sobre PDF** (§13.2): decisión de diseño para EVA-01/DET-02 — heurística de encabezados con página como respaldo. Se valida con 2-3 PDFs reales de entregas del ciclo pasado.
3. **Spike de costo + viabilidad del contrato** (§13.3): una llamada real a la API con una entrega verdadera, **pidiendo la salida en el esquema JSON borrador del punto 1** — un spike, dos validaciones: presupuesto y que el modelo pueda producir el contrato (referencias con la granularidad pedida, sin campos que fuercen invención). Medir específicamente la unidad transversal, la candidata a más cara del pipeline (recibe la entrega completa, contenido variable que no se beneficia del caché). Proyectar 13 grupos × 5 unidades × 2 exposiciones en **dos escenarios**: evaluación en tanda (el caché pega entre grupos) y un grupo por sesión (el caché expira y nunca pega) — el caché de la API es efímero y el ahorro depende del patrón de uso. Elegir el modelo por defecto con esos números.
4. **PoC HTML→PDF** (AD-09): las opciones reales son tres. **WeasyPrint** (el mejor CSS para tu sistema visual, pero notoriamente frágil de congelar en Windows: arrastra Pango/GObject); **QTextDocument** (congela trivial, pero CSS muy limitado — sin variables, flexbox ni grid: probable descarte rápido); **QWebEngine `printToPdf`** (fidelidad Chromium completa, congela bien, pero suma ~150 MB al ejecutable). La pulseada real es WeasyPrint vs. QWebEngine, decidida por congelamiento vs. tamaño — con el número en la mano. A favor: tu sistema visual ya tiene modo claro imprimible, que es lo que un informe PDF necesita.
5. **PoC de congelamiento**: PyInstaller con PySide6 + el motor PDF elegido, en Windows y Linux. Un "hola mundo" que abra una ventana y genere un PDF, congelado y ejecutado en ambas plataformas.
6. **Set de calibración, particionado y re-evaluado**: seleccionar entregas del ciclo anterior cubriendo el rango de calidad y **separarlas en dos**: 4-6 para iterar (Etapas 3 y 6) y 2-3 **reservadas que no se miran hasta el simulacro final** (Etapa 9). El mismo principio que no diseñar casos de prueba mirando la implementación: iterar y medir con los mismos datos produce prompts sobreajustados. Además: **re-evaluar a mano cada entrega del set con la rúbrica real actual** (punto siguiente del §13.4) — las evaluaciones históricas pueden no ser comparables si la rúbrica difiere en criterios o pesos, y sin esa re-evaluación la métrica del punto 7 mide contra un patrón que no corresponde. Se hace al armar el set, con el criterio fresco; es trabajo real y está presupuestado acá.
7. **Métrica de coincidencia** (una página): la definición operativa de "coincide con el criterio del docente" que gobierna las Etapas 3, 6 y 9. Propuesta de base a refinar: (a) nota sugerida dentro de ±1 de la nota docente, (b) cobertura de hallazgos — % de las observaciones que el docente hizo a mano que el sistema también detecta, (c) valoración por criterio — % de criterios con el mismo nivel o adyacente. Incluye el **umbral de aceptación** (cuánta discrepancia es tolerable) decidido *antes* de empezar a iterar, y — porque un evaluador no determinístico corrido una vez da un punto, no una medición — la **disciplina de corridas**: mínimo 2-3 corridas por entrega, el método de agregación (promedio para la métrica, peor caso reportado aparte) y la temperatura fijada. Sin esto, la validación final de la Etapa 9 puede aprobar o reprobar por ruido.
8. **Política de datos y privacidad** (una página): qué contenido viaja a la API (las entregas incluyen nombres, a veces legajos o correos en carátulas), la base normativa aplicable (Ley 25.326 de Protección de Datos Personales), qué se informa a los alumnos y al instituto, y la posición sobre anonimización (asumida como no necesaria por el carácter público de los trabajos — decisión que debe quedar escrita, no implícita). Incluye la **política de transparencia, ya decidida y en práctica en la cátedra: los grupos saben que la evaluación cuenta con asistencia de IA validada por el docente** — coherente con el principio rector del proyecto y con el uso responsable de IA que la materia enseña. Este documento acompaña al proyecto cuando se abra a la comunidad.

**Aprendés:** Messages API básica (primera llamada real, anatomía de tokens y precios), y el hábito profesional de despejar incertidumbre antes de construir.
**Criterio de salida:** presupuesto validado o corregido; motor PDF elegido; congelamiento probado (al menos en Windows); esquema JSON, estrategia de referencias, métrica de coincidencia y política de datos documentados (una página cada uno); set de calibración particionado en carpetas.

## Etapa 1 — Dominio puro

**Se construye:** `dominio.rubrica` (modelo y validación, todos los casos inválidos de CFG-01), `dominio.nota` (composición, regla de crítico, artefactos ausentes, redondeo de mitades hacia arriba — los ejemplos del Apéndice B como primeros tests), `dominio.evaluacion` (entidades y máquina de estados).
**Cubre:** CFG-01/02/03, EVA-05/06, base de GRP-04/06.
**Aprendés:** nada nuevo — y eso es deliberado: la primera etapa es terreno conocido (Python puro + pytest) para que el proyecto arranque con tracción. Es también tu material de clase perfecto: TDD real sobre reglas de negocio reales.
**Criterio de salida:** suite pytest verde con los casos del Apéndice B, los casos inválidos de CFG-01 y los bordes del testeo con lector (rúbrica sin críticos, `.ui` vacío, entrega parcial).

## Etapa 2 — Persistencia

**Se construye:** esquema SQLite (las 13 entidades de Arquitectura §5.1), repositorios sobre `sqlite3`, estructura de carpetas, `decisiones.json` de escritura continua, `infra.snapshots`, verificación de integridad. Además, un **arnés CLI mínimo y descartable** (`qhaway_cli.py`) que permite ejercitar servicios sin UI: es lo que hace verificables los criterios de salida de las Etapas 3 a 6 antes de que exista la interfaz — y de paso, material de clase sobre separación dominio/interfaz.
**Cubre:** GRP-01..08, CFG-11, base de RNF-06/09.
**Aprendés:** patrones de persistencia sin ORM (repositorios, transacciones, migraciones con campo de versión), escritura atómica de archivos (escribir + renombrar).
**Criterio de salida:** test de la regla de oro — borrar `qhaway.db` y reconstruir desde las carpetas **todo el trabajo de evaluación** (entregas, análisis, decisiones, valoraciones y notas). Los metadatos operativos (grupos, integrantes, consumo) no se reconstruyen desde archivos por diseño (AD-03: los nombres jamás en la estructura compartible); se recuperan desde respaldo o recarga manual — pérdida aceptada y documentada.

## Etapa 3 — Extracción + DET (primer producto usable)

**Se construye:** `infra.extraccion` (PyMuPDF, python-docx, ElementTree) y `dominio.deteccion` (checklist, elementos formales, nomenclatura del `.ui`), con la estrategia de referencias de la Etapa 0 puesta a prueba contra entregas reales.
**Cubre:** ING-02/04/06, DET-01..05, CFG-05/06.
**Aprendés:** extracción de estructura desde documentos hostiles (el PDF de alumnos es el caso difícil) — habilidad transferible a cualquier proyecto de IA documental.
**Criterio de salida:** correr DET (vía el arnés CLI) sobre el subconjunto de iteración del set de calibración y que los hallazgos coincidan con lo que vos detectarías a ojo. **Hito:** QHAWAY ya sirve sin IA — verificación de nomenclatura y completitud gratis.

## Etapa 4 — Conector de IA

**Se construye:** `infra.conector_ia` (interfaz neutral, reintentos con backoff, validación EVA-13 contra el esquema JSON de la Etapa 0, registro de consumo) + `ConectorFalso` para tests.
**Cubre:** IEX-02, EVA-13, MON-01, CFG-07/08.
**Aprendés:** **el corazón del plan de estudio** — salidas estructuradas (exigir y validar JSON del modelo), manejo de errores de API reales, y el patrón de diseño "puerto y adaptador" que hace testeable un sistema con IA.
**Criterio de salida:** suite de integración del conector contra el falso (incluyendo respuestas inválidas y fallas) y una llamada real validada de punta a punta.

## Etapa 5 — Pipeline completo

**Se construye:** `servicios.analizar_entrega` (los 6 pasos de Arquitectura §6), reanudación por unidades, MON-02/03, worker QThread con señales de progreso.
**Cubre:** EVA-02/10, ING-01/03/05, MON-02/03, IEX-01, RNF-06.
**Aprendés:** orquestación con estado persistente (la máquina de estados en acción) y el patrón worker de Qt en serio (señales entre hilos, nada de tocar widgets desde el worker).
**Criterio de salida:** el test de la desconexión — arrancar un análisis real, cortar internet en la unidad 3, cerrar la app, reabrir, reanudar, y que el costo registrado muestre que las unidades 1-2 no se repagaron. **Límite conocido y aceptado:** el pipeline es secuencial (5 unidades × 13 grupos con latencias de decenas de segundos por unidad puede ser un rato largo en tanda); el diseño por unidades independientes (AD-04) permite paralelizar entregas distintas en el futuro sin rediseño, si llega a molestar.

## Etapa 6 — Prompts y evaluación real

**Se construye:** las plantillas de `prompts/` (analisis_artefacto × 4, analisis_transversal), inyección de rúbrica/modelo/hallazgos DET, prompt caching, EVA-01/03/04/07/08/09.
**Aprendés:** la otra mitad del corazón — **prompt engineering de evaluación**: instrucciones de rol, calibración-no-plantilla, exigencia de referencias, cacheo por orden de contexto (estable primero, variable al final). Acá es donde tu criterio docente se convierte en texto ejecutable.
**Criterio de salida:** primera pasada del **subconjunto de iteración** del set de calibración, medida con la métrica de coincidencia de la Etapa 0, con resultados dentro de distancia razonable del umbral (la iteración fina es la Etapa 9; las entregas reservadas no se tocan).

## Etapa 7 — UI

**Se construye:** `ui.ciclo`, `ui.configuracion`, `ui.entrega`, `ui.monitor` primero (son formularios y tablas, tu terreno); `ui.revision` al final, diseñada en Qt Designer **con borradores reales del pipeline en pantalla** — su diseño surge de usarla, no de imaginarla.
**Cubre:** REV-01..07, GRP-06, MON-02/03/04, REV-06.
**Aprendés:** diseño de UI para flujos de validación (patrones aceptar/editar/descartar) — y el valor de diferir el diseño de lo complejo hasta tener datos verdaderos.
**Criterio de salida:** revisar un borrador real completo de punta a punta sin tocar la base a mano, con tests de humo en pytest-qt para los flujos aceptar/editar/descartar (coherencia con lo que se enseña en Ingeniería de Software: la UI también se testea).

## Etapa 8 — Exportación

**Se construye:** `infra.informes` (Jinja2 + el motor validado en Etapa 0), plantillas del informe de grupo y la guía de defensa, EXP-01..04.
**Aprendés:** plantillas Jinja2 (transferible directo a tus materiales de cátedra, que ya son HTML).
**Criterio de salida:** los dos PDF de una evaluación real, con tu identidad visual, sin señales ni marcas de origen en el informe del grupo.

## Etapa 9 — Calibración y cierre

**Se hace:** iterar prompts contra el subconjunto de iteración midiendo con la métrica de la Etapa 0, con **límite de tres rondas completas** (un evaluador no determinístico nunca coincide al 100%; el umbral de aceptación se decidió antes de empezar, justamente para que el sesgo no sea "seguir iterando"); congelar versiones de prompts; correr **una única vez** las entregas reservadas como validación final no contaminada; empaquetado final (RNF-10); guía de instalación y uso (incluyendo la política de datos de la Etapa 0); simulacro completo de evaluación como si fuera el día real.
**Aprendés:** evaluación de sistemas con IA — cómo se mide, itera y versiona la calidad de un evaluador no determinístico. La habilidad más nueva de todas y la más valiosa para donde va la industria.
**Criterio de salida:** los criterios de éxito del MVP (Visión §9) medibles en el simulacro; **QHAWAY listo para la primera exposición del ciclo**.

---

## Plan de estudio (resumen por tema)

| Tema | Etapa | Profundidad |
|---|---|---|
| Messages API: anatomía, tokens, precios | 0 | Fundamentos |
| Salidas estructuradas y validación | 4 | A fondo — tema central |
| Prompt engineering de evaluación | 6, 9 | A fondo — tema central |
| Prompt caching | 6 | Operativa |
| Patrón puerto/adaptador para IA testeable | 4 | A fondo |
| Persistencia sin ORM, transacciones, migraciones | 2 | Operativa |
| Extracción de documentos hostiles | 3 | Operativa |
| Worker QThread y señales entre hilos | 5 | Consolidación |
| Jinja2 y HTML→PDF | 0, 8 | Operativa |
| PyInstaller multiplataforma | 0, 9 | Operativa |
| Evaluación de sistemas de IA (calibración, regresión de prompts) | 9 | A fondo — tema central |

Regla del plan: **ninguna habilidad se estudia en abstracto** — cada tema se aprende en la etapa que lo necesita, sobre el código de QHAWAY, y cada cosa aprendida es material potencial para tus materias.
