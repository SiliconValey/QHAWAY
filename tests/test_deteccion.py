"""Tests de DET puro (DET-02/03/04/05), con estructuras literales."""

from __future__ import annotations

from qhaway.dominio.contenido import ArbolUI, ContenidoDocumento, NodoUI, Seccion
from qhaway.dominio.deteccion import (
    Bloque,
    ChecklistDocumento,
    ConvencionNomenclatura,
    ejecutar_det_ui,
    verificar_completitud,
    verificar_elementos_formales,
    verificar_nomenclatura,
)


def _doc(secciones, texto="", **kw):
    return ContenidoDocumento(
        tipo_artefacto="srs",
        texto=texto or " ".join(s.titulo + " " + s.texto for s in secciones),
        secciones=tuple(secciones),
        **kw,
    )


# --- DET-02 Completitud -------------------------------------------------------
def test_completitud_bloque_presente_por_titulo():
    checklist = ChecklistDocumento(
        "srs", bloques=(Bloque("rf", ("requerimientos funcionales",)),)
    )
    doc = _doc([Seccion("3", "Requerimientos Funcionales", 3)])
    assert verificar_completitud(doc, checklist) == []


def test_completitud_matchea_por_sinonimo_no_por_titulo_exacto():
    # Lección Etapa 0.2: "Definiciones y siglas" vs "Definiciones y acrónimos".
    checklist = ChecklistDocumento(
        "srs", bloques=(Bloque("def", ("definiciones", "acronimos", "siglas")),)
    )
    doc_a = _doc([Seccion("2", "Definiciones y siglas", 2)])
    doc_b = _doc([Seccion("2", "Definiciones y Acrónimos", 2)])
    assert verificar_completitud(doc_a, checklist) == []
    assert verificar_completitud(doc_b, checklist) == []


def test_completitud_bloque_ausente_se_reporta():
    checklist = ChecklistDocumento(
        "srs", bloques=(Bloque("referencias", ("referencias", "bibliografia")),)
    )
    doc = _doc([Seccion("1", "Introducción", 1)])
    hallazgos = verificar_completitud(doc, checklist)
    assert len(hallazgos) == 1
    assert hallazgos[0].tipo == "bloque_ausente"
    assert hallazgos[0].datos["bloque"] == "referencias"
    assert hallazgos[0].categoria == "deterministico"


def test_completitud_respaldo_en_texto_completo():
    # No es un título, pero la palabra aparece en el cuerpo -> presente.
    checklist = ChecklistDocumento("srs", bloques=(Bloque("rest", ("restricciones",)),))
    doc = _doc(
        [Seccion("1", "Introducción", 1, "Se detallan las restricciones del sistema")],
    )
    assert verificar_completitud(doc, checklist) == []


# --- DET-03 Elementos formales ------------------------------------------------
def test_caratula_ausente():
    checklist = ChecklistDocumento("srs", requiere_caratula=True)
    doc = _doc([Seccion("1", "Introducción", 1)], texto_primera_pagina="Introducción al sistema")
    h = verificar_elementos_formales(doc, checklist)
    assert any(x.datos.get("elemento") == "caratula" for x in h)


def test_caratula_presente_no_reporta():
    checklist = ChecklistDocumento("srs", requiere_caratula=True)
    doc = _doc(
        [Seccion("1", "Introducción", 2)],
        texto_primera_pagina="Instituto Superior — Integrantes: Ana, Beto — Profesor: X",
    )
    assert verificar_elementos_formales(doc, checklist) == []


def test_secciones_numeradas_ausentes():
    checklist = ChecklistDocumento("srs", requiere_secciones_numeradas=True)
    doc = _doc([Seccion(None, "Introducción", 1)])  # sin número
    h = verificar_elementos_formales(doc, checklist)
    assert any(x.datos.get("elemento") == "secciones_numeradas" for x in h)


def test_indice_presente_por_seccion():
    checklist = ChecklistDocumento("srs", requiere_indice=True)
    doc = _doc([Seccion(None, "Índice", 2), Seccion("1", "Introducción", 3)])
    assert verificar_elementos_formales(doc, checklist) == []


# --- DET-04 Nomenclatura ------------------------------------------------------
def _convencion():
    return ConvencionNomenclatura(prefijos={"QPushButton": "btn", "QLineEdit": "txt"})


def test_nomenclatura_conforme_no_reporta():
    arbol = ArbolUI("ui", NodoUI("QWidget", "form", (
        NodoUI("QPushButton", "btnGuardar"),
        NodoUI("QLineEdit", "txtNombre"),
    )))
    assert verificar_nomenclatura(arbol, _convencion()) == []


def test_nomenclatura_no_conforme_reporta_datos():
    arbol = ArbolUI("ui", NodoUI("QWidget", "form", (
        NodoUI("QPushButton", "guardar"),  # falta prefijo btn
    )))
    h = verificar_nomenclatura(arbol, _convencion())
    assert len(h) == 1
    assert h[0].tipo == "nomenclatura_no_conforme"
    assert h[0].datos == {
        "nombre_actual": "guardar",
        "tipo_widget": "QPushButton",
        "prefijo_esperado": "btn",
    }
    assert h[0].referencia.objeto == "guardar"


def test_nomenclatura_ignora_clases_estructurales():
    # El QWidget raíz y los layouts no se juzgan.
    arbol = ArbolUI("ui", NodoUI("QWidget", "form", (
        NodoUI("QVBoxLayout", "layout", (NodoUI("QPushButton", "btnOk"),)),
    )))
    assert verificar_nomenclatura(arbol, _convencion()) == []


def test_nomenclatura_clase_sin_convencion_no_se_juzga():
    arbol = ArbolUI("ui", NodoUI("QWidget", "form", (
        NodoUI("QCalendarWidget", "cualquierNombre"),  # sin prefijo definido
    )))
    assert verificar_nomenclatura(arbol, _convencion()) == []


# --- DET-05 Reproducibilidad --------------------------------------------------
def test_reproducibilidad_mismo_reporte():
    arbol = ArbolUI("ui", NodoUI("QWidget", "form", (
        NodoUI("QPushButton", "guardar"),
        NodoUI("QLineEdit", "nombre"),
    )))
    r1 = ejecutar_det_ui(arbol, _convencion())
    r2 = ejecutar_det_ui(arbol, _convencion())
    # Mismo orden, mismo contenido: reproducible (DET-05).
    assert [h.datos for h in r1] == [h.datos for h in r2]
    assert len(r1) == 2
    assert [h.datos["nombre_actual"] for h in r1] == ["guardar", "nombre"]
