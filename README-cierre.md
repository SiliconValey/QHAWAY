# QHAWAY — Calibración y cierre (Etapa 9)

La última etapa: medir si QHAWAY evalúa como el docente, con disciplina
estadística, y dejar todo listo para producción. Aquí termina el plan de
construcción.

## Qué hay

```
qhaway/dominio/
  calibracion.py   + agregación por moda, distancia 3 (C3 descalificante)
qhaway/servicios/
  calibrar.py      Arnés: N corridas, moda, peor caso, aceptación del set
qhaway/infra/
  conector_ia.py   + temperatura (0 para el evaluador)
packaging/
  qhaway.spec      Congelamiento PyInstaller (receta validada en PoC 0.5)
qhaway_app.py      Punto de entrada de la app empaquetada
docs-GUIA-INSTALACION.md   Instalación, empaquetado y manejo de datos
tests/
  test_calibrar.py  moda, inestabilidad por peor caso, aceptación del set
```

## Lo que se construyó (código testeable)

- **Disciplina de corridas (0.7)**: el arnés corre el pipeline N veces (default 3)
  a **temperatura 0**, agrega el nivel por criterio **por moda**, mide C1 (nota
  ±1) y C3 (valoración) sobre el agregado, y reporta el **peor caso**: si el
  promedio pasa pero una corrida invirtió un juicio (distancia 3), se marca como
  **inestable** y falla C3. Un evaluador que a veces acierta no es confiable.
- **Regla de aceptación del set**: C1 en ≥80% de las entregas, C3 en todas, y
  **cero distancia 3** en cualquier lado (descalificante). Testeado.
- **Empaquetado (RNF-10)**: `qhaway.spec` con la receta de la PoC 0.5 — WeasyPrint
  con `collect_all`, GTK embebido para que el usuario final no instale nada,
  `--onedir` porque la distribución es la carpeta entera.

## Probar

```bash
python3 -m pytest -q      # 117 tests (Etapas 1-9)
```

## Lo que es tuyo (requiere tus datos reales)

Estos son los criterios de salida que dependen de tu clave y tus entregas —el
código que los ejecuta está listo y testeado, pero la corrida es tuya:

1. **Calibración fina** contra el subconjunto de iteración, **máximo 3 rondas**
   (el umbral se decidió antes de iterar, en la métrica 0.7, para que el sesgo no
   sea "seguir iterando hasta que dé"). Usá `servicios.calibrar` con el
   `ConectorAnthropic` real.
2. **Validación no contaminada**: una **única** corrida de las entregas
   **reservadas** (las que no se miraron durante la iteración). Si pasan los
   cuatro componentes, el evaluador generaliza; si no, no.
3. **Empaquetado en Windows**: `pyinstaller packaging\qhaway.spec` y probar el
   `.exe` en una PC sin Python (tu PoC 0.5 ya validó que la receta funciona).
4. **Simulacro completo**: evaluar los 13 grupos como si fuera el día real, y
   medir los criterios de éxito del MVP (Visión §9): tiempo por grupo, detalle de
   la devolución, uso del cuestionario, y costo dentro del presupuesto.

## Nota metodológica (lo más valioso del plan)

C1 y C3 son computables desde el esquema y están automatizados. **C2** (cobertura
de hallazgos) y **C4** (ruido) requieren tu apareamiento manual y las métricas de
retrabajo (REV-06); no se automatizan porque dependen de tu juicio sobre qué
observación "coincide" con la tuya. Y la vara final de todo —"¿lo firmaría como
devolución de mi cátedra?"— no es un número: se audita a ojo en cada ronda.

---

# El proyecto, completo

Nueve etapas, cinco capas, 117 tests. QHAWAY pasó de documento de visión a sistema
que evalúa una entrega de punta a punta:

| Capa | Módulos | Qué hace |
|---|---|---|
| **dominio** | rubrica, nota, estados, deteccion, esquema_salidas, calibracion, contenido | Reglas puras, 100% testeables sin infraestructura |
| **infra** | persistencia (SQLite+carpetas), extraccion, conector_ia, informes, prompts, config | Todo lo que habla con el mundo |
| **servicios** | analizar_entrega, revision, monitor, exportar, calibrar | Orquesta los casos de uso |
| **ui** | revision, monitor, worker, app | PySide6, capa delgada sobre servicios |
| **cli** | qhaway_cli.py | Arnés para ejercitar todo sin UI |

Las decisiones que sostienen el sistema: el dominio no depende de nada (AD-02);
archivos como contenido, base como índice (AD-03); la IA por un puerto testeable
(AD-06); la máquina de estados que hace imposibles los saltos ilegales; y el
principio innegociable — **la IA propone, el docente decide**.

Lo que sigue no es más código: es correr la calibración con tus entregas, empaquetar
en Windows, y el simulacro. Cuando esos cuatro puntos pasen, QHAWAY está listo para
la primera exposición del ciclo.
