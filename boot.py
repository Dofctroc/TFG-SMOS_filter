import os
import sys

# 1. Configuración del entorno usando RUTAFUENTE (definida en ADS)
if 'RUTAFUENTE' in globals():
    # El directorio del proyecto es donde está boot.py
    directorio_proyecto = os.path.dirname(RUTAFUENTE)
    
    os.chdir(directorio_proyecto)
    if directorio_proyecto not in sys.path:
        sys.path.insert(0, directorio_proyecto)
    
    print(f"--- Entorno configurado en: {directorio_proyecto} ---")

    # 2. Definir qué archivo ejecutar a continuación
    # Construimos la ruta a main.py basándonos en la ubicación de boot.py
    archivo_main = os.path.join(directorio_proyecto, "main.py")

    if os.path.exists(archivo_main):
        print(f"--- Ejecutando: {archivo_main} ---")
        exec(open(archivo_main, encoding="utf-8").read())
    else:
        print(f"Error: No se encontró main.py en {directorio_proyecto}")

else:
    print("Error: No se ha definido la variable RUTAFUENTE en la consola de ADS")