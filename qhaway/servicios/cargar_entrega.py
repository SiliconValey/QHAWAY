"""Carga y clasificación de entregas (ING-01/03/05).

Crea una versión de entrega (GRP-04), copia los archivos a la carpeta de la
versión y los registra clasificados por tipo de artefacto. La vista `ui.entrega`
solo recolecta los archivos y su tipo; la lógica de versionado y copia vive acá.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from ..dominio.estados import EstadoEvaluacion
from ..infra.db import transaccion

# Extensión → formato declarado (ING-02).
_FORMATOS = {".pdf": "pdf", ".docx": "docx", ".ui": "ui"}


@dataclass(frozen=True)
class ArchivoACargar:
    ruta: Path
    tipo_artefacto: str          # presentacion|srs|fd|ui
    # El formato se deduce de la extensión.


def clasificar_por_extension(ruta: Path) -> str | None:
    """Sugerencia de tipo para el .ui (ING-03); el resto lo confirma el docente."""
    if ruta.suffix.lower() == ".ui":
        return "ui"
    return None


def sugerir_tipo(ruta: Path) -> tuple[str | None, str]:
    """Sugiere el tipo de un archivo por su contenido (ING-03).

    Devuelve (tipo_sugerido, motivo). El .ui se resuelve por extensión; los
    documentos se clasifican leyendo su texto. Es una sugerencia: el docente
    confirma o corrige.
    """
    from ..dominio.clasificacion import clasificar_texto
    from ..infra.extraccion import extraer

    por_ext = clasificar_por_extension(ruta)
    if por_ext is not None:
        return por_ext, "Detectado por extensión (.ui)."

    res = extraer(ruta, "desconocido")
    if not res.ok or not hasattr(res.contenido, "texto"):
        return None, "No se pudo leer el contenido para sugerir un tipo."

    clasif = clasificar_texto(res.contenido.texto)
    return clasif.tipo_sugerido, clasif.motivo


class TipoDuplicado(ValueError):
    """Dos o más archivos fueron marcados con el mismo tipo de artefacto (ING-03).

    Se rechaza en vez de pisar uno en silencio: cada tipo (srs, fd, presentacion,
    ui) admite un solo archivo por entrega, y elegir cuál es decisión del docente.
    """


def detectar_tipos_duplicados(archivos: list[ArchivoACargar]) -> dict[str, list[str]]:
    """Devuelve {tipo: [nombres]} para los tipos asignados a más de un archivo."""
    por_tipo: dict[str, list[str]] = {}
    for a in archivos:
        por_tipo.setdefault(a.tipo_artefacto, []).append(a.ruta.name)
    return {tipo: nombres for tipo, nombres in por_tipo.items() if len(nombres) > 1}


def cargar_entrega(
    ciclo, grupo, exposicion: int, archivos: list[ArchivoACargar], *, fecha: str | None = None
):
    """Crea una versión de entrega con sus archivos (ING-01, GRP-04).

    Copia cada archivo a `entrega/` de la versión y lo registra. Devuelve la
    Entrega creada. Levanta ValueError por formato no soportado (ING-02) y
    TipoDuplicado si dos archivos comparten tipo (ING-03).
    """
    fecha = fecha or date.today().isoformat()

    for a in archivos:
        if a.ruta.suffix.lower() not in _FORMATOS:
            raise ValueError(f"Formato no soportado: {a.ruta.name} (ING-02).")

    # Rechazar tipos duplicados ANTES de crear la versión (nada se persiste si falla).
    duplicados = detectar_tipos_duplicados(archivos)
    if duplicados:
        detalle = "; ".join(
            f"'{tipo}': {', '.join(nombres)}" for tipo, nombres in duplicados.items()
        )
        raise TipoDuplicado(
            f"Hay archivos con el mismo tipo (cada tipo admite uno solo): {detalle}. "
            "Corregí el tipo de los archivos repetidos antes de cargar."
        )

    with transaccion(ciclo.con):
        entrega = ciclo.entregas.crear_version(
            grupo.id, exposicion, fecha, EstadoEvaluacion.ENTREGA_CARGADA.value
        )

    cv = ciclo.carpeta_version(grupo, exposicion, entrega.version)
    carpeta_entrega = cv / "entrega"
    carpeta_entrega.mkdir(parents=True, exist_ok=True)

    manifiesto = []
    with transaccion(ciclo.con):
        for a in archivos:
            destino = carpeta_entrega / a.ruta.name
            shutil.copy2(a.ruta, destino)
            formato = _FORMATOS[a.ruta.suffix.lower()]
            ciclo.archivos.agregar(
                entrega.id, a.tipo_artefacto, ciclo.rutas.relativa(destino), formato
            )
            manifiesto.append({
                "nombre": a.ruta.name, "tipo_artefacto": a.tipo_artefacto, "formato": formato,
            })

    ciclo.guardar_manifiesto_entrega(grupo, entrega, manifiesto)
    return entrega
