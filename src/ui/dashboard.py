from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QFrame, QTabWidget, QComboBox, QDateEdit, QLineEdit
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QFont, QColor
from src.data.repositories import EmployeeRepository
from src.data.database import DatabaseManager

class DashboardWidget(QWidget):
    logout_requested = Signal()

    def __init__(self, scanner_provider=None, parent=None):
        super().__init__(parent)
        self.scanner_provider = scanner_provider
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        
        header_layout = QHBoxLayout()
        title_label = QLabel("Admin Console")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        
        logout_btn = QPushButton("Log Out")
        logout_btn.setFixedWidth(100)
        logout_btn.clicked.connect(self.logout_requested.emit)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(logout_btn)
        main_layout.addLayout(header_layout)

        
        self.tabs = QTabWidget()
        
        self.tab_overview = QWidget()
        self.tab_attendance = QWidget()
        self.tab_employees = QWidget()
        
        self.tabs.addTab(self.tab_overview, "Overview")
        self.tabs.addTab(self.tab_attendance, "Reports")
        self.tabs.addTab(self.tab_employees, "Manage Employees")
        
        self.setup_overview_tab()
        self.setup_attendance_tab()
        self.setup_employees_tab()
        
        main_layout.addWidget(self.tabs)

    def setup_overview_tab(self):
        layout = QVBoxLayout(self.tab_overview)
        layout.setSpacing(20)
        
        
        kpi_layout = QHBoxLayout()
        emp_repo = EmployeeRepository()
        try:
            total_employees = len(emp_repo.get_all())
        except Exception:
            total_employees = 0

        kpi_layout.addWidget(self.create_kpi_card("Total Employees", str(total_employees), "#e3f2fd"))
        kpi_layout.addWidget(self.create_kpi_card("Present Today", "0", "#e8f5e9"))
        kpi_layout.addWidget(self.create_kpi_card("Absent / Leave", "0", "#ffebee"))
        
        layout.addLayout(kpi_layout)
        
        
        backup_layout = QHBoxLayout()
        backup_btn = QPushButton("Run Daily Backup to SQLite")
        backup_btn.setFixedWidth(200)
        backup_btn.clicked.connect(self.run_backup)
        
        backup_layout.addStretch()
        backup_layout.addWidget(backup_btn)
        
        layout.addLayout(backup_layout)
        layout.addStretch()

    def run_backup(self):
        from src.services.backup import BackupService
        from PySide6.QtWidgets import QMessageBox
        try:
            service = BackupService()
            file_path, count = service.backup_daily_attendance()
            QMessageBox.information(self, "Backup Successful", f"Backed up {count} records to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Backup Failed", str(e))

    def setup_attendance_tab(self):
        layout = QVBoxLayout(self.tab_attendance)
        
        
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("From:"))
        self.from_date = QDateEdit()
        self.from_date.setCalendarPopup(True)
        self.from_date.setDate(QDate.currentDate().addDays(-30)) 
        filter_layout.addWidget(self.from_date)
        
        filter_layout.addWidget(QLabel("To:"))
        self.to_date = QDateEdit()
        self.to_date.setCalendarPopup(True)
        self.to_date.setDate(QDate.currentDate())
        filter_layout.addWidget(self.to_date)
        
        view_reports_btn = QPushButton("View Reports")
        view_reports_btn.setStyleSheet("background-color: #3b82f6; color: white;")
        view_reports_btn.clicked.connect(self.load_attendance)
        filter_layout.addWidget(view_reports_btn)
        
        filter_layout.addStretch()
        
        filter_layout.addWidget(QLabel("Search:"))
        self.search_emp = QLineEdit()
        self.search_emp.setPlaceholderText("Name, ID, or Dept...")
        self.search_emp.textChanged.connect(self.load_attendance)
        filter_layout.addWidget(self.search_emp)
        
        export_btn = QPushButton("Export CSV/Excel")
        export_btn.clicked.connect(self.export_reports)
        filter_layout.addWidget(export_btn)
        
        layout.addLayout(filter_layout)
        
        
        self.attendance_table = QTableWidget(0, 7) 
        self.attendance_table.setHorizontalHeaderLabels(["Name", "Employee ID.", "Job Title", "Date", "Time-In", "Time-Out", "Status"])
        
        
        self.attendance_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.attendance_table.verticalHeader().setVisible(True) 
        self.attendance_table.setShowGrid(True)
        self.attendance_table.setAlternatingRowColors(False)
        
        excel_style = """
            QTableWidget {
                background-color: #ffffff;
                color: #000000;
                gridline-color: #d0d0d0;
                font-family: 'Segoe UI', Calibri, Arial;
                font-size: 11pt;
                border: 1px solid #d0d0d0;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #000000;
            }
            QHeaderView::section {
                background-color: #f3f3f3;
                color: #000000;
                padding: 4px;
                border: 1px solid #d0d0d0;
                font-family: 'Segoe UI', Calibri, Arial;
                font-size: 11pt;
            }
            QTableCornerButton::section {
                background-color: #f3f3f3;
                border: 1px solid #d0d0d0;
            }
        """
        self.attendance_table.setStyleSheet(excel_style)
        
        layout.addWidget(self.attendance_table)
        self.load_attendance()

    def setup_employees_tab(self):
        layout = QVBoxLayout(self.tab_employees)
        
        action_layout = QHBoxLayout()
        self.add_emp_btn = QPushButton("+ Add Employee")
        self.add_emp_btn.clicked.connect(self.open_add_employee)
        
        self.edit_emp_btn = QPushButton("Edit Employee")
        self.edit_emp_btn.clicked.connect(self.edit_employee)
        
        self.enroll_btn = QPushButton("Enroll Fingerprint")
        self.enroll_btn.clicked.connect(lambda: self.open_enroll_fingerprint(None))
        
        self.delete_emp_btn = QPushButton("Delete Employee")
        self.delete_emp_btn.setStyleSheet("background-color: #ff4c4c; color: white;")
        self.delete_emp_btn.clicked.connect(self.delete_employee)
        
        action_layout.addWidget(self.add_emp_btn)
        action_layout.addWidget(self.edit_emp_btn)
        action_layout.addWidget(self.enroll_btn)
        action_layout.addWidget(self.delete_emp_btn)
        action_layout.addStretch()
        
        layout.addLayout(action_layout)
        
        self.emp_table = QTableWidget(0, 4)
        self.emp_table.setHorizontalHeaderLabels(["Emp ID", "First Name", "Last Name", "Job Title"])
        self.emp_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.emp_table.verticalHeader().setVisible(True)
        self.emp_table.setShowGrid(True)
        self.emp_table.setAlternatingRowColors(False)
        self.emp_table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                color: #000000;
                gridline-color: #d0d0d0;
                font-family: 'Segoe UI', Calibri, Arial;
                font-size: 11pt;
                border: 1px solid #d0d0d0;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #000000;
            }
            QHeaderView::section {
                background-color: #f3f3f3;
                color: #000000;
                padding: 4px;
                border: 1px solid #d0d0d0;
                font-family: 'Segoe UI', Calibri, Arial;
                font-size: 11pt;
            }
            QTableCornerButton::section {
                background-color: #f3f3f3;
                border: 1px solid #d0d0d0;
            }
        """)
        self.emp_table.setSelectionBehavior(QTableWidget.SelectRows) 
        self.emp_table.setSelectionMode(QTableWidget.SingleSelection)
        
        layout.addWidget(self.emp_table)
        self.load_employees()

    def load_attendance(self):
        self.attendance_table.setRowCount(0)
        db = DatabaseManager.get_db()
        try:
            from_str = self.from_date.date().toString("yyyy-MM-dd")
            to_str = self.to_date.date().toString("yyyy-MM-dd")
            query = {"work_date": {"$gte": from_str, "$lte": to_str}}
            
            records = list(db.attendance_records.find(query).sort("work_date", -1))
            search_text = self.search_emp.text().lower()
            
            row_idx = 0
            for rec in records:
                emp = db.employees.find_one({"_id": rec.get("employee_id")})
                emp_name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}" if emp else "Unknown"
                
                emp_id_str = str(emp.get("employee_id", "")) if emp else ""
                job_title = emp.get("job_title", "N/A") if emp else "N/A"
                
                
                if search_text and search_text not in emp_name.lower() and search_text not in emp_id_str.lower() and search_text not in job_title.lower():
                    continue
                
                
                clock_in = rec.get("clock_in_at")
                clock_in_str = clock_in.strftime("%I:%M %p").lower() if clock_in else "--:--"
                
                clock_out = rec.get("clock_out_at")
                clock_out_str = clock_out.strftime("%I:%M %p").lower() if clock_out else "--:--"
                
                status = rec.get("status", "Present")
                
                self.attendance_table.insertRow(row_idx)
                self.attendance_table.setItem(row_idx, 0, QTableWidgetItem(emp_name))
                self.attendance_table.setItem(row_idx, 1, QTableWidgetItem(emp_id_str))
                self.attendance_table.setItem(row_idx, 2, QTableWidgetItem(job_title))
                self.attendance_table.setItem(row_idx, 3, QTableWidgetItem(rec.get("work_date", "")))
                self.attendance_table.setItem(row_idx, 4, QTableWidgetItem(clock_in_str))
                self.attendance_table.setItem(row_idx, 5, QTableWidgetItem(clock_out_str))
                self.attendance_table.setItem(row_idx, 6, QTableWidgetItem(status))
                
                row_idx += 1
        except Exception as e:
            print(f"Error loading attendance: {e}")
            
    def export_reports(self):
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        import csv
        
        path, _ = QFileDialog.getSaveFileName(self, "Save Reports", "Attendance_Report.csv", "CSV Files (*.csv)")
        if not path: return
        
        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                headers = []
                for i in range(self.attendance_table.columnCount()):
                    headers.append(self.attendance_table.horizontalHeaderItem(i).text())
                writer.writerow(headers)
                
                for row in range(self.attendance_table.rowCount()):
                    row_data = []
                    for col in range(self.attendance_table.columnCount()):
                        item = self.attendance_table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            
            QMessageBox.information(self, "Success", f"Reports successfully exported to {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export: {str(e)}")

    def load_employees(self):
        self.emp_table.setRowCount(0)
        emp_repo = EmployeeRepository()
        db = DatabaseManager.get_db()
        try:
            employees = emp_repo.get_all()
            for row_idx, emp in enumerate(employees):
                self.emp_table.insertRow(row_idx)
                
                
                item_id = QTableWidgetItem(str(emp.get("employee_id", "")))
                item_id.setData(Qt.UserRole, str(emp["_id"])) 
                
                self.emp_table.setItem(row_idx, 0, item_id)
                self.emp_table.setItem(row_idx, 1, QTableWidgetItem(emp.get("first_name", "")))
                self.emp_table.setItem(row_idx, 2, QTableWidgetItem(emp.get("last_name", "")))
                self.emp_table.setItem(row_idx, 3, QTableWidgetItem(emp.get("job_title", "")))
        except Exception as e:
            print(f"Error loading employees: {e}")

    def open_add_employee(self):
        from src.ui.add_employee import AddEmployeeDialog
        dialog = AddEmployeeDialog(self)
        if dialog.exec():
            self.load_employees()
            
            
            if hasattr(dialog, 'new_employee_id') and dialog.new_employee_id:
                from PySide6.QtWidgets import QMessageBox
                reply = QMessageBox.question(
                    self, 'Enroll Fingerprint', 
                    "Employee added! Do you want to enroll their fingerprint right now?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
                )
                if reply == QMessageBox.Yes:
                    self.open_enroll_fingerprint(dialog.new_employee_id)
                    
    def edit_employee(self):
        from PySide6.QtWidgets import QMessageBox
        from src.ui.add_employee import AddEmployeeDialog
        from src.data.database import DatabaseManager
        from bson import ObjectId
        
        selected_items = self.emp_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Select Employee", "Please select an employee to edit.")
            return
            
        row = selected_items[0].row()
        emp_id_str = self.emp_table.item(row, 0).data(Qt.UserRole)
        
        db = DatabaseManager.get_db()
        emp = db.employees.find_one({"_id": ObjectId(emp_id_str)})
        if emp:
            dialog = AddEmployeeDialog(self, emp)
            if dialog.exec():
                self.load_employees()
                    
    def open_enroll_fingerprint(self, employee_id=None):
        from PySide6.QtWidgets import QMessageBox
        
        
        if not employee_id:
            selected_items = self.emp_table.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "Select Employee", "Please select an employee from the table first.")
                return
            row = selected_items[0].row()
            employee_id = self.emp_table.item(row, 0).data(Qt.UserRole)
            
        from src.ui.enrollment import EnrollFingerprintDialog
        dialog = EnrollFingerprintDialog(employee_id, self.scanner_provider, self)
        dialog.exec()
        
    def delete_employee(self):
        from PySide6.QtWidgets import QMessageBox
        selected_items = self.emp_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Select Employee", "Please select an employee to delete.")
            return
            
        row = selected_items[0].row()
        emp_id_str = self.emp_table.item(row, 0).data(Qt.UserRole)
        emp_name = self.emp_table.item(row, 1).text()
        
        reply = QMessageBox.question(
            self, "Confirm Delete", 
            f"Are you sure you want to permanently delete {emp_name} and all of their attendance records? This cannot be undone.", 
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            from bson import ObjectId
            db = DatabaseManager.get_db()
            try:
                obj_id = ObjectId(emp_id_str)
                db.employees.delete_one({"_id": obj_id})
                db.attendance_records.delete_many({"employee_id": obj_id})
                
                
                db.users.delete_one({"employee_id": obj_id})
                
                QMessageBox.information(self, "Deleted", f"Employee {emp_name} deleted successfully.")
                self.load_employees()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete: {e}")
            
    def create_kpi_card(self, title, value, color_hex):
        frame = QFrame()
        frame.setStyleSheet(f"QFrame {  background-color: {color_hex}; border-radius: 8px; border: 1px solid #ccc; } ")
        layout = QVBoxLayout(frame)
        
        t_label = QLabel(title)
        t_label.setAlignment(Qt.AlignCenter)
        t_label.setFont(QFont("Arial", 11))
        t_label.setStyleSheet("color: #555;")
        
        v_label = QLabel(value)
        v_label.setAlignment(Qt.AlignCenter)
        v_label.setFont(QFont("Arial", 24, QFont.Bold))
        v_label.setStyleSheet("color: #222;")
        
        layout.addWidget(t_label)
        layout.addWidget(v_label)
        return frame
