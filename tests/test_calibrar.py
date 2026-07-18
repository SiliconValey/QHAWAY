"""Tests del arnés de calibración (Etapa 9, métrica 0.7)."""

from __future__ import annotations

import json

from qhaway.dominio.calibracion import CasoCalibracion, agregar_corridas, moda_nivel
from qhaway.dominio.niveles import Nivel
from qhaway.dominio.rubrica import Rubrica
from qhaway.servicios import calibrar
from qhaway.servicios.calibrar import ResultadoCorrida


def _rubrica():
    niveles = {n.value: "..." for n in Nivel}
    return Rubrica.desde_dict({"rubrica": {"nombre": "R", "escala": {"tope_por_critico": 6},
        "secciones": [{"artefacto": "srs", "criterios": [
            {"id": "A", "descripcion": "d", "peso": 1, "niveles": niveles},
            {"id": "B", "descripcion": "d", "peso": 1, "niveles": niveles}]}]}},
        artefactos_requeridos=frozenset())


def test_moda_nivel_y_empate_conservador():
    assert moda_nivel([Nivel.BUENO, Nivel.BUENO, Nivel.REGULAR]) == Nivel.BUENO
    # Empate 1-1: gana el de menor orden (conservador)
    assert moda_nivel([Nivel.BUENO, Nivel.REGULAR]) == Nivel.REGULAR


def test_agregar_corridas_por_criterio():
    corridas = [
        {"A": Nivel.BUENO, "B": Nivel.REGULAR},
        {"A": Nivel.BUENO, "B": Nivel.BUENO},
        {"A": Nivel.REGULAR, "B": Nivel.BUENO},
    ]
    agg = agregar_corridas(corridas)
    assert agg["A"] == Nivel.BUENO   # 2 Bueno, 1 Regular
    assert agg["B"] == Nivel.BUENO   # 2 Bueno, 1 Regular


def test_agregar_y_medir_coincidencia_buena():
    caso = CasoCalibracion("G01", nota_docente=8,
                           valoraciones_docente={"A": Nivel.BUENO, "B": Nivel.BUENO})
    corridas = [
        ResultadoCorrida(8, {"A": Nivel.BUENO, "B": Nivel.BUENO}),
        ResultadoCorrida(8, {"A": Nivel.BUENO, "B": Nivel.BUENO}),
        ResultadoCorrida(7, {"A": Nivel.BUENO, "B": Nivel.REGULAR}),
    ]
    r = calibrar.agregar_y_medir(caso, corridas, _rubrica())
    assert r.c1_ok()               # nota agregada 8, Δ0
    assert r.c3_ok()               # todos ≤1
    assert not r.inestable


def test_inestabilidad_por_peor_caso():
    # El agregado por moda pasa, pero UNA corrida invirtió el juicio (distancia 3).
    caso = CasoCalibracion("G02", nota_docente=9,
                           valoraciones_docente={"A": Nivel.EXCELENTE, "B": Nivel.EXCELENTE})
    corridas = [
        ResultadoCorrida(9, {"A": Nivel.EXCELENTE, "B": Nivel.EXCELENTE}),
        ResultadoCorrida(9, {"A": Nivel.EXCELENTE, "B": Nivel.EXCELENTE}),
        ResultadoCorrida(4, {"A": Nivel.INSUFICIENTE, "B": Nivel.EXCELENTE}),  # distancia 3 en A
    ]
    r = calibrar.agregar_y_medir(caso, corridas, _rubrica())
    assert r.coincidencia.distancia_3 == 0   # el agregado no la tiene
    assert r.peor_distancia_3 == 1           # pero una corrida sí
    assert r.inestable                        # -> falla C3 por inestabilidad
    assert not r.c3_ok()


def test_resumen_set_aceptacion():
    caso = CasoCalibracion("G", 8, {"A": Nivel.BUENO, "B": Nivel.BUENO})
    bueno = calibrar.agregar_y_medir(caso, [
        ResultadoCorrida(8, {"A": Nivel.BUENO, "B": Nivel.BUENO})], _rubrica())
    resumen = calibrar.resumir_set([bueno, bueno, bueno])
    assert resumen.aceptado()
    assert "ACEPTADO" in resumen.resumen()


def test_distancia_3_descalifica_el_set():
    caso = CasoCalibracion("G", 5, {"A": Nivel.EXCELENTE, "B": Nivel.BUENO})
    # IA pone Insuficiente donde el docente puso Excelente: distancia 3
    malo = calibrar.agregar_y_medir(caso, [
        ResultadoCorrida(5, {"A": Nivel.INSUFICIENTE, "B": Nivel.BUENO})], _rubrica())
    resumen = calibrar.resumir_set([malo])
    assert resumen.hay_distancia_3
    assert not resumen.aceptado()


# --- Integración con el pipeline real (conector falso, 3 corridas) ----------
UI_XML = '<ui version="4.0"><widget class="QWidget" name="F">' \
         '<widget class="QPushButton" name="btnOk"/></widget></ui>'


def _preparar_entrega(tmp_path):
    from qhaway.infra import crear_ciclo
    from qhaway.dominio.estados import EstadoEvaluacion as E
    c = crear_ciclo(tmp_path / "c", "ciclo")
    gid = c.grupos.crear(c.ciclo_id, "G01", "N", "P")
    grupo = c.grupos.obtener(gid)
    entrega = c.entregas.crear_version(gid, 1, "2027-04-10", E.ENTREGA_CARGADA.value)
    cv = c.carpeta_version(grupo, 1, 1)
    (cv / "entrega").mkdir(parents=True, exist_ok=True)
    (cv / "entrega" / "form.ui").write_text(UI_XML, encoding="utf-8")
    c.archivos.agregar(entrega.id, "ui", c.rutas.relativa(cv / "entrega" / "form.ui"), "ui")
    return c, grupo, entrega


def test_correr_n_corridas_integra_pipeline(tmp_path):
    from qhaway.dominio.rubrica import Rubrica
    from qhaway.infra import NOMENCLATURA_DEFECTO
    from qhaway.infra.conector_ia import ConectorFalso
    from qhaway.servicios import ContextoAnalisis

    c, grupo, entrega = _preparar_entrega(tmp_path)
    niveles = {n.value: "..." for n in Nivel}
    rubrica = Rubrica.desde_dict({"rubrica": {"nombre": "R", "escala": {"tope_por_critico": 6},
        "secciones": [{"artefacto": "ui", "criterios": [
            {"id": "UI-NOM", "descripcion": "d", "peso": 1, "niveles": niveles}]}]}},
        artefactos_requeridos=frozenset())
    contexto = ContextoAnalisis(rubrica=rubrica, checklists={}, nomenclatura=NOMENCLATURA_DEFECTO)

    def resp(nivel):
        return json.dumps({"artefacto": "ui", "valoraciones": [
            {"criterio_id": "UI-NOM", "nivel": nivel, "justificacion": "x"}], "observaciones": []})
    trans = json.dumps({"consistencias": [], "senales": [], "preguntas_defensa": []})

    # 3 corridas: Bueno, Bueno, Regular  (moda -> Bueno)
    guion = [resp("Bueno"), trans, resp("Bueno"), trans, resp("Regular"), trans]
    conector = ConectorFalso(guion, dormir=lambda s: None, reloj=lambda: "t")

    corridas = calibrar.correr_n_corridas(c, grupo, entrega, contexto, conector, n=3)
    assert len(corridas) == 3
    agg = agregar_corridas([x.valoraciones for x in corridas])
    assert agg["UI-NOM"] == Nivel.BUENO
    c.cerrar()
