<p align="center">
  <img src="qhaway-icono.png" width="96" alt="Ícono de QHAWAY">
</p>

<h1 align="center">QHAWAY</h1>

<p align="center">
  Asistente de corrección de proyectos grupales de ingeniería de software.<br>
  De docentes, para docentes.
</p>

<p align="center">
  <img alt="Licencia" src="https://img.shields.io/badge/licencia-MIT-blue.svg">
  <img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-blue.svg">
  <img alt="UI" src="https://img.shields.io/badge/UI-PySide6-41cd52.svg">
  <img alt="Estado" src="https://img.shields.io/badge/estado-en%20desarrollo-yellow.svg">
</p>

---

**QHAWAY** (del quechua *qhaway*: observar, examinar) es una aplicación de escritorio que asiste al
docente en la evaluación de proyectos grupales: analiza las entregas de los alumnos (SRS, diseño
funcional, interfaz, presentación) contra una rúbrica y un proyecto modelo de referencia, y produce
un borrador de corrección completo — observaciones fundamentadas por criterio, verificación de
completitud, análisis de consistencia entre artefactos, una nota sugerida trazable y un cuestionario
de defensa personalizado para la exposición oral.

Corregir a fondo un proyecto grupal multi-artefacto lleva alrededor de una hora, y lo más costoso no
es detectar los problemas sino redactar la devolución. QHAWAY invierte esa ecuación: el análisis
exhaustivo lo hace la herramienta; el docente dedica su tiempo a validar, ajustar y enriquecer.

## Principio rector

**La IA propone, el docente decide.** QHAWAY nunca asigna una calificación de forma autónoma.
Toda observación es un borrador que el docente acepta, edita o descarta antes de que llegue al
grupo.

## Características

- **Gestión de ciclos y grupos**: alta de ciclo lectivo, grupos e integrantes (los nombres viven
  solo en la base local, nunca se envían a la API).
- **Carga de entregas**: extracción de contenido de PDF, Word y proyectos de Qt Designer.
- **Análisis asistido por IA**: valoraciones por criterio contra una rúbrica y un proyecto modelo,
  con detección de inconsistencias entre artefactos.
- **Revisión editable**: cada observación y cada nota sugerida se acepta, edita o descarta antes de
  validar la corrección.
- **Exportación a PDF**: informe de devolución y guía de preguntas de defensa oral.
- **Empaquetado standalone**: se distribuye como aplicación de escritorio (PyInstaller), sin que el
  usuario final necesite instalar Python.

## Instalación (desde el código fuente)

Requisitos: Python 3.11+ y, en Windows, el runtime GTK3 (para WeasyPrint).

```bash
git clone https://github.com/SiliconValey/QHAWAY.git
cd QHAWAY
python -m venv venv
# Windows:  venv\Scripts\activate     Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
python -m pytest -q            # debería dar toda la suite en verde
```

En Windows, si al generar un PDF aparece `cannot load library 'libgobject-2.0-0'`, instalá el
[GTK3-Runtime para Windows](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases)
y reiniciá la terminal.

### Configurar la clave de API

```bash
python qhaway_cli.py guardar-clave      # pega tu clave de API (no se muestra)
python qhaway_cli.py probar-conexion    # verifica la conexión
```

La clave se guarda en `%APPDATA%/qhaway` (Windows) o `~/.config/qhaway` (Linux), **fuera del
repositorio**. Copiá `config-ejemplo/*.yaml` a la carpeta `config/` de tu ciclo y reemplazá los
valores por los de tu cátedra (checklist real, tabla de nomenclatura).

### Ejecutar

```bash
python qhaway_app.py
```

## Uso (flujo del docente)

1. Crear el ciclo lectivo y dar de alta los grupos.
2. Cargar la rúbrica, el proyecto modelo y los checklists (una vez por ciclo).
3. Por cada grupo: cargar la entrega → analizar → revisar el borrador (aceptar/editar/descartar
   cada elemento, ajustar la nota) → validar.
4. Exportar el informe de devolución y la guía de defensa (PDF).

## Manejo de datos y privacidad

QHAWAY envía a la API de Anthropic el **contenido de las entregas** para su análisis. Los nombres
de los integrantes de los grupos viven solo en la base local y nunca se envían a la API. La clave
de API nunca se guarda en el repositorio ni en los informes. Ver la política completa en
[`docs/md/qhaway-politica-datos.md`](docs/md/qhaway-politica-datos.md).

## Documentación

Toda la documentación de arquitectura, dominio, SRS y visión del proyecto vive en
[`docs/md/`](docs/md/); ver especialmente
[`docs-GUIA-INSTALACION.md`](docs/md/docs-GUIA-INSTALACION.md) y
[`qhaway-vision.md`](docs/md/qhaway-vision.md).

## Distribuir (empaquetado)

Se congela con PyInstaller. Construir **en Windows**, dentro del venv:

```powershell
pip install pyinstaller
pyinstaller packaging\qhaway.spec
```

El resultado es la **carpeta** `dist\qhaway\` completa (no solo el `.exe`: necesita su carpeta
`_internal\`). El GTK viaja adentro, así que el usuario final no instala nada.

## Licencia

[MIT](LICENSE) — código abierto para la comunidad docente.
