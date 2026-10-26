from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QRadioButton, QButtonGroup,
                             QDateEdit, QTimeEdit, QLineEdit, QMessageBox, QGroupBox)
from PySide6.QtCore import Qt, QDate, QTime
from src.client import api
from src.ui.theme import ThemeManager


class ManualClockInDialog(QDialog):
    def __init__(self, employees=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Supervisor Manual Staff Clock-In / Out")
        self.setFixedWidth(520)
        self.employees = employees or {}
        self.is_dark = ThemeManager.instance().is_dark()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        title_color = "#60a5fa" if self.is_dark else "#1d4ed8"
        desc_color = "#94a3b8" if self.is_dark else "#64748b"
        label_color = "#f1f5f9" if self.is_dark else "#1e293b"
        card_bg = "#18181b" if self.is_dark else "#f8fafc"
        card_border = "#27272a" if self.is_dark else "#e2e8f0"

        title = QLabel("Manual Staff Check-In / Out")
        title.setStyleSheet(f"font-size: 17px; font-weight: bold; color: {title_color};")
        layout.addWidget(title)

        desc = QLabel(
            "Record attendance for staff with injured/unreadable fingerprints or hardware issues. "
            "All entries are stamped with your supervisor username in the audit log."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {desc_color}; font-size: 12px; margin-bottom: 2px;")
        layout.addWidget(desc)

        form_group = QGroupBox("Attendance Details")
        form_group.setStyleSheet(f"""
            QGroupBox {{
                background-color: {card_bg};
                border: 1px solid {card_border};
                border-radius: 8px;
                margin-top: 14px;
                padding: 16px 14px 14px 14px;
                font-weight: bold;
                color: {title_color};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                left: 12px;
                color: {title_color};
            }}
        """)
        f_layout = QVBoxLayout(form_group)
        f_layout.setSpacing(12)

        # Employee Picker
        emp_label = QLabel("Select Employee:")
        emp_label.setStyleSheet(f"font-weight: 600; font-size: 13px; color: {label_color};")
        f_layout.addWidget(emp_label)

        self.emp_combo = QComboBox()
        self.emp_combo.setFixedHeight(36)
        sorted_emps = sorted(
            [e for e in self.employees.values() if e.get("status") == "active"],
            key=lambda e: (e.get("office_id", ""), e.get("full_name", ""))
        )
        for emp in sorted_emps:
            name = emp.get("full_name") or f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip()
            office = emp.get("office_id", "")
            emp_no = emp.get("employee_no", "")
            label = f"{name} ({emp_no}) - {office}"
            self.emp_combo.addItem(label, str(emp.get("_id", "")))

        if not sorted_emps:
            self.emp_combo.addItem("No active employees found", "")
            self.emp_combo.setEnabled(False)

        f_layout.addWidget(self.emp_combo)

        # Action Picker
        action_layout = QHBoxLayout()
        action_label = QLabel("Action:")
        action_label.setStyleSheet(f"font-weight: 600; font-size: 13px; color: {label_color};")
        action_layout.addWidget(action_label)

        self.action_group = QButtonGroup(self)
        self.radio_in = QRadioButton("Time In")
        self.radio_out = QRadioButton("Time Out")
        self.radio_in.setChecked(True)
        self.action_group.addButton(self.radio_in, 1)
        self.action_group.addButton(self.radio_out, 2)
        action_layout.addWidget(self.radio_in)
        action_layout.addWidget(self.radio_out)
        action_layout.addStretch()
        f_layout.addLayout(action_layout)

        # Date and Time
        dt_layout = QHBoxLayout()
        dt_layout.setSpacing(12)

        date_box = QVBoxLayout()
        d_lbl = QLabel("Date:")
        d_lbl.setStyleSheet(f"color: {label_color}; font-weight: 500;")
        date_box.addWidget(d_lbl)
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setFixedHeight(34)
        date_box.addWidget(self.date_edit)
        dt_layout.addLayout(date_box)

        time_box = QVBoxLayout()
        t_lbl = QLabel("Time (HH:MM):")
        t_lbl.setStyleSheet(f"color: {label_color}; font-weight: 500;")
        time_box.addWidget(t_lbl)
        self.time_edit = QTimeEdit(QTime.currentTime())
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setFixedHeight(34)
        time_box.addWidget(self.time_edit)
        dt_layout.addLayout(time_box)

        f_layout.addLayout(dt_layout)

        # Reason Picker
        r_lbl = QLabel("Reason for Manual Override:")
        r_lbl.setStyleSheet(f"color: {label_color}; font-weight: 500;")
        f_layout.addWidget(r_lbl)
        self.reason_combo = QComboBox()
        self.reason_combo.setFixedHeight(34)
        self.reason_combo.addItems([
            "Cut / injured finger",
            "Biometric unreadable / dry skin",
            "Scanner hardware issue",
            "Supervisor verified on-site arrival",
            "Off-site / field assignment",
            "Other (specify below)"
        ])
        f_layout.addWidget(self.reason_combo)

        self.custom_reason = QLineEdit()
        self.custom_reason.setPlaceholderText("Additional notes or custom reason...")
        self.custom_reason.setFixedHeight(34)
        f_layout.addWidget(self.custom_reason)

        layout.addWidget(form_group)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedHeight(36)
        cancel_bg = "#27272a" if self.is_dark else "#e5e7eb"
        cancel_fg = "#e2e8f0" if self.is_dark else "#374151"
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {cancel_bg};
                color: {cancel_fg};
                border: 1px solid {card_border};
                border-radius: 6px;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background-color: {"#3f3f46" if self.is_dark else "#d1d5db"};
            }}
        """)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.submit_btn = QPushButton("Submit Manual Record")
        self.submit_btn.setFixedHeight(36)
        self.submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                font-weight: 600;
                border-radius: 6px;
                padding: 0 20px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:pressed {
                background-color: #1e40af;
            }
        """)
        self.submit_btn.clicked.connect(self.submit_record)
        btn_layout.addWidget(self.submit_btn)

        layout.addLayout(btn_layout)

    def submit_record(self):
        emp_id = self.emp_combo.currentData()
        if not emp_id:
            QMessageBox.warning(self, "No Employee Selected", "Please select an active employee.")
            return

        action = "in" if self.radio_in.isChecked() else "out"
        work_date = self.date_edit.date().toString("yyyy-MM-dd")
        time_str = self.time_edit.time().toString("HH:mm")

        selected_reason = self.reason_combo.currentText()
        notes = self.custom_reason.text().strip()
        reason = f"{selected_reason}: {notes}" if notes else selected_reason

        self.submit_btn.setEnabled(False)
        self.submit_btn.setText("Submitting...")

        try:
            res = api.manual_attendance_record(
                employee_id=emp_id,
                action=action,
                work_date=work_date,
                time_str=time_str,
                reason=reason
            )
            QMessageBox.information(
                self,
                "Manual Record Confirmed",
                res.get("message", "Manual attendance recorded successfully.")
            )
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Submission Failed", str(exc))
            self.submit_btn.setEnabled(True)
            self.submit_btn.setText("Submit Manual Record")
