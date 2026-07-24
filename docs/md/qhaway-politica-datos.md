# QHAWAY — Política de Datos y Privacidad (Etapa 0.8)

**Versión:** 1.0 · **Fecha:** Julio 2026
**Realiza:** Plan Etapa 0.8 · consolida RNF-04/05, CFG-07, AD-03 y la práctica vigente de la cátedra.
**Destinatarios:** docentes que adopten QHAWAY, sus instituciones y sus estudiantes.

## Qué datos maneja QHAWAY y dónde viven

**1. Entregas de los alumnos (documentos y, en Fase 2, código).** Se envían a la API de Anthropic para su análisis, **tal como fueron presentadas**. Su contenido es de carácter académico y ficticio (empresas y datos inventados por los propios grupos como consigna de la materia), pero puede incluir los nombres reales que los alumnos pusieron en carátulas o pies de página. Anthropic procesa estos contenidos según sus términos de servicio de API vigentes; el docente que adopte QHAWAY debe conocerlos.

**2. Datos gestionados por la aplicación (nombres de integrantes, composición de grupos, historial).** Viven **exclusivamente en la persistencia local** de la máquina del docente y **nunca se envían a la API** — no es una promesa operativa sino una propiedad estructural del diseño: el armado del contexto de análisis solo toma contenido de los archivos de entrega y la configuración (Arquitectura §10). Tampoco entran en la estructura de carpetas compartible: residen solo en la base local.

**3. Evaluaciones, notas y decisiones del docente.** Locales, nunca transmitidas. Los informes exportados los distribuye el docente por sus canales habituales.

**4. Credenciales.** La clave de API vive en la configuración de usuario del sistema operativo, fuera del directorio del proyecto: un respaldo o una carpeta de ciclo compartida con un colega jamás la contiene.

## Marco normativo

En Argentina aplica la **Ley 25.326 de Protección de Datos Personales**. La posición de QHAWAY: los nombres en carátulas de trabajos académicos de carácter público-institucional, producidos como consigna con contenido ficticio, se procesan con fines exclusivamente educativos (la corrección del propio trabajo) y bajo conocimiento de los alumnos (ver transparencia). Los datos personales estructurados que la aplicación administra no salen del equipo local. Instituciones con requisitos adicionales pueden optar por pedir a los grupos carátulas sin datos personales — una convención de entrega, sin cambios en la herramienta.

## Transparencia con los estudiantes (política vigente de la cátedra de origen)

**Los grupos saben que la evaluación cuenta con asistencia de IA validada por el docente.** No es una concesión: es coherencia — el principio rector del producto ("la IA propone, el docente decide") se les comunica igual que se les enseña el uso responsable de IA en su propia práctica. Toda observación, nota y pregunta de defensa que reciben pasó por el criterio del docente (REV: nada se exporta sin validación). QHAWAY no toma decisiones académicas: las prepara.

## Qué NO hace QHAWAY

- No detecta "autoría por IA" ni acusa a estudiantes (decisión pedagógica documentada en la Visión §4).
- No envía datos a ningún servicio distinto de la API de IA configurada; no tiene telemetría, cuentas en la nube ni componente servidor.
- No conserva las señales para indagar ni el origen de las observaciones en los informes entregados a los grupos.

## Recomendaciones para docentes que adopten QHAWAY

1. Informar a los estudiantes, al inicio del ciclo, que la corrección cuenta con asistencia de IA validada por el docente (puede incluirse en la consigna del proyecto).
2. Verificar los términos vigentes de la API de Anthropic y las normas de su propia institución.
3. Si la institución lo requiere: carátulas sin datos personales como convención de entrega.
4. Respaldar el directorio del ciclo (incluye la base local) por los medios habituales; el respaldo nunca contiene la clave de API.
