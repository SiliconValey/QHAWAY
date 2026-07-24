"""Tests de validación del esquema de salidas (EVA-13, esquema Etapa 0.1)."""

from __future__ import annotations

from qhaway.dominio.esquema_salidas import (
    parsear_json,
    validar_artefacto,
    validar_transversal,
)

CRITERIOS = {"SRS-REQ", "SRS-EST"}


def _artefacto_valido():
    return {
        "artefacto": "srs",
        "valoraciones": [
            {"criterio_id": "SRS-REQ", "nivel": "Bueno", "justificacion": "ok"},
            {"criterio_id": "SRS-EST", "nivel": "Regular", "justificacion": "ok"},
        ],
        "observaciones": [
            {
                "criterio_id": "SRS-REQ",
                "tipo": "mejora",
                "contenido": "RF-06 sin estructura tarifaria",
                "referencia": {"ubicacion": "3 Requerimientos", "pagina": 5, "cita": None},
            }
        ],
    }


def test_artefacto_valido():
    v = validar_artefacto(_artefacto_valido(), CRITERIOS)
    assert v.ok
    assert len(v.resultado.valoraciones) == 2
    assert v.resultado.observaciones[0].referencia.pagina == 5


def test_regla1_nivel_no_canonico():
    data = _artefacto_valido()
    data["valoraciones"][0]["nivel"] = "Excelentísimo"
    v = validar_artefacto(data, CRITERIOS)
    assert not v.ok
    assert any("enum canónico" in e for e in v.errores)


def test_regla2_criterio_desconocido():
    data = _artefacto_valido()
    data["valoraciones"][0]["criterio_id"] = "SRS-XXX"
    v = validar_artefacto(data, CRITERIOS)
    assert not v.ok
    assert any("desconocido" in e for e in v.errores)


def test_regla3_valoracion_faltante():
    data = _artefacto_valido()
    data["valoraciones"] = data["valoraciones"][:1]  # falta SRS-EST
    v = validar_artefacto(data, CRITERIOS)
    assert not v.ok
    assert any("Faltan valoraciones" in e for e in v.errores)


def test_regla3_valoracion_duplicada():
    data = _artefacto_valido()
    data["valoraciones"].append(
        {"criterio_id": "SRS-REQ", "nivel": "Bueno", "justificacion": "dup"}
    )
    v = validar_artefacto(data, CRITERIOS)
    assert not v.ok
    assert any("duplicad" in e for e in v.errores)


def test_regla5_observacion_sin_ubicacion():
    data = _artefacto_valido()
    data["observaciones"][0]["referencia"] = {"ubicacion": "", "pagina": None}
    v = validar_artefacto(data, CRITERIOS)
    assert not v.ok
    assert any("ubicacion" in e for e in v.errores)


def test_regla5_cita_demasiado_larga():
    data = _artefacto_valido()
    data["observaciones"][0]["referencia"]["cita"] = " ".join(["palabra"] * 26)
    v = validar_artefacto(data, CRITERIOS)
    assert not v.ok
    assert any("palabras" in e for e in v.errores)


# --- Transversal --------------------------------------------------------------
def _transversal_valido():
    return {
        "consistencias": [
            {"tipo": "srs_fd", "elemento": "RF-03", "hallazgo": "no está en el FD",
             "referencias": []}
        ],
        "preguntas_defensa": [
            {"pregunta": "¿Por qué RF-03 no tiene pantalla?", "elemento": "RF-03",
             "artefacto": "srs", "intencion": "verificar comprensión"}
        ],
        "senales": [
            {"descripcion": "salto de sofisticación", "artefacto": "srs",
             "sugerencia": "preguntar el porqué"}
        ],
    }


def test_transversal_valido():
    v = validar_transversal(_transversal_valido())
    assert v.ok
    assert v.resultado.preguntas_defensa[0].elemento == "RF-03"


def test_regla4_pregunta_sin_elemento():
    data = _transversal_valido()
    data["preguntas_defensa"][0]["elemento"] = ""
    v = validar_transversal(data)
    assert not v.ok
    assert any("elemento" in e for e in v.errores)


def test_regla6_senal_con_criterio_es_invalida():
    data = _transversal_valido()
    data["senales"][0]["criterio_id"] = "SRS-REQ"  # prohibido
    v = validar_transversal(data)
    assert not v.ok
    assert any("señal" in e.lower() for e in v.errores)


# --- Parseo -------------------------------------------------------------------
def test_parseo_tolera_cercas_markdown():
    texto = "```json\n{\"a\": 1}\n```"
    data, err = parsear_json(texto)
    assert err is None and data == {"a": 1}


def test_parseo_tolera_texto_alrededor():
    # Respuesta real típica: preámbulo + JSON + comentario final.
    texto = 'Claro, acá está el análisis:\n\n{"a": 1, "b": [2, 3]}\n\nEspero que sirva.'
    data, err = parsear_json(texto)
    assert err is None and data == {"a": 1, "b": [2, 3]}


def test_parseo_json_invalido():
    data, err = parsear_json("no soy json")
    assert data is None and err is not None
