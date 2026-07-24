"""Vistas de Ayuda y Acerca de (IEX-01).

Contenido estático en HTML, renderizado con QTextBrowser (soporta formato rico y
scroll sin dependencias extra). La ayuda describe el flujo real de trabajo del
docente; el "Acerca de" reúne identidad, licencia y política de datos.
"""

from __future__ import annotations

from PySide6.QtWidgets import QTextBrowser, QVBoxLayout, QWidget

from ..version import (
    AUTOR,
    DESCRIPCION,
    INSTITUCION,
    LICENCIA,
    MATERIA,
    MODELO_IA,
    NOMBRE,
    PRINCIPIO,
    SIGNIFICADO,
    __version__,
)
from .tema import AZUL, BORDE, INK, PURPURA, SUPERFICIE, TENUE

_CSS = f"""
<style>
  body {{ font-family: "Segoe UI", Arial, sans-serif; color: {INK}; font-size: 10.5pt;
         line-height: 1.55; }}
  h1 {{ font-size: 15pt; color: {INK}; margin: 0 0 2px 0; }}
  h2 {{ font-size: 12pt; color: {AZUL}; margin: 18px 0 4px 0;
        border-bottom: 1px solid {BORDE}; padding-bottom: 3px; }}
  h3 {{ font-size: 10.5pt; color: {PURPURA}; margin: 12px 0 2px 0; }}
  p  {{ margin: 4px 0 8px 0; }}
  .sub {{ color: {TENUE}; font-size: 10pt; margin-bottom: 10px; }}
  .nota {{ background: #F0F4FA; border-left: 3px solid {AZUL};
           padding: 8px 12px; margin: 10px 0; }}
  .aviso {{ background: #FDF3F2; border-left: 3px solid #C0392B;
            padding: 8px 12px; margin: 10px 0; }}
  ol, ul {{ margin: 4px 0 8px 18px; }}
  li {{ margin: 3px 0; }}
  code {{ background: #EEF1F6; padding: 1px 5px; border-radius: 3px;
          font-family: Consolas, monospace; font-size: 9.5pt; }}
  .paso {{ font-weight: 600; color: {INK}; }}
</style>
"""

_AYUDA = _CSS + f"""
<h1>Cómo usar {NOMBRE}</h1>
<p class="sub">{DESCRIPCION}. {PRINCIPIO}</p>

<div class="nota">
  <b>El flujo en una línea:</b> configurar el ciclo una vez → dar de alta los grupos →
  por cada grupo: cargar entrega, analizar, revisar, validar y exportar.
</div>

<h2>1. Preparar el ciclo (una sola vez)</h2>
<p>En la pestaña <b>Configuración</b>:</p>
<ol>
  <li><span class="paso">Clave de API</span> — pegala y presioná <i>Guardar clave</i>. Se
      almacena fuera del repositorio, en la configuración del sistema. Usá
      <i>Probar conexión</i> para verificar que responde.</li>
  <li><span class="paso">Rúbrica</span> — cargá tu archivo <code>.yaml</code>. Si tiene un
      error, {NOMBRE} lo rechaza y te dice por qué: una rúbrica inválida nunca
      entra al sistema.</li>
  <li><span class="paso">Parámetros</span> — nombre del ciclo y cantidad de preguntas de
      defensa a generar.</li>
</ol>

<h2>2. Dar de alta los grupos</h2>
<p>En la pestaña <b>Grupos</b>: completá código, nombre y proyecto, y presioná
<i>Alta de grupo</i>. Con un grupo seleccionado podés agregar integrantes o
archivarlo (archivar conserva todo el historial, no borra nada).</p>
<div class="nota">Los nombres de los integrantes viven <b>solo en tu equipo</b>: nunca
se envían a la API.</div>

<h2>3. Trabajar un grupo</h2>
<p>Seleccioná el grupo y presioná <b>Abrir flujo del grupo →</b>. Se abre una ventana
con las cuatro etapas en orden.</p>

<h3>3.1 Cargar la entrega</h3>
<ol>
  <li>Presioná <i>Elegir archivos…</i> y seleccioná los documentos del grupo.</li>
  <li><span class="paso">Revisá la columna «Tipo».</span> {NOMBRE} sugiere el tipo leyendo
      el contenido de cada archivo, pero la última palabra es tuya: corregilo si
      hace falta.</li>
  <li>Presioná <i>Cargar entrega</i>.</li>
</ol>
<div class="aviso">
  <b>Lo más importante de toda la carga:</b> que cada archivo tenga el tipo correcto
  (presentación, SRS, diseño funcional o UI). Si marcás mal un documento, se
  evalúa como si fuera otra cosa y el resultado será incorrecto — aunque el
  análisis se complete sin errores. Dos archivos no pueden compartir tipo: si
  ocurre, {NOMBRE} te avisa antes de cargar.
</div>

<h3>3.2 Analizar</h3>
<p>Presioná <b>Analizar entrega vigente</b>. La barra avanza artefacto por artefacto
y termina con una pasada de consistencia entre todos.</p>
<ul>
  <li>Si se interrumpe (corte de red, respuesta inválida), {NOMBRE} te dice qué unidad
      falló y por qué. <b>El progreso se guarda</b>: volver a presionar <i>Analizar</i>
      retoma desde donde quedó, sin repetir ni volver a pagar lo ya hecho.</li>
  <li>Cada llamada queda registrada en la pestaña <b>Consumo</b>.</li>
</ul>

<h3>3.3 Revisar el borrador</h3>
<p>Presioná <b>Abrir revisión</b>. Ahí está todo lo que propuso la IA: observaciones,
preguntas de defensa y señales. Sobre cada elemento podés:</p>
<ul>
  <li><b>Aceptar</b> — lo incorporás tal cual.</li>
  <li><b>Editar</b> — lo reescribís con tus palabras (se guardan ambas versiones).</li>
  <li><b>Descartar</b> — no aparece en ninguna salida.</li>
</ul>
<p>Cuando no queden elementos pendientes, elegí la <b>nota final</b> (el selector
arranca en la sugerida) y presioná <i>Fijar nota final</i>. Recién entonces se
habilita <b>Validar evaluación</b>.</p>

<h3>3.4 Exportar</h3>
<p>Con la evaluación validada, <b>Exportar informe + guía</b> genera dos PDF:</p>
<ul>
  <li><b>Informe de devolución</b> — para el grupo. Incluye observaciones y nota; no
      lleva el cuestionario, ni las señales, ni marcas de qué escribió la IA.</li>
  <li><b>Guía de defensa</b> — solo para vos: el cuestionario y las señales a indagar.</li>
</ul>

<h2>4. Consultar lo ya evaluado</h2>
<p>La pestaña <b>Evaluados</b> lista las evaluaciones validadas. Podés
<i>Ver detalle</i> (en modo lectura, sin riesgo de modificar) o
<i>Reexportar</i> los PDF cuando los necesites, sin recargar la entrega.</p>

<h2>5. Vigilar el gasto</h2>
<p>La pestaña <b>Consumo</b> muestra el gasto del mes contra tu presupuesto y el
histórico mensual. Al pasar el umbral aparece un aviso, pero {NOMBRE}
<b>nunca bloquea</b> un análisis por presupuesto: la decisión es tuya.</p>

<h2>Preguntas frecuentes</h2>
<h3>¿Se pierde lo que revisé si cierro la aplicación?</h3>
<p>No. Todo queda guardado en el ciclo, incluidas tus decisiones sobre cada
elemento. Al reabrir el flujo de un grupo, {NOMBRE} retoma la evaluación en curso.</p>
<h3>¿Puedo evaluar sin conexión?</h3>
<p>Las verificaciones automáticas (estructura de documentos, nomenclatura de la
interfaz) funcionan sin IA. La valoración por criterios y las preguntas de
defensa sí requieren conexión.</p>
<h3>El grupo entregó una versión corregida, ¿qué hago?</h3>
<p>Cargá la entrega de nuevo: se guarda como una versión nueva y la anterior queda
en el historial.</p>
"""

