from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from src.services.auth import AuthService

class LoginWidget(QWidget):
    login_successful = Signal(dict)
    cancel_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.auth_service = AuthService()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("Admin Console Login")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setFixedWidth(300)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedWidth(300)
        
        self.login_btn = QPushButton("Log In")
        self.login_btn.setFixedWidth(300)
        self.login_btn.clicked.connect(self.on_login)

        self.cancel_btn = QPushButton("Back to Kiosk")
        self.cancel_btn.setFixedWidth(300)
        self.cancel_btn.clicked.connect(self.cancel_requested.emit)

        layout.addWidget(title)
        layout.addSpacing(20)
        layout.addWidget(self.username_input, alignment=Qt.AlignCenter)
        layout.addWidget(self.password_input, alignment=Qt.AlignCenter)
        layout.addSpacing(20)
        layout.addWidget(self.login_btn, alignment=Qt.AlignCenter)
        layout.addWidget(self.cancel_btn, alignment=Qt.AlignCenter)

    def on_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Error", "Username and password required.")
            return

        try:
            user = self.auth_service.authenticate(username, password)
            self.username_input.clear()
            self.password_input.clear()
            self.login_successful.emit(user)
        except ValueError as e:
            QMessageBox.critical(self, "Login Failed", str(e))
