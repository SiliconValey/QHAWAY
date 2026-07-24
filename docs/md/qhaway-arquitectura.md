# QHAWAY — Documento de Arquitectura de Software

**Versión:** 1.0
**Fecha:** Julio 2026
**Autor:** Christian — ISFT N.º 179
**Documentos base:** Visión v1.0 · SRS v1.0

---

## 1. Introducción y objetivos de la arquitectura

Este documento describe la arquitectura del MVP de QHAWAY: las decisiones estructurales, los componentes, el modelo de datos y los diseños que realizan los requisitos del SRS v1.0. Su audiencia es quien construya o extienda el sistema.

Cuatro atributos de calidad gobiernan las decisiones, en este orden de prioridad cuando entran en conflicto:

1. **Auditabilidad (RNF-09)**: toda evaluación debe poder reconstruirse por completo — incluidos la rúbrica y los prompts exactos que la produjeron.
2. **Confiabilidad y reanudación (RNF-06, EVA-10)**: ninguna interrupción pierde trabajo ni dinero ya gastado.
3. **Extensibilidad (RNF-07)**: la Fase 2 (código) y la Fase 3 (otras materias, otros proveedores de IA) no deben requerir rediseño.
4. **Costo de API acotado (MON, Visión §10)**: la arquitectura trata cada token como un recurso a administrar.

## 2. Vista de contexto

QHAWAY es un sistema de un solo proceso que corre en la máquina del docente. Sus interacciones externas son tres:

- **Docente** (único actor humano): opera la interfaz PySide6 en todo el flujo — configuración, carga, revisión, exportación.
- **API de Anthropic** (única dependencia de red): recibe los contenidos de análisis y devuelve resultados estructurados. Toda la comunicación pasa por el conector (AD-06), por HTTPS, con la clave leída de la configuración de usuario.
- **Sistema de archivos local**: entrada (archivos de entregas, configuración YAML) y salida (persistencia del ciclo, informes PDF).

No existen: componente servidor propio, comunicación entre instalaciones, telemetría, ni acceso de los alumnos. El diagrama de contexto se reduce a esos tres vínculos — y esa simplicidad es deliberada (Visión §8: sin dependencia de servicios contratados).

## 3. Decisiones arquitectónicas

Registro de decisiones en formato abreviado (contexto → decisión → alternativas descartadas → consecuencias).

**AD-01 — Aplicación de escritorio con PySide6.** *Contexto:* usuario único local, sin necesidad de servidor (Visión §4). *Decisión:* aplicación de escritorio Python/PySide6. *Alternativas:* aplicación web (descartada: agrega servidor, despliegue y superficie de seguridad sin beneficio para un usuario local); CLI (descartada: el flujo de revisión REV es esencialmente visual). *Consecuencias:* distribución como ejecutable autocontenido (RNF-10); la experiencia del equipo en PySide6 reduce riesgo.

**AD-02 — Arquitectura en capas con dominio puro.** *Contexto:* testabilidad del cálculo de nota y las reglas de evaluación (RNF-07, sección 11). *Decisión:* cuatro capas — **interfaz** (PySide6) → **servicios de aplicación** (orquestación de casos de uso) → **dominio** (evaluación, composición de nota, máquina de estados, entidades) → **infraestructura** (persistencia, conector IA, extractores, generador de informes). El dominio no importa Qt ni el SDK de la API: se testea puro. *Alternativas:* estructura monolítica alrededor de la UI (descartada: acopla las reglas de negocio a Qt, imposibilita el testing barato). *Consecuencias:* algo más de ceremonia inicial; el dominio es reutilizable si en Fase 3+ cambia la interfaz.

