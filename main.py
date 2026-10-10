import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from src.data.database import DatabaseManager
from src.data.migrations import MigrationManager
from src.data import initial_schema

def run_migrations():
    print("Running migrations...")
    db = DatabaseManager.get_db()
    manager = MigrationManager(db)
    manager.initialize()
    manager.apply_migration(
        version="001",
        description="Initial schema setup",
        up_func=initial_schema.up
    )
    print("Migrations complete.")

from src.ui.dashboard import DashboardWidget
from src.ui.kiosk import KioskWidget
from src.ui.setup import SetupWidget
from src.ui.login import LoginWidget
from src.scanner.provider import KojackVendorProvider
from PySide6.QtWidgets import QStackedWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Workplace Attendance System")
        self.resize(1000, 700)
        
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        
        self.scanner_provider = KojackVendorProvider()
        self.scanner_provider.initialize()
        
        self.setup_ui()
        self.check_setup()

    def setup_ui(self):
        self.kiosk_view = KioskWidget(self.scanner_provider)
        self.setup_view = SetupWidget()
        self.login_view = LoginWidget()
        self.dashboard_view = DashboardWidget(self.scanner_provider)
        
        self.stacked_widget.addWidget(self.kiosk_view)
        self.stacked_widget.addWidget(self.setup_view)
        self.stacked_widget.addWidget(self.login_view)
        self.stacked_widget.addWidget(self.dashboard_view)
        
        
        self.kiosk_view.login_requested.connect(self.show_login)
        self.login_view.cancel_requested.connect(self.show_kiosk)
        self.login_view.login_successful.connect(self.show_dashboard)
        self.setup_view.setup_complete.connect(lambda: self.show_dashboard(None))
        self.dashboard_view.logout_requested.connect(self.show_kiosk)
        
    def check_setup(self):
        db = DatabaseManager.get_db()
        if db.users.count_documents({}) == 0:
            self.stacked_widget.setCurrentWidget(self.setup_view)
        else:
            self.stacked_widget.setCurrentWidget(self.kiosk_view)
            
    def show_login(self):
        self.stacked_widget.setCurrentWidget(self.login_view)
        
    def show_kiosk(self):
        self.stacked_widget.setCurrentWidget(self.kiosk_view)
        
    def show_dashboard(self, user):
        
        self.stacked_widget.setCurrentWidget(self.dashboard_view)

def main():
    
    try:
        run_migrations()
    except Exception as e:
        print(f"Failed to run migrations: {e}")
        

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    
    exit_code = app.exec()
    DatabaseManager.close()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
