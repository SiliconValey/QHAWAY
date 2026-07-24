"""Tests de las plantillas de prompts (AD-07, EVA-03/04/08/09, EVA-12)."""

from __future__ import annotations

import pytest

from qhaway.infra.prompts import PLANTILLAS, VariableFaltante


def _ctx_artefacto():
    return {
        "artefacto": "srs",
        "criterios": [{"id": "SRS-REQ", "descripcion": "Requisitos",
                       "niveles": {"Bueno": "bien"}}],
        "modelo": "TEXTO DEL MODELO",
        "hallazgos_det": [{"tipo": "bloque_ausente", "detalle": "falta X"}],
        "entrega": "TEXTO DE LA ENTREGA DEL GRUPO",
    }


def test_contrato_variable_faltante_falla():
    ctx = _ctx_artefacto()
    del ctx["modelo"]
    with pytest.raises(VariableFaltante):
        PLANTILLAS["analisis_artefacto"].render(ctx)


def test_artefacto_incluye_instrucciones_de_comportamiento():
    texto = PLANTILLAS["analisis_artefacto"].render(_ctx_artefacto()).texto
    # EVA-03 calibración-no-plantilla
    assert "NO una plantilla" in texto
    # EVA-04 hallazgos no contradecibles
    assert "NO los contradigas" in texto
    # EVA-01 referencias, sin inventar página
    assert "NUNCA la inventes" in texto
    # El modelo y la entrega viajan
    assert "TEXTO DEL MODELO" in texto
    assert "TEXTO DE LA ENTREGA DEL GRUPO" in texto


def test_orden_de_cacheo_estable_antes_que_variable():
    ensamblado = PLANTILLAS["analisis_artefacto"].render(_ctx_artefacto())
    flags = [b.cacheable for b in ensamblado.bloques]
    # Una vez que aparece un bloque no cacheable, no vuelve a haber cacheables:
    # lo estable va primero, lo variable al final (EVA-12).
    primer_variable = flags.index(False)
    assert all(not f for f in flags[primer_variable:])


def test_esqueleto_fuerza_las_valoraciones():
    ensamblado = PLANTILLAS["analisis_artefacto"].render(_ctx_artefacto())
    # El último bloque es el esqueleto JSON con el criterio ya adentro.
    ultimo = ensamblado.bloques[-1].texto
    assert "SRS-REQ" in ultimo            # el criterio viene pre-cargado
    assert '"nivel": "___"' in ultimo     # slot a completar
    assert "TAREA PRINCIPAL" in ultimo


def test_bloques_cacheables_incluyen_rubrica_y_modelo():
    ensamblado = PLANTILLAS["analisis_artefacto"].render(_ctx_artefacto())
    cacheables = "\n".join(ensamblado.bloques_cacheables())
    assert "SRS-REQ" in cacheables         # la rúbrica es estable
    assert "TEXTO DEL MODELO" in cacheables  # el modelo es estable
    assert "ENTREGA DEL GRUPO" not in cacheables  # la entrega no


def test_transversal_incluye_reglas_eva08_eva09():
    texto = PLANTILLAS["analisis_transversal"].render({
        "entrega": {"srs": "texto srs", "ui": "texto ui"},
        "cantidad_preguntas": 10,
    }).texto
    assert "elemento NOMBRADO" in texto     # EVA-08
    assert "SUGERENCIA" in texto            # EVA-09
    assert "10 preguntas" in texto          # cantidad configurable


def test_plantillas_tienen_version():
    assert PLANTILLAS["analisis_artefacto"].version
    assert PLANTILLAS["analisis_transversal"].version
