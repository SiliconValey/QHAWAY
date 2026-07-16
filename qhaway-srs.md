# QHAWAY — Especificación de Requisitos de Software (SRS)

**Versión:** 1.0
**Fecha:** Julio 2026
**Autor:** Christian — ISFT N.º 179
**Estándar de referencia:** IEEE 830-1998
**Documento base:** QHAWAY — Documento de Visión y Alcance v1.0

---

## 1. Introducción

### 1.1 Propósito

Este documento especifica los requisitos de software de **QHAWAY** en su versión MVP (Fase 1), conforme a la estructura del estándar IEEE 830-1998. Está dirigido a quienes diseñen, implementen y verifiquen el sistema, y a la comunidad docente y técnica que evalúe su adopción o contribución futura. Es, además, un documento pedagógico: sigue el mismo estándar que se exige a los proyectos de la materia de origen.

### 1.2 Alcance

QHAWAY es una aplicación de escritorio que asiste al docente en la evaluación de proyectos grupales de ingeniería de software. El MVP cubre la evaluación de la Exposición 1 del proyecto anual de la materia Algoritmos y Estructuras de Datos II (ISFT N.º 179): cuatro artefactos documentales (presentación de empresa, SRS, diseño funcional y UI de Qt Designer), evaluados mediante tres capas (verificación determinística, rúbrica calibrada con proyecto modelo y análisis transversal), con flujo de validación docente obligatorio, exportación de informes y monitoreo de costos. Quedan fuera del MVP el análisis de código (Fase 2), la generalización a otras materias (Fase 3) y todo lo listado como fuera de alcance en el documento de visión. El principio rector del sistema es que **la IA propone y el docente decide**: ninguna salida llega a los alumnos sin validación docente.

### 1.3 Definiciones, acrónimos y abreviaturas

- **Artefacto**: cada uno de los productos que componen una entrega (presentación, SRS, diseño funcional, UI).
- **Ciclo lectivo**: año académico durante el cual los grupos desarrollan el proyecto.
- **Entrega**: conjunto de artefactos presentado por un grupo para una exposición.
- **Exposición**: instancia de evaluación con defensa oral; el proyecto anual tiene dos.
- **Proyecto modelo**: proyecto de referencia completo, elaborado por el docente, usado como calibración del nivel de calidad esperado.
- **Rúbrica**: definición estructurada de criterios de evaluación, con pesos y niveles cualitativos.
- **Borrador de corrección**: conjunto de elementos generados por el sistema (observaciones, valoraciones, nota sugerida, cuestionario, señales) pendiente de validación docente.
- **Señal para indagar**: aspecto llamativo de una entrega, marcado como sugerencia de profundización para la defensa oral, nunca como veredicto.
- **SRS/ERS**: Especificación de Requisitos de Software (Software Requirements Specification).
- **FD**: Diseño Funcional.
- **UI**: interfaz de usuario; en este contexto, el archivo `.ui` de Qt Designer.
- **API**: interfaz de programación de aplicaciones; aquí, el servicio de IA de Anthropic.
- **Token**: unidad de consumo de la API de IA, base de su facturación.

### 1.4 Referencias

1. QHAWAY — Documento de Visión y Alcance, v1.0 (julio 2026).
2. IEEE Std 830-1998, *Recommended Practice for Software Requirements Specifications*.
3. Documentación de la API de Anthropic (Messages API, prompt caching).
4. Convención de prefijos de nomenclatura de widgets adoptada por la cátedra.

### 1.5 Visión general del documento

La sección 2 describe el producto en su contexto: perspectiva, funciones, usuarios, restricciones y dependencias. La sección 3 contiene los requisitos específicos: funcionales (organizados en ocho módulos), de interfaces externas y no funcionales. Los apéndices especifican el esquema del archivo de rúbrica, el modelo de escala de valoración y la matriz de trazabilidad con el documento de visión.

## 2. Descripción general

### 2.1 Perspectiva del producto

QHAWAY es una aplicación de escritorio autónoma (Python/PySide6) que se ejecuta íntegramente en la máquina del docente, con una única dependencia externa en tiempo de evaluación: la API de IA de Anthropic, consumida por internet. La persistencia es local e híbrida: una base SQLite para metadatos (grupos, versiones, estados, consumo) y una estructura de carpetas navegable para archivos de entregas, análisis e informes. No existe componente servidor, servicio en la nube propio ni comunicación entre instalaciones: cada docente opera su instalación de forma independiente.

### 2.2 Funciones del producto

Las funciones se organizan en ocho módulos: **CFG** (configuración del ciclo: rúbrica YAML, proyecto modelo, checklists, clave de API, plantilla visual), **GRP** (gestión de grupos, versiones e historial multi-exposición), **ING** (carga, clasificación y extracción de contenido de entregas PDF/.docx/.ui), **DET** (verificación determinística local: completitud, elementos formales, nomenclatura), **EVA** (evaluación con IA por criterio y por artefacto, análisis transversal de consistencia, nota sugerida trazable, cuestionario de defensa, señales para indagar), **REV** (revisión docente elemento por elemento con trazabilidad interna de origen), **EXP** (exportación del informe de devolución y la guía de defensa) y **MON** (registro y visibilidad del consumo y costo de API).