**AD-03 — Persistencia híbrida: SQLite + carpetas, con `sqlite3` estándar.** *Contexto:* GRP-03, GRP-07; el docente debe poder ver y respaldar sus datos. *Decisión:* metadatos y estados en SQLite (módulo `sqlite3` de la biblioteca estándar, con capa de repositorios propia, sin ORM); archivos (entregas, análisis, informes, instantáneas) en una estructura de carpetas navegable. La base vive **dentro** del directorio raíz del ciclo: el respaldo es copiar una carpeta. *Alternativas:* SQLAlchemy (descartado: dependencia y abstracción innecesarias para este volumen; el SQL visible tiene además valor didáctico); todo en carpetas+JSON (descartado: consultas de estado e historial se vuelven artesanales); todo en SQLite con blobs (descartado: opaco para el docente). *Consecuencias:* dos fuentes de verdad que mantener consistentes. La regla, con su alcance preciso: **los archivos son el contenido de evaluación; la base es el índice más los metadatos operativos**. Todo el trabajo de evaluación — entregas, análisis por unidad, decisiones de revisión (`decisiones.json`, materializando REV-07), valoraciones y notas — existe como archivo y es íntegramente reconstruible ante discrepancia o corrupción de `qhaway.db`, sin pérdida de trabajo validado (RNF-06). Los metadatos operativos (grupos, integrantes, consumo de API, parámetros del ciclo) viven **solo en la base**, por decisión deliberada: los nombres de los alumnos jamás entran en la estructura de carpetas compartible (RNF-05). Su pérdida ante corrupción sin respaldo se acepta explícitamente como recuperable a mano (recargar los grupos de un ciclo es trabajo de minutos) — y el respaldo normal del directorio raíz incluye la base (GRP-07), por lo que el escenario solo ocurre sin respaldo alguno.

**AD-04 — Pipeline por artefacto con unidades de reanudación.** *Contexto:* EVA-02, EVA-10, RNF-06; costo por token. *Decisión:* el análisis se ejecuta como una secuencia de unidades independientes (una por artefacto + una transversal), cada una persistida atómicamente al completarse. El estado del pipeline vive en la base; reanudar es ejecutar las unidades pendientes. *Alternativas:* una sola llamada con toda la entrega (descartada: irrecuperable ante fallas, cara en reintentos, menos enfocada). *Consecuencias:* más llamadas a la API (mitigado por caché, AD-07); la transversal necesita como entrada los resultados de las unidades previas.

**AD-05 — Capa determinística local previa.** *Contexto:* DET-01..05; minimizar costo y máxima confiabilidad en lo verificable. *Decisión:* DET corre siempre primero, 100% local, y sus hallazgos se inyectan al contexto de EVA como hechos. *Alternativas:* pedirle todo a la IA (descartado: pagar por lo que un script hace gratis y exacto). *Consecuencias:* dos categorías de hallazgos con tratamiento distinto en el borrador (DET-05).

**AD-06 — Conector de IA aislado con interfaz neutral.** *Contexto:* IEX-02; riesgo de dependencia de proveedor (Visión §10). *Decisión:* un único módulo de infraestructura conoce el SDK de Anthropic; expone una interfaz propia (`analizar(unidad, contexto) → resultado estructurado`) e implementa reintentos, timeouts, caché y registro de consumo. El dominio y los servicios no saben qué proveedor hay detrás. *Alternativas:* llamadas al SDK dispersas (descartado: cambiar de proveedor tocaría todo el sistema). *Consecuencias:* punto único para MON y para EVA-13; habilita un conector falso para testing (sección 11).

**AD-07 — Prompts como artefactos versionados.** *Contexto:* sección 8; CFG-11; un cambio de prompt cambia las evaluaciones tanto como un cambio de código. *Decisión:* los prompts viven en archivos de texto externos (`prompts/`), con identificador de versión, versionados en git e incluidos en la instantánea de configuración de cada evaluación. *Alternativas:* strings embebidos en el código (descartado: invisibles para auditoría, inseparables del release). *Consecuencias:* la auditabilidad (RNF-09) alcanza al prompt exacto usado en cada evaluación.

