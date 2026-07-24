"""Tests de los servicios de ABM (gestión, carga de entrega, configuración)."""

from __future__ import annotations

import pytest

from qhaway.dominio.rubrica import RubricaInvalida
from qhaway.infra import crear_ciclo
from qhaway.servicios import cargar_entrega, configurar, gestion
from qhaway.servicios.cargar_entrega import ArchivoACargar


def _ciclo(tmp_path):
    return crear_ciclo(tmp_path / "c", "AED II — 2027")


# --- Gestión de grupos --------------------------------------------------------
def test_alta_grupo_con_integrantes(tmp_path):
    c = _ciclo(tmp_path)
    gid = gestion.alta_grupo(c, "G01", "Los Punteros", "EstaciónAR",
                             integrantes=["Ana", "Beto"], fecha="2027-03-01")
    assert gestion.composicion(c, gid, "2027-03-15") == ["Ana", "Beto"]
    assert len(gestion.listar_grupos(c)) == 1
    c.cerrar()


def test_baja_integrante_y_archivado(tmp_path):
    c = _ciclo(tmp_path)
    gid = gestion.alta_grupo(c, "G01", "N", "P", integrantes=["Ana"], fecha="2027-03-01")
    iid = gestion.agregar_integrante(c, gid, "Beto", fecha="2027-03-01")
    gestion.baja_integrante(c, iid, fecha="2027-04-01")
    assert gestion.composicion(c, gid, "2027-04-15") == ["Ana"]

    gestion.archivar_grupo(c, gid)
    assert gestion.listar_grupos(c) == []
    assert len(gestion.listar_grupos(c, incluir_archivados=True)) == 1
    c.cerrar()


# --- Carga de entrega ---------------------------------------------------------
def test_cargar_entrega_copia_y_registra(tmp_path):
    c = _ciclo(tmp_path)
    gid = gestion.alta_grupo(c, "G01", "N", "P")
    grupo = c.grupos.obtener(gid)

    # Archivos fuente
    ui = tmp_path / "form.ui"
    ui.write_text('<ui version="4.0"><widget class="QWidget" name="F"/></ui>', encoding="utf-8")

    entrega = cargar_entrega.cargar_entrega(
        c, grupo, 1, [ArchivoACargar(ui, "ui")], fecha="2027-04-10"
    )
    assert entrega.version == 1
    # El archivo se copió a la carpeta de la versión
    archivos = c.archivos.de_entrega(entrega.id)
    assert len(archivos) == 1
    assert c.rutas.absoluta(archivos[0]["ruta_relativa"]).exists()
    c.cerrar()


def test_cargar_entrega_rechaza_formato(tmp_path):
    c = _ciclo(tmp_path)
    gid = gestion.alta_grupo(c, "G01", "N", "P")
    grupo = c.grupos.obtener(gid)
    txt = tmp_path / "notas.txt"
    txt.write_text("x", encoding="utf-8")
    with pytest.raises(ValueError):
        cargar_entrega.cargar_entrega(c, grupo, 1, [ArchivoACargar(txt, "srs")])
    c.cerrar()


def test_reentrega_incrementa_version(tmp_path):
    c = _ciclo(tmp_path)
    gid = gestion.alta_grupo(c, "G01", "N", "P")
    grupo = c.grupos.obtener(gid)
    ui = tmp_path / "form.ui"
    ui.write_text('<ui version="4.0"><widget class="QWidget" name="F"/></ui>', encoding="utf-8")
    e1 = cargar_entrega.cargar_entrega(c, grupo, 1, [ArchivoACargar(ui, "ui")])
    e2 = cargar_entrega.cargar_entrega(c, grupo, 1, [ArchivoACargar(ui, "ui")])
    assert (e1.version, e2.version) == (1, 2)
    c.cerrar()


# --- Configuración ------------------------------------------------------------
def test_cargar_rubrica_valida(tmp_path):
    c = _ciclo(tmp_path)
    rub = tmp_path / "rubrica.yaml"
    rub.write_text("""
rubrica:
  nombre: Prueba
  escala: {tope_por_critico: 6}
  secciones:
    - artefacto: presentacion
      criterios: [{id: P1, descripcion: d, peso: 1, niveles: {Insuficiente: a, Regular: b, Bueno: c, Excelente: d}}]
    - artefacto: srs
      criterios: [{id: S1, descripcion: d, peso: 1, niveles: {Insuficiente: a, Regular: b, Bueno: c, Excelente: d}}]
    - artefacto: fd
      criterios: [{id: F1, descripcion: d, peso: 1, niveles: {Insuficiente: a, Regular: b, Bueno: c, Excelente: d}}]
    - artefacto: ui
      criterios: [{id: U1, descripcion: d, peso: 1, niveles: {Insuficiente: a, Regular: b, Bueno: c, Excelente: d}}]
""", encoding="utf-8")
    rubrica = configurar.cargar_rubrica(c, rub)
    assert rubrica.nombre == "Prueba"
    assert (c.rutas.config() / "rubrica.yaml").exists()
    c.cerrar()