### 2.3 Características de los usuarios

El usuario del MVP es el docente de la materia de origen, según el perfil definido en la sección 5 del documento de visión: dominio de los formatos de la disciplina, competencia para editar archivos de configuración, sin experiencia previa requerida en herramientas de IA más allá de la configuración inicial documentada de la cuenta de API. Los alumnos no interactúan con el sistema.

### 2.4 Restricciones

- Lenguaje e interfaz en español; plataforma de escritorio Windows y Linux.
- Implementación en Python con PySide6 (Qt).
- Escala de calificación institucional: enteros de 1 a 10, sin decimales ni medios puntos.
- Presupuesto operativo de API: USD 20 mensuales como tope de referencia.
- Motor de IA del MVP: API de Anthropic (con la integración aislada en un módulo propio para permitir proveedores alternativos en fases futuras).
- Los datos personales gestionados por la aplicación no deberán transmitirse al proveedor de IA.

### 2.5 Suposiciones y dependencias

Se asumen las condiciones de la sección 10 del documento de visión: entregas de contenido ficticio y carácter público; conexión a internet disponible durante la evaluación; cuenta de API de Anthropic propia del docente, con facturación en dólares por consumo. El sistema depende de la disponibilidad y estabilidad del servicio de API; su comportamiento ante interrupciones está especificado en EVA-10.

## 3. Requisitos específicos

### 3.1 Requisitos funcionales

Los requisitos funcionales se organizan por módulo:

| Prefijo | Módulo |
|---------|--------|
| CFG | Configuración del ciclo (rúbrica, proyecto modelo, checklist, API, plantilla visual) |
| GRP | Gestión de grupos e historial |
| ING | Ingesta y procesamiento de entregas (PDF, .docx, .ui) |
| DET | Verificación determinística (Capa 1) |
| EVA | Evaluación con IA (Capas 2 y 3) |
| REV | Revisión y validación docente |
| EXP | Exportación de informes |
| MON | Monitoreo de consumo y costos de API |

#### 3.1.1 CFG — Configuración del ciclo

**CFG-01 — Carga de rúbrica desde archivo YAML.** El sistema deberá cargar la rúbrica de evaluación desde un archivo YAML editable externamente, validar su estructura contra el esquema definido (Apéndice A) y, ante errores de formato o contenido, reportar el problema indicando la ubicación en el archivo. La validación deberá rechazar, como mínimo: valoraciones o niveles distintos de los cuatro canónicos (Apéndice B), pesos no numéricos o menores o iguales a cero, secciones faltantes para artefactos requeridos por la exposición, `tope_por_critico` fuera del rango 1-10 y rúbricas sin ningún criterio. Una rúbrica inválida no deberá poder usarse en una evaluación. *Prioridad: Esencial.*

**CFG-02 — Estructura de la rúbrica.** La rúbrica deberá organizarse en secciones por artefacto más una sección de criterios transversales a la entrega completa. Cada criterio deberá definir: identificador, descripción, peso relativo, marca opcional de crítico (`critico: true`) y descripción de qué se espera para cada nivel cualitativo. La rúbrica deberá definir además el tope de nota por criterio crítico insuficiente (por defecto: 6). *Prioridad: Esencial.*

**CFG-03 — Auditoría de ponderación.** Al cargar la rúbrica, el sistema deberá informar el peso efectivo (normalizado) de cada criterio sobre la nota final, de modo que el docente pueda auditar la ponderación antes de evaluar. La validación de pesos inválidos corresponde a CFG-01. *Prioridad: Esencial.*

**CFG-04 — Carga del proyecto modelo.** El sistema deberá permitir asociar al ciclo lectivo un proyecto modelo compuesto por un archivo por tipo de artefacto (presentación, SRS, diseño funcional, UI), en los mismos formatos aceptados para las entregas. *Prioridad: Esencial.*

**CFG-05 — Checklist de completitud configurable.** Los bloques obligatorios de cada tipo de documento (utilizados por DET) deberán definirse en un archivo de configuración editable, no estar cableados en el código. *Prioridad: Esencial.*

**CFG-06 — Convención de nomenclatura configurable.** Los prefijos esperados por tipo de widget para la verificación del archivo `.ui` deberán definirse en la configuración. La configuración por defecto incluida con la aplicación deberá contener la tabla completa de la convención de la cátedra (referencia 4), que forma parte de los entregables del proyecto. *Prioridad: Deseable.*

**CFG-07 — Almacenamiento de la clave de API.** El sistema deberá almacenar la clave de API de Anthropic en un archivo de configuración local del usuario. La clave no deberá aparecer nunca en los informes exportados, en los archivos de evaluación persistidos ni en los registros de la aplicación. *Nota de evolución: en Fase 3 el almacenamiento deberá migrar al almacén de credenciales del sistema operativo (keyring).* *Prioridad: Esencial.*

