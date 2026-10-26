import os
import time
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QGroupBox, QFormLayout, QLineEdit, QRadioButton, QButtonGroup)
from PySide6.QtCore import Qt, Signal, QTimer, QThread, QRectF
from PySide6.QtGui import QFont, QPixmap, QImage, QPainter, QPainterPath, QColor
from src.utils import get_asset_path, speak
from src.scanner.worker import ScannerWorker


class HeartbeatWorker(QThread):
    status_updated = Signal(bool, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = True

    def stop(self):
        self._running = False

    def run(self):
        from src.client import api
        from src.services.offline_sync import offline_manager

        while self._running:
            try:
                is_online = offline_manager.check_server_online(api, timeout=2.0)
                pending = offline_manager.get_pending_count()

                # If connection resumed and we have queued records, push them immediately
                if is_online and pending > 0 and getattr(api, "token", None):
                    synced = offline_manager.push_offline_records_to_server(api)
                    if synced > 0:
                        pending = offline_manager.get_pending_count()

                self.status_updated.emit(is_online, pending)
            except Exception:
                self.status_updated.emit(False, 0)

            # Sleep in short increments for responsive thread termination
            for _ in range(35):
                if not self._running:
                    break
                time.sleep(0.1)


class ScanWorker(QThread):
    scan_success = Signal(dict)
    scan_error = Signal(str)

    def __init__(self, sample, action):
        super().__init__()
        self.sample = sample
        self.action = action

    def run(self):
        from src.client import api
        from src.services.offline_sync import offline_manager

        # Proactively push any pending offline records (e.g. earlier offline Time In)
        # to the central server so the server has the Time In record before processing /scan!
        if offline_manager.get_pending_count() > 0 and getattr(api, "token", None):
            try:
                offline_manager.push_offline_records_to_server(api)
            except Exception:
                pass

        try:
            result = api.call('/scan', {'samples': [self.sample.tolist()], 'action': self.action})
            self.scan_success.emit(result)
            return
        except Exception as exc:
            error_str = str(exc)

            # If server reported "Must time in first", check if an offline Time In is in local storage
            if "time in first" in error_str.lower():
                if offline_manager.get_pending_count() > 0 and getattr(api, "token", None):
                    try:
                        synced = offline_manager.push_offline_records_to_server(api)
                        if synced > 0:
                            retry_result = api.call('/scan', {'samples': [self.sample.tolist()], 'action': self.action})
                            self.scan_success.emit(retry_result)
                            return
                    except Exception:
                        pass

            is_network_issue = any(term in error_str.lower() for term in (
                "cannot reach", "timeout", "connection", "remote end closed",
                "database unavailable", "network", "failed to establish",
                "nodename nor servname", "name or service not known", "refused",
                "socket", "offline", "unreachable"
            ))
            if is_network_issue:
                try:
                    employee, score = offline_manager.match_offline_fingerprint(self.sample)
                    if employee and score >= 18:
                        offline_result = offline_manager.record_offline_attendance(employee, self.action)
                        self.scan_success.emit(offline_result)
                        return
                    elif employee is None and score == 0:
                        self.scan_error.emit("Offline Mode: Server unreachable and no employee templates cached yet.")
                        return
                    else:
                        self.scan_error.emit("Fingerprint not recognized clearly (offline). Please scan again.")
                        return
                except Exception as off_exc:
                    self.scan_error.emit(f"Offline scan error: {off_exc}")
                    return

            self.scan_error.emit(error_str)


class KioskWidget(QWidget):
    login_requested = Signal()

    def __init__(self, scanner_provider, parent=None):
        super().__init__(parent)
        self.setObjectName("kioskWidget")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.scanner_provider = scanner_provider
        self.worker = None
        self.scan_worker = None
        self.heartbeat_worker = None
        self.is_online = True
        self.pending_count = 0
        self._has_photo = False

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

        self.sync_badge = QLabel("● Checking...")
        self.sync_badge.setCursor(Qt.PointingHandCursor)
        self.sync_badge.mousePressEvent = lambda e: self.trigger_background_sync()

        from src.ui.theme import ThemeToggleButton
        self.theme_btn = ThemeToggleButton()

        admin_btn = QPushButton("Admin Login")
        admin_btn.setFixedSize(140, 38)
        admin_btn.clicked.connect(self.login_requested.emit)

        reconnect = QPushButton("Reconnect scanner")
        reconnect.clicked.connect(self.reconnect_scanner)

        top_layout.addWidget(title)
        top_layout.addStretch()
        top_layout.addWidget(self.sync_badge)
        top_layout.addWidget(self.theme_btn)
        top_layout.addWidget(admin_btn)
        top_layout.addWidget(reconnect)

        main_layout.addLayout(top_layout)

        action_layout = QHBoxLayout()
        action_layout.setSpacing(12)
        action_label = QLabel("Select Action:")
        action_label.setFont(QFont("Arial", 15, QFont.Bold))

        self.action_group = QButtonGroup(self)
        self.action_group.setExclusive(True)

        self.radio_in = QPushButton("Time In")
        self.radio_in.setCheckable(True)
        self.radio_in.setChecked(True)
        self.radio_in.setCursor(Qt.PointingHandCursor)
        self.radio_in.setFixedSize(130, 40)
        self.radio_in.setFont(QFont("Arial", 13, QFont.Bold))

        self.radio_out = QPushButton("Time Out")
        self.radio_out.setCheckable(True)
        self.radio_out.setCursor(Qt.PointingHandCursor)
        self.radio_out.setFixedSize(130, 40)
        self.radio_out.setFont(QFont("Arial", 13, QFont.Bold))

        self.action_group.addButton(self.radio_in)
        self.action_group.addButton(self.radio_out)

        self._update_action_button_styles()
        self._update_badge_ui()
        self.radio_in.toggled.connect(self._update_action_button_styles)
        self.radio_out.toggled.connect(self._update_action_button_styles)
        self.theme_btn.theme_mgr.theme_changed.connect(self.on_theme_changed)

        action_layout.addStretch()
        action_layout.addWidget(action_label)
        action_layout.addWidget(self.radio_in)
        action_layout.addWidget(self.radio_out)
        action_layout.addStretch()

        main_layout.addLayout(action_layout)

        self.status_label = QLabel("Place finger flat on scanner and hold steady (3s)...")
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

        left_group = QGroupBox("Fingerprint Scanner")
        left_layout = QVBoxLayout(left_group)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("background-color: white; border: 1px solid #ccc; border-radius: 8px;")
        self.preview_label.setMinimumSize(400, 400)
        self.preview_label.setScaledContents(False)

        instruction = QLabel("Place finger flat on the scanner platen and hold for 3 seconds.")
        instruction.setAlignment(Qt.AlignCenter)

        left_layout.addWidget(self.preview_label)
        left_layout.addWidget(instruction)

        right_group = QGroupBox("Employee Verification Result")
        right_layout_main = QHBoxLayout(right_group)

        info_layout = QFormLayout()
        info_layout.setVerticalSpacing(20)

        self.name_field = QLineEdit()
        self.name_field.setReadOnly(True)
        self.name_field.setStyleSheet("font-size: 16px; padding: 6px 10px;")

        self.id_field = QLineEdit()
        self.id_field.setReadOnly(True)
        self.id_field.setStyleSheet("font-size: 16px; padding: 6px 10px;")

        self.job_field = QLineEdit()
        self.job_field.setReadOnly(True)
        self.job_field.setStyleSheet("font-size: 16px; padding: 6px 10px;")

        self.action_field = QLineEdit()
        self.action_field.setReadOnly(True)
        self.action_field.setStyleSheet("font-size: 16px; padding: 6px 10px; font-weight: bold;")

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
        self.photo_label.setFixedSize(160, 200)
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setAttribute(Qt.WA_StyledBackground, True)
        self._update_photo_placeholder()

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

    def on_heartbeat_status(self, is_online: bool, pending_count: int):
        self.is_online = is_online
        self.pending_count = pending_count
        self._update_badge_ui()

    def _update_badge_ui(self):
        try:
            import shiboken6
            if not shiboken6.isValid(self) or not hasattr(self, 'sync_badge') or not shiboken6.isValid(self.sync_badge):
                return
        except Exception:
            return

        is_online = getattr(self, 'is_online', True)
        pending = getattr(self, 'pending_count', 0)

        if is_online:
            if pending > 0:
                self.sync_badge.setText(f"● Syncing ({pending} pending)")
                self.sync_badge.setToolTip(f"Central Server: Connected\n{pending} offline scan(s) queued.\nClick to sync now.")
                self.sync_badge.setStyleSheet("""
                    QLabel {
                        background-color: rgba(59, 130, 246, 0.15);
                        color: #3b82f6;
                        border: 1px solid rgba(59, 130, 246, 0.45);
                        font-size: 12px;
                        font-weight: bold;
                        padding: 6px 14px;
                        border-radius: 14px;
                        margin-right: 8px;
                    }
                """)
            else:
                self.sync_badge.setText("● Connected")
                self.sync_badge.setToolTip("Central Server: Online\nAll records synchronized.")
                self.sync_badge.setStyleSheet("""
                    QLabel {
                        background-color: rgba(16, 185, 129, 0.15);
                        color: #10b981;
                        border: 1px solid rgba(16, 185, 129, 0.45);
                        font-size: 12px;
                        font-weight: bold;
                        padding: 6px 14px;
                        border-radius: 14px;
                        margin-right: 8px;
                    }
                """)
        else:
            q_txt = f" ({pending} queued)" if pending > 0 else ""
            self.sync_badge.setText(f"● Offline Mode{q_txt}")
            self.sync_badge.setToolTip(f"Central Server: Unreachable (Offline)\nScans are safely cached locally and will auto-sync upon reconnection.\nClick to test connection.")
            self.sync_badge.setStyleSheet("""
                QLabel {
                    background-color: rgba(245, 158, 11, 0.18);
                    color: #f59e0b;
                    border: 1px solid rgba(245, 158, 11, 0.5);
                    font-size: 12px;
                    font-weight: bold;
                    padding: 6px 14px;
                    border-radius: 14px;
                    margin-right: 8px;
                }
            """)

    def _update_photo_placeholder(self):
        self._has_photo = False
        is_dark = self.theme_btn.theme_mgr.is_dark if hasattr(self, 'theme_btn') else True
        if is_dark:
            self.photo_label.setStyleSheet("""
                QLabel {
                    background-color: #18181b;
                    border: 2px dashed #3f3f46;
                    border-radius: 12px;
                    color: #71717a;
                    font-size: 13px;
                    font-weight: bold;
                }
            """)
        else:
            self.photo_label.setStyleSheet("""
                QLabel {
                    background-color: #f8fafc;
                    border: 2px dashed #cbd5e1;
                    border-radius: 12px;
                    color: #94a3b8;
                    font-size: 13px;
                    font-weight: bold;
                }
            """)
        self.photo_label.setText("No Photo")
        self.photo_label.setPixmap(QPixmap())

    def _set_employee_photo(self, photo_bytes):
        if not photo_bytes:
            self._update_photo_placeholder()
            return
        try:
            raw_pixmap = QPixmap()
            raw_pixmap.loadFromData(photo_bytes)
            if raw_pixmap.isNull():
                self._update_photo_placeholder()
                return

            self._has_photo = True
            target_w = 154
            target_h = 194
            scaled = raw_pixmap.scaled(target_w, target_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)

            rounded = QPixmap(scaled.size())
            rounded.fill(Qt.transparent)

            painter = QPainter(rounded)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            path = QPainterPath()
            path.addRoundedRect(QRectF(0, 0, scaled.width(), scaled.height()), 10, 10)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, scaled)
            painter.end()

            is_dark = self.theme_btn.theme_mgr.is_dark if hasattr(self, 'theme_btn') else True
            border_col = "#3f3f46" if is_dark else "#cbd5e1"
            bg_col = "#18181b" if is_dark else "#f8fafc"

            self.photo_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {bg_col};
                    border: 2px solid {border_col};
                    border-radius: 12px;
                    padding: 2px;
                }}
            """)
            self.photo_label.setText("")
            self.photo_label.setPixmap(rounded)
        except Exception:
            self._update_photo_placeholder()

    def on_theme_changed(self, is_dark: bool):
        self._update_action_button_styles()
        self._update_badge_ui()
        if not getattr(self, '_has_photo', False):
            self._update_photo_placeholder()

    def _update_action_button_styles(self):
        try:
            import shiboken6
            if not shiboken6.isValid(self) or not hasattr(self, 'radio_in') or not shiboken6.isValid(self.radio_in):
                return
        except Exception:
            return

        is_dark = self.theme_btn.theme_mgr.is_dark if hasattr(self, 'theme_btn') else True
        selected_style = """
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                border: 2px solid #3b82f6;
                border-radius: 8px;
                padding: 6px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """
        if is_dark:
            unselected_style = """
                QPushButton {
                    background-color: #18181b;
                    color: #a1a1aa;
                    border: 1px solid #3f3f46;
                    border-radius: 8px;
                    padding: 6px 16px;
                    font-weight: 500;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #27272a;
                    color: #ffffff;
                    border-color: #52525b;
                }
            """
        else:
            unselected_style = """
                QPushButton {
                    background-color: #ffffff;
                    color: #4b5563;
                    border: 1px solid #cbd5e1;
                    border-radius: 8px;
                    padding: 6px 16px;
                    font-weight: 500;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #f1f5f9;
                    color: #111827;
                    border-color: #94a3b8;
                }
            """

        if self.radio_in.isChecked():
            self.radio_in.setStyleSheet(selected_style)
            self.radio_out.setStyleSheet(unselected_style)
        else:
            self.radio_in.setStyleSheet(unselected_style)
            self.radio_out.setStyleSheet(selected_style)

    def trigger_background_sync(self):
        try:
            from src.client import api
            from src.services.offline_sync import offline_manager
            is_online = offline_manager.check_server_online(api, timeout=2.0)
            self.is_online = is_online
            pending = offline_manager.get_pending_count()
            if is_online and pending > 0 and getattr(api, "token", None):
                offline_manager.push_offline_records_to_server(api)
                pending = offline_manager.get_pending_count()
            self.pending_count = pending
            self._update_badge_ui()
        except Exception:
            pass

    def start_heartbeat(self):
        if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
            return
        if self.heartbeat_worker is None or not self.heartbeat_worker.isRunning():
            self.heartbeat_worker = HeartbeatWorker(self)
            self.heartbeat_worker.status_updated.connect(self.on_heartbeat_status)
            self.heartbeat_worker.start()

    def stop_heartbeat(self):
        if hasattr(self, 'heartbeat_worker') and self.heartbeat_worker:
            try:
                if self.heartbeat_worker.isRunning():
                    self.heartbeat_worker.stop()
                    self.heartbeat_worker.wait(1000)
            except Exception:
                pass
            self.heartbeat_worker = None

    def showEvent(self, event):
        super().showEvent(event)
        speak("Welcome to Randaframes Attendance System.")
        self.start_scanner()
        self.start_heartbeat()
        try:
            from src.client import api
            from src.services.offline_sync import offline_manager
            if getattr(api, "token", None):
                QTimer.singleShot(1500, lambda: offline_manager.sync_templates_from_server(api))
                QTimer.singleShot(2500, self.trigger_background_sync)
        except Exception:
            pass

    def hideEvent(self, event):
        super().hideEvent(event)
        self.stop_scanner()
        self.stop_heartbeat()

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

    def cleanup(self):
        self.stop_scanner()
        self.stop_heartbeat()

    def closeEvent(self, event):
        self.cleanup()
        super().closeEvent(event)

    def update_status(self, msg):
        self.status_label.setStyleSheet("color: #0078D7; margin: 10px 0;")
        self.status_label.setText(msg)

    def update_error(self, msg):
        self.status_label.setStyleSheet("color: red; margin: 10px 0; font-weight: bold;")
        self.status_label.setText(f"Scanner Error: {msg}")
        self.name_field.clear()
        self.id_field.clear()
        self.job_field.clear()
        self.action_field.clear()
        self._update_photo_placeholder()

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
        self._update_photo_placeholder()
        self.status_label.setStyleSheet("color: #0078D7; margin: 10px 0;")
        self.status_label.setText("Place finger flat on scanner and hold steady (3s)...")
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
        is_offline = result.get('offline', False)

        self.name_field.setText(f"{first_name} {last_name}".strip())
        self.id_field.setText(employee.get('employee_no', ''))
        self.job_field.setText(employee.get('job_title', ''))
        self.action_field.setText(action)

        if is_offline:
            self.status_label.setText(f"{action} (Saved Offline - Queued)")
            self.status_label.setStyleSheet('color: #d97706; font-size: 18px; font-weight: bold;')
            self.trigger_background_sync()
        else:
            self.status_label.setText(f"{action} (Confirmed)")
            self.status_label.setStyleSheet('color: green; font-size: 20px;')

        if employee.get('photo_bytes'):
            self._set_employee_photo(employee['photo_bytes'])
        else:
            self._update_photo_placeholder()

        if is_offline:
            if 'Time In' in action:
                speak(f"Welcome, {first_name}. Recorded offline.")
            elif 'Time Out' in action:
                speak(f"Goodbye, {first_name}. Recorded offline.")
            else:
                speak(f"Recorded offline for {first_name}.")
        elif 'Time In' in action:
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
