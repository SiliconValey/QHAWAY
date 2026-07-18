"""Tests de exportación (EXP-01..04)."""

from __future__ import annotations

import pytest

from qhaway.dominio.estados import EstadoEvaluacion as E
from qhaway.dominio.niveles import Nivel
from qhaway.dominio.rubrica import Rubrica
from qhaway.infra import crear_ciclo
from qhaway.infra.informes import renderizar_guia_defensa, renderizar_informe_grupo
from qhaway.servicios import exportar, revision


def _rubrica():
    niveles = {n.value: "..." for n in Nivel}
    return Rubrica.desde_dict({"rubrica": {"nombre": "R", "escala": {"tope_por_critico": 6},
        "secciones": [{"artefacto": "srs", "criterios": [
            {"id": "SRS-REQ", "descripcion": "d", "peso": 1, "niveles": niveles}]}]}},
        artefactos_requeridos=frozenset())


def _evaluacion_validada(tmp_path):
    """Ciclo con una evaluación validada: obs aceptada, pregunta, señal, hallazgo DET."""
    c = crear_ciclo(tmp_path / "c", "ciclo")
    gid = c.grupos.crear(c.ciclo_id, "G03", "Los Andinos", "Distribuidora Andes")
    grupo = c.grupos.obtener(gid)
    entrega = c.entregas.crear_version(gid, 1, "2027-04-10", E.ENTREGA_CARGADA.value)
    for destino in (E.ANALIZANDO, E.BORRADOR_EN_REVISION):
        c.transicionar_entrega(entrega.id, destino)
    ev_id = c.evaluaciones.crear(entrega.id, E.BORRADOR_EN_REVISION.value)
    c.valoraciones.registrar(ev_id, "SRS-REQ", Nivel.BUENO.value, None)

    # Hallazgo DET, observación de artefacto, consistencia, pregunta, señal
    c.hallazgos.registrar(ev_id, "bloque_ausente", "srs", "Falta sección Referencias")
    obs = c.elementos.crear(ev_id, "observacion", criterio_id="SRS-REQ",
                            contenido_original="RF-06 sin estructura tarifaria",
                            referencia="3 Requerimientos")
    cons = c.elementos.crear(ev_id, "observacion", contenido_original="RF-03 no está en el FD",
                             referencia="RF-03")
    preg = c.elementos.crear(ev_id, "pregunta_defensa",
                             contenido_original="¿Por qué RF-03 no tiene pantalla?",
                             referencia="RF-03")
    sen = c.elementos.crear(ev_id, "senal", contenido_original="salto de sofisticación en el FD")

    for e in (obs, cons, preg, sen):
        revision.aceptar(c, e)
    revision.fijar_nota_final(c, ev_id, 8, "2027-04-13")
    revision.validar(c, entrega.id, ev_id)
    return c, grupo, entrega, ev_id


def test_guard_no_exporta_sin_validar(tmp_path):
    c = crear_ciclo(tmp_path / "c", "ciclo")
    gid = c.grupos.crear(c.ciclo_id, "G01", "N", "P")
    grupo = c.grupos.obtener(gid)
    entrega = c.entregas.crear_version(gid, 1, "2027-04-10", E.ENTREGA_CARGADA.value)
    ev_id = c.evaluaciones.crear(entrega.id, E.BORRADOR_EN_REVISION.value)
    with pytest.raises(exportar.NoValidada):
        exportar.exportar_informe_grupo(c, grupo, entrega, ev_id, _rubrica())
    c.cerrar()


def test_informe_grupo_html_excluye_señales_preguntas_origen(tmp_path):
    c, grupo, entrega, ev_id = _evaluacion_validada(tmp_path)
    ctx = exportar._contexto_grupo(c, grupo, entrega, ev_id, _rubrica(), "2027-04-13")
    html = renderizar_informe_grupo(ctx)

    # SÍ están: nota, observación de artefacto, hallazgo DET, consistencia
    assert "8" in html
    assert "RF-06 sin estructura tarifaria" in html
    assert "Falta sección Referencias" in html
    assert "RF-03 no está en el FD" in html
    # NO están: pregunta de defensa, señal, marca de origen (EXP-01, REV-05)
    assert "¿Por qué RF-03 no tiene pantalla?" not in html
    assert "salto de sofisticación" not in html
    assert "ia_aceptado" not in html and "origen" not in html.lower()
    c.cerrar()


def test_guia_defensa_incluye_preguntas_y_señales(tmp_path):
    c, grupo, entrega, ev_id = _evaluacion_validada(tmp_path)
    elementos = c.elementos.de_evaluacion(ev_id)
    preguntas = [{"contenido": e["contenido_original"], "referencia": e["referencia"]}
                 for e in elementos if e["tipo"] == "pregunta_defensa"]
    senales = [{"contenido": e["contenido_original"]}
               for e in elementos if e["tipo"] == "senal"]
    html = renderizar_guia_defensa({
        "grupo": grupo.codigo, "proyecto": grupo.proyecto, "exposicion": 1,
        "preguntas": preguntas, "senales": senales,
    })
    assert "¿Por qué RF-03 no tiene pantalla?" in html
    assert "salto de sofisticación" in html
    c.cerrar()


def test_descartado_no_aparece_en_informe(tmp_path):
    c, grupo, entrega, ev_id = _evaluacion_validada(tmp_path)
    # Agregar una observación descartada NO debe salir (pero requiere re-validar;
    # acá comprobamos el filtro directamente sobre el contexto).
    did = c.elementos.crear(ev_id, "observacion", criterio_id="SRS-REQ",
                            contenido_original="observación descartada")
    revision.descartar(c, did)
    ctx = exportar._contexto_grupo(c, grupo, entrega, ev_id, _rubrica(), "")
    html = renderizar_informe_grupo(ctx)
    assert "observación descartada" not in html
    c.cerrar()


def test_pdf_real_se_genera_y_archiva(tmp_path):
    pytest.importorskip("weasyprint")
    c, grupo, entrega, ev_id = _evaluacion_validada(tmp_path)

    ruta_informe = exportar.exportar_informe_grupo(c, grupo, entrega, ev_id, _rubrica(),
                                                   fecha="2027-04-13")
    ruta_guia = exportar.exportar_guia_defensa(c, grupo, entrega, ev_id)

    # Se generaron PDFs no vacíos
    assert ruta_informe.exists() and ruta_informe.stat().st_size > 1000
    assert ruta_guia.exists() and ruta_guia.stat().st_size > 1000
    # Archivados en la carpeta informes/ de la versión (EXP-04)
    assert ruta_informe.parent.name == "informes"
    assert ruta_informe.read_bytes()[:4] == b"%PDF"
    c.cerrar()
