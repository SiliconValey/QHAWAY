"""Tests de validación de rúbrica (CFG-01, CFG-02).

Cada caso inválido enumerado en CFG-01 tiene su test.
"""

from __future__ import annotations

import pytest

from qhaway.dominio import Nivel, Rubrica, RubricaInvalida
from qhaway.dominio.rubrica import ARTEFACTOS_EXPO1

NIVELES_OK = {n.value: "descripcion" for n in Nivel}


def _criterio(cid="C1", peso=1, critico=False, niveles=None):
    return {
        "id": cid,
        "descripcion": "d",
        "peso": peso,
        "critico": critico,
        "niveles": NIVELES_OK if niveles is None else niveles,
    }


def _rubrica_completa_expo1():
    """Una rúbrica válida con las 4 secciones de artefacto de la Expo 1."""
    secciones = [
        {"artefacto": a, "criterios": [_criterio(cid=f"{a}-1")]}
        for a in sorted(ARTEFACTOS_EXPO1)
    ]
    return {
        "rubrica": {
            "nombre": "AED II — Expo 1",
            "escala": {"tope_por_critico": 6},
            "secciones": secciones,
        }
    }


def test_rubrica_valida_expo1_se_construye():
    r = Rubrica.desde_dict(_rubrica_completa_expo1())
    assert r.nombre == "AED II — Expo 1"
    assert r.tope_por_critico == 6
    assert len(r.criterios()) == 4


def test_peso_no_positivo_es_invalido():
    datos = _rubrica_completa_expo1()
    datos["rubrica"]["secciones"][0]["criterios"][0]["peso"] = 0
    with pytest.raises(RubricaInvalida) as exc:
        Rubrica.desde_dict(datos)
    assert any("peso" in p for p in exc.value.problemas)


def test_peso_no_numerico_es_invalido():
    datos = _rubrica_completa_expo1()
    datos["rubrica"]["secciones"][0]["criterios"][0]["peso"] = "alto"
    with pytest.raises(RubricaInvalida):
        Rubrica.desde_dict(datos)


def test_peso_booleano_no_cuenta_como_numerico():
    datos = _rubrica_completa_expo1()
    datos["rubrica"]["secciones"][0]["criterios"][0]["peso"] = True
    with pytest.raises(RubricaInvalida):
        Rubrica.desde_dict(datos)


def test_niveles_no_canonicos_es_invalido():
    datos = _rubrica_completa_expo1()
    datos["rubrica"]["secciones"][0]["criterios"][0]["niveles"] = {
        "Malo": "x",
        "Bueno": "y",
    }
    with pytest.raises(RubricaInvalida) as exc:
        Rubrica.desde_dict(datos)
    assert any("no canónicos" in p or "canónic" in p for p in exc.value.problemas)


def test_tope_fuera_de_rango_es_invalido():
    datos = _rubrica_completa_expo1()
    datos["rubrica"]["escala"]["tope_por_critico"] = 11
    with pytest.raises(RubricaInvalida) as exc:
        Rubrica.desde_dict(datos)
    assert any("tope_por_critico" in p for p in exc.value.problemas)


def test_artefacto_requerido_faltante_es_invalido():
    datos = _rubrica_completa_expo1()
    # Sacamos la sección 'ui'
    datos["rubrica"]["secciones"] = [
        s for s in datos["rubrica"]["secciones"] if s["artefacto"] != "ui"
    ]
    with pytest.raises(RubricaInvalida) as exc:
        Rubrica.desde_dict(datos)
    assert any("ui" in p for p in exc.value.problemas)


def test_rubrica_sin_criterios_es_invalida():
    datos = {
        "rubrica": {
            "nombre": "vacia",
            "escala": {"tope_por_critico": 6},
            "secciones": [],
        }
    }
    with pytest.raises(RubricaInvalida) as exc:
        Rubrica.desde_dict(datos, artefactos_requeridos=frozenset())
    assert any("ningún criterio" in p for p in exc.value.problemas)


def test_ids_duplicados_es_invalido():
    datos = _rubrica_completa_expo1()
    # Forzamos dos criterios con el mismo id en secciones distintas
    datos["rubrica"]["secciones"][0]["criterios"][0]["id"] = "DUP"
    datos["rubrica"]["secciones"][1]["criterios"][0]["id"] = "DUP"
    with pytest.raises(RubricaInvalida) as exc:
        Rubrica.desde_dict(datos)
    assert any("duplicado" in p for p in exc.value.problemas)


def test_acumula_multiples_problemas():
    """La validación no se detiene en el primer error (CFG-01: corregir de una)."""
    datos = _rubrica_completa_expo1()
    datos["rubrica"]["escala"]["tope_por_critico"] = 99  # problema 1
    datos["rubrica"]["secciones"][0]["criterios"][0]["peso"] = -1  # problema 2
    with pytest.raises(RubricaInvalida) as exc:
        Rubrica.desde_dict(datos)
    assert len(exc.value.problemas) >= 2


def test_transversales_se_incorporan_como_seccion():
    datos = _rubrica_completa_expo1()
    datos["rubrica"]["transversales"] = {
        "criterios": [_criterio(cid="TRZ-1", peso=3, critico=True)]
    }
    r = Rubrica.desde_dict(datos)
    assert r.seccion("transversal") is not None
    assert any(c.id == "TRZ-1" and c.critico for c in r.criterios())
