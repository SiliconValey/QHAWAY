"""Tests del conector de IA con ConectorFalso (IEX-02, EVA-13, MON-01).

Sin tokens, sin red: el falso ejercita toda la máquina compartida (reintentos,
validación, registro de consumo).
"""

from __future__ import annotations

import json

from qhaway.infra.conector_ia import (
    ConectorFalso,
    ErrorTransitorio,
    PoliticaReintentos,
    RespuestaCruda,
)

CRITERIOS = {"SRS-REQ", "SRS-EST"}


def _json_valido() -> str:
    return json.dumps({
        "artefacto": "srs",
        "valoraciones": [
            {"criterio_id": "SRS-REQ", "nivel": "Bueno", "justificacion": "x"},
            {"criterio_id": "SRS-EST", "nivel": "Regular", "justificacion": "x"},
        ],
        "observaciones": [],
    })


def _json_invalido() -> str:
    # Falta la valoración de SRS-EST -> viola la regla 3.
    return json.dumps({
        "artefacto": "srs",
        "valoraciones": [
            {"criterio_id": "SRS-REQ", "nivel": "Bueno", "justificacion": "x"},
        ],
        "observaciones": [],
    })


def _conector(guion, **kw):
    esperas: list[float] = []
    c = ConectorFalso(
        guion,
        dormir=lambda s: esperas.append(s),
        reloj=lambda: "t",
        **kw,
    )
    return c, esperas


def test_valido_a_la_primera():
    c, esperas = _conector([_json_valido()])
    r = c.analizar_artefacto("prompt", CRITERIOS)
    assert r.completado
    assert c.llamadas == 1
    assert len(r.consumos) == 1
    assert esperas == []  # no hubo que esperar


def test_invalido_luego_valido_reintenta():
    c, esperas = _conector([_json_invalido(), _json_valido()])
    r = c.analizar_artefacto("prompt", CRITERIOS)
    assert r.completado
    assert c.llamadas == 2
    # Ambos intentos costaron tokens y se registraron (MON-01)
    assert len(r.consumos) == 2
    assert [x.reintento for x in r.consumos] == [0, 1]
    assert len(esperas) == 1  # esperó una vez, entre los dos intentos


def test_todo_invalido_queda_pendiente():
    guion = [_json_invalido()] * 4  # 1 + 3 reintentos
    c, esperas = _conector(guion)
    r = c.analizar_artefacto("prompt", CRITERIOS)
    assert r.estado == "pendiente"
    assert not r.completado
    assert c.llamadas == 4
    assert r.errores  # reporta por qué
    # Registró consumo de los 4 intentos
    assert len(r.consumos) == 4


def test_red_caida_luego_valido():
    c, esperas = _conector([ErrorTransitorio("timeout"), _json_valido()])
    r = c.analizar_artefacto("prompt", CRITERIOS)
    assert r.completado
    assert c.llamadas == 2
    # El intento fallido se registró con 0 tokens (no hubo respuesta)
    assert r.consumos[0].tokens_entrada == 0
    assert r.consumos[0].costo_estimado == 0.0


def test_toda_la_red_caida_queda_pendiente():
    c, esperas = _conector([ErrorTransitorio("x")] * 4)
    r = c.analizar_artefacto("prompt", CRITERIOS)
    assert r.estado == "pendiente"
    assert c.llamadas == 4


def test_backoff_exponencial_no_espera_tras_ultimo():
    guion = [_json_invalido()] * 4
    c, esperas = _conector(guion, politica=PoliticaReintentos(reintentos=3, base_espera=1.0))
    c.analizar_artefacto("prompt", CRITERIOS)
    # Espera tras intentos 0,1,2 pero NO tras el 3 (último): 1, 2, 4
    assert esperas == [1.0, 2.0, 4.0]


def test_costo_se_calcula_de_los_tokens():
    resp = RespuestaCruda(texto=_json_valido(), tokens_entrada=1_000_000, tokens_salida=0)
    c, _ = _conector([resp])
    r = c.analizar_artefacto("prompt", CRITERIOS)
    # 1M tokens de entrada a USD 3/MTok = USD 3.0
    assert abs(r.consumos[0].costo_estimado - 3.0) < 1e-9


def test_transversal_valido():
    texto = json.dumps({
        "consistencias": [],
        "preguntas_defensa": [
            {"pregunta": "¿por qué?", "elemento": "RF-01", "artefacto": "srs", "intencion": "x"}
        ],
        "senales": [],
    })
    c, _ = _conector([texto])
    r = c.analizar_transversal("prompt")
    assert r.completado
    assert r.resultado.preguntas_defensa[0].elemento == "RF-01"
