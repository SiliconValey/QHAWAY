"""Repositorios de persistencia (AD-03: SQL a mano, sin ORM).

Cada repositorio encapsula el acceso a una tabla. No hay lógica de dominio acá:
las reglas de negocio viven en `qhaway.dominio`. Sí viven acá las reglas de
persistencia (versionado de entregas, baja lógica, historial por fechas).

Las escrituras se hacen dentro de una transacción abierta por el llamador
(`db.transaccion`), para que un caso de uso agrupe varias inserciones de forma
atómica (RNF-06).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass


# ----------------------------------------------------------------------------
# Ciclo
# ----------------------------------------------------------------------------
@dataclass(frozen=True)
class Ciclo:
    id: int
    nombre: str
    cantidad_preguntas: int
    cantidad_exposiciones: int
    presupuesto_mensual: float


class CicloRepo:
    def __init__(self, con: sqlite3.Connection) -> None:
        self.con = con

    def crear(
        self,
        nombre: str,
        *,
        cantidad_preguntas: int = 10,
        cantidad_exposiciones: int = 2,
        presupuesto_mensual: float = 20.0,
    ) -> int:
        cur = self.con.execute(
            "INSERT INTO ciclo (nombre, cantidad_preguntas, cantidad_exposiciones, "
            "presupuesto_mensual) VALUES (?, ?, ?, ?)",
            (nombre, cantidad_preguntas, cantidad_exposiciones, presupuesto_mensual),
        )
        return int(cur.lastrowid)

    def obtener(self, ciclo_id: int) -> Ciclo | None:
        fila = self.con.execute(
            "SELECT * FROM ciclo WHERE id = ?", (ciclo_id,)
        ).fetchone()
        return _a_ciclo(fila) if fila else None

    def actualizar_parametros(
        self, ciclo_id: int, *, nombre: str | None = None,
        cantidad_preguntas: int | None = None, cantidad_exposiciones: int | None = None,
        presupuesto_mensual: float | None = None,
    ) -> None:
        """Actualiza los parámetros del ciclo (CFG-10)."""
        campos, params = [], []
        for col, val in (
            ("nombre", nombre), ("cantidad_preguntas", cantidad_preguntas),
            ("cantidad_exposiciones", cantidad_exposiciones),
            ("presupuesto_mensual", presupuesto_mensual),
        ):
            if val is not None:
                campos.append(f"{col} = ?")
                params.append(val)
        if not campos:
            return
        params.append(ciclo_id)
        self.con.execute(f"UPDATE ciclo SET {', '.join(campos)} WHERE id = ?", params)


# ----------------------------------------------------------------------------
# Grupo + Integrante (GRP-01, GRP-02, GRP-08)
# ----------------------------------------------------------------------------
@dataclass(frozen=True)
class Grupo:
    id: int
    ciclo_id: int
    codigo: str
    nombre: str
    proyecto: str
    archivado: bool


class GrupoRepo:
    def __init__(self, con: sqlite3.Connection) -> None:
        self.con = con

    def crear(
        self, ciclo_id: int, codigo: str, nombre: str, proyecto: str = ""
    ) -> int:
        cur = self.con.execute(
            "INSERT INTO grupo (ciclo_id, codigo, nombre, proyecto) "
            "VALUES (?, ?, ?, ?)",
            (ciclo_id, codigo, nombre, proyecto),
        )
        return int(cur.lastrowid)

    def archivar(self, grupo_id: int) -> None:
        """Baja lógica (GRP-08): nunca se borra físicamente un grupo con historial."""
        self.con.execute("UPDATE grupo SET archivado = 1 WHERE id = ?", (grupo_id,))

    def listar(self, ciclo_id: int, *, incluir_archivados: bool = False) -> list[Grupo]:
        sql = "SELECT * FROM grupo WHERE ciclo_id = ?"
        if not incluir_archivados:
            sql += " AND archivado = 0"
        sql += " ORDER BY codigo"
        return [_a_grupo(f) for f in self.con.execute(sql, (ciclo_id,)).fetchall()]

    def obtener(self, grupo_id: int) -> Grupo | None:
        fila = self.con.execute(
            "SELECT * FROM grupo WHERE id = ?", (grupo_id,)
        ).fetchone()
        return _a_grupo(fila) if fila else None


class IntegranteRepo:
    def __init__(self, con: sqlite3.Connection) -> None:
        self.con = con

    def agregar(self, grupo_id: int, nombre: str, fecha_alta: str) -> int:
        cur = self.con.execute(
            "INSERT INTO integrante (grupo_id, nombre, fecha_alta) VALUES (?, ?, ?)",
            (grupo_id, nombre, fecha_alta),
        )
        return int(cur.lastrowid)

    def dar_baja(self, integrante_id: int, fecha_baja: str) -> None:
        """GRP-02: baja con fecha; no se elimina, para reconstruir composiciones."""
        self.con.execute(
            "UPDATE integrante SET fecha_baja = ? WHERE id = ?",
            (fecha_baja, integrante_id),
        )

    def composicion_en(self, grupo_id: int, fecha: str) -> list[str]:
        """Integrantes vigentes del grupo en una fecha dada (GRP-02).

        Vigente = alta <= fecha AND (sin baja OR baja > fecha).
        """
        filas = self.con.execute(
            "SELECT nombre FROM integrante WHERE grupo_id = ? "
            "AND fecha_alta <= ? AND (fecha_baja IS NULL OR fecha_baja > ?) "
            "ORDER BY nombre",
            (grupo_id, fecha, fecha),
        ).fetchall()
        return [f["nombre"] for f in filas]


# ----------------------------------------------------------------------------
# Entrega + Archivo (GRP-04)
# ----------------------------------------------------------------------------
@dataclass(frozen=True)
class Entrega:
    id: int
    grupo_id: int
    exposicion: int
    version: int
    fecha: str
    vigente: bool
    estado: str


class EntregaRepo:
    def __init__(self, con: sqlite3.Connection) -> None:
        self.con = con

    def crear_version(
        self, grupo_id: int, exposicion: int, fecha: str, estado: str
    ) -> Entrega:
        """Inserta una nueva versión de entrega (GRP-04).

        La versión es la siguiente correlativa para (grupo, exposición). La nueva
        pasa a ser la vigente y las anteriores dejan de serlo (por defecto la
        última cargada es vigente; el docente puede cambiarlo con `marcar_vigente`).
        """
        prev = self.con.execute(
            "SELECT COALESCE(MAX(version), 0) AS m FROM entrega "
            "WHERE grupo_id = ? AND exposicion = ?",
            (grupo_id, exposicion),
        ).fetchone()["m"]
        nueva_version = prev + 1
        # Las anteriores dejan de ser vigentes.
        self.con.execute(
            "UPDATE entrega SET vigente = 0 WHERE grupo_id = ? AND exposicion = ?",
            (grupo_id, exposicion),
        )
        cur = self.con.execute(
            "INSERT INTO entrega (grupo_id, exposicion, version, fecha, vigente, estado) "
            "VALUES (?, ?, ?, ?, 1, ?)",
            (grupo_id, exposicion, nueva_version, fecha, estado),
        )
        return Entrega(
            id=int(cur.lastrowid),
            grupo_id=grupo_id,
            exposicion=exposicion,
            version=nueva_version,
            fecha=fecha,
            vigente=True,
            estado=estado,
        )

    def marcar_vigente(self, entrega_id: int) -> None:
        """El docente designa manualmente la versión vigente (GRP-04)."""
        fila = self.con.execute(
            "SELECT grupo_id, exposicion FROM entrega WHERE id = ?", (entrega_id,)
        ).fetchone()
        if fila is None:
            raise KeyError(f"No existe entrega {entrega_id}")
        self.con.execute(
            "UPDATE entrega SET vigente = 0 WHERE grupo_id = ? AND exposicion = ?",
            (fila["grupo_id"], fila["exposicion"]),
        )
        self.con.execute(
            "UPDATE entrega SET vigente = 1 WHERE id = ?", (entrega_id,)
        )

    def actualizar_estado(self, entrega_id: int, estado: str) -> None:
        self.con.execute(
            "UPDATE entrega SET estado = ? WHERE id = ?", (estado, entrega_id)
        )

    def vigente(self, grupo_id: int, exposicion: int) -> Entrega | None:
        fila = self.con.execute(
            "SELECT * FROM entrega WHERE grupo_id = ? AND exposicion = ? AND vigente = 1",
            (grupo_id, exposicion),
        ).fetchone()
        return _a_entrega(fila) if fila else None

    def historial(self, grupo_id: int, exposicion: int) -> list[Entrega]:
        filas = self.con.execute(
            "SELECT * FROM entrega WHERE grupo_id = ? AND exposicion = ? "
            "ORDER BY version",
            (grupo_id, exposicion),
        ).fetchall()
        return [_a_entrega(f) for f in filas]


class ArchivoEntregaRepo:
    def __init__(self, con: sqlite3.Connection) -> None:
        self.con = con

    def agregar(
        self,
        entrega_id: int,
        tipo_artefacto: str,
        ruta_relativa: str,
        formato: str,
        multiarchivo_confirmado: bool = False,
    ) -> int:
        cur = self.con.execute(
            "INSERT INTO archivo_entrega (entrega_id, tipo_artefacto, ruta_relativa, "
            "formato, multiarchivo_confirmado) VALUES (?, ?, ?, ?, ?)",
            (entrega_id, tipo_artefacto, ruta_relativa, formato, int(multiarchivo_confirmado)),
        )
        return int(cur.lastrowid)

    def de_entrega(self, entrega_id: int) -> list[sqlite3.Row]:
        return self.con.execute(
            "SELECT * FROM archivo_entrega WHERE entrega_id = ?", (entrega_id,)
        ).fetchall()


# ----------------------------------------------------------------------------
# Snapshot de configuración (CFG-11)
# ----------------------------------------------------------------------------
class SnapshotRepo:
    def __init__(self, con: sqlite3.Connection) -> None:
        self.con = con

    def crear(self, fecha: str, ruta_relativa: str, hash_: str) -> int:
        cur = self.con.execute(
            "INSERT INTO snapshot_config (fecha, ruta_relativa, hash) VALUES (?, ?, ?)",
            (fecha, ruta_relativa, hash_),
        )
        return int(cur.lastrowid)


# ----------------------------------------------------------------------------
# Evaluación + Valoración
# ----------------------------------------------------------------------------
@dataclass(frozen=True)
class Evaluacion:
    id: int
    entrega_id: int
    snapshot_id: int | None
    estado: str
    nota_sugerida: int | None
    nota_final: int | None
    fecha_validacion: str | None


class EvaluacionRepo:
    def __init__(self, con: sqlite3.Connection) -> None:
        self.con = con

    def crear(
        self, entrega_id: int, estado: str, snapshot_id: int | None = None
    ) -> int:
        cur = self.con.execute(
            "INSERT INTO evaluacion (entrega_id, snapshot_id, estado) VALUES (?, ?, ?)",
            (entrega_id, snapshot_id, estado),
        )
        return int(cur.lastrowid)

    def fijar_nota_sugerida(self, evaluacion_id: int, nota: int) -> None:
        self.con.execute(
            "UPDATE evaluacion SET nota_sugerida = ? WHERE id = ?", (nota, evaluacion_id)
        )

    def validar(self, evaluacion_id: int, nota_final: int, fecha: str) -> None:
        """Registra la nota final tras validación docente (EXP-03)."""
        self.con.execute(
            "UPDATE evaluacion SET nota_final = ?, fecha_validacion = ?, "
            "estado = 'evaluacion_validada' WHERE id = ?",
            (nota_final, fecha, evaluacion_id),
        )

    def actualizar_estado(self, evaluacion_id: int, estado: str) -> None:
        self.con.execute(
            "UPDATE evaluacion SET estado = ? WHERE id = ?", (estado, evaluacion_id)
        )

    def obtener(self, evaluacion_id: int) -> Evaluacion | None:
        fila = self.con.execute(
            "SELECT * FROM evaluacion WHERE id = ?", (evaluacion_id,)
        ).fetchone()
        return _a_evaluacion(fila) if fila else None


class ValoracionRepo:
    def __init__(self, con: sqlite3.Connection) -> None:
        self.con = con

    def registrar(
        self,
        evaluacion_id: int,
        criterio_id: str,
        nivel_ia: str | None,
        nivel_final: str | None,
    ) -> None:
        self.con.execute(
            "INSERT INTO valoracion (evaluacion_id, criterio_id, nivel_ia, nivel_final) "
            "VALUES (?, ?, ?, ?) "
            "ON CONFLICT(evaluacion_id, criterio_id) DO UPDATE SET "
            "nivel_ia = excluded.nivel_ia, nivel_final = excluded.nivel_final",
            (evaluacion_id, criterio_id, nivel_ia, nivel_final),
        )

    def fijar_nivel_final(self, evaluacion_id: int, criterio_id: str, nivel_final: str) -> None:
        """El docente ajusta la valoración de un criterio (REV-04)."""
        self.con.execute(
            "UPDATE valoracion SET nivel_final = ? WHERE evaluacion_id = ? AND criterio_id = ?",
            (nivel_final, evaluacion_id, criterio_id),
        )

    def de_evaluacion(self, evaluacion_id: int) -> dict[str, dict[str, str | None]]:
        filas = self.con.execute(
            "SELECT criterio_id, nivel_ia, nivel_final FROM valoracion "
            "WHERE evaluacion_id = ?",
            (evaluacion_id,),
        ).fetchall()
        return {
            f["criterio_id"]: {"nivel_ia": f["nivel_ia"], "nivel_final": f["nivel_final"]}
            for f in filas
        }


class AnalisisRepo:
    """Estado de análisis por unidad — el corazón de la reanudación (EVA-10, AD-04).

    `unidad` ∈ {presentacion, srs, fd, ui, transversal}; `estado` ∈
    {pendiente, completado}. Reanudar es, simplemente, ejecutar las unidades que
    no están completadas.
    """

    def __init__(self, con: sqlite3.Connection) -> None:
        self.con = con

    def crear_unidad(self, evaluacion_id: int, unidad: str, fecha: str) -> int:
        cur = self.con.execute(
            "INSERT INTO analisis (evaluacion_id, unidad, estado, intento, fecha) "
            "VALUES (?, ?, 'pendiente', 0, ?)",
            (evaluacion_id, unidad, fecha),
        )
        return int(cur.lastrowid)

    def marcar_completado(self, analisis_id: int, fecha: str) -> None:
        self.con.execute(
            "UPDATE analisis SET estado = 'completado', fecha = ? WHERE id = ?",
            (fecha, analisis_id),
        )

    def incrementar_intento(self, analisis_id: int) -> None:
        self.con.execute(
            "UPDATE analisis SET intento = intento + 1 WHERE id = ?", (analisis_id,)
        )

    def pendientes(self, evaluacion_id: int) -> list[sqlite3.Row]:
        return self.con.execute(
            "SELECT * FROM analisis WHERE evaluacion_id = ? AND estado = 'pendiente' "
            "ORDER BY id",
            (evaluacion_id,),
        ).fetchall()

    def unidades(self, evaluacion_id: int) -> list[sqlite3.Row]:
        return self.con.execute(
            "SELECT * FROM analisis WHERE evaluacion_id = ? ORDER BY id",
            (evaluacion_id,),
        ).fetchall()


class HallazgoDetRepo:
    """Hallazgos determinísticos persistidos (DET, categoría propia)."""

    def __init__(self, con: sqlite3.Connection) -> None:
        self.con = con

    def registrar(self, evaluacion_id: int, tipo: str, artefacto: str, detalle: str) -> int:
        cur = self.con.execute(
            "INSERT INTO hallazgo_det (evaluacion_id, tipo, artefacto, detalle) "
            "VALUES (?, ?, ?, ?)",
            (evaluacion_id, tipo, artefacto, detalle),
        )
        return int(cur.lastrowid)

    def de_evaluacion(self, evaluacion_id: int) -> list[sqlite3.Row]:
        return self.con.execute(
            "SELECT * FROM hallazgo_det WHERE evaluacion_id = ? ORDER BY id",
            (evaluacion_id,),
        ).fetchall()


class ElementoRepo:
    """Elementos del borrador (observaciones, preguntas, señales) — base de REV.

    Todos nacen en estado 'pendiente' (REV-02): el docente aún no los revisó.
    """

    def __init__(self, con: sqlite3.Connection) -> None:
        self.con = con

    def crear(
        self,
        evaluacion_id: int,
        tipo: str,
        *,
        criterio_id: str | None = None,
        contenido_original: str = "",
        origen: str = "ia_aceptado",
        referencia: str = "",
    ) -> int:
        cur = self.con.execute(
            "INSERT INTO elemento (evaluacion_id, tipo, criterio_id, contenido_original, "
            "contenido_final, origen, estado_revision, referencia) "
            "VALUES (?, ?, ?, ?, NULL, ?, 'pendiente', ?)",
            (evaluacion_id, tipo, criterio_id, contenido_original, origen, referencia),
        )
        return int(cur.lastrowid)

    def de_evaluacion(self, evaluacion_id: int, tipo: str | None = None) -> list[sqlite3.Row]:
        if tipo:
            return self.con.execute(
                "SELECT * FROM elemento WHERE evaluacion_id = ? AND tipo = ? ORDER BY id",
                (evaluacion_id, tipo),
            ).fetchall()
        return self.con.execute(
            "SELECT * FROM elemento WHERE evaluacion_id = ? ORDER BY id",
            (evaluacion_id,),
        ).fetchall()

    def obtener(self, elemento_id: int) -> sqlite3.Row | None:
        return self.con.execute(
            "SELECT * FROM elemento WHERE id = ?", (elemento_id,)
        ).fetchone()

    def actualizar_revision(
        self,
        elemento_id: int,
        estado_revision: str,
        *,
        contenido_final: str | None = None,
        origen: str | None = None,
    ) -> None:
        """Actualiza el estado de revisión de un elemento (REV-02/05/07)."""
        sets = ["estado_revision = ?"]
        params: list = [estado_revision]
        if contenido_final is not None:
            sets.append("contenido_final = ?")
            params.append(contenido_final)
        if origen is not None:
            sets.append("origen = ?")
            params.append(origen)
        params.append(elemento_id)
        self.con.execute(
            f"UPDATE elemento SET {', '.join(sets)} WHERE id = ?", params
        )

    def pendientes(self, evaluacion_id: int) -> int:
        return self.con.execute(
            "SELECT COUNT(*) AS n FROM elemento WHERE evaluacion_id = ? "
            "AND estado_revision = 'pendiente'",
            (evaluacion_id,),
        ).fetchone()["n"]

    def conteo_por_estado(self, evaluacion_id: int) -> dict[str, int]:
        """Conteo por estado de revisión + origen, para métricas de retrabajo (REV-06)."""
        filas = self.con.execute(
            "SELECT estado_revision, origen, COUNT(*) AS n FROM elemento "
            "WHERE evaluacion_id = ? GROUP BY estado_revision, origen",
            (evaluacion_id,),
        ).fetchall()
        return {f"{f['estado_revision']}|{f['origen']}": f["n"] for f in filas}


class ConsumoRepo:
    """Registro de consumo de API por llamada (MON-01)."""

    def __init__(self, con: sqlite3.Connection) -> None:
        self.con = con

    def registrar(
        self,
        analisis_id: int | None,
        *,
        tokens_entrada: int,
        tokens_salida: int,
        tokens_cache: int,
        costo_estimado: float,
        reintento: int,
        fecha: str,
    ) -> int:
        cur = self.con.execute(
            "INSERT INTO consumo_api (analisis_id, tokens_entrada, tokens_salida, "
            "tokens_cache, costo_estimado, reintento, fecha) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (analisis_id, tokens_entrada, tokens_salida, tokens_cache,
             costo_estimado, reintento, fecha),
        )
        return int(cur.lastrowid)

    def total_costo(self) -> float:
        fila = self.con.execute(
            "SELECT COALESCE(SUM(costo_estimado), 0.0) AS t FROM consumo_api"
        ).fetchone()
        return float(fila["t"])

    def costo_de_evaluacion(self, evaluacion_id: int) -> float:
        """Costo total de una evaluación (MON-02), sumando el de sus unidades."""
        fila = self.con.execute(
            "SELECT COALESCE(SUM(c.costo_estimado), 0.0) AS t FROM consumo_api c "
            "JOIN analisis a ON a.id = c.analisis_id WHERE a.evaluacion_id = ?",
            (evaluacion_id,),
        ).fetchone()
        return float(fila["t"])

    def costo_del_mes(self, prefijo_mes: str) -> float:
        """Costo acumulado de un mes calendario 'YYYY-MM' (MON-03)."""
        fila = self.con.execute(
            "SELECT COALESCE(SUM(costo_estimado), 0.0) AS t FROM consumo_api "
            "WHERE fecha LIKE ?",
            (prefijo_mes + "%",),
        ).fetchone()
        return float(fila["t"])

    def historico_por_mes(self) -> list[sqlite3.Row]:
        """Costo agrupado por mes (MON-04, histórico exportable)."""
        return self.con.execute(
            "SELECT substr(fecha, 1, 7) AS mes, "
            "COALESCE(SUM(costo_estimado), 0.0) AS costo, COUNT(*) AS llamadas "
            "FROM consumo_api WHERE fecha IS NOT NULL AND fecha != '' "
            "GROUP BY mes ORDER BY mes"
        ).fetchall()


# ----------------------------------------------------------------------------
# Conversores fila -> dataclass
# ----------------------------------------------------------------------------
def _a_ciclo(f: sqlite3.Row) -> Ciclo:
    return Ciclo(
        id=f["id"],
        nombre=f["nombre"],
        cantidad_preguntas=f["cantidad_preguntas"],
        cantidad_exposiciones=f["cantidad_exposiciones"],
        presupuesto_mensual=f["presupuesto_mensual"],
    )


def _a_grupo(f: sqlite3.Row) -> Grupo:
    return Grupo(
        id=f["id"],
        ciclo_id=f["ciclo_id"],
        codigo=f["codigo"],
        nombre=f["nombre"],
        proyecto=f["proyecto"],
        archivado=bool(f["archivado"]),
    )


def _a_entrega(f: sqlite3.Row) -> Entrega:
    return Entrega(
        id=f["id"],
        grupo_id=f["grupo_id"],
        exposicion=f["exposicion"],
        version=f["version"],
        fecha=f["fecha"],
        vigente=bool(f["vigente"]),
        estado=f["estado"],
    )


def _a_evaluacion(f: sqlite3.Row) -> Evaluacion:
    return Evaluacion(
        id=f["id"],
        entrega_id=f["entrega_id"],
        snapshot_id=f["snapshot_id"],
        estado=f["estado"],
        nota_sugerida=f["nota_sugerida"],
        nota_final=f["nota_final"],
        fecha_validacion=f["fecha_validacion"],
    )
