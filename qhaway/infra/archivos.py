"""Escritura atómica de archivos (RNF-06).

La regla: nunca dejar un archivo a medias. Se escribe en un temporal en el mismo
directorio y se hace `os.replace` (renombre atómico dentro del mismo sistema de
archivos). Si el proceso muere en medio de la escritura, el archivo de destino
conserva su versión anterior íntegra o directamente no existe — nunca queda un
JSON truncado que rompa la reconstrucción de la regla de oro.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def escribir_atomico(ruta: Path | str, contenido: str, *, encoding: str = "utf-8") -> None:
    """Escribe `contenido` en `ruta` de forma atómica (temporal + renombre)."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    # El temporal debe estar en el MISMO directorio para que os.replace sea atómico.
    fd, tmp = tempfile.mkstemp(dir=str(ruta.parent), prefix=".tmp_", suffix=ruta.suffix)
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(contenido)
            f.flush()
            os.fsync(f.fileno())  # asegurar que llegó al disco antes de renombrar
        os.replace(tmp, ruta)     # atómico
    except Exception:
        # Si algo falla, no dejar basura.
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def escribir_json(ruta: Path | str, datos: Any) -> None:
    """Serializa `datos` a JSON legible y lo escribe atómicamente."""
    texto = json.dumps(datos, ensure_ascii=False, indent=2, sort_keys=True)
    escribir_atomico(ruta, texto + "\n")


def leer_json(ruta: Path | str) -> Any:
    """Lee y parsea un JSON. Propaga el error si el archivo no existe o es inválido."""
    return json.loads(Path(ruta).read_text(encoding="utf-8"))
