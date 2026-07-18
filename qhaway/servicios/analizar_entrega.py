"""Caso de uso `analizar_entrega`: el pipeline completo (Arquitectura §6).

Cose todas las capas: extracción + DET (Etapa 3), conector (Etapa 4), cálculo de
nota + máquina de estados (Etapa 1), persistencia (Etapa 2). Ejecuta los seis
pasos como una secuencia de **unidades independientes** (una por artefacto + una
transversal), cada una persistida atómicamente al completarse (AD-04, EVA-10).

Reanudación (EVA-10): el estado de cada unidad vive en la tabla `analisis`.
Reanudar es, simplemente, volver a llamar a `analizar_entrega`: las unidades ya
`completado` se saltan, y el costo de la API no se vuelve a pagar. Ese es el
"test de la desconexión" del criterio de salida.

La construcción fina de los prompts (rol evaluador, calibración-no-plantilla,
cacheo por orden de contexto) es la Etapa 6; acá se arma un prompt mínimo pero
completo en cuanto a los datos que viajan, para que el pipeline sea ejecutable y
testeable de punta a punta.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date

from ..dominio.contenido import ArbolUI, ContenidoDocumento
from ..dominio.deteccion import (
    ChecklistDocumento,
    ConvencionNomenclatura,
    ejecutar_det_documento,
    ejecutar_det_ui,
)
from ..dominio.estados import EstadoEvaluacion, transicionar
from ..dominio.niveles import Nivel
from ..dominio.nota import calcular_nota, valoraciones_con_ausentes
from ..dominio.rubrica import Rubrica
from ..infra import extraer
from ..infra.conector_ia import Conector
from ..infra.db import transaccion

UNIDAD_TRANSVERSAL = "transversal"


@dataclass
class ContextoAnalisis:
    """Todo lo que el pipeline necesita para evaluar una entrega."""

    rubrica: Rubrica
    checklists: dict[str, ChecklistDocumento]
    nomenclatura: ConvencionNomenclatura
    modelo: dict[str, str] = field(default_factory=dict)  # texto homólogo del modelo por tipo
    cantidad_preguntas: int = 10


@dataclass
class ResultadoPipeline:
    evaluacion_id: int
    estado_final: str
    unidades_completadas: list[str]
    unidades_pendientes: list[str]
    nota: int | None
    costo_total: float


def _hoy() -> str:
    return date.today().isoformat()


def analizar_entrega(
    ciclo,
    grupo,
    entrega,
    contexto: ContextoAnalisis,
    conector: Conector,
    *,
    on_progreso: Callable[[str, str], None] | None = None,
    reloj: Callable[[], str] = _hoy,
    forzar_nueva: bool = False,
) -> ResultadoPipeline:
    """Ejecuta (o reanuda) el análisis de una entrega. Idempotente por unidad.

    `forzar_nueva=True` crea siempre una evaluación nueva en vez de reanudar la
    existente (lo usa el arnés de calibración para hacer corridas independientes).
    """
    con = ciclo.con
    progreso = on_progreso or (lambda unidad, estado: None)

    # --- Paso 1: Preparación (crea la evaluación y sus unidades si no existen) ---
    evaluacion_id = _preparar(ciclo, entrega, contexto, reloj, forzar_nueva=forzar_nueva)

    # --- Paso 2-3: Extracción + DET (local), solo de lo aún no procesado ------
    contenidos, ausentes = _extraer_y_detectar(ciclo, entrega, evaluacion_id, contexto, reloj)

    # --- Paso 4-5: procesar unidades pendientes (EVA por artefacto, transversal) ---
    interrumpido = False
    for fila in ciclo.analisis.pendientes(evaluacion_id):
        unidad = fila["unidad"]
        progreso(unidad, "analizando")

        if unidad == UNIDAD_TRANSVERSAL:
            ok = _procesar_transversal(
                ciclo, evaluacion_id, fila["id"], contexto, conector, contenidos, reloj
            )
        else:
            ok = _procesar_artefacto(
                ciclo, evaluacion_id, fila, contexto, conector,
                contenidos, ausentes, reloj,
            )

        if not ok:
            interrumpido = True
            progreso(unidad, "interrumpido")
            break  # agotados los reintentos: se corta y queda reanudable (EVA-10)
        progreso(unidad, "completado")

    # --- Paso 6: Composición (si no quedó nada pendiente) ----------------------
    pendientes = [f["unidad"] for f in ciclo.analisis.pendientes(evaluacion_id)]
    completadas = [
        f["unidad"] for f in ciclo.analisis.unidades(evaluacion_id)
        if f["estado"] == "completado"
    ]
    nota = None

    if interrumpido or pendientes:
        if not forzar_nueva:
            _transicionar(con, ciclo, entrega.id, EstadoEvaluacion.ANALISIS_INTERRUMPIDO)
        estado_final = EstadoEvaluacion.ANALISIS_INTERRUMPIDO.value
    else:
        nota = _componer(ciclo, evaluacion_id, contexto)
        if not forzar_nueva:
            _transicionar(con, ciclo, entrega.id, EstadoEvaluacion.BORRADOR_EN_REVISION)
        estado_final = EstadoEvaluacion.BORRADOR_EN_REVISION.value

    return ResultadoPipeline(
        evaluacion_id=evaluacion_id,
        estado_final=estado_final,
        unidades_completadas=completadas,
        unidades_pendientes=pendientes,
        nota=nota,
        costo_total=ciclo.consumos.total_costo(),
    )


# ----------------------------------------------------------------------------
# Paso 1 — Preparación
# ----------------------------------------------------------------------------
def _preparar(ciclo, entrega, contexto: ContextoAnalisis, reloj, *, forzar_nueva=False) -> int:
    """Crea la evaluación y sus unidades (o reanuda una existente)."""
    # ¿Ya hay una evaluación activa (no validada) para esta entrega? -> reanudar.
    if not forzar_nueva:
        fila = ciclo.con.execute(
            "SELECT id FROM evaluacion WHERE entrega_id = ? AND nota_final IS NULL "
            "ORDER BY id DESC LIMIT 1",
            (entrega.id,),
        ).fetchone()
        if fila is not None:
            # Reanudación: de análisis_interrumpido se vuelve a analizando (EVA-10).
            _transicionar(ciclo.con, ciclo, entrega.id, EstadoEvaluacion.ANALIZANDO)
            return int(fila["id"])

    with transaccion(ciclo.con):
        evaluacion_id = ciclo.evaluaciones.crear(
            entrega.id, EstadoEvaluacion.ANALIZANDO.value
        )
        # Una unidad por artefacto de la rúbrica + la transversal.
        for artefacto in _artefactos_rubrica(contexto.rubrica):
            ciclo.analisis.crear_unidad(evaluacion_id, artefacto, reloj())
        ciclo.analisis.crear_unidad(evaluacion_id, UNIDAD_TRANSVERSAL, reloj())

    # Las corridas de calibración no alteran el estado de la entrega (medición lateral).
    if not forzar_nueva:
        _transicionar(ciclo.con, ciclo, entrega.id, EstadoEvaluacion.ANALIZANDO)
    return evaluacion_id


# ----------------------------------------------------------------------------
# Paso 2-3 — Extracción + DET
# ----------------------------------------------------------------------------
def _extraer_y_detectar(ciclo, entrega, evaluacion_id, contexto, reloj):
    """Extrae los archivos y corre DET; devuelve (contenidos_por_tipo, ausentes)."""
    contenidos: dict[str, object] = {}
    ausentes: set[str] = set()

    tipos_rubrica = set(_artefactos_rubrica(contexto.rubrica))
    presentes: set[str] = set()

    for fila in ciclo.archivos.de_entrega(entrega.id):
        tipo = fila["tipo_artefacto"]
        ruta = ciclo.rutas.absoluta(fila["ruta_relativa"])
        res = extraer(ruta, tipo)
        if res.ok:
            contenidos[tipo] = res.contenido
            presentes.add(tipo)
        # ING-06: archivo problemático = artefacto ausente para el análisis (ING-05)

    ausentes = tipos_rubrica - presentes

    # DET local sobre lo presente (solo si aún no hay hallazgos persistidos).
    ya_corrio = bool(ciclo.hallazgos.de_evaluacion(evaluacion_id))
    if not ya_corrio:
        with transaccion(ciclo.con):
            for tipo, contenido in contenidos.items():
                if isinstance(contenido, ArbolUI):
                    hallazgos = ejecutar_det_ui(contenido, contexto.nomenclatura)
                else:
                    checklist = contexto.checklists.get(tipo)
                    hallazgos = (
                        ejecutar_det_documento(contenido, checklist) if checklist else []
                    )
                for h in hallazgos:
                    ciclo.hallazgos.registrar(evaluacion_id, h.tipo, h.artefacto, h.detalle)
    return contenidos, ausentes


# ----------------------------------------------------------------------------
# Paso 4 — EVA por artefacto
# ----------------------------------------------------------------------------
def _procesar_artefacto(
    ciclo, evaluacion_id, fila, contexto, conector, contenidos, ausentes, reloj
) -> bool:
    """Procesa una unidad de artefacto. Devuelve False si quedó pendiente (corte)."""
    artefacto = fila["unidad"]
    seccion = contexto.rubrica.seccion(artefacto)
    criterios = {c.id for c in seccion.criterios} if seccion else set()

    # Artefacto ausente: Insuficiente sin llamada (EVA-05). No corta el pipeline.
    if artefacto in ausentes or artefacto not in contenidos:
        with transaccion(ciclo.con):
            for cid in criterios:
                ciclo.valoraciones.registrar(evaluacion_id, cid, Nivel.INSUFICIENTE.value, None)
            ciclo.analisis.marcar_completado(fila["id"], reloj())
        return True

    # Artefacto presente: llamada a la IA.
    hallazgos = ciclo.hallazgos.de_evaluacion(evaluacion_id)
    prompt = _prompt_artefacto(artefacto, seccion, contenidos[artefacto], contexto, hallazgos)
    resultado = conector.analizar_artefacto(prompt, criterios)

    # Consumo primero (MON-01): se registra aunque la unidad quede pendiente.
    _registrar_consumo(ciclo, fila["id"], resultado)

    if not resultado.completado:
        ciclo.analisis.incrementar_intento(fila["id"])
        return False

    # Persistencia atómica de la unidad completada (EVA-10, RNF-06).
    r = resultado.resultado
    with transaccion(ciclo.con):
        for v in r.valoraciones:
            ciclo.valoraciones.registrar(evaluacion_id, v.criterio_id, v.nivel.value, None)
        for o in r.observaciones:
            ciclo.elementos.crear(
                evaluacion_id, "observacion",
                criterio_id=o.criterio_id,
                contenido_original=o.contenido,
                referencia=o.referencia.ubicacion,
            )
        ciclo.analisis.marcar_completado(fila["id"], reloj())
    return True


# ----------------------------------------------------------------------------
# Paso 5 — Pasada transversal
# ----------------------------------------------------------------------------
def _procesar_transversal(
    ciclo, evaluacion_id, analisis_id, contexto, conector, contenidos, reloj
) -> bool:
    prompt = _prompt_transversal(contexto, contenidos)
    resultado = conector.analizar_transversal(prompt)
    _registrar_consumo(ciclo, analisis_id, resultado)

    if not resultado.completado:
        ciclo.analisis.incrementar_intento(analisis_id)
        return False

    r = resultado.resultado
    with transaccion(ciclo.con):
        for c in r.consistencias:
            ciclo.elementos.crear(
                evaluacion_id, "observacion",
                contenido_original=c.hallazgo, referencia=c.elemento,
            )
        for p in r.preguntas_defensa:
            ciclo.elementos.crear(
                evaluacion_id, "pregunta_defensa",
                contenido_original=p.pregunta, referencia=p.elemento,
            )
        for s in r.senales:
            ciclo.elementos.crear(
                evaluacion_id, "senal", contenido_original=s.descripcion,
            )
        ciclo.analisis.marcar_completado(analisis_id, reloj())
    return True


# ----------------------------------------------------------------------------
# Paso 6 — Composición de la nota
# ----------------------------------------------------------------------------
def _componer(ciclo, evaluacion_id, contexto) -> int:
    """Calcula la nota sugerida desde las valoraciones de la IA (dominio.nota)."""
    almacenadas = ciclo.valoraciones.de_evaluacion(evaluacion_id)
    valoraciones = {
        cid: Nivel(v["nivel_ia"]) for cid, v in almacenadas.items() if v["nivel_ia"]
    }
    comp = calcular_nota(contexto.rubrica, valoraciones)
    with transaccion(ciclo.con):
        ciclo.evaluaciones.fijar_nota_sugerida(evaluacion_id, comp.nota)
    return comp.nota


# ----------------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------------
def _artefactos_rubrica(rubrica: Rubrica) -> list[str]:
    return [s.artefacto for s in rubrica.secciones if s.artefacto != "transversal"]


def _registrar_consumo(ciclo, analisis_id, resultado) -> None:
    with transaccion(ciclo.con):
        for c in resultado.consumos:
            ciclo.consumos.registrar(
                analisis_id,
                tokens_entrada=c.tokens_entrada,
                tokens_salida=c.tokens_salida,
                tokens_cache=c.tokens_cache,
                costo_estimado=c.costo_estimado,
                reintento=c.reintento,
                fecha=c.fecha,
            )


def _transicionar(con, ciclo, entrega_id, hasta):
    """Transición de estado de la entrega vía la máquina del dominio."""
    fila = con.execute("SELECT estado FROM entrega WHERE id = ?", (entrega_id,)).fetchone()
    desde = EstadoEvaluacion(fila["estado"])
    if desde == hasta:
        return
    nuevo = transicionar(desde, hasta)  # levanta si la máquina no lo permite
    with transaccion(con):
        ciclo.entregas.actualizar_estado(entrega_id, nuevo.value)


# ----------------------------------------------------------------------------
# Prompts (plantillas versionadas de infra.prompts, AD-07)
# ----------------------------------------------------------------------------
def _texto_contenido(contenido) -> str:
    if isinstance(contenido, ContenidoDocumento):
        return contenido.texto[:8000]
    if isinstance(contenido, ArbolUI):
        return "\n".join(f"{n.clase} {n.nombre or ''}" for n in contenido.widgets())
    return ""


def _prompt_artefacto(artefacto, seccion, contenido, contexto, hallazgos) -> str:
    from ..infra.prompts import PLANTILLAS

    criterios = [
        {"id": c.id, "descripcion": c.descripcion, "niveles": c.niveles}
        for c in seccion.criterios
    ]
    det = [dict(h) for h in hallazgos if h["artefacto"] == artefacto]
    ensamblado = PLANTILLAS["analisis_artefacto"].render({
        "artefacto": artefacto,
        "criterios": criterios,
        "modelo": contexto.modelo.get(artefacto, "(sin proyecto modelo cargado)"),
        "hallazgos_det": det,
        "entrega": _texto_contenido(contenido),
    })
    return ensamblado.texto


def _prompt_transversal(contexto, contenidos) -> str:
    from ..infra.prompts import PLANTILLAS

    ensamblado = PLANTILLAS["analisis_transversal"].render({
        "entrega": {t: _texto_contenido(c) for t, c in contenidos.items()},
        "cantidad_preguntas": contexto.cantidad_preguntas,
    })
    return ensamblado.texto