**AD-08 — Análisis en hilo trabajador (QThread).** *Contexto:* IEX-01: la UI no se bloquea; progreso por artefacto. *Decisión:* el pipeline corre en un `QThread` trabajador que emite señales Qt de progreso/estado; la UI solo reacciona a señales. *Alternativas:* `asyncio` (descartado: integración con el loop de Qt agrega complejidad sin necesidad — el paralelismo real está en la API, no local). *Consecuencias:* disciplina estricta de no tocar widgets desde el worker.

**AD-09 — Informes por plantilla HTML → PDF.** *Contexto:* EXP-01, CFG-09; el sistema visual de la cátedra ya existe como HTML/CSS dark-theme. *Decisión:* los informes se generan rellenando plantillas HTML (Jinja2) convertidas a PDF, reutilizando la identidad visual existente. *Alternativas:* construcción directa del PDF con reportlab (descartada: duplicar en código un sistema visual que ya existe en CSS). *Consecuencias:* las plantillas son configurables editando HTML/CSS (CFG-09) sin tocar código; la elección de motor de conversión (WeasyPrint vs. motor de Qt) se valida con una prueba de concepto al inicio de la construcción.

## 4. Vista de componentes

Organización en las cuatro capas de AD-02, con el mapeo a los módulos del SRS:

**Capa de interfaz (PySide6)** — solo presentación y eventos; ninguna regla de negocio:
- `ui.ciclo`: vista de estado del ciclo y ABM de grupos — alta, edición de integrantes y archivado (GRP-01/02/06/08)
- `ui.configuracion`: carga de rúbrica/modelo/API, prueba de conexión (CFG)
- `ui.entrega`: carga y clasificación de archivos (ING-01/03)
- `ui.revision`: el flujo de validación elemento por elemento (REV) — la vista más compleja del sistema
- `ui.monitor`: consumo y presupuesto (MON-02/03), histórico exportable (MON-04) y métricas de retrabajo (REV-06)

**Capa de servicios de aplicación** — orquesta casos de uso completos, coordina dominio e infraestructura, corre el pipeline en el worker (AD-08):
- `servicios.configurar_ciclo`, `servicios.gestionar_grupos`, `servicios.cargar_entrega`, `servicios.analizar_entrega` (el pipeline, sección 6), `servicios.revisar_borrador`, `servicios.exportar`, `servicios.verificar_integridad`

**Capa de dominio** — puro Python, sin Qt ni SDK, 100% testeable en aislamiento:
- `dominio.rubrica`: modelo y validación de la rúbrica (CFG-01/02/03)
- `dominio.nota`: composición de la nota sugerida, regla de crítico, regla de artefacto ausente, redondeo explícito (EVA-05/06, Apéndice B del SRS)
- `dominio.evaluacion`: entidades (entrega, evaluación, elemento, valoración) y máquina de estados (sección 6)
- `dominio.deteccion`: las verificaciones determinísticas (DET-02/03/04) — reciben contenido ya extraído, no tocan archivos

**Capa de infraestructura** — todo lo que habla con el mundo:
- `infra.persistencia`: repositorios sobre `sqlite3` + gestión de la estructura de carpetas (AD-03)
- `infra.conector_ia`: el conector de AD-06 (SDK Anthropic, reintentos, caché, validación estructural EVA-13, registro de consumo)
- `infra.extraccion`: PyMuPDF (PDF), python-docx (.docx), ElementTree (.ui) → contenido normalizado para dominio y prompts (ING-04)
- `infra.informes`: plantillas Jinja2 + conversión HTML→PDF (AD-09)
- `infra.snapshots`: creación y lectura de instantáneas de configuración (CFG-11)

Regla de dependencias: las capas solo conocen hacia abajo (interfaz→servicios→dominio) y la infraestructura se inyecta en los servicios — el dominio no importa nada de las otras capas.

## 5. Modelo de datos

### 5.1 Esquema SQLite

Entidades principales y sus campos clave (el DDL completo es un entregable de la construcción):

