import os
import sys

# RUTAFUENTE da error puesto que es una varible deinida en consola python de ADS
# No es un error realmente
if 'RUTAFUENTE' in globals():
    directorio_proyecto = os.path.dirname(RUTAFUENTE)
    
    os.chdir(directorio_proyecto)
    if directorio_proyecto not in sys.path:
        sys.path.insert(0, directorio_proyecto)
    
    print(f"--- Entorno configurado en: {directorio_proyecto} ---")
    exec(open(RUTAFUENTE, encoding="utf-8").read())
else:
    print("Error: No se ha definido la variable RUTAFUENTE")