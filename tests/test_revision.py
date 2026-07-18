"""Tests de los servicios de revisión y monitoreo (sin Qt)."""

from __future__ import annotations

import pytest

from qhaway.dominio.estados import EstadoEvaluacion as E, TransicionInvalida
from qhaway.dominio.niveles import Nivel
from qhaway.dominio.rubrica import Rubrica
from qhaway.infra import crear_ciclo
from qhaway.servicios import monitor, revision


def _rubrica():
    niveles = {n.value: "..." for n in Nivel}
    return Rubrica.desde_dict({"rubrica": {"nombre": "R", "escala": {"tope_por_critico": 6},
        "secciones": [{"artefacto": "srs", "criterios": [
            {"id": "SRS-REQ", "descripcion": "d", "peso": 1, "niveles": niveles}]}]}},
        artefactos_requeridos=frozenset())


def _evaluacion_en_revision(tmp_path):
    """Ciclo con una evaluación en borrador_en_revision, con elementos y valoración."""
    c = crear_ciclo(tmp_path / "c", "ciclo")
    gid = c.grupos.crear(c.ciclo_id, "G01", "N", "P")
    entrega = c.entregas.crear_version(gid, 1, "2027-04-10", E.ENTREGA_CARGADA.value)
    # Llevar la entrega hasta borrador_en_revision por la máquina de estados
    for destino in (E.ANALIZANDO, E.BORRADOR_EN_REVISION):
        c.transicionar_entrega(entrega.id, destino)
    ev_id = c.evaluaciones.crear(entrega.id, E.BORRADOR_EN_REVISION.value)
    c.valoraciones.registrar(ev_id, "SRS-REQ", Nivel.BUENO.value, None)
    c.evaluaciones.fijar_nota_sugerida(ev_id, 8)
    # Tres elementos pendientes
    e1 = c.elementos.crear(ev_id, "observacion", contenido_original="obs 1")
    e2 = c.elementos.crear(ev_id, "observacion", contenido_original="obs 2")
    e3 = c.elementos.crear(ev_id, "pregunta_defensa", contenido_original="¿por qué?")
    return c, entrega, ev_id, (e1, e2, e3)


def test_aceptar_editar_descartar(tmp_path):
    c, entrega, ev_id, (e1, e2, e3) = _evaluacion_en_revision(tmp_path)

    revision.aceptar(c, e1)
    revision.editar(c, e2, "observación corregida por el docente")
    revision.descartar(c, e3)

    el1 = c.elementos.obtener(e1)
    el2 = c.elementos.obtener(e2)
    el3 = c.elementos.obtener(e3)
    assert el1["estado_revision"] == "aceptado" and el1["origen"] == "ia_aceptado"
    assert el2["estado_revision"] == "editado" and el2["origen"] == "ia_editado"
    assert el2["contenido_final"] == "observación corregida por el docente"
    assert el3["estado_revision"] == "descartado"
    assert c.elementos.pendientes(ev_id) == 0  # los tres revisados
    c.cerrar()


def test_agregar_elemento_docente_nace_aceptado(tmp_path):
    c, entrega, ev_id, _ = _evaluacion_en_revision(tmp_path)
    nid = revision.agregar_elemento_docente(c, ev_id, "observacion", "observación propia")
    el = c.elementos.obtener(nid)
    assert el["origen"] == "docente"
    assert el["estado_revision"] == "aceptado"
    c.cerrar()


def test_ajustar_valoracion_recalcula_nota(tmp_path):
    c, entrega, ev_id, _ = _evaluacion_en_revision(tmp_path)
    # IA puso Bueno (nota 8). El docente lo baja a Regular (5).
    nueva = revision.ajustar_valoracion(c, ev_id, "SRS-REQ", Nivel.REGULAR, _rubrica())
    assert nueva == 5
    # Se conserva el nivel de la IA (REV-04)
    vals = c.valoraciones.de_evaluacion(ev_id)
    assert vals["SRS-REQ"]["nivel_ia"] == Nivel.BUENO.value
    assert vals["SRS-REQ"]["nivel_final"] == Nivel.REGULAR.value
    c.cerrar()


def test_no_se_puede_validar_con_pendientes(tmp_path):
    c, entrega, ev_id, _ = _evaluacion_en_revision(tmp_path)
    revision.fijar_nota_final(c, ev_id, 8, "2027-04-13")
    ok, motivo = revision.puede_validar(c, ev_id)
    assert not ok and "pendiente" in motivo
    # Y validar levanta (el guard de la máquina de estados, EXP-03)
    with pytest.raises(TransicionInvalida):
        revision.validar(c, entrega.id, ev_id)
    c.cerrar()


def test_validar_con_todo_listo(tmp_path):
    c, entrega, ev_id, (e1, e2, e3) = _evaluacion_en_revision(tmp_path)
    for e in (e1, e2, e3):
        revision.aceptar(c, e)
    revision.fijar_nota_final(c, ev_id, 7, "2027-04-13")

    ok, _ = revision.puede_validar(c, ev_id)
    assert ok
    revision.validar(c, entrega.id, ev_id)

    estado = c.con.execute(
        "SELECT estado FROM entrega WHERE id = ?", (entrega.id,)
    ).fetchone()["estado"]
    assert estado == E.EVALUACION_VALIDADA.value
    c.cerrar()


def test_metricas_retrabajo(tmp_path):
    c, entrega, ev_id, (e1, e2, e3) = _evaluacion_en_revision(tmp_path)
    revision.aceptar(c, e1)
    revision.editar(c, e2, "editada")
    revision.descartar(c, e3)
    revision.agregar_elemento_docente(c, ev_id, "observacion", "propia")

    m = revision.metricas_retrabajo(c, ev_id)
    assert m.total == 4
    assert m.aceptados_sin_cambios == 1
    assert m.editados == 1
    assert m.descartados == 1
    assert m.agregados_docente == 1
    c.cerrar()


def test_monitor_presupuesto_alerta(tmp_path):
    c = crear_ciclo(tmp_path / "c", "ciclo", presupuesto_mensual=20.0)
    # Registrar consumo del mes por USD 17 (85% -> alerta con umbral 80%)
    c.consumos.registrar(None, tokens_entrada=0, tokens_salida=0, tokens_cache=0,
                         costo_estimado=17.0, reintento=0, fecha="2027-04-15")
    est = monitor.estado_presupuesto(c, mes="2027-04")
    assert est.acumulado == 17.0
    assert est.alerta is True
    assert 0.84 < est.proporcion < 0.86
    c.cerrar()


def test_monitor_costo_por_evaluacion(tmp_path):
    c, entrega, ev_id, _ = _evaluacion_en_revision(tmp_path)
    aid = c.analisis.crear_unidad(ev_id, "srs", "2027-04-10")
    c.consumos.registrar(aid, tokens_entrada=100, tokens_salida=50, tokens_cache=0,
                         costo_estimado=0.5, reintento=0, fecha="2027-04-10")
    assert monitor.costo_evaluacion(c, ev_id) == 0.5
    c.cerrar()
