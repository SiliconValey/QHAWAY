# QHAWAY — Documento de Visión y Alcance

**Versión:** 1.0
**Fecha:** Julio 2026
**Autor:** Christian — ISFT N.º 179
**Licencia del proyecto:** MIT (repositorio público a partir de la Fase 3)

---

## 1. Resumen ejecutivo

**QHAWAY** (del quechua *qhaway*: observar, examinar) es un asistente de corrección de código abierto que le devuelve al docente el tiempo para enseñar. Es una aplicación de escritorio (Python/PySide6) que asiste la evaluación de proyectos grupales de ingeniería de software: analiza las entregas de los alumnos contra una rúbrica definida por el docente y un proyecto modelo de referencia, y produce un borrador de corrección completo — observaciones fundamentadas por criterio, verificación de completitud, análisis de consistencia entre artefactos, una nota sugerida trazable y un cuestionario de defensa personalizado para la exposición oral.

El problema que ataca es concreto: corregir a fondo un proyecto grupal multi-artefacto lleva alrededor de una hora, y lo más costoso no es detectar los problemas sino redactar la devolución. Con trece grupos y dos exposiciones anuales, el resultado inevitable es un feedback más pobre del que los alumnos necesitan y análisis —como la trazabilidad entre SRS, diseño e interfaz— que directamente no se hacen. QHAWAY invierte la ecuación: el análisis exhaustivo lo hace la herramienta; el docente dedica su tiempo a validar, ajustar y enriquecer. El ahorro de tiempo es la consecuencia; el feedback rico es el objetivo.

El principio rector del proyecto es innegociable: **la IA propone, el docente decide**. QHAWAY nunca asignará una calificación de forma autónoma; toda observación es un borrador que el docente acepta, edita o descarta. Frente al uso de IA por parte de los alumnos, el proyecto adopta una postura pedagógica explícita: no detectores de plagio —técnicamente poco confiables e injustos—, sino verificación de comprensión mediante un cuestionario de defensa generado a partir de la propia entrega de cada grupo.

El MVP se acota deliberadamente a un caso real: la primera exposición anual de la materia **Algoritmos y Estructuras de Datos II** del ISFT N.º 179 (Buenos Aires), con validación en aula como criterio de éxito medible — corregir los trece grupos en menos de la mitad del tiempo actual, con devoluciones más detalladas, dentro de un presupuesto operativo de USD 20 mensuales. Las fases siguientes incorporan el análisis de código (segunda exposición), la generalización a otras materias y la apertura del proyecto, bajo licencia MIT, a la comunidad docente.

## 2. El problema

Evaluar proyectos grupales de ingeniería de software es una de las tareas más valiosas y más costosas de la práctica docente. Cada entrega es un paquete de artefactos heterogéneos —una presentación institucional, un SRS según IEEE 830, un diseño funcional y una interfaz construida en Qt Designer— que deben evaluarse tanto individualmente como en conjunto.

En el caso concreto que origina este proyecto, la corrección completa de un grupo lleva **alrededor de una hora**. Con trece grupos y dos exposiciones anuales, son más de **26 horas por ciclo lectivo** dedicadas solo a corregir — y la parte que más tiempo consume no es detectar los problemas, sino **armar la devolución**: redactar para cada grupo qué debe mejorar y, sobre todo, por qué.

Esa presión de tiempo produce tres consecuencias conocidas por cualquier docente del área:

**Feedback más pobre del que los alumnos necesitan.** La devolución termina reducida a una nota y observaciones generales. El análisis detallado —qué requisito está mal especificado, qué pantalla no respeta la convención de nomenclatura, qué sección del SRS es genérica— existe en la cabeza del corrector, pero no llega al grupo porque redactarlo para trece equipos es inviable.

**La consistencia entre artefactos no se verifica a fondo.** Comprobar que cada requisito del SRS está reflejado en el diseño funcional, y que cada pantalla del diseño corresponde a la interfaz entregada, exige leer los documentos en paralelo, ida y vuelta. Es exactamente el tipo de análisis que más revela sobre la madurez de un trabajo, y el primero que se sacrifica por falta de tiempo.

