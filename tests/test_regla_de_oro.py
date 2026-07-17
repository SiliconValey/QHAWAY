"""Test de la REGLA DE ORO (criterio de salida de la Etapa 2).

Borrar `qhaway.db` y reconstruir TODO el trabajo de evaluación desde las
carpetas: entregas, análisis, decisiones, valoraciones y notas. Los metadatos
operativos (integrantes, parámetros del ciclo) NO se reconstruyen — por diseño
(AD-03) — y eso también se verifica.
"""

from __future__ import annotations

from qhaway.dominio.estados import EstadoEvaluacion as E
from qhaway.infra import crear_ciclo, reconstruir_desde_carpetas


def _armar_ciclo_con_trabajo(raiz):
    """Crea un ciclo con un grupo y una evaluación completa, materializada a disco."""
    c = crear_ciclo(raiz, "AED II — 2027")
    gid = c.grupos.crear(c.ciclo_id, "G03", "Los Andinos", "Distribuidora Andes")
    c.integrantes.agregar(gid, "Ana Pérez", "2027-03-01")
    c.integrantes.agregar(gid, "Beto Gómez", "2027-03-01")
    grupo = c.grupos.obtener(gid)

    entrega = c.entregas.crear_version(gid, 1, "2027-04-10", E.BORRADOR_EN_REVISION.value)

    # Índice en base
    cv = c.carpeta_version(grupo, 1, 1)
    ruta_rel = c.rutas.relativa(cv / "entrega" / "srs.pdf")
    c.archivos.agregar(entrega.id, "srs", ruta_rel, "pdf")
    (cv / "entrega").mkdir(parents=True, exist_ok=True)
    (cv / "entrega" / "srs.pdf").write_bytes(b"%PDF-1.4 contenido de prueba")

    ev_id = c.evaluaciones.crear(entrega.id, E.BORRADOR_EN_REVISION.value)
    c.valoraciones.registrar(ev_id, "SRS-REQ", "Bueno", "Bueno")
    c.valoraciones.registrar(ev_id, "SRS-EST", "Regular", "Bueno")  # el docente subió el nivel
    c.evaluaciones.fijar_nota_sugerida(ev_id, 7)
    c.evaluaciones.validar(ev_id, 8, "2027-04-13")

    # Contenido en archivos (lo que la regla de oro exige poder reconstruir)
    c.guardar_manifiesto_entrega(grupo, entrega, [
        {"nombre": "srs.pdf", "tipo_artefacto": "srs", "formato": "pdf"},
    ])
    c.guardar_evaluacion_en_archivo(grupo, entrega, {
        "estado": E.EVALUACION_VALIDADA.value,
        "vigente": True,
        "fecha": "2027-04-10",
        "nota_sugerida": 7,
        "nota_final": 8,
        "fecha_validacion": "2027-04-13",
        "valoraciones": {
            "SRS-REQ": {"nivel_ia": "Bueno", "nivel_final": "Bueno"},
            "SRS-EST": {"nivel_ia": "Regular", "nivel_final": "Bueno"},
        },
    })
    c.guardar_analisis_en_archivo(grupo, entrega, "srs", {
        "unidad": "srs",
        "observaciones": [{"criterio_id": "SRS-REQ", "texto": "RF-06 sin estructura tarifaria"}],
    })
    c.guardar_decisiones_en_archivo(grupo, entrega, {
        "decisiones": [{"elemento": "obs-1", "estado_revision": "aceptado"}],
    })
    c.cerrar()
    return raiz


def test_regla_de_oro(tmp_path):
    raiz = _armar_ciclo_con_trabajo(tmp_path / "AED2-2027")

    # --- Cataclismo: se pierde la base ---
    (raiz / "qhaway.db").unlink()
    for wal in raiz.glob("qhaway.db-*"):  # WAL/SHM
        wal.unlink()

    # --- Reconstrucción desde carpetas ---
    rep = reconstruir_desde_carpetas(raiz)

    # El trabajo de evaluación volvió
    assert rep.grupos == 1
    assert rep.entregas == 1
    assert rep.evaluaciones == 1
    assert rep.valoraciones == 2
    assert rep.analisis == 1
    assert rep.decisiones == 1

    # Verificación directa contra la base reconstruida
    from qhaway.infra import abrir_ciclo
    c = abrir_ciclo(raiz)

    ev = c.con.execute(
        "SELECT nota_sugerida, nota_final FROM evaluacion"
    ).fetchone()
    assert ev["nota_sugerida"] == 7
    assert ev["nota_final"] == 8  # la nota validada se recuperó

    vals = {
        f["criterio_id"]: f
        for f in c.con.execute(
            "SELECT criterio_id, nivel_ia, nivel_final FROM valoracion"
        ).fetchall()
    }
    # Se conservan ambos niveles (REV-04): el de la IA y el corregido por el docente
    assert vals["SRS-EST"]["nivel_ia"] == "Regular"
    assert vals["SRS-EST"]["nivel_final"] == "Bueno"

    # El código y el proyecto del grupo son recuperables (no personales)
    grupo = c.grupos.listar(c.ciclo_id)[0]
    assert grupo.codigo == "G03"
    assert grupo.proyecto == "distribuidora-andes"

    # --- Lo que NO se reconstruye (AD-03) ---
    integrantes = c.con.execute("SELECT COUNT(*) AS n FROM integrante").fetchone()["n"]
    assert integrantes == 0  # los nombres de los alumnos NO están en las carpetas
    assert "integrantes" in " ".join(rep.metadatos_perdidos)
    c.cerrar()


def test_archivo_de_entrega_sobrevive(tmp_path):
    # El archivo crudo de la entrega sigue en disco tras la reconstrucción.
    raiz = _armar_ciclo_con_trabajo(tmp_path / "AED2-2027")
    (raiz / "qhaway.db").unlink()
    for wal in raiz.glob("qhaway.db-*"):
        wal.unlink()
    reconstruir_desde_carpetas(raiz)

    from qhaway.infra import abrir_ciclo
    c = abrir_ciclo(raiz)
    fila = c.con.execute("SELECT ruta_relativa FROM archivo_entrega").fetchone()
    assert c.rutas.absoluta(fila["ruta_relativa"]).exists()
    # Y la integridad da OK: la base reconstruida y el disco coinciden
    assert c.verificar_integridad().ok
    c.cerrar()
