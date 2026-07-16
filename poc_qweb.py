"""
QHAWAY — PoC 0.4b: HTML → PDF con QWebEngine (Chromium de Qt)
==============================================================
Instalación:  pip install PySide6
(el metapaquete completo incluye QtWebEngine; si instalaste PySide6-Essentials
 solo, hace falta: pip install PySide6-Addons)

Uso:  python poc_qweb.py simi-diseno-funcional.html
"""
import sys, os, time
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, QMarginsF
from PySide6.QtGui import QPageLayout, QPageSize

def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    entrada = os.path.abspath(sys.argv[1])
    salida = os.path.abspath("salida_qwebengine.pdf")
    t0 = time.time()

    app = QApplication(sys.argv)
    vista = QWebEngineView()

    def al_cargar(ok):
        if not ok:
            print("✗ No se pudo cargar el HTML"); app.quit(); return
        layout = QPageLayout(QPageSize(QPageSize.PageSizeId.A4),
                             QPageLayout.Orientation.Portrait,
                             QMarginsF(12, 12, 12, 12))
        vista.page().printToPdf(salida, layout)

    def al_terminar(ruta, ok):
        if ok:
            print(f"✓ {ruta} generado en {time.time()-t0:.1f}s "
                  f"({os.path.getsize(ruta)//1024} KB)")
            print("Revisar: ¿fuentes cargadas? ¿colores fieles? ¿cortes de página razonables?")
        else:
            print("✗ Falló la generación del PDF")
        app.quit()

    vista.loadFinished.connect(al_cargar)
    vista.page().pdfPrintingFinished.connect(al_terminar)
    vista.load(QUrl.fromLocalFile(entrada))
    app.exec()

if __name__ == "__main__":
    main()
