"""Carga de la configuración de DET: checklist (CFG-05) y nomenclatura (CFG-06).

El dominio recibe la config ya parseada; este módulo la construye desde dicts
(como los de `yaml.safe_load`) y ofrece defaults de EJEMPLO para arrancar.

IMPORTANTE: los defaults de acá son un punto de partida basado en los hallazgos
de la Etapa 0.2 (estructura de 7 secciones) y en los prefijos estándar de Qt.
Deben reemplazarse por los contenidos reales de la cátedra —el checklist real y
la tabla completa de nomenclatura son entregables del proyecto (CFG-06)—. Por eso
viven en `config/*.yaml` dentro del ciclo, editables, no cableados.
"""

from __future__ import annotations

from ..dominio.deteccion import Bloque, ChecklistDocumento, ConvencionNomenclatura


# ----------------------------------------------------------------------------
# Carga desde dict
# ----------------------------------------------------------------------------
def cargar_checklist(datos: dict) -> dict[str, ChecklistDocumento]:
    """Construye {tipo_artefacto -> ChecklistDocumento} desde un dict parseado.

    Estructura esperada:
        checklist:
          srs:
            requiere_caratula: true
            requiere_indice: true
            requiere_secciones_numeradas: true
            bloques:
              - id: introduccion
                palabras_clave: ["introduccion", "propósito"]
    """
    raiz = datos.get("checklist", datos) or {}
    resultado: dict[str, ChecklistDocumento] = {}
    for tipo, cfg in raiz.items():
        cfg = cfg or {}
        bloques = tuple(
            Bloque(
                id=b["id"],
                palabras_clave=tuple(b.get("palabras_clave", [b["id"]])),
            )
            for b in cfg.get("bloques", [])
        )
        extra = {}
        if "palabras_caratula" in cfg:
            extra["palabras_caratula"] = tuple(cfg["palabras_caratula"])
        if "palabras_indice" in cfg:
            extra["palabras_indice"] = tuple(cfg["palabras_indice"])
        resultado[tipo] = ChecklistDocumento(
            tipo_artefacto=tipo,
            bloques=bloques,
            requiere_caratula=bool(cfg.get("requiere_caratula", False)),
            requiere_indice=bool(cfg.get("requiere_indice", False)),
            requiere_secciones_numeradas=bool(cfg.get("requiere_secciones_numeradas", False)),
            **extra,
        )
    return resultado


def cargar_nomenclatura(datos: dict) -> ConvencionNomenclatura:
    """Construye la convención de nomenclatura desde un dict parseado.

    Estructura esperada:
        nomenclatura:
          prefijos:
            QPushButton: btn
            QLineEdit: txt
          ignorar: [QWidget, QVBoxLayout]
    """
    raiz = datos.get("nomenclatura", datos) or {}
    prefijos = dict(raiz.get("prefijos", {}))
    ignorar = raiz.get("ignorar")
    if ignorar is not None:
        return ConvencionNomenclatura(prefijos=prefijos, ignorar=frozenset(ignorar))
    return ConvencionNomenclatura(prefijos=prefijos)


# ----------------------------------------------------------------------------
# Defaults de EJEMPLO (reemplazar por los reales de la cátedra)
# ----------------------------------------------------------------------------
# Checklist SRS basado en la estructura de 7 secciones hallada en la Etapa 0.2,
# más los bloques que documentos reales omitieron (Definiciones, Referencias).
CHECKLIST_DEFECTO: dict[str, ChecklistDocumento] = cargar_checklist({
    "checklist": {
        "srs": {
            "requiere_caratula": True,
            "requiere_indice": True,
            "requiere_secciones_numeradas": True,
            "bloques": [
                {"id": "introduccion", "palabras_clave": ["introduccion", "proposito", "objetivo"]},
                {"id": "descripcion_general", "palabras_clave": ["descripcion general", "vision general", "perspectiva del producto"]},
                {"id": "definiciones", "palabras_clave": ["definiciones", "acronimos", "siglas", "glosario"]},
                {"id": "requerimientos_funcionales", "palabras_clave": ["requerimientos funcionales", "requisitos funcionales"]},
                {"id": "requerimientos_no_funcionales", "palabras_clave": ["requerimientos no funcionales", "requisitos no funcionales"]},
                {"id": "restricciones", "palabras_clave": ["restricciones", "limitaciones"]},
                {"id": "interfaces", "palabras_clave": ["interfaz", "interfaces"]},
                {"id": "referencias", "palabras_clave": ["referencias", "bibliografia"]},
            ],
        },
        "presentacion": {
            "requiere_caratula": True,
            "requiere_indice": False,
            "requiere_secciones_numeradas": False,
            "bloques": [
                {"id": "empresa", "palabras_clave": ["empresa", "organizacion"]},
                {"id": "mision_vision", "palabras_clave": ["mision", "vision"]},
                {"id": "problema", "palabras_clave": ["problema", "necesidad"]},
                {"id": "solucion", "palabras_clave": ["solucion", "producto", "propuesta"]},
            ],
        },
        "fd": {
            "requiere_caratula": True,
            "requiere_indice": True,
            "requiere_secciones_numeradas": True,
            "bloques": [
                {"id": "pantallas", "palabras_clave": ["pantallas", "interfaz de usuario", "mockups"]},
                {"id": "flujos", "palabras_clave": ["flujo", "navegacion", "recorrido"]},
                {"id": "datos", "palabras_clave": ["datos", "validaciones", "campos"]},
            ],
        },
    }
})

# Convención de nomenclatura de EJEMPLO (prefijos estándar de Qt).
# Reemplazar por la tabla completa de la cátedra (referencia 4, CFG-06).
NOMENCLATURA_DEFECTO: ConvencionNomenclatura = cargar_nomenclatura({
    "nomenclatura": {
        "prefijos": {
            "QPushButton": "btn",
            "QToolButton": "btn",
            "QLineEdit": "txt",
            "QTextEdit": "txt",
            "QPlainTextEdit": "txt",
            "QLabel": "lbl",
            "QComboBox": "cmb",
            "QCheckBox": "chk",
            "QRadioButton": "rad",
            "QSpinBox": "spn",
            "QDoubleSpinBox": "spn",
            "QDateEdit": "dte",
            "QTableWidget": "tbl",
            "QTableView": "tbl",
            "QListWidget": "lst",
            "QListView": "lst",
            "QTreeWidget": "tre",
            "QGroupBox": "grp",
            "QTabWidget": "tab",
            "QProgressBar": "prg",
            "QSlider": "sld",
            "QMenu": "mnu",
            "QAction": "act",
        }
    }
})
