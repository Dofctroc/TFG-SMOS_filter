import os
import subprocess
import re
import numpy as np

from PySide6.QtWidgets import (QApplication, QFileDialog)


def select_workspace_path() -> str:
    """Selecciona carpeta usando PySide6 (Evita el WinError 6)"""
    # Si no hay una aplicación Qt creada (raro en ADS), la crea
    app = QApplication.instance() or QApplication([])
    
    path = QFileDialog.getExistingDirectory(
        None, 
        "Selecciona la carpeta del workspace",
        "",
        QFileDialog.ShowDirsOnly
    )
    return path

def select_file_to_read(file_filter: str = "All Files (*.*)") -> str:
    """Selecciona archivo usando PySide6 (Evita el WinError 6)"""
    app = QApplication.instance() or QApplication([])
    
    # Ajustamos el filtro: Qt usa ";;" como separador en lugar de "|"
    qt_filter = file_filter.replace("|", ";;")
    
    file_path, _ = QFileDialog.getOpenFileName(
        None,
        "Selecciona un archivo",
        "",
        qt_filter
    )
    return file_path

def read_and_parse_file(file_path: str) -> dict:
    """Lee solo la sección [BVD_NETWORK] del archivo INI."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
    
    parameters = {}
    in_bvd_network = False
    in_bvd_losses = False
    in_basic_settings = False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Buscar inicio de [BASIC SETTINGS]
        if line.startswith("[BASIC SETTINGS]"):
            in_basic_settings = True
            i += 1
            continue

        # Buscar inicio de [BVD_NETWORK]
        if line.startswith("[BVD_NETWORK]"):
            in_bvd_network = True
            i += 1
            continue

        # Buscar inicio de [BVD_losses]
        if line.startswith("[LOSSES]"):
            in_bvd_losses = True
            i += 1
            continue
        
        # Si encontramos otra sección, salir
        if in_bvd_losses and line.startswith("[") and line.endswith("]"):
            break
        
        # Leer líneas dentro de [BVD_NETWORK]
        if in_bvd_network or in_bvd_losses or in_basic_settings:
            # Si es una línea que contiene '='
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Si el valor contiene 'array(' y no está cerrado, continuar leyendo
                if 'array(' in value and ')' not in value.split('array(')[1]:
                    i += 1
                    # Continuar leyendo líneas hasta cerrar el array
                    while i < len(lines):
                        next_line = lines[i].strip()
                        value += ' ' + next_line
                        if ')' in next_line:
                            break
                        i += 1
                
                parameters[key] = value

        i += 1
    
    parameters = adapt_parameters_for_ADS(parameters)
    parameters = compute_extra_parameters_AND_convert_tofloat(parameters)

    return parameters

def adapt_parameters_for_ADS(parameters: dict) -> dict: 
    """Adapta los parámetros leídos para que sean compatibles con ADS."""
    adapted_params = {} 
    for key, value in parameters.items(): # Adaptar el formato de los arrays 
        if value.startswith("array([") and value.endswith("])"): 
            # Convertir a formato compatible con ADS las listas de valores 
            adapted_value = value.replace("array([", "list(").replace("])", ")") 
            adapted_params[key] = adapted_value
        else:
            adapted_value = value

        adapted_params[key] = re.sub(r'(\d+)\.(?!\d)', r'\1.0', adapted_value) 
    
    return adapted_params

def compute_extra_parameters_AND_convert_tofloat(parameters: dict) -> dict:
    # COMPUTE resonant frequencies and Ra RESISTOR
    # List type: list(xx, xx, xx, ...)
    qa = float(parameters["qa"])

    # Convertir las listas de strings a listas de números
    contenido = parameters["c0"].replace("list(", "").replace(")", "")
    c0_vals = [float(x.strip()) for x in contenido.split(",")]
    parameters["c0_vals"] = c0_vals

    contenido = parameters["ca"].replace("list(", "").replace(")", "")
    ca_vals = [float(x.strip()) for x in contenido.split(",")]
    parameters["ca_vals"] = ca_vals

    contenido = parameters["la"].replace("list(", "").replace(")", "")
    la_vals = [float(x.strip()) for x in contenido.split(",")]
    parameters["la_vals"] = la_vals

    contenido = parameters["ladd_ser"].replace("list(", "").replace(")", "")
    ladd_ser_vals = [float(x.strip()) for x in contenido.split(",")]
    parameters["ladd_ser_vals"] = ladd_ser_vals

    contenido = parameters["ladd_shu"].replace("list(", "").replace(")", "")
    ladd_shu_vals = [float(x.strip()) for x in contenido.split(",")]
    parameters["ladd_shu_vals"] = ladd_shu_vals

    contenido = parameters["cadd_ser"].replace("list(", "").replace(")", "")
    cadd_ser_vals = [float(x.strip()) for x in contenido.split(",")]
    parameters["cadd_ser_vals"] = cadd_ser_vals

    contenido = parameters["cadd_shu"].replace("list(", "").replace(")", "")
    cadd_shu_vals = [float(x.strip()) for x in contenido.split(",")]
    parameters["cadd_shu_vals"] = cadd_shu_vals

    contenido = parameters["ladd_ground"].replace("list(", "").replace(")", "")
    ladd_ground_vals = [float(x.strip()) for x in contenido.split(",")]
    parameters["ladd_ground_vals"] = ladd_ground_vals

    # Calcular fs y fp para cada par de la y ca
    matriz_valores = zip(la_vals, ca_vals)
    fs_vals = [(1/(2 * np.pi * np.sqrt(la * ca))) for la, ca in matriz_valores]
    parameters["fs"] = f"list({', '.join(str(fs) for fs in fs_vals)})"
    parameters["fs_vals"] = fs_vals

    matriz_valores = zip(c0_vals, ca_vals)
    cp_vals = [c0-ca for c0, ca in matriz_valores]
    parameters["cp_vals"] = cp_vals

    matriz_valores = zip(cp_vals, ca_vals, la_vals)
    fp_vals = [(1/(2 * np.pi)*np.sqrt((cp+ca)/(cp*ca*la))) for cp, ca, la in matriz_valores]
    parameters["fp"] = f"list({', '.join(str(fp) for fp in fp_vals)})"
    parameters["fp_vals"] = fp_vals

    # Calcular Ra para cada par de la y fs
    matriz_valores = zip(fs_vals, la_vals)
    ra_vals = [(2 * np.pi * fs * la / qa) for fs, la in matriz_valores]
    parameters["ra"] = f"list({', '.join(str(ra) for ra in ra_vals)})"
    parameters["ra_vals"] = ra_vals

    return parameters
