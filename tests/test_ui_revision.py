"""Tests de humo de la UI de revisión (pytest-qt, offscreen).

Verifican que los flujos aceptar/editar/descartar de la vista delegan bien en el
servicio y que el botón validar se habilita solo cuando corresponde (EXP-03).
La lógica de fondo ya está testeada en test_revision.py; acá se prueba la costura
vista↔servicio.
"""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")
pytest.importorskip("pytestqt")

from qhaway.dominio.estados import EstadoEvaluacion as E
from qhaway.dominio.niveles import Nivel
from qhaway.dominio.rubrica import Rubrica
from qhaway.infra import crear_ciclo
from qhaway.ui.monitor import VistaMonitor
from qhaway.ui.revision import VistaRevision


def _rubrica():
    niveles = {n.value: "..." for n in Nivel}
    return Rubrica.desde_dict({"rubrica": {"nombre": "R", "escala": {"tope_por_critico": 6},
        "secciones": [{"artefacto": "srs", "criterios": [
            {"id": "SRS-REQ", "descripcion": "d", "peso": 1, "niveles": niveles}]}]}},
        artefactos_requeridos=frozenset())


def _setup(tmp_path):
    c = crear_ciclo(tmp_path / "c", "ciclo")
    gid = c.grupos.crear(c.ciclo_id, "G01", "N", "P")
    entrega = c.entregas.crear_version(gid, 1, "2027-04-10", E.ENTREGA_CARGADA.value)
    for destino in (E.ANALIZANDO, E.BORRADOR_EN_REVISION):
        c.transicionar_entrega(entrega.id, destino)
    ev_id = c.evaluaciones.crear(entrega.id, E.BORRADOR_EN_REVISION.value)
    c.valoraciones.registrar(ev_id, "SRS-REQ", Nivel.BUENO.value, None)
    c.evaluaciones.fijar_nota_sugerida(ev_id, 8)
    e1 = c.elementos.crear(ev_id, "observacion", contenido_original="obs 1")
    e2 = c.elementos.crear(ev_id, "observacion", contenido_original="obs 2")
    e3 = c.elementos.crear(ev_id, "pregunta_defensa", contenido_original="¿por qué?")
    return c, entrega, ev_id, (e1, e2, e3)


def test_vista_revision_flujo_completo(qtbot, tmp_path):
    c, entrega, ev_id, (e1, e2, e3) = _setup(tmp_path)
    vista = VistaRevision(c, entrega.id, ev_id, _rubrica())
    qtbot.addWidget(vista)

    # La tabla muestra los 3 elementos; validar deshabilitado (hay pendientes).
    assert vista.tabla.rowCount() == 3
    assert not vista.btn_validar.isEnabled()

    # Aceptar / editar / descartar a través de la vista
    vista.aceptar(e1)
    vista.editar(e2, "corregida")
    vista.descartar(e3)
    assert c.elementos.obtener(e2)["contenido_final"] == "corregida"
    assert c.elementos.pendientes(ev_id) == 0

    # Aún falta la nota final -> sigue deshabilitado
    assert not vista.btn_validar.isEnabled()

    # Fijada la nota, se habilita y se puede validar
    vista.fijar_nota_final(7, "2027-04-13")
    assert vista.btn_validar.isEnabled()

    vista.validar()
    estado = c.con.execute(
        "SELECT estado FROM entrega WHERE id = ?", (entrega.id,)
    ).fetchone()["estado"]
    assert estado == E.EVALUACION_VALIDADA.value
    c.cerrar()


def test_vista_revision_refresca_estados_en_tabla(qtbot, tmp_path):
    c, entrega, ev_id, (e1, e2, e3) = _setup(tmp_path)
    vista = VistaRevision(c, entrega.id, ev_id, _rubrica())
    qtbot.addWidget(vista)

    vista.descartar(e1)
    # La columna Estado (índice 2) de la primera fila refleja el descarte
    assert vista.tabla.item(0, 2).text() == "descartado"
    c.cerrar()


def test_vista_monitor_muestra_presupuesto(qtbot, tmp_path):
    c, entrega, ev_id, _ = _setup(tmp_path)
    aid = c.analisis.crear_unidad(ev_id, "srs", "2027-04-10")
    c.consumos.registrar(aid, tokens_entrada=100, tokens_salida=50, tokens_cache=0,
                         costo_estimado=0.5, reintento=0, fecha="2027-04-10")
    vista = VistaMonitor(c, ev_id)
    qtbot.addWidget(vista)
    assert "USD" in vista.lbl_presupuesto.text()
    assert "0.5" in vista.lbl_costo_eval.text()
    c.cerrar()
