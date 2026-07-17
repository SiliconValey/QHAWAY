"""
QHAWAY — PoC 0.5: Congelamiento con PyInstaller (la prueba final de la Etapa 0)
================================================================================
App minima que combina las dos dependencias criticas de QHAWAY:
PySide6 (ventana) + WeasyPrint (HTML -> PDF). Si ESTO congela y corre,
el stack completo es viable.

Pasos (en el venv del proyecto):
  1. pip install pyinstaller
  2. pyinstaller --noconfirm --onedir --windowed --collect-all weasyprint poc_congelar.py
  3. El ejecutable queda en dist\\poc_congelar\\poc_congelar.exe
  4. CRITERIO DE EXITO: abrir el .exe con doble clic DESDE OTRA CARPETA
     (o mejor: copiarlo a otra PC sin Python), tocar el boton, y que
     genere el PDF con las tipografias del sistema.

Si PyInstaller falla por modulos faltantes de WeasyPrint, probar sumando:
  --collect-all fontTools --collect-all tinycss2 --collect-all cssselect2 --collect-all pydyf
Anotar TODO lo que haga falta: eso es el entregable del PoC.
"""
import sys, os
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget

HTML_PRUEBA = """
<html><head><style>
  :root { --tinta:#16121f; --papel:#faf5ec; --maiz:#e8b13c; --cobre:#c96f4a; }
  @page { size: A4; margin: 18mm; }
  body { font-family: sans-serif; background: var(--papel); color: var(--tinta); }
  h1 { color: var(--cobre); border-bottom: 3px solid var(--maiz); padding-bottom: 8px; }
  table { border-collapse: collapse; width: 100%; }
  td, th { border: 1px solid var(--tinta); padding: 6px 10px; }
  th { background: var(--tinta); color: var(--papel); }
</style></head><body>
  <h1>QHAWAY — PoC de congelamiento</h1>
  <p>Si este PDF existe, PySide6 + WeasyPrint sobrevivieron a PyInstaller.</p>
  <table><tr><th>Prueba</th><th>Estado</th></tr>
  <tr><td>Variables CSS</td><td>funcionando</td></tr>
  <tr><td>Tablas</td><td>funcionando</td></tr>
  <tr><td>@page A4</td><td>funcionando</td></tr></table>
</body></html>
"""

class Ventana(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QHAWAY — PoC congelamiento")
        self.resize(420, 180)
        w = QWidget(); lay = QVBoxLayout(w)
        self.lbl = QLabel("PySide6 congelado: OK. Ahora la parte dificil:")
        btn = QPushButton("Generar PDF con WeasyPrint")
        btn.clicked.connect(self.generar)
        lay.addWidget(self.lbl); lay.addWidget(btn)
        self.setCentralWidget(w)

    def generar(self):
        try:
            # Windows: registrar GTK en la busqueda de DLLs (para corridas sin congelar;
            # en el exe congelado las DLLs viajan adentro via --add-binary)
            gtk = r"C:\Program Files\GTK3-Runtime Win64\bin"
            if hasattr(os, "add_dll_directory") and os.path.isdir(gtk):
                os.add_dll_directory(gtk)
            from weasyprint import HTML
            from PySide6.QtCore import QStandardPaths
            escritorio = QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.DesktopLocation)
            destino = os.path.join(escritorio, "qhaway_poc.pdf")
            HTML(string=HTML_PRUEBA).write_pdf(destino)
            self.lbl.setText(f"EXITO: {destino}")
        except Exception as e:
            self.lbl.setText(f"FALLO: {type(e).__name__}: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    v = Ventana(); v.show()
    sys.exit(app.exec())