**La evaluación pierde uniformidad.** El grupo corregido un sábado a la mañana no recibe el mismo nivel de detalle que el corregido un miércoles a la noche después de un día de trabajo. La rúbrica existe, pero aplicarla con idéntica profundidad trece veces seguidas es humanamente difícil.

A esto se suma un problema nuevo: los alumnos ya usan IA generativa para producir sus entregas. El desafío pedagógico no es impedirlo —es una herramienta que usarán toda su vida profesional— sino **verificar que comprenden lo que entregan**, algo que la corrección tradicional de documentos no puede determinar.

## 3. Visión de la solución

**QHAWAY es un asistente de corrección que le devuelve al docente el tiempo para enseñar.**

QHAWAY (del quechua *qhaway*: observar, examinar) es una aplicación de escritorio que asiste al docente en la evaluación de proyectos grupales de ingeniería de software. Analiza las entregas de los alumnos —documentación y, en fases futuras, código— contra una rúbrica definida por el docente y un proyecto modelo de referencia, y produce un borrador de corrección detallado: observaciones por criterio, verificación de completitud, análisis de consistencia entre artefactos, una nota sugerida y un cuestionario de defensa personalizado para la exposición oral.

QHAWAY no se limita a evaluar documentos: acompaña el **ciclo completo de evaluación**. Desde la entrega escrita hasta la defensa oral, la herramienta le da al docente insumos concretos para cada instancia — el informe de corrección para la devolución escrita y las preguntas de defensa para verificar la comprensión real del grupo el día de la exposición.

### Principio rector: la IA propone, el docente decide

Este principio es innegociable y define la identidad del proyecto: **QHAWAY nunca asignará una calificación de forma autónoma**, ni en esta versión ni en las futuras. Toda observación generada por la IA es un borrador que el docente puede aceptar, editar o rechazar; la nota sugerida es un insumo, no un veredicto. La responsabilidad pedagógica es del docente, y la herramienta está diseñada para potenciar su criterio, no para sustituirlo.

### El beneficio central: el feedback que los alumnos necesitan

Un docente que corrige a mano trece proyectos grupales —cada uno con presentación, SRS, diseño funcional e interfaz— debe elegir entre profundidad y viabilidad. El resultado habitual es un feedback superficial: una nota y un puñado de observaciones generales, cuando cada grupo merecería una devolución detallada de qué está bien, qué está mal y por qué. QHAWAY invierte esa ecuación: el análisis exhaustivo (criterio por criterio, documento por documento, incluida la trazabilidad entre artefactos que un corrector humano casi nunca llega a verificar) lo hace la herramienta; el docente dedica su tiempo a lo que sí requiere su criterio profesional: validar, ajustar y enriquecer esa devolución. El ahorro de tiempo es la consecuencia; el feedback rico es el objetivo.

### Hecho por un docente, para docentes

QHAWAY no nace de un plan de negocios: nace de un aula concreta. Su primer caso de uso son los trece grupos de una materia real, **Algoritmos y Estructuras de Datos II** (ISFT N.º 179, Buenos Aires), con un proyecto modelo completo construido por el propio docente como referencia de calidad. Esa raíz define su filosofía: las funcionalidades responden a dolores reales de la práctica docente, y el proyecto se abre a la comunidad educativa bajo licencia MIT para que cualquier docente pueda adoptarlo, adaptarlo y mejorarlo.

## 4. Alcance del MVP

El MVP de QHAWAY se acota deliberadamente al caso concreto de la materia de origen (**Algoritmos y Estructuras de Datos II**, ISFT N.º 179): la evaluación de la **Exposición 1** del proyecto anual grupal. La evaluación de código Python (Exposición 2) queda para la fase siguiente, pero el modelo de datos del MVP se diseña desde el inicio para soportarla: cada grupo posee un historial persistente de entregas, de modo que al evaluar la segunda exposición la herramienta disponga de todo el contexto de la primera.

### Dentro del alcance

