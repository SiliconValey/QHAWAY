"""Test de humo del flujo completo por grupo (cargar → analizar → revisar → exportar)."""

from __future__ import annotations

import json

import pytest

pytest.importorskip("PySide6")
pytest.importorskip("pytestqt")

from qhaway.infra import crear_ciclo
from qhaway.infra.conector_ia import ConectorFalso
from qhaway.servicios import configurar, gestion, revision
from qhaway.ui.flujo import VentanaGrupo

RUBRICA_YAML = """
rubrica:
  nombre: R
  escala: {tope_por_critico: 6}
  secciones:
    - artefacto: presentacion
      criterios:
        - {id: PRE-1, descripcion: d, peso: 1, niveles: {Insuficiente: a, Regular: b, Bueno: c, Excelente: e}}
    - artefacto: srs
      criterios:
        - {id: SRS-1, descripcion: d, peso: 1, niveles: {Insuficiente: a, Regular: b, Bueno: c, Excelente: e}}
    - artefacto: fd
      criterios:
        - {id: FD-1, descripcion: d, peso: 1, niveles: {Insuficiente: a, Regular: b, Bueno: c, Excelente: e}}
    - artefacto: ui
      criterios:
        - {id: UI-NOM, descripcion: Nomenclatura, peso: 1, niveles: {Insuficiente: a, Regular: b, Bueno: c, Excelente: e}}
"""

UI_XML = '<ui version="4.0"><widget class="QWidget" name="F">' \
         '<widget class="QPushButton" name="btnOk"/></widget></ui>'


def test_flujo_completo_por_grupo(qtbot, tmp_path):
    c = crear_ciclo(tmp_path / "c", "AED II — 2027")

    # Config: rúbrica cargada
    rub = tmp_path / "rubrica.yaml"; rub.write_text(RUBRICA_YAML, encoding="utf-8")
    rubrica = configurar.cargar_rubrica(c, rub)

    # Alta de grupo
    gid = gestion.alta_grupo(c, "G01", "Grupo Uno", "Proyecto", integrantes=["Ana"])
    grupo = c.grupos.obtener(gid)

    ventana = VentanaGrupo(c, grupo, rubrica)
    qtbot.addWidget(ventana)

    # Etapa 1: cargar entrega (un .ui)
    ui = tmp_path / "form.ui"; ui.write_text(UI_XML, encoding="utf-8")
    ventana.vista_entrega.agregar_archivo(ui)
    entrega = ventana.vista_entrega.cargar()
    assert entrega.version == 1

    # Etapa 2: analizar (conector falso)
    resp_ui = json.dumps({"artefacto": "ui", "valoraciones": [
        {"criterio_id": "UI-NOM", "nivel": "Bueno", "justificacion": "x"}], "observaciones": [
        {"criterio_id": "UI-NOM", "tipo": "mejora", "contenido": "renombrar btnOk",
         "referencia": {"ubicacion": "btnOk"}}]})
    trans = json.dumps({"consistencias": [], "senales": [], "preguntas_defensa": [
        {"pregunta": "¿por qué?", "elemento": "btnOk", "artefacto": "ui", "intencion": "x"}]})
    conector = ConectorFalso([resp_ui, trans], dormir=lambda s: None, reloj=lambda: "t")

    ev_id = ventana.ejecutar_analisis(conector)
    assert ev_id is not None
    assert ventana.btn_revisar.isEnabled()
    assert ventana.btn_exportar.isEnabled()

    # Etapa 3: revisar (aceptar todo, fijar nota, validar)
    for e in c.elementos.de_evaluacion(ev_id):
        revision.aceptar(c, e["id"])
    revision.fijar_nota_final(c, ev_id, 8, "2027-04-13")
    revision.validar(c, entrega.id, ev_id)

    # Etapa 4: exportar (si WeasyPrint está disponible)
    if pytest.importorskip("weasyprint", reason="sin motor PDF"):
        informe, guia = ventana.exportar()
        assert informe.exists() and guia.exists()
        assert informe.parent.name == "informes"
    c.cerrar()


def test_flujo_requiere_entrega_para_analizar(qtbot, tmp_path):
    c = crear_ciclo(tmp_path / "c", "ciclo")
    rub = tmp_path / "r.yaml"; rub.write_text(RUBRICA_YAML, encoding="utf-8")
    rubrica = configurar.cargar_rubrica(c, rub)
    gid = gestion.alta_grupo(c, "G01", "N", "P")
    grupo = c.grupos.obtener(gid)
    ventana = VentanaGrupo(c, grupo, rubrica)
    qtbot.addWidget(ventana)

    conector = ConectorFalso([], dormir=lambda s: None, reloj=lambda: "t")
    with pytest.raises(ValueError):
        ventana.ejecutar_analisis(conector)  # no hay entrega vigente
    c.cerrar()
