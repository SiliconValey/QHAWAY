"""Arnés CLI descartable de QHAWAY (Etapa 2).

NO es la interfaz del producto (esa es Qt, Etapa 7). Es una herramienta mínima
para ejercitar los servicios sin UI, y de paso material de clase sobre separación
dominio/infraestructura: acá se ve que el mismo dominio y la misma persistencia
funcionan sin una sola línea de Qt.

Uso:
    python3 qhaway_cli.py crear   <ruta>
    python3 qhaway_cli.py listar  <ruta>
    python3 qhaway_cli.py demo    <ruta>     # flujo completo + regla de oro

El subcomando `demo` arma un ciclo con un grupo y una evaluación (calculando la
nota con el dominio de la Etapa 1), materializa todo a archivos, borra la base y
la reconstruye desde las carpetas — la prueba viva del criterio de salida.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from qhaway.dominio import Nivel, Rubrica, calcular_nota
from qhaway.dominio.estados import EstadoEvaluacion as E
from qhaway.infra import abrir_ciclo, crear_ciclo, reconstruir_desde_carpetas


def _rubrica_demo() -> Rubrica:
    niveles = {n.value: "..." for n in Nivel}
    datos = {
        "rubrica": {
            "nombre": "AED II — Expo 1 (demo)",
            "escala": {"tope_por_critico": 6},
            "secciones": [
                {
                    "artefacto": "srs",
                    "criterios": [
                        {"id": "SRS-REQ", "descripcion": "Requisitos", "peso": 3,
                         "critico": True, "niveles": niveles},
                        {"id": "SRS-EST", "descripcion": "Estructura", "peso": 1,
                         "niveles": niveles},
                    ],
                },
            ],
        }
    }
    return Rubrica.desde_dict(datos, artefactos_requeridos=frozenset())


def cmd_crear(ruta: Path) -> None:
    c = crear_ciclo(ruta, "AED II — 2027")
    print(f"Ciclo creado en {ruta}  (base: {c.rutas.db.name})")
    c.cerrar()


def cmd_listar(ruta: Path) -> None:
    c = abrir_ciclo(ruta)
    grupos = c.grupos.listar(c.ciclo_id, incluir_archivados=True)
    if not grupos:
        print("Sin grupos.")
    for g in grupos:
        marca = " [archivado]" if g.archivado else ""
        print(f"  {g.codigo}  {g.nombre}  ({g.proyecto}){marca}")
    c.cerrar()


def cmd_demo(ruta: Path) -> None:
    if ruta.exists():
        shutil.rmtree(ruta)

    print("=== 1. Crear ciclo y grupo ===")
    c = crear_ciclo(ruta, "AED II — 2027")
    gid = c.grupos.crear(c.ciclo_id, "G03", "Los Andinos", "Distribuidora Andes")
    c.integrantes.agregar(gid, "Ana Pérez", "2027-03-01")
    c.integrantes.agregar(gid, "Beto Gómez", "2027-03-01")
    grupo = c.grupos.obtener(gid)
    print(f"  grupo {grupo.codigo} — {grupo.nombre} ({grupo.proyecto}), 2 integrantes")

    print("\n=== 2. Entrega + evaluación (nota vía dominio) ===")
    entrega = c.entregas.crear_version(gid, 1, "2027-04-10", E.BORRADOR_EN_REVISION.value)
    valoraciones = {"SRS-REQ": Nivel.BUENO, "SRS-EST": Nivel.REGULAR}
    comp = calcular_nota(_rubrica_demo(), valoraciones)
    print("  " + comp.explicacion().replace("\n", "\n  "))

    ev_id = c.evaluaciones.crear(entrega.id, E.BORRADOR_EN_REVISION.value)
    for crit, niv in valoraciones.items():
        c.valoraciones.registrar(ev_id, crit, niv.value, niv.value)
    c.evaluaciones.fijar_nota_sugerida(ev_id, comp.nota)
    c.evaluaciones.validar(ev_id, comp.nota, "2027-04-13")

    print("\n=== 3. Materializar todo a archivos ===")
    c.guardar_manifiesto_entrega(grupo, entrega, [
        {"nombre": "srs.pdf", "tipo_artefacto": "srs", "formato": "pdf"},
    ])
    cv = c.carpeta_version(grupo, 1, 1)
    (cv / "entrega" / "srs.pdf").write_bytes(b"%PDF-1.4 demo")
    c.archivos.agregar(entrega.id, "srs", c.rutas.relativa(cv / "entrega" / "srs.pdf"), "pdf")
    c.guardar_evaluacion_en_archivo(grupo, entrega, {
        "estado": E.EVALUACION_VALIDADA.value, "vigente": True, "fecha": "2027-04-10",
        "nota_sugerida": comp.nota, "nota_final": comp.nota,
        "fecha_validacion": "2027-04-13",
        "valoraciones": {
            k: {"nivel_ia": v.value, "nivel_final": v.value} for k, v in valoraciones.items()
        },
    })
    c.guardar_analisis_en_archivo(grupo, entrega, "srs", {"unidad": "srs", "observaciones": []})
    c.guardar_decisiones_en_archivo(grupo, entrega, {"decisiones": []})
    print(f"  integridad base↔carpetas: {'OK' if c.verificar_integridad().ok else 'FALLA'}")
    c.cerrar()

    print("\n=== 4. Cataclismo: borrar qhaway.db ===")
    (ruta / "qhaway.db").unlink()
    for wal in ruta.glob("qhaway.db-*"):
        wal.unlink()
    print("  base eliminada.")

    print("\n=== 5. Reconstruir desde carpetas (regla de oro) ===")
    rep = reconstruir_desde_carpetas(ruta)
    print("  " + rep.resumen().replace("\n", "\n  "))

    c2 = abrir_ciclo(ruta)
    ev = c2.con.execute("SELECT nota_final FROM evaluacion").fetchone()
    integ = c2.con.execute("SELECT COUNT(*) AS n FROM integrante").fetchone()["n"]
    print(f"\n  nota_final recuperada de archivo: {ev['nota_final']}")
    print(f"  integrantes recuperados: {integ}  (esperado 0: no viven en carpetas, AD-03)")
    c2.cerrar()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Arnés CLI de QHAWAY (Etapa 2).")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for nombre in ("crear", "listar", "demo"):
        p = sub.add_parser(nombre)
        p.add_argument("ruta", type=Path)
    args = parser.parse_args(argv)

    {"crear": cmd_crear, "listar": cmd_listar, "demo": cmd_demo}[args.cmd](args.ruta)
    return 0


if __name__ == "__main__":
    sys.exit(main())
