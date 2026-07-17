"""Fachada del ciclo: ata base (índice) y carpetas (contenido) — AD-03.

Expone la API de alto nivel que usan el arnés CLI y, más adelante, los servicios
de aplicación. Dos responsabilidades clave de esta etapa viven acá:

* **Materialización del trabajo de evaluación a archivos.** Todo lo que la regla
  de oro exige reconstruir (entregas, análisis, decisiones, valoraciones, notas)
  se escribe como archivo además de indexarse en la base.
* **Verificación de integridad base↔carpetas** al abrir un ciclo.

La máquina de estados del dominio (Etapa 1) gobierna las transiciones de estado
de la entrega: no se escribe un estado "a mano" que la máquina no permita.
"""

from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path

from ..dominio.estados import EstadoEvaluacion, transicionar
from . import almacen, esquema, repos
from .almacen import ReporteIntegridad, Rutas
from .archivos import escribir_json, leer_json
from .db import conectar, transaccion


@dataclass
class Ciclo:
    """Un ciclo lectivo abierto: conexión + rutas + repositorios."""

    con: object  # sqlite3.Connection
    rutas: Rutas
    ciclo_id: int

    # Repositorios (se arman en __post_init__)
    ciclos: repos.CicloRepo = None            # type: ignore[assignment]
    grupos: repos.GrupoRepo = None            # type: ignore[assignment]
    integrantes: repos.IntegranteRepo = None  # type: ignore[assignment]
    entregas: repos.EntregaRepo = None        # type: ignore[assignment]
    archivos: repos.ArchivoEntregaRepo = None # type: ignore[assignment]
    snapshots: repos.SnapshotRepo = None      # type: ignore[assignment]
    evaluaciones: repos.EvaluacionRepo = None # type: ignore[assignment]
    valoraciones: repos.ValoracionRepo = None # type: ignore[assignment]
    consumos: repos.ConsumoRepo = None        # type: ignore[assignment]
    analisis: repos.AnalisisRepo = None        # type: ignore[assignment]
    hallazgos: repos.HallazgoDetRepo = None    # type: ignore[assignment]
    elementos: repos.ElementoRepo = None       # type: ignore[assignment]

    def __post_init__(self) -> None:
        self.ciclos = repos.CicloRepo(self.con)
        self.grupos = repos.GrupoRepo(self.con)
        self.integrantes = repos.IntegranteRepo(self.con)
        self.entregas = repos.EntregaRepo(self.con)
        self.archivos = repos.ArchivoEntregaRepo(self.con)
        self.snapshots = repos.SnapshotRepo(self.con)
        self.evaluaciones = repos.EvaluacionRepo(self.con)
        self.valoraciones = repos.ValoracionRepo(self.con)
        self.consumos = repos.ConsumoRepo(self.con)
        self.analisis = repos.AnalisisRepo(self.con)
        self.hallazgos = repos.HallazgoDetRepo(self.con)
        self.elementos = repos.ElementoRepo(self.con)

    def cerrar(self) -> None:
        self.con.close()

    # --- Transiciones de estado (vía dominio) -------------------------------
    def transicionar_entrega(
        self, entrega_id: int, hasta: EstadoEvaluacion, **guards
    ) -> None:
        """Cambia el estado de una entrega validando con la máquina del dominio."""
        fila = self.con.execute(
            "SELECT estado FROM entrega WHERE id = ?", (entrega_id,)
        ).fetchone()
        if fila is None:
            raise KeyError(f"No existe entrega {entrega_id}")
        desde = EstadoEvaluacion(fila["estado"])
        nuevo = transicionar(desde, hasta, **guards)  # levanta si es inválido
        with transaccion(self.con):
            self.entregas.actualizar_estado(entrega_id, nuevo.value)

    # --- Materialización del trabajo de evaluación a archivos ---------------
    def carpeta_version(self, grupo: repos.Grupo, exposicion: int, version: int) -> Path:
        cg = self.rutas.grupo(grupo.codigo, _slug(grupo.proyecto))
        return self.rutas.version(cg, exposicion, version)

    def guardar_evaluacion_en_archivo(
        self, grupo: repos.Grupo, entrega: repos.Entrega, datos: dict
    ) -> None:
        """Escribe evaluacion.json (estado, notas, valoraciones) atómicamente."""
        cv = self.carpeta_version(grupo, entrega.exposicion, entrega.version)
        almacen.crear_carpetas_version(self.rutas, cv)
        escribir_json(cv / "evaluacion.json", datos)

    def guardar_analisis_en_archivo(
        self, grupo: repos.Grupo, entrega: repos.Entrega, unidad: str, datos: dict
    ) -> None:
        cv = self.carpeta_version(grupo, entrega.exposicion, entrega.version)
        almacen.crear_carpetas_version(self.rutas, cv)
        escribir_json(cv / "analisis" / f"{unidad}.json", datos)

    def guardar_decisiones_en_archivo(
        self, grupo: repos.Grupo, entrega: repos.Entrega, datos: dict
    ) -> None:
        cv = self.carpeta_version(grupo, entrega.exposicion, entrega.version)
        almacen.crear_carpetas_version(self.rutas, cv)
        escribir_json(cv / "revision" / "decisiones.json", datos)

    def guardar_manifiesto_entrega(
        self, grupo: repos.Grupo, entrega: repos.Entrega, archivos: list[dict]
    ) -> None:
        cv = self.carpeta_version(grupo, entrega.exposicion, entrega.version)
        almacen.crear_carpetas_version(self.rutas, cv)
        escribir_json(cv / "entrega" / "manifiesto.json", {"archivos": archivos})

    # --- CFG-11: instantánea de configuración -------------------------------
    def crear_snapshot(self, fecha: str) -> int:
        """Copia la carpeta config/ a snapshots/<fecha>_<hash>/ y la registra."""
        origen = self.rutas.config()
        hash_ = _hash_carpeta(origen)
        nombre = f"{fecha}_{hash_[:6]}"
        destino = self.rutas.snapshots() / nombre
        if destino.exists():
            shutil.rmtree(destino)
        shutil.copytree(origen, destino)
        rel = self.rutas.relativa(destino)
        with transaccion(self.con):
            return self.snapshots.crear(fecha, rel, hash_)

    # --- Verificación de integridad base↔carpetas ---------------------------
    def verificar_integridad(self) -> ReporteIntegridad:
        """Compara las rutas referenciadas en la base con los archivos en disco."""
        referenciadas: set[str] = set()
        for fila in self.con.execute(
            "SELECT ruta_relativa FROM archivo_entrega"
        ).fetchall():
            referenciadas.add(fila["ruta_relativa"])

        faltantes = tuple(
            sorted(r for r in referenciadas if not self.rutas.absoluta(r).exists())
        )

        # Huérfanos: archivos dentro de grupos/*/entrega/ no referenciados
        # (excluyendo el manifiesto, que es metadato de la carpeta).
        en_disco: set[str] = set()
        base_grupos = self.rutas.raiz / "grupos"
        if base_grupos.exists():
            for f in base_grupos.rglob("*"):
                if f.is_file() and f.parent.name == "entrega" and f.name != "manifiesto.json":
                    en_disco.add(self.rutas.relativa(f))
        huerfanos = tuple(sorted(en_disco - referenciadas))

        return ReporteIntegridad(faltantes=faltantes, huerfanos=huerfanos)


