"""Tests de la capa de persistencia (GRP-02/04/08, CFG-11, integridad)."""

from __future__ import annotations

from qhaway.dominio.estados import EstadoEvaluacion as E, TransicionInvalida
from qhaway.infra import crear_ciclo, abrir_ciclo
from qhaway.infra.archivos import escribir_atomico, leer_json, escribir_json


def _ciclo(tmp_path):
    return crear_ciclo(tmp_path / "AED2-2027", "AED II — 2027")


def test_crear_y_reabrir_ciclo(tmp_path):
    c = _ciclo(tmp_path)
    assert c.rutas.db.exists()
    assert (c.rutas.raiz / "grupos").is_dir()
    c.cerrar()

    c2 = abrir_ciclo(tmp_path / "AED2-2027")
    assert c2.ciclos.obtener(c2.ciclo_id).nombre == "AED II — 2027"
    c2.cerrar()


def test_esquema_versionado(tmp_path):
    c = _ciclo(tmp_path)
    v = c.con.execute("PRAGMA user_version").fetchone()[0]
    assert v == 1
    c.cerrar()


def test_alta_y_composicion_por_fecha(tmp_path):
    # GRP-02: la composición del grupo se reconstruye a una fecha dada.
    c = _ciclo(tmp_path)
    gid = c.grupos.crear(c.ciclo_id, "G01", "Los Punteros", "EstacionAR")
    ana = c.integrantes.agregar(gid, "Ana", "2027-03-01")
    c.integrantes.agregar(gid, "Beto", "2027-03-01")
    # Beto se va y entra Caro en abril
    c.integrantes.dar_baja(_id_de(c, gid, "Beto"), "2027-04-01")
    c.integrantes.agregar(gid, "Caro", "2027-04-01")

    en_marzo = c.integrantes.composicion_en(gid, "2027-03-15")
    en_abril = c.integrantes.composicion_en(gid, "2027-04-15")
    assert en_marzo == ["Ana", "Beto"]
    assert en_abril == ["Ana", "Caro"]
    c.cerrar()


def test_reentrega_crea_version_nueva_sin_pisar(tmp_path):
    # GRP-04: la re-entrega inserta versión nueva; la última es la vigente.
    c = _ciclo(tmp_path)
    gid = c.grupos.crear(c.ciclo_id, "G01", "N", "P")
    e1 = c.entregas.crear_version(gid, 1, "2027-04-10", E.ENTREGA_CARGADA.value)
    e2 = c.entregas.crear_version(gid, 1, "2027-04-20", E.ENTREGA_CARGADA.value)
    assert e1.version == 1 and e2.version == 2

    hist = c.entregas.historial(gid, 1)
    assert [e.version for e in hist] == [1, 2]
    assert c.entregas.vigente(gid, 1).version == 2  # la última

    # El docente vuelve a marcar la v1 como vigente
    c.entregas.marcar_vigente(e1.id)
    assert c.entregas.vigente(gid, 1).version == 1
    c.cerrar()


def test_archivado_es_baja_logica(tmp_path):
    # GRP-08: archivar oculta de la operación pero conserva el historial.
    c = _ciclo(tmp_path)
    gid = c.grupos.crear(c.ciclo_id, "G01", "N", "P")
    c.grupos.archivar(gid)
    assert c.grupos.listar(c.ciclo_id) == []  # no aparece
    assert len(c.grupos.listar(c.ciclo_id, incluir_archivados=True)) == 1  # sigue ahí
    c.cerrar()


def test_transicion_estado_via_dominio(tmp_path):
    c = _ciclo(tmp_path)
    gid = c.grupos.crear(c.ciclo_id, "G01", "N", "P")
    e = c.entregas.crear_version(gid, 1, "2027-04-10", E.SIN_ENTREGA.value)
    c.transicionar_entrega(e.id, E.ENTREGA_CARGADA)
    c.transicionar_entrega(e.id, E.ANALIZANDO)
    fila = c.con.execute("SELECT estado FROM entrega WHERE id = ?", (e.id,)).fetchone()
    assert fila["estado"] == E.ANALIZANDO.value

    # Una transición ilegal se rechaza (la máquina del dominio manda).
    try:
        c.transicionar_entrega(e.id, E.INFORME_EXPORTADO)
        assert False, "debió rechazar la transición"
    except TransicionInvalida:
        pass
    c.cerrar()


def test_snapshot_congela_config(tmp_path):
    # CFG-11: la instantánea copia config/ y queda registrada.
    c = _ciclo(tmp_path)
    escribir_atomico(c.rutas.config() / "rubrica.yaml", "rubrica: {}\n")
    sid = c.crear_snapshot("2027-04-12")
    assert sid > 0
    filas = list(c.con.execute("SELECT * FROM snapshot_config"))
    assert len(filas) == 1
    # La carpeta de snapshot existe en disco
    carpeta = c.rutas.absoluta(filas[0]["ruta_relativa"])
    assert (carpeta / "rubrica.yaml").exists()
    c.cerrar()


def test_integridad_detecta_faltante(tmp_path):
    c = _ciclo(tmp_path)
    gid = c.grupos.crear(c.ciclo_id, "G01", "N", "P")
    e = c.entregas.crear_version(gid, 1, "2027-04-10", E.ENTREGA_CARGADA.value)
    grupo = c.grupos.obtener(gid)
    cv = c.carpeta_version(grupo, 1, 1)
    # Referenciamos un archivo en la base que NO escribimos en disco.
    ruta_rel = c.rutas.relativa(cv / "entrega" / "srs.pdf")
    c.archivos.agregar(e.id, "srs", ruta_rel, "pdf")

    rep = c.verificar_integridad()
    assert not rep.ok
    assert ruta_rel in rep.faltantes
    c.cerrar()


def test_escritura_atomica_roundtrip(tmp_path):
    ruta = tmp_path / "sub" / "datos.json"
    escribir_json(ruta, {"b": 2, "a": 1})
    assert leer_json(ruta) == {"a": 1, "b": 2}
    # No quedan temporales
    assert not list((tmp_path / "sub").glob(".tmp_*"))


def _id_de(c, grupo_id, nombre):
    return c.con.execute(
        "SELECT id FROM integrante WHERE grupo_id = ? AND nombre = ?",
        (grupo_id, nombre),
    ).fetchone()["id"]
