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
                               QLabel, QLineEdit, QMessageBox, QGroupBox, QGridLayout, QScrollArea)

importlib.reload(ads)
importlib.reload(fs)
importlib.reload(mat_bvd_com)

# ============= VARIABLES GLOBALES ==============

# ============= CLASE PRINCIPAL DE LA APLICACIÓN ==============

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("TFG-SMOSfilter")
        self.setGeometry(100, 100, 900, 700)

        # Variables de clase (accesibles entre métodos)
        self.workspace_path = None
        self.network_file_path = None
        self.filter_parameters = None

        self.list_BVD = []
        self.list_COM = []

        # Crear scroll area para contenido
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        main_widget = QWidget()
        main_layout = QVBoxLayout()

        # ============== SECCIÓN 1: LECTURA DE ARCHIVO ==============
        btn_layout = QHBoxLayout()
        
        self.btn_read_network = QPushButton("📁 Read Network File")
        self.btn_read_network.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.btn_read_network.clicked.connect(self.btn_readNetworkFile_clicked)
        btn_layout.addWidget(self.btn_read_network)
        
        # Label para mostrar el archivo de network seleccionado
        self.label_network_file = QLabel("No file selected")
        self.label_network_file.setStyleSheet("color: gray; font-size: 10px; margin-left: 10px;")
        btn_layout.addWidget(self.label_network_file, 1)
        
        main_layout.addLayout(btn_layout)

        # ============== SECCIÓN 2: MATCHING NETWORK ==============
        matching_group = QGroupBox("Matching Network Parameters")
        matching_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #2196F3;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                color: #2196F3;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
        """)
        matching_layout = QGridLayout()
        
        self.matching_inputs = {}
        matching_params = ["input_l", "lfini1", "lfini2", "cfini1", "cfini2"]
        
        for idx, param in enumerate(matching_params):
            label = QLabel(f"{param}:")
            label.setStyleSheet("font-weight: bold;")
            input_field = QLineEdit()
            input_field.setPlaceholderText(f"Enter {param} value")
            row = idx // 2
            col = (idx % 2) * 2
            matching_layout.addWidget(label, row, col)
            matching_layout.addWidget(input_field, row, col + 1)
            self.matching_inputs[param] = input_field
        
        matching_group.setLayout(matching_layout)
        main_layout.addWidget(matching_group)

        # ============== SECCIÓN 3: LOSSY BVD ==============
        lossy_group = QGroupBox("Lossy BVD Parameters")
        lossy_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #FF9800;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                color: #FF9800;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
        """)
        lossy_layout = QGridLayout()
        
        self.lossy_inputs = {}
        lossy_params = ["c0", "la", "ca", "rs", "rp", "qa", "ql", "qc",
                       "cadd_shu", "ladd_shu", "cadd_ser", "ladd_ser", "ladd_ground"]
        
        for idx, param in enumerate(lossy_params):
            label = QLabel(f"{param}:")
            label.setStyleSheet("font-weight: bold;")
            input_field = QLineEdit()
            input_field.setPlaceholderText(f"Enter {param} value")
            row = idx // 2
            col = (idx % 2) * 2
            lossy_layout.addWidget(label, row, col)
            lossy_layout.addWidget(input_field, row, col + 1)
            self.lossy_inputs[param] = input_field
        
        lossy_group.setLayout(lossy_layout)
        main_layout.addWidget(lossy_group)

        # ============== SECCIÓN 4: CONTROLES DE WORKSPACE ==============
        workspace_group = QGroupBox("Workspace Configuration")
        workspace_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #9C27B0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                color: #9C27B0;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
        """)
        workspace_layout = QVBoxLayout()
        
        # Botón 2: Leer directorio
        self.btn_read_dir = QPushButton("📂 Read Directory")
        self.btn_read_dir.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 5px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        self.btn_read_dir.clicked.connect(self.btn_readDirectoy_clicked)
        workspace_layout.addWidget(self.btn_read_dir)
        
        # Label para mostrar el directorio seleccionado
        self.label_workspace_path = QLabel("No directory selected")
        self.label_workspace_path.setStyleSheet("color: gray; font-size: 10px; margin-left: 10px;")
        workspace_layout.addWidget(self.label_workspace_path)

        # Input para el nombre del workspace
        workspace_name_label = QLabel("Workspace Name:")
        workspace_name_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        workspace_layout.addWidget(workspace_name_label)
        self.input_workspace_name = QLineEdit()
        self.input_workspace_name.setPlaceholderText("Enter workspace name")
        workspace_layout.addWidget(self.input_workspace_name)

        # Botón 3: Crear workspace
        self.btn_create_workspace = QPushButton("🚀 Create Full Workspace")
        self.btn_create_workspace.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
        """)
        self.btn_create_workspace.clicked.connect(self.btn_createFullWorkspace_clicked)
        workspace_layout.addWidget(self.btn_create_workspace)
        
        workspace_group.setLayout(workspace_layout)
        main_layout.addWidget(workspace_group)
        
        main_layout.addStretch()
        
        main_widget.setLayout(main_layout)
        scroll_area.setWidget(main_widget)
        self.setCentralWidget(scroll_area)

    def btn_readNetworkFile_clicked(self):
        try:
            file_path = fs.select_file_to_read("Network files (*.ntw)|*.ntw|Text Files (*.txt)|*.txt|All Files (*.*)|*.*")
            if file_path:
                self.network_file_path = file_path
                self.label_network_file.setText(f"Selected: {file_path}")
                self.label_network_file.setStyleSheet("color: green; font-size: 10px; margin-left: 10px; margin-bottom: 10px;")
                self.filter_parameters = fs.read_and_parse_file(file_path)
                
                # Rellenar los campos de Matching Network y Lossy BVD con los parámetros leídos
                self.populate_parameters_from_file()
        except Exception as e:
            error_detallado = traceback.format_exc()
            QMessageBox.critical(self, "Error", 
                f"Error al leer el archivo Network.\n\n"
                f"Tipo: {type(e).__name__}\n"
                f"Mensaje: {str(e)}\n\n"+
                error_detallado)
            return

    def populate_parameters_from_file(self):
        """Rellena los campos de entrada con los parámetros del archivo leído."""
        if not self.filter_parameters:
            return
        
        # Mapear parámetros leídos a los campos de Matching Network
        for param_name, input_field in self.matching_inputs.items():
            if param_name in self.filter_parameters:
                input_field.setText(str(self.filter_parameters[param_name]))
        
        # Mapear parámetros leídos a los campos de Lossy BVD
        for param_name, input_field in self.lossy_inputs.items():
            if param_name in self.filter_parameters:
                input_field.setText(str(self.filter_parameters[param_name]))

    def btn_readDirectoy_clicked(self):
        try:
            selected_path = fs.select_workspace_path()
            if selected_path:
                self.workspace_path = selected_path
                self.label_workspace_path.setText(f"Selected: {self.workspace_path}")
                self.label_workspace_path.setStyleSheet("color: green; font-size: 10px; margin-left: 10px; margin-bottom: 10px;")
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
            ads.create_Schematic_ladderFilter_BVDlossy(lib, library_name, self.filter_parameters)
            ads.create_SchematicAndSymbol_lossyCOM(lib, library_name)
        except Exception as e:
            error_detallado = traceback.format_exc()
            QMessageBox.critical(self, "Error", 
                f"Error al crear el esquema.\n\n"
                f"Tipo: {type(e).__name__}\n"
                f"Mensaje: {str(e)}\n\n"+
                error_detallado)
            return
        
        # Crear lista de BVD y convertir a lista COM
        try:
            self.list_BVD = mat_bvd_com.create_list_BVD(self.filter_parameters)
            self.list_COM = mat_bvd_com.compute_list_COM(self.list_BVD)
            QMessageBox.information(self, "COM", 
                "COM parameters computed:\n\n" +
                "\n".join([f"COM {i+1}: d={com.d:.12e}, Ap={com.Ap:.12e}, N={com.N}, NR={com.NR}, alpha={com.alpha:.12e},"
                           f"alpha_n={com.alpha_n:.12e}, Ct={com.Ct:.12e}" for i, com in enumerate(self.list_COM)]))
        except Exception as e:
            error_detallado = traceback.format_exc()
            QMessageBox.critical(self, "Error", 
                f"Error crear lista BVD o al calcular los parámetros COM.\n\n"
                f"Tipo: {type(e).__name__}\n"
                f"Mensaje: {str(e)}\n\n"+
                error_detallado)
            return
        
        QMessageBox.information(self, "Éxito", f"Workspace '{workspace_name}' creado exitosamente en:\n{full_workspace_path}")


# Run the test if this file is executed directly
if __name__ == "__main__":

    app = QApplication.instance() # or QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()