# ----------------------------------------------------------------------------
# Crear / abrir
# ----------------------------------------------------------------------------
def crear_ciclo(
    raiz: Path | str,
    nombre: str,
    *,
    cantidad_preguntas: int = 10,
    cantidad_exposiciones: int = 2,
    presupuesto_mensual: float = 20.0,
) -> Ciclo:
    """Crea la estructura de carpetas, la base con su esquema, y el ciclo."""
    raiz = Path(raiz)
    rutas = almacen.crear_estructura(raiz)
    con = conectar(rutas.db)
    esquema.migrar(con)
    with transaccion(con):
        cid = repos.CicloRepo(con).crear(
            nombre,
            cantidad_preguntas=cantidad_preguntas,
            cantidad_exposiciones=cantidad_exposiciones,
            presupuesto_mensual=presupuesto_mensual,
        )
    return Ciclo(con=con, rutas=rutas, ciclo_id=cid)


def abrir_ciclo(raiz: Path | str) -> Ciclo:
    """Abre un ciclo existente, migrando el esquema si hiciera falta."""
    raiz = Path(raiz)
    rutas = Rutas(raiz=raiz)
    if not rutas.db.exists():
        raise FileNotFoundError(f"No hay base en {rutas.db}")
    con = conectar(rutas.db)
    esquema.migrar(con)
    fila = con.execute("SELECT id FROM ciclo LIMIT 1").fetchone()
    ciclo_id = fila["id"] if fila else 0
    return Ciclo(con=con, rutas=rutas, ciclo_id=ciclo_id)


# ----------------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------------
def _slug(texto: str) -> str:
    base = "".join(c if c.isalnum() else "-" for c in texto.lower())
    return "-".join(p for p in base.split("-") if p)


def _hash_carpeta(carpeta: Path) -> str:
    """Hash estable del contenido de una carpeta (para identificar snapshots)."""
    h = hashlib.sha256()
    for f in sorted(carpeta.rglob("*")):
        if f.is_file():
            h.update(f.relative_to(carpeta).as_posix().encode())
            h.update(f.read_bytes())
    return h.hexdigest()
