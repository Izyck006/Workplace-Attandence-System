import sys
import os
import time
import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, 
    QPushButton, QWidget, QFrame, QMessageBox
)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPixmap, QFont
from src.scanner.kojack import KojackScanner
from src.services.fingerprint import FingerprintMatcher
import cv2
import numpy as np

try:
    import winsound
except ImportError:
    winsound = None

class ColumboScannerTestApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fingerprint Scanner Test Tool (Columbo / Kojack)")
        self.setFixedSize(700, 820)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e2e;
            }
            QLabel {
                color: #cdd6f4;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QFrame#card {
                background-color: #181825;
                border-radius: 12px;
                border: 1px solid #313244;
            }
            QPushButton {
                background-color: #89b4fa;
                color: #11111b;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
            QPushButton:pressed {
                background-color: #74c7ec;
            }
            QPushButton#secondary {
                background-color: #313244;
                color: #cdd6f4;
            }
            QPushButton#secondary:hover {
                background-color: #45475a;
            }
            QPushButton#captureBtn {
                background-color: #a6e3a1;
                color: #11111b;
            }
            QPushButton#captureBtn:hover {
                background-color: #94e2d5;
            }
        """)

        self.scanner = KojackScanner()
        self.matcher = FingerprintMatcher()
        self.current_image_bytes = None
        self.current_w = 0
        self.current_h = 0
        self.is_captured = False
        self.finger_present = False

        self.setup_ui()
        self.init_scanner()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header Card
        header_card = QFrame()
        header_card.setObjectName("card")
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(15, 12, 15, 12)

        title_layout = QVBoxLayout()
        title_label = QLabel("Scanner Diagnostics & Test Tool")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.device_info_label = QLabel("Detecting scanner...")
        self.device_info_label.setStyleSheet("color: #a6adc8; font-size: 13px;")
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.device_info_label)
        header_layout.addLayout(title_layout)

        header_layout.addStretch()

        self.status_badge = QLabel("Initializing")
        self.status_badge.setStyleSheet("""
            background-color: #45475a;
            color: #cdd6f4;
            padding: 6px 14px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 12px;
        """)
        header_layout.addWidget(self.status_badge)
        main_layout.addWidget(header_card)

        # Center Preview Card
        preview_card = QFrame()
        preview_card.setObjectName("card")
        preview_layout = QVBoxLayout(preview_card)
        preview_layout.setContentsMargins(15, 15, 15, 15)

        self.preview_label = QLabel("No Live Feed")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setFixedSize(450, 480)
        self.preview_label.setStyleSheet("""
            background-color: #11111b;
            border: 2px dashed #45475a;
            border-radius: 10px;
            color: #6c7086;
            font-size: 15px;
        """)
        preview_layout.addWidget(self.preview_label, alignment=Qt.AlignCenter)

        # Live Status Prompt
        self.prompt_label = QLabel("👉 Place your finger on the scanner platen")
        self.prompt_label.setAlignment(Qt.AlignCenter)
        self.prompt_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #89b4fa; margin-top: 5px;")
        preview_layout.addWidget(self.prompt_label)

        # Metrics bar
        self.metrics_label = QLabel("Resolution: 500 DPI | Size: 0x0 | Keypoints: -")
        self.metrics_label.setAlignment(Qt.AlignCenter)
        self.metrics_label.setStyleSheet("font-size: 12px; color: #a6adc8;")
        preview_layout.addWidget(self.metrics_label)

        main_layout.addWidget(preview_card)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.force_btn = QPushButton("Force Capture")
        self.force_btn.setObjectName("captureBtn")
        self.force_btn.clicked.connect(self.on_force_capture)
        btn_layout.addWidget(self.force_btn)

        self.save_btn = QPushButton("Save Image")
        self.save_btn.setObjectName("secondary")
        self.save_btn.clicked.connect(self.on_save_image)
        self.save_btn.setEnabled(False)
        btn_layout.addWidget(self.save_btn)

        self.reset_btn = QPushButton("New Scan")
        self.reset_btn.setObjectName("secondary")
        self.reset_btn.clicked.connect(self.on_reset_scan)
        btn_layout.addWidget(self.reset_btn)

        main_layout.addLayout(btn_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Polling Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.poll_scanner)

    def init_scanner(self):
        count = self.scanner.get_device_count()
        if count == 0:
            self.device_info_label.setText("No scanner found. Please plug in your scanner.")
            self.status_badge.setText("DISCONNECTED")
            self.status_badge.setStyleSheet("background-color: #f38ba8; color: #11111b; padding: 6px 14px; border-radius: 6px; font-weight: bold;")
            self.prompt_label.setText("Scanner not connected. Plug in your Columbo scanner and restart.")
            return

        if not self.scanner.open_device(0):
            self.device_info_label.setText("Device detected but failed to open.")
            self.status_badge.setText("OPEN ERROR")
            self.status_badge.setStyleSheet("background-color: #f38ba8; color: #11111b; padding: 6px 14px; border-radius: 6px; font-weight: bold;")
            return

        supported_type = self.scanner.get_supported_image_type()
        mode_names = {
            1: "Single Finger (Roll)",
            2: "Columbo Single Finger (Flat)",
            3: "Two Fingers (Flat)",
            4: "Four Fingers (Flat)"
        }
        mode_str = mode_names.get(supported_type, f"Type {supported_type}")
        self.device_info_label.setText(f"Connected: IB Scanner | Mode: {mode_str}")
        self.status_badge.setText("CONNECTED")
        self.status_badge.setStyleSheet("background-color: #a6e3a1; color: #11111b; padding: 6px 14px; border-radius: 6px; font-weight: bold;")

        self.start_capture()

    def start_capture(self):
        self.is_captured = False
        self.current_image_bytes = None
        self.save_btn.setEnabled(False)
        self.preview_label.setStyleSheet("""
            background-color: #11111b;
            border: 2px dashed #89b4fa;
            border-radius: 10px;
        """)
        self.prompt_label.setText("👉 Place your finger firmly on the scanner platen")
        self.prompt_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #89b4fa; margin-top: 5px;")
        
        ok = self.scanner.begin_capture()
        if not ok:
            self.prompt_label.setText("Failed to begin capture. Check driver.")
            self.prompt_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #f38ba8;")
            return

        self.timer.start(40)

    def poll_scanner(self):
        success, img_bytes, w, h, is_final, finger_state = self.scanner.block_get_image(ignore_preview=False)
        
        if success and img_bytes and w > 0 and h > 0:
            self.current_image_bytes = img_bytes
            self.current_w = w
            self.current_h = h

            # Render image
            img = QImage(img_bytes, w, h, w, QImage.Format_Grayscale8)
            pixmap = QPixmap.fromImage(img)
            scaled = pixmap.scaled(self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.preview_label.setPixmap(scaled)

            # Finger detection state
            # state 0: OK/Present, state 2: Moving/present, state 3: Not present
            if finger_state in (0, 2):
                if not self.is_captured:
                    self.prompt_label.setText("🔍 Finger Detected! Hold still...")
                    self.prompt_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #f9e2af;")
            else:
                if not self.is_captured:
                    self.prompt_label.setText("👉 Place your finger firmly on the scanner platen")
                    self.prompt_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #89b4fa;")

            # On Final Capture
            if is_final and not self.is_captured:
                self.handle_final_capture()

    def handle_final_capture(self):
        self.is_captured = True
        self.timer.stop()
        self.save_btn.setEnabled(True)

        if winsound:
            try:
                winsound.Beep(1500, 180)
            except Exception:
                pass

        self.preview_label.setStyleSheet("""
            background-color: #11111b;
            border: 3px solid #a6e3a1;
            border-radius: 10px;
        """)
        self.prompt_label.setText(" Capture Complete! Image captured successfully.")
        self.prompt_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #a6e3a1; margin-top: 5px;")

        # Extract minutiae keypoints to show quality
        try:
            desc = self.matcher.extract_descriptors(self.current_image_bytes, self.current_w, self.current_h)
            kp_count = len(desc) if desc is not None else 0
            quality = "Excellent" if kp_count > 150 else ("Good" if kp_count > 80 else "Fair")
            self.metrics_label.setText(
                f"Resolution: 500 DPI | Size: {self.current_w}x{self.current_h} px | Keypoints: {kp_count} ({quality} Quality)"
            )
        except Exception:
            self.metrics_label.setText(f"Resolution: 500 DPI | Size: {self.current_w}x{self.current_h} px")

        # Auto-save a test copy into captures folder
        self.auto_save()

    def on_force_capture(self):
        if self.scanner and not self.is_captured:
            self.scanner.take_result_image_manually()

    def on_reset_scan(self):
        self.scanner.cancel_capture()
        self.start_capture()

    def auto_save(self):
        if not self.current_image_bytes:
            return
        os.makedirs("captures", exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join("captures", f"scan_{ts}.png")
        
        arr = np.frombuffer(self.current_image_bytes, dtype=np.uint8).reshape((self.current_h, self.current_w))
        cv2.imwrite(filename, arr)
        print(f"Captured fingerprint saved to: {filename}")

    def on_save_image(self):
        if not self.current_image_bytes:
            return
        os.makedirs("captures", exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join("captures", f"manual_scan_{ts}.png")
        
        arr = np.frombuffer(self.current_image_bytes, dtype=np.uint8).reshape((self.current_h, self.current_w))
        cv2.imwrite(filename, arr)
        QMessageBox.information(self, "Saved", f"Fingerprint saved to:\n{os.path.abspath(filename)}")

    def closeEvent(self, event):
        self.timer.stop()
        self.scanner.close_device()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ColumboScannerTestApp()
    window.show()
    sys.exit(app.exec())
