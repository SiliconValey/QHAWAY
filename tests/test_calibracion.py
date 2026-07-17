"""Tests de la métrica de calibración (Etapa 0.7)."""

from __future__ import annotations

from qhaway.dominio.niveles import Nivel
from qhaway.dominio.calibracion import CasoCalibracion, medir, resumir


def _caso():
    return CasoCalibracion(
        id="G03-expo1",
        nota_docente=8,
        valoraciones_docente={
            "SRS-REQ": Nivel.BUENO,
            "SRS-EST": Nivel.EXCELENTE,
            "UI-NOM": Nivel.REGULAR,
        },
    )


def test_coincidencia_perfecta():
    c = medir(_caso(), 8, {
        "SRS-REQ": Nivel.BUENO, "SRS-EST": Nivel.EXCELENTE, "UI-NOM": Nivel.REGULAR
    })
    assert c.diferencia_nota == 0
    assert c.exactas == 3
    assert c.distancia_promedio == 0.0
    assert c.dentro_umbral()


def test_valoracion_adyacente():
    # SRS-REQ Bueno(2) vs Excelente(3): distancia 1 (adyacente)
    c = medir(_caso(), 8, {
        "SRS-REQ": Nivel.EXCELENTE, "SRS-EST": Nivel.EXCELENTE, "UI-NOM": Nivel.REGULAR
    })
    assert c.adyacentes == 1
    assert c.exactas == 2
    assert c.criterios_lejanos == ()


def test_valoracion_lejana_se_reporta():
    # UI-NOM Regular(1) vs Insuficiente(0)... hagamos distancia 2:
    # docente Regular(1), ia Excelente(3) -> distancia 2 (lejana)
    c = medir(_caso(), 6, {
        "SRS-REQ": Nivel.BUENO, "SRS-EST": Nivel.EXCELENTE, "UI-NOM": Nivel.EXCELENTE
    })
    assert c.lejanas == 1
    assert "UI-NOM" in c.criterios_lejanos
    assert c.diferencia_nota == 2


def test_solo_compara_criterios_presentes_en_ambos():
    c = medir(_caso(), 8, {"SRS-REQ": Nivel.BUENO})  # faltan dos
    assert c.criterios_comparados == 1


def test_fuera_de_umbral_por_nota():
    c = medir(_caso(), 5, {  # Δnota = 3 > 1
        "SRS-REQ": Nivel.BUENO, "SRS-EST": Nivel.EXCELENTE, "UI-NOM": Nivel.REGULAR
    })
    assert not c.dentro_umbral(umbral_nota=1)


def test_resumen_agrega_varios_casos():
    caso = _caso()
    c1 = medir(caso, 8, {
        "SRS-REQ": Nivel.BUENO, "SRS-EST": Nivel.EXCELENTE, "UI-NOM": Nivel.REGULAR
    })  # perfecto
    c2 = medir(caso, 7, {
        "SRS-REQ": Nivel.REGULAR, "SRS-EST": Nivel.EXCELENTE, "UI-NOM": Nivel.REGULAR
    })  # una adyacente, Δnota 1
    resumen = resumir([c1, c2])
    assert resumen.casos == 2
    assert 0.0 <= resumen.proporcion_exactas <= 1.0
    assert resumen.dentro_umbral >= 1
    assert "Calibración sobre 2" in resumen.resumen()
