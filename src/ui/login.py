import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QInputDialog)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont, QPixmap
from src.utils import get_asset_path
from src.client import api


class LoginWorker(QThread):
    finished_success = Signal(dict)
    finished_error = Signal(str)

    def __init__(self, server_url, username, password):
        super().__init__()
        self.server_url = server_url
        self.username = username
        self.password = password

    def run(self):
        try:
            if self.server_url:
                api.configure(self.server_url)
            user = api.login(self.username, self.password)
            self.finished_success.emit(user)
        except Exception as exc:
            self.finished_error.emit(str(exc))


class PasswordChangeWorker(QThread):
    finished_success = Signal()
    finished_error = Signal(str)

    def __init__(self, new_password):
        super().__init__()
        self.new_password = new_password

    def run(self):
        try:
            api.call("/password", {"password": self.new_password})
            self.finished_success.emit()
        except Exception as exc:
            self.finished_error.emit(str(exc))


class LoginWidget(QWidget):
    login_successful = Signal(dict)
    cancel_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.pw_worker = None
        self.current_user_pending = None
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
        layout.addWidget(title)
        layout.addSpacing(20)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setFixedWidth(300)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedWidth(300)

        self.login_btn = QPushButton("Log In")
        self.login_btn.setFixedWidth(300)
        self.login_btn.setFixedHeight(38)
        self.login_btn.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.login_btn.clicked.connect(self.on_login)

        self.cancel_btn = QPushButton("Back to Kiosk")
        self.cancel_btn.setFixedWidth(300)
        self.cancel_btn.setFixedHeight(34)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #3f4248;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 4px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #4f535a;
                color: #ffffff;
            }
        """)
        self.cancel_btn.clicked.connect(self.cancel_requested.emit)

        layout.addWidget(self.username_input, alignment=Qt.AlignCenter)
        layout.addWidget(self.password_input, alignment=Qt.AlignCenter)
        layout.addSpacing(15)
        layout.addWidget(self.login_btn, alignment=Qt.AlignCenter)
        layout.addSpacing(6)
        layout.addWidget(self.cancel_btn, alignment=Qt.AlignCenter)

        self.password_input.returnPressed.connect(self.on_login)
        self.username_input.returnPressed.connect(self.password_input.setFocus)

    def on_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Username and password required.")
            return

        self.login_btn.setEnabled(False)
        self.login_btn.setText("Logging in...")
        self.cancel_btn.setEnabled(False)

        self.worker = LoginWorker(api.url, username, password)
        self.worker.finished_success.connect(self.on_login_success)
        self.worker.finished_error.connect(self.on_login_error)
        self.worker.start()

    def on_login_success(self, user):
        self.current_user_pending = user
        if user.get("must_change_password"):
            new_password, ok = QInputDialog.getText(
                self,
                "Change Temporary Password",
                "Set your permanent password (at least 10 characters with letters, numbers, and symbols):",
                QLineEdit.Password
            )
            if not ok or not new_password:
                self.login_btn.setEnabled(True)
                self.login_btn.setText("Log In")
                self.cancel_btn.setEnabled(True)
                api.logout()
                return

            self.login_btn.setText("Updating password...")
            self.pw_worker = PasswordChangeWorker(new_password)
            self.pw_worker.finished_success.connect(self.on_password_change_success)
            self.pw_worker.finished_error.connect(self.on_password_change_error)
            self.pw_worker.start()
            return

        self._finalize_login(user)

    def on_password_change_success(self):
        QMessageBox.information(self, "Success", "Password updated successfully!")
        if self.current_user_pending:
            self.current_user_pending["must_change_password"] = False
            self._finalize_login(self.current_user_pending)

    def on_password_change_error(self, err):
        self.login_btn.setEnabled(True)
        self.login_btn.setText("Log In")
        self.cancel_btn.setEnabled(True)
        QMessageBox.critical(self, "Password Change Failed", err)
        api.logout()

    def _finalize_login(self, user):
        self.login_btn.setEnabled(True)
        self.login_btn.setText("Log In")
        self.cancel_btn.setEnabled(True)
        self.username_input.clear()
        self.password_input.clear()
        self.login_successful.emit(user)

    def on_login_error(self, error_msg):
        self.login_btn.setEnabled(True)
        self.login_btn.setText("Log In")
        self.cancel_btn.setEnabled(True)
        QMessageBox.critical(self, "Login Failed", error_msg)
