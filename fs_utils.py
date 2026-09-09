import os
import re
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QFileDialog)

from bvd_com_computations import (BVD, COM, COMconstants)

from models import *
# ========================== FUNCIONES ===========================

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
    # Convertir las listas de strings a listas de números
    parameters["cp"] = parameters["c0"]
    contenido = parameters["cp"].replace("list(", "").replace(")", "")
    cp_vals = [float(x.strip()) for x in contenido.split(",")]
    parameters["cp_vals"] = cp_vals

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

    return parameters

def create_frequency_plan(parameters: dict) -> FrequencyPlan:
    fstart = float(parameters["fstart1"])
    fstop = float(parameters["fstop1"])
    npoints = int(parameters["npoints1"])
    freqPlan = FrequencyPlan(fstart, fstop, npoints)

    return freqPlan

def create_mask(ruta_archivo) -> MASK:
    mask = MASK(os.path.basename(ruta_archivo), None)
    mask.limits = read_mask_limits(ruta_archivo)

    return mask

def read_mask_limits(ruta_archivo):
    limites = []

    with open(ruta_archivo, "r") as f:
        for linea in f:
            linea = linea.strip()

            # Saltar líneas vacías
            if not linea:
                continue

            valores = linea.split()

            limite = MASK_LIMIT(
                fstart = float(valores[0]) * 1e9,
                fstop = float(valores[1]) * 1e9,
                value_dB = float(valores[2]),
                upper_lower = "upper" if float(valores[3]) == 0 else "lower",
                loss_type = "S21" if float(valores[4]) == 0 else "S11"
            )

            limites.append(limite)
    
    return limites

def get_save_filepath(default_path: str) -> str:
    """
    Abre el diálogo 'Guardar como...' apuntando a una ruta por defecto 
    (directorio + nombre de archivo sugerido).
    """
    app = QApplication.instance() or QApplication([])
    
    # Muestra el diálogo estándar de guardado preseleccionando el directorio y nombre
    filepath, _ = QFileDialog.getSaveFileName(
        None,
        "Guardar configuración del filtro",
        default_path,
        "Archivos de texto (*.txt);;Archivos INI (*.ini);;Todos los archivos (*.*)"
    )
    return filepath

def format_val(val: object) -> str:
    """Convierte tipos de datos de NumPy/Python a representaciones limpias en texto."""
    if val is None:
        return "None"
    
    if hasattr(val, "item"):
        val = val.item()
        
    if isinstance(val, complex):
        sign = "+" if val.imag >= 0 else ""
        return f"{val.real}{sign}{val.imag}j"
        
    return str(val)

def format_array(values: list) -> str:
    """Genera la cadena array([v1, v2, ...]) con valores limpios."""
    formatted_elements = [format_val(v) for v in values]
    items_str = ", ".join(
        f"'{v}'" if isinstance(v, str) else str(v) 
        for v in formatted_elements
    )
    return f"array([{items_str}])"

