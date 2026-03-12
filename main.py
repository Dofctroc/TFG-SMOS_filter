import os
import sys
import importlib
import traceback

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
                               QComboBox, QFormLayout)
from PySide6.QtCore import Qt
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
        
        self.layout_bvd = QVBoxLayout(self.panel_izquierdo)
        self.setup_bvd_panel()

        # --- 3. PANEL DERECHO (COM + GRÁFICO) ---
        self.panel_derecho_contenedor = QWidget()
        self.layout_derecha_total = QVBoxLayout(self.panel_derecho_contenedor)
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

        # --- 4. ENSAMBLAJE CUERPO ---
        self.layout_cuerpo.addWidget(self.panel_izquierdo, stretch=1)
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
        self.btn_convertir.clicked.connect(self.btn_convertBVD2COM_clicked)
        self.btn_convertir.setStyleSheet("background-color: #e0efff; color: black; font-weight: bold;")
        
        self.barra_superior.addWidget(self.btn_archivo)
        self.barra_superior.addWidget(self.btn_directorio)
        self.barra_superior.addStretch() # Empuja el botón convertir a la derecha
        self.barra_superior.addWidget(self.btn_convertir)

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
        # 1. El Desplegable (Selector)
        self.combo_bvd = QComboBox()
        self.combo_bvd.addItem("Archivo .ntw no leído")
        
        # Conectamos el cambio de selección a una función
        self.combo_bvd.currentIndexChanged.connect(self.actualizar_formulario_bvd)

        # 2. El Formulario de parámetros
        self.form_layout_BVD = QFormLayout()
        
        # Creamos los campos (QLineEdit)
        self.input_c0 = QLineEdit()
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
        for inp in [self.input_c0, self.input_ca, self.input_la, self.input_fs, self.input_fp, self.input_ladd_ser,
                    self.input_ladd_shu, self.input_cadd_ser, self.input_cadd_shu, self.input_ladd_ground]:
            inp.setReadOnly(True)
            inp.setPlaceholderText("---")
            inp.setStyleSheet("background-color: #f0f0f0; color: #555;")

        # Añadimos al layout del formulario
        self.form_layout_BVD.addRow("C0 (F):", self.input_c0)
        self.form_layout_BVD.addRow("Ca (F):", self.input_ca)
        self.form_layout_BVD.addRow("La (H):", self.input_la)
        self.form_layout_BVD.addRow("fs (Hz):", self.input_fs)
        self.form_layout_BVD.addRow("fp (Hz):", self.input_fp)
        self.form_layout_BVD.addRow("Ladd_ser (H):", self.input_ladd_ser)
        self.form_layout_BVD.addRow("Ladd_shu (H):", self.input_ladd_shu)
        self.form_layout_BVD.addRow("Cadd_ser (F):", self.input_cadd_ser)
        self.form_layout_BVD.addRow("Cadd_shu (F):", self.input_cadd_shu)
        self.form_layout_BVD.addRow("Ladd_gnd (H):", self.input_ladd_ground)

        # Añadir parámetros generales (rs, rp, ql, qc, qa) al formulario de BVD
        self.form_layout_BVD_general = QFormLayout()

        self.input_rs = QLineEdit()
        self.input_rp = QLineEdit()
        self.input_ql = QLineEdit()
        self.input_qc = QLineEdit()
        self.input_qa = QLineEdit()

        # Configuramos como "Solo lectura" y ponemos placeholders
        for inp in [self.input_rs, self.input_rp, self.input_ql, self.input_qc, self.input_qa]:
            inp.setReadOnly(True)
            inp.setPlaceholderText("---")
            inp.setStyleSheet("background-color: #f0f0f0; color: #555;")

        self.form_layout_BVD_general.addRow("Rs (Ohms):", self.input_rs)
        self.form_layout_BVD_general.addRow("Rp (Ohms):", self.input_rp)
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
        bvd_general_label=QLabel("Parámetros Resonador:")
        bvd_general_label.setStyleSheet("font-weight: bold; color: darkgray;")
        self.layout_bvd.addWidget(bvd_general_label)
        self.layout_bvd.addLayout(self.form_layout_BVD_general)
        self.layout_bvd.addStretch()

    def actualizar_formulario_bvd(self, index):
        """Esta función se llama cada vez que eliges un BVD en el combo"""
        # Si no hay datos (solo el mensaje por defecto) o la lista está vacía
        if not self.list_BVD or self.combo_bvd.currentText() == "Archivo .ntw no leído":
            return

        # Obtenemos el objeto BVD seleccionado
        bvd_seleccionado = self.list_BVD[index]
        
        # Rellenamos los campos
        self.input_c0.setText(str(bvd_seleccionado.c0))
        self.input_ca.setText(str(bvd_seleccionado.ca))
        self.input_la.setText(str(bvd_seleccionado.la))
        self.input_fs.setText(str(bvd_seleccionado.fs))
        self.input_fp.setText(str(bvd_seleccionado.fp))
        self.input_ladd_ser.setText(str(bvd_seleccionado.ladd_ser))
        self.input_ladd_shu.setText(str(bvd_seleccionado.ladd_shu))
        self.input_cadd_ser.setText(str(bvd_seleccionado.cadd_ser))
        self.input_cadd_shu.setText(str(bvd_seleccionado.cadd_shu))
        self.input_ladd_ground.setText(str(bvd_seleccionado.ladd_ground))

    def setup_com_panel(self):
        # 1. El Desplegable (Selector)
        self.combo_com = QComboBox()
        self.combo_com.addItem("Conversión no realizada")
        
        # Conectamos el cambio de selección a una función
        self.combo_com.currentIndexChanged.connect(self.actualizar_formulario_com)

        # 2. El Formulario de parámetros
        self.form_layout_COM = QFormLayout()
        
        # Creamos los campos (QLineEdit)
        self.input_pitch = QLineEdit()
        self.input_aperture = QLineEdit()
        self.input_digitsIDT = QLineEdit()
        self.input_digitsREFL = QLineEdit()
        self.input_alpha = QLineEdit()
        
        # Configuramos como "Solo lectura" y ponemos placeholders
        for inp in [self.input_pitch, self.input_aperture, self.input_digitsIDT, 
                    self.input_digitsREFL, self.input_alpha]:
            inp.setReadOnly(True)
            inp.setPlaceholderText("---")
            inp.setStyleSheet("background-color: #f0f0f0; color: #555;")

        # Añadimos al layout del formulario
        self.form_layout_COM.addRow("p (m):", self.input_pitch)
        self.form_layout_COM.addRow("Ap (λ0):", self.input_aperture)
        self.form_layout_COM.addRow("digitsIDT (-):", self.input_digitsIDT)
        self.form_layout_COM.addRow("digitsREFL (-):", self.input_digitsREFL)
        self.form_layout_COM.addRow("α (-):", self.input_alpha)

        # 3. Montaje en el panel derecho
        # Limpiamos el layout_com por si acaso y añadimos
        com_label=QLabel("Parámetros modelo COM:")
        com_label.setStyleSheet("font-weight: bold; color: darkgray;")
        self.layout_com.addWidget(com_label)
        self.layout_com.addWidget(self.combo_com)
        self.layout_com.addSpacing(10) # Espacio visual
        self.layout_com.addLayout(self.form_layout_COM)
        self.layout_com.addStretch()

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
        self.input_digitsIDT.setText(str(com_seleccionado.N))
        self.input_digitsREFL.setText(str(com_seleccionado.NR))
        self.input_alpha.setText(str(com_seleccionado.alpha))

    def setup_graph_panel(self):
        # Usamos el layout que ya definiste en el __init__
        # Si no lo definiste allí, asegúrate de que esta línea sea la única que crea el QVBoxLayout
        if self.bloque_grafico.layout() is None:
            self.layout_grafico = QVBoxLayout(self.bloque_grafico)
        else:
            self.layout_grafico = self.bloque_grafico.layout()
            
        self.layout_grafico.setContentsMargins(10, 20, 10, 10)
        self.layout_grafico.setSpacing(5)

        # --- BARRA DE CONTROL DEL GRÁFICO (Horizontal) ---
        barra_filtros = QHBoxLayout()
        
        # 1. Selector de Elemento
        label_el = QLabel("Elemento:")
        label_el.setStyleSheet("font-weight: bold;")
        self.combo_elemento_graf = QComboBox()
        self.combo_elemento_graf.addItem("Sin datos")
        self.combo_elemento_graf.setFixedWidth(120)
        
        # 2. Botones de Radio (BVD vs COM)
        self.radio_bvd = QRadioButton("BVD")
        self.radio_com = QRadioButton("COM")
        self.radio_bvd.setChecked(True) # BVD por defecto
        
        # Agrupamos los radios para que sean mutuamente excluyentes
        self.grupo_tipo = QButtonGroup(self)
        self.grupo_tipo.addButton(self.radio_bvd)
        self.grupo_tipo.addButton(self.radio_com)
        self.radio_bvd.setEnabled(False)
        self.radio_com.setEnabled(False)

        # Montamos la barrita de control
        barra_filtros.addWidget(label_el)
        barra_filtros.addWidget(self.combo_elemento_graf)
        barra_filtros.addSpacing(20)
        barra_filtros.addWidget(self.radio_bvd)
        barra_filtros.addWidget(self.radio_com)
        barra_filtros.addStretch() # Empuja todo a la izquierda

        # 3. Canvas y Toolbar
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.toolbar = NavigationToolbar(self.canvas, self)
        # Hacer la toolbar más discreta
        self.toolbar.setStyleSheet("background-color: transparent; border: none;")

        # --- AÑADIR TODO AL LAYOUT PRINCIPAL DEL BLOQUE ---
        self.layout_grafico.addLayout(barra_filtros)
        self.layout_grafico.addWidget(self.canvas)
        self.layout_grafico.addWidget(self.toolbar)

        # --- CONEXIONES ---
        self.combo_elemento_graf.currentIndexChanged.connect(self.plot_admitancia)
        self.radio_bvd.toggled.connect(self.plot_admitancia)
        self.radio_com.toggled.connect(self.plot_admitancia)

    def plot_admitancia(self):
        idx = self.combo_elemento_graf.currentIndex()
    
        # Verificaciones de seguridad
        if idx < 0:
            return

        # Decidir qué fuente usar
        if self.radio_bvd.isChecked():
            # Suponiendo que tu clase BVD tiene .Y y .f calculados
            data = self.list_BVD[idx]
            color_plot = 'red'
            label_plot = f"BVD - Elemento {idx+1}"
        else:
            data = self.list_COM[idx]
            color_plot = 'blue'
            label_plot = f"COM - Elemento {idx+1}"

        # Verificamos que el objeto seleccionado tenga los datos
        if not hasattr(data, 'Y') or data.Y is None:
            return
        if not hasattr(data, 'f') or data.f is None:
            return

        # CONVERSIÓN A dB
        # Usamos 20*log10 porque la admitancia es una magnitud de "voltaje/corriente"
        # Añadimos un pequeño valor (1e-20) para evitar log(0) si hubiera ceros
        magnitud_Y_dB = 20 * np.log10(np.abs(data.Y) + 1e-20)

        self.canvas.axes.cla()
        
        # Ploteamos f (log) vs Y (dB lineal)
        self.canvas.axes.plot(data.f, magnitud_Y_dB, label=label_plot, color=color_plot)
        
        self.canvas.axes.set_title("Respuesta en Frecuencia (Magnitud)")
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

                msg = "\n".join([f"{i}: {v:.4e}" for i, v in enumerate(self.list_BVD[0].Y[:20])])
                QMessageBox.information(None, "f Values", msg)  
                
                # Rellenar los campos de Matching Network y Lossy BVD con los parámetros leídos
                self.combo_bvd.clear() # Borra el "Archivo no leído"
                for bvd in self.list_BVD:
                    self.combo_bvd.addItem(bvd.name)
                
                self.input_rs.setText(str(self.network_parameters["rs"]))
                self.input_rp.setText(str(self.network_parameters["rp"]))
                self.input_ql.setText(str(self.network_parameters["ql"]))
                self.input_qc.setText(str(self.network_parameters["qc"]))
                self.input_qa.setText(str(self.network_parameters["qa"]))

                # Rellenar el combo del gráfico con los elementos disponibles
                self.combo_elemento_graf.clear() # Borra el "Archivo no leído"
                idx = 1
                for bvd in self.list_BVD:
                    self.combo_elemento_graf.addItem("Elemento " + str(idx))
                    idx += 1

                # Habilitamos el radio button de COM y ploteamos la primera curva por defecto
                self.radio_bvd.setEnabled(True)
                self.plot_admitancia()

        except Exception as e:
            error_detallado = traceback.format_exc()
            QMessageBox.critical(self, "Error", 
                f"Error al leer el archivo Network.\n\n"
                f"Tipo: {type(e).__name__}\n"
                f"Mensaje: {str(e)}\n\n"+
                error_detallado)
            return

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
            ads.create_SchematicAndSymbol_lossyBVD(lib, library_name)
            ads.create_Schematic_ladderFilter_BVDlossy(lib, library_name, self.network_parameters)
            ads.create_SchematicAndSymbol_lossyCOM(lib, library_name)
        except Exception as e:
            error_detallado = traceback.format_exc()
            QMessageBox.critical(self, "Error", 
                f"Error al crear el esquema.\n\n"
                f"Tipo: {type(e).__name__}\n"
                f"Mensaje: {str(e)}\n\n"+
                error_detallado)
            return
        
        QMessageBox.information(self, "Éxito", f"Workspace '{workspace_name}' creado exitosamente en:\n{full_workspace_path}")

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

                # Rellenar los campos de Matching Network y Lossy BVD con los parámetros leídos
                self.combo_com.clear() # Borra el "Archivo no leído"
                for com in self.list_COM:
                    self.combo_com.addItem(com.name)
                    
                # Habilitamos el radio button de COM
                self.radio_com.setEnabled(True)

            except Exception as e:
                error_detallado = traceback.format_exc()
                QMessageBox.critical(self, "Error", 
                    f"Error crear lista BVD o al calcular los parámetros COM.\n\n"
                    f"Tipo: {type(e).__name__}\n"
                    f"Mensaje: {str(e)}\n\n"+
                    error_detallado)
                return


# Run the test if this file is executed directly
if __name__ == "__main__":

    app = QApplication.instance() # or QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()