**CFG-08 — Verificación de conexión.** El sistema deberá ofrecer una acción de prueba de conexión que valide la clave de API con una llamada mínima y reporte el resultado, para diagnosticar problemas de configuración antes de una evaluación real. *Prioridad: Deseable.*

**CFG-09 — Plantilla visual de informes.** El sistema deberá permitir configurar la plantilla visual de los informes PDF exportados. El MVP deberá incluir como plantilla por defecto el sistema visual dark-theme de la cátedra de origen. *Prioridad: Deseable.*

**CFG-10 — Parámetros del ciclo lectivo.** El sistema deberá permitir definir los parámetros generales del ciclo: nombre del ciclo (por ejemplo, "AED II — 2027"), cantidad de preguntas del cuestionario de defensa (por defecto: 10; mínimo: 1) y cantidad de exposiciones (por defecto: 2). *Prioridad: Esencial.*

**CFG-11 — Congelamiento de la configuración por evaluación.** Al iniciar el análisis de una entrega, el sistema deberá tomar una instantánea de la rúbrica, el checklist, la configuración de nomenclatura y las plantillas de prompts utilizadas (con sus versiones), y asociarla a esa evaluación. Las modificaciones posteriores de los archivos de configuración no deberán afectar evaluaciones en curso ni cerradas, y la reconstrucción exigida por RNF-09 deberá realizarse desde la instantánea. *Prioridad: Esencial.*

#### 3.1.2 GRP — Gestión de grupos e historial

**GRP-01 — Alta de grupos.** El sistema deberá permitir dar de alta grupos dentro del ciclo lectivo activo, registrando: nombre del grupo, lista de integrantes y nombre del proyecto/empresa ficticia. *Prioridad: Esencial.*

**GRP-02 — Modificación de grupos con historial.** El sistema deberá permitir editar la composición de un grupo (altas, bajas y cambios de integrantes) durante el ciclo lectivo. Toda modificación deberá quedar registrada con fecha, de modo que pueda reconstruirse la composición exacta del grupo al momento de cada exposición. *Prioridad: Esencial.*

**GRP-03 — Espacio persistente por grupo.** Cada grupo deberá poseer un espacio de almacenamiento propio donde se acumulen sus entregas, análisis y evaluaciones validadas, siguiendo el modelo híbrido de persistencia: metadatos en la base local, archivos de entregas y resultados en una estructura de carpetas navegable por el docente con el explorador del sistema. *Prioridad: Esencial.*

**GRP-04 — Historial completo por versiones.** Toda entrega y toda evaluación deberán conservarse como versiones: una re-entrega (recuperatorio, corrección) o una re-evaluación deberá crear una versión nueva sin eliminar ni sobrescribir las anteriores. La **versión vigente** de cada exposición será por defecto la última cargada, y el docente deberá poder cambiar esa designación manualmente; la nota y el estado del grupo (GRP-06) corresponden siempre a la versión vigente. *Prioridad: Esencial.*

**GRP-05 — Soporte del contexto multi-exposición.** El modelo de datos deberá vincular las entregas y evaluaciones de un grupo a través de las exposiciones del ciclo, de modo que el análisis de la Exposición 2 (EVA-11, Fase 2) pueda recuperar íntegramente el contexto de la Exposición 1 sin cambios estructurales. *Prioridad: Esencial (habilitante de Fase 2).*

**GRP-06 — Vista de estado del ciclo.** El sistema deberá presentar una vista general de los grupos del ciclo con el estado de cada uno respecto de la exposición en curso: sin entrega, entrega cargada, análisis en curso, análisis interrumpido (reanudable), borrador en revisión, evaluación validada, informe exportado. *Prioridad: Deseable.*

**GRP-07 — Respaldo transparente.** Dado el modelo híbrido de persistencia, el sistema deberá documentar (y la estructura de carpetas deberá permitir) el respaldo completo de un ciclo lectivo copiando un único directorio raíz. La base SQLite deberá residir dentro de ese directorio raíz. *Prioridad: Deseable.*

**GRP-08 — Archivado de grupos.** El sistema deberá permitir archivar un grupo (baja lógica): el grupo deja de aparecer en la operación corriente pero su historial completo se conserva y permanece auditable (RNF-09). No deberá existir eliminación física de grupos con evaluaciones registradas. *Prioridad: Deseable.*

#### 3.1.3 ING — Ingesta y procesamiento de entregas

**ING-01 — Carga de entregas por grupo.** El sistema deberá permitir cargar los archivos de una entrega (incluyendo arrastrar y soltar) al espacio del grupo correspondiente, asociándolos a la exposición en curso. *Prioridad: Esencial.*

**ING-02 — Formatos aceptados.** El sistema deberá aceptar archivos PDF, Word (.docx) y Qt Designer (.ui). Los archivos de otros formatos deberán rechazarse con un mensaje que indique los formatos válidos. *Prioridad: Esencial.*