- **Evaluación de los cuatro artefactos de la Exposición 1**: presentación de empresa, SRS/ERS (IEEE 830), diseño funcional y UI construida en Qt Designer.
- **Formatos de entrada**: PDF, Word (.docx) y archivos `.ui` de Qt Designer.
- **Análisis del archivo `.ui` como XML**: estructura de la interfaz, widgets utilizados y verificación de la convención de nomenclatura de objetos de uso extendido en la industria (notación de prefijos: `btn`, `txt`, `lbl`, `cmb`, etc.), configurable por el docente.
- **Rúbrica editable en archivo** (YAML): criterios y pesos definidos por el docente, editables a mano. Sin editor visual en el MVP.
- **Proyecto modelo como calibración**: el sistema utiliza un proyecto de referencia completo como ejemplo del nivel de calidad esperado, sin tratarlo como única solución válida. En el MVP, el proyecto modelo es **SIMI/QUIPU IA**: el proyecto integrador completo (presentación de empresa ficticia, ERS, diseño funcional y UI) desarrollado por el propio docente como estándar de referencia de la materia.
- **Checklist determinístico de completitud**: verificación automática (sin IA) de que cada documento contiene los bloques obligatorios.
- **Análisis de consistencia entre artefactos**: trazabilidad SRS ↔ diseño funcional ↔ UI (los requisitos declarados se reflejan en el diseño; las pantallas del diseño corresponden a la UI entregada).
- **Gestión de grupos con persistencia local**: alta de los grupos del ciclo lectivo, historial de entregas por grupo y evaluación de a un grupo por vez.
- **Flujo docente asistido**: carga de entregas → la IA genera un borrador de corrección con observaciones por criterio y una nota sugerida → el docente edita, acepta o rechaza cada observación → exportación del informe final.
- **Generador de cuestionario de defensa por grupo**: a partir del análisis de la entrega, la IA produce preguntas específicas sobre las decisiones de diseño del grupo, para usar durante la exposición oral. Verifica comprensión real del trabajo, independientemente de qué herramientas se usaron para producirlo.
- **Señales para indagar**: la herramienta puede marcar aspectos llamativos de la entrega (secciones genéricas sin conexión con el dominio del proyecto, saltos abruptos de sofisticación) como puntos sugeridos para profundizar en la defensa. Nunca como veredictos ni acusaciones.
- **Exportación del informe en PDF** con plantilla visual configurable (por defecto, el sistema visual dark-theme de la cátedra de origen).
- **Motor de IA**: API de Claude (Anthropic).
- **Plataforma**: aplicación de escritorio en Python/PySide6, en español.

### Fuera del alcance (MVP)

- Análisis de código Python y evaluación de la Exposición 2 (Fase 2; el modelo de datos ya lo contempla).
- Portal o acceso para alumnos.
- **Detección de autoría por IA ("detector de plagio con IA")**: se descarta deliberadamente, no por limitación técnica sino por decisión pedagógica. Los detectores de texto generado por IA no son confiables (falsos positivos frecuentes, evasión trivial) y no pueden sustentar una decisión académica justa. QHAWAY adopta en su lugar la verificación de comprensión mediante el cuestionario de defensa: el uso de IA por parte de los alumnos no es el problema; no entender lo que se entrega, sí.
- Editor visual de rúbricas.
- Generalización a otras materias, carreras o tipos de proyecto.
- Interfaz multiidioma (el inglés se incorpora en una fase posterior).
- Versión web o multiusuario.

## 5. Usuarios

El usuario del MVP es el **docente de ingeniería de software / análisis de sistemas de nivel superior** que evalúa proyectos grupales integradores: trabajos con múltiples artefactos (documentación de especificación y diseño, interfaces, código) producidos a lo largo de un ciclo lectivo y defendidos en exposiciones orales.

Perfil asumido: maneja los formatos estándar de la disciplina (IEEE 830, diseño funcional, herramientas como Qt Designer), tiene competencia técnica para editar un archivo de configuración (YAML) y trabaja habitualmente en una PC de escritorio o notebook. No se asume experiencia previa con herramientas de IA más allá de una configuración inicial documentada (creación de la cuenta de API, ver sección 10); la gestión del consumo la resuelve la propia aplicación, que mide y reporta el costo de cada análisis.

El usuario cero es el autor del proyecto, con sus propias materias como campo de prueba. Los alumnos **no** son usuarios del MVP: reciben los informes de devolución generados por la herramienta, pero no interactúan con ella.

