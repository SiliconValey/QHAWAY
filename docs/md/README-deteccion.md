# QHAWAY — Extracción + DET (Etapa 3)

**Primer producto usable: QHAWAY ya sirve sin IA.** Verifica nomenclatura y
completitud gratis, en la máquina local, sin gastar un token.

## Qué hay

```
qhaway/dominio/
  contenido.py   Contrato puro: ContenidoDocumento, Seccion, ArbolUI, NodoUI, Referencia
  deteccion.py   DET-02/03/04/05: completitud, elementos formales, nomenclatura (PURO)
qhaway/infra/
  extraccion.py  PDF (PyMuPDF), .docx (python-docx), .ui (ElementTree) → contrato
  config.py      Carga de checklist/nomenclatura desde YAML + defaults de ejemplo
config-ejemplo/
  checklist.yaml      CFG-05: bloques obligatorios por tipo de documento
  nomenclatura.yaml   CFG-06: prefijos esperados por tipo de widget
tests/
  test_deteccion.py   DET puro (con estructuras literales)
  test_extraccion.py  extracción sobre PDF/docx/.ui generados + ING-02/06
```

## Cubre (SRS)

- **ING-02** formatos aceptados (PDF/.docx/.ui); otros se rechazan con mensaje.
- **ING-04** extracción de texto + estructura (documentos) y árbol de objetos (.ui).
- **ING-06** archivos problemáticos (corruptos, protegidos, PDF escaneado sin
  texto) reportados sin abortar.
- **DET-02** completitud: bloques obligatorios presentes/ausentes, matcheados por
  **sinónimos** (nunca por título exacto — lección de la Etapa 0.2).
- **DET-03** elementos formales: carátula, índice, secciones numeradas.
- **DET-04** nomenclatura del `.ui`: por cada objeto no conforme informa nombre
  actual, tipo de widget y prefijo esperado.
- **DET-05** reporte **reproducible** (mismas entradas + config → mismo reporte)
  y en **categoría propia**, distinguible de las observaciones de IA.
- **CFG-05/06** checklist y nomenclatura configurables en archivo, no cableados.

## Probar (criterio de salida)

```bash
python3 -m pytest -q                          # 59 tests (Etapas 1-3)
python3 qhaway_cli.py det ruta/al/form.ui --tipo ui
python3 qhaway_cli.py det ruta/al/srs.pdf --tipo srs
```

El subcomando `det` extrae un archivo real y corre la Capa 1. Sobre un `.ui`
lista los objetos mal nombrados; sobre un SRS, los bloques ausentes y la
carátula/índice/numeración faltantes. Ese es el hito: valor entregado sin IA.

## Arquitectura de la etapa

- **El dominio define el contrato, la infra lo implementa** (AD-02). `deteccion`
  no sabe qué es un PDF: opera sobre `ContenidoDocumento`/`ArbolUI` ya extraídos.
  Por eso DET se testea con estructuras literales, sin archivos.
- **Reproducibilidad por construcción** (DET-05): recorridos en orden estable
  (config en orden, árbol `.ui` en profundidad), sin estructuras cuyo orden de
  iteración sea incidental.
- **Matcheo robusto**: normalización sin acentos ni mayúsculas, y sinónimos por
  bloque — porque en documentos reales los títulos varían y "el título miente"
  (EstacionAR se titulaba "Diseño Funcional" siendo un SRS).

## Nota sobre la configuración

Los `config-ejemplo/*.yaml` y los defaults en `config.py` son un **punto de
partida** basado en la Etapa 0.2 y en los prefijos estándar de Qt. Reemplazalos
por los contenidos reales de la cátedra: el checklist real y la **tabla completa
de nomenclatura** son entregables del proyecto (CFG-06). Copialos a
`config/checklist.yaml` y `config/nomenclatura.yaml` del ciclo para empezar.

## Qué sigue (Etapa 4)

El conector de IA: interfaz neutral, salidas estructuradas validadas contra el
esquema JSON de la Etapa 0, reintentos con backoff, registro de consumo, y un
`ConectorFalso` para testear el pipeline sin gastar tokens. Los hallazgos DET de
esta etapa entran como contexto (hechos verificados) a EVA (EVA-04).
