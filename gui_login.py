import json
from PyQt5.QtWidgets import (
    QWidget, QLineEdit, QPushButton, QLabel, QComboBox,
    QVBoxLayout, QFormLayout, QTabWidget, QMessageBox
)
from PyQt5.QtCore import Qt

import virtuallab_client as backend
from config import SERVER_URL
from gui_professor import ProfessorWindow
from gui_student import StudentWindow


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VirtualLab - Acceso al Sistema")
        self.setMinimumSize(450, 420)
        self.resize(450, 420)
        self.active_window = None
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 22, 28, 22)
        main_layout.setSpacing(14)

        title = QLabel("VirtualLab Electrónica")
        title.setObjectName("TitleLabel")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Plataforma de Simulación de Circuitos y Laboratorios")
        subtitle.setObjectName("SubtitleLabel")
        subtitle.setAlignment(Qt.AlignCenter)

        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        self.tabs = QTabWidget()
        self.tab_login = QWidget()
        self.tab_register = QWidget()

        self._build_login_tab()
        self._build_register_tab()

        self.tabs.addTab(self.tab_login, "Iniciar Sesión")
        self.tabs.addTab(self.tab_register, "Registrarse")
        main_layout.addWidget(self.tabs)

    def _build_login_tab(self):
        layout = QVBoxLayout(self.tab_login)
        layout.setContentsMargins(10, 14, 10, 10)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setVerticalSpacing(12)
        form.setHorizontalSpacing(14)

        self.login_id = QLineEdit()
        self.login_id.setPlaceholderText("Ej: 1001")
        self.login_pass = QLineEdit()
        self.login_pass.setPlaceholderText("Ingresa tu contraseña")
        self.login_pass.setEchoMode(QLineEdit.Password)
        self.login_pass.returnPressed.connect(self.handle_login)

        form.addRow("ID de Usuario:", self.login_id)
        form.addRow("Contraseña:", self.login_pass)

        self.btn_login = QPushButton("Ingresar al Laboratorio")
        self.btn_login.clicked.connect(self.handle_login)

        layout.addLayout(form)
        layout.addStretch()
        layout.addWidget(self.btn_login)

    def _build_register_tab(self):
        layout = QVBoxLayout(self.tab_register)
        layout.setContentsMargins(10, 14, 10, 10)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setVerticalSpacing(12)
        form.setHorizontalSpacing(14)

        self.reg_name = QLineEdit()
        self.reg_name.setPlaceholderText("Ej: Carlos Pérez")

        self.reg_id = QLineEdit()
        self.reg_id.setPlaceholderText("Ej: 202601")

        self.reg_role = QComboBox()
        self.reg_role.addItem("Estudiante", "student")
        self.reg_role.addItem("Profesor", "professor")

        self.reg_pass = QLineEdit()
        self.reg_pass.setPlaceholderText("Crea una contraseña")
        self.reg_pass.setEchoMode(QLineEdit.Password)

        form.addRow("Nombre:", self.reg_name)
        form.addRow("ID:", self.reg_id)
        form.addRow("Rol:", self.reg_role)
        form.addRow("Contraseña:", self.reg_pass)

        self.btn_register = QPushButton("Crear Cuenta")
        self.btn_register.setObjectName("SuccessButton")
        self.btn_register.clicked.connect(self.handle_register)

        layout.addLayout(form)
        layout.addStretch()
        layout.addWidget(self.btn_register)

    def handle_login(self):
        user_id = self.login_id.text().strip()
        password = self.login_pass.text().strip()

        if not user_id or not password:
            QMessageBox.warning(self, "Campos incompletos", "Por favor ingresa tu ID y contraseña.")
            return

        try:
            response = backend.openSession(SERVER_URL, user_id, password)
        except Exception as exc:
            QMessageBox.critical(
                self, "Error de conexión",
                f"No se pudo conectar con el servidor ({SERVER_URL}).\n"
                f"Asegúrate de ejecutar virtuallab_server.py primero.\n\nDetalle: {exc}"
            )
            return

        if "succesfully opened" in response:
            role = self._detect_user_role(user_id)
            user_info = {"id": user_id, "name": user_id, "role": role}

            if role == "professor":
                self.active_window = ProfessorWindow(user_info, on_logout=self.show_again)
            else:
                self.active_window = StudentWindow(user_info, on_logout=self.show_again)

            self.active_window.show()
            self.hide()
        else:
            QMessageBox.warning(self, "Acceso denegado", "ID o contraseña incorrectos.")

    def _detect_user_role(self, user_id):
        try:
            labs_resp = backend.listProfessorsLabs(SERVER_URL, user_id)
            parsed = json.loads(labs_resp)
            if isinstance(parsed, list):
                return "professor"
        except Exception:
            pass
        return "student"

    def handle_register(self):
        name = self.reg_name.text().strip()
        user_id = self.reg_id.text().strip()
        role = self.reg_role.currentData()
        password = self.reg_pass.text().strip()

        if not name or not user_id or not password:
            QMessageBox.warning(self, "Campos incompletos", "Completa todos los campos para registrarte.")
            return

        try:
            response = backend.registerUser(SERVER_URL, name, user_id, role, password)
        except Exception as exc:
            QMessageBox.critical(self, "Error de conexión", f"No se pudo conectar al servidor:\n{exc}")
            return

        if "already registered" in response:
            QMessageBox.warning(self, "ID duplicado", f"El ID '{user_id}' ya se encuentra registrado.")
        elif "registered" in response:
            role_label = "Profesor" if role == "professor" else "Estudiante"
            QMessageBox.information(
                self, "Registro exitoso",
                f"Usuario '{name}' registrado como {role_label}.\nYa puedes iniciar sesión."
            )
            self.reg_name.clear()
            self.reg_id.clear()
            self.reg_pass.clear()
            self.login_id.setText(user_id)
            self.tabs.setCurrentIndex(0)
        else:
            QMessageBox.warning(self, "Error", f"Respuesta inesperada del servidor: {response}")

    def show_again(self):
        self.login_pass.clear()
        self.show()