# QHAWAY — Exportación de informes (Etapa 8)

Los dos PDF que cierran el ciclo de evaluación: el **informe de devolución** para
el grupo y la **guía de defensa** para el docente. Plantillas HTML (Jinja2) →
PDF (WeasyPrint), el motor que validaste en la PoC de la Etapa 0.4 (AD-09).

## Qué hay

```
qhaway/infra/
  informes.py     Plantillas Jinja2 + conversión HTML→PDF (WeasyPrint)
qhaway/servicios/
  exportar.py     Reúne datos, aplica filtros EXP-01/02, guard EXP-03, archiva EXP-04
tests/
  test_exportacion.py   filtros, guard, y generación de PDF real
```

## Cubre (SRS)

- **EXP-01** informe de devolución: observaciones validadas por artefacto y
  criterio, hallazgos DET, consistencia y nota final. **Sin** señales, **sin**
  cuestionario, **sin** marcas de origen (REV-05).
- **EXP-02** guía de defensa (aparte): cuestionario validado + señales aceptadas,
  identificando grupo y exposición.
- **EXP-03** exportación solo desde evaluación validada (guard).
- **EXP-04** archivado del PDF en `informes/` de la versión de la entrega.
- **CFG-09** plantilla visual configurable (editando HTML/CSS, sin tocar código).

## El filtro que importa (EXP-01)

El informe al grupo se presenta como **devolución unificada de la cátedra**: no
distingue qué observación puso la IA y cuál el docente (REV-05), y no incluye lo
que es para uso interno del docente (señales y preguntas de defensa). El servicio
separa dos flujos desde los mismos elementos revisados:

- **Informe grupo**: solo `observacion` en estado aceptado/editado. Las de artefacto
  se agrupan por criterio→artefacto; las de consistencia (sin criterio) van aparte.
- **Guía defensa**: `pregunta_defensa` y `senal` aceptadas/editadas.

Los elementos descartados no aparecen en ninguno.

## Probar

```bash
python3 -m pytest -q      # 110 tests (Etapas 1-8); los de PDF se saltan si falta WeasyPrint
```

El test `test_pdf_real_se_genera_y_archiva` produce PDFs de verdad y verifica que
empiecen con `%PDF` y se archiven en `informes/`.

## Criterio de salida

Los dos PDF de una evaluación real, con tu identidad visual, sin señales ni marcas
de origen en el informe del grupo. La plantilla por defecto es un tema claro
imprimible (lo que un PDF necesita); reemplazala por tu sistema visual editando el
HTML/CSS de `infra/informes.py` o pasando una plantilla propia a `renderizar_*`
(CFG-09).

## Nota sobre WeasyPrint

WeasyPrint necesita librerías del sistema (Pango/cairo). En tu Windows de
desarrollo puede requerir GTK; el plan ya lo previó: **el usuario final no instala
nada** porque la dependencia viaja dentro del ejecutable congelado (PyInstaller,
Etapa 9). Si en desarrollo te da problemas de GTK, es esperable y se resuelve en
el empaquetado.

## Qué sigue (Etapa 9 — la última)

Calibración fina contra el subconjunto de iteración (máximo 3 rondas), corrida
única de las entregas reservadas como validación no contaminada, empaquetado con
PyInstaller (RNF-10), guía de instalación con la política de datos, y el simulacro
completo. Al final: QHAWAY listo para la primera exposición del ciclo.
