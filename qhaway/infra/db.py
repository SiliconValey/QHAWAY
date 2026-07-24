"""Conexión a SQLite y manejo de transacciones (AD-03).

`sqlite3` de la biblioteca estándar, sin ORM: los repositorios escriben SQL a
mano. Este módulo centraliza la apertura de la conexión (con los PRAGMA que
importan) y ofrece un contexto de transacción que hace commit al salir bien y
rollback ante cualquier excepción — la mitad SQLite de la regla "ninguna
escritura queda a medias" (RNF-06).
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


def conectar(ruta_db: Path | str) -> sqlite3.Connection:
    """Abre (o crea) la base en `ruta_db` con la configuración estándar.

    - `row_factory = sqlite3.Row` para acceder por nombre de columna.
    - `foreign_keys = ON`: las FK se respetan (por defecto SQLite las ignora).
    - `journal_mode = WAL`: lecturas concurrentes con la escritura, y menos
      riesgo de corrupción ante cierre abrupto (RNF-06).
    """
    con = sqlite3.connect(
        str(ruta_db),
        isolation_level=None,      # autocommit; las transacciones se manejan a mano
        check_same_thread=False,   # el worker de análisis corre en otro hilo (AD-08)
    )
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA journal_mode = WAL")
    con.execute("PRAGMA synchronous = NORMAL")
    return con


@contextmanager
def transaccion(con: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Contexto transaccional explícito: commit al salir, rollback ante error.

    Se usa con `isolation_level=None` (autocommit): abrimos la transacción con
    BEGIN y la cerramos nosotros, de modo que el alcance sea inequívoco.
    """
    con.execute("BEGIN")
    try:
        yield con
    except Exception:
        con.execute("ROLLBACK")
        raise
    else:
        con.execute("COMMIT")
