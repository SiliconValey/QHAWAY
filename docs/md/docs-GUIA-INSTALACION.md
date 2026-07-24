# QHAWAY — Guía de instalación y uso

Asistente de corrección de proyectos grupales. De docentes, para docentes.
Código abierto (MIT).

## Para desarrollar (desde el código fuente)

Requisitos: Python 3.11+ y, en Windows, el runtime GTK3 (para WeasyPrint).

```bash
git clone <tu-repo>/QHAWAY.git
cd QHAWAY
python -m venv venv
# Windows:  venv\Scripts\activate     Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
python -m pytest -q            # debería dar toda la suite en verde
```

En Windows, si al generar un PDF aparece `cannot load library 'libgobject-2.0-0'`:
instalá el [GTK3-Runtime para Windows](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases)
y reiniciá la terminal. (El usuario final no necesita esto: ver "Distribuir".)

## Configurar

```bash
python qhaway_cli.py guardar-clave      # pega tu clave de API (no se muestra)
python qhaway_cli.py probar-conexion    # verifica la conexión
```

La clave se guarda en `%APPDATA%/qhaway` (Windows) o `~/.config/qhaway` (Linux),
**fuera del repositorio**. Copiá `config-ejemplo/*.yaml` a la carpeta `config/`
de tu ciclo y reemplazá los valores por los de tu cátedra (checklist real, tabla
de nomenclatura).

## Distribuir (empaquetado, RNF-10)

Se congela con PyInstaller. Construir **en Windows**, en el venv:

```powershell
pip install pyinstaller
pyinstaller packaging\qhaway.spec
```

El resultado es la **carpeta** `dist\qhaway\` completa — esa es la app distribuible
(zippeala o armá un instalador). **Copiar solo el .exe no funciona**: necesita su
carpeta `_internal\`. El GTK viaja adentro, así que **el usuario final no instala
nada**.

## Manejo de datos y privacidad

QHAWAY envía a la API de Anthropic el **contenido de las entregas** (documentos y
UI) para su análisis. Consideraciones (política completa: `docs/qhaway-politica-datos.md`):

- **Qué viaja**: el texto de las entregas, que puede incluir nombres en carátulas.
  Los trabajos son de carácter público y de contenido ficticio (empresas
  inventadas), base sobre la que se asume innecesaria la anonimización — decisión
  explícita, no implícita.
- **Qué NO viaja**: los nombres de los integrantes cargados en la gestión de
  grupos viven **solo en la base local** y nunca se envían a la API (RNF-05).
- **La clave de API** nunca se guarda en el repositorio ni en los informes; vive
  en la config de usuario del sistema (CFG-07).
- **Marco normativo**: Ley 25.326 de Protección de Datos Personales (Argentina).
  Se recomienda informar a alumnos e institución sobre el uso de IA en la
  corrección, como parte de la transparencia del proceso.

## Uso (flujo del docente)

1. Crear el ciclo lectivo y dar de alta los grupos.
2. Cargar la rúbrica, el proyecto modelo y los checklists (una vez por ciclo).
3. Por cada grupo: cargar la entrega → analizar → revisar el borrador
   (aceptar/editar/descartar cada elemento, ajustar la nota) → validar.
4. Exportar el informe de devolución y la guía de defensa (PDF).

Principio rector: **la IA propone, el docente decide**. Ninguna salida llega al
grupo sin pasar por tu criterio.
