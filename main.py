import sys
import ctypes
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QMessageBox
from PySide6.QtGui import QIcon
from src.utils import get_asset_path, apply_window_icon
from src.client import api
from src.ui.dashboard import DashboardWidget
from src.ui.kiosk import KioskWidget
from src.ui.login import LoginWidget
from src.scanner.provider import KojackVendorProvider


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Randaframes Attendance')
        self.resize(1200, 800)
        apply_window_icon(self)
        self.scanner_provider = KojackVendorProvider()
        self.scanner_provider.initialize()
        self.setObjectName('mainWindow')
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setObjectName('centralStacked')
        self.setCentralWidget(self.stacked_widget)
        self.login_view = LoginWidget()
        self.dashboard_view = DashboardWidget(self.scanner_provider)
        self.kiosk_view = KioskWidget(self.scanner_provider)
        for widget in (self.login_view, self.dashboard_view, self.kiosk_view):
            self.stacked_widget.addWidget(widget)
        self.login_view.login_successful.connect(self.show_dashboard)
        self.login_view.cancel_requested.connect(self.return_to_kiosk)
        self.kiosk_view.login_requested.connect(self.show_login_from_kiosk)
        self.dashboard_view.logout_requested.connect(self.show_login_from_dashboard)
        self.dashboard_view.kiosk_requested.connect(self.show_kiosk)
        self.stacked_widget.setCurrentWidget(self.login_view)
        from src.utils import speak
        speak("Welcome to Randaframes Attendance System.")

    def show_login_from_kiosk(self):
        self.kiosk_view.stop_scanner()
        self.stacked_widget.setCurrentWidget(self.login_view)

    def show_login_from_dashboard(self):
        self.kiosk_view.stop_scanner()
        try:
            api.logout()
        except ValueError:
            pass
        self.dashboard_view.clear_data()
        self.stacked_widget.setCurrentWidget(self.login_view)

    def return_to_kiosk(self):
        if api.token or api.restore_saved_session():
            self.stacked_widget.setCurrentWidget(self.kiosk_view)
            self.kiosk_view.start_scanner()
        else:
            self.stacked_widget.setCurrentWidget(self.kiosk_view)
            self.kiosk_view.update_status("Please click 'Admin Login' to log in with an office account first.")

    def show_dashboard(self, user):
        self.dashboard_view.set_user(user)
        self.stacked_widget.setCurrentWidget(self.dashboard_view)

    def show_kiosk(self):
        try:
            result = api.call('/kiosk')
            api.token = result['token']
            self.dashboard_view.clear_data()
            self.stacked_widget.setCurrentWidget(self.kiosk_view)
        except ValueError as exc:
            QMessageBox.warning(self, 'Terminal', str(exc))

    def closeEvent(self, event):
        self.kiosk_view.stop_scanner()
        self.scanner_provider.close()
        event.accept()


def main():
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('randaframes.attendance.system.v2')
    except AttributeError:
        pass
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(get_asset_path('icon.ico')))
    from src.ui.theme import ThemeManager
    ThemeManager.instance().apply(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
