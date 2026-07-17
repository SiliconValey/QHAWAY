"""Tests de la máquina de estados de la evaluación (GRP-06, EXP-03)."""

from __future__ import annotations

import pytest

from qhaway.dominio import (
    EstadoEvaluacion as E,
    Evaluacion,
    TransicionInvalida,
    puede_transicionar,
    transicionar,
)


def test_camino_feliz_completo():
    ev = Evaluacion()  # arranca en sin_entrega
    assert ev.estado is E.SIN_ENTREGA
    ev.a(E.ENTREGA_CARGADA)
    ev.a(E.ANALIZANDO)
    ev.a(E.BORRADOR_EN_REVISION)
    ev.a(E.EVALUACION_VALIDADA, elementos_pendientes=0, nota_final_confirmada=True)
    ev.a(E.INFORME_EXPORTADO)
    assert ev.estado is E.INFORME_EXPORTADO


def test_interrupcion_y_reanudacion():
    assert puede_transicionar(E.ANALIZANDO, E.ANALISIS_INTERRUMPIDO)
    assert puede_transicionar(E.ANALISIS_INTERRUMPIDO, E.ANALIZANDO)
    # ida y vuelta
    s = transicionar(E.ANALIZANDO, E.ANALISIS_INTERRUMPIDO)
    s = transicionar(s, E.ANALIZANDO)
    assert s is E.ANALIZANDO


def test_transicion_ilegal_levanta_error():
    with pytest.raises(TransicionInvalida):
        transicionar(E.SIN_ENTREGA, E.ANALIZANDO)  # saltea entrega_cargada


def test_no_se_puede_validar_con_pendientes():
    with pytest.raises(TransicionInvalida) as exc:
        transicionar(
            E.BORRADOR_EN_REVISION,
            E.EVALUACION_VALIDADA,
            elementos_pendientes=3,
            nota_final_confirmada=True,
        )
    assert "pendiente" in str(exc.value)


def test_no_se_puede_validar_sin_confirmar_nota():
    with pytest.raises(TransicionInvalida):
        transicionar(
            E.BORRADOR_EN_REVISION,
            E.EVALUACION_VALIDADA,
            elementos_pendientes=0,
            nota_final_confirmada=False,
        )


def test_validar_sin_pasar_guards_es_error():
    # Si no se informan los guards, no se puede validar (EXP-03).
    with pytest.raises(TransicionInvalida):
        transicionar(E.BORRADOR_EN_REVISION, E.EVALUACION_VALIDADA)


def test_informe_exportado_es_terminal():
    with pytest.raises(TransicionInvalida):
        transicionar(E.INFORME_EXPORTADO, E.ANALIZANDO)