## 6. Flujo de trabajo principal

El uso de QHAWAY se organiza en dos momentos: una **configuración inicial** que se realiza una vez por ciclo lectivo, y el **ciclo de evaluación** que se repite para cada grupo en cada exposición.

### Configuración del ciclo lectivo (una vez al año)

1. **Cargar la rúbrica**: el docente define criterios, descripciones y pesos en un archivo YAML editable.
2. **Cargar el proyecto modelo**: los artefactos del proyecto de referencia (presentación, SRS, diseño funcional, UI) que calibran el nivel de calidad esperado.
3. **Dar de alta los grupos**: nombre del grupo, integrantes y proyecto elegido. Cada grupo queda con su espacio persistente donde se acumula el historial de entregas.

### Ciclo de evaluación (por grupo, por exposición)

1. **Cargar la entrega**: el docente arrastra los archivos del grupo (PDF, .docx, .ui) al espacio del grupo correspondiente.
2. **Análisis automático**: QHAWAY ejecuta primero las verificaciones determinísticas (bloques obligatorios presentes, convención de nomenclatura en el .ui) y luego el análisis con IA: evaluación por criterio de la rúbrica, comparación con el proyecto modelo y análisis de consistencia entre artefactos. Para la segunda exposición, el análisis incorpora automáticamente el contexto de la primera entrega del grupo.
3. **Revisión del borrador**: la herramienta presenta el borrador de corrección — observaciones organizadas por criterio y por documento, señales para indagar, nota sugerida y cuestionario de defensa. El docente recorre cada elemento y lo **acepta, edita o descarta**; el filtro aplica a todas las salidas de la IA por igual, incluidas las preguntas de defensa y las señales para indagar. Puede además agregar observaciones propias.
4. **Exportación**: con la corrección validada, QHAWAY genera dos salidas: el **informe de devolución para el grupo** (PDF con la plantilla visual configurada, sin las señales para indagar) y la **guía de defensa para el docente** (cuestionario de preguntas y puntos a profundizar en la exposición oral).
5. **Cierre**: la evaluación queda registrada en el historial del grupo, disponible como contexto para la exposición siguiente.

Este flujo garantiza que ninguna salida de la IA llegue a los alumnos sin pasar por el criterio del docente, y que el esfuerzo docente se concentre en el paso 3 —validar y enriquecer— en lugar de en la redacción desde cero.

## 7. Modelo de evaluación

La evaluación de QHAWAY se apoya en tres capas complementarias, ordenadas de lo determinístico a lo interpretativo:

### Capa 1 — Verificación determinística (sin IA)

Comprobaciones exactas y reproducibles que no requieren interpretación: presencia de los bloques obligatorios en cada documento (según checklist configurable), elementos formales requeridos (carátula, índice, secciones numeradas) y convención de prefijos en los nombres de los objetos del archivo `.ui` (`btn`, `txt`, `lbl`, `cmb`, etc.). Esta capa corre primero, es gratuita e instantánea, y sus resultados alimentan como contexto a las capas siguientes.

### Capa 2 — Evaluación por rúbrica, calibrada con el proyecto modelo

La **rúbrica es la columna vertebral** de la evaluación: define qué se evalúa, con qué criterios y con qué pesos. Se organiza en secciones por artefacto más criterios transversales a la entrega completa. Cada criterio produce observaciones fundamentadas y una valoración parcial, que se componen en la **nota sugerida** — siempre como propuesta trazable: el docente puede ver cómo se llega al número, criterio por criterio. La escala de valoración y el mecanismo exacto de ponderación se especifican en el SRS del proyecto.

El **proyecto modelo actúa como calibración, no como plantilla**: le indica al sistema el nivel de calidad esperado, pero las entregas no se penalizan por resolver el problema de manera distinta. Dos diseños diferentes pueden ser igualmente correctos; lo que se evalúa es el cumplimiento de los criterios, no la similitud con la referencia.

### Capa 3 — Análisis transversal

Los análisis que consideran la entrega como un todo:

