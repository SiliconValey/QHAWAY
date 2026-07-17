# QHAWAY — Prompts y evaluación real (Etapa 6)

La otra mitad del corazón del plan: **prompt engineering de evaluación**. Acá tu
criterio docente se convierte en texto ejecutable, y por primera vez podés medir
si QHAWAY evalúa como vos.

## Qué hay

```
qhaway/infra/
  prompts.py          Plantillas versionadas (AD-07) + ensamblador con orden de caché
qhaway/dominio/
  calibracion.py      Métrica de coincidencia (Etapa 0.7) — PURA
qhaway/servicios/
  analizar_entrega.py  El pipeline ahora usa las plantillas reales
tests/
  test_prompts.py      contrato de variables, instrucciones, orden de caché
  test_calibracion.py  la métrica
```

## Cubre (SRS)

- **EVA-01** exigencia de referencias (sin inventar página) · **EVA-03**
  calibración-no-plantilla · **EVA-04** hallazgos DET como hechos no contradecibles
  · **EVA-07** trazabilidad transversal · **EVA-08** preguntas con elemento
  nombrado · **EVA-09** señales en lenguaje de sugerencia.

## Diseño de los prompts (AD-07)

- **Contrato de variables explícito**: cada plantilla declara qué variables
  recibe; renderizar sin una es un error (`VariableFaltante`), no un hueco
  silencioso. Testeable.
- **Instrucciones inspeccionables**: las reglas del SRS (EVA-03/04/08/09) viven en
  el texto del prompt, no escondidas en el código. Un test verifica que estén.
- **Orden de contexto para el caché (EVA-12)**: lo estable primero (rol, rúbrica,
  modelo), lo variable al final (la entrega del grupo). Los bloques estables se
  marcan como cacheables; entre grupos, ese prefijo se sirve desde caché.
- **Versión en cada plantilla**: se incluye en el snapshot de la evaluación
  (CFG-11). Un cambio de prompt exige re-correr la calibración — como una
  regresión de código.

## La métrica de coincidencia (Etapa 0.7)

`dominio.calibracion.medir` compara la salida del pipeline contra tu evaluación
conocida de una entrega: distancia de nota, y coincidencia de valoraciones nivel
por nivel (exactas / adyacentes / lejanas). `resumir` agrega el subconjunto. Las
**lejanas** (distancia ≥ 2) son las que conviene revisar primero.

## Probar

```bash
python3 -m pytest -q            # 94 tests (Etapas 1-6)
```

## Criterio de salida: primera pasada de calibración (con tu clave y tus entregas)

Esto es inherentemente tuyo: requiere entregas reales del ciclo pasado con tu
evaluación conocida. La receta:

```python
from qhaway.infra import abrir_ciclo
from qhaway.infra.conector_ia import ConectorAnthropic
from qhaway.infra.config_usuario import cargar_clave
from qhaway.servicios import ContextoAnalisis, analizar_entrega
from qhaway.dominio.niveles import Nivel
from qhaway.dominio.calibracion import CasoCalibracion, medir

# 1. Corré el pipeline real sobre una entrega ya cargada del set de iteración
conector = ConectorAnthropic(cargar_clave())
resultado = analizar_entrega(ciclo, grupo, entrega, contexto, conector)

# 2. Compará contra tu evaluación conocida
caso = CasoCalibracion(id="G03", nota_docente=8, valoraciones_docente={
    "SRS-REQ": Nivel.BUENO, ...})
valoraciones_ia = {cid: Nivel(v["nivel_ia"])
                   for cid, v in ciclo.valoraciones.de_evaluacion(resultado.evaluacion_id).items()
                   if v["nivel_ia"]}
print(medir(caso, resultado.nota, valoraciones_ia))
```

El criterio: los resultados del **subconjunto de iteración** dentro de distancia
razonable del umbral. La iteración fina es la Etapa 9; las entregas **reservadas**
no se tocan (no se calibra contra ellas, para no sobreajustar).

## Alcance honesto

- El **ensamblado** produce el orden estable→variable y marca los bloques
  cacheables (la parte sustantiva de EVA-12). Falta cablear esas marcas como
  `cache_control` en la llamada real del `ConectorAnthropic` (hoy manda el prompt
  como un bloque único): es un refinamiento acotado, sin cambio de diseño.
- Los **prompts por defecto** son un punto de partida sólido; la calibración es
  precisamente el proceso de afinarlos con tus entregas reales.

## Qué sigue (Etapa 7)

La UI en PySide6: `ui.ciclo`, `ui.configuracion`, `ui.entrega`, `ui.monitor`
primero; `ui.revision` al final, diseñada con borradores reales del pipeline en
pantalla — su diseño surge de usarla, no de imaginarla.
