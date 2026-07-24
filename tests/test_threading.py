"""Regresión: el análisis corre en el worker (otro hilo) y escribe en SQLite.

El bug: la conexión se creaba en el hilo principal y SQLite rechazaba su uso
desde el hilo del worker ('SQLite objects created in a thread can only be used
in that same thread'). Este test reproduce el escenario sin Qt: corre el pipeline
en un hilo aparte y verifica que completa.
"""

from __future__ import annotations

import json
import threading

from qhaway.dominio.estados import EstadoEvaluacion as E
from qhaway.dominio.niveles import Nivel
from qhaway.dominio.rubrica import Rubrica
from qhaway.infra import NOMENCLATURA_DEFECTO, crear_ciclo
from qhaway.infra.conector_ia import ConectorFalso
from qhaway.servicios import ContextoAnalisis, analizar_entrega

UI_XML = '<ui version="4.0"><widget class="QWidget" name="F">' \
         '<widget class="QPushButton" name="btnOk"/></widget></ui>'


def test_pipeline_desde_otro_hilo(tmp_path):
    c = crear_ciclo(tmp_path / "c", "ciclo")
    gid = c.grupos.crear(c.ciclo_id, "G01", "N", "P")
    grupo = c.grupos.obtener(gid)
    entrega = c.entregas.crear_version(gid, 1, "2027-04-10", E.ENTREGA_CARGADA.value)
    cv = c.carpeta_version(grupo, 1, 1)
    (cv / "entrega").mkdir(parents=True, exist_ok=True)
    (cv / "entrega" / "form.ui").write_text(UI_XML, encoding="utf-8")
    c.archivos.agregar(entrega.id, "ui", c.rutas.relativa(cv / "entrega" / "form.ui"), "ui")

    niveles = {n.value: "..." for n in Nivel}
    rubrica = Rubrica.desde_dict({"rubrica": {"nombre": "R", "escala": {"tope_por_critico": 6},
        "secciones": [{"artefacto": "ui", "criterios": [
            {"id": "UI-NOM", "descripcion": "d", "peso": 1, "niveles": niveles}]}]}},
        artefactos_requeridos=frozenset())
    contexto = ContextoAnalisis(rubrica=rubrica, checklists={}, nomenclatura=NOMENCLATURA_DEFECTO)

    resp = json.dumps({"artefacto": "ui", "valoraciones": [
        {"criterio_id": "UI-NOM", "nivel": "Bueno", "justificacion": "x"}], "observaciones": []})
    trans = json.dumps({"consistencias": [], "senales": [], "preguntas_defensa": []})
    conector = ConectorFalso([resp, trans], dormir=lambda s: None, reloj=lambda: "t")

    resultado = {}
    error = {}

    def correr():
        try:
            resultado["r"] = analizar_entrega(c, grupo, entrega, contexto, conector)
        except Exception as e:  # noqa: BLE001
            error["e"] = e

    hilo = threading.Thread(target=correr)
    hilo.start()
    hilo.join(timeout=10)

    assert "e" not in error, f"El pipeline falló en otro hilo: {error.get('e')}"
    assert resultado["r"].estado_final == E.BORRADOR_EN_REVISION.value
    c.cerrar()
