import os
import sys
import pathlib

# 1. Obtenemos la ruta absoluta de la carpeta donde está este boot.py
directorio_actual = pathlib.Path(__file__).parent.resolve()

# 2. Definimos la ruta al main.py de forma dinámica
ruta_main = directorio_actual / "main.py"

# 3. Cambiamos el directorio de trabajo y actualizamos sys.path
os.chdir(directorio_actual)
if str(directorio_actual) not in sys.path:
    sys.path.insert(0, str(directorio_actual))

# 4. Ejecutamos main.py
if ruta_main.exists():
    with open(ruta_main, encoding="utf-8") as f:
        exec(f.read(), {'__name__': '__main__'})
else:
    print(f"Error: No se encontró {ruta_main}")