def export_project_to_ini(
    workspace_path: str,
    workspace_name: str,
    parameters: dict, 
    freq_plan: FrequencyPlan, 
    bvd_list: list[BVD], 
    com_list: list[COM]
) -> None:
    # 1. Definir la ruta inicial predeterminada (workspace_path + nombre de archivo sugerido)
    default_filename = f"{workspace_name}_filter_config.txt"
    initial_full_path = os.path.join(workspace_path, default_filename)
    
    # 2. Abrir la interfaz de "Guardar como..." iniciando en workspace_path
    filepath = get_save_filepath(initial_full_path)
    
    # Si el usuario cancela la ventana de diálogo (botón Cancelar o 'X')
    if not filepath:
        print("Operación de guardado cancelada por el usuario.")
        return

    lines = []

    # 0. PARAMETROS GENERALES
    lines.append("[BASIC_SETTINGS]")
    lines.append(f"norder_ini = {format_val(parameters['norder_ini'])}")
    lines.append(f"typeseriesshunt_ini = {parameters['typeseriesshunt_ini']}")
    lines.append(f"matching_network = {format_val(parameters['matching_network'])}")
    lines.append(f"mntype1 = {parameters['mntype1']}")
    lines.append(f"input_l = {format_val(parameters['input_l'])}")
    lines.append(f"lfini1 = {format_val(parameters['lfini1'])}")
    lines.append(f"lfini2 = {format_val(parameters['lfini2'])}")
    lines.append(f"cfini1 = {format_val(parameters['cfini1'])}")
    lines.append(f"cfini2 = {format_val(parameters['cfini2'])}")
    lines.append("")

    # 1. FREQUENCY PLAN
    lines.append("[FREQ_PLANS]")
    lines.append(f"fstart1 = {format_val(freq_plan.fstart)}")
    lines.append(f"fstop1 = {format_val(freq_plan.fstop)}")
    lines.append(f"npoints1 = {format_val(freq_plan.Nsteps)}")
    lines.append("")

    # 2. BVD ELEMENTS
    lines.append("[BVD_ELEMENTS]")
    lines.append(f"count = {len(bvd_list)}")
    if bvd_list:
        lines.append(f"names = {[bvd.name for bvd in bvd_list]}")
        lines.append(f"c0 = {format_array([bvd.c0 for bvd in bvd_list])}")
        lines.append(f"cp = {format_array([bvd.cp for bvd in bvd_list])}")
        lines.append(f"ca = {format_array([bvd.ca for bvd in bvd_list])}")
        lines.append(f"la = {format_array([bvd.la for bvd in bvd_list])}")
        lines.append(f"fs = {format_array([bvd.fs for bvd in bvd_list])}")
        lines.append(f"fp = {format_array([bvd.fp for bvd in bvd_list])}")
        lines.append(f"cadd_shu = {format_array([bvd.cadd_shu for bvd in bvd_list])}")
        lines.append(f"ladd_shu = {format_array([bvd.ladd_shu for bvd in bvd_list])}")
        lines.append(f"cadd_ser = {format_array([bvd.cadd_ser for bvd in bvd_list])}")
        lines.append(f"ladd_ser = {format_array([bvd.ladd_ser for bvd in bvd_list])}")
        lines.append(f"ladd_ground = {format_array([bvd.ladd_ground for bvd in bvd_list])}")
        lines.append(f"rs = {format_array([bvd.rs for bvd in bvd_list])}")
        lines.append(f"rp = {format_array([bvd.rp for bvd in bvd_list])}")
        lines.append(f"ql = {format_array([bvd.ql for bvd in bvd_list])}")
        lines.append(f"qc = {format_array([bvd.qc for bvd in bvd_list])}")
        lines.append(f"qa = {format_array([bvd.qa for bvd in bvd_list])}")
    lines.append("")

    # 3. COM ELEMENTS
    lines.append("[COM_ELEMENTS]")
    lines.append(f"count = {len(com_list)}")
    if com_list:
        lines.append(f"names = {[com.name for com in com_list]}")
        lines.append(f"d = {format_array([com.d for com in com_list])}")
        lines.append(f"dR = {format_array([com.dR for com in com_list])}")
        lines.append(f"Ap = {format_array([com.Ap for com in com_list])}")
        lines.append(f"digitsN = {format_array([com.digitsN for com in com_list])}")
        lines.append(f"digitsNR = {format_array([com.digitsNR for com in com_list])}")
        lines.append(f"alpha = {format_array([com.alpha for com in com_list])}")
        lines.append(f"alpha_n = {format_array([com.alpha_n for com in com_list])}")
        lines.append(f"Ct = {format_array([com.Ct for com in com_list])}")
        lines.append(f"fs = {format_array([com.fs for com in com_list])}")
        lines.append(f"fp = {format_array([com.fp for com in com_list])}")
        
        # Atributos dentro del sub-objeto COMconstants
        lines.append(f"k11 = {format_array([com.constants.k11 if com.constants else None for com in com_list])}")
        lines.append(f"k12 = {format_array([com.constants.k12 if com.constants else None for com in com_list])}")
        lines.append(f"vp = {format_array([com.constants.vp if com.constants else None for com in com_list])}")
        lines.append(f"eps_r = {format_array([com.constants.eps_r if com.constants else None for com in com_list])}")
        lines.append("")

    # Guardar en el archivo dentro de la ruta especificada por el usuario
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        
    print(f"Archivo guardado exitosamente en: {filepath}")