"""Conector de IA (AD-06): interfaz neutral, reintentos, validación, consumo.

Patrón puerto-y-adaptador: la máquina de reintentos + validación + registro de
consumo vive en la clase base `Conector` (el puerto); cada adaptador solo
implementa `_llamar` (la llamada de bajo nivel). Consecuencia: el `ConectorFalso`
ejercita TODA la lógica que importa —reintentos (IEX-02), validación (EVA-13),
consumo (MON-01)— sin gastar un token, y el `ConectorAnthropic` reusa esa misma
lógica cambiando solo cómo se hace la llamada real.

Los servicios (Etapa 5) no conocen el SDK: hablan con `Conector`. Cambiar de
proveedor (Fase 4) es escribir otro adaptador (RNF-07).
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone

from ..dominio.esquema_salidas import (
    Validacion,
    parsear_json,
    validar_artefacto,
    validar_transversal,
)


# ----------------------------------------------------------------------------
# Errores del conector
# ----------------------------------------------------------------------------
class ErrorTransitorio(Exception):
    """Fallo reintentable: red, timeout, límite de tasa, 5xx."""


# ----------------------------------------------------------------------------
# Respuesta cruda y consumo (MON-01)
# ----------------------------------------------------------------------------
@dataclass(frozen=True)
class RespuestaCruda:
    """Lo que devuelve una llamada de bajo nivel, antes de validar."""

    texto: str
    tokens_entrada: int = 0
    tokens_salida: int = 0
    tokens_cache_escritura: int = 0
    tokens_cache_lectura: int = 0


@dataclass(frozen=True)
class TablaPrecios:
    """Precios en USD por millón de tokens (MON-01, configurable)."""

    entrada: float
    salida: float
    cache_escritura: float
    cache_lectura: float

    def costo(self, r: RespuestaCruda) -> float:
        return (
            r.tokens_entrada * self.entrada
            + r.tokens_salida * self.salida
            + r.tokens_cache_escritura * self.cache_escritura
            + r.tokens_cache_lectura * self.cache_lectura
        ) / 1_000_000


# Precios verificados en el spike (jul-2026) para el modelo por defecto del MVP.
PRECIOS: dict[str, TablaPrecios] = {
    "claude-sonnet-4-6": TablaPrecios(
        entrada=3.0, salida=15.0, cache_escritura=3.75, cache_lectura=0.30
    ),
}


@dataclass(frozen=True)
class RegistroConsumo:
    """Consumo de una llamada (MON-01), listo para persistir en consumo_api."""

    tokens_entrada: int
    tokens_salida: int
    tokens_cache: int
    costo_estimado: float
    reintento: int
    fecha: str


# ----------------------------------------------------------------------------
# Política de reintentos
# ----------------------------------------------------------------------------
@dataclass(frozen=True)
class PoliticaReintentos:
    """Reintentos con retroceso exponencial (IEX-02). Por defecto 3 reintentos."""

    reintentos: int = 3           # intentos totales = reintentos + 1
    base_espera: float = 0.5      # segundos; espera = base_espera * 2**intento


# ----------------------------------------------------------------------------
# Resultado de una llamada de alto nivel
# ----------------------------------------------------------------------------
@dataclass(frozen=True)
class ResultadoLlamada:
    """Resultado de analizar una unidad: completado o pendiente (EVA-13)."""

    estado: str                          # completado | pendiente
    resultado: object | None = None      # ResultadoArtefacto | ResultadoTransversal
    consumos: tuple[RegistroConsumo, ...] = ()
    errores: tuple[str, ...] = ()

    @property
    def completado(self) -> bool:
        return self.estado == "completado"

    @property
    def costo_total(self) -> float:
        return sum(c.costo_estimado for c in self.consumos)


# ----------------------------------------------------------------------------
# Conector (puerto) — máquina de reintentos + validación + consumo
# ----------------------------------------------------------------------------
def _ahora_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Conector(ABC):
    def __init__(
        self,
        modelo: str = "claude-sonnet-4-6",
        *,
        politica: PoliticaReintentos = PoliticaReintentos(),
        precios: TablaPrecios | None = None,
        dormir: Callable[[float], None] = time.sleep,
        reloj: Callable[[], str] = _ahora_iso,
    ) -> None:
        self.modelo = modelo
        self.politica = politica
        self.precios = precios or PRECIOS.get(modelo, PRECIOS["claude-sonnet-4-6"])
        self._dormir = dormir
        self._reloj = reloj

    @abstractmethod
    def _llamar(self, prompt: str) -> RespuestaCruda:
        """Llamada de bajo nivel. Levanta ErrorTransitorio si es reintentable."""

    # --- Interfaz neutral que usan los servicios --------------------------
    def analizar_artefacto(self, prompt: str, criterios_esperados: set[str]) -> ResultadoLlamada:
        return self._ejecutar(prompt, lambda d: validar_artefacto(d, criterios_esperados))

    def analizar_transversal(self, prompt: str) -> ResultadoLlamada:
        return self._ejecutar(prompt, validar_transversal)

    # --- Máquina de reintentos (compartida) -------------------------------
    def _ejecutar(
        self, prompt: str, validar: Callable[[dict], Validacion]
    ) -> ResultadoLlamada:
        consumos: list[RegistroConsumo] = []
        ultimos_errores: tuple[str, ...] = ()

        for intento in range(self.politica.reintentos + 1):
            try:
                cruda = self._llamar(prompt)
            except ErrorTransitorio as e:
                # Falla de red: no hubo tokens, pero se registra el intento (MON-01).
                consumos.append(
                    RegistroConsumo(0, 0, 0, 0.0, intento, self._reloj())
                )
                ultimos_errores = (f"Error transitorio: {e}",)
                self._esperar(intento)
                continue

            # Hubo respuesta: cuesta tokens aunque sea inválida -> se registra.
            consumos.append(self._registrar(cruda, intento))

            data, err = parsear_json(cruda.texto)
            if err is not None:
                ultimos_errores = (err,)
                self._esperar(intento)
                continue

            validacion = validar(data)
            if validacion.ok:
                return ResultadoLlamada(
                    estado="completado",
                    resultado=validacion.resultado,
                    consumos=tuple(consumos),
                )
            ultimos_errores = validacion.errores
            self._esperar(intento)

        # Agotados los reintentos: unidad pendiente (EVA-13), reanudable (EVA-10).
        return ResultadoLlamada(
            estado="pendiente", consumos=tuple(consumos), errores=ultimos_errores
        )

    def _registrar(self, cruda: RespuestaCruda, intento: int) -> RegistroConsumo:
        return RegistroConsumo(
            tokens_entrada=cruda.tokens_entrada,
            tokens_salida=cruda.tokens_salida,
            tokens_cache=cruda.tokens_cache_escritura + cruda.tokens_cache_lectura,
            costo_estimado=self.precios.costo(cruda),
            reintento=intento,
            fecha=self._reloj(),
        )

    def _esperar(self, intento: int) -> None:
        if intento < self.politica.reintentos:  # no dormir tras el último intento
            self._dormir(self.politica.base_espera * (2 ** intento))


# ----------------------------------------------------------------------------
# ConectorFalso (para tests, sin tokens)
# ----------------------------------------------------------------------------
class ConectorFalso(Conector):
    """Reproduce un guion de respuestas. Cada elemento del guion es:

    * un `str` -> se devuelve como texto (con tokens por defecto),
    * un `RespuestaCruda` -> se devuelve tal cual,
    * una `Exception` -> se levanta (simula falla de red si es ErrorTransitorio).

    Permite scriptear: válido a la primera, inválido-luego-válido, todo inválido
    (-> pendiente), red-caída-luego-válido, etc.
    """

    def __init__(self, guion: list, **kw) -> None:
        super().__init__(**kw)
        self._guion = list(guion)
        self.llamadas = 0

    def _llamar(self, prompt: str) -> RespuestaCruda:
        self.llamadas += 1
        if not self._guion:
            raise ErrorTransitorio("guion agotado")
        item = self._guion.pop(0)
        if isinstance(item, Exception):
            raise item
        if isinstance(item, RespuestaCruda):
            return item
        return RespuestaCruda(texto=str(item), tokens_entrada=100, tokens_salida=50)


# ----------------------------------------------------------------------------
# ConectorAnthropic (real) — no se ejercita en tests (requiere clave y red)
# ----------------------------------------------------------------------------
class ConectorAnthropic(Conector):
    """Adaptador real sobre el SDK de Anthropic.

    El SDK se importa perezosamente para que el resto del sistema no dependa de
    él (los tests corren sin el SDK instalado). El marcado de caché (EVA-12) se
    aplica a los bloques estables del prompt cuando se los pasa por separado; en
    esta etapa la construcción fina del prompt es responsabilidad de Etapa 6.
    """

    def __init__(self, api_key: str, *, max_tokens: int = 4096, **kw) -> None:
        super().__init__(**kw)
        self._api_key = api_key
        self._max_tokens = max_tokens
        self._cliente = None

    def _asegurar_cliente(self):
        if self._cliente is None:
            import anthropic  # perezoso
            self._cliente = anthropic.Anthropic(api_key=self._api_key)
        return self._cliente

    def _llamar(self, prompt: str) -> RespuestaCruda:
        cliente = self._asegurar_cliente()
        try:
            import anthropic
            resp = cliente.messages.create(
                model=self.modelo,
                max_tokens=self._max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as e:  # errores de red/tasa -> reintentables
            # Los errores de API del SDK se tratan como transitorios; un error de
            # autenticación real se manifestará como pendiente tras los reintentos
            # y se diagnostica mejor con probar_conexion (CFG-08).
            raise ErrorTransitorio(str(e)) from e

        texto = "".join(
            b.text for b in resp.content if getattr(b, "type", None) == "text"
        )
        u = resp.usage
        return RespuestaCruda(
            texto=texto,
            tokens_entrada=getattr(u, "input_tokens", 0),
            tokens_salida=getattr(u, "output_tokens", 0),
            tokens_cache_escritura=getattr(u, "cache_creation_input_tokens", 0) or 0,
            tokens_cache_lectura=getattr(u, "cache_read_input_tokens", 0) or 0,
        )
