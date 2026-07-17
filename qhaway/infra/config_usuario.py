"""Configuración de usuario: clave de API (CFG-07) y prueba de conexión (CFG-08).

La clave vive en la config del usuario, **fuera del directorio del ciclo y del
repositorio** (RNF-04): `%APPDATA%/qhaway` en Windows, `~/.config/qhaway` en
Linux/Mac. Consecuencia deliberada: respaldar o compartir un ciclo jamás incluye
la credencial. La clave nunca se escribe en logs, informes ni persistencia del
ciclo (CFG-07).

Nota de evolución: en Fase 3 esto debería migrar al keyring del sistema operativo.
"""

from __future__ import annotations

import json
import os
from pathlib import Path


def dir_config_usuario() -> Path:
    """Directorio de configuración de usuario, según plataforma."""
    if os.name == "nt":  # Windows
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / "qhaway"
    return Path.home() / ".config" / "qhaway"


def _ruta_credenciales() -> Path:
    return dir_config_usuario() / "credenciales.json"


def guardar_clave(api_key: str) -> Path:
    """Guarda la clave de API en la config de usuario (CFG-07)."""
    ruta = _ruta_credenciales()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps({"anthropic_api_key": api_key}), encoding="utf-8")
    # Permisos restrictivos donde el SO lo soporte (no en Windows).
    try:
        os.chmod(ruta, 0o600)
    except OSError:
        pass
    return ruta


def cargar_clave() -> str | None:
    """Lee la clave de API. Precedencia: variable de entorno, luego archivo.

    Permitir `ANTHROPIC_API_KEY` facilita CI y uso avanzado sin tocar el archivo.
    """
    de_entorno = os.environ.get("ANTHROPIC_API_KEY")
    if de_entorno:
        return de_entorno
    ruta = _ruta_credenciales()
    if not ruta.exists():
        return None
    try:
        return json.loads(ruta.read_text(encoding="utf-8")).get("anthropic_api_key")
    except (json.JSONDecodeError, OSError):
        return None


def probar_conexion(
    api_key: str | None = None, *, modelo: str = "claude-sonnet-4-6"
) -> tuple[bool, str]:
    """Valida la clave con una llamada mínima (CFG-08).

    Devuelve (ok, mensaje). No levanta: reporta el problema para diagnóstico.
    """
    clave = api_key or cargar_clave()
    if not clave:
        return False, "No hay clave de API configurada."

    try:
        import anthropic
    except ImportError:
        return False, "El SDK de Anthropic no está instalado (pip install anthropic)."

    try:
        cliente = anthropic.Anthropic(api_key=clave)
        cliente.messages.create(
            model=modelo,
            max_tokens=8,
            messages=[{"role": "user", "content": "ping"}],
        )
        return True, f"Conexión OK con el modelo {modelo}."
    except Exception as e:  # noqa: BLE001 - queremos el diagnóstico crudo
        return False, f"Falló la conexión: {e}"
