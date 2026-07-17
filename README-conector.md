# QHAWAY — Conector de IA (Etapa 4)

El corazón del plan de estudio: **salidas estructuradas** (exigir y validar el
JSON del modelo), manejo de errores de API reales y el patrón **puerto y
adaptador** que hace testeable un sistema con IA sin gastar un token.

## Qué hay

```
qhaway/dominio/
  esquema_salidas.py   Modelo + validación del contrato (EVA-13, esquema 0.1) — PURO
qhaway/infra/
  conector_ia.py       Conector (puerto) + ConectorFalso + ConectorAnthropic
  config_usuario.py    Clave de API en config de usuario (CFG-07) + prueba (CFG-08)
  repos.py             + ConsumoRepo (MON-01)
tests/
  test_esquema_salidas.py   las 7 reglas de EVA-13
  test_conector.py          reintentos, validación, consumo, backoff (con el falso)
requirements.txt
```

## Cubre (SRS)

- **EVA-13** validación de la respuesta contra el esquema antes de persistir;
  inválida → reintento; agotados → unidad **pendiente** (nunca datos inválidos).
- **IEX-02** reintentos con retroceso exponencial (por defecto 3), tanto para
  errores de red como para respuestas inválidas.
- **MON-01** registro de consumo por llamada (tokens entrada/salida/caché y costo
  estimado), incluidos los reintentos.
- **CFG-07** clave de API en la config de usuario, fuera del repo y del ciclo.
- **CFG-08** prueba de conexión con una llamada mínima.

## El diseño clave: puerto y adaptador

La máquina de **reintentos + validación + consumo** vive en la clase base
`Conector`. Cada adaptador solo implementa `_llamar` (la llamada de bajo nivel):

- `ConectorFalso` reproduce un guion de respuestas (válidas, inválidas, o
  excepciones de red). Ejercita TODA la lógica compartida sin tokens — por eso la
  suite de integración corre gratis y determinística.
- `ConectorAnthropic` cambia solo cómo se hace la llamada real (SDK, importado
  perezosamente). Cambiar de proveedor en Fase 4 es escribir otro adaptador
  (RNF-07); los servicios hablan con `Conector`, no con el SDK.

## Probar

```bash
python3 -m pytest -q                       # 79 tests (Etapas 1-4), sin API

# Criterio de salida — llamada real de punta a punta (requiere clave):
python3 qhaway_cli.py guardar-clave        # la pide sin echo; la guarda fuera del repo
python3 qhaway_cli.py probar-conexion      # CFG-08
```

La suite de integración del conector contra el falso (respuestas inválidas y
fallas incluidas) es el criterio de salida verificable sin gastar un token; la
llamada real de punta a punta la hacés con tu clave vía `probar-conexion`.

## Validación del esquema (EVA-13) — las 7 reglas

1. `nivel` dentro del enum canónico. 2. `criterio_id` debe existir en la sección.
3. Cada criterio exactamente una valoración. 4. Toda pregunta con `elemento`
nombrado (EVA-08). 5. `referencia.ubicacion` obligatoria; `cita` ≤ 25 palabras.
6. Una señal nunca lleva `criterio_id` ni nivel (EVA-09). 7. Respuesta inválida →
reintento; agotados → pendiente.

## Nota de seguridad

La clave se guarda en `%APPDATA%/qhaway` (Windows) o `~/.config/qhaway` (Linux),
nunca en el repo. `requirements.txt` y `.gitignore` acompañan para que un colega
que clone tenga todo y no suba credenciales por accidente.

## Qué sigue (Etapa 5)

El pipeline completo (`servicios.analizar_entrega`): los 6 pasos de la
arquitectura §6, orquestando extracción → DET → EVA por artefacto → transversal →
composición de nota, con reanudación por unidades (EVA-10) y el worker de Qt.
Acá se cosen todas las piezas de las Etapas 1-4.
