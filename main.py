import importlib
import pathlib
import traceback
import math
import time
import ads_utils as ads
import fs_utils as fs
import bvd_com_computations as mat_bvd_com

from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QLineEdit, QMessageBox, QGroupBox, QSizePolicy, QRadioButton, QButtonGroup,
                               QComboBox, QFormLayout, QCheckBox, QMenu)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import numpy as np

importlib.reload(ads)
importlib.reload(fs)
importlib.reload(mat_bvd_com)

# ========================== VARIABLES GLOBALES ===========================
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        # Usamos layout='constrained' o llamamos a tight_layout()
        self.fig = Figure(figsize=(width, height), dpi=dpi, layout='constrained')
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)

USE_DEFAULT_WORKSPACE_NAME = True
CREATE_DEBUGGING_SCHEMATIC = False

DEFAULT_WORKSPACE_NAME = "unnamed_wrk"

# ========================== CLASE PRINCIPAL DE LA APLICACIÓN ===========================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.list_BVD = None
        self.list_COM = None
        self.dataset_s2p_file_path = None
        self.mask = None
        self.network_file_path = None
        self.workspace_path = None
        self.filterResponse = None

        self.setWindowTitle("TFG-SMOSfilter")
        self.setGeometry(100, 100, 1000, 700)

        self.setup_menu_bar()

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
        self.panel_izquierdo_contedor = QWidget()
        self.layout_left_total = QVBoxLayout(self.panel_izquierdo_contedor)
        self.setup_left_panel()

        # --- 2.5. PANEL CENTRAL (MATCHING NETWORKS + COM CONSTANTS)
        self.panel_central_contenedor = QWidget()
        self.layout_central_total = QVBoxLayout(self.panel_central_contenedor)
        self.setup_central_panel()

        # --- 3. PANEL DERECHO (COM + GRÁFICO) ---
        self.panel_derecho_contenedor = QWidget()
        self.layout_derecha_total = QVBoxLayout(self.panel_derecho_contenedor)
        self.setup_right_panel()

        # --- 4. ENSAMBLAJE CUERPO ---
        self.panel_izquierdo_contedor.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.panel_central_contenedor.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.panel_izquierdo_contedor.setMinimumWidth(300)
        self.panel_central_contenedor.setMinimumWidth(300)
        self.panel_derecho_contenedor.setMinimumWidth(600)
        
        self.layout_cuerpo.addWidget(self.panel_izquierdo_contedor, stretch=0)
        self.layout_cuerpo.addWidget(self.panel_central_contenedor, stretch=0)
        self.layout_cuerpo.addWidget(self.panel_derecho_contenedor, stretch=1)
        
        layout_principal.addLayout(self.layout_cuerpo)

        # --- 5. BOTÓN CREAR WORKSPACE ---
        self.setup_footer()
        layout_principal.addLayout(self.barra_inferior)

        self.aplicar_cursor_pointer()
            
    def setup_menu_bar(self):
        # Crear la barra de menú
        bar = self.menuBar()

        # ==========================================
        # 1) MENÚ FILE (Botones normales)
        # ==========================================
        file_menu = bar.addMenu("&File")

        self.action_open = QAction("Select new Network File", self)
        self.action_open.triggered.connect(self.btn_readNetworkFile_clicked)
        file_menu.addAction(self.action_open)

        self.action_workspace = QAction("Select Workspace Directory", self)
        self.action_workspace.triggered.connect(self.btn_readDirectoy_clicked)
        file_menu.addAction(self.action_workspace)

        file_menu.addSeparator() # Línea divisoria

        self.action_save = QAction("Save BVD and COM data", self)
        self.action_save.triggered.connect(self.on_save_data)
        file_menu.addAction(self.action_save)

        # ==========================================
        # 2) MENÚ VIEW (Checkboxes)
        # ==========================================
        view_menu = bar.addMenu("&View")

        self.check_matching = QAction("Show Matching Network Parameters", self)
        self.check_matching.setCheckable(True)
        self.check_matching.setChecked(False) 
        self.check_matching.toggled.connect(self.update_view)
        view_menu.addAction(self.check_matching)

        # ==========================================
        # 3) MENÚ OPTIONS (Checkboxes)
        # ==========================================
        options_menu = bar.addMenu("&Options")

        self.check_duplicate = QAction("Duplicate Resonators when necessary", self)
        self.check_duplicate.setCheckable(True)
        self.check_duplicate.setChecked(True) 
        options_menu.addAction(self.check_duplicate)

        self.check_debug = QAction("Create debugging Schematic and DDS", self)
        self.check_debug.setCheckable(True)
        self.check_debug.setChecked(False)
        options_menu.addAction(self.check_debug)

    def setup_header(self):
        self.barra_superior = QHBoxLayout()

        self.btn_readNetwork = QPushButton("Select Network File")
        self.btn_readNetwork.clicked.connect(self.btn_readNetworkFile_clicked)

        self.btn_readMask = QPushButton("Select Mask File")
        self.btn_readMask.clicked.connect(self.btn_readMask_clicked)

        self.btn_directorio = QPushButton("Select Workspace Directory")
        self.btn_directorio.clicked.connect(self.btn_readDirectoy_clicked)
        
        self.barra_superior.addWidget(self.btn_readNetwork)
        self.barra_superior.addWidget(self.btn_readMask)
        self.barra_superior.addWidget(self.btn_directorio)
        self.barra_superior.addStretch()

    def setup_sub_header(self):
        self.sub_barra_superior = QVBoxLayout()

        self.label_network_file = QLabel("No file selected")
        self.label_network_file.setStyleSheet("color: red; font-size: 14px;")

        self.label_mask_file = QLabel("No file selected")
        self.label_mask_file.setStyleSheet("color: red; font-size: 14px;")

        self.label_workspace_path = QLabel("No directory selected")
        self.label_workspace_path.setStyleSheet("color: red; font-size: 14px;")

        self.sub_barra_superior.addWidget(self.label_network_file)
        self.sub_barra_superior.addWidget(self.label_mask_file)
        self.sub_barra_superior.addWidget(self.label_workspace_path)

    def setup_footer(self):
        self.barra_inferior = QHBoxLayout()

        self.label_workspace_name = QLabel("Workspace Name:")
        self.input_workspace_name = QLineEdit()
        self.input_workspace_name.setPlaceholderText(DEFAULT_WORKSPACE_NAME)
        self.input_workspace_name.setFixedWidth(200)
        self.input_workspace_name.setMaxLength(20)

        self.btn_create_workspace = QPushButton("Create ADS Workspace")
        self.btn_create_workspace.clicked.connect(self.btn_createFullWorkspace_clicked)
        self.btn_create_workspace.setStyleSheet("background-color: #fffce6; color: black; font-weight: bold;")

        self.barra_inferior.addWidget(self.label_workspace_name)
        self.barra_inferior.addWidget(self.input_workspace_name)
        self.barra_inferior.addStretch()
        self.barra_inferior.addWidget(self.btn_create_workspace)
        
    def setup_left_panel(self):
        self.layout_left_total.setContentsMargins(0, 0, 0, 0) # Quitar márgenes internos

        # Sub-bloque COM (Superior)
        self.bloque_bvd = QGroupBox("COM Parameters")
        self.bloque_bvd.setMaximumWidth(500)
        self.bloque_bvd.setStyleSheet("""
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
        
        self.layout_bvd = QVBoxLayout(self.bloque_bvd)
        self.setup_bvd_formLayout()

        # Añadimos los sub-bloques al panel central
        self.layout_left_total.addWidget(self.bloque_bvd)
        
        # Añadimos un espaciador al final para que si ocultas uno, 
        # el otro no ocupe toda la pantalla a la fuerza.
        self.layout_left_total.addStretch(1)

    def setup_bvd_formLayout(self):
        # 1. El Desplegable (Selector)
        self.combo_bvd = QComboBox()
        self.combo_bvd.setFixedWidth(200)
        self.combo_bvd.addItem("File .ntw not selected")
        
        # Conectamos el cambio de selección a una función
        self.combo_bvd.currentIndexChanged.connect(self.actualizar_formulario_bvd)
        self.combo_bvd.currentIndexChanged.connect(self.unificar_grafico_bvd)
        
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

        # Campos de BVD general params
        self.input_rs = QLineEdit()
        self.input_rp = QLineEdit()
        self.input_ql = QLineEdit()
        self.input_qc = QLineEdit()
        self.input_qa = QLineEdit()
        
        # Configuramos como "Solo lectura" y ponemos placeholders
        self.campos_form_bvd = [self.input_c0, self.input_cp, self.input_ca, self.input_la, self.input_fs, self.input_fp, self.input_ladd_ser,
                    self.input_ladd_shu, self.input_cadd_ser, self.input_cadd_shu, self.input_ladd_ground]
        for inp in self.campos_form_bvd:
            inp.setReadOnly(True)
            inp.setPlaceholderText("---")
            inp.setStyleSheet("background-color: #f0f0f0; color: #555;")

        # Añadimos al layout del formulario
        self.form_layout_BVD = QFormLayout()
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


        # Configuramos como "Solo lectura" y ponemos placeholders
        self.campos_form_bvdgeneral = [self.input_rs, self.input_rp, self.input_ql, self.input_qc, self.input_qa]
        for inp in self.campos_form_bvdgeneral:
            inp.setReadOnly(True)
            inp.setPlaceholderText("---")
            inp.setStyleSheet("background-color: #f0f0f0; color: #555;")

        # Añadir parámetros generales (rs, rp, ql, qc, qa) al formulario de BVD
        self.form_layout_BVD_general = QFormLayout()
        self.form_layout_BVD_general.addRow("Rs (Ω):", self.input_rs)
        self.form_layout_BVD_general.addRow("Rp (Ω):", self.input_rp)
        self.form_layout_BVD_general.addRow("Ql (-):", self.input_ql)
        self.form_layout_BVD_general.addRow("Qc (-):", self.input_qc)
        self.form_layout_BVD_general.addRow("Qa (-):", self.input_qa)

        # 3. Montaje en el panel izquierdo (el que ya tenías)
        # Limpiamos el layout_bvd por si acaso y añadimos
        self.layout_bvd.addWidget(self.combo_bvd)
        self.layout_bvd.addSpacing(10) # Espacio visual
        self.layout_bvd.addLayout(self.form_layout_BVD)

        self.layout_bvd.addSpacing(20) # Espacio visual
        bvd_general_label=QLabel("General BVD parameters:")
        bvd_general_label.setStyleSheet("font-weight: bold; color: darkgray;")
        self.layout_bvd.addWidget(bvd_general_label)
        self.layout_bvd.addLayout(self.form_layout_BVD_general)
        self.layout_bvd.addStretch(1)

    def actualizar_formulario_bvd(self, index):
        """Esta función se llama cada vez que eliges un BVD en el combo"""
        # Si no hay datos (solo el mensaje por defecto) o la lista está vacía
        if not self.list_BVD or self.combo_bvd.currentText() == "File .ntw not selected":
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

        # Sub-bloque COM (Superior)
        self.bloque_com = QGroupBox("COM Parameters")
        self.bloque_com.setMaximumWidth(500)
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
        self.setup_com_formLayout()

        # Añadimos los sub-bloques al panel central
        self.layout_central_total.addWidget(self.bloque_com)
        
        # Añadimos un espaciador al final para que si ocultas uno, 
        # el otro no ocupe toda la pantalla a la fuerza.
        self.layout_central_total.addStretch(1)

    def setup_com_formLayout(self):
        K11 = -82053.9 - 1j*450
        K12 = 59340.0

        VP = 3741.8
        EPS_R = 39.56
        EPS_0 = 8.854e-12
        DUTY = 0.55

        Z0_PRIMA = 1
        R_SHUNT = 4e5
        R_SERIE = 0.1

        # 1. El Desplegable (Selector)
        self.combo_com = QComboBox()
        self.combo_com.setFixedWidth(200)
        self.combo_com.addItem("Pending Conversion")
        
        # Conectamos el cambio de selección a una función
        self.combo_com.currentIndexChanged.connect(self.actualizar_formulario_com)
        self.combo_com.currentIndexChanged.connect(self.unificar_grafico_com)
        
        # Creamos los campos (QLineEdit)
        self.input_pitch = QLineEdit()
        self.input_pitch_refl = QLineEdit()
        self.input_Ct_COM = QLineEdit()
        self.input_digitsIDT = QLineEdit()
        self.input_digitsREFL = QLineEdit()
        
        # Nuevos campos para la segunda columna
        self.input_aperture = QLineEdit()
        self.input_alpha = QLineEdit()
        self.input_alpha_n = QLineEdit()
        self.input_fs_COM = QLineEdit()
        self.input_fp_COM = QLineEdit()
        
        # Configuramos como "Solo lectura" y ponemos placeholders
        self.campos_form_com = [self.input_pitch, self.input_pitch_refl, self.input_aperture, self.input_Ct_COM, self.input_digitsIDT, 
                    self.input_digitsREFL, self.input_alpha, self.input_alpha_n, self.input_fs_COM, self.input_fp_COM]
        for inp in self.campos_form_com:
            inp.setReadOnly(True)
            inp.setPlaceholderText("---")
            inp.setStyleSheet("background-color: #f0f0f0; color: #555;")

        # Creamos los campos de constantes
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
        self.form_layout_COM = QFormLayout()
        self.form_layout_COM.addRow("p IDT (m):", self.input_pitch)
        self.form_layout_COM.addRow("p REFL (m):", self.input_pitch_refl)
        self.form_layout_COM.addRow("Ap (λ0):", self.input_aperture)
        self.form_layout_COM.addRow("Ct (H):", self.input_Ct_COM)
        self.form_layout_COM.addRow("Digits IDT (-):", self.input_digitsIDT)
        self.form_layout_COM.addRow("Digits REFL (-):", self.input_digitsREFL)
        self.form_layout_COM.addRow("α (-):", self.input_alpha)
        self.form_layout_COM.addRow("α_n (-):", self.input_alpha_n)

        # Formulario Derecho: Resultados de Frecuencia
        # self.form_layout_COM.addRow("fs (Hz):", self.input_fs_COM)
        # self.form_layout_COM.addRow("fp (Hz):", self.input_fp_COM)

        # Añadimos al layout del formulario consts
        self.form_layout_constCOM = QFormLayout()
        self.form_layout_constCOM.addRow("k11 (?):", self.input_K11)
        self.form_layout_constCOM.addRow("k12 (?):", self.input_K12)
        self.form_layout_constCOM.addRow("Vp (m/s):", self.input_VP)
        self.form_layout_constCOM.addRow("ε_r (-):", self.input_EPS_R)
        self.form_layout_constCOM.addRow("ε_0 (-):", self.input_EPS_0)
        self.form_layout_constCOM.addRow("η (-):", self.input_DUTY)
        # self.form_layout_constCOM.addRow("Z0' (Ω):", self.input_Z0_PRIMA)
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
        self.layout_com.addWidget(self.combo_com)
        self.layout_com.addSpacing(10) # Espacio visual
        self.layout_com.addLayout(self.form_layout_COM)

        self.layout_com.addSpacing(20) # Espacio visual
        label_general_com=QLabel("Dataset COM constants:")
        label_general_com.setStyleSheet("font-weight: bold; color: darkgray;")
        self.layout_com.addWidget(label_general_com)
        self.layout_com.addLayout(self.form_layout_constCOM)
        self.layout_com.addStretch()

    def setup_matchnetw_formLayout(self):
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
        self.form_layout_MN.addRow("L_output type:", self.input_matchnetw_type)
        self.form_layout_MN.addRow("C_output (pF):", self.input_Cfini)
        self.form_layout_MN.addRow("C_output type:", self.input_Cfini_type)

        # 3. Montaje en el panel derecho
        # Limpiamos el layout_com por si acaso y añadimos
        self.layout_matchnetw.addSpacing(10) # Espacio visual
        self.layout_matchnetw.addLayout(self.form_layout_MN)
        self.layout_matchnetw.addStretch()

    def setup_right_panel(self):
        self.layout_derecha_total.setContentsMargins(0, 0, 0, 0) # Quitar márgenes internos       

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
        self.setup_matchnetw_formLayout()

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
        self.layout_derecha_total.addWidget(self.bloque_matchnetw, stretch=0)
        self.layout_derecha_total.addWidget(self.bloque_grafico, stretch=1)

        self.update_view()

    def actualizar_formulario_com(self):
        index = self.combo_com.currentIndex()

        """Esta función se llama cada vez que eliges un BVD en el combo"""
        # Si no hay datos (solo el mensaje por defecto) o la lista está vacía
        if not self.list_COM or self.combo_com.currentText() == "Pending Conversion":
            return

        # Obtenemos el objeto BVD seleccionado
        com_seleccionado = self.list_COM[index]
        
        # Rellenamos los campos
        self.input_pitch.setText(formato_ingenieria(com_seleccionado.d, 12))
        self.input_pitch_refl.setText(formato_ingenieria(com_seleccionado.dR, 12))
        self.input_Ct_COM.setText(formato_ingenieria(com_seleccionado.Ct))
        self.input_digitsIDT.setText(str(com_seleccionado.digitsN))
        self.input_digitsREFL.setText(str(com_seleccionado.digitsNR))

        self.input_aperture.setText(formato_ingenieria(com_seleccionado.Ap))
        self.input_alpha.setText(str(com_seleccionado.alpha))
        self.input_alpha_n.setText(str(com_seleccionado.alpha_n))
        self.input_fs_COM.setText(formato_ingenieria(com_seleccionado.fs))
        self.input_fp_COM.setText(formato_ingenieria(com_seleccionado.fp))

        self.input_VP.setText(str(com_seleccionado.constants.vp))
        self.input_K11.setText(str(com_seleccionado.constants.k11))
        self.input_K12.setText(str(com_seleccionado.constants.k12))
        self.input_EPS_R.setText(str(com_seleccionado.constants.eps_r))

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
        self.combo_elemento_graf.addItem("No data")
        self.combo_elemento_graf.setFixedWidth(200)
        
        # 2. Botones de Radio (BVD vs COM)
        self.radio_bvd = QRadioButton("BVD")
        self.radio_com = QRadioButton("COM")
        self.radio_both = QRadioButton("Both")
        self.radio_bvd.setChecked(True) # BVD por defecto

        # 3. Checkbox de Mask
        self.checkb_mask = QCheckBox("Plot Mask")
        self.checkb_mask.setChecked(False)
        
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
        barra_filtros.addStretch()
        barra_filtros.addWidget(self.checkb_mask)

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
        self.checkb_mask.toggled.connect(self.plot_admitancia)

    def plot_admitancia(self):
        order = len(self.list_BVD)
        idx = self.combo_elemento_graf.currentIndex()
        
        color_dataBVD = "green"
        color_dataCOM = "goldenrod"
        color_dataFilter = "goldenrod"
        label_dataBVD = f"BVD - Element {idx+1}"
        label_dataCOM = f"COM - Element {idx+1}"
        label_dataFilter = "COM - Filter"

        # Decidir qué fuente usar
        if idx < order:
            dataBVD = self.list_BVD[idx] if (self.radio_bvd.isChecked() or self.radio_both.isChecked()) else None
            dataCOM = self.list_COM[idx] if (self.radio_com.isChecked() or self.radio_both.isChecked()) else None
            dataFilter = None
        else:
            dataBVD = None
            dataCOM = None
            dataFilter = self.filterCOM_ADS_Response
            
        self.canvas.axes.cla()

        # Verificamos que el objeto seleccionado tenga los datos
        if dataBVD is not None and (hasattr(dataBVD, 'Y') or dataBVD.Y is not None):
            # CONVERSIÓN A dB
            magnitud_Y_dB = 20 * np.log10(np.abs(dataBVD.Y) + 1e-20)
            # Ploteamos f (log) vs Y (dB lineal)
            self.canvas.axes.plot(dataBVD.f, magnitud_Y_dB, label=label_dataBVD, color=color_dataBVD)

            if dataCOM is None and hasattr(dataBVD, "fs"):
                frecuencias_interes = [dataBVD.fs, dataBVD.fp]
                frecuencias_interes_names = ["fs_BVD", "fp_BVD"]
                for f_marcar, f_marcar_name in zip(frecuencias_interes, frecuencias_interes_names):
                    # Solo marcamos si está dentro del rango de los datos actuales
                    if dataBVD.f.min() <= f_marcar <= dataBVD.f.max():
                        idx = np.abs(dataBVD.f - f_marcar).argmin()
                        self.canvas.axes.plot(dataBVD.f[idx], magnitud_Y_dB[idx], 'kx')

                        ha_val = 'left'
                        x_pos = dataBVD.f[idx] + (dataBVD.f.max() - dataBVD.f.min()) * 0.03
                        # Ajuste específico para "fp"
                        if "fp" in f_marcar_name.lower():
                            ha_val = 'right'
                            x_pos = dataBVD.f[idx] - (dataBVD.f.max() - dataBVD.f.min()) * 0.03

                        self.canvas.axes.text(
                            x_pos, 
                            magnitud_Y_dB[idx],
                            f"{f_marcar_name}: {f_marcar:.4e}",
                            verticalalignment='center',
                            horizontalalignment=ha_val,  # Dinámico: 'right' para fp, 'left' para los demás
                            fontsize=9,
                            clip_on=True
                        )

        if dataCOM is not None and (hasattr(dataCOM, 'Y') or dataCOM.Y is not None):
            # CONVERSIÓN A dB
            magnitud_Y_dB = 20 * np.log10(np.abs(dataCOM.Y) + 1e-20)
            # Ploteamos f (log) vs Y (dB lineal)
            self.canvas.axes.plot(dataCOM.f, magnitud_Y_dB, label=label_dataCOM, color=color_dataCOM)

            if dataBVD is None and hasattr(dataCOM, "fs"):
                frecuencias_interes = [dataCOM.fs, dataCOM.fp]
                frecuencias_interes_names = ["fs_COM", "fp_COM"]
                for f_marcar, f_marcar_name in zip(frecuencias_interes, frecuencias_interes_names):
                    # Solo marcamos si está dentro del rango de los datos actuales
                    if dataCOM.f.min() <= f_marcar <= dataCOM.f.max():
                        idx = np.abs(dataCOM.f - f_marcar).argmin()
                        self.canvas.axes.plot(dataCOM.f[idx], magnitud_Y_dB[idx], 'kx')
                        
                        ha_val = 'left'
                        x_pos = dataCOM.f[idx] + (dataCOM.f.max() - dataCOM.f.min()) * 0.03
                        # Ajuste específico para "fp"
                        if "fp" in f_marcar_name.lower():
                            ha_val = 'right'
                            x_pos = dataCOM.f[idx] - (dataCOM.f.max() - dataCOM.f.min()) * 0.03

                        self.canvas.axes.text(
                            x_pos, 
                            magnitud_Y_dB[idx],              # Coordenada Y
                            f"{f_marcar_name}: {f_marcar:.4e}",
                            verticalalignment='center',
                            horizontalalignment=ha_val,      # Empieza a la derecha del punto
                            fontsize=9,
                            clip_on=True
                        )

        if dataFilter is not None:
            # CONVERSIÓN A dB
            magnitud_Y_dB = 20 * np.log10(np.abs(dataFilter.Y) + 1e-20)
            # Ploteamos f (log) vs Y (dB lineal)
            self.canvas.axes.plot(dataFilter.f, magnitud_Y_dB, label=label_dataFilter, color=color_dataFilter)

            # Only when the filter is plotted, we plot the mask if wanted
            if self.mask is not None and self.checkb_mask.isChecked():
                try:
                    if self.list_BVD is not None:
                        f_min = self.list_BVD[0].f.min()
                        f_max = self.list_BVD[0].f.max()

                        for limit in self.mask.limits:
                            if limit.loss_type != "S11":
                                # Recortar límite al rango visible
                                x_start = max(limit.fstart, f_min)
                                x_stop = min(limit.fstop, f_max)

                                # Si el límite queda fuera del rango visible, ignorarlo
                                if x_start >= x_stop:
                                    continue

                                # Color según tipo
                                if limit.upper_lower.lower() == "upper":
                                    color = "darkblue"
                                else:
                                    color = "darkred"

                                # Dibujar línea horizontal del límite
                                self.canvas.axes.plot(
                                    [x_start, x_stop],
                                    [limit.value_dB, limit.value_dB],
                                    color=color,
                                    linewidth=1.2,   # ligeramente menor que plots principales
                                    linestyle='--'
                                )

                except Exception:
                    QMessageBox.critical(self, "Error", "Error drawing mask.\n""The read mask format might be incorrect or broken.")
                    pass

        self.canvas.axes.set_xlabel("Frequency (Hz)")
        self.canvas.axes.set_ylabel("Admitance (dB)")
        
        # La escala Y ahora es lineal porque los datos YA están en dB
        self.canvas.axes.set_yscale('linear') 
        
        self.canvas.axes.grid(True, which="both", linestyle='--', alpha=0.5)
        self.canvas.axes.legend()
        
        self.canvas.draw()

    # ============================================================== FUNCIONES AUXILIARES ==============================================================

    def unificar_grafico_admitancia(self, index):
        # Actualizamos los formularios BVD y GRPHICS para que haya uniformidad en la GUI
        if self.list_BVD is not None and index < len(self.list_BVD):
            self.combo_bvd.setCurrentIndex(index)
            self.combo_com.setCurrentIndex(index)

    def unificar_grafico_com(self, index):
        # Actualizamos los formularios BVD y GRPHICS para que haya uniformidad en la GUI
        self.combo_bvd.setCurrentIndex(index)
        self.combo_elemento_graf.setCurrentIndex(index)

    def unificar_grafico_bvd(self, index):
        # Actualizamos los formularios BVD y GRPHICS para que haya uniformidad en la GUI
        self.combo_com.setCurrentIndex(index)
        self.combo_elemento_graf.setCurrentIndex(index)
        
    def aplicar_cursor_pointer(self):
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
        
        # 2. Buscamos todos los combobox
        check_boxs = self.findChildren(QCheckBox)
        for check_box in check_boxs:
            check_box.setCursor(Qt.PointingHandCursor)
    
    # ============================================================== FUNCIONES DE LOS BOTONES ==============================================================
    def on_save_data(self):
        print("Guardando datos...")

    def update_view(self):
        # 1. Visibilidad de los bloques internos
        show_mn = self.check_matching.isChecked()
        self.bloque_matchnetw.setVisible(show_mn)
        
    def btn_readNetworkFile_clicked(self):
        try:
            file_path_network = fs.select_file_to_read("Network files (*.ntw)|*.ntw|Text Files (*.txt)|*.txt|All Files (*.*)|*.*")
            if file_path_network:
                self.network_file_path = file_path_network
                self.label_network_file.setText(f"Selected: {file_path_network}")
                self.label_network_file.setStyleSheet("color: green; font-size: 14px;")
                self.network_parameters = fs.read_and_parse_file(file_path_network)

                # Crear la lista de BVDs a partir de los parámetros leídos
                self.list_BVD = mat_bvd_com.create_list_BVD(self.network_parameters)
                
                # Rellenar los campos de Matching Network y Lossy BVD con los parámetros leídos
                self.combo_bvd.clear() # Borra el "Archivo no leído"
                for bvd in self.list_BVD:
                    self.combo_bvd.addItem(bvd.name)
                
                self.assign_input_GeneralBVDParams()
                self.assign_input_MatchingNetworkParams()

                # Ejecutamos la conversión a los parámetros COM
                self.convertBVD2COM()

                # Rellenar el combo del gráfico con los elementos disponibles
                self.combo_elemento_graf.clear() # Borra el "Archivo no leído"
                for bvd in self.list_BVD:
                    self.combo_elemento_graf.addItem(bvd.name.replace("BVD", "Element"))

                self.radio_bvd.setEnabled(True)
                self.radio_com.setEnabled(True)
                self.radio_both.setEnabled(True)

                self.plot_admitancia()

        except Exception as e:
            error_detallado = traceback.format_exc()
            QMessageBox.critical(self, "Error", 
                f"Error reading network file.\n\n"
                f"Type: {type(e).__name__}\n"
                f"Message: {str(e)}\n\n"+
                error_detallado)
            return
        
    def btn_readMask_clicked(self):
        try:
            file_path_mask = fs.select_file_to_read("Mask files (*.msk)|*.msk|Text Files (*.txt)|*.txt|All Files (*.*)|*.*")
            if file_path_mask:
                self.label_mask_file.setText(f"Selected: {file_path_mask}")
                self.label_mask_file.setStyleSheet("color: green; font-size: 14px;")
                self.mask = fs.create_mask(file_path_mask)
                log_mask(self.mask)

        except Exception as e:
            error_detallado = traceback.format_exc()
            QMessageBox.critical(self, "Error", 
                f"Error reading network file.\n\n"
                f"Type: {type(e).__name__}\n"
                f"Message: {str(e)}\n\n"+
                error_detallado)
            return
        return

    def convertBVD2COM(self):
        # Crear lista de BVD y convertir a lista COM
        try:
            # Creamos la lista de elementos COM con los parámetros iniciales
            self.list_COM = mat_bvd_com.compute_list_COM(self.list_BVD, self.network_parameters)

            # Rellenar los campos de Matching Network y Lossy BVD con los parámetros leídos
            self.combo_com.clear() # Borra el "Archivo no leído"
            for com in self.list_COM:
                self.combo_com.addItem(com.name)
            
            self.actualizar_formulario_com()
            self.plot_admitancia()

        except Exception as e:
            error_detallado = traceback.format_exc()
            QMessageBox.critical(self, "Error", 
                f"Error creating BVD list or computing COM parameters.\n\n"
                f"Type: {type(e).__name__}\n"
                f"Message: {str(e)}\n\n"+
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
                f"Error importing Keysight ADS DE.\n\n"
                f"Type: {type(e).__name__}\n"
                f"Message: {str(e)}\n\n"+
                error_detallado)
            return

    def btn_createFullWorkspace_clicked(self):
        # ============================================= Verificaciones iniciales del flujo de trabajo =============================================
        if self.list_BVD is None:
            QMessageBox.critical(self, "Error", "Error: No BVD data. \n Select a network file first")
            return
        if self.list_COM is None:
            QMessageBox.critical(self, "Error", "Error: No COM data. \n Convert BVD -> COM parameters first")
            return
        if self.workspace_path is None:
            QMessageBox.critical(self, "Error", "Error: Select a workspace directory first")
            return
        
        # ====================================================== Buscamos si existe archivo .s2p ======================================================
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
                break

        if not encontrado:
            boton_pulsado = QMessageBox.question(
                self, 
                "Missing Network File", 
                f"File .s2p not found for the selected network:\n\n{self.network_file_path}\n\nDo you want to proceed with the creation of the workspace?", 
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.Yes
            )

            if boton_pulsado == QMessageBox.Yes:
                self.dataset_s2p_file_path = None
            else:
                return

        # ====================================================== Comprobamos importación de ADS ======================================================
        try:
            ads.test_import_keysight_ads_de_example()
        except Exception as e:
            error_detallado = traceback.format_exc()
            QMessageBox.critical(self, "Error", 
                f"Error importing Keysight ADS DE.\n\n"
                f"Type: {type(e).__name__}\n"
                f"Message: {str(e)}\n\n"+
                error_detallado)
            return

        # ====================================================== Obtener el nombre del workspace ======================================================
        workspace_name = self.input_workspace_name.text().strip()
        if not workspace_name:
            if not USE_DEFAULT_WORKSPACE_NAME:
                QMessageBox.critical(self, "Error", "Error: Input a workspace name first")
                return
            workspace_name = DEFAULT_WORKSPACE_NAME

        # Crear la ruta completa del workspace
        full_workspace_path = self.workspace_path + "/" + workspace_name
        library_name = workspace_name + "_lib"

        # ====================================================== Crear el workspace y la librería ======================================================
        try:
            workspace = ads.create_and_open_an_empty_workspace(full_workspace_path)
            if workspace is None: 
                QMessageBox.critical(self, "Error", "Error: A workspace with that name already exists")
                return
            library = ads.create_a_library_and_add_it_to_the_workspace(workspace, library_name)
        except Exception as e:
            error_detallado = traceback.format_exc()
            QMessageBox.critical(self, "Error", 
                f"Error creating the workspace or library.\n\n"
                f"Type: {type(e).__name__}\n"
                f"Message: {str(e)}\n\n"+
                error_detallado)
            return
            
        # Crear los esquemáticos y los símbolos correspondientes
        try:
            inicio = time.time()       
            # =============================================== 0) Generate BVD and COM symbols ===============================================
            ads.create_SchematicAndSymbol_lossyBVD(library, library_name)
            ads.create_SchematicAndSymbol_lossyCOM(library, library_name)
            log_tiempo(f"Paso 1 completado en: {time.time() - inicio:.2f} segundos")

            # =============================================== 1) Duplicate resonnators if necessary ===============================================
            if self.check_duplicate.isChecked():
                list_COM_ADS = mat_bvd_com.duplicar_resonadores(self.list_BVD, self.list_COM, self.network_parameters)
                log_tiempo(f"Paso 1.5 completado en: {time.time() - inicio:.2f} segundos")
            else:
                list_COM_ADS = self.list_COM

            # =============================================== 2.0) Genearate BUSBAR layout and simulation ===============================================
            library.setup_schematic_tech()
            library.create_layout_tech_std_ads("millimeter", 10000, False)

            for com in list_COM_ADS:
                ads.create_busbars_layout(library, library_name, com)

            # ========================================== 2.1) Debugging and tunning schematic and DDS ==========================================
            if self.check_debug.isChecked():
                ads.create_Schematic_debugging(full_workspace_path, library_name, self.network_parameters, self.list_BVD, list_COM_ADS)
                log_tiempo(f"Paso 2 completado en: {time.time() - inicio:.2f} segundos")
                ads.create_DDS_debugging(full_workspace_path, len(self.list_BVD), self.network_parameters["typeseriesshunt_ini"])
                log_tiempo(f"Paso 3 completado en: {time.time() - inicio:.2f} segundos")

            # ============================================ 3) Generate BVD and COM LADDER FILTERS ============================================
            ads.create_Schematic_ladderFilter_BVD(full_workspace_path, library_name, self.dataset_s2p_file_path, self.network_parameters, self.list_BVD)
            ads.create_Schematic_ladderFilter_COM(full_workspace_path, library_name, self.dataset_s2p_file_path, self.network_parameters, list_COM_ADS)
            log_tiempo(f"Paso 4 completado en: {time.time() - inicio:.2f} segundos")

            # ========================================== 4) Generate BVD and COM filters' DDS pages ==========================================
            ads.create_DDS_ladderFilter_COM(full_workspace_path)
            log_tiempo(f"Paso 5 completado en: {time.time() - inicio:.2f} segundos")

            # ========================================== 5) Extract data from COM FILTER and plot ==========================================
            self.filterCOM_ADS_Response = ads.extract_data_filterCOM(full_workspace_path)
            if not self.combo_elemento_graf.count() > len(self.list_BVD):
                self.combo_elemento_graf.addItem("Full COM filter")
            self.combo_elemento_graf.setCurrentIndex(len(self.list_BVD))

        except Exception as e:
            error_detallado = traceback.format_exc()
            QMessageBox.critical(self, "Error", 
                f"Error creating the schematic.\n\n"
                f"Type: {type(e).__name__}\n"
                f"Message: {str(e)}\n\n"+
                error_detallado)
            return
        
        QMessageBox.information(self, "Success", f"Workspace '{workspace_name}' created successfully in:\n{full_workspace_path}")


def formato_ingenieria(valor, precision=8):
    if valor == 0:
        return "0"
    
    # 1. Hallar el exponente (potencia de 10)
    exp = int(math.floor(math.log10(abs(valor))))
    # 2. Ajustar al múltiplo de 3 inferior
    eng_exp = (exp // 3) * 3
    # 3. Calcular el coeficiente
    coef = valor / (10**eng_exp)

    if eng_exp == 0:
        return f"{coef:.{precision}f}"
    
    return f"{coef:.{precision}f}e{eng_exp}"

def log_tiempo(mensaje):
    with open("tiempos_ejecucion.log", "a") as f:
        from datetime import datetime
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {mensaje}\n")

def log_mask(mask):
    with open("mask.log", "a") as f:
        f.write(f"MASK: {mask.name}\n")

        for i, limit in enumerate(mask.limits):
            f.write(
                f"  LIMIT {i}: "
                f"fstart={limit.fstart}, "
                f"fstop={limit.fstop}, "
                f"value_dB={limit.value_dB}, "
                f"upper_lower={limit.upper_lower}, "
                f"loss_type={limit.loss_type}\n"
            )

        f.write("\n")

# Run the test if this file is executed directly
if __name__ == "__main__":

    app = QApplication.instance() # or QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()