- **ciclo** (id, nombre, parámetros: cantidad_preguntas, cantidad_exposiciones, presupuesto_mensual)
- **grupo** (id, ciclo_id, nombre, proyecto, archivado) — GRP-01, GRP-08
- **integrante** (id, grupo_id, nombre, fecha_alta, fecha_baja) — el historial de composición de GRP-02 se deriva de las fechas
- **entrega** (id, grupo_id, exposicion, version, fecha, vigente, estado) — GRP-04: la re-entrega inserta una versión nueva; `vigente` es la marca editable por el docente
- **archivo_entrega** (id, entrega_id, tipo_artefacto, ruta_relativa, formato, multiarchivo_confirmado) — ING-03
- **snapshot_config** (id, fecha, ruta_relativa, hash) — CFG-11: apunta a la carpeta de instantánea (rúbrica, checklist, nomenclatura, prompts con sus versiones)
- **evaluacion** (id, entrega_id, snapshot_id, estado, nota_sugerida, nota_final, fecha_validacion) — una por versión de entrega
- **analisis** (id, evaluacion_id, unidad, estado, intento, fecha) — AD-04: `unidad` ∈ {presentacion, srs, fd, ui, transversal}; el estado por unidad implementa la reanudación de EVA-10
- **hallazgo_det** (id, evaluacion_id, tipo, artefacto, detalle) — DET, categoría propia (DET-05)
- **elemento** (id, evaluacion_id, tipo, criterio_id, contenido_original, contenido_final, origen, estado_revision, referencia) — el corazón de REV: `tipo` ∈ {observacion, pregunta_defensa, senal}; `origen` ∈ {ia_aceptado, ia_editado, docente} (REV-05); `estado_revision` ∈ {pendiente, aceptado, editado, descartado} (REV-02/07); `referencia` es la ubicación verificable de EVA-01
- **valoracion** (id, evaluacion_id, criterio_id, nivel_ia, nivel_final) — REV-04: se conservan ambas
- **exportacion** (id, evaluacion_id, tipo, ruta_relativa, fecha) — `tipo` ∈ {informe_grupo, guia_defensa} (EXP-01/02/04)
- **consumo_api** (id, analisis_id, tokens_entrada, tokens_salida, tokens_cache, costo_estimado, reintento, fecha) — MON-01, granularidad por llamada

Reglas transversales del modelo: nada se borra físicamente (versiones GRP-04, archivado GRP-08); toda ruta almacenada es **relativa al directorio raíz del ciclo** (habilita GRP-07: mover o respaldar la carpeta no rompe nada); las notas y valoraciones finales solo existen tras validación docente (REV-04, EXP-03).

### 5.2 Estructura de carpetas

```
qhaway-ciclos/
└── AED2-2027/                      ← directorio raíz del ciclo (unidad de respaldo, GRP-07)
    ├── qhaway.db                   ← base SQLite (dentro del raíz, AD-03)
    ├── config/
    │   ├── rubrica.yaml
    │   ├── checklist.yaml
    │   ├── nomenclatura.yaml
    │   └── clasificacion.yaml      ← palabras clave de inferencia de artefactos (ING-03)
    ├── modelo/                     ← artefactos del proyecto modelo (CFG-04)
    ├── prompts/                    ← plantillas versionadas (AD-07)
    ├── plantillas/                 ← HTML/CSS de informes (AD-09, CFG-09)
    ├── snapshots/
    │   └── 2027-04-12_e7f3a1/      ← instantánea por evaluación (CFG-11, incluye prompts)
    └── grupos/
        └── G03-distribuidora-andes/
            ├── expo1/
            │   ├── v1/
            │   │   ├── entrega/    ← archivos tal como los subió el grupo
            │   │   ├── analisis/   ← resultados persistidos por unidad (EVA-10)
            │   │   ├── revision/
            │   │   │   └── decisiones.json  ← decisiones docentes, escritura continua (REV-07, AD-03)
            │   │   └── informes/   ← PDF exportados (EXP-04)
            │   └── v2/             ← re-entrega (GRP-04)
            └── expo2/
```

