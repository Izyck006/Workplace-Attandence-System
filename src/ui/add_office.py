import re
import secrets
import string
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QMessageBox, QApplication, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from src.client import api
from src.ui.password_input import PasswordLineEdit


def generate_secure_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%&*?"
    while True:
        pw = "".join(secrets.choice(alphabet) for _ in range(length))
        if (any(c.islower() for c in pw) and any(c.isupper() for c in pw)
                and any(c.isdigit() for c in pw) and any(c in "!@#$%&*?" for c in pw)):
            return pw


class AddOfficeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Office")
        self.setFixedWidth(480)
        self.created_office = None
        self.created_credentials = None

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 20, 24, 20)

        title = QLabel("Add New Company Office")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        layout.addWidget(title)

        desc = QLabel("Set up a new branch location and its dedicated administrator account. The administrator can immediately log in and manage the local attendance terminal.")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #888888; font-size: 12px; margin-bottom: 4px;")
        layout.addWidget(desc)

        layout.addWidget(QLabel("Office Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Logistics Ibadan")
        self.name_input.textChanged.connect(self._on_name_changed)
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("Location / City:"))
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("e.g. Ibadan")
        layout.addWidget(self.location_input)

        layout.addWidget(QLabel("Office ID (System Slug):"))
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("e.g. logistics-ibadan")
        self.id_input.textChanged.connect(self._on_id_changed)
        layout.addWidget(self.id_input)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setStyleSheet("color: #333333; margin: 4px 0;")
        layout.addWidget(sep)

        layout.addWidget(QLabel("Office Admin Username:"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("e.g. logistics-ibadan")
        layout.addWidget(self.username_input)

        layout.addWidget(QLabel("Temporary Password:"))
        pw_box = QHBoxLayout()
        self.pw_input = PasswordLineEdit("Temporary Password")
        self.pw_input.setText(generate_secure_password())
        pw_box.addWidget(self.pw_input)

        self.regen_btn = QPushButton("Generate Password")
        self.regen_btn.setToolTip("Generate a fresh secure temporary password and copy it to clipboard")
        self.regen_btn.setFixedHeight(34)
        self.regen_btn.clicked.connect(self._regenerate_and_copy_password)
        pw_box.addWidget(self.regen_btn)

        self.copy_pw_btn = QPushButton("Copy Password")
        self.copy_pw_btn.setToolTip("Copy the temporary password to clipboard")
        self.copy_pw_btn.setFixedHeight(34)
        self.copy_pw_btn.clicked.connect(self._copy_password_only)
        pw_box.addWidget(self.copy_pw_btn)
        layout.addLayout(pw_box)

        copy_box = QHBoxLayout()
        self.copy_btn = QPushButton("Copy All Credentials to Clipboard")
        self.copy_btn.setFixedHeight(32)
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #38bdf8;
                border: 1px solid #0284c7;
                border-radius: 6px;
                font-weight: 600;
                font-size: 12px;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background-color: #0369a1;
                color: #ffffff;
            }
        """)
        self.copy_btn.clicked.connect(self._copy_credentials)
        copy_box.addWidget(self.copy_btn)
        copy_box.addStretch()
        layout.addLayout(copy_box)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedHeight(36)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.create_btn = QPushButton("Create Office")
        self.create_btn.setFixedHeight(36)
        self.create_btn.setMinimumWidth(130)
        self.create_btn.setStyleSheet("font-weight: bold; font-size: 13px;")
        self.create_btn.clicked.connect(self._on_create)
        btn_layout.addWidget(self.create_btn)

        layout.addLayout(btn_layout)

    def _on_name_changed(self, text: str):
        slug = re.sub(r"[^a-zA-Z0-9_-]", "", text.strip().lower().replace(" ", "-"))[:50]
        self.id_input.setText(slug)

    def _on_id_changed(self, text: str):
        self.username_input.setText(text.strip().lower())

    def _regenerate_and_copy_password(self):
        new_pw = generate_secure_password()
        self.pw_input.setText(new_pw)
        QApplication.clipboard().setText(new_pw)
        self.regen_btn.setText("Generated & Copied!")
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2000, lambda: self.regen_btn.setText("Generate Password"))

    def _copy_password_only(self):
        pw = self.pw_input.text()
        if pw:
            QApplication.clipboard().setText(pw)
            self.copy_pw_btn.setText("Copied!")
            from PySide6.QtCore import QTimer
            QTimer.singleShot(2000, lambda: self.copy_pw_btn.setText("Copy Password"))

    def _get_credentials_text(self) -> str:
        name = self.name_input.text().strip()
        loc = self.location_input.text().strip()
        oid = self.id_input.text().strip()
        user = self.username_input.text().strip()
        pw = self.pw_input.text()
        return (
            f"Randaframes Attendance - Office Credentials\n"
            f"-----------------------------------------\n"
            f"Office Name: {name}\n"
            f"Location: {loc}\n"
            f"Office ID: {oid}\n"
            f"Username: {user}\n"
            f"Temporary Password: {pw}\n"
            f"-----------------------------------------\n"
            f"Note: You will be prompted to set your permanent password upon first login."
        )

    def _copy_credentials(self):
        text = self._get_credentials_text()
        QApplication.clipboard().setText(text)
        self.copy_btn.setText("Copied to Clipboard!")
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2000, lambda: self.copy_btn.setText("Copy All Credentials to Clipboard"))

    def _on_create(self):
        name = self.name_input.text().strip()
        loc = self.location_input.text().strip()
        oid = self.id_input.text().strip()
        user = self.username_input.text().strip()
        pw = self.pw_input.text()

        if not name:
            QMessageBox.warning(self, "Validation Error", "Office Name is required.")
            self.name_input.setFocus()
            return
        if not loc:
            QMessageBox.warning(self, "Validation Error", "Location / City is required.")
            self.location_input.setFocus()
            return
        if not oid:
            QMessageBox.warning(self, "Validation Error", "Office ID is required.")
            self.id_input.setFocus()
            return
        if not user:
            QMessageBox.warning(self, "Validation Error", "Office Admin Username is required.")
            self.username_input.setFocus()
            return
        if not pw or len(pw) < 8:
            QMessageBox.warning(self, "Validation Error", "Password must be at least 8 characters.")
            self.pw_input.setFocus()
            return

        self.create_btn.setEnabled(False)
        self.create_btn.setText("Creating...")

        try:
            result = api.call("/offices/create", {
                "name": name,
                "location": loc,
                "office_id": oid,
                "username": user,
                "password": pw
            })
            self.created_office = result.get("office")
            if self.created_office:
                from src.offices import register_office
                register_office(self.created_office)
            self.created_credentials = {
                "username": user,
                "password": pw,
                "name": name,
                "location": loc
            }
            QApplication.clipboard().setText(self._get_credentials_text())

            QMessageBox.information(
                self,
                "Office Created Successfully",
                f"Office '{name}' has been created!\n\n"
                f"The login credentials have been copied to your clipboard:\n"
                f"• Username: {user}\n"
                f"• Temporary Password: {pw}\n\n"
                f"Please share these credentials securely with the branch administrator."
            )
            self.accept()
        except Exception as exc:
            self.create_btn.setEnabled(True)
            self.create_btn.setText("Create Office")
            QMessageBox.critical(self, "Creation Failed", str(exc))
