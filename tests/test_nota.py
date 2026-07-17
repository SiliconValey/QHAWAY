"""Tests del cálculo de nota (EVA-05, EVA-06, Apéndice B del SRS).

Los dos ejemplos del Apéndice B son los tests canónicos: si estos pasan, la
mecánica base es correcta.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from qhaway.dominio import (
    Nivel,
    Rubrica,
    ValoracionFaltante,
    calcular_nota,
    valoraciones_con_ausentes,
)


def _rubrica(criterios, *, tope=6):
    """Arma una rúbrica válida mínima con los criterios dados en una sola sección.

    `criterios` es una lista de (id, peso, critico). Se completan los cuatro
    niveles canónicos con descripciones dummy y se cubren los artefactos
    requeridos con secciones vacías-no (cada artefacto necesita >=1 criterio para
    CFG-01, así que distribuimos). Para simplificar, metemos todo en 'srs' y
    desactivamos el chequeo de artefactos requeridos con un set vacío.
    """
    niveles = {n.value: "..." for n in Nivel}
    secc = {
        "artefacto": "srs",
        "criterios": [
            {
                "id": cid,
                "descripcion": "d",
                "peso": peso,
                "critico": crit,
                "niveles": niveles,
            }
            for (cid, peso, crit) in criterios
        ],
    }
    datos = {
        "rubrica": {
            "nombre": "test",
            "escala": {"tope_por_critico": tope},
            "secciones": [secc],
        }
    }
    return Rubrica.desde_dict(datos, artefactos_requeridos=frozenset())


def test_apendice_b_ejemplo_1():
    # pesos 3,1,2 con Bueno(8), Excelente(10), Regular(5): 44/6 = 7,33 -> 7
    r = _rubrica([("A", 3, False), ("B", 1, False), ("C", 2, False)])
    comp = calcular_nota(
        r, {"A": Nivel.BUENO, "B": Nivel.EXCELENTE, "C": Nivel.REGULAR}
    )
    assert comp.promedio_ponderado == Fraction(44, 6)
    assert comp.nota == 7
    assert comp.tope_aplicado is False


def test_apendice_b_ejemplo_2_critico_insuficiente():
    # tercer criterio crítico e Insuficiente(2): 38/6 = 6,33 -> 6, tope 6 acota
    r = _rubrica([("A", 3, False), ("B", 1, False), ("C", 2, True)], tope=6)
    comp = calcular_nota(
        r, {"A": Nivel.BUENO, "B": Nivel.EXCELENTE, "C": Nivel.INSUFICIENTE}
    )
    assert comp.promedio_ponderado == Fraction(38, 6)
    assert comp.nota == 6
    assert comp.criticos_insuficientes == ("C",)


def test_mitad_exacta_redondea_hacia_arriba():
    # (8 + 5) / 2 = 6,5 -> 7 (regla EVA-05 v1.1: mitades hacia arriba)
    r = _rubrica([("A", 1, False), ("B", 1, False)])
    comp = calcular_nota(r, {"A": Nivel.BUENO, "B": Nivel.REGULAR})
    assert comp.promedio_ponderado == Fraction(13, 2)
    assert comp.nota == 7


def test_tope_por_critico_acota_una_nota_alta():
    # A vale mucho (Excelente) pero el crítico B es Insuficiente -> tope 6
    # (10*4 + 2*1) / 5 = 42/5 = 8,4 -> 8, acotado a 6 por B crítico insuficiente
    r = _rubrica([("A", 4, False), ("B", 1, True)], tope=6)
    comp = calcular_nota(r, {"A": Nivel.EXCELENTE, "B": Nivel.INSUFICIENTE})
    assert comp.nota == 6
    assert comp.tope_aplicado is True


def test_critico_no_insuficiente_no_activa_tope():
    # crítico presente pero en Bueno: sin tope
    r = _rubrica([("A", 1, True)], tope=6)
    comp = calcular_nota(r, {"A": Nivel.BUENO})
    assert comp.nota == 8
    assert comp.tope_aplicado is False


def test_todo_insuficiente_da_dos():
    r = _rubrica([("A", 1, False), ("B", 3, False)])
    comp = calcular_nota(r, {"A": Nivel.INSUFICIENTE, "B": Nivel.INSUFICIENTE})
    assert comp.nota == 2


def test_valoracion_faltante_levanta_error():
    r = _rubrica([("A", 1, False), ("B", 1, False)])
    with pytest.raises(ValoracionFaltante):
        calcular_nota(r, {"A": Nivel.BUENO})  # falta B


def test_peso_efectivo_normalizado_suma_uno():
    r = _rubrica([("A", 3, False), ("B", 1, False), ("C", 2, False)])
    comp = calcular_nota(
        r, {"A": Nivel.BUENO, "B": Nivel.BUENO, "C": Nivel.BUENO}
    )
    total = sum((a.peso_efectivo for a in comp.aportes), Fraction(0))
    assert total == 1
    # 3/6, 1/6, 2/6
    assert {a.criterio_id: a.peso_efectivo for a in comp.aportes} == {
        "A": Fraction(1, 2),
        "B": Fraction(1, 6),
        "C": Fraction(1, 3),
    }


def test_artefacto_ausente_fuerza_insuficiente_en_su_seccion():
    # Rúbrica con dos secciones: srs (presente) y ui (ausente).
    niveles = {n.value: "..." for n in Nivel}
    datos = {
        "rubrica": {
            "nombre": "t",
            "escala": {"tope_por_critico": 6},
            "secciones": [
                {
                    "artefacto": "srs",
                    "criterios": [
                        {"id": "S1", "descripcion": "d", "peso": 1, "niveles": niveles}
                    ],
                },
                {
                    "artefacto": "ui",
                    "criterios": [
                        {"id": "U1", "descripcion": "d", "peso": 1, "niveles": niveles}
                    ],
                },
            ],
        }
    }
    r = Rubrica.desde_dict(datos, artefactos_requeridos=frozenset())

    # El docente solo valoró el srs; ui está ausente.
    parciales = {"S1": Nivel.EXCELENTE}
    completas = valoraciones_con_ausentes(r, parciales, {"ui"})
    assert completas["U1"] is Nivel.INSUFICIENTE

    comp = calcular_nota(r, completas)
    # (10 + 2) / 2 = 6
    assert comp.nota == 6
