import os
import json
import zipfile
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QListWidget, QPushButton, QLabel,
    QVBoxLayout, QHBoxLayout, QSplitter, QMessageBox,
    QFileDialog, QTextEdit, QTabWidget, QAbstractItemView
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

import virtuallab_client as backend
from config import SERVER_URL
from simulator_engine import SimulationPlotWidget, run_circuit_simulation


class ProfessorWindow(QMainWindow):
    def __init__(self, user, on_logout=None):
        super().__init__()
        self.user = user
        self.on_logout = on_logout
        self.current_cir_text = None
        self.current_lab_name = None

        self.setWindowTitle(f"VirtualLab [Panel Docente] - Prof. ID: {user['id']}")
        self.resize(1080, 680)
        self._build_ui()
        self.refresh_all()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(16, 14, 16, 14)
        root_layout.setSpacing(10)

        # Barra superior
        top_bar = QHBoxLayout()
        header = QLabel(f"Panel de Gestión Docente  |  Usuario ID: {self.user['id']}")
        header.setObjectName("TitleLabel")

        btn_refresh = QPushButton("Actualizar Listas")
        btn_refresh.setObjectName("SecondaryButton")
        btn_refresh.clicked.connect(self.refresh_all)

        btn_logout = QPushButton("Cerrar Sesión")
        btn_logout.setObjectName("DangerButton")
        btn_logout.clicked.connect(self.logout)

        top_bar.addWidget(header)
        top_bar.addStretch()
        top_bar.addWidget(btn_refresh)
        top_bar.addWidget(btn_logout)
        root_layout.addLayout(top_bar)

        # Divisor principal: Izquierda (Gestión) | Derecha (Vista previa y Simulación)
        splitter = QSplitter(Qt.Horizontal)

        # --- PANEL IZQUIERDO ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 8, 0)

        lbl_labs = QLabel("1. Laboratorios Disponibles en Servidor")
        lbl_labs.setObjectName("SectionHeader")
        self.lab_list = QListWidget()
        self.lab_list.itemClicked.connect(self.on_select_lab)

        self.btn_upload = QPushButton("Subir Nuevo Laboratorio (.zip)")
        self.btn_upload.setObjectName("SuccessButton")
        self.btn_upload.clicked.connect(self.upload_lab)

        lbl_students = QLabel("2. Estudiantes Registrados (Selecciona para asignar)")
        lbl_students.setObjectName("SectionHeader")
        self.student_list = QListWidget()
        self.student_list.setSelectionMode(QAbstractItemView.MultiSelection)

        self.btn_assign = QPushButton("Asignar Laboratorio Seleccionado")
        self.btn_assign.clicked.connect(self.assign_lab_to_students)

        left_layout.addWidget(lbl_labs)
        left_layout.addWidget(self.lab_list, stretch=2)
        left_layout.addWidget(self.btn_upload)
        left_layout.addSpacing(8)
        left_layout.addWidget(lbl_students)
        left_layout.addWidget(self.student_list, stretch=2)
        left_layout.addWidget(self.btn_assign)

        # --- PANEL DERECHO ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(8, 0, 0, 0)

        sim_header_layout = QHBoxLayout()
        self.lbl_selected_lab = QLabel("Vista Previa del Circuito: Ninguno seleccionado")
        self.lbl_selected_lab.setObjectName("SectionHeader")

        self.btn_test_sim = QPushButton("Probar Simulación Ahora")
        self.btn_test_sim.clicked.connect(self.test_simulation)

        sim_header_layout.addWidget(self.lbl_selected_lab)
        sim_header_layout.addStretch()
        sim_header_layout.addWidget(self.btn_test_sim)
        right_layout.addLayout(sim_header_layout)

        # Imagen del circuito
        self.image_label = QLabel("Selecciona un laboratorio de la lista para ver su esquema")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedHeight(220)
        self.image_label.setStyleSheet(
            "border: 1px solid #cbd5e1; border-radius: 6px; background-color: #ffffff; color: #64748b;"
        )
        right_layout.addWidget(self.image_label)

        # Pestañas: Resultados y Gráfica / Archivo .CIR
        self.preview_tabs = QTabWidget()

        tab_results = QWidget()
        res_layout = QVBoxLayout(tab_results)
        self.plot_widget = SimulationPlotWidget()
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setFixedHeight(140)
        self.console_output.setPlaceholderText("Los resultados de la simulación de prueba aparecerán aquí...")
        res_layout.addWidget(self.plot_widget, stretch=2)
        res_layout.addWidget(self.console_output, stretch=1)

        tab_cir = QWidget()
        cir_layout = QVBoxLayout(tab_cir)
        self.cir_viewer = QTextEdit()
        self.cir_viewer.setReadOnly(True)
        self.cir_viewer.setPlaceholderText("Contenido del archivo SPICE (.cir)...")
        cir_layout.addWidget(self.cir_viewer)

        self.preview_tabs.addTab(tab_results, "Gráfica y Resultados")
        self.preview_tabs.addTab(tab_cir, "Código del Circuito (.cir)")
        right_layout.addWidget(self.preview_tabs)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([360, 720])
        root_layout.addWidget(splitter)

    def refresh_all(self):
        self.load_labs()
        self.load_students()

    def load_labs(self):
        self.lab_list.clear()
        response = backend.listProfessorsLabs(SERVER_URL, self.user["id"])
        try:
            labs = json.loads(response)
            if isinstance(labs, list):
                for lab in labs:
                    self.lab_list.addItem(str(lab).replace(".zip", ""))
        except Exception:
            QMessageBox.warning(self, "Error", f"No se pudieron cargar los laboratorios:\n{response}")

    def load_students(self):
        self.student_list.clear()
        response = backend.listStudents(SERVER_URL, self.user["id"])
        try:
            students = json.loads(response)
            if isinstance(students, list):
                for st in students:
                    self.student_list.addItem(str(st))
        except Exception:
            QMessageBox.warning(self, "Error", f"No se pudieron listar los estudiantes:\n{response}")

    def on_select_lab(self, item):
        lab_name = item.text()
        self.current_lab_name = lab_name
        self.current_cir_text = None
        self.lbl_selected_lab.setText(f"Vista Previa del Circuito: {lab_name}")
        self.console_output.clear()
        self.plot_widget.clear_plot("Presiona 'Probar Simulación Ahora' para analizar")

        # En virtuallab_functions.py, downloadLab está restringido a rol 'student'.
        # Por eso el profesor lee el ZIP desde server/labs/ si está en la misma máquina.
        zip_path = os.path.join("server", "labs", f"{lab_name}.zip")
        if not os.path.isfile(zip_path):
            backend.downloadLab(SERVER_URL, self.user["id"], f"{lab_name}.zip")
            zip_path = os.path.join("client", "labs", f"{lab_name}.zip")

        if not os.path.isfile(zip_path):
            self.image_label.setText("No se encontró el archivo ZIP para previsualizar.")
            return

        has_img = False
        try:
            with zipfile.ZipFile(zip_path, "r") as archive:
                for entry in archive.namelist():
                    base = os.path.basename(entry)
                    if base.lower().endswith(".cir"):
                        self.current_cir_text = archive.read(entry).decode("utf-8", errors="replace")
                        self.cir_viewer.setPlainText(self.current_cir_text)
                    elif base.lower().endswith((".png", ".jpg", ".jpeg")):
                        pixmap = QPixmap()
                        pixmap.loadFromData(archive.read(entry))
                        if not pixmap.isNull():
                            has_img = True
                            self.image_label.setPixmap(
                                pixmap.scaled(520, 210, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            )

            if not has_img:
                self._load_fallback_image(lab_name)
            if self.current_cir_text is None:
                self.cir_viewer.setPlainText("El archivo .zip no contiene ningún archivo .cir.")
        except zipfile.BadZipFile:
            QMessageBox.warning(self, "Archivo corrupto", f"El archivo {zip_path} no es un ZIP válido.")

    def _load_fallback_image(self, lab_name):
        if "voltage" in lab_name.lower() or "divisor" in lab_name.lower():
            if os.path.isfile("divisordevoltaje.png"):
                pixmap = QPixmap("divisordevoltaje.png")
                self.image_label.setPixmap(
                    pixmap.scaled(520, 210, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
                return
        self.image_label.setPixmap(QPixmap())
        self.image_label.setText("Este laboratorio no incluye imagen esquemática")

    def test_simulation(self):
        if not self.current_cir_text:
            QMessageBox.warning(self, "Sin circuito", "Selecciona primero un laboratorio con archivo .cir válido.")
            return
        try:
            result = run_circuit_simulation(self.current_cir_text, self.current_lab_name)
            self.console_output.setPlainText(result["report"])
            if result["mode"] == "transient":
                self.plot_widget.plot_transient(result["time"], result["node_series"], self.current_lab_name)
            else:
                self.plot_widget.plot_dc_bars(
                    result["node_voltages"], result["branch_currents"], self.current_lab_name
                )
        except RuntimeError as exc:
            QMessageBox.critical(self, "Error de Simulación", str(exc))

    def upload_lab(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar paquete de laboratorio (.zip)",
            "",
            "Paquetes de Laboratorio (*.zip)"
        )
        if not file_path:
            return

        response = backend.uploadLab(SERVER_URL, self.user["id"], file_path)
        if "succesfully received" in response:
            QMessageBox.information(
                self, "Laboratorio Subido",
                f"El laboratorio '{os.path.basename(file_path)}' se subió correctamente al servidor."
            )
            self.load_labs()
        else:
            QMessageBox.warning(self, "Error al subir", f"El servidor respondió:\n{response}")

    def assign_lab_to_students(self):
        lab_item = self.lab_list.currentItem()
        if lab_item is None:
            QMessageBox.warning(self, "Falta laboratorio", "Selecciona un laboratorio de la lista superior.")
            return

        selected_students = self.student_list.selectedItems()
        if not selected_students:
            QMessageBox.warning(self, "Faltan estudiantes", "Selecciona al menos un estudiante de la lista.")
            return

        lab_name = lab_item.text()
        assigned_ok = []
        errors = []

        for st_item in selected_students:
            st_id = st_item.text()
            resp = backend.assignLab(SERVER_URL, self.user["id"], lab_name, st_id)
            if "success" in resp:
                assigned_ok.append(st_id)
            else:
                errors.append(f"{st_id} ({resp})")

        msg = ""
        if assigned_ok:
            msg += f"Laboratorio '{lab_name}' asignado a: {', '.join(assigned_ok)}."
        if errors:
            msg += f"\nErrores en: {', '.join(errors)}"
        QMessageBox.information(self, "Resultado de Asignación", msg)

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