def test_cargar_rubrica_invalida_no_copia(tmp_path):
    c = _ciclo(tmp_path)
    rub = tmp_path / "mala.yaml"
    rub.write_text("rubrica: {nombre: X, escala: {tope_por_critico: 99}, secciones: []}",
                   encoding="utf-8")
    with pytest.raises(RubricaInvalida):
        configurar.cargar_rubrica(c, rub)
    assert not (c.rutas.config() / "rubrica.yaml").exists()  # no se copió
    c.cerrar()


def test_actualizar_parametros_ciclo(tmp_path):
    c = _ciclo(tmp_path)
    configurar.actualizar_parametros(c, nombre="AED II — 2028", cantidad_preguntas=8)
    ciclo_row = c.ciclos.obtener(c.ciclo_id)
    assert ciclo_row.nombre == "AED II — 2028"
    assert ciclo_row.cantidad_preguntas == 8

    with pytest.raises(ValueError):
        configurar.actualizar_parametros(c, cantidad_preguntas=0)  # mínimo 1
    c.cerrar()


def test_cargar_entrega_rechaza_tipos_duplicados(tmp_path):
    import pytest as _pytest
    from qhaway.servicios.cargar_entrega import TipoDuplicado, detectar_tipos_duplicados
    c = _ciclo(tmp_path)
    gid = gestion.alta_grupo(c, "G01", "N", "P")
    grupo = c.grupos.obtener(gid)

    # Dos PDF marcados ambos como 'srs'
    a = tmp_path / "ers.pdf"; a.write_bytes(b"%PDF-1.4 fake")
    b = tmp_path / "brochure.pdf"; b.write_bytes(b"%PDF-1.4 fake")
    archivos = [ArchivoACargar(a, "srs"), ArchivoACargar(b, "srs")]

    # La detección los reporta
    dup = detectar_tipos_duplicados(archivos)
    assert dup == {"srs": ["ers.pdf", "brochure.pdf"]}

    # cargar_entrega los rechaza y NO crea ninguna versión
    with _pytest.raises(TipoDuplicado):
        cargar_entrega.cargar_entrega(c, grupo, 1, archivos)
    assert c.con.execute("SELECT COUNT(*) AS n FROM entrega").fetchone()["n"] == 0
    c.cerrar()


def test_cargar_entrega_tipos_distintos_ok(tmp_path):
    c = _ciclo(tmp_path)
    gid = gestion.alta_grupo(c, "G01", "N", "P")
    grupo = c.grupos.obtener(gid)
    ers = tmp_path / "ers.pdf"; ers.write_bytes(b"%PDF-1.4 fake")
    fd = tmp_path / "fd.pdf"; fd.write_bytes(b"%PDF-1.4 fake")
    entrega = cargar_entrega.cargar_entrega(
        c, grupo, 1, [ArchivoACargar(ers, "srs"), ArchivoACargar(fd, "fd")])
    assert len(c.archivos.de_entrega(entrega.id)) == 2
    c.cerrar()


def test_clasificacion_por_contenido():
    from qhaway.dominio.clasificacion import clasificar_texto
    srs = clasificar_texto("Especificación de requisitos. RF-01 el sistema deberá... "
                           "Requerimientos no funcionales RNF-01. Criterios de aceptación.")
    assert srs.tipo_sugerido == "srs"
    fd = clasificar_texto("Diseño funcional. La pantalla principal. Máquina de estados. "
                          "objectName btnGuardar QPushButton. Comportamiento de cada control.")
    assert fd.tipo_sugerido == "fd"
    pres = clasificar_texto("Quiénes somos. Nuestra misión y visión. A qué nos dedicamos. "
                           "Nuestros servicios. Contacto.")
    assert pres.tipo_sugerido == "presentacion"
    # Texto sin señales -> no arriesga sugerencia
    vacio = clasificar_texto("Hola, este es un texto cualquiera sin estructura.")
    assert vacio.tipo_sugerido is None
