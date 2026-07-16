# QHAWAY — PoC de PDF y Congelamiento (Etapas 0.4 y 0.5)

**Versión:** 1.0 · **Fecha:** Julio 2026
**Realiza:** AD-09, Arquitectura §12/§13.5 · Plan Etapas 0.4 y 0.5
**Estado: AMBOS APROBADOS en Windows** (Linux diferido por regla anti-pantano; el entorno Linux de desarrollo ya validó WeasyPrint sin congelar).

## 0.4 — Duelo de motores HTML→PDF: gana WeasyPrint

Probados ambos contra el diseño funcional real de SIMI (31KB, variables CSS, Google Fonts, SVG inline, `@media print`):

| | WeasyPrint | QWebEngine (printToPdf) |
|---|---|---|
| Fidelidad de layout, colores, tablas, SVG | ✓ total | ✓ total |
| Tipografías reales (Syne/Atkinson) | ✓ embebidas | ✗ cayó a Arial (carrera de webfonts: imprime antes de que carguen) |
| Tamaño del PDF | 104 KB | 418 KB (4x) |
| Costo en el ejecutable | DLLs GTK (~decenas de MB) | ~150+ MB (Chromium) |
| Instalación de desarrollo (Windows) | pip + instalador GTK3-Runtime (una vez) | pip solo |

**Decisión: WeasyPrint** como motor de `infra.informes` (AD-09 resuelta). QWebEngine queda como plan B documentado; su bug de fuentes es corregible (esperar `document.fonts.ready`) si alguna vez hiciera falta.

**Nota para producción:** las fuentes se cargaron desde Google Fonts (red). El informe final debe **empaquetar las fuentes localmente** (@font-face con archivos locales): offline y reproducible.

## 0.5 — Receta de congelamiento validada (Windows 11, Python 3.14)

App de prueba: PySide6 (ventana) + WeasyPrint (PDF con variables CSS, tablas y @page). Congelada y ejecutada con éxito.

```powershell
pyinstaller --noconfirm --onedir --windowed ^
  --collect-all weasyprint ^
  --add-binary "C:\Program Files\GTK3-Runtime Win64\bin\*.dll;." ^
  poc_congelar.py
```

**Los tres obstáculos encontrados y sus soluciones (el valor real del PoC):**

1. **`--onedir` no produce un exe autónomo**: el ejecutable necesita su carpeta completa (`_internal\` incluida). Copiar solo el .exe da "Failed to load Python DLL". → La distribución es la carpeta entera (zip o instalador); la guía de instalación lo dirá en negrita. `--onefile` existe como alternativa (más lento al arrancar, más fricción con antivirus); se mantiene `--onedir`.
2. **GTK instalado no alcanza para el exe congelado**: error 0x7E al cargar `libgobject-2.0-0.dll` (sus dependencias no se resuelven desde Program Files en el contexto congelado). → `--add-binary` empaqueta la familia GTK completa dentro de la app. Beneficio mayor: **el usuario final no instala GTK** — la dependencia viaja adentro.
3. **Rutas de usuario jamás a mano**: `expanduser("~") + "Desktop"` no existe en máquinas con OneDrive (escritorio redirigido — la norma en instituciones educativas, es decir, en los usuarios de QHAWAY). → `QStandardPaths.writableLocation(...)` siempre. Coherente con las decisiones ya tomadas (configuración en %APPDATA%, ciclos en directorio elegido por el docente).

## Consecuencias para el proyecto

- AD-09: cerrada (WeasyPrint + Jinja2 + fuentes locales).
- Receta de empaquetado de la Etapa 9: esta acta es su primera versión.
- RNF-10: viable, demostrado.
- Riesgo técnico mayor de la arquitectura: **extinguido en la semana 0**, con una app de 60 líneas — exactamente el propósito de la Etapa 0.