**ING-03 — Clasificación por tipo de artefacto.** El sistema deberá asignar cada archivo cargado a un tipo de artefacto (presentación, SRS, diseño funcional, UI), proponiendo la clasificación automáticamente cuando sea inferible y permitiendo al docente corregirla. Reglas mínimas de inferencia: extensión `.ui` → artefacto UI; nombre de archivo que contenga palabras clave configurables (por ejemplo "srs", "ers", "diseño", "presentacion") → tipo correspondiente. Por defecto, cada tipo de artefacto admite un único archivo; ante una clasificación duplicada el sistema deberá advertirlo, y un artefacto multi-archivo solo será válido con confirmación explícita del docente. Una entrega no deberá poder analizarse con artefactos sin clasificar. *Prioridad: Esencial.*

**ING-04 — Extracción de contenido.** El sistema deberá extraer el contenido textual y estructural de cada archivo: texto y estructura de PDF y .docx, y árbol de objetos (widgets, nombres, jerarquía) del XML de los archivos .ui. *Prioridad: Esencial.*

**ING-05 — Detección de entrega incompleta.** Si al iniciar el análisis faltan tipos de artefacto requeridos por la exposición, el sistema deberá advertirlo y requerir confirmación explícita del docente para continuar con una entrega parcial. La ausencia deberá reflejarse en el borrador de corrección y en la nota (EVA-05). Una entrega sin ningún archivo no deberá poder analizarse bajo ninguna circunstancia. *Prioridad: Esencial.*

**ING-06 — Manejo de archivos problemáticos.** Ante un archivo corrupto, protegido con contraseña o del cual no pueda extraerse contenido (por ejemplo, un PDF escaneado sin texto), el sistema deberá informarlo identificando el archivo y el problema, sin abortar la carga del resto de la entrega. *Prioridad: Esencial.*

#### 3.1.4 DET — Verificación determinística

**DET-01 — Ejecución previa y local.** La verificación determinística deberá ejecutarse antes del análisis con IA, íntegramente en la máquina local, sin consumo de API. Sus resultados deberán persistirse y entregarse como contexto a EVA. *Prioridad: Esencial.*

**DET-02 — Verificación de completitud documental.** El sistema deberá verificar, por cada documento, la presencia de los bloques obligatorios definidos en el checklist configurable (CFG-05), reportando cada bloque como presente o ausente. *Prioridad: Esencial.*

**DET-03 — Verificación de elementos formales.** El sistema deberá verificar los elementos formales requeridos de cada documento definidos en la configuración: carátula, índice y secciones numeradas. *Prioridad: Esencial.*

**DET-04 — Verificación de nomenclatura del archivo .ui.** El sistema deberá recorrer el árbol de objetos del archivo .ui y verificar cada nombre contra la convención de prefijos configurada (CFG-06), reportando por cada objeto no conforme: nombre actual, tipo de widget y prefijo esperado. *Prioridad: Esencial.*

**DET-05 — Reporte reproducible.** El resultado de la verificación determinística deberá ser reproducible: las mismas entradas y la misma configuración deberán producir exactamente el mismo reporte. Los hallazgos deberán presentarse en el borrador de corrección en una categoría propia, distinguible de las observaciones generadas por IA. *Prioridad: Esencial.*

#### 3.1.5 EVA — Evaluación con IA

**EVA-01 — Evaluación por criterio de rúbrica.** Para cada criterio de la rúbrica aplicable al artefacto en análisis, el sistema deberá generar mediante la API de IA: (a) una o más observaciones fundamentadas, con referencia verificable a la parte del documento que las motiva (sección o elemento identificable; para la UI, el objeto involucrado), y (b) una valoración en uno de cuatro niveles cualitativos: **Insuficiente, Regular, Bueno, Excelente**. *Prioridad: Esencial.*

**EVA-02 — Análisis por artefacto.** El análisis con IA deberá ejecutarse de forma independiente por artefacto (presentación, SRS, diseño funcional, UI), en llamadas separadas, seguido de una pasada transversal sobre la entrega completa. Cada análisis por artefacto deberá recibir como contexto: la sección correspondiente de la rúbrica, el artefacto homólogo del proyecto modelo y los resultados de la verificación determinística (DET) de ese artefacto. *Prioridad: Esencial.*

**EVA-03 — Calibración sin penalizar la diferencia.** Las instrucciones enviadas a la IA deberán establecer explícitamente que el proyecto modelo es una referencia del nivel de calidad esperado y no una plantilla: las soluciones distintas pero correctas no deberán generar observaciones negativas por su diferencia con el modelo. *Prioridad: Esencial.*

**EVA-04 — Coherencia con los hallazgos determinísticos.** El análisis con IA deberá recibir los hallazgos de la Capa 1 (DET) como hechos ya verificados y **no deberá contradecirlos** (*Prioridad: Esencial*). Adicionalmente, no deberá re-detectarlos, limitándose a elaborarlos — por ejemplo, explicar el impacto de un bloque faltante (*Prioridad: Deseable*).

