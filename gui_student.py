import os
import json
import zipfile
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QListWidget, QPushButton, QLabel,
    QVBoxLayout, QHBoxLayout, QSplitter, QMessageBox,
    QTextEdit, QTabWidget
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

import virtuallab_client as backend
from config import SERVER_URL
from simulator_engine import SimulationPlotWidget, run_circuit_simulation, detect_circuit_type


class StudentWindow(QMainWindow):
    def __init__(self, user, on_logout=None):
        super().__init__()
        self.user = user
        self.on_logout = on_logout
        self.current_cir_text = None
        self.current_lab_name = None

        self.setWindowTitle(f"VirtualLab [Área de Estudiante] - ID: {user['id']}")
        self.resize(1060, 660)
        self._build_ui()
        self.load_assigned_labs()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(16, 14, 16, 14)
        root_layout.setSpacing(10)

        # Barra superior
        top_bar = QHBoxLayout()
        header = QLabel(f"Mis Prácticas de Laboratorio  |  Estudiante ID: {self.user['id']}")
        header.setObjectName("TitleLabel")

        btn_refresh = QPushButton("Actualizar Mis Labs")
        btn_refresh.setObjectName("SecondaryButton")
        btn_refresh.clicked.connect(self.load_assigned_labs)

        btn_logout = QPushButton("Cerrar Sesión")
        btn_logout.setObjectName("DangerButton")
        btn_logout.clicked.connect(self.logout)

        top_bar.addWidget(header)
        top_bar.addStretch()
        top_bar.addWidget(btn_refresh)
        top_bar.addWidget(btn_logout)
        root_layout.addLayout(top_bar)

        # Splitter principal
        splitter = QSplitter(Qt.Horizontal)

        # --- PANEL IZQUIERDO: Lista de prácticas ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 8, 0)

        lbl_list = QLabel("Laboratorios Asignados")
        lbl_list.setObjectName("SectionHeader")

        self.lab_list = QListWidget()
        self.lab_list.itemClicked.connect(self.download_and_load_lab)

        self.lbl_circuit_type = QLabel("Tipo de práctica: -")
        self.lbl_circuit_type.setWordWrap(True)
        self.lbl_circuit_type.setStyleSheet(
            "background-color: #e0f2fe; color: #0369a1; padding: 8px; border-radius: 6px; font-weight: bold;"
        )

        self.btn_simulate = QPushButton("▶  Ejecutar Simulación")
        self.btn_simulate.setObjectName("SuccessButton")
        self.btn_simulate.setMinimumHeight(42)
        self.btn_simulate.clicked.connect(self.execute_simulation)

        left_layout.addWidget(lbl_list)
        left_layout.addWidget(self.lab_list, stretch=1)
        left_layout.addWidget(self.lbl_circuit_type)
        left_layout.addWidget(self.btn_simulate)

        # --- PANEL DERECHO: Esquema + Gráfica + Resultados ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(8, 0, 0, 0)

        lbl_diagram = QLabel("Esquema del Circuito")
        lbl_diagram.setObjectName("SectionHeader")
        right_layout.addWidget(lbl_diagram)

        self.image_label = QLabel("Selecciona un laboratorio asignado para cargar el esquema")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedHeight(230)
        self.image_label.setStyleSheet(
            "border: 1px solid #cbd5e1; border-radius: 6px; background-color: #ffffff; color: #64748b;"
        )
        right_layout.addWidget(self.image_label)

        self.tabs = QTabWidget()

        tab_sim = QWidget()
        sim_layout = QVBoxLayout(tab_sim)
        self.plot_widget = SimulationPlotWidget()
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFixedHeight(150)
        self.results_text.setPlaceholderText("Presiona 'Ejecutar Simulación' para ver voltajes, corrientes y ondas...")
        sim_layout.addWidget(self.plot_widget, stretch=2)
        sim_layout.addWidget(self.results_text, stretch=1)

        tab_netlist = QWidget()
        net_layout = QVBoxLayout(tab_netlist)
        self.netlist_viewer = QTextEdit()
        self.netlist_viewer.setReadOnly(True)
        net_layout.addWidget(self.netlist_viewer)

        self.tabs.addTab(tab_sim, "Gráficas y Mediciones")
        self.tabs.addTab(tab_netlist, "Netlist del Circuito (.cir)")
        right_layout.addWidget(self.tabs)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([310, 750])
        root_layout.addWidget(splitter)

    def load_assigned_labs(self):
        self.lab_list.clear()
        response = backend.listStudentLabs(SERVER_URL, self.user["id"])
        try:
            labs = json.loads(response)
            if isinstance(labs, list):
                if not labs:
                    self.results_text.setPlainText("Aún no tienes laboratorios asignados por tu profesor.")
                for lab in labs:
                    self.lab_list.addItem(str(lab).replace(".zip", ""))
            else:
                QMessageBox.warning(self, "Aviso", f"Respuesta del servidor: {response}")
        except Exception:
            QMessageBox.warning(self, "Error", f"No se pudieron obtener tus laboratorios:\n{response}")

    def download_and_load_lab(self, item):
        lab_name = item.text()
        self.current_lab_name = lab_name
        self.current_cir_text = None
        self.results_text.clear()
        self.plot_widget.clear_plot("Laboratorio cargado. Listo para simular.")

        response = backend.downloadLab(SERVER_URL, self.user["id"], f"{lab_name}.zip")
        zip_path = os.path.join("client", "labs", f"{lab_name}.zip")

        if not os.path.isfile(zip_path):
            QMessageBox.warning(self, "Error de descarga", f"No se pudo descargar el laboratorio:\n{response}")
            return

        has_image = False
        try:
            with zipfile.ZipFile(zip_path, "r") as archive:
                for entry in archive.namelist():
                    base = os.path.basename(entry)
                    if base.lower().endswith(".cir"):
                        self.current_cir_text = archive.read(entry).decode("utf-8", errors="replace")
                        self.netlist_viewer.setPlainText(self.current_cir_text)
                        c_type = detect_circuit_type(self.current_cir_text)
                        self.lbl_circuit_type.setText(f"Tipo de práctica:\n{c_type}")
                    elif base.lower().endswith((".png", ".jpg", ".jpeg")):
                        pixmap = QPixmap()
                        pixmap.loadFromData(archive.read(entry))
                        if not pixmap.isNull():
                            has_image = True
                            self.image_label.setPixmap(
                                pixmap.scaled(540, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            )

            if not has_image:
                self._apply_default_diagram(lab_name)

            if self.current_cir_text is None:
                QMessageBox.warning(self, "Laboratorio incompleto", "El paquete .zip no contiene un archivo .cir.")

        except zipfile.BadZipFile:
            QMessageBox.warning(self, "Error", "El archivo descargado está dañado o no es un ZIP válido.")

    def _apply_default_diagram(self, lab_name):
        """Si es el laboratorio de divisor de voltaje y el ZIP no trae imagen, usa divisordevoltaje.png."""
        if "voltage" in lab_name.lower() or "divisor" in lab_name.lower():
            if os.path.isfile("divisordevoltaje.png"):
                pixmap = QPixmap("divisordevoltaje.png")
                self.image_label.setPixmap(
                    pixmap.scaled(540, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
                return
        self.image_label.setPixmap(QPixmap())
        self.image_label.setText("Esquema no incluido en el paquete del laboratorio")

    def execute_simulation(self):
        if self.lab_list.currentItem() is None:
            QMessageBox.warning(self, "Selecciona un laboratorio", "Haz clic en un laboratorio de la lista.")
            return
        if not self.current_cir_text:
            QMessageBox.warning(self, "Sin datos", "El laboratorio seleccionado no tiene un circuito válido.")
            return

        try:
            result = run_circuit_simulation(self.current_cir_text, self.current_lab_name)
            self.results_text.setPlainText(result["report"])
            if result["mode"] == "transient":
                self.plot_widget.plot_transient(result["time"], result["node_series"], self.current_lab_name)
            else:
                self.plot_widget.plot_dc_bars(
                    result["node_voltages"], result["branch_currents"], self.current_lab_name
                )
        except RuntimeError as exc:
            QMessageBox.critical(self, "Error en Simulación", str(exc))

    def logout(self):
        try:
            backend.closeSession(SERVER_URL, self.user["id"])
        except Exception:
            pass
        if self.on_logout:
            self.on_logout()
        self.close()

    def closeEvent(self, event):
        try:
            backend.closeSession(SERVER_URL, self.user["id"])
        except Exception:
            pass
        event.accept()