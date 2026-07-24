# QHAWAY — Dominio puro (Etapa 1)

Primer bloque de construcción del plan: el **dominio puro**, sin Qt, sin SDK de
IA, sin red ni sistema de archivos. Todo se testea con pytest sin mocks de
infraestructura (Arquitectura §11, AD-02).

## Qué hay

```
qhaway/dominio/
  niveles.py    Niveles canónicos y su mapeo a valores (SRS Apéndice B)
  rubrica.py    Modelo de rúbrica + validación CFG-01/CFG-02
  nota.py       Cálculo de nota sugerida, trazable (EVA-05, EVA-06)
  estados.py    Máquina de estados de la evaluación (GRP-06, EXP-03)
  errores.py    Excepciones del dominio
tests/          Suite pytest (los casos del Apéndice B son los canónicos)
demo.py         Demostración ejecutable de la composición trazable
```

## Cubre (SRS)

- **EVA-05** cálculo de nota como suma ponderada, composición trazable.
- **EVA-06** regla de criterio crítico (tope por defecto 6).
- **Redondeo de mitades hacia arriba** (EVA-05 v1.1): 6,5 → 7. Se usa
  `fractions.Fraction`, no `float`: el cálculo es exacto y reproducible.
- **CFG-01** validación de rúbrica: niveles no canónicos, pesos ≤ 0 o no
  numéricos, tope fuera de [1,10], artefactos requeridos faltantes, rúbrica sin
  criterios, IDs duplicados. Acumula todos los problemas de una vez.
- **GRP-06 / Arquitectura §6** máquina de estados con el guard de EXP-03
  (validar exige cero pendientes + nota confirmada).

## Correr

```bash
python3 -m pytest -q      # 27 tests
python3 demo.py           # ver la composición trazable en acción
```

## Decisiones de diseño

- El dominio recibe **estructuras ya parseadas** (dicts como los de
  `yaml.safe_load`). La lectura del YAML es infraestructura (Etapa 2) y no vive
  acá — por eso los tests usan dicts literales, sin tocar disco.
- `Rubrica.desde_dict` **valida antes de construir**: si el objeto existe, es
  válido. Una rúbrica inválida nunca llega a una evaluación (CFG-01).
- La nota se calcula con `Fraction` para que "mitad exacta" sea exacta y el
  resultado sea reproducible (misma entrada → mismo número, siempre).

## Qué sigue (Etapa 2)

Persistencia SQLite + estructura de carpetas + el arnés CLI descartable
(`qhaway_cli.py`) que ejercita estos servicios sin UI. Criterio de salida de esa
etapa: borrar `qhaway.db` y reconstruir todo el trabajo de evaluación desde las
carpetas.