**EVA-05 — Cálculo de la nota sugerida.** El sistema deberá calcular la nota sugerida como la suma ponderada de las valoraciones por criterio, según el mapeo nivel→valor y los pesos definidos en la rúbrica (ver Apéndices A y B), redondeada al entero más próximo en la escala 1-10. La composición deberá ser trazable: el docente deberá poder ver el aporte de cada criterio al resultado. Si un artefacto requerido está ausente (entrega parcial confirmada, ING-05), todos los criterios de su sección deberán valorarse **Insuficiente** — incluidos los críticos, con la consecuente aplicación de EVA-06 —; los criterios de artefactos ausentes nunca se excluyen del promedio ni se renormaliza sin ellos. *Prioridad: Esencial.*

**EVA-06 — Regla de criterio crítico.** Los criterios de la rúbrica podrán marcarse como críticos (`critico: true`). Si al menos un criterio crítico recibe la valoración Insuficiente, la nota sugerida no deberá superar el tope configurado en la rúbrica (valor por defecto: 6), independientemente de la suma ponderada. La aplicación de esta regla deberá quedar explícita en la composición de la nota. *Prioridad: Esencial.*

**EVA-07 — Análisis transversal de consistencia.** La pasada transversal deberá verificar la trazabilidad entre artefactos —cada requisito del SRS reflejado en el diseño funcional; cada pantalla del diseño funcional presente en la UI entregada— y generar observaciones específicas por cada inconsistencia detectada, identificando los elementos involucrados. *Prioridad: Esencial.*

**EVA-08 — Cuestionario de defensa.** El sistema deberá generar **10 preguntas de defensa** por entrega (cantidad configurable), específicas de las decisiones tomadas por el grupo en sus propios artefactos, orientadas a verificar comprensión. Criterio de aceptación: cada pregunta deberá referenciar al menos un elemento nombrado de la entrega del grupo (un requisito concreto, una pantalla, un objeto de la UI, una decisión documentada); las preguntas aplicables a cualquier entrega no satisfacen este requisito. *Prioridad: Esencial.*

**EVA-09 — Señales para indagar.** El sistema podrá marcar aspectos llamativos de la entrega como señales para profundizar en la defensa oral. Las señales deberán presentarse en una categoría separada de las observaciones de corrección, con lenguaje de sugerencia y nunca de veredicto, y no deberán influir en la nota sugerida. *Prioridad: Deseable.*

**EVA-10 — Persistencia y reanudación del análisis.** El sistema deberá persistir el resultado de cada análisis por artefacto apenas se completa. Ante una interrupción (falla de la API, corte de conexión, cierre de la aplicación), el sistema deberá poder reanudar el análisis desde el último artefacto completado, sin repetir los análisis ya realizados. La pasada transversal constituye una unidad de reanudación propia: si la interrupción ocurre durante ella, solo ella se repite. Nota: la reanudación evita repetir el costo de los análisis completados, pero puede implicar el sobrecosto de reconstruir el caché de contexto de la API si este expiró durante la interrupción (ver EVA-12); dicho sobrecosto deberá registrarse en MON-01. *Prioridad: Esencial.*

**EVA-11 — Contexto multi-exposición.** Al analizar una entrega de la Exposición 2, el sistema deberá incorporar como contexto el historial de la Exposición 1 del mismo grupo (entrega, evaluación validada y observaciones). *Alcance: fuera del MVP (Fase 2); el modelo de datos del MVP deberá soportarlo (GRP-05).*

**EVA-12 — Optimización de contexto repetido.** El sistema deberá utilizar el mecanismo de cacheo de contexto de la API para los contenidos que se repiten entre análisis (rúbrica, proyecto modelo, instrucciones), minimizando el costo por entrega. *Prioridad: Deseable.*

**EVA-13 — Validación de las respuestas de la IA.** Toda respuesta de la API deberá validarse contra la estructura esperada antes de persistirse: formato correcto, valoraciones dentro de los cuatro niveles canónicos, referencias presentes. Ante una respuesta inválida, el sistema deberá reintentar según la política de IEX-02; agotados los reintentos, el criterio o análisis afectado deberá marcarse como **pendiente** — nunca completarse con datos inválidos — y el estado resultante deberá ser reanudable según EVA-10. *Prioridad: Esencial.*

**EVA-14 — Contexto de re-entrega (misma exposición).** Al analizar una nueva versión de entrega de una exposición ya evaluada (recuperatorio, corrección), el sistema deberá incorporar como contexto la evaluación validada de la versión anterior, instruyendo a la IA a verificar específicamente si las observaciones señaladas fueron corregidas. *Prioridad: Deseable.*

#### 3.1.6 REV — Revisión y validación docente

**REV-01 — Presentación del borrador.** El sistema deberá presentar el borrador de corrección organizado por artefacto y por criterio, incluyendo: hallazgos determinísticos, observaciones de IA, análisis transversal, señales para indagar, composición de la nota sugerida y cuestionario de defensa. *Prioridad: Esencial.*

**REV-02 — Validación por elemento.** El docente deberá poder, sobre cada elemento generado (observación, pregunta de defensa, señal para indagar): **aceptarlo**, **editarlo** o **descartarlo**. Ningún elemento deberá incluirse en las salidas exportadas sin haber sido aceptado o editado. *Prioridad: Esencial.*

