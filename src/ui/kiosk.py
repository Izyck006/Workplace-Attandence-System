import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox, QFormLayout, QLineEdit, QRadioButton, QButtonGroup
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QPixmap
from src.utils import get_asset_path
from src.scanner.worker import ScannerWorker

class KioskWidget(QWidget):
    login_requested = Signal()

    def __init__(self, scanner_provider, parent=None):
        super().__init__(parent)
        self.scanner_provider = scanner_provider
        self.worker = None
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
        
        admin_btn = QPushButton("Admin / Manager Login")
        admin_btn.setFixedSize(200, 40)
        admin_btn.clicked.connect(self.login_requested.emit)
        
        top_layout.addWidget(title)
        top_layout.addStretch()
        top_layout.addWidget(admin_btn)
        
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
        
        instruction = QLabel("Please give fingerprint sample.")
        instruction.setAlignment(Qt.AlignCenter)
        
        left_layout.addWidget(self.preview_label)
        left_layout.addWidget(instruction)
        
        
        right_group = QGroupBox("Search Employee / Verification")
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
        self.start_scanner()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.stop_scanner()

    def start_scanner(self):
        if self.worker is None or not self.worker.isRunning():
            
            self.worker = ScannerWorker(self.scanner_provider.scanner, image_type=3)
            self.worker.scan_status.connect(self.update_status)
            self.worker.scan_error.connect(self.update_error)
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
            self.countdown_label.setText(f"Please scan again in ... {self.countdown_seconds}")
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
        self.update_status("Fingerprint captured! Extracting minutiae...")
        
        if template_data.get("status") == "success":
            image_bytes = template_data.get("image")
            width = template_data.get("width")
            height = template_data.get("height")
            
            from src.services.fingerprint import FingerprintMatcher
            matcher = FingerprintMatcher()
            probe_descriptors = matcher.extract_descriptors(image_bytes, width, height)
            
            if probe_descriptors is None:
                self.update_error("Failed to read fingerprint. Try again.")
                self.stop_scanner()
                QTimer.singleShot(500, lambda: self.start_scanner())
                return
                
            self.update_status("Searching database...")
            
            from src.data.database import DatabaseManager
            import pickle
            db = DatabaseManager.get_db()
            
            best_match = None
            best_score = 0
            
            for emp in db.employees.find({"has_fingerprint": True}):
                if "fingerprint_descriptors" in emp:
                    import zlib
                    try:
                        raw_bytes = zlib.decompress(emp["fingerprint_descriptors"])
                    except Exception:
                        raw_bytes = emp["fingerprint_descriptors"]
                    
                    db_desc_data = pickle.loads(raw_bytes)
                    
                    emp_best_score = 0
                    
                    if isinstance(db_desc_data, list):
                        for db_desc in db_desc_data:
                            score = matcher.get_match_score(probe_descriptors, db_desc)
                            if score > emp_best_score:
                                emp_best_score = score
                    else:
                        emp_best_score = matcher.get_match_score(probe_descriptors, db_desc_data)
                    
                    if emp_best_score > best_score:
                        best_score = emp_best_score
                        best_match = emp
                        
            if best_match and best_score >= 5: 
                self.stop_scanner()
                
                import datetime
                now = datetime.datetime.now()
                today_str = now.strftime("%Y-%m-%d")
                
                
                record = db.attendance_records.find_one({
                    "employee_id": best_match["_id"],
                    "work_date": today_str
                })
                
                is_time_in = self.radio_in.isChecked()
                
                action_text = ""
                
                if is_time_in:
                    if record:
                        action_text = "Already Timed In"
                        self.action_field.setStyleSheet("font-size: 16px; padding: 5px; font-weight: bold; color: orange;")
                    else:
                        db.attendance_records.insert_one({
                            "employee_id": best_match["_id"],
                            "work_date": today_str,
                            "clock_in_at": now,
                            "clock_out_at": None,
                            "status": "present",
                            "day_type": "working",
                            "source": "scanner",
                            "is_edited": False,
                            "created_at": now,
                            "updated_at": now
                        })
                        action_text = "Time In Recorded"
                        self.action_field.setStyleSheet("font-size: 16px; padding: 5px; font-weight: bold; color: green;")
                else:
                    if record:
                        if not record.get("clock_out_at"):
                            db.attendance_records.update_one(
                                {"_id": record["_id"]},
                                {"$set": {
                                    "clock_out_at": now,
                                    "updated_at": now
                                }}
                            )
                            action_text = "Time Out Recorded"
                            self.action_field.setStyleSheet("font-size: 16px; padding: 5px; font-weight: bold; color: blue;")
                        else:
                            action_text = "Already Timed Out"
                            self.action_field.setStyleSheet("font-size: 16px; padding: 5px; font-weight: bold; color: orange;")
                    else:
                        action_text = "Error: Must Time In First!"
                        self.action_field.setStyleSheet("font-size: 16px; padding: 5px; font-weight: bold; color: red;")
                
                self.status_label.setStyleSheet("color: green; font-size: 20px; font-weight: bold; margin: 10px 0;")
                self.status_label.setText("Verification Successful!")
                
                first_name = best_match.get('first_name', '')
                self.name_field.setText(f"{first_name} {best_match.get('last_name', '')}")
                
                # Play audio greeting using native Windows TTS
                import threading
                import subprocess
                def _speak():
                    try:
                        if "Time In" in action_text:
                            text = f"Welcome, {first_name}."
                        elif "Time Out" in action_text:
                            text = f"Goodbye, {first_name}. Have a great day!"
                        elif "Already" in action_text:
                            text = f"You are already clocked in, {first_name}."
                        else:
                            text = f"Hello, {first_name}."
                            
                        # Escape single quotes in name if any
                        text = text.replace("'", "''")
                        ps_cmd = f"Add-Type -AssemblyName System.Speech; $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; $synth.Speak('{text}')"
                        subprocess.run(["powershell", "-Command", ps_cmd], creationflags=subprocess.CREATE_NO_WINDOW)
                    except Exception as e:
                        print("Audio error:", e)
                threading.Thread(target=_speak, daemon=True).start()
                self.id_field.setText(str(best_match.get('employee_id', '')))
                self.job_field.setText(str(best_match.get('job_title', '')))
                self.action_field.setText(f"{action_text} at {now.strftime('%I:%M %p')}")
                
                if best_match.get("photo_bytes"):
                    pm = QPixmap()
                    pm.loadFromData(best_match["photo_bytes"])
                    self.photo_label.setPixmap(pm.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                else:
                    self.photo_label.setText("No Photo")
                    self.photo_label.setPixmap(QPixmap())
                
                
                self.start_countdown(3, self.reset_and_start)
            else:
                self.status_label.setStyleSheet("color: #E65100; font-size: 18px; font-weight: bold; margin: 10px 0;")
                self.status_label.setText("Fingerprint not recognized. Please try again.")
                self.name_field.clear()
                self.id_field.clear()
                self.job_field.clear()
                self.action_field.clear()
                self.photo_label.setText("No Photo")
                self.photo_label.setPixmap(QPixmap())
                self.stop_scanner()
                
                
                self.start_countdown(3, self.start_scanner)
        else:
            self.update_error("Scan failed. Please try again.")
            self.stop_scanner()
            QTimer.singleShot(500, lambda: self.start_scanner())
