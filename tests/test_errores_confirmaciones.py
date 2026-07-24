"""Tests de manejo de errores (RNF-06) y confirmaciones de acciones irreversibles."""

from __future__ import annotations

import json
import sqlite3

import pytest

from qhaway.ui.errores import InformeError, formatear_excepcion, registrar


def _informe_de(exc: Exception) -> InformeError:
    try:
        raise exc
    except Exception:  # noqa: BLE001
        import sys
        return formatear_excepcion(*sys.exc_info())


# --- Traducción de errores a lenguaje del docente ----------------------------
def test_error_de_conexion_se_traduce():
    inf = _informe_de(ConnectionError("connection refused"))
    assert "conectar" in inf.mensaje.lower()
    assert "reanudar" in inf.sugerencia.lower() or "internet" in inf.sugerencia.lower()
    assert "ConnectionError" in inf.detalle          # el detalle técnico se conserva


def test_archivo_bloqueado_sugiere_cerrarlo():
    inf = _informe_de(PermissionError("archivo en uso"))
    assert "bloqueado" in inf.mensaje.lower() or "acceder" in inf.mensaje.lower()
    assert "otro programa" in inf.sugerencia.lower()


def test_error_de_base_de_datos_se_traduce():
    inf = _informe_de(sqlite3.OperationalError("database is locked"))
    assert "datos del ciclo" in inf.mensaje.lower()


def test_json_invalido_sugiere_reintentar():
    inf = _informe_de(json.JSONDecodeError("Expecting value", "", 0))
    assert "incompleta" in inf.mensaje.lower() or "mal formada" in inf.mensaje.lower()


def test_error_desconocido_usa_mensaje_generico_sin_perder_detalle():
    inf = _informe_de(RuntimeError("algo muy raro"))
    assert "inesperado" in inf.mensaje.lower()
    assert "no se perdió" in inf.sugerencia.lower()
    assert "algo muy raro" in inf.detalle           # el detalle sigue disponible


def test_registrar_escribe_el_log_y_nunca_levanta(tmp_path):
    inf = _informe_de(RuntimeError("para el log"))
    destino = registrar(inf, ruta=tmp_path / "sub" / "errores.log")
    assert destino is not None and destino.exists()
    assert "para el log" in destino.read_text(encoding="utf-8")

    # Ruta imposible (un archivo ocupa el lugar de la carpeta): no debe levantar
    bloqueo = tmp_path / "archivo.txt"
    bloqueo.write_text("soy un archivo, no una carpeta", encoding="utf-8")
    assert registrar(inf, ruta=bloqueo / "imposible.log") is None


# --- Confirmaciones ----------------------------------------------------------
pytest.importorskip("PySide6")
pytest.importorskip("pytestqt")

from qhaway.dominio.estados import EstadoEvaluacion as E  # noqa: E402
from qhaway.infra import crear_ciclo  # noqa: E402
from qhaway.servicios import gestion  # noqa: E402
from qhaway.ui.ciclo import VistaCiclo  # noqa: E402


def test_archivar_grupo_requiere_confirmacion(qtbot, tmp_path):
    c = crear_ciclo(tmp_path / "c", "ciclo")
    gid = gestion.alta_grupo(c, "G01", "Los Punteros", "Proyecto")
    vista = VistaCiclo(c)
    qtbot.addWidget(vista)
    vista.tabla.setCurrentCell(0, 0)

    # El docente cancela: el grupo sigue visible
    vista.confirmar = lambda *a, **k: False
    vista._archivar_seleccionado()
    assert vista.tabla.rowCount() == 1

    # El docente acepta: se archiva
    vista.confirmar = lambda *a, **k: True
    vista._archivar_seleccionado()
    assert vista.tabla.rowCount() == 0
    assert len(gestion.listar_grupos(c, incluir_archivados=True)) == 1  # no se borró
    c.cerrar()


def test_cargar_version_nueva_requiere_confirmacion(qtbot, tmp_path):
    from qhaway.ui.entrega import VistaEntrega

    c = crear_ciclo(tmp_path / "c", "ciclo")
    gid = gestion.alta_grupo(c, "G01", "N", "P")
    grupo = c.grupos.obtener(gid)
    ui = tmp_path / "form.ui"
    ui.write_text('<ui version="4.0"><widget class="QWidget" name="F"/></ui>', encoding="utf-8")

    vista = VistaEntrega(c, grupo, 1)
    qtbot.addWidget(vista)
    vista.agregar_archivo(ui, "ui")
    vista.cargar()                      # primera carga: sin confirmación

    # Segunda carga: si cancela, no se crea versión 2
    vista.agregar_archivo(ui, "ui")
    vista.confirmar = lambda *a, **k: False
    vista._cargar()
    assert c.entregas.vigente(gid, 1).version == 1

    # Si acepta, sí
    vista.confirmar = lambda *a, **k: True
    vista._cargar()
    assert c.entregas.vigente(gid, 1).version == 2
    c.cerrar()