- **Consistencia entre artefactos**: trazabilidad SRS ↔ diseño funcional ↔ UI. Cada requisito declarado debe estar reflejado en el diseño; cada pantalla del diseño debe corresponder a la interfaz entregada. En la segunda exposición se agrega la dimensión código ↔ documentación, incluyendo la verificación de que los documentos fueron actualizados cuando la implementación los obligó a cambiar.
- **Cuestionario de defensa**: preguntas específicas sobre las decisiones del grupo, generadas a partir de su propia entrega, para verificar comprensión durante la exposición oral.
- **Señales para indagar**: aspectos llamativos marcados como sugerencias de profundización para la defensa, nunca como veredictos.

## 8. Diferenciales

¿Por qué QHAWAY y no corregir a mano, o pegar los documentos en un chat de IA genérico?

**Frente a la corrección manual**, la diferencia es de alcance: QHAWAY hace en minutos el análisis exhaustivo que a mano lleva una hora por grupo, e incluye verificaciones que la corrección manual casi nunca alcanza a cubrir, como la trazabilidad completa entre artefactos.

**Frente a un chat de IA genérico** (pegar el SRS en un chatbot y pedir "corregime esto"), los diferenciales son estructurales:

- **Evaluación estructurada para la uniformidad**: la misma rúbrica, el mismo proyecto modelo y el mismo proceso para los trece grupos. Ningún sistema basado en IA generativa es perfectamente determinístico, pero estructurar la evaluación reduce drásticamente la variabilidad frente a un chat genérico, donde cada corrección depende de cómo se formule el pedido.
- **Análisis multi-artefacto con contexto persistente**: un chat no puede sostener cómodamente cuatro documentos cruzados más el historial de la exposición anterior. QHAWAY gestiona ese contexto de forma nativa.
- **Flujo de validación docente integrado**: aceptar, editar o descartar cada observación es parte de la herramienta, no un copy-paste artesanal.
- **Salidas listas para usar**: informe de devolución en PDF con la plantilla visual del docente y guía de defensa para la exposición, sin trabajo de formateo posterior.
- **Capa determinística gratuita**: los chequeos exactos (bloques, nomenclatura) no dependen de la IA ni de su costo.

**Frente a las plataformas EdTech comerciales**, QHAWAY es de código abierto (MIT), está hecho por un docente en ejercicio para un caso real, no requiere que la institución contrate un servicio, y tiene una postura pedagógica explícita: la IA propone, el docente decide, y la comprensión de los alumnos se verifica en la defensa oral, no con detectores de plagio poco confiables.

## 9. Criterios de éxito del MVP

El MVP se considera exitoso si, en la primera exposición del próximo ciclo lectivo:

1. **Los trece grupos se corrigen íntegramente con QHAWAY**, cubriendo los cuatro artefactos de la Exposición 1.
2. **El tiempo por grupo se reduce a menos de la mitad**: de una hora actual a menos de 30 minutos, incluyendo la revisión y validación del borrador por parte del docente.
3. **La devolución entregada a cada grupo es más detallada que la actual**: observaciones fundamentadas por criterio y por documento, incluyendo el análisis de consistencia entre artefactos que hoy no se realiza.
4. **El cuestionario de defensa se usa efectivamente en las exposiciones orales** y aporta preguntas que el docente no habría formulado a mano.
5. **El costo operativo se mantiene dentro del presupuesto definido** (ver sección 10).

## 10. Supuestos y riesgos

### Supuestos

- Las entregas de los alumnos son de carácter público y de contenido ficticio (empresas inventadas), por lo que su procesamiento mediante una API en la nube no compromete datos sensibles. Los documentos se envían a la API tal como fueron entregados por los grupos.
- **Los datos personales gestionados por la aplicación** (nombres de los integrantes en el alta de grupos) **residen exclusivamente en la persistencia local** y no se envían al proveedor de IA. Este es un compromiso de diseño, no una circunstancia.
- **El uso de QHAWAY requiere una cuenta propia en la API de Anthropic**, con su clave de acceso y facturación en dólares por consumo. La guía de instalación documentará este paso; es la única configuración relacionada con IA que se le pide al usuario.
- El docente dispone de conexión a internet durante la evaluación (requerida por la API de IA).
- **Presupuesto operativo: hasta USD 20 mensuales** en consumo de API, costeado por el docente. Con 13 grupos y dos exposiciones anuales, el volumen estimado de evaluación es bajo y debería ubicarse muy por debajo de ese tope; el consumo real se medirá desde el primer análisis y es una variable de diseño explícita (la capa determinística resuelve gratis lo que no requiere IA, y el cacheo de contexto de la API — reutilizar la rúbrica y el proyecto modelo entre análisis sin re-procesarlos a costo completo — minimiza el resto).

