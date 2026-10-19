import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap
from src.utils import get_asset_path
from src.client import api

class LoginWidget(QWidget):
    login_successful = Signal(dict)
    cancel_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        logo_path = get_asset_path("randaframes logo.jpg")
        if not os.path.exists(logo_path):
            logo_path = get_asset_path("icon.ico")
        if os.path.exists(logo_path):
            logo_label = QLabel()
            pixmap = QPixmap(logo_path).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
            logo_label.setStyleSheet("margin-bottom: 12px;")
            layout.addWidget(logo_label, alignment=Qt.AlignCenter)

        title = QLabel("Admin Console Login")
        title.setFont(QFont("Arial", 22, QFont.Bold))
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
        self.server_input = QLineEdit(api.url)
        self.server_input.setPlaceholderText("https://attendance.your-company.com")
        self.server_input.setFixedWidth(360)
        layout.addWidget(QLabel("Central server address:"), alignment=Qt.AlignCenter)
        layout.addWidget(self.server_input, alignment=Qt.AlignCenter)
        layout.addWidget(self.username_input, alignment=Qt.AlignCenter)
        layout.addWidget(self.password_input, alignment=Qt.AlignCenter)
        layout.addSpacing(20)
        layout.addWidget(self.login_btn, alignment=Qt.AlignCenter)
        self.cancel_btn.hide()
        self.password_input.returnPressed.connect(self.on_login)

    def on_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Error", "Username and password required.")
            return

        try:
            api.configure(self.server_input.text())
            user = api.login(username, password)
            if user.get("must_change_password"):
                from PySide6.QtWidgets import QInputDialog
                new_password, ok = QInputDialog.getText(self, "Change temporary password",
                    "New password: at least 10 characters, letters, numbers and a symbol (!@#$%&*?)", QLineEdit.Password)
                if not ok:
                    api.logout()
                    return
                api.call("/password", {"password": new_password})
                user["must_change_password"] = False
            self.username_input.clear()
            self.password_input.clear()
            self.login_successful.emit(user)
        except ValueError as e:
            QMessageBox.critical(self, "Login Failed", str(e))
