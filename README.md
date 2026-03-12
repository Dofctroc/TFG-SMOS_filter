# TFG-SMOS_filter
Código del programa en python usado para automatizar la creación de esquemáticos en ADS sobre filtros ladder que implementan resonadores BVD y su equivalente COM.

Command line (inputed in ADS - Python Console):
import os
import sys
ruta = r"C:\Users\G513\Documents\ADSworkspaces\TFG-SMOS_filter [CODE]\main.py"
directorio_script = os.path.dirname(ruta)
os.chdir(directorio_script)
if directorio_script not in sys.path:
      sys.path.insert(0, directorio_script)
exec(open(ruta, encoding="utf-8").read())
