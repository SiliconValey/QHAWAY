"""Configuración del ciclo (CFG-01/09/10) — servicios para la vista ui.configuracion.

La clave de API y la prueba de conexión ya viven en `infra.config_usuario`; acá se
suman la carga validada de la rúbrica y la actualización de parámetros del ciclo.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from ..dominio.rubrica import Rubrica
from ..infra.db import transaccion


def cargar_rubrica(ciclo, ruta_yaml: Path | str) -> Rubrica:
    """Valida una rúbrica y, si es válida, la copia a config/ del ciclo (CFG-01).

    Devuelve la Rubrica validada. Levanta RubricaInvalida si no cumple CFG-01 —la
    rúbrica inválida nunca llega a copiarse.
    """
    ruta_yaml = Path(ruta_yaml)
    datos = yaml.safe_load(ruta_yaml.read_text(encoding="utf-8"))
    rubrica = Rubrica.desde_dict(datos)  # valida; levanta si es inválida

    destino = ciclo.rutas.config() / "rubrica.yaml"
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ruta_yaml, destino)
    return rubrica


def rubrica_activa(ciclo) -> Rubrica | None:
    """Lee la rúbrica configurada del ciclo (config/rubrica.yaml), o None."""
    ruta = ciclo.rutas.config() / "rubrica.yaml"
    if not ruta.exists():
        return None
    return Rubrica.desde_dict(yaml.safe_load(ruta.read_text(encoding="utf-8")))


def cargar_recurso_config(ciclo, ruta: Path | str, nombre_destino: str) -> Path:
    """Copia un recurso de configuración (checklist, nomenclatura) a config/."""
    ruta = Path(ruta)
    destino = ciclo.rutas.config() / nombre_destino
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ruta, destino)
    return destino


def actualizar_parametros(
    ciclo, *, nombre: str | None = None, cantidad_preguntas: int | None = None,
    cantidad_exposiciones: int | None = None, presupuesto_mensual: float | None = None,
) -> None:
    """Actualiza los parámetros del ciclo (CFG-10)."""
    if cantidad_preguntas is not None and cantidad_preguntas < 1:
        raise ValueError("La cantidad de preguntas debe ser al menos 1 (CFG-10).")
    with transaccion(ciclo.con):
        ciclo.ciclos.actualizar_parametros(
            ciclo.ciclo_id, nombre=nombre, cantidad_preguntas=cantidad_preguntas,
            cantidad_exposiciones=cantidad_exposiciones, presupuesto_mensual=presupuesto_mensual,
        )


def cargar_contexto(ciclo, rubrica):
    """Arma el ContextoAnalisis desde la configuración del ciclo.

    Lee checklist y nomenclatura de config/ si existen; si no, usa los defaults.
    El texto del proyecto modelo se toma de modelo/<tipo>.txt si está presente.
    """
    import yaml

    from ..infra import CHECKLIST_DEFECTO, NOMENCLATURA_DEFECTO, cargar_checklist, cargar_nomenclatura
    from ..servicios import ContextoAnalisis

    config = ciclo.rutas.config()

    ruta_ck = config / "checklist.yaml"
    checklists = (
        cargar_checklist(yaml.safe_load(ruta_ck.read_text(encoding="utf-8")))
        if ruta_ck.exists() else CHECKLIST_DEFECTO
    )
    ruta_nm = config / "nomenclatura.yaml"
    nomenclatura = (
        cargar_nomenclatura(yaml.safe_load(ruta_nm.read_text(encoding="utf-8")))
        if ruta_nm.exists() else NOMENCLATURA_DEFECTO
    )

    modelo = {}
    carpeta_modelo = ciclo.rutas.raiz / "modelo"
    if carpeta_modelo.exists():
        for f in carpeta_modelo.glob("*.txt"):
            modelo[f.stem] = f.read_text(encoding="utf-8")

    ciclo_row = ciclo.ciclos.obtener(ciclo.ciclo_id)
    return ContextoAnalisis(
        rubrica=rubrica, checklists=checklists, nomenclatura=nomenclatura,
        modelo=modelo, cantidad_preguntas=ciclo_row.cantidad_preguntas if ciclo_row else 10,
    )
