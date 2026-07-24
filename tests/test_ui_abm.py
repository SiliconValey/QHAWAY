"""Tests de humo (pytest-qt, offscreen) de las vistas de ABM."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")
pytest.importorskip("pytestqt")

from qhaway.infra import crear_ciclo
from qhaway.ui.app import crear_ventana
from qhaway.ui.ciclo import VistaCiclo
from qhaway.ui.configuracion import VistaConfiguracion
from qhaway.ui.entrega import VistaEntrega


def _ciclo(tmp_path):
    return crear_ciclo(tmp_path / "c", "AED II — 2027")


def test_vista_ciclo_alta_y_archivo(qtbot, tmp_path):
    c = _ciclo(tmp_path)
    vista = VistaCiclo(c)
    qtbot.addWidget(vista)

    gid = vista.alta_grupo("G01", "Los Punteros", "EstaciónAR", integrantes=["Ana"])
    assert vista.tabla.rowCount() == 1
    assert vista.tabla.item(0, 0).text() == "G01"

    vista.agregar_integrante(gid, "Beto")
    # La columna integrantes (3) muestra a ambos
    assert "Beto" in vista.tabla.item(0, 3).text()

    vista.archivar_grupo(gid)
    assert vista.tabla.rowCount() == 0  # archivado no aparece
    c.cerrar()


def test_vista_entrega_carga(qtbot, tmp_path):
    c = _ciclo(tmp_path)
    gid = c.grupos.crear(c.ciclo_id, "G01", "N", "P")
    grupo = c.grupos.obtener(gid)
    vista = VistaEntrega(c, grupo, 1)
    qtbot.addWidget(vista)

    ui = tmp_path / "form.ui"
    ui.write_text('<ui version="4.0"><widget class="QWidget" name="F"/></ui>', encoding="utf-8")
    vista.agregar_archivo(ui)          # auto-clasifica .ui -> ui
    assert vista.tabla.rowCount() == 1

    entrega = vista.cargar()
    assert entrega.version == 1
    assert len(c.archivos.de_entrega(entrega.id)) == 1
    c.cerrar()


def test_vista_configuracion_rubrica(qtbot, tmp_path):
    c = _ciclo(tmp_path)
    vista = VistaConfiguracion(c)
    qtbot.addWidget(vista)

    rub = tmp_path / "r.yaml"
    rub.write_text("""
rubrica:
  nombre: R
  escala: {tope_por_critico: 6}
  secciones:
    - artefacto: presentacion
      criterios: [{id: P, descripcion: d, peso: 1, niveles: {Insuficiente: a, Regular: b, Bueno: c, Excelente: e}}]
    - artefacto: srs
      criterios: [{id: S, descripcion: d, peso: 1, niveles: {Insuficiente: a, Regular: b, Bueno: c, Excelente: e}}]
    - artefacto: fd
      criterios: [{id: F, descripcion: d, peso: 1, niveles: {Insuficiente: a, Regular: b, Bueno: c, Excelente: e}}]
    - artefacto: ui
      criterios: [{id: U, descripcion: d, peso: 1, niveles: {Insuficiente: a, Regular: b, Bueno: c, Excelente: e}}]
""", encoding="utf-8")
    vista.cargar_rubrica(rub)
    assert vista.rubrica is not None
    assert "✓" in vista.lbl_rubrica.text()

    vista.in_nombre.setText("AED II — 2028")
    vista.guardar_parametros()
    assert c.ciclos.obtener(c.ciclo_id).nombre == "AED II — 2028"
    c.cerrar()


def test_ventana_principal_se_construye(qtbot, tmp_path):
    c = _ciclo(tmp_path)
    ventana = crear_ventana(c)
    qtbot.addWidget(ventana)
    # Tres pestañas: Grupos, Configuración, Consumo
    tabs = ventana.centralWidget()
    assert tabs.count() == 6  # Grupos, Configuración, Evaluados, Consumo, Ayuda, Acerca de
    c.cerrar()


def test_vistas_ayuda_y_acerca_de(qtbot):
    """La ayuda describe el flujo y el Acerca de lleva versión y licencia."""
    from qhaway.ui.ayuda import VistaAcercaDe, VistaAyuda
    from qhaway.version import __version__

    ayuda = VistaAyuda()
    qtbot.addWidget(ayuda)
    texto = ayuda.texto.toPlainText()
    # Cubre las etapas del flujo real
    for hito in ("Configuración", "Alta de grupo", "Analizar", "Validar", "Exportar"):
        assert hito in texto
    # Advierte sobre lo que más importa al cargar (lección de uso real)
    assert "Tipo" in texto

    acerca = VistaAcercaDe()
    qtbot.addWidget(acerca)
    t2 = acerca.texto.toPlainText()
    assert __version__ in t2
    assert "MIT" in t2
    assert "nunca se envían" in t2   # política de datos visible


def test_titulo_ventana_incluye_version():
    from qhaway.version import __version__, titulo_ventana
    t = titulo_ventana("AED II — 2027")
    assert __version__ in t and "AED II" in t
    assert titulo_ventana() == f"QHAWAY {__version__}"
