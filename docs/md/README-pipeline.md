# QHAWAY — Pipeline completo (Etapa 5)

Por primera vez QHAWAY **evalúa una entrega de punta a punta**. Esta etapa cose
todas las capas: extracción + DET (Etapa 3), conector (Etapa 4), cálculo de nota
y máquina de estados (Etapa 1), persistencia (Etapa 2).

## Qué hay

```
qhaway/servicios/
  analizar_entrega.py   Los 6 pasos del pipeline (Arquitectura §6) + reanudación
qhaway/ui/
  worker.py             Worker QThread que emite señales de progreso (AD-08)
qhaway/infra/
  repos.py              + AnalisisRepo, HallazgoDetRepo, ElementoRepo
  esquema.py            + tabla 'analisis' (estado de reanudación por unidad)
tests/
  test_pipeline.py      camino feliz, artefacto ausente, y el test de la desconexión
```

## Los 6 pasos (Arquitectura §6)

1. **Preparación**: crea la evaluación y una unidad de análisis por artefacto +
   una transversal, todas `pendiente`. Transición de la entrega a `analizando`.
2. **Extracción** (local): contenido de cada archivo; los problemáticos se
   reportan sin abortar (ING-06) y equivalen a artefacto ausente (ING-05).
3. **DET** (local): checklist, elementos formales, nomenclatura; hallazgos
   persistidos, que entran como hechos verificados a EVA (EVA-04).
4. **EVA por artefacto** (API, una unidad por vez): valida y persiste cada unidad
   atómicamente al completarse (EVA-10). Artefacto ausente → Insuficiente sin
   llamada (EVA-05).
5. **Transversal** (API, unidad propia de reanudación): consistencias, preguntas
   de defensa y señales.
6. **Composición** (local): nota sugerida (dominio.nota) y borrador con todos los
   elementos en `pendiente`. Transición a `borrador_en_revision`.

## Cubre (SRS)

- **EVA-02/10** pipeline por unidades con reanudación · **EVA-05** artefacto
  ausente · **ING-01/03/05** carga y artefactos ausentes · **MON-01** consumo por
  unidad · **IEX-01** análisis fuera del hilo de UI (worker) · **RNF-06** cada
  unidad se persiste atómicamente.

## El criterio de salida: el test de la desconexión

> Arrancar un análisis, cortar internet en una unidad, cerrar la app, reabrir,
> reanudar, y que el costo registrado muestre que las unidades previas no se
> repagaron.

Testeado (`test_desconexion_reanudacion_no_repaga`) y demostrable en vivo, sin
gastar un token:

```bash
python3 -m pytest -q                     # 82 tests (Etapas 1-5)
python3 qhaway_cli.py pipeline-demo /tmp/demo
```

La salida del demo muestra: en el corte, la red caída cuesta 0 y solo la unidad
completada se cobra; en la reanudación, solo se llaman las unidades pendientes, la
completada **no se repaga**, y la evaluación termina en `borrador_en_revision`.

## Cómo se logra la reanudación (EVA-10)

El estado de cada unidad vive en la tabla `analisis`. Reanudar es, literalmente,
volver a llamar a `analizar_entrega`: las unidades `completado` se saltan. La
máquina de estados del dominio gobierna las transiciones (`analisis_interrumpido
→ analizando → borrador_en_revision`), así que un salto ilegal es imposible por
construcción — la misma máquina de la Etapa 1, ahora orquestando el pipeline.

## Nota sobre el worker y los prompts

- **Worker QThread** (`ui/worker.py`): PySide6 se importa perezosamente; la
  lógica que importa ya está testeada en el servicio vía el callback `on_progreso`
  —el worker solo traduce ese callback a señales de Qt (AD-08)—.
- **Prompts mínimos**: el pipeline arma un prompt con todos los datos que viajan
  (rúbrica, modelo, hallazgos DET, entrega), pero la construcción fina —rol
  evaluador, calibración-no-plantilla, cacheo por orden de contexto— es la
  **Etapa 6**, donde tu criterio docente se vuelve texto ejecutable.

## Límite conocido y aceptado

El pipeline es secuencial (5 unidades × 13 grupos, con latencias de decenas de
segundos, puede ser un rato en tanda). El diseño por unidades independientes
(AD-04) permite paralelizar entregas distintas en el futuro sin rediseño, si
llega a molestar.

## Qué sigue (Etapa 6)

Las plantillas de `prompts/` (analisis_artefacto × 4, analisis_transversal) con la
inyección de rúbrica/modelo/hallazgos DET y prompt caching. Primera pasada del
subconjunto de iteración del set de calibración con la métrica de la Etapa 0.