**REV-03 — Observaciones propias.** El docente deberá poder agregar observaciones y preguntas de defensa propias en cualquier punto del borrador, con el mismo tratamiento que los elementos generados. *Prioridad: Esencial.*

**REV-04 — Ajuste de valoraciones y nota.** El docente deberá poder modificar la valoración cualitativa de cualquier criterio (con recálculo automático de la nota sugerida) y fijar una nota final distinta de la sugerida. El sistema deberá registrar ambas: la sugerida por composición y la final decidida por el docente. *Prioridad: Esencial.*

**REV-05 — Trazabilidad de origen (interna).** El sistema deberá registrar en la persistencia el origen de cada elemento del informe final: generado por IA y aceptado sin cambios, generado por IA y editado, o creado por el docente. Esta distinción es exclusivamente interna: no deberá aparecer en el informe exportado al grupo, que se presenta como devolución unificada de la cátedra. *Prioridad: Esencial.*

**REV-06 — Métricas de retrabajo.** A partir de REV-05, el sistema deberá poder informar por evaluación y por ciclo: porcentaje de elementos aceptados sin cambios, editados, descartados y agregados por el docente. Estas métricas son el instrumento de medición del criterio de éxito del MVP referido a la calidad del borrador. *Prioridad: Deseable.*

**REV-07 — Estado de revisión persistente.** La revisión deberá poder interrumpirse y retomarse: el estado de cada elemento (pendiente, aceptado, editado, descartado) deberá persistirse de forma continua. *Prioridad: Esencial.*

#### 3.1.7 EXP — Exportación de informes

**EXP-01 — Informe de devolución para el grupo.** El sistema deberá exportar en PDF, con la plantilla visual configurada (CFG-09), el informe de devolución: observaciones validadas organizadas por artefacto y criterio, hallazgos determinísticos, resultado del análisis de consistencia y nota final. El informe **no** deberá incluir las señales para indagar, el cuestionario de defensa ni ninguna marca de origen de los elementos (REV-05). *Prioridad: Esencial.*

**EXP-02 — Guía de defensa para el docente.** El sistema deberá exportar por separado la guía de defensa: cuestionario validado de preguntas y señales para indagar aceptadas, identificando el grupo y la exposición. *Prioridad: Esencial.*

**EXP-03 — Exportación solo desde evaluación validada.** La exportación solo deberá estar disponible cuando no queden elementos pendientes de revisión (REV-07) y el docente haya confirmado la nota final. *Prioridad: Esencial.*

**EXP-04 — Archivado de exportaciones.** Todo informe exportado deberá archivarse en el espacio del grupo como parte de la versión de evaluación correspondiente (GRP-04). *Prioridad: Esencial.*

#### 3.1.8 MON — Monitoreo de consumo y costos

**MON-01 — Registro de consumo por análisis.** El sistema deberá registrar, por cada llamada a la API: tokens de entrada y salida, tokens servidos desde caché y costo estimado en dólares, asociados a la entrega y al grupo. El costo estimado deberá calcularse a partir de una **tabla de precios por modelo configurable y editable** (los precios del proveedor cambian con el tiempo), incluida con valores por defecto en la configuración de la aplicación. *Prioridad: Esencial.*

**MON-02 — Costo visible por evaluación.** Al finalizar el análisis de una entrega, el sistema deberá mostrar el costo total estimado de esa evaluación. *Prioridad: Esencial.*

**MON-03 — Acumulado y presupuesto mensual.** El sistema deberá mostrar el consumo acumulado del mes calendario contra un presupuesto configurable (por defecto: USD 20) y advertir al superar un umbral configurable (por defecto: 80%). El sistema no deberá bloquear análisis por presupuesto; la decisión es del docente. *Prioridad: Esencial.*

**MON-04 — Histórico exportable.** El sistema deberá permitir consultar y exportar el histórico de consumo por ciclo lectivo, como insumo para validar el supuesto de presupuesto del documento de visión. *Prioridad: Deseable.*

### 3.2 Requisitos de interfaces externas

**IEX-01 — Interfaz de usuario.** Interfaz gráfica de escritorio construida con PySide6, en español, organizada alrededor de la vista de estado del ciclo (GRP-06) y del flujo de revisión (REV). Las operaciones de larga duración (análisis con IA) no deberán bloquear la interfaz y deberán mostrar progreso por artefacto.

**IEX-02 — API de IA.** Integración con la Messages API de Anthropic, incluyendo su mecanismo de cacheo de contexto (EVA-12), aislada en un módulo conector propio. El conector deberá exponer una interfaz interna neutral respecto del proveedor, para habilitar alternativas en fases futuras sin impacto en el resto del sistema. El conector deberá implementar una política configurable de timeouts y reintentos con retroceso exponencial (por defecto: 3 reintentos) antes de declarar el análisis interrumpido (EVA-10); todos los reintentos y su costo deberán registrarse en MON-01. El modelo de IA a utilizar deberá ser configurable, con un valor por defecto definido en la configuración de la aplicación.

