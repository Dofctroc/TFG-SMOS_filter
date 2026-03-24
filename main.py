import os
import sys
import importlib
import pathlib
import traceback
import math

# Intentamos obtener la ruta del archivo, si falla (consola), usamos el directorio actual
try:
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
except NameError:
    directorio_actual = os.getcwd()

if directorio_actual not in sys.path:
    sys.path.insert(0, directorio_actual)

import ads_utils as ads
import fs_utils as fs
import bvd_com_computations as mat_bvd_com

from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QLineEdit, QMessageBox, QGroupBox, QSizePolicy, QRadioButton, QButtonGroup,
                               QComboBox, QFormLayout, QGridLayout)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QCursor

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import numpy as np

importlib.reload(ads)
importlib.reload(fs)
importlib.reload(mat_bvd_com)

# ============= VARIABLES GLOBALES ==============
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        # Usamos layout='constrained' o llamamos a tight_layout()
        self.fig = Figure(figsize=(width, height), dpi=dpi, layout='constrained')
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)

# ============= CLASE PRINCIPAL DE LA APLICACIÓN ==============

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.list_BVD = None
        self.list_COM = None
        self.network_file_path = None
        self.workspace_path = None

        self.setWindowTitle("TFG-SMOSfilter")
        self.setGeometry(100, 100, 1000, 700)

        # 1. CREAR EL WIDGET CENTRAL (El "lienzo" donde va todo)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal de la ventana (Vertical: Barra superior + Cuerpo)
        layout_principal = QVBoxLayout(central_widget)

        # --- SECCIÓN: BARRA SUPERIOR (Botones de archivos) ---
        self.setup_header()
        layout_principal.addLayout(self.barra_superior)

        # --- SECCIÓN: SUB BARRA SUPERIOR (Botones de archivos) ---
        self.setup_sub_header()
        layout_principal.addLayout(self.sub_barra_superior)

        # --- SECCIÓN: CUERPO (Layout Horizontal 50/50) ---
        self.layout_cuerpo = QHBoxLayout()

        # --- 2. PANEL IZQUIERDO (BVD) ---
        self.panel_izquierdo = QGroupBox("BVD Parameters")
        
        self.layout_bvd = QVBoxLayout(self.panel_izquierdo)
        self.setup_bvd_panel()

        # --- 2.5. PANEL CENTRAL (MATCHING NETWORKS + COM CONSTANTS)
        self.panel_central_contenedor = QWidget()
        self.layout_central_total = QVBoxLayout(self.panel_central_contenedor)
        self.setup_central_panel()

        # --- 3. PANEL DERECHO (COM + GRÁFICO) ---
        self.panel_derecho_contenedor = QWidget()
        self.layout_derecha_total = QVBoxLayout(self.panel_derecho_contenedor)
        self.setup_right_panel()

        # --- 4. ENSAMBLAJE CUERPO ---
        self.panel_izquierdo.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.panel_central_contenedor.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.panel_izquierdo.setMinimumWidth(300)
        self.panel_central_contenedor.setMinimumWidth(300)
        self.panel_derecho_contenedor.setMinimumWidth(600)
        
        self.layout_cuerpo.addWidget(self.panel_izquierdo, stretch=0)
        self.layout_cuerpo.addWidget(self.panel_central_contenedor, stretch=0)
        self.layout_cuerpo.addWidget(self.panel_derecho_contenedor, stretch=1)
        
        layout_principal.addLayout(self.layout_cuerpo)

        # --- 5. BOTÓN CREAR WORKSPACE ---
        self.setup_footer()
        layout_principal.addLayout(self.barra_inferior)

        self.aplicar_cursor_interactivo()
    

    def aplicar_cursor_interactivo(self):
        # 1. Buscamos todos los botones
        botones = self.findChildren(QPushButton)
        for boton in botones:
            boton.setCursor(Qt.PointingHandCursor)
        
        # 2. Buscamos todos los combobox
        combos = self.findChildren(QComboBox)
        for combo in combos:
            combo.setCursor(Qt.PointingHandCursor)
            # Opcional: Esto asegura que la lista desplegable también tenga el cursor
            combo.view().viewport().setCursor(Qt.PointingHandCursor)
        
        # 2. Buscamos todos los combobox
        radio_btns = self.findChildren(QRadioButton)
        for radio_btn in radio_btns:
            radio_btn.setCursor(Qt.PointingHandCursor)
            
    def setup_header(self):
        self.barra_superior = QHBoxLayout()

        self.btn_archivo = QPushButton("Seleccionar Archivo")
        self.btn_archivo.clicked.connect(self.btn_readNetworkFile_clicked)

        self.btn_directorio = QPushButton("Seleccionar Directorio")
        self.btn_directorio.clicked.connect(self.btn_readDirectoy_clicked)

        self.btn_convertir = QPushButton("Convertir BVD -> COM")
        self.btn_convertir.setEnabled(False)
        self.btn_convertir.clicked.connect(self.btn_convertBVD2COM_clicked)
        self.btn_convertir.setStyleSheet("background-color: #e0efff; color: black; font-weight: bold;")

        self.btn_duplicar = QPushButton("Duplicar Resonadores")
        self.btn_duplicar.setEnabled(False)
        self.btn_duplicar.clicked.connect(self.btn_duplicar_resonadores_clicked)
        self.btn_duplicar.setStyleSheet("background-color: #e0efff; color: black; font-weight: bold;")
        
        self.barra_superior.addWidget(self.btn_archivo)
        self.barra_superior.addWidget(self.btn_directorio)
        self.barra_superior.addStretch() # Empuja el botón convertir a la derecha
        self.barra_superior.addWidget(self.btn_convertir)
        self.barra_superior.addWidget(self.btn_duplicar)

    def setup_sub_header(self):
        self.sub_barra_superior = QVBoxLayout()

        self.label_network_file = QLabel("No file selected")
        self.label_network_file.setStyleSheet("color: red; font-size: 14px;")

        self.label_workspace_path = QLabel("No directory selected")
        self.label_workspace_path.setStyleSheet("color: red; font-size: 14px;")

        self.sub_barra_superior.addWidget(self.label_network_file)
        self.sub_barra_superior.addWidget(self.label_workspace_path)

    def setup_footer(self):
        self.barra_inferior = QHBoxLayout()

        self.label_workspace_name = QLabel("Workspace Name:")
        self.input_workspace_name = QLineEdit()
        self.input_workspace_name.setPlaceholderText("---")
        self.input_workspace_name.setFixedWidth(200)
        self.input_workspace_name.setMaxLength(20)

        self.btn_create_workspace = QPushButton("Create ADS Workspace")
        self.btn_create_workspace.clicked.connect(self.btn_createFullWorkspace_clicked)
        self.btn_create_workspace.setStyleSheet("background-color: #fffce6; color: black; font-weight: bold;")

        self.barra_inferior.addWidget(self.label_workspace_name)
        self.barra_inferior.addWidget(self.input_workspace_name)
        self.barra_inferior.addStretch()
        self.barra_inferior.addWidget(self.btn_create_workspace)
        
    def setup_bvd_panel(self):
        self.panel_izquierdo.setStyleSheet("""
            QGroupBox {
                border: 1px solid black;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: black;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
        """)
        # 1. El Desplegable (Selector)
        self.combo_bvd = QComboBox()
        self.combo_bvd.setFixedWidth(200)
        self.combo_bvd.addItem("Archivo .ntw no leído")
        
        # Conectamos el cambio de selección a una función
        self.combo_bvd.currentIndexChanged.connect(self.actualizar_formulario_bvd)
        self.combo_bvd.currentIndexChanged.connect(self.unificar_grafico_bvd)

        # 2. El Formulario de parámetros
        self.form_layout_BVD = QFormLayout()
        
        # Creamos los campos (QLineEdit)
        self.input_c0 = QLineEdit()
        self.input_cp = QLineEdit()
        self.input_ca = QLineEdit()
        self.input_la = QLineEdit()
        self.input_fs = QLineEdit()
        self.input_fp = QLineEdit()
        self.input_ladd_ser = QLineEdit()
        self.input_ladd_shu = QLineEdit()
        self.input_cadd_ser = QLineEdit()
        self.input_cadd_shu = QLineEdit()
        self.input_ladd_ground = QLineEdit()
        
        # Configuramos como "Solo lectura" y ponemos placeholders
        self.campos_form_bvd = [self.input_c0, self.input_cp, self.input_ca, self.input_la, self.input_fs, self.input_fp, self.input_ladd_ser,
                    self.input_ladd_shu, self.input_cadd_ser, self.input_cadd_shu, self.input_ladd_ground]
        for inp in self.campos_form_bvd:
            inp.setReadOnly(True)
            inp.setPlaceholderText("---")
            inp.setStyleSheet("background-color: #f0f0f0; color: #555;")

        # Añadimos al layout del formulario
        self.form_layout_BVD.addRow("C0 (pF):", self.input_c0)
        self.form_layout_BVD.addRow("Cp (pF):", self.input_cp)
        self.form_layout_BVD.addRow("Ca (pF):", self.input_ca)
        self.form_layout_BVD.addRow("La (nH):", self.input_la)
        self.form_layout_BVD.addRow("fs (Hz):", self.input_fs)
        self.form_layout_BVD.addRow("fp (Hz):", self.input_fp)
        self.form_layout_BVD.addRow("Ladd_ser (nH):", self.input_ladd_ser)
        self.form_layout_BVD.addRow("Ladd_shu (nH):", self.input_ladd_shu)
        self.form_layout_BVD.addRow("Cadd_ser (pF):", self.input_cadd_ser)
        self.form_layout_BVD.addRow("Cadd_shu (pF):", self.input_cadd_shu)
        self.form_layout_BVD.addRow("Ladd_gnd (nH):", self.input_ladd_ground)

        # Añadir parámetros generales (rs, rp, ql, qc, qa) al formulario de BVD
        self.form_layout_BVD_general = QFormLayout()

        self.input_rs = QLineEdit()
        self.input_rp = QLineEdit()
        self.input_ql = QLineEdit()
        self.input_qc = QLineEdit()
        self.input_qa = QLineEdit()

        # Configuramos como "Solo lectura" y ponemos placeholders
        self.campos_form_bvdgeneral = [self.input_rs, self.input_rp, self.input_ql, self.input_qc, self.input_qa]
        for inp in self.campos_form_bvdgeneral:
            inp.setReadOnly(True)
            inp.setPlaceholderText("---")
            inp.setStyleSheet("background-color: #f0f0f0; color: #555;")

        self.form_layout_BVD_general.addRow("Rs (Ω):", self.input_rs)
        self.form_layout_BVD_general.addRow("Rp (Ω):", self.input_rp)
        self.form_layout_BVD_general.addRow("Ql (-):", self.input_ql)
        self.form_layout_BVD_general.addRow("Qc (-):", self.input_qc)
        self.form_layout_BVD_general.addRow("Qa (-):", self.input_qa)

        # 3. Montaje en el panel izquierdo (el que ya tenías)
        # Limpiamos el layout_bvd por si acaso y añadimos
        bvd_label=QLabel("Parámetros Resonador:")
        bvd_label.setStyleSheet("font-weight: bold; color: darkgray;")
        self.layout_bvd.addWidget(bvd_label)
        self.layout_bvd.addWidget(self.combo_bvd)
        self.layout_bvd.addSpacing(10) # Espacio visual
        self.layout_bvd.addLayout(self.form_layout_BVD)

        self.layout_bvd.addSpacing(20) # Espacio visual
        bvd_general_label=QLabel("Parámetros Generales:")
        bvd_general_label.setStyleSheet("font-weight: bold; color: darkgray;")
        self.layout_bvd.addWidget(bvd_general_label)
        self.layout_bvd.addLayout(self.form_layout_BVD_general)
        self.layout_bvd.addStretch()

    def unificar_grafico_bvd(self, index):
        # Actualizamos los formularios BVD y GRPHICS para que haya uniformidad en la GUI
        self.combo_com.setCurrentIndex(index)
        self.combo_elemento_graf.setCurrentIndex(index)

    def actualizar_formulario_bvd(self, index):
        """Esta función se llama cada vez que eliges un BVD en el combo"""
        # Si no hay datos (solo el mensaje por defecto) o la lista está vacía
        if not self.list_BVD or self.combo_bvd.currentText() == "Archivo .ntw no leído":
            return

        # Obtenemos el objeto BVD seleccionado
        bvd_seleccionado = self.list_BVD[index]
        
        # Rellenamos los campos
        self.input_c0.setText(str(bvd_seleccionado.c0/1e-12))
        self.input_cp.setText(str(bvd_seleccionado.cp/1e-12))
        self.input_ca.setText(str(bvd_seleccionado.ca/1e-12))
        self.input_la.setText(str(bvd_seleccionado.la/1e-09))
        self.input_fs.setText(formato_ingenieria(bvd_seleccionado.fs))
        self.input_fp.setText(formato_ingenieria(bvd_seleccionado.fp))
        self.input_ladd_ser.setText(str(bvd_seleccionado.ladd_ser/1e-09) if bvd_seleccionado.ladd_ser < 10 else "inf")
        self.input_ladd_shu.setText(str(bvd_seleccionado.ladd_shu/1e-09) if bvd_seleccionado.ladd_shu < 10 else "inf")
        self.input_cadd_ser.setText(str(bvd_seleccionado.cadd_ser/1e-12) if bvd_seleccionado.cadd_ser < 10 else "inf")
        self.input_cadd_shu.setText(str(bvd_seleccionado.cadd_shu/1e-12) if bvd_seleccionado.cadd_shu < 10 else "inf")
        self.input_ladd_ground.setText(str(bvd_seleccionado.ladd_ground/1e-09))

    def setup_central_panel(self):
        self.layout_central_total.setContentsMargins(0, 0, 0, 0) # Quitar márgenes internos

        # Sub-bloque MN (Superior)
        self.bloque_matchnetw = QGroupBox("Matching Networks Parameters")
        self.bloque_matchnetw.setStyleSheet("""
            QGroupBox {
                border: 1px solid black;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: black;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
        """)
        
        self.layout_matchnetw = QVBoxLayout(self.bloque_matchnetw)
        self.setup_matchnetw_panel()

        # Sub-bloque COM_consts (Inferior)
        self.bloque_constsCOM = QGroupBox("COM Constants")
        self.bloque_constsCOM.setStyleSheet("""
            QGroupBox {
                border: 1px solid black;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: black;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
        """)
        
        self.layout_constsCOM = QVBoxLayout(self.bloque_constsCOM)
        self.setup_constsCOM_panel()

        # Añadimos los sub-bloques al panel central
        self.layout_central_total.addWidget(self.bloque_matchnetw, stretch=0)
        self.layout_central_total.addWidget(self.bloque_constsCOM, stretch=1)

    def setup_matchnetw_panel(self):
        # 2. El Formulario de parámetros
        self.form_layout_MN = QFormLayout()
        
        # Creamos los campos (QLineEdit)
        self.input_inputL = QLineEdit()
        self.input_inputL_type = QLineEdit()
        self.input_Lfini = QLineEdit()
        self.input_matchnetw_type = QLineEdit()
        self.input_Cfini = QLineEdit()
        self.input_Cfini_type = QLineEdit()
        
        # Configuramos como "Solo lectura" y ponemos placeholders
        self.campos_form_MN = [self.input_inputL, self.input_inputL_type, self.input_Lfini, self.input_matchnetw_type, 
                    self.input_Cfini, self.input_Cfini_type]
        for inp in self.campos_form_MN:
            inp.setReadOnly(True)
            inp.setPlaceholderText("---")
            inp.setStyleSheet("background-color: #f0f0f0; color: #555;")

        # Añadimos al layout del formulario
        self.form_layout_MN.addRow("L_input (nH):", self.input_inputL)
        self.form_layout_MN.addRow("L_input type:", self.input_inputL_type)
        self.form_layout_MN.addRow("L_output (nH):", self.input_Lfini)
        self.form_layout_MN.addRow("L_output_type:", self.input_matchnetw_type)
        self.form_layout_MN.addRow("C_output (pF):", self.input_Cfini)
        self.form_layout_MN.addRow("C_output_type:", self.input_Cfini_type)

        # 3. Montaje en el panel derecho
        # Limpiamos el layout_com por si acaso y añadimos
        matchnetw_label=QLabel("Parámetros Matching Networks:")
        matchnetw_label.setStyleSheet("font-weight: bold; color: darkgray;")
        self.layout_matchnetw.addWidget(matchnetw_label)
        self.layout_matchnetw.addSpacing(10) # Espacio visual
        self.layout_matchnetw.addLayout(self.form_layout_MN)
        self.layout_matchnetw.addStretch()

    def setup_constsCOM_panel(self):
        K11 = -82053.9 - 1j*450
        K12 = 59340.0

        VP = 3741.8
        EPS_R = 39.56
        EPS_0 = 8.854e-12
        DUTY = 0.55

        Z0_PRIMA = 1
        R_SHUNT = 4e5
        R_SERIE = 0.1

        # 2. El Formulario de parámetros
        self.form_layout_constCOM = QFormLayout()
        
        # Creamos los campos (QLineEdit)
        self.input_K11 = QLineEdit()
        self.input_K12 = QLineEdit()
        self.input_VP = QLineEdit()
        self.input_EPS_R = QLineEdit()
        self.input_EPS_0 = QLineEdit()
        self.input_DUTY = QLineEdit()
        self.input_Z0_PRIMA = QLineEdit()
        self.input_R_SHUNT = QLineEdit()
        self.input_R_SERIE = QLineEdit()
        
        # Configuramos como "Solo lectura" y ponemos placeholders
        self.campos_form_comparameters = [self.input_K11, self.input_K12, self.input_VP, self.input_EPS_R, self.input_EPS_0, 
                    self.input_DUTY, self.input_Z0_PRIMA, self.input_R_SHUNT, self.input_R_SERIE]
        for inp in self.campos_form_comparameters:
            inp.setReadOnly(True)
            inp.setPlaceholderText("---")
            inp.setStyleSheet("background-color: #f0f0f0; color: #555;")

        # Añadimos al layout del formulario
        self.form_layout_constCOM.addRow("k11 (?):", self.input_K11)
        self.form_layout_constCOM.addRow("k12 (?):", self.input_K12)
        self.form_layout_constCOM.addRow("Vp (m/s):", self.input_VP)
        self.form_layout_constCOM.addRow("ε_r (-):", self.input_EPS_R)
        self.form_layout_constCOM.addRow("ε_0 (-):", self.input_EPS_0)
        self.form_layout_constCOM.addRow("η (-):", self.input_DUTY)
        self.form_layout_constCOM.addRow("Z0' (Ω):", self.input_Z0_PRIMA)
        self.form_layout_constCOM.addRow("Rp (Ω):", self.input_R_SHUNT)
        self.form_layout_constCOM.addRow("Rs (Ω):", self.input_R_SERIE)
        
        self.input_K11.setText(str(K11))
        self.input_K12.setText(str(K12))
        self.input_VP.setText(str(VP))
        self.input_EPS_R.setText(str(EPS_R))
        self.input_EPS_0.setText(str(EPS_0))
        self.input_DUTY.setText(str(DUTY))
        self.input_Z0_PRIMA.setText(str(Z0_PRIMA))
        self.input_R_SHUNT.setText(str(R_SHUNT))
        self.input_R_SERIE.setText(str(R_SERIE))

        # 3. Montaje en el panel derecho
        # Limpiamos el layout_com por si acaso y añadimos
        matchnetw_label=QLabel("Constantes COM:")
        matchnetw_label.setStyleSheet("font-weight: bold; color: darkgray;")
        self.layout_constsCOM.addWidget(matchnetw_label)
        self.layout_constsCOM.addSpacing(10) # Espacio visual
        self.layout_constsCOM.addLayout(self.form_layout_constCOM)
        self.layout_constsCOM.addStretch()

    def setup_right_panel(self):
        self.layout_derecha_total.setContentsMargins(0, 0, 0, 0) # Quitar márgenes internos

        # Sub-bloque COM (Superior)
        self.bloque_com = QGroupBox("COM Parameters")
        self.bloque_com.setStyleSheet("""
            QGroupBox {
                border: 1px solid black;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: black;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
        """)
        
        self.layout_com = QVBoxLayout(self.bloque_com)
        self.setup_com_panel()

        # Sub-bloque Gráfico (Inferior)
        self.bloque_grafico = QGroupBox("Admitance Visualization")
        self.bloque_grafico.setStyleSheet("""
            QGroupBox {
                border: 1px solid black;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: black;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
        """)

        self.layout_grafico = QVBoxLayout(self.bloque_grafico)
        self.setup_graph_panel()

        # Añadimos los sub-bloques al panel derecho
        self.layout_derecha_total.addWidget(self.bloque_com, stretch=0)
        self.layout_derecha_total.addWidget(self.bloque_grafico, stretch=1)

    def setup_com_panel(self):
        # 1. El Desplegable (Selector)
        self.combo_com = QComboBox()
        self.combo_com.setFixedWidth(200)
        self.combo_com.addItem("Conversión no realizada")
        
        # Conectamos el cambio de selección a una función
        self.combo_com.currentIndexChanged.connect(self.actualizar_formulario_com)
        self.combo_com.currentIndexChanged.connect(self.unificar_grafico_com)
        
        # Creamos los campos (QLineEdit)
        self.input_pitch = QLineEdit()
        self.input_aperture = QLineEdit()
        self.input_digitsIDT = QLineEdit()
        self.input_digitsREFL = QLineEdit()
        self.input_alpha = QLineEdit()
        
        # Nuevos campos para la segunda columna
        self.input_fs_COM = QLineEdit()
        self.input_fp_COM = QLineEdit()
        
        # Configuramos como "Solo lectura" y ponemos placeholders
        self.campos_form_com = [self.input_pitch, self.input_aperture, self.input_digitsIDT, 
                    self.input_digitsREFL, self.input_alpha, self.input_fs_COM, self.input_fp_COM]
        for inp in self.campos_form_com:
            inp.setReadOnly(True)
            inp.setPlaceholderText("---")
            inp.setStyleSheet("background-color: #f0f0f0; color: #555;")

        # 3. Organización en dos columnas (Layout Horizontal con dos FormLayouts)
        self.layout_horizontal_formularios = QHBoxLayout()

        # Añadimos al layout del formulario
        self.form_layout_COM_izq = QFormLayout()
        self.form_layout_COM_izq.addRow("p (m):", self.input_pitch)
        self.form_layout_COM_izq.addRow("Ap (λ0):", self.input_aperture)
        self.form_layout_COM_izq.addRow("digitsIDT (-):", self.input_digitsIDT)
        self.form_layout_COM_izq.addRow("digitsREFL (-):", self.input_digitsREFL)
        self.form_layout_COM_izq.addRow("α (-):", self.input_alpha)

        # Formulario Derecho: Resultados de Frecuencia
        self.form_layout_COM_der = QFormLayout()
        self.form_layout_COM_der.addRow("fs (Hz):", self.input_fs_COM)
        self.form_layout_COM_der.addRow("fp (Hz):", self.input_fp_COM)

        # Ensamblamos los dos formularios
        self.layout_horizontal_formularios.addLayout(self.form_layout_COM_izq)
        self.layout_horizontal_formularios.addSpacing(20) # Separación entre columnas
        self.layout_horizontal_formularios.addLayout(self.form_layout_COM_der)

        # 3. Montaje en el panel derecho
        # Limpiamos el layout_com por si acaso y añadimos
        com_label=QLabel("Parámetros modelo COM:")
        com_label.setStyleSheet("font-weight: bold; color: darkgray;")
        self.layout_com.addWidget(com_label)
        self.layout_com.addWidget(self.combo_com)
        self.layout_com.addSpacing(10) # Espacio visual
        self.layout_com.addLayout(self.layout_horizontal_formularios)
        self.layout_com.addStretch()

    def unificar_grafico_com(self, index):
        # Actualizamos los formularios BVD y GRPHICS para que haya uniformidad en la GUI
        self.combo_bvd.setCurrentIndex(index)
        self.combo_elemento_graf.setCurrentIndex(index)

    def actualizar_formulario_com(self, index):
        """Esta función se llama cada vez que eliges un BVD en el combo"""
        # Si no hay datos (solo el mensaje por defecto) o la lista está vacía
        if not self.list_COM or self.combo_com.currentText() == "Conversión no realizada":
            return

        # Obtenemos el objeto BVD seleccionado
        com_seleccionado = self.list_COM[index]
        
        # Rellenamos los campos
        self.input_pitch.setText(str(com_seleccionado.d))
        self.input_aperture.setText(str(com_seleccionado.Ap))
        self.input_digitsIDT.setText(str(com_seleccionado.digitsN))
        self.input_digitsREFL.setText(str(com_seleccionado.digitsNR))
        self.input_alpha.setText(str(com_seleccionado.alpha))

        self.input_fs_COM.setText(formato_ingenieria(com_seleccionado.fs))
        self.input_fp_COM.setText(formato_ingenieria(com_seleccionado.fp))

    def setup_graph_panel(self):
        # Usamos el layout que ya definiste en el __init__
        # Si no lo definiste allí, asegúrate de que esta línea sea la única que crea el QVBoxLayout
        if self.bloque_grafico.layout() is None:
            self.layout_grafico = QVBoxLayout(self.bloque_grafico)
        else:
            self.layout_grafico = self.bloque_grafico.layout()
            
        self.layout_grafico.setContentsMargins(10, 10, 10, 10)
        self.layout_grafico.setSpacing(5)

        # --- BARRA DE CONTROL DEL GRÁFICO (Horizontal) ---
        barra_filtros = QHBoxLayout()
        
        # 1. Selector de Elemento
        self.combo_elemento_graf = QComboBox()
        self.combo_elemento_graf.addItem("Sin datos")
        self.combo_elemento_graf.setFixedWidth(200)
        
        # 2. Botones de Radio (BVD vs COM)
        self.radio_bvd = QRadioButton("BVD")
        self.radio_com = QRadioButton("COM")
        self.radio_both = QRadioButton("Both")
        self.radio_bvd.setChecked(True) # BVD por defecto
        
        # Agrupamos los radios para que sean mutuamente excluyentes
        self.grupo_tipo = QButtonGroup(self)
        self.grupo_tipo.addButton(self.radio_bvd)
        self.grupo_tipo.addButton(self.radio_com)
        self.grupo_tipo.addButton(self.radio_both)
        self.radio_bvd.setEnabled(False)
        self.radio_com.setEnabled(False)
        self.radio_both.setEnabled(False)

        # Montamos la barrita de control
        barra_filtros.addWidget(self.combo_elemento_graf)
        barra_filtros.addSpacing(20)
        barra_filtros.addWidget(self.radio_bvd)
        barra_filtros.addWidget(self.radio_com)
        barra_filtros.addWidget(self.radio_both)
        barra_filtros.addStretch() # Empuja todo a la izquierda

        # 3. Canvas y Toolbar
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.toolbar = NavigationToolbar(self.canvas, self)
        # Hacer la toolbar más discreta
        self.toolbar.setStyleSheet("background-color: transparent; border: none;")
        self.toolbar.setIconSize(QSize(24, 24))

        # --- AÑADIR TODO AL LAYOUT PRINCIPAL DEL BLOQUE ---
        self.layout_grafico.addLayout(barra_filtros)
        self.layout_grafico.addWidget(self.canvas)
        self.layout_grafico.addWidget(self.toolbar)

        # --- CONEXIONES ---
        self.combo_elemento_graf.currentIndexChanged.connect(self.unificar_grafico_admitancia)
        self.combo_elemento_graf.currentIndexChanged.connect(self.plot_admitancia)
        self.radio_bvd.toggled.connect(self.plot_admitancia)
        self.radio_com.toggled.connect(self.plot_admitancia)
        self.radio_both.toggled.connect(self.plot_admitancia)

    def unificar_grafico_admitancia(self, index):
        # Actualizamos los formularios BVD y GRPHICS para que haya uniformidad en la GUI
        self.combo_bvd.setCurrentIndex(index)
        self.combo_com.setCurrentIndex(index)

    def plot_admitancia(self):
        idx = self.combo_elemento_graf.currentIndex()
        
        color_data1 = "red"
        color_data2 = "blue"
        label_data1 = f"BVD - Elemento {idx+1}"
        label_data2 = f"COM - Elemento {idx+1}"

        # Decidir qué fuente usar
        data1 = self.list_BVD[idx] if (self.radio_bvd.isChecked() or self.radio_both.isChecked()) else None
        data2 = self.list_COM[idx] if (self.radio_com.isChecked() or self.radio_both.isChecked()) else None
            
        self.canvas.axes.cla()

        # Verificamos que el objeto seleccionado tenga los datos
        if data1 is not None and (hasattr(data1, 'Y') or data1.Y is not None):
            # CONVERSIÓN A dB
            magnitud_Y_dB = 20 * np.log10(np.abs(data1.Y) + 1e-20)
            # Ploteamos f (log) vs Y (dB lineal)
            self.canvas.axes.plot(data1.f, magnitud_Y_dB, label=label_data1, color=color_data1)

            if data2 is None and hasattr(data1, "fs"):
                frecuencias_interes = [data1.fs, data1.fp]
                frecuencias_interes_names = ["fs_BVD", "fp_BVD"]
                for f_marcar, f_marcar_name in zip(frecuencias_interes, frecuencias_interes_names):
                    # Solo marcamos si está dentro del rango de los datos actuales
                    if data1.f.min() <= f_marcar <= data1.f.max():
                        idx = np.abs(data1.f - f_marcar).argmin()
                        self.canvas.axes.plot(data1.f[idx], magnitud_Y_dB[idx], 'kx')

                        ha_val = 'left'
                        x_pos = data1.f[idx] + (data1.f.max() - data1.f.min()) * 0.03
                        # Ajuste específico para "fp"
                        if "fp" in f_marcar_name.lower():
                            ha_val = 'right'
                            x_pos = data1.f[idx] - (data1.f.max() - data1.f.min()) * 0.03

                        self.canvas.axes.text(
                            x_pos, 
                            magnitud_Y_dB[idx],
                            f"{f_marcar_name}: {f_marcar:.4e}",
                            verticalalignment='center',
                            horizontalalignment=ha_val,  # Dinámico: 'right' para fp, 'left' para los demás
                            fontsize=9,
                            clip_on=True
                        )

        if data2 is not None and (hasattr(data2, 'Y') or data2.Y is not None):
            # CONVERSIÓN A dB
            magnitud_Y_dB = 20 * np.log10(np.abs(data2.Y) + 1e-20)
            # Ploteamos f (log) vs Y (dB lineal)
            self.canvas.axes.plot(data2.f, magnitud_Y_dB, label=label_data2, color=color_data2)

            if data1 is None and hasattr(data2, "fs"):
                frecuencias_interes = [data2.fs, data2.fp]
                frecuencias_interes_names = ["fs_COM", "fp_COM"]
                for f_marcar, f_marcar_name in zip(frecuencias_interes, frecuencias_interes_names):
                    # Solo marcamos si está dentro del rango de los datos actuales
                    if data2.f.min() <= f_marcar <= data2.f.max():
                        idx = np.abs(data2.f - f_marcar).argmin()
                        self.canvas.axes.plot(data2.f[idx], magnitud_Y_dB[idx], 'kx')
                        
                        ha_val = 'left'
                        x_pos = data2.f[idx] + (data2.f.max() - data2.f.min()) * 0.03
                        # Ajuste específico para "fp"
                        if "fp" in f_marcar_name.lower():
                            ha_val = 'right'
                            x_pos = data2.f[idx] - (data2.f.max() - data2.f.min()) * 0.03

                        self.canvas.axes.text(
                            x_pos, 
                            magnitud_Y_dB[idx],              # Coordenada Y
                            f"{f_marcar_name}: {f_marcar:.4e}",
                            verticalalignment='center',
                            horizontalalignment=ha_val,      # Empieza a la derecha del punto
                            fontsize=9,
                            clip_on=True
                        )

        self.canvas.axes.set_xlabel("Frecuencia (Hz)")
        self.canvas.axes.set_ylabel("Admitancia (dB)")
        
        # La escala Y ahora es lineal porque los datos YA están en dB
        self.canvas.axes.set_yscale('linear') 
        
        self.canvas.axes.grid(True, which="both", linestyle='--', alpha=0.5)
        self.canvas.axes.legend()
        
        self.canvas.draw()

    def btn_readNetworkFile_clicked(self):
        try:
            file_path = fs.select_file_to_read("Network files (*.ntw)|*.ntw|Text Files (*.txt)|*.txt|All Files (*.*)|*.*")
            if file_path:
                self.network_file_path = file_path
                self.label_network_file.setText(f"Selected: {file_path}")
                self.label_network_file.setStyleSheet("color: green; font-size: 14px;")
                self.network_parameters = fs.read_and_parse_file(file_path)

                # Crear la lista de BVDs a partir de los parámetros leídos
                self.list_BVD = mat_bvd_com.create_list_BVD(self.network_parameters)
                self.list_BVD = mat_bvd_com.compute_admitance_BVD(self.list_BVD, self.network_parameters)
                
                # Rellenar los campos de Matching Network y Lossy BVD con los parámetros leídos
                self.combo_bvd.clear() # Borra el "Archivo no leído"
                for bvd in self.list_BVD:
                    self.combo_bvd.addItem(bvd.name)
                
                self.assign_input_GeneralBVDParams()
                self.assign_input_MatchingNetworkParams()

                # Limpiamos el combo com por si ya había valores de antes
                self.combo_com.clear()
                self.combo_com.addItem("Conversión no realizada")

                # Rellenar el combo del gráfico con los elementos disponibles
                self.combo_elemento_graf.clear() # Borra el "Archivo no leído"
                for bvd in self.list_BVD:
                    self.combo_elemento_graf.addItem(bvd.name.replace("BVD", "Elemento"))

                # Borramos formulario com, Habilitamos el radio button de COM y ploteamos la primera curva por defecto
                self.list_COM = None
                for inp in self.campos_form_com:
                    inp.clear()

                self.radio_bvd.setEnabled(True)
                self.radio_com.setEnabled(False)
                self.radio_both.setEnabled(False)

                self.btn_convertir.setEnabled(True)
                self.btn_duplicar.setEnabled(False)
                self.plot_admitancia()

        except Exception as e:
            error_detallado = traceback.format_exc()
            QMessageBox.critical(self, "Error", 
                f"Error al leer el archivo Network.\n\n"
                f"Tipo: {type(e).__name__}\n"
                f"Mensaje: {str(e)}\n\n"+
                error_detallado)
            return
        
    def assign_input_GeneralBVDParams(self):
        # Assign General BVD parameters
        self.input_rs.setText(str(self.list_BVD[0].rs))
        self.input_rp.setText(str(self.list_BVD[0].rp))
        self.input_ql.setText(str(self.list_BVD[0].ql))
        self.input_qc.setText(str(self.list_BVD[0].qc))
        self.input_qa.setText(str(self.list_BVD[0].qa))

    def assign_input_MatchingNetworkParams(self):
        # Assign Matching Network parameters
        startBVD_type = self.network_parameters["typeseriesshunt_ini"]
        order = int(self.network_parameters["norder_ini"])
        mntype1 = self.network_parameters["mntype1"]
        matching_network_type = self.network_parameters["matching_network"]

        # Calculamos si el último elemento es shunt o series
        if order % 2 == 0:
            endBVD_type = "shunt" if startBVD_type == "series" else "series"
        else:
            endBVD_type = "series" if startBVD_type == "series" else "shunt"

        self.input_inputL.setText(str(self.network_parameters["input_l"]))
        self.input_inputL_type.setText("series" if startBVD_type == "shunt" else "shunt")

        if matching_network_type == "0.0":
            # Output matching network is a single inductance
            self.input_Lfini.setText(str(self.network_parameters["lfini2"]))
            self.input_Cfini.setText("N/A")
            self.input_matchnetw_type.setText("Single inductance in: " + "series" if endBVD_type == "shunt" else "shunt")
        else:
            # Output has a LC matching network
            if mntype1 == "s":
                self.input_Lfini.setText(str(self.network_parameters["lfini1"]))
                self.input_Cfini.setText(str(self.network_parameters["cfini2"]))
                self.input_matchnetw_type.setText("Lfini series + Cfini shunt")
            else:
                self.input_Lfini.setText(str(self.network_parameters["lfini2"]))
                self.input_Cfini.setText(str(self.network_parameters["cfini1"]))
                self.input_matchnetw_type.setText("Cfini shunt + Lfini series")

    def btn_readDirectoy_clicked(self):
        try:
            selected_path = fs.select_workspace_path()
            if selected_path:
                self.workspace_path = selected_path
                self.label_workspace_path.setText(f"Selected: {self.workspace_path}")
                self.label_workspace_path.setStyleSheet("color: green; font-size: 14px;")
        except Exception as e:
            error_detallado = traceback.format_exc()
            QMessageBox.critical(self, "Error", 
                f"Error al importar Keysight ADS DE.\n\n"
                f"Tipo: {type(e).__name__}\n"
                f"Mensaje: {str(e)}\n\n"+
                error_detallado)
            return
        
    def btn_convertBVD2COM_clicked(self):
        # Crear lista de BVD y convertir a lista COM
        if self.list_BVD is None:
            QMessageBox.critical(self, "Error", 
                                 "Error: No hay datos de BVD para convertir. \n"
                                 "Asegúrate de haber leído un archivo .ntw primero.")
            return
        else:
            try:
                self.list_COM = mat_bvd_com.compute_list_COM(self.list_BVD)
                self.list_COM = mat_bvd_com.compute_admitance_COM(self.list_COM, self.network_parameters)
                # self.filter_COM = mat_bvd_com.compute_filter_admitance(self.list_COM, self.network_parameters)

                # Rellenar los campos de Matching Network y Lossy BVD con los parámetros leídos
                self.combo_com.clear() # Borra el "Archivo no leído"
                for com in self.list_COM:
                    self.combo_com.addItem(com.name)
                    
                # Habilitamos el radio button de COM
                self.radio_com.setEnabled(True)
                self.radio_both.setEnabled(True)

                # Habilitamos el botón de convertir
                self.btn_convertir.setEnabled(False)
                self.btn_duplicar.setEnabled(True)

            except Exception as e:
                error_detallado = traceback.format_exc()
                QMessageBox.critical(self, "Error", 
                    f"Error crear lista BVD o al calcular los parámetros COM.\n\n"
                    f"Tipo: {type(e).__name__}\n"
                    f"Mensaje: {str(e)}\n\n"+
                    error_detallado)
                return

    def btn_createFullWorkspace_clicked(self):
        # Verificar que se haya ejecutado btn_readDirectoy_clicked primero
        if self.list_BVD is None:
            QMessageBox.critical(self, "Error", 
                                 "Error: No hay datos de BVD. \n"
                                 "Asegúrate de haber leído un archivo .ntw primero.")
            return
        
        if self.list_COM is None:
            QMessageBox.critical(self, "Error", 
                                 "Error: No hay datos de COM. \n"
                                 "Asegúrate de haber convertido los datos BVD a COM primero.")
            return
        
        if self.workspace_path is None:
            QMessageBox.critical(self, "Error", "Error: Debes hacer clic en 'Read Directory' primero")
            return

        # Obtener el nombre del workspace del input
        workspace_name = self.input_workspace_name.text().strip()
        if not workspace_name:
            QMessageBox.critical(self, "Error", "Error: Debes ingresar un nombre para el workspace")
            return

        # Crear la ruta completa del workspace
        full_workspace_path = self.workspace_path + "/" + workspace_name
        library_name = workspace_name + "_lib"

        # Check the keysight import is working properly
        try:
            ads.test_import_keysight_ads_de_example()
        except Exception as e:
            error_detallado = traceback.format_exc()
            QMessageBox.critical(self, "Error", 
                f"Error al importar Keysight ADS DE.\n\n"
                f"Tipo: {type(e).__name__}\n"
                f"Mensaje: {str(e)}\n\n"+
                error_detallado)
            return

        # Crear el workspace y la librería
        try:
            workspace = ads.create_and_open_an_empty_workspace(full_workspace_path)
            if workspace is None: 
                QMessageBox.critical(self, "Error", "Error: Ya existe un workspace con ese nombre")
                return

            lib = ads.create_a_library_and_add_it_to_the_workspace(workspace, library_name)
        except Exception as e:
            error_detallado = traceback.format_exc()
            QMessageBox.critical(self, "Error", 
                f"Error al crear el workspace o la librería.\n\n"
                f"Tipo: {type(e).__name__}\n"
                f"Mensaje: {str(e)}\n\n"+
                error_detallado)
            return
            
        # Crear los esquemáticos y los símbolos correspondientes
        try:
            # Buscamos si existe archivo .s2p con mismo nombre que el archivo network
            network_file_clean_path = pathlib.Path(self.network_file_path.strip('"'))
            datasets_folder = network_file_clean_path.parent.parent / "Datasets"
            sufijos = ["_2", "_1"]
            encontrado = False

            for sufijo in sufijos:
                dataset_s2p_file = f"{network_file_clean_path.stem}{sufijo}.s2p"
                path_obj = datasets_folder / dataset_s2p_file
                
                if path_obj.exists():
                    # Convertimos a string y envolvemos en comillas dobles literales
                    self.dataset_s2p_file_path = f'"{path_obj}"'
                    encontrado = True
                    break # Detenemos la búsqueda al hallar el primero

            if not encontrado:
                QMessageBox.information(self, "Info", f"No se ha encontrado el archivo .s2p correspondiente a la network:\n{self.network_file_path}")
                self.dataset_s2p_file_path = None

            ads.create_SchematicAndSymbol_lossyBVD(lib, library_name)
            ads.create_Schematic_ladderFilter_BVDlossy(lib, library_name, self.dataset_s2p_file_path, self.network_parameters, self.list_BVD)
            ads.create_SchematicAndSymbol_lossyCOM(lib, library_name)
            ads.create_Schematic_ladderFilter_COM(lib, library_name, self.dataset_s2p_file_path, self.network_parameters, self.list_COM)

        except Exception as e:
            error_detallado = traceback.format_exc()
            QMessageBox.critical(self, "Error", 
                f"Error al crear el esquema.\n\n"
                f"Tipo: {type(e).__name__}\n"
                f"Mensaje: {str(e)}\n\n"+
                error_detallado)
            return
        
        QMessageBox.information(self, "Éxito", f"Workspace '{workspace_name}' creado con éxito en:\n{full_workspace_path}")

    def btn_duplicar_resonadores_clicked(self):
        if self.list_BVD is None:
            QMessageBox.critical(self, "Error", 
                                 "Error: No hay datos de BVD. \n"
                                 "Asegúrate de haber leído un archivo .ntw primero.")
        
        elif self.list_COM is None:
            QMessageBox.critical(self, "Error", 
                                 "Error: No hay datos de COM. \n"
                                 "Asegúrate de haber convertido los datos BVD a COM primero.")

        try:
            # Duplicamos los BVDs de la lista que sean necesarios según digitsNidt del COM
            self.list_BVD, self.list_COM = mat_bvd_com.duplicate_resonators(self.list_BVD, self.list_COM, self.network_parameters)
            
            # Rellenar los campos de Matching Network y Lossy BVD con los parámetros leídos
            self.combo_bvd.clear()
            for bvd in self.list_BVD:
                self.combo_bvd.addItem(bvd.name)

            self.combo_com.clear()
            for com in self.list_COM:
                self.combo_com.addItem(com.name)

            self.combo_elemento_graf.clear()
            for bvd in self.list_BVD:
                self.combo_elemento_graf.addItem(bvd.name.replace("BVD", "Elemento"))

            # Ponemos todos los combos en la primera posición
            self.radio_bvd.setChecked(True)

            self.combo_bvd.setCurrentIndex(0)
            self.combo_com.setCurrentIndex(0)
            self.combo_elemento_graf.setCurrentIndex(0)

            self.assign_input_GeneralBVDParams()

            # Desactivamos el botón de duplicar resonadores
            self.btn_duplicar.setEnabled(False)

        except Exception as e:
            error_detallado = traceback.format_exc()
            QMessageBox.critical(self, "Error", 
                f"Error al leer el archivo Network.\n\n"
                f"Tipo: {type(e).__name__}\n"
                f"Mensaje: {str(e)}\n\n"+
                error_detallado)
            return
        

def formato_ingenieria(valor, precision=8):
    if valor == 0:
        return "0"
    
    # 1. Hallar el exponente (potencia de 10)
    exp = int(math.floor(math.log10(abs(valor))))
    # 2. Ajustar al múltiplo de 3 inferior
    eng_exp = (exp // 3) * 3
    # 3. Calcular el coeficiente
    coef = valor / (10**eng_exp)
    
    return f"{coef:.{precision}f}e{eng_exp}"

# Run the test if this file is executed directly
if __name__ == "__main__":

    app = QApplication.instance() # or QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()
