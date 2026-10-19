from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox
from PySide6.QtCore import Qt, QTimer
from src.scanner.worker import ScannerWorker
from src.services.fingerprint import FingerprintMatcher


class EnrollFingerprintDialog(QDialog):
    def __init__(self, employee_id, scanner_provider, parent=None):
        super().__init__(parent)
        self.employee_id = employee_id
        self.scanner_provider = scanner_provider
        self.worker = None
        self.step = 0
        
        scanner = getattr(self.scanner_provider, 'scanner', None)
        is_two_finger = False
        if scanner and hasattr(scanner, 'is_capture_available'):
            is_two_finger = scanner.is_capture_available(3)
            
        if is_two_finger:
            self.instructions = [
                "Capture 1 of 3: Place both thumbs on the scanner.",
                "Capture 2 of 3: Lift and place both thumbs again.",
                "Capture 3 of 3: Lift and place both thumbs one last time."
            ]
            self.image_types = [3, 3, 3]
            self.setWindowTitle("Enroll Fingerprints (Dual Finger)")
        else:
            self.instructions = [
                "Capture 1 of 3: Place your finger on the scanner.",
                "Capture 2 of 3: Lift and place your finger again.",
                "Capture 3 of 3: Lift and place your finger one last time."
            ]
            self.image_types = [2, 2, 2]
            self.setWindowTitle("Enroll Fingerprints (Single Finger)")
            
        self.captured_templates = []
        self.setFixedSize(600, 500)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.status_label = QLabel("Initializing scanner...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 16px; color: #333; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("background-color: white; border: 1px solid #ccc; border-radius: 8px;")
        self.preview_label.setMinimumSize(400, 350)
        self.preview_label.setScaledContents(False)
        layout.addWidget(self.preview_label, 1) 
        
        btn_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        
    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(500, self.start_scanner)
        
    def hideEvent(self, event):
        super().hideEvent(event)
        self.stop_scanner()
        
    def start_scanner(self):
        if not self.isVisible():
            return
        if not self.scanner_provider.scanner:
            self.status_label.setText("Scanner not connected!")
            return
            
        self.status_label.setText(self.instructions[self.step])
        self.status_label.setStyleSheet("font-size: 18px; color: #4285F4; font-weight: bold;")
            
        if not self.worker:
            self.worker = ScannerWorker(self.scanner_provider.scanner, image_type=self.image_types[self.step])
            self.worker.scan_status.connect(self.on_status)
            self.worker.scan_error.connect(self.on_error)
            self.worker.preview_frame.connect(self.on_preview_frame)
            self.worker.scan_complete.connect(self.on_scan_complete)
            self.worker.start()
            
    def stop_scanner(self):
        if hasattr(self, 'countdown_timer'):
            self.countdown_timer.stop()
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait() 
        self.worker = None
            
    def on_status(self, msg):
        pass
        
    def on_error(self, msg):
        self.status_label.setStyleSheet("font-size: 16px; color: red;")
        self.status_label.setText(f"Error: {msg}")
        
    def on_preview_frame(self, img_bytes, w, h):
        from PySide6.QtGui import QImage, QPixmap, QTransform
        img = QImage(img_bytes, w, h, w, QImage.Format_Grayscale8)
        pixmap = QPixmap.fromImage(img).transformed(QTransform().rotate(180))
        scaled = pixmap.scaled(self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.preview_label.setPixmap(scaled)
        
    def on_scan_complete(self, template_data):
        if not isinstance(template_data, dict) or template_data.get("status") != "success":
            return
            
        self.captured_templates.append({
            "image": template_data.get("image"),
            "width": template_data.get("width"),
            "height": template_data.get("height")
        })
        self.step += 1
        
        self.stop_scanner()
        
        if self.step < len(self.instructions):
            self.start_countdown(2, self.start_scanner)
        else:
            self.status_label.setStyleSheet("font-size: 16px; color: green;")
            self.status_label.setText("Extracting minutiae... Please wait.")
            QTimer.singleShot(100, self.save_templates)
            
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
            self.status_label.setText(f"Capture successful. Next capture in ... {self.countdown_seconds}")
            self.countdown_seconds -= 1
        else:
            self.countdown_timer.stop()
            self.countdown_callback()
        
    def save_templates(self):
        from src.client import ClientDatabase as DatabaseManager
        from bson import ObjectId
        import datetime
        
        db = DatabaseManager.get_db()
        
        matcher = FingerprintMatcher()
        all_descriptors = []
        
        for template in self.captured_templates:
            descriptors = matcher.extract_descriptors(template["image"], template["width"], template["height"])
            if descriptors is not None:
                all_descriptors.append(descriptors)
        
        if not all_descriptors:
            QMessageBox.critical(self, "Error", "Failed to extract fingerprint features. Try again.")
            self.reject()
            return
            
        from src.client import api
        try:
            api.call(f'/employees/{self.employee_id}/fingerprint',
                     {'samples': [descriptors.tolist() for descriptors in all_descriptors]})
        except ValueError as exc:
            QMessageBox.critical(self, 'Enrollment not saved', str(exc))
            return
        QMessageBox.information(self, 'Success', 'Fingerprints enrolled for this office.')
        self.accept()
