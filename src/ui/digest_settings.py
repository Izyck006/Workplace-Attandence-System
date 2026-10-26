from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QCheckBox, QComboBox,
                             QMessageBox, QGroupBox, QScrollArea, QWidget, QFormLayout)
from PySide6.QtCore import Qt
from src.client import api
from src.offices import OFFICES


class DigestSettingsDialog(QDialog):
    def __init__(self, user=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Daily Morning Email Digest Settings")
        self.setFixedWidth(560)
        self.user = user or getattr(api, "user", {}) or {}
        self.is_master = self.user.get("role") == "main_admin"
        self.office_inputs = {}
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        title = QLabel("Morning Attendance Email Digest")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1e3a8a;")
        layout.addWidget(title)

        desc = QLabel(
            "Configure email recipients for the automated daily morning attendance digest. "
            "Every morning, management receives a complete summary of who is present, late, or absent."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #6b7280; font-size: 12px; margin-bottom: 6px;")
        layout.addWidget(desc)

        self.smtp_status_label = QLabel("Checking mail server status...")
        self.smtp_status_label.setStyleSheet("font-size: 11px; padding: 4px 8px; border-radius: 4px; background: #f3f4f6; color: #4b5563;")
        layout.addWidget(self.smtp_status_label)

        if self.is_master:
            # Executive emails
            exec_group = QGroupBox("Executive & Head Office Recipients")
            e_layout = QVBoxLayout(exec_group)
            e_layout.addWidget(QLabel("Email addresses (comma-separated):"))
            self.exec_emails_input = QLineEdit()
            self.exec_emails_input.setPlaceholderText("md@randaframes.com, hr@randaframes.com, ops@randaframes.com")
            self.exec_emails_input.setFixedHeight(34)
            e_layout.addWidget(self.exec_emails_input)
            layout.addWidget(exec_group)

            # Schedule & Enable
            sched_layout = QHBoxLayout()
            self.enable_checkbox = QCheckBox("Enable Daily Morning Digest")
            self.enable_checkbox.setChecked(True)
            sched_layout.addWidget(self.enable_checkbox)

            sched_layout.addStretch()
            sched_layout.addWidget(QLabel("Dispatch Time:"))
            self.hour_combo = QComboBox()
            for h in range(7, 13):
                self.hour_combo.addItem(f"{h:02d}:00 AM Lagos Time", h)
            self.hour_combo.setCurrentIndex(2)  # 9:00 AM
            sched_layout.addWidget(self.hour_combo)
            layout.addLayout(sched_layout)

            # Branch Office emails
            branch_group = QGroupBox("Branch Office Notification Emails")
            b_layout = QVBoxLayout(branch_group)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFixedHeight(160)
            scroll_content = QWidget()
            s_form = QFormLayout(scroll_content)
            s_form.setSpacing(8)

            for office in OFFICES:
                off_id = office["_id"]
                off_name = f"{office['name']} ({office['location']})"
                inp = QLineEdit()
                inp.setPlaceholderText(f"manager.{off_id}@randaframes.com")
                inp.setFixedHeight(28)
                self.office_inputs[off_id] = inp
                s_form.addRow(QLabel(off_name), inp)

            scroll.setWidget(scroll_content)
            b_layout.addWidget(scroll)
            layout.addWidget(branch_group)

        else:
            # Office admin view (single branch)
            branch_group = QGroupBox("Your Branch Notification Email")
            b_layout = QVBoxLayout(branch_group)
            b_layout.addWidget(QLabel(f"Alert email for {self.user.get('office_id', 'this office')}:"))
            self.single_office_email = QLineEdit()
            self.single_office_email.setPlaceholderText("your-email@randaframes.com")
            self.single_office_email.setFixedHeight(34)
            b_layout.addWidget(self.single_office_email)
            layout.addWidget(branch_group)

        # Action Buttons
        btn_layout = QHBoxLayout()

        self.test_btn = QPushButton("Send Test Digest Now")
        self.test_btn.setFixedHeight(36)
        self.test_btn.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: #ffffff;
                font-weight: 600;
                border-radius: 6px;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #047857;
            }
        """)
        self.test_btn.clicked.connect(self.send_test_digest)
        btn_layout.addWidget(self.test_btn)

        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Close")
        self.cancel_btn.setFixedHeight(36)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("Save Settings")
        self.save_btn.setFixedHeight(36)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                font-weight: 600;
                border-radius: 6px;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        self.save_btn.clicked.connect(self.save_settings)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

    def load_settings(self):
        try:
            res = api.get_digest_settings()
            smtp_ok = res.get("smtp_configured", False)
            if smtp_ok:
                self.smtp_status_label.setText("● Mail server connected (SMTP configured in .env)")
                self.smtp_status_label.setStyleSheet("color: #059669; font-weight: bold; background: #ecfdf5; padding: 4px 8px; border-radius: 4px;")
            else:
                self.smtp_status_label.setText("● SMTP credentials not configured in .env (Emails will be simulated in system console until configured)")
                self.smtp_status_label.setStyleSheet("color: #d97706; font-weight: bold; background: #fffbeb; padding: 4px 8px; border-radius: 4px;")

            if self.is_master:
                exec_emails = res.get("executive_emails", [])
                self.exec_emails_input.setText(", ".join(exec_emails))
                self.enable_checkbox.setChecked(res.get("is_enabled", True))
                send_hour = res.get("send_hour", 9)
                idx = self.hour_combo.findData(send_hour)
                if idx >= 0:
                    self.hour_combo.setCurrentIndex(idx)

                office_emails = res.get("office_emails", {})
                for off_id, inp in self.office_inputs.items():
                    if off_id in office_emails:
                        inp.setText(office_emails[off_id])
            else:
                self.single_office_email.setText(res.get("office_email", ""))

        except Exception as exc:
            self.smtp_status_label.setText(f"Could not load settings: {exc}")
            self.smtp_status_label.setStyleSheet("color: #dc2626;")

    def save_settings(self):
        self.save_btn.setEnabled(False)
        self.save_btn.setText("Saving...")

        try:
            if self.is_master:
                raw_exec = self.exec_emails_input.text()
                exec_list = [e.strip() for e in raw_exec.split(",") if e.strip()]
                office_dict = {
                    off_id: inp.text().strip()
                    for off_id, inp in self.office_inputs.items()
                    if inp.text().strip()
                }
                send_hour = self.hour_combo.currentData()
                is_enabled = self.enable_checkbox.isChecked()

                res = api.save_digest_settings(
                    executive_emails=exec_list,
                    office_emails=office_dict,
                    send_hour=send_hour,
                    is_enabled=is_enabled
                )
            else:
                single_email = self.single_office_email.text().strip()
                res = api.save_digest_settings(office_email=single_email)

            QMessageBox.information(self, "Settings Saved", res.get("message", "Digest settings saved successfully."))
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Save Error", str(exc))
            self.save_btn.setEnabled(True)
            self.save_btn.setText("Save Settings")

    def send_test_digest(self):
        self.test_btn.setEnabled(False)
        self.test_btn.setText("Sending...")

        try:
            # Let the admin choose which email receives the test
            target_test = ""
            if self.is_master and self.exec_emails_input.text().strip():
                first_email = [e.strip() for e in self.exec_emails_input.text().split(",") if e.strip()]
                if first_email:
                    target_test = first_email[0]
            elif not self.is_master and hasattr(self, 'single_office_email'):
                target_test = self.single_office_email.text().strip()

            res = api.send_digest_now(test_email=target_test or None)
            delivery = res.get("delivery", {})
            stats = res.get("stats", {})
            msg = (
                f"Morning Digest Generated!\n\n"
                f"• Total Staff: {stats.get('total_staff')}\n"
                f"• Present Today: {stats.get('present')}\n"
                f"• Turnout Rate: {stats.get('turnout')}\n"
                f"• Recipients: {', '.join(res.get('recipients', []))}\n\n"
                f"Status: {delivery.get('message', 'Delivered successfully.')}"
            )
            QMessageBox.information(self, "Test Digest Result", msg)
        except Exception as exc:
            QMessageBox.critical(self, "Test Send Failed", str(exc))
        finally:
            self.test_btn.setEnabled(True)
            self.test_btn.setText("Send Test Digest Now")