**La clave de API no vive en esta estructura**: se guarda en la configuración de la aplicación a nivel usuario (`%APPDATA%/qhaway` en Windows, `~/.config/qhaway` en Linux). Consecuencia deliberada: un respaldo del ciclo — o la carpeta compartida con un colega — jamás contiene la credencial (CFG-07, RNF-04).

Consistencia entre base y carpetas (AD-03): los archivos son el contenido, la base es el índice. La aplicación deberá incluir una verificación de integridad al abrir un ciclo (archivos referenciados ausentes, archivos huérfanos) con reporte al docente.

## 6. Pipeline de evaluación

El caso de uso `analizar_entrega` ejecuta esta secuencia (en el worker, AD-08):

1. **Preparación**: verificación de entrega analizable (ING-05: no vacía; parciales con confirmación), creación de la instantánea de configuración (CFG-11), creación de la evaluación con sus unidades de análisis pendientes.
2. **Extracción** (local): contenido normalizado de cada archivo (ING-04); archivos problemáticos reportados sin abortar (ING-06).
3. **DET** (local): checklist, elementos formales y nomenclatura sobre el contenido extraído; hallazgos persistidos (DET).
4. **EVA por artefacto** (API, una unidad por vez): para cada artefacto presente, el conector envía prompt + rúbrica de la sección + artefacto homólogo del modelo + hallazgos DET, y recibe el resultado estructurado (observaciones con referencia, valoraciones). Cada unidad se valida (EVA-13) y persiste atómicamente al completarse (EVA-10). Artefactos ausentes: sus criterios se valoran Insuficiente sin llamada (EVA-05).
5. **Pasada transversal** (API, unidad propia de reanudación): recibe los resultados de las unidades previas y la entrega completa; produce observaciones de consistencia (EVA-07), cuestionario de defensa (EVA-08) y señales (EVA-09).
6. **Composición** (local): cálculo de la nota sugerida (dominio.nota), armado del borrador con todos los elementos en estado `pendiente`.

### Máquina de estados de la evaluación

Los estados de GRP-06, con sus transiciones:

`sin_entrega → entrega_cargada → analizando → [análisis_interrumpido ⇄ analizando] → borrador_en_revision → evaluacion_validada → informe_exportado`

Reglas: `analizando → análisis_interrumpido` ocurre ante falla agotados los reintentos (IEX-02) o cierre de la aplicación; la reanudación retoma las unidades no completadas. `borrador_en_revision → evaluacion_validada` exige cero elementos pendientes y nota final confirmada (EXP-03). Un re-análisis sobre una evaluación en revisión crea una **nueva evaluación** para la misma versión de entrega — nunca pisa las decisiones de revisión existentes (GRP-04, RNF-06). Todos los estados son persistentes: la aplicación puede cerrarse en cualquier punto.

## 7. Integración con la API de IA

El conector (`infra.conector_ia`, AD-06) implementa:

- **Interfaz neutral**: `analizar(unidad, contexto) → ResultadoEstructurado`. Los servicios no conocen el SDK; el proveedor es un detalle de infraestructura reemplazable (Fase 4).
- **Salidas estructuradas**: cada llamada exige a la API responder en un esquema JSON definido (observaciones con criterio, nivel y referencia; preguntas; señales). La respuesta se valida contra el esquema antes de persistir (EVA-13): formato, niveles canónicos, referencias presentes. Inválida → reintento; agotados → unidad `pendiente`.
- **Política de reintentos**: timeouts y reintentos con retroceso exponencial, configurables (por defecto 3), aplicados tanto a errores de red como a respuestas inválidas. Todo reintento se registra con su costo (MON-01).
- **Prompt caching**: los bloques que se repiten entre unidades y entregas (instrucciones, rúbrica, proyecto modelo) se marcan para caché de la API (EVA-12). El orden de armado del contexto está diseñado para maximizar aciertos: primero lo estable (instrucciones, rúbrica, modelo), al final lo variable (la entrega del grupo). El conector registra tokens servidos desde caché para que MON muestre el ahorro real.
- **Registro de consumo**: cada llamada persiste tokens de entrada/salida/caché y costo estimado según la tabla de precios configurable (MON-01), asociados a la unidad de análisis.

