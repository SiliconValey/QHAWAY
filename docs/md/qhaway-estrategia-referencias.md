# QHAWAY — Estrategia de Referencias sobre Documentos (Etapa 0.2)

**Versión:** 1.0 · **Fecha:** Julio 2026
**Realiza:** EVA-01, DET-02/03 · Arquitectura §13.2
**Validada contra:** SIMI (ERS modelo, PDF), EstacionAR (SRS de grupo, PDF), HospitalACL (SRS de grupo, docx)

## El hallazgo que ordena todo

La hipótesis tipográfica ("los encabezados se distinguen por tamaño de fuente o negrita") **falla en los documentos reales de alumnos**: el PDF de EstacionAR tiene sus títulos de sección en el mismo cuerpo 11pt sin negrita que el texto, y el docx de HospitalACL no usa ningún estilo de encabezado de Word (54 párrafos, todos "Normal"). Solo el proyecto modelo tiene jerarquía tipográfica limpia. La señal universal que sí funciona en los tres documentos es **el patrón de numeración jerárquica al inicio de línea** (`1`, `1.1`, `2.3`, con o sin punto final) — porque la consigna de la cátedra impone la estructura IEEE 830 numerada y los alumnos la siguen, aunque no sepan formatearla.

## La heurística (validada: 15/15 SIMI, 13/13 EstacionAR, 13/13 HospitalACL)

1. **Reconstrucción de líneas visuales (solo PDF)**: agrupar las líneas de PyMuPDF por coordenada Y (tolerancia 3pt) y concatenar por X. Imprescindible: la numeración automática de Word deja el número y el título en cajas separadas que PyMuPDF reporta como líneas distintas ("2" / "Descripcion General").
2. **Señal primaria**: línea que matchea `^\d{1,2}(\.\d{1,2})*[.\)]?\s+Título`.
3. **Filtros anti-falso-positivo**: longitud ≤ 80 caracteres; el título arranca con mayúscula (mata celdas de tabla como "2 s" y "0 duplicados"); el título no arranca con dígito ni unidad.
4. **Validación de coherencia de secuencia**: los encabezados aceptados deben formar una progresión razonable (1 → 1.1 → 1.2 → 2...); los que rompen la secuencia se descartan (mata el falso positivo "1.0 Junio 2026" de las carátulas). Se implementa en la construcción (Etapa 3).
5. **Tipografía como refuerzo, nunca como requisito**: tamaño > cuerpo o negrita eleva la confianza del encabezado (alta/media) pero su ausencia no lo descarta.
6. **En docx**: intentar primero estilos `Heading` (por si algún grupo los usa); fallback inmediato a la misma heurística de numeración sobre párrafos, que es el caso real.

## Resolución de referencias (el objeto `referencia` del esquema)

- **`ubicacion`**: el encabezado de la sección que contiene el hallazgo (texto tal como aparece en el documento del grupo, ej. "3 Requerimientos funcionales"). Para el `.ui`: el nombre del objeto.
- **`pagina`**: en PDF siempre existe y es el respaldo universal — aunque la detección de secciones fallara por completo, la referencia degrada a página + cita, nunca a nada. En docx **no existe el concepto de página** (se pagina al renderizar): las referencias de docx llevan `pagina: null` y se apoyan en ubicación + cita. Esto se informa al modelo en el prompt.
- **`cita`**: fragmento ≤ 25 palabras cuando el contenido es citable; la verificación es por búsqueda del fragmento en el texto extraído de la sección.

## Subproductos para el checklist (CFG-05) — hallazgos de los documentos reales

1. **Los títulos varían**: "Definiciones y siglas" / "Definiciones y acrónimos" / "Definiciones y Acrónimos". El checklist debe matchear por **palabras clave con sinónimos**, nunca por título exacto.
2. **El título del documento miente**: EstacionAR se titula "Documento de Diseño Funcional" siendo un SRS. La clasificación de artefactos (ING-03) no puede confiar solo en el título del documento; el contenido (presencia de "Requerimientos funcionales", tablas RF-XX) es mejor señal.
3. **Secciones ausentes reales**: EstacionAR no tiene "Referencias" ni "Criterios de aceptación" — casos reales para el checklist y para DET-02.
4. **La estructura de 7 secciones** (Introducción / Descripción General / RF / RNF / Restricciones / Interfaz / Aprobaciones) se repite en ambos grupos: buena base para el checklist por defecto de la cátedra.

## Límite conocido

La heurística depende de que la consigna imponga estructura numerada — lo cual es cierto en esta cátedra y verosímil en la disciplina, pero un documento sin numeración alguna degradaría a referencias por página+cita. Aceptado para el MVP; documentado para la Fase 3 (otras materias podrían necesitar detectores adicionales).