### Riesgos

- **Costo de API superior al estimado**: si el análisis multi-artefacto consume más tokens de lo previsto, se supera el presupuesto. *Mitigación*: medición de consumo desde el primer análisis, optimización de prompts, y la arquitectura permite incorporar modelos alternativos (incluidos locales) en fases futuras.
- **Calidad insuficiente de las observaciones de la IA**: si el borrador requiere tanto retrabajo que no ahorra tiempo, el proyecto pierde su razón de ser. *Mitigación*: calibración iterativa con las entregas reales del ciclo anterior antes del uso en vivo; el proyecto modelo y la rúbrica detallada acotan la ambigüedad.
- **Sobreconfianza en la nota sugerida**: el riesgo de que la sugerencia de la IA ancle el criterio del docente. *Mitigación*: la nota se presenta como composición trazable por criterio, revisable pieza por pieza, y el flujo obliga a recorrer las observaciones antes de exportar.
- **Recepción institucional o de colegas**: el uso de IA en evaluación puede generar resistencias legítimas. *Mitigación*: el principio rector ("la IA propone, el docente decide") y la postura explícita frente a los detectores de plagio están documentados precisamente para dar esa discusión con fundamentos.
- **Dependencia de un único proveedor de IA**: cambios de precios o de servicio afectan el proyecto. *Mitigación*: aislar la integración con la API en un módulo propio, de modo que cambiar de proveedor sea un costo acotado.

## 11. Roadmap de fases

**Fase 1 — MVP (Exposición 1).** Aplicación de escritorio funcional para el caso ISFT N.º 179: evaluación de los cuatro artefactos documentales, las tres capas del modelo de evaluación, flujo de validación docente, exportación de informe PDF y guía de defensa. Modelo de datos preparado para el historial multi-exposición.

**Fase 2 — Exposición 2 y código.** Análisis del código Python entregado: correctitud, calidad y, sobre todo, trazabilidad código ↔ documentación usando el historial de la Exposición 1. Verificación de que los documentos fueron actualizados frente a los cambios de la implementación.

**Fase 3 — Generalización y apertura.** Rúbricas y checklists totalmente configurables para otras materias y tipos de proyecto, editor de rúbricas en la aplicación, documentación para adopción por terceros, publicación del repositorio con guía de contribución. La primera materia candidata para la generalización es **Ingeniería de Software II** de la misma institución, con entregas centradas en testing y calidad; luego, primeros docentes externos usando la herramienta.

**Fase 4 — Comunidad e internacionalización.** Interfaz multiidioma (español/inglés), glosario y documentación para lectores fuera del contexto educativo argentino, soporte de proveedores de IA alternativos (incluidos modelos locales), y evolución guiada por las necesidades de la comunidad docente.

Cada fase se valida en aulas reales antes de pasar a la siguiente.

## 12. Licencia y comunidad

QHAWAY se publica bajo **licencia MIT**: la más simple y permisiva, elegida deliberadamente para eliminar toda fricción de adopción. Cualquier docente o institución puede usar, modificar y redistribuir la herramienta sin restricciones ni costos de licenciamiento.

La visión de comunidad es que QHAWAY sea una herramienta **de docentes para docentes**: nacida de un aula real, validada en aulas reales, y mejorada por quienes la usan. La apertura del repositorio (Fase 3) incluirá documentación de adopción, guía de contribución y ejemplos de rúbricas para distintas materias, de modo que el costo de entrada para un docente nuevo sea el mínimo posible.

El proyecto sostiene públicamente sus dos posturas fundacionales — *la IA propone, el docente decide* y *comprensión verificada en la defensa, no detectores de plagio* — como parte de su identidad, no solo de su implementación.
