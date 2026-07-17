"""
QHAWAY — PoC 0.4a: HTML → PDF con WeasyPrint
=============================================
Instalación (Windows — acá está la prueba de verdad):
  pip install weasyprint
  → Si al importar falla con "cannot load library 'libgobject-2.0-0'":
    WeasyPrint necesita el runtime GTK3. Opciones:
    a) Instalador GTK3 para Windows: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases
       (instalar y reiniciar la terminal)
    b) Si esto ya duele, ES DATA para la decisión: anotalo y probá el PoC b.
En Linux: pip install weasyprint (suele andar directo).

Uso:  python poc_weasy.py simi-diseno-funcional.html
"""
import sys, os, time

def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    from weasyprint import HTML   # import adentro para que el error sea claro
    entrada = sys.argv[1]
    salida = "salida_weasyprint.pdf"
    t0 = time.time()
    HTML(entrada).write_pdf(salida)
    print(f"✓ {salida} generado en {time.time()-t0:.1f}s "
          f"({os.path.getsize(salida)//1024} KB)")
    print("Revisar: ¿fuentes Syne/Atkinson cargadas? ¿colores y layout fieles? ¿tablas enteras?")

if __name__ == "__main__":
    main()
