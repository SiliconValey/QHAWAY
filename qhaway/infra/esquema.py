"""Esquema de la base y su versionado (Arquitectura §5.1).

El versionado usa `PRAGMA user_version`. `migrar()` aplica en orden las
migraciones cuya versión sea mayor a la actual, de modo que una base vieja se
actualice sin perder datos (compatibilidad hacia adelante, sección 12 de la
arquitectura).

Alcance de la Etapa 2: se crean todas las tablas del modelo, pero los
repositorios de esta etapa cubren el backbone operativo + GRP + CFG-11 +
evaluación/valoración (lo necesario para la regla de oro). Las tablas del
pipeline fino (hallazgo_det, elemento) se crean ya para que las etapas 3-6 no
requieran migración estructural (RNF-07, GRP-05).
"""

from __future__ import annotations

import sqlite3

VERSION_ESQUEMA = 1

# --- DDL de la versión 1 -----------------------------------------------------
_DDL_V1 = """
CREATE TABLE ciclo (
    id                     INTEGER PRIMARY KEY,
    nombre                 TEXT NOT NULL,
    cantidad_preguntas     INTEGER NOT NULL DEFAULT 10,
    cantidad_exposiciones  INTEGER NOT NULL DEFAULT 2,
    presupuesto_mensual    REAL    NOT NULL DEFAULT 20.0
);

CREATE TABLE grupo (
    id         INTEGER PRIMARY KEY,
    ciclo_id   INTEGER NOT NULL REFERENCES ciclo(id),
    codigo     TEXT    NOT NULL,            -- identificador de carpeta (no personal)
    nombre     TEXT    NOT NULL,            -- puede contener datos personales: solo en DB
    proyecto   TEXT    NOT NULL DEFAULT '',
    archivado  INTEGER NOT NULL DEFAULT 0,  -- GRP-08 baja lógica
    UNIQUE (ciclo_id, codigo)
);

CREATE TABLE integrante (
    id          INTEGER PRIMARY KEY,
    grupo_id    INTEGER NOT NULL REFERENCES grupo(id),
    nombre      TEXT    NOT NULL,           -- dato personal: solo en DB (RNF-05)
    fecha_alta  TEXT    NOT NULL,
    fecha_baja  TEXT                        -- NULL = integrante vigente (GRP-02)
);

CREATE TABLE entrega (
    id          INTEGER PRIMARY KEY,
    grupo_id    INTEGER NOT NULL REFERENCES grupo(id),
    exposicion  INTEGER NOT NULL,
    version     INTEGER NOT NULL,           -- GRP-04: re-entrega = versión nueva
    fecha       TEXT    NOT NULL,
    vigente     INTEGER NOT NULL DEFAULT 1, -- marca editable por el docente
    estado      TEXT    NOT NULL,           -- estado de la máquina (dominio.estados)
    UNIQUE (grupo_id, exposicion, version)
);

CREATE TABLE archivo_entrega (
    id                      INTEGER PRIMARY KEY,
    entrega_id              INTEGER NOT NULL REFERENCES entrega(id),
    tipo_artefacto          TEXT    NOT NULL,   -- presentacion|srs|fd|ui
    ruta_relativa           TEXT    NOT NULL,   -- relativa al raíz del ciclo
    formato                 TEXT    NOT NULL,   -- pdf|docx|ui
    multiarchivo_confirmado INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE snapshot_config (
    id             INTEGER PRIMARY KEY,
    fecha          TEXT NOT NULL,
    ruta_relativa  TEXT NOT NULL,
    hash           TEXT NOT NULL               -- CFG-11
);

CREATE TABLE evaluacion (
    id                INTEGER PRIMARY KEY,
    entrega_id        INTEGER NOT NULL REFERENCES entrega(id),
    snapshot_id       INTEGER REFERENCES snapshot_config(id),
    estado            TEXT    NOT NULL,
    nota_sugerida     INTEGER,
    nota_final        INTEGER,                 -- solo tras validación (EXP-03)
    fecha_validacion  TEXT
);

CREATE TABLE valoracion (
    id             INTEGER PRIMARY KEY,
    evaluacion_id  INTEGER NOT NULL REFERENCES evaluacion(id),
    criterio_id    TEXT    NOT NULL,
    nivel_ia       TEXT,                        -- REV-04: se conservan ambos
    nivel_final    TEXT,
    UNIQUE (evaluacion_id, criterio_id)
);

CREATE TABLE analisis (
    id             INTEGER PRIMARY KEY,
    evaluacion_id  INTEGER NOT NULL REFERENCES evaluacion(id),
    unidad         TEXT    NOT NULL,   -- presentacion|srs|fd|ui|transversal
    estado         TEXT    NOT NULL,   -- pendiente|completado (reanudación EVA-10)
    intento        INTEGER NOT NULL DEFAULT 0,
    fecha          TEXT,
    UNIQUE (evaluacion_id, unidad)
);

-- Tablas del pipeline fino: se crean ya (sin repos en Etapa 2) para no migrar
-- estructura en etapas 3-6.
CREATE TABLE hallazgo_det (
    id             INTEGER PRIMARY KEY,
    evaluacion_id  INTEGER NOT NULL REFERENCES evaluacion(id),
    tipo           TEXT NOT NULL,
    artefacto      TEXT,
    detalle        TEXT
);

CREATE TABLE elemento (
    id                 INTEGER PRIMARY KEY,
    evaluacion_id      INTEGER NOT NULL REFERENCES evaluacion(id),
    tipo               TEXT NOT NULL,   -- observacion|pregunta_defensa|senal
    criterio_id        TEXT,
    contenido_original TEXT,
    contenido_final    TEXT,
    origen             TEXT,            -- ia_aceptado|ia_editado|docente
    estado_revision    TEXT,           -- pendiente|aceptado|editado|descartado
    referencia         TEXT
);

CREATE TABLE consumo_api (
    id              INTEGER PRIMARY KEY,
    analisis_id     INTEGER,
    tokens_entrada  INTEGER,
    tokens_salida   INTEGER,
    tokens_cache    INTEGER,
    costo_estimado  REAL,
    reintento       INTEGER NOT NULL DEFAULT 0,
    fecha           TEXT
);
"""

# Registro de migraciones: (version_destino, sql). Aplicadas en orden ascendente.
_MIGRACIONES: list[tuple[int, str]] = [
    (1, _DDL_V1),
]


def version_actual(con: sqlite3.Connection) -> int:
    return con.execute("PRAGMA user_version").fetchone()[0]


def migrar(con: sqlite3.Connection) -> int:
    """Aplica las migraciones pendientes. Devuelve la versión resultante."""
    actual = version_actual(con)
    for destino, sql in _MIGRACIONES:
        if destino > actual:
            con.executescript(sql)
            con.execute(f"PRAGMA user_version = {destino}")
            actual = destino
    return actual
