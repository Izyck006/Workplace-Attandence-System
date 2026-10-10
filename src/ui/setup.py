from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from src.services.auth import AuthService
from src.data.database import DatabaseManager

class SetupWidget(QWidget):
    setup_complete = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.auth_service = AuthService()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("Initial Setup")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        
        desc = QLabel("Welcome! Let's create the Main Admin account.")
        desc.setAlignment(Qt.AlignCenter)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Admin Username")
        self.username_input.setFixedWidth(300)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password (min 10 chars)")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedWidth(300)
        
        self.create_btn = QPushButton("Create Admin Account")
        self.create_btn.setFixedWidth(300)
        self.create_btn.clicked.connect(self.on_create)

        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addSpacing(20)
        layout.addWidget(self.username_input, alignment=Qt.AlignCenter)
        layout.addWidget(self.password_input, alignment=Qt.AlignCenter)
        layout.addSpacing(20)
        layout.addWidget(self.create_btn, alignment=Qt.AlignCenter)

    def on_create(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or len(password) < 10:
            QMessageBox.warning(self, "Error", "Username is required and password must be at least 10 characters.")
            return

        db = DatabaseManager.get_db()
        users = db.users
        
        try:
            hashed_pw = self.auth_service.hash_password(password)
            users.insert_one({
                "username": username,
                "password_hash": hashed_pw,
                "role": "main_admin",
                "is_active": True,
                "failed_attempts": 0,
                "must_change_password": False
            })
            QMessageBox.information(self, "Success", "Main Admin created. Please save your recovery code: RECOVERY-1234-ABCD")
            self.setup_complete.emit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not create account: {e}")
