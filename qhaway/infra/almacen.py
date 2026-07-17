"""Estructura de carpetas del ciclo (Arquitectura §5.2).

Toda ruta que se guarda en la base es **relativa al directorio raíz del ciclo**:
mover o respaldar la carpeta no rompe nada (GRP-07). Este módulo es la única
fuente de verdad sobre cómo se llaman y dónde van las carpetas, para que la base
y el disco no se contradigan.

La clave de API NO vive acá: va en la config de usuario (%APPDATA%/~/.config).
Los nombres de integrantes NO viven acá: solo en la base (RNF-05, AD-03). El
código de grupo en el nombre de carpeta es un identificador no personal.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

NOMBRE_DB = "qhaway.db"

# Subdirectorios de configuración y recursos del ciclo.
SUBDIRS_CICLO = ("config", "modelo", "prompts", "plantillas", "snapshots", "grupos")


@dataclass(frozen=True)
class Rutas:
    """Resuelve rutas absolutas y relativas dentro de un ciclo dado su raíz."""

    raiz: Path

    @property
    def db(self) -> Path:
        return self.raiz / NOMBRE_DB

    def config(self) -> Path:
        return self.raiz / "config"

    def snapshots(self) -> Path:
        return self.raiz / "snapshots"

    def grupo(self, codigo: str, proyecto_slug: str = "") -> Path:
        nombre = codigo if not proyecto_slug else f"{codigo}-{proyecto_slug}"
        return self.raiz / "grupos" / nombre

    def version(self, carpeta_grupo: Path, exposicion: int, version: int) -> Path:
        return carpeta_grupo / f"expo{exposicion}" / f"v{version}"

    def relativa(self, ruta: Path) -> str:
        """Convierte una ruta absoluta a relativa al raíz (para guardar en la base)."""
        return str(ruta.relative_to(self.raiz).as_posix())

    def absoluta(self, ruta_relativa: str) -> Path:
        return self.raiz / ruta_relativa


def crear_estructura(raiz: Path) -> Rutas:
    """Crea el directorio raíz del ciclo y sus subcarpetas estándar."""
    raiz.mkdir(parents=True, exist_ok=True)
    for sub in SUBDIRS_CICLO:
        (raiz / sub).mkdir(exist_ok=True)
    return Rutas(raiz=raiz)


def crear_carpetas_version(rutas: Rutas, carpeta_version: Path) -> None:
    """Crea las subcarpetas de una versión de entrega (entrega/analisis/revision/informes)."""
    for sub in ("entrega", "analisis", "revision", "informes"):
        (carpeta_version / sub).mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class ReporteIntegridad:
    """Resultado de la verificación de integridad base↔carpetas (Arquitectura §5.2)."""

    faltantes: tuple[str, ...]   # rutas referenciadas en la base que no existen en disco
    huerfanos: tuple[str, ...]   # archivos en disco no referenciados por la base

    @property
    def ok(self) -> bool:
        return not self.faltantes and not self.huerfanos
