import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QGroupBox, QFormLayout, QLineEdit, QRadioButton, QButtonGroup)
from PySide6.QtCore import Qt, Signal, QTimer, QThread
from PySide6.QtGui import QFont, QPixmap
from src.utils import get_asset_path, speak
from src.scanner.worker import ScannerWorker


class ScanWorker(QThread):
    scan_success = Signal(dict)
    scan_error = Signal(str)

    def __init__(self, sample, action):
        super().__init__()
        self.sample = sample
        self.action = action

    def run(self):
        try:
            from src.client import api
            result = api.call('/scan', {'samples': [self.sample.tolist()], 'action': self.action})
            self.scan_success.emit(result)
        except Exception as exc:
            self.scan_error.emit(str(exc))


class KioskWidget(QWidget):
    login_requested = Signal()

    def __init__(self, scanner_provider, parent=None):
        super().__init__(parent)
        self.scanner_provider = scanner_provider
        self.worker = None
        self.scan_worker = None
        self.reconnect_timer = QTimer(self)
        self.reconnect_timer.setSingleShot(True)
        self.reconnect_timer.timeout.connect(self.reconnect_scanner)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        top_layout = QHBoxLayout()
        logo_path = get_asset_path("randaframes logo.jpg")
        if not os.path.exists(logo_path):
            logo_path = get_asset_path("icon.ico")
        if os.path.exists(logo_path):
            logo_label = QLabel()
            pixmap = QPixmap(logo_path).scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
            logo_label.setStyleSheet("margin-right: 8px;")
            top_layout.addWidget(logo_label)

        title = QLabel("Randaframes Attendance Terminal")
        title.setFont(QFont("Arial", 20, QFont.Bold))

        admin_btn = QPushButton("Admin Login")
        admin_btn.setFixedSize(160, 38)
        admin_btn.clicked.connect(self.login_requested.emit)

        top_layout.addWidget(title)
        top_layout.addStretch()
        top_layout.addWidget(admin_btn)
        reconnect = QPushButton("Reconnect scanner")
        reconnect.clicked.connect(self.reconnect_scanner)
        top_layout.addWidget(reconnect)

        main_layout.addLayout(top_layout)

        action_layout = QHBoxLayout()
        action_label = QLabel("Select Action:")
        action_label.setFont(QFont("Arial", 16, QFont.Bold))

        self.action_group = QButtonGroup(self)

        self.radio_in = QRadioButton("Time In")
        self.radio_in.setFont(QFont("Arial", 16))
        self.radio_in.setStyleSheet("spacing: 10px; margin-right: 20px;")
        self.radio_in.setChecked(True)

        self.radio_out = QRadioButton("Time Out")
        self.radio_out.setFont(QFont("Arial", 16))
        self.radio_out.setStyleSheet("spacing: 10px;")

        self.action_group.addButton(self.radio_in)
        self.action_group.addButton(self.radio_out)

        action_layout.addStretch()
        action_layout.addWidget(action_label)
        action_layout.addWidget(self.radio_in)
        action_layout.addWidget(self.radio_out)
        action_layout.addStretch()

        main_layout.addLayout(action_layout)

        self.status_label = QLabel("Please place your finger on the scanner.")
        self.status_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #0078D7; margin: 10px 0;")
        main_layout.addWidget(self.status_label)

        self.countdown_label = QLabel("")
        self.countdown_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setStyleSheet("color: #888; margin-bottom: 10px;")
        main_layout.addWidget(self.countdown_label)

        content_layout = QHBoxLayout()

        left_group = QGroupBox("Place your finger on the scanner")
        left_layout = QVBoxLayout(left_group)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        self.preview_label.setMinimumSize(400, 400)
        self.preview_label.setScaledContents(False)

        instruction = QLabel("Please place finger on the scanner platen.")
        instruction.setAlignment(Qt.AlignCenter)

        left_layout.addWidget(self.preview_label)
        left_layout.addWidget(instruction)

        right_group = QGroupBox("Employee Verification Result")
        right_layout_main = QHBoxLayout(right_group)

        info_layout = QFormLayout()
        info_layout.setVerticalSpacing(20)

        self.name_field = QLineEdit()
        self.name_field.setReadOnly(True)
        self.name_field.setStyleSheet("font-size: 16px; padding: 5px;")

        self.id_field = QLineEdit()
        self.id_field.setReadOnly(True)
        self.id_field.setStyleSheet("font-size: 16px; padding: 5px;")

        self.job_field = QLineEdit()
        self.job_field.setReadOnly(True)
        self.job_field.setStyleSheet("font-size: 16px; padding: 5px;")

        self.action_field = QLineEdit()
        self.action_field.setReadOnly(True)
        self.action_field.setStyleSheet("font-size: 16px; padding: 5px; font-weight: bold;")

        label_font = QFont("Arial", 12)
        l1 = QLabel("Name:")
        l1.setFont(label_font)
        l2 = QLabel("Employee ID:")
        l2.setFont(label_font)
        l3 = QLabel("Job Title:")
        l3.setFont(label_font)
        l4 = QLabel("Status:")
        l4.setFont(label_font)

        info_layout.addRow(l1, self.name_field)
        info_layout.addRow(l2, self.id_field)
        info_layout.addRow(l3, self.job_field)
        info_layout.addRow(l4, self.action_field)

        photo_layout = QVBoxLayout()
        photo_title = QLabel("Employee Photo")
        photo_title.setFont(label_font)
        photo_title.setAlignment(Qt.AlignCenter)
        self.photo_label = QLabel()
        self.photo_label.setFixedSize(150, 150)
        self.photo_label.setStyleSheet("border: 1px solid #ccc; background-color: #eee;")
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setText("No Photo")

        photo_layout.addWidget(photo_title)
        photo_layout.addWidget(self.photo_label)
        photo_layout.addStretch()

        right_layout_main.addLayout(info_layout, stretch=2)
        right_layout_main.addLayout(photo_layout, stretch=1)

        content_layout.addWidget(left_group)
        content_layout.addWidget(right_group)
        content_layout.setStretchFactor(left_group, 1)
        content_layout.setStretchFactor(right_group, 1)

        main_layout.addLayout(content_layout)
        main_layout.addStretch()

    def showEvent(self, event):
        super().showEvent(event)
        speak("Welcome to Randaframes Attendance System.")
        self.start_scanner()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.stop_scanner()

    def start_scanner(self):
        if not self.isVisible():
            return
        from src.client import api
        if not api.token:
            if not api.restore_saved_session():
                self.update_error("Please click 'Admin Login' to log in with an office account first.")
                return
        if self.worker is None or not self.worker.isRunning():
            self.worker = ScannerWorker(self.scanner_provider.scanner, image_type=None)
            self.worker.scan_status.connect(self.update_status)
            self.worker.scan_error.connect(self.on_scanner_error)
            self.worker.preview_frame.connect(self.update_preview)
            self.worker.scan_complete.connect(self.process_scan)
            self.worker.start()

    def force_capture(self):
        if self.scanner_provider.scanner:
            self.scanner_provider.scanner.take_result_image_manually()

    def update_preview(self, img_bytes, w, h):
        from PySide6.QtGui import QImage, QPixmap, QTransform
        img = QImage(img_bytes, w, h, w, QImage.Format_Grayscale8)
        pixmap = QPixmap.fromImage(img).transformed(QTransform().rotate(180))
        scaled = pixmap.scaled(self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.preview_label.setPixmap(scaled)

    def stop_scanner(self):
        self.reconnect_timer.stop()
        if hasattr(self, 'countdown_timer'):
            self.countdown_timer.stop()
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
            self.worker = None

    def update_status(self, msg):
        self.status_label.setStyleSheet("color: #0078D7; margin: 10px 0;")
        self.status_label.setText(f"Scanner Status: {msg}")

    def update_error(self, msg):
        self.status_label.setStyleSheet("color: red; margin: 10px 0; font-weight: bold;")
        self.status_label.setText(f"Scanner Error: {msg}")
        self.name_field.clear()
        self.id_field.clear()
        self.job_field.clear()
        self.action_field.clear()
        self.photo_label.setText("No Photo")
        self.photo_label.setPixmap(QPixmap())

    def start_countdown(self, seconds, callback):
        self.countdown_seconds = seconds
        self.countdown_callback = callback
        if not hasattr(self, 'countdown_timer'):
            self.countdown_timer = QTimer(self)
            self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_timer.start(1000)
        self.update_countdown()

    def update_countdown(self):
        if self.countdown_seconds > 0:
            self.countdown_label.setText(f"Please scan again in {self.countdown_seconds}s...")
            self.countdown_seconds -= 1
        else:
            self.countdown_timer.stop()
            self.countdown_label.setText("")
            self.countdown_callback()

    def reset_and_start(self):
        self.name_field.clear()
        self.id_field.clear()
        self.job_field.clear()
        self.action_field.clear()
        self.photo_label.setText("No Photo")
        self.photo_label.setPixmap(QPixmap())
        self.status_label.setStyleSheet("color: #0078D7; margin: 10px 0;")
        self.status_label.setText("Please place your finger on the scanner.")
        self.start_scanner()

    def process_scan(self, template_data):
        self.stop_scanner()
        try:
            from src.services.fingerprint import FingerprintMatcher
            if template_data.get('status') != 'success':
                raise ValueError('Scan failed. Please try again.')
            sample = FingerprintMatcher().extract_descriptors(template_data['image'], template_data['width'], template_data['height'])
            if sample is None:
                raise ValueError('Could not read fingerprint clearly. Please scan again.')

            self.update_status('Verifying with central server...')
            action = 'in' if self.radio_in.isChecked() else 'out'

            self.scan_worker = ScanWorker(sample, action)
            self.scan_worker.scan_success.connect(self.on_scan_success)
            self.scan_worker.scan_error.connect(self.on_scan_error)
            self.scan_worker.start()

        except Exception as exc:
            self.update_error(str(exc))
            if self.isVisible():
                self.start_countdown(3, self.reset_and_start)

    def on_scan_success(self, result):
        employee = result['employee']
        first_name = employee.get('first_name', '')
        last_name = employee.get('last_name', '')
        action = result['action']

        self.name_field.setText(f"{first_name} {last_name}".strip())
        self.id_field.setText(employee.get('employee_no', ''))
        self.job_field.setText(employee.get('job_title', ''))
        self.action_field.setText(action)
        self.status_label.setText(f"{action} (Confirmed)")
        self.status_label.setStyleSheet('color: green; font-size: 20px;')

        if employee.get('photo_bytes'):
            pixmap = QPixmap()
            pixmap.loadFromData(employee['photo_bytes'])
            self.photo_label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.photo_label.setText("No Photo")
            self.photo_label.setPixmap(QPixmap())

        if 'Time In' in action:
            speak(f"Welcome, {first_name}.")
        elif 'Time Out' in action:
            speak(f"Goodbye, {first_name}. Have a great day!")
        elif 'Already' in action:
            speak(f"You are already clocked in, {first_name}.")
        else:
            speak(f"Hello, {first_name}.")

        if self.isVisible():
            self.start_countdown(4, self.reset_and_start)

    def on_scan_error(self, err_msg):
        self.update_error(err_msg)
        if "not recognized" in err_msg.lower() or "read" in err_msg.lower():
            speak("Fingerprint not recognized. Please scan again.")
        if self.isVisible():
            self.start_countdown(3, self.reset_and_start)

    def reconnect_scanner(self):
        if not self.isVisible():
            return
        self.stop_scanner()
        self.scanner_provider.close()
        if self.scanner_provider.initialize():
            self.start_scanner()
        else:
            self.update_error('Connect the scanner and install the USB driver, then click Reconnect scanner.')
            self.reconnect_timer.start(5000)

    def on_scanner_error(self, message):
        self.update_error(message)
        self.reconnect_timer.start(5000)