## 8. Diseño de prompts

Los prompts son componentes del sistema con el mismo tratamiento que el código (AD-07): archivos en `prompts/`, con identificador de versión en su encabezado, incluidos en la instantánea de cada evaluación (CFG-11). Tres familias de plantillas:

- **`analisis_artefacto`** (una por tipo: presentación, SRS, FD, UI): instrucciones del rol evaluador, la sección de rúbrica correspondiente con sus descripciones por nivel (que son el criterio operativo de valoración, Apéndice A del SRS), el artefacto homólogo del proyecto modelo con la instrucción explícita de calibración-no-plantilla (EVA-03), los hallazgos DET como hechos no contradecibles (EVA-04), y el esquema de salida exigido.
- **`analisis_transversal`**: instrucciones de trazabilidad entre artefactos (EVA-07), generación del cuestionario con la regla del elemento nombrado (EVA-08) y de señales con lenguaje de sugerencia (EVA-09); recibe los resultados de las unidades previas como contexto.
- **`reanalisis_version`** (EVA-14, Deseable): extiende el transversal con la evaluación validada de la versión anterior y la instrucción de verificar correcciones.

Principios de diseño: cada plantilla declara **qué variables recibe** (contrato explícito, verificable en tests); las instrucciones de comportamiento del SRS (EVA-03, EVA-04, EVA-08, EVA-09) viven en el texto del prompt y su presencia es inspeccionable — son requisitos implementados en lenguaje natural; la calidad de las evaluaciones se valida con el set de calibración (sección 11), y **todo cambio de prompt exige re-correr la calibración** antes de usarse en evaluaciones reales — exactamente como una regresión de código.

## 9. Manejo de errores y estados

Taxonomía y comportamiento:

- **Errores de archivo** (corrupto, protegido, sin texto extraíble): se reportan por archivo sin abortar la carga (ING-06); un artefacto inextraíble equivale a ausente para el análisis, con la advertencia correspondiente (ING-05).
- **Errores de configuración** (rúbrica inválida, clave ausente): bloquean el inicio del análisis con mensaje accionable (CFG-01, CFG-08); nunca se descubren a mitad de pipeline — la preparación (paso 1) valida todo antes de gastar el primer token.
- **Errores de API** (red, timeout, límite de tasa, respuesta inválida): reintentos según política; agotados → `análisis_interrumpido`, reanudable (EVA-10, EVA-13).
- **Inconsistencia base↔carpetas**: detectada por la verificación de integridad al abrir el ciclo; reporte al docente y reconstrucción del trabajo de evaluación desde los archivos (AD-03, incluyendo `decisiones.json`); los metadatos operativos se recuperan desde el respaldo del directorio raíz o por recarga manual.

Regla general: ningún error deja la persistencia en estado intermedio no reanudable (RNF-06); las escrituras de cada unidad son atómicas (transacción SQLite + escritura de archivo con renombre final).

## 10. Seguridad y privacidad

- **Clave de API**: en configuración de usuario, fuera del directorio del ciclo (sección 5.2); jamás en logs, informes, instantáneas ni persistencia del ciclo (CFG-07, RNF-04). Comunicación exclusivamente HTTPS (el SDK oficial lo garantiza).
- **Datos personales**: los nombres de integrantes viven solo en `qhaway.db` local; el armado de contexto para la API toma contenido únicamente de los archivos de entrega y la configuración — estructuralmente no hay ruta por la que los datos de GRP lleguen al conector (RNF-05).
- **Documentos de entrega**: viajan como fueron presentados; la advertencia correspondiente forma parte de la guía de uso (RNF-05, RNF-10).

