"""Tests de lectura de grupos ya evaluados (consulta + vista)."""

from __future__ import annotations

import pytest

from qhaway.dominio.estados import EstadoEvaluacion as E
from qhaway.dominio.niveles import Nivel
from qhaway.dominio.rubrica import Rubrica
from qhaway.infra import crear_ciclo
from qhaway.servicios import configurar, consulta, revision


def _rubrica_yaml(tmp_path):
    rub = tmp_path / "r.yaml"
    rub.write_text("""
rubrica:
  nombre: R
  escala: {tope_por_critico: 6}
  secciones:
    - artefacto: presentacion
      criterios: [{id: P1, descripcion: d, peso: 1, niveles: {Insuficiente: a, Regular: b, Bueno: c, Excelente: e}}]
    - artefacto: srs
      criterios: [{id: S1, descripcion: d, peso: 1, niveles: {Insuficiente: a, Regular: b, Bueno: c, Excelente: e}}]
    - artefacto: fd
      criterios: [{id: F1, descripcion: d, peso: 1, niveles: {Insuficiente: a, Regular: b, Bueno: c, Excelente: e}}]
    - artefacto: ui
      criterios: [{id: U1, descripcion: d, peso: 1, niveles: {Insuficiente: a, Regular: b, Bueno: c, Excelente: e}}]
""", encoding="utf-8")
    return rub


def _evaluacion_validada(tmp_path):
    c = crear_ciclo(tmp_path / "c", "ciclo")
    configurar.cargar_rubrica(c, _rubrica_yaml(tmp_path))
    gid = c.grupos.crear(c.ciclo_id, "G100", "QuipuIA", "SIMI")
    grupo = c.grupos.obtener(gid)
    entrega = c.entregas.crear_version(gid, 1, "2027-04-10", E.ENTREGA_CARGADA.value)
    for d in (E.ANALIZANDO, E.BORRADOR_EN_REVISION):
        c.transicionar_entrega(entrega.id, d)
    ev = c.evaluaciones.crear(entrega.id, E.BORRADOR_EN_REVISION.value)
    c.valoraciones.registrar(ev, "S1", Nivel.BUENO.value, None)
    e = c.elementos.crear(ev, "observacion", criterio_id="S1", contenido_original="obs")
    revision.aceptar(c, e)
    revision.fijar_nota_final(c, ev, 8, "2027-04-13")
    revision.validar(c, entrega.id, ev)
    return c, grupo, entrega, ev


def test_listar_evaluados_solo_validadas(tmp_path):
    c, grupo, entrega, ev = _evaluacion_validada(tmp_path)
    # Un segundo grupo SIN validar no debe aparecer
    g2 = c.grupos.crear(c.ciclo_id, "G200", "Otro", "P")
    e2 = c.entregas.crear_version(g2, 1, "2027-04-10", E.ENTREGA_CARGADA.value)
    c.evaluaciones.crear(e2.id, E.BORRADOR_EN_REVISION.value)

    lista = consulta.listar_evaluados(c)
    assert len(lista) == 1
    fila = lista[0]
    assert fila.grupo_codigo == "G100"
    assert fila.nota_final == 8
    assert fila.evaluacion_id == ev
    c.cerrar()


def test_entrega_de_reconstruye(tmp_path):
    c, grupo, entrega, ev = _evaluacion_validada(tmp_path)
    e = consulta.entrega_de(c, entrega.id)
    assert e.id == entrega.id
    assert e.exposicion == entrega.exposicion
    c.cerrar()


def test_vista_evaluados(qtbot, tmp_path):
    pytest.importorskip("PySide6")
    pytest.importorskip("pytestqt")
    from qhaway.ui.evaluados import VistaEvaluados

    c, grupo, entrega, ev = _evaluacion_validada(tmp_path)
    vista = VistaEvaluados(c)
    qtbot.addWidget(vista)
    assert vista.tabla.rowCount() == 1
    assert "G100" in vista.tabla.item(0, 0).text()

    # Ver detalle abre la revisión en modo solo lectura
    detalle = vista.ver_detalle(vista._filas[0])
    qtbot.addWidget(detalle)
    assert detalle.solo_lectura
    assert not detalle.btn_validar.isVisible()
    assert not detalle.btn_aceptar.isVisible()

    # Reexportar regenera los PDF (si hay WeasyPrint)
    if pytest.importorskip("weasyprint", reason="sin motor PDF"):
        informe, guia = vista.reexportar(vista._filas[0])
        assert informe.exists() and guia.exists()
    c.cerrar()