**IEX-03 — Sistema de archivos.** Lectura de los formatos de entrega (PDF, .docx, .ui) y escritura de la estructura de persistencia híbrida (base SQLite + directorio raíz del ciclo) y de los PDF exportados. El directorio raíz del ciclo deberá ser configurable.

### 3.3 Requisitos no funcionales

**RNF-01 — Rendimiento del análisis.** El análisis completo de una entrega de Exposición 1 (cuatro artefactos más pasada transversal) deberá completarse en **menos de 5 minutos**, medido con la API respondiendo dentro de sus latencias publicadas y sin reintentos. El procesamiento local (extracción, verificación determinística, composición del borrador) no deberá superar los 30 segundos de ese total. El proceso no es interactivo: la prioridad es la calidad del borrador sobre la latencia.

**RNF-02 — Rendimiento de la interfaz.** Las operaciones locales (navegación, revisión de elementos, recálculo de nota) deberán responder en menos de 1 segundo.

**RNF-03 — Portabilidad.** El sistema deberá ejecutarse en Windows 10/11 y en Ubuntu 22.04 LTS o superior (distribución Linux de referencia para verificación), sin diferencias funcionales.

**RNF-04 — Seguridad de credenciales.** La clave de API se almacenará según CFG-07; no deberá registrarse en logs, informes ni archivos de evaluación. Las comunicaciones con la API deberán realizarse exclusivamente por HTTPS.

**RNF-05 — Privacidad de datos personales.** Los datos personales gestionados por la aplicación (nombres de integrantes y metadatos de grupos, módulo GRP) residirán exclusivamente en la persistencia local y nunca deberán agregarse por el sistema al contenido enviado a la API. Los documentos de entrega, en cambio, se envían tal como fueron presentados y pueden contener los nombres que los propios alumnos incluyeron (por ejemplo, en la carátula); esta condición está asumida en el documento de visión (entregas de carácter público) y deberá informarse explícitamente en la guía de uso.

**RNF-06 — Confiabilidad y reanudación.** Ninguna interrupción (falla de API, corte de energía, cierre de la aplicación) deberá producir pérdida de trabajo validado ni corrupción de datos: los análisis se reanudan según EVA-10 y la revisión según REV-07.

**RNF-07 — Mantenibilidad y extensibilidad.** La arquitectura deberá mantener separadas las capas de evaluación (DET/EVA), el conector de IA (IEX-02) y la interfaz, de modo que la incorporación del análisis de código (Fase 2) y de nuevos tipos de artefacto (Fase 3) no requiera rediseño estructural.

**RNF-08 — Usabilidad.** Un docente que cumpla el perfil de la sección 2.3 deberá poder completar su primera evaluación asistido únicamente por la guía de instalación y uso, sin soporte adicional. Verificación: guion de prueba de primera evaluación completa (instalación, configuración de API, alta de rúbrica y grupo, análisis, revisión y exportación), ejecutado por al menos un docente distinto del autor antes de la Fase 3.

**RNF-09 — Auditabilidad.** Toda evaluación exportada deberá poder reconstruirse desde la persistencia: versión de la entrega, instantánea de la rúbrica y configuración utilizadas (CFG-11), hallazgos, decisiones de revisión (con origen según REV-05), composición de la nota y fecha de cada paso.

**RNF-10 — Distribución e instalación.** El MVP deberá distribuirse como paquete instalable o ejecutable autocontenido para Windows y Linux, acompañado de la guía de instalación y uso, que deberá incluir el paso de creación y configuración de la cuenta de API (CFG-07) y la advertencia de privacidad de RNF-05.

## 4. Apéndices

### Apéndice A — Estructura del archivo de rúbrica (YAML)

Esquema del archivo, con un ejemplo abreviado y criterios ilustrativos (a reemplazar por la rúbrica real de la cátedra):

```yaml
rubrica:
  nombre: "AED II — Proyecto anual — Exposición 1"
  escala:
    tope_por_critico: 6        # nota máxima si un criterio crítico da Insuficiente
    # Los cuatro niveles (Insuficiente/Regular/Bueno/Excelente) son FIJOS en el MVP
    # y no se declaran en el archivo; una rúbrica que declare otros niveles
    # o valore fuera de los canónicos es inválida (CFG-01).

  secciones:
    - artefacto: srs
      criterios:
        - id: SRS-REQ
          descripcion: "Los requisitos funcionales son completos, no ambiguos y verificables"
          peso: 3
          critico: true
          niveles:
            Insuficiente: "Requisitos ausentes, vagos o no verificables"
            Regular: "Requisitos presentes pero con ambigüedades o vacíos importantes"
            Bueno: "Requisitos claros y verificables, con omisiones menores"
            Excelente: "Requisitos completos, precisos y verificables en su totalidad"
        - id: SRS-EST
          descripcion: "El documento respeta la estructura IEEE 830 exigida"
          peso: 1
          niveles:
            Insuficiente: "No sigue la estructura"
            Regular: "Estructura parcial o desordenada"
            Bueno: "Estructura correcta con detalles menores"
            Excelente: "Estructura completa y prolija"

    - artefacto: ui
      criterios:
        - id: UI-NOM
          descripcion: "Los objetos respetan la convención de prefijos de la cátedra"
          peso: 1
          niveles:
            Insuficiente: "La mayoría de los objetos no la respeta"
            Regular: "Cumplimiento parcial"
            Bueno: "Cumplimiento casi total"
            Excelente: "Cumplimiento total"

  transversales:
    criterios:
      - id: TRZ-SRS-FD
        descripcion: "Cada requisito del SRS está reflejado en el diseño funcional"
        peso: 2
        critico: true
        niveles:
          Insuficiente: "La mayoría de los requisitos no tiene correlato en el FD"
          Regular: "Trazabilidad parcial con vacíos significativos"
          Bueno: "Trazabilidad casi completa"
          Excelente: "Trazabilidad completa y explícita"
```