## 11. Estrategia de verificación

Tres niveles, alineados con las capas:

- **Unitarias sobre el dominio** (pytest, sin mocks de infraestructura): cálculo de nota con todos sus casos borde (críticos, artefactos ausentes, redondeo de mitades — los casos del Apéndice B del SRS son los primeros tests), validación de rúbricas (los casos inválidos de CFG-01), verificaciones DET, máquina de estados.
- **Integración con conector falso**: un `ConectorFalso` que implementa la interfaz neutral (AD-06) con respuestas predefinidas — incluyendo respuestas inválidas y fallas — permite testear el pipeline completo, la reanudación (EVA-10) y la validación (EVA-13) sin gastar un token.
- **Calibración de EVA** (el testing específico de IA): un set de entregas reales del ciclo anterior con evaluación docente conocida; se corre el pipeline real y se compara la salida contra el criterio del docente. Es la verificación de EVA-01/03/07/08, se re-ejecuta ante todo cambio de prompt o de modelo (sección 8), y sus resultados se documentan. Este set es, además, la herramienta de mejora continua del sistema.

## 12. Empaquetado y despliegue

- **Distribución**: ejecutable autocontenido por plataforma (PyInstaller como candidato principal), Windows 10/11 y Ubuntu 22.04+ (RNF-03, RNF-10). La prueba de concepto de empaquetado (incluyendo WeasyPrint/motor PDF, el punto más frágil de congelar) se realiza al inicio de la construcción, no al final.
- **Ubicaciones por plataforma**: configuración de usuario y clave en `%APPDATA%/qhaway` / `~/.config/qhaway`; los ciclos donde el docente elija (directorio raíz configurable, IEX-03).
- **Primera ejecución**: asistente mínimo que guía la configuración de la clave (con la prueba de conexión CFG-08) y la creación del primer ciclo — el camino crítico de RNF-08.
- **Actualizaciones**: manuales en el MVP (descargar nueva versión); los datos de ciclos son compatibles hacia adelante mediante versionado del esquema SQLite (campo de versión + migraciones).

## 13. Cuestiones abiertas para el inicio de la construcción

Entregables y decisiones identificados que no pertenecen a este documento pero condicionan la construcción, en orden de urgencia:

1. **Esquema JSON de las salidas estructuradas** de la API (campos exactos de observación, valoración, pregunta y señal): es el contrato central entre conector, dominio y prompts. Se diseña antes de escribir cualquiera de los tres.
2. **Estrategia de referencias verificables sobre PDF** (EVA-01, DET-02): cómo se localiza una sección o bloque en documentos sin estructura semántica confiable (heurística de encabezados + número de página como respaldo). Es el problema técnico abierto más grande; se enfrenta en la etapa de Extracción+DET.
3. **Spike de costo**: una llamada real con una entrega del ciclo anterior, medición de tokens y proyección a 13 grupos × 5 unidades, para validar el presupuesto (Visión §10) y elegir el modelo por defecto (IEX-02).
4. **Contenidos de configuración reales**: la rúbrica de la cátedra (reemplaza los ejemplos del Apéndice A del SRS), los checklists por defecto por tipo de documento (CFG-05), la tabla completa de nomenclatura (CFG-06) y las palabras clave de clasificación (ING-03).
5. **Pruebas de concepto declaradas**: HTML→PDF (AD-09) y congelamiento con PyInstaller incluyendo el motor elegido (§12). Bloqueantes de sus decisiones respectivas; se ejecutan en la semana 0.
6. **Set de calibración**: selección de entregas reales del ciclo anterior con evaluación docente conocida (§11). Se arma en paralelo desde el inicio.
7. **Diseño de `ui.revision`**: wireframe/`.ui` de la vista más compleja del sistema. Deliberadamente diferido hasta que el pipeline produzca borradores reales (ver orden de construcción en el plan de construcción).
