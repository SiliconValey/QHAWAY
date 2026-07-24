# QHAWAY — Persistencia + arnés CLI (Etapa 2)

Segundo bloque del plan: la **persistencia híbrida SQLite + carpetas** (AD-03) y
el arnés CLI descartable. Depende del dominio de la Etapa 1 (importa la máquina
de estados y el cálculo de nota); el dominio no depende de esta capa (AD-02).

## Qué hay

```
qhaway/infra/
  db.py             Conexión sqlite3 + transacción (commit/rollback)
  esquema.py        DDL + versionado (PRAGMA user_version) + migraciones
  archivos.py       Escritura atómica (temporal + renombre) + JSON
  almacen.py        Estructura de carpetas del ciclo + rutas relativas (§5.2)
  repos.py          Repositorios SQL a mano (sin ORM): Ciclo, Grupo, Integrante,
                    Entrega, Archivo, Snapshot, Evaluacion, Valoracion
  ciclo.py          Fachada: crear/abrir, integridad, materialización a archivos
  reconstruccion.py La REGLA DE ORO: rearmar el trabajo desde las carpetas
qhaway_cli.py       Arnés descartable (crear / listar / demo)
tests/
  test_persistencia.py   GRP-02/04/08, CFG-11, integridad, escritura atómica
  test_regla_de_oro.py   borrar la base y reconstruir
```

## Cubre (SRS)

- **GRP-01** alta de grupos · **GRP-02** historial de integrantes por fechas
  (composición reconstruible a cualquier fecha) · **GRP-04** versionado de
  entregas (re-entrega = versión nueva, `vigente` editable) · **GRP-07** respaldo
  copiando un directorio (base dentro del raíz, rutas relativas) · **GRP-08**
  archivado como baja lógica (sin borrado físico).
- **CFG-11** congelamiento de configuración por evaluación (snapshot con hash).
- **RNF-06** confiabilidad: transacciones SQLite + escritura atómica de archivos.
- **RNF-09** auditabilidad: la evaluación se reconstruye desde la persistencia.

## La regla de oro (criterio de salida)

> Borrar `qhaway.db` y reconstruir **todo el trabajo de evaluación** desde las
> carpetas: entregas, análisis, decisiones, valoraciones y notas.

Se cumple y está testeado (`test_regla_de_oro.py`). Con el alcance preciso de
AD-03: el trabajo de evaluación vive como archivo y se reconstruye íntegro; los
**metadatos operativos** (nombres de integrantes, parámetros del ciclo, consumo)
viven **solo en la base** —los nombres de los alumnos jamás entran en la
estructura de carpetas compartible (RNF-05)— y su pérdida sin respaldo es una
consecuencia aceptada y documentada, no un olvido.

## Correr

```bash
python3 -m pytest -q                 # 38 tests (Etapa 1 + Etapa 2)
python3 qhaway_cli.py demo /tmp/c    # flujo completo + regla de oro en vivo
```

## Decisiones de diseño

- **SQLite = índice; carpetas = contenido** (AD-03). Toda ruta guardada es
  relativa al raíz del ciclo, así mover o respaldar la carpeta no rompe nada.
- **Escritura atómica**: temporal en el mismo directorio + `os.replace`. Un corte
  a mitad de escritura nunca deja un JSON truncado que rompa la reconstrucción.
- **La máquina de estados manda**: los cambios de estado de una entrega pasan por
  `dominio.transicionar`; un estado que la máquina no permite no se persiste.
- **La clave de API no vive en el ciclo**: va en la config de usuario
  (`%APPDATA%/qhaway`, `~/.config/qhaway`). Un respaldo del ciclo jamás la
  contiene (CFG-07, RNF-04).

## Qué sigue (Etapa 3)

Extracción (PyMuPDF, python-docx, ElementTree) + DET (checklist, elementos
formales, nomenclatura del `.ui`). Primer producto usable: QHAWAY sirve **sin
IA**, verificando nomenclatura y completitud gratis. El arnés CLI de esta etapa
es lo que hará verificable su criterio de salida.