Notas del esquema: los pesos son relativos (el sistema los normaliza e informa el peso efectivo, CFG-03); cada sección de artefacto aplica solo a ese artefacto; los criterios transversales se evalúan en la pasada transversal (EVA-07); las descripciones por nivel son el insumo directo de las instrucciones a la IA (EVA-01); la rúbrica deberá contener una sección por cada artefacto requerido por la exposición (CFG-01).

### Apéndice B — Modelo de escala de valoración

Cada nivel cualitativo mapea a un valor numérico de referencia:

| Nivel | Valor |
|---|---|
| Insuficiente | 2 |
| Regular | 5 |
| Bueno | 8 |
| Excelente | 10 |

La **nota sugerida** se calcula como el promedio de los valores de todos los criterios, ponderado por sus pesos normalizados, redondeado al entero más próximo (mitades hacia arriba — nótese que difiere del redondeo bancario de `round()` en Python, que deberá evitarse) y acotado al rango 1-10. Si algún criterio con `critico: true` recibe Insuficiente, la nota sugerida se acota al `tope_por_critico` (EVA-06), y la aplicación de la regla se muestra en la composición. El valor por defecto del tope (6) corresponde al umbral institucional habitual de aprobación. Los criterios de un artefacto ausente valoran Insuficiente y nunca se excluyen del promedio (EVA-05). El mapeo de valores es fijo en el MVP; su parametrización por rúbrica queda para la Fase 3.

**Ejemplo**: tres criterios con pesos 3, 1 y 2, valorados Bueno (8), Excelente (10) y Regular (5): nota = (3×8 + 1×10 + 2×5) / 6 = 44/6 = 7,33 → **7**. Si el tercer criterio fuera crítico y diera Insuficiente (2): nota = (3×8+1×10+2×2)/6 = 6,33 → 6, y por regla de crítico el tope 6 ya la acota: **6**.

### Apéndice C — Matriz de trazabilidad con el documento de visión

| Punto del alcance del MVP (Visión, sección 4) | Requisitos que lo implementan |
|---|---|
| Evaluación de los cuatro artefactos | ING-01..06, EVA-01, EVA-02 |
| Formatos PDF, .docx, .ui | ING-02, ING-04 |
| Análisis del .ui y nomenclatura | ING-04, DET-04, CFG-06 |
| Rúbrica editable en archivo | CFG-01, CFG-02, CFG-03, Apéndice A |
| Proyecto modelo como calibración | CFG-04, EVA-03 |
| Checklist determinístico de completitud | CFG-05, DET-01, DET-02, DET-03, DET-05, EVA-04 |
| Consistencia entre artefactos | EVA-07, criterios transversales (Apéndice A) |
| Gestión de grupos con persistencia e historial | GRP-01..08 |
| Historial por versiones y re-entregas | GRP-04, EVA-14, EXP-04 |
| Flujo docente asistido (propone/decide) | EVA-05, EVA-06, REV-01..07, EXP-03 |
| Cuestionario de defensa | EVA-08, REV-02, EXP-02, CFG-10 |
| Señales para indagar | EVA-09, REV-02, EXP-02 (materialización), EXP-01 (exclusión del informe al grupo) |
| Exportación PDF con plantilla | EXP-01..04, CFG-09 |
| Motor de IA: API de Claude | IEX-02, EVA-12, EVA-13, CFG-07, CFG-08 |
| Presupuesto y costos (Visión, sección 10) | MON-01..04, EVA-12 |
| Confiabilidad ante interrupciones (Visión, sección 10: riesgos) | EVA-10, EVA-13, REV-07, RNF-06, GRP-06 |
| Privacidad de datos personales (Visión, sección 10) | RNF-05, CFG-07 |
| Auditabilidad de la evaluación (Visión: nota trazable) | CFG-11, REV-05, RNF-09 |
| Preparación para Exposición 2 (Fase 2) | GRP-05, EVA-11, RNF-07 |

Los requisitos de interfaz (IEX-01, IEX-03) y los no funcionales de plataforma y calidad (RNF-01..04, RNF-08, RNF-10) no trazan a puntos puntuales del alcance sino a las restricciones generales del documento de visión (plataforma de escritorio, perfil de usuario, presupuesto), y se listan aquí para constancia de que su ausencia en las filas anteriores es deliberada.
