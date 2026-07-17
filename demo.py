"""Demo del dominio puro: muestra la composición trazable de la nota.

No es parte del sistema; es una demostración de que la Etapa 1 funciona de punta
a punta. Correr con:  python3 demo.py
"""

from __future__ import annotations

from qhaway.dominio import Nivel, Rubrica, calcular_nota
from qhaway.dominio.estados import EstadoEvaluacion as E, Evaluacion


def rubrica_demo(criterios, tope=6):
    niveles = {n.value: "..." for n in Nivel}
    datos = {
        "rubrica": {
            "nombre": "demo",
            "escala": {"tope_por_critico": tope},
            "secciones": [
                {
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
            ],
        }
    }
    return Rubrica.desde_dict(datos, artefactos_requeridos=frozenset())


def separador(titulo):
    print("\n" + "=" * 64)
    print(titulo)
    print("=" * 64)


separador("Apéndice B — Ejemplo 1 (44/6 = 7,33 -> 7)")
r1 = rubrica_demo([("PRE-IDN", 3, False), ("PRE-PRO", 1, False), ("PRE-COM", 2, False)])
c1 = calcular_nota(
    r1, {"PRE-IDN": Nivel.BUENO, "PRE-PRO": Nivel.EXCELENTE, "PRE-COM": Nivel.REGULAR}
)
print(c1.explicacion())

separador("Apéndice B — Ejemplo 2 (crítico Insuficiente, tope 6)")
r2 = rubrica_demo([("A", 3, False), ("B", 1, False), ("C", 2, True)])
c2 = calcular_nota(r2, {"A": Nivel.BUENO, "B": Nivel.EXCELENTE, "C": Nivel.INSUFICIENTE})
print(c2.explicacion())

separador("Mitad exacta (6,5 -> 7, regla EVA-05 v1.1)")
r3 = rubrica_demo([("A", 1, False), ("B", 1, False)])
c3 = calcular_nota(r3, {"A": Nivel.BUENO, "B": Nivel.REGULAR})
print(c3.explicacion())

separador("Máquina de estados — camino feliz")
ev = Evaluacion()
print("inicio:", ev.estado.value)
for destino, guards in [
    (E.ENTREGA_CARGADA, {}),
    (E.ANALIZANDO, {}),
    (E.BORRADOR_EN_REVISION, {}),
    (E.EVALUACION_VALIDADA, {"elementos_pendientes": 0, "nota_final_confirmada": True}),
    (E.INFORME_EXPORTADO, {}),
]:
    ev.a(destino, **guards)
    print("  ->", ev.estado.value)
