"""Reconstrucción del trabajo de evaluación desde las carpetas (la "regla de oro").

AD-03, alcance preciso: **los archivos son el contenido de evaluación; la base es
el índice más los metadatos operativos.** Ante corrupción o pérdida de
`qhaway.db`, todo el trabajo de evaluación — entregas, análisis por unidad,
decisiones de revisión, valoraciones y notas — se reconstruye desde el disco sin
pérdida de trabajo validado (RNF-06).

Lo que NO se reconstruye, por diseño deliberado: los nombres de integrantes y los
metadatos operativos (parámetros del ciclo, consumo de API). Nunca entraron en la
estructura de carpetas compartible (RNF-05), así que su pérdida sin respaldo es
una consecuencia aceptada y documentada, no un olvido.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import esquema, repos
from .almacen import NOMBRE_DB, Rutas
from .archivos import leer_json
from .db import conectar, transaccion


@dataclass
class ReporteReconstruccion:
    """Qué se reconstruyó y qué se perdió (para reportar al docente)."""

    grupos: int = 0
    entregas: int = 0
    evaluaciones: int = 0
    valoraciones: int = 0
    analisis: int = 0
    decisiones: int = 0
    # Metadatos NO reconstruibles desde archivos (AD-03): se listan para el docente.
    metadatos_perdidos: list[str] = field(
        default_factory=lambda: [
            "nombres de integrantes (recargar manualmente o desde respaldo)",
            "parámetros del ciclo (nombre, presupuesto, cantidad de preguntas)",
            "consumo de API histórico",
        ]
    )

    def resumen(self) -> str:
        return (
            f"Reconstruido desde carpetas: {self.grupos} grupo(s), "
            f"{self.entregas} entrega(s), {self.evaluaciones} evaluación(es), "
            f"{self.valoraciones} valoración(es), {self.analisis} análisis, "
            f"{self.decisiones} archivo(s) de decisiones.\n"
            f"NO reconstruible desde archivos (por diseño AD-03): "
            + "; ".join(self.metadatos_perdidos)
            + "."
        )


def reconstruir_desde_carpetas(raiz: Path | str) -> ReporteReconstruccion:
    """Recrea `qhaway.db` con el trabajo de evaluación leído del disco.

    Requiere que la base NO exista (o esté vacía); es un procedimiento de
    recuperación, no de fusión. Devuelve un reporte de lo reconstruido y lo
    perdido.
    """
    raiz = Path(raiz)
    rutas = Rutas(raiz=raiz)

    con = conectar(rutas.db)
    esquema.migrar(con)

    rep = ReporteReconstruccion()

    grupo_repo = repos.GrupoRepo(con)
    entrega_repo = repos.EntregaRepo(con)
    archivo_repo = repos.ArchivoEntregaRepo(con)
    eval_repo = repos.EvaluacionRepo(con)
    valor_repo = repos.ValoracionRepo(con)

    with transaccion(con):
        # Ciclo placeholder: sus parámetros son metadatos operativos perdidos.
        ciclo_id = repos.CicloRepo(con).crear("(reconstruido — recargar parámetros)")

        base_grupos = raiz / "grupos"
        if not base_grupos.exists():
            return rep

        for carpeta_grupo in sorted(p for p in base_grupos.iterdir() if p.is_dir()):
            codigo, proyecto = _parsear_nombre_grupo(carpeta_grupo.name)
            # Grupo stub: código y proyecto son recuperables (no personales);
            # el nombre real y los integrantes NO (viven solo en la base).
            grupo_id = grupo_repo.crear(
                ciclo_id,
                codigo=codigo,
                nombre="(reconstruido — recargar integrantes)",
                proyecto=proyecto,
            )
            grupo = grupo_repo.obtener(grupo_id)
            assert grupo is not None
            rep.grupos += 1

            for carpeta_expo in sorted(
                p for p in carpeta_grupo.iterdir() if p.is_dir() and p.name.startswith("expo")
            ):
                exposicion = int(carpeta_expo.name.removeprefix("expo"))
                for carpeta_v in sorted(
                    p for p in carpeta_expo.iterdir() if p.is_dir() and p.name.startswith("v")
                ):
                    version = int(carpeta_v.name.removeprefix("v"))
                    _reconstruir_version(
                        rutas, carpeta_v, grupo, exposicion, version,
                        entrega_repo, archivo_repo, eval_repo, valor_repo, rep,
                    )

    return rep


def _reconstruir_version(
    rutas, carpeta_v: Path, grupo, exposicion, version,
    entrega_repo, archivo_repo, eval_repo, valor_repo, rep,
) -> None:
    eval_json = carpeta_v / "evaluacion.json"
    datos_eval = leer_json(eval_json) if eval_json.exists() else {}
    estado = datos_eval.get("estado", "borrador_en_revision")

    # Entrega. Reinsertamos respetando el número de versión de la carpeta.
    entrega_repo.con.execute(
        "INSERT INTO entrega (grupo_id, exposicion, version, fecha, vigente, estado) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            grupo.id, exposicion, version,
            datos_eval.get("fecha", ""),
            1 if datos_eval.get("vigente", True) else 0,
            estado,
        ),
    )
    entrega_id = int(
        entrega_repo.con.execute(
            "SELECT id FROM entrega WHERE grupo_id = ? AND exposicion = ? AND version = ?",
            (grupo.id, exposicion, version),
        ).fetchone()["id"]
    )
    rep.entregas += 1

    # Archivos de la entrega (desde el manifiesto).
    manifiesto = carpeta_v / "entrega" / "manifiesto.json"
    if manifiesto.exists():
        for a in leer_json(manifiesto).get("archivos", []):
            ruta_rel = rutas.relativa(carpeta_v / "entrega" / a["nombre"])
            archivo_repo.agregar(
                entrega_id, a["tipo_artefacto"], ruta_rel, a["formato"]
            )

    # Evaluación + valoraciones + notas.
    eval_id = eval_repo.crear(entrega_id, estado)
    if datos_eval.get("nota_sugerida") is not None:
        eval_repo.fijar_nota_sugerida(eval_id, datos_eval["nota_sugerida"])
    if datos_eval.get("nota_final") is not None:
        eval_repo.validar(
            eval_id, datos_eval["nota_final"], datos_eval.get("fecha_validacion", "")
        )
    rep.evaluaciones += 1

    for crit, niveles in (datos_eval.get("valoraciones") or {}).items():
        valor_repo.registrar(
            eval_id, crit, niveles.get("nivel_ia"), niveles.get("nivel_final")
        )
        rep.valoraciones += 1

    # Constancia de análisis y decisiones (su contenido queda en disco, íntegro).
    carpeta_analisis = carpeta_v / "analisis"
    if carpeta_analisis.exists():
        rep.analisis += sum(1 for _ in carpeta_analisis.glob("*.json"))
    if (carpeta_v / "revision" / "decisiones.json").exists():
        rep.decisiones += 1


def _parsear_nombre_grupo(nombre: str) -> tuple[str, str]:
    """'G03-distribuidora-andes' -> ('G03', 'distribuidora-andes')."""
    partes = nombre.split("-", 1)
    if len(partes) == 1:
        return partes[0], ""
    return partes[0], partes[1]
