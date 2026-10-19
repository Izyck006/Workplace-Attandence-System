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
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        self.login_view = LoginWidget()
        self.dashboard_view = DashboardWidget(self.scanner_provider)
        self.kiosk_view = KioskWidget(self.scanner_provider)
        for widget in (self.login_view, self.dashboard_view, self.kiosk_view):
            self.stacked_widget.addWidget(widget)
        self.login_view.login_successful.connect(self.show_dashboard)
        self.kiosk_view.login_requested.connect(self.show_login)
        self.dashboard_view.logout_requested.connect(self.show_login)
        self.dashboard_view.kiosk_requested.connect(self.show_kiosk)
        self.stacked_widget.setCurrentWidget(self.login_view)

    def show_login(self):
        self.kiosk_view.stop_scanner()
        try:
            api.logout()
        except ValueError:
            pass
        self.dashboard_view.clear_data()
        self.stacked_widget.setCurrentWidget(self.login_view)

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
        try:
            api.logout()
        except ValueError:
            pass
        event.accept()


def main():
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('randaframes.attendance.system.v2')
    except AttributeError:
        pass
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(get_asset_path('icon.ico')))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
