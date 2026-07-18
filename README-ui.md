# QHAWAY — Interfaz gráfica (Etapa 7)

La UI en PySide6, organizada alrededor del flujo de revisión (REV). El principio
de la etapa: **la lógica vive en servicios testeables; la vista es delgada.** Así
los flujos aceptar/editar/descartar se prueban de verdad, no a ojo.

## Qué hay

```
qhaway/servicios/
  revision.py   REV-02..07 + EXP-03: aceptar/editar/descartar, ajuste de nota,
                validación con guard, métricas de retrabajo (REV-06) — SIN Qt
  monitor.py    MON-02/03/04: costo por evaluación, presupuesto con alerta, histórico
qhaway/ui/
  revision.py   VistaRevision: la vista del flujo REV (capa delgada)
  monitor.py    VistaMonitor: presupuesto + retrabajo
  app.py        Ventana principal (punto de entrada)
  worker.py     (Etapa 5) worker de análisis
tests/
  test_revision.py     lógica REV/MON sin Qt
  test_ui_revision.py  tests de humo pytest-qt (headless) de la costura vista↔servicio
  conftest.py          fija Qt en modo offscreen
```

## Cubre (SRS)

- **REV-02** aceptar/editar/descartar por elemento · **REV-03** observaciones
  propias del docente · **REV-04** ajuste de valoración con recálculo de nota +
  nota final · **REV-05** origen interno (ia_aceptado/ia_editado/docente) ·
  **REV-06** métricas de retrabajo · **REV-07** estado de revisión persistente.
- **EXP-03** validar solo con cero pendientes + nota final (el guard es la máquina
  de estados de la Etapa 1).
- **MON-02** costo por evaluación · **MON-03** acumulado vs presupuesto con alerta
  al 80%, sin bloquear · **MON-04** histórico por mes.

## El diseño clave: la vista es delgada

Toda la lógica de REV vive en `servicios.revision` (sin Qt). `VistaRevision` solo
llama a esas funciones y refresca. Por eso sus métodos públicos (`aceptar`,
`editar`, `descartar`, `validar`) se testean con pytest-qt sin simular clics, y el
grueso (recálculo de nota, guard EXP-03, métricas) se testea con pytest normal.

Esto también hace honor al plan: `ui.revision` está pensada para **evolucionar
usándola con borradores reales**, no para quedar fija ahora. Como la lógica no
está atrapada en el widget, rediseñar la vista no toca las reglas.

## Probar

```bash
# Todo (los tests de UI corren headless por el conftest):
python3 -m pytest -q                      # 105 tests (Etapas 1-7)

# Solo los de humo de la UI, explícito:
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/test_ui_revision.py -q
```

En Windows con pantalla, los tests de UI corren igual (Qt usa el backend nativo).

## Criterio de salida

Revisar un borrador real completo de punta a punta sin tocar la base a mano.
El instrumento está listo: tras correr el pipeline (Etapa 5-6) sobre una entrega
real, abrís la ventana con:

```python
from qhaway.infra import abrir_ciclo
from qhaway.ui.app import abrir_revision
ciclo = abrir_ciclo("ruta/al/ciclo")
abrir_revision(ciclo, entrega_id=1, evaluacion_id=1, rubrica=rubrica)
```

y aceptás/editás/descartás cada elemento, ajustás la nota y validás — todo por la
UI. Los tests de humo pytest-qt cubren esa costura (coherencia con lo que enseñás:
la UI también se testea).

## Alcance de la etapa

Se construyó el flujo de revisión completo (la vista más compleja y el criterio de
salida) más el monitor. Las vistas de ABM (ciclo/grupos, configuración, carga de
entrega) son formularios y tablas sobre los servicios ya existentes: se suman como
pestañas de `app.py` del mismo modo, y son el terreno ideal para seguir vos —el
que construye, aprende—. Ninguna necesita lógica nueva de dominio: los servicios
que consumen ya están hechos y testeados.

## Qué sigue (Etapa 8)

Exportación: `infra.informes` con Jinja2 + el motor HTML→PDF validado en la Etapa
0, plantillas del informe de grupo y la guía de defensa (EXP-01..04). El informe
al grupo, sin señales ni marcas de origen; la guía de defensa, aparte.
