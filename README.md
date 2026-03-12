# TFG-SMOS_filter
Código del programa en python usado para automatizar la creación de esquemáticos en ADS sobre filtros ladder que implementan resonadores BVD y su equivalente COM.

Command line (inputed in ADS - Python Console):

import os <br />
import sys <br />
ruta = r"...\main.py" <br />
directorio_script = os.path.dirname(ruta) <br />
os.chdir(directorio_script) <br />
if directorio_script not in sys.path: <br />
      sys.path.insert(0, directorio_script) <br />
exec(open(ruta, encoding="utf-8").read()) <br />