_ACERCA = _CSS + f"""
<h1>{NOMBRE} <span style="color:{TENUE}; font-size:11pt;">v{__version__}</span></h1>
<p class="sub">{DESCRIPCION}<br>{SIGNIFICADO}</p>

<div class="nota"><b>{PRINCIPIO}</b><br>
{NOMBRE} redacta un borrador de corrección; ninguna salida llega al grupo sin
pasar por el criterio del docente.</div>

<h2>El proyecto</h2>
<p>Herramienta de escritorio que asiste la corrección de proyectos grupales:
analiza las entregas contra la rúbrica de la cátedra y produce un borrador con
observaciones, una nota trazable y un cuestionario de defensa.</p>
<ul>
  <li><b>Autor:</b> {AUTOR}</li>
  <li><b>Institución:</b> {INSTITUCION} — {MATERIA}</li>
  <li><b>Licencia:</b> {LICENCIA} (código abierto)</li>
  <li><b>Modelo de IA:</b> {MODELO_IA}</li>
</ul>

<h2>Tus datos</h2>
<ul>
  <li>Las entregas y sus evaluaciones se guardan <b>en tu equipo</b>, dentro de la
      carpeta del ciclo.</li>
  <li>Para analizar, el contenido de los documentos se envía a la API del modelo.</li>
  <li>Los <b>nombres de los integrantes nunca se envían</b>: viven solo en la base local.</li>
  <li>La clave de API se guarda en la configuración del sistema, fuera del proyecto.</li>
</ul>
<p>Se recomienda informar a alumnos e institución sobre el uso de IA en la
corrección, como parte de la transparencia del proceso (Ley 25.326).</p>

<h2>Cómo trabaja</h2>
<ul>
  <li><b>Verificaciones automáticas</b> — estructura de los documentos y nomenclatura
      de la interfaz, sin usar IA.</li>
  <li><b>Valoración por criterios</b> — cada criterio de tu rúbrica recibe un nivel con
      su justificación; la nota se calcula a partir de esos niveles.</li>
  <li><b>Consistencia entre artefactos</b> — trazabilidad entre requisitos, diseño e
      interfaz.</li>
  <li><b>Trazabilidad de la revisión</b> — se conserva lo que propuso la IA y lo que
      decidiste vos.</li>
</ul>
"""


class _PaginaTexto(QWidget):
    """Contenedor simple con un QTextBrowser de solo lectura."""

    def __init__(self, html: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.texto = QTextBrowser(self)
        self.texto.setOpenExternalLinks(True)
        self.texto.setHtml(html)
        self.texto.setStyleSheet(
            f"QTextBrowser {{ background: {SUPERFICIE}; border: 1px solid {BORDE};"
            f" border-radius: 10px; padding: 14px; }}"
        )
        layout.addWidget(self.texto)


class VistaAyuda(_PaginaTexto):
    """Instrucciones de uso paso a paso."""

    def __init__(self, parent=None):
        super().__init__(_AYUDA, parent)


class VistaAcercaDe(_PaginaTexto):
    """Identidad del proyecto, licencia y política de datos."""

    def __init__(self, parent=None):
        super().__init__(_ACERCA, parent)
