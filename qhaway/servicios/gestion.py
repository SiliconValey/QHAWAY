"""Gestión de grupos e integrantes (GRP-01/02/08).

Envuelve las operaciones de los repositorios en transacciones, para que la UI
(vista `ui.ciclo`) llame a una API limpia sin conocer SQL ni manejar commits.
La lógica de persistencia (historial por fechas, baja lógica) ya vive en los
repos; acá se orquesta y se testea sin Qt.
"""

from __future__ import annotations

from datetime import date

from ..infra.db import transaccion


def alta_grupo(
    ciclo, codigo: str, nombre: str, proyecto: str = "", integrantes: list[str] | None = None,
    *, fecha: str | None = None,
) -> int:
    """Da de alta un grupo con sus integrantes iniciales (GRP-01)."""
    fecha = fecha or date.today().isoformat()
    with transaccion(ciclo.con):
        gid = ciclo.grupos.crear(ciclo.ciclo_id, codigo, nombre, proyecto)
        for nombre_int in (integrantes or []):
            ciclo.integrantes.agregar(gid, nombre_int, fecha)
    return gid


def agregar_integrante(ciclo, grupo_id: int, nombre: str, *, fecha: str | None = None) -> int:
    """Alta de un integrante con fecha (GRP-02)."""
    fecha = fecha or date.today().isoformat()
    with transaccion(ciclo.con):
        return ciclo.integrantes.agregar(grupo_id, nombre, fecha)


def baja_integrante(ciclo, integrante_id: int, *, fecha: str | None = None) -> None:
    """Baja de un integrante con fecha, sin borrar (GRP-02)."""
    fecha = fecha or date.today().isoformat()
    with transaccion(ciclo.con):
        ciclo.integrantes.dar_baja(integrante_id, fecha)


def archivar_grupo(ciclo, grupo_id: int) -> None:
    """Archiva un grupo (baja lógica, conserva historial — GRP-08)."""
    with transaccion(ciclo.con):
        ciclo.grupos.archivar(grupo_id)


def listar_grupos(ciclo, *, incluir_archivados: bool = False) -> list:
    return ciclo.grupos.listar(ciclo.ciclo_id, incluir_archivados=incluir_archivados)


def composicion(ciclo, grupo_id: int, fecha: str) -> list[str]:
    """Integrantes vigentes del grupo en una fecha (GRP-02)."""
    return ciclo.integrantes.composicion_en(grupo_id, fecha)
