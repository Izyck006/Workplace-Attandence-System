from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QFileDialog, QComboBox
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QPixmap
import datetime
from src.data.repositories import EmployeeRepository


class EmployeeSaveWorker(QThread):
    save_success = Signal(str, bool)
    save_failed = Signal(str)

    def __init__(self, data, existing_id, department_name):
        super().__init__()
        self.data = data
        self.existing_id = existing_id
        self.department_name = department_name

    def run(self):
        try:
            from src.client import ClientDatabase as DatabaseManager
            from src.data.repositories import EmployeeRepository
            db = DatabaseManager.get_db()
            emp_repo = EmployeeRepository()

            dept_doc = db.departments.find_one({"name": self.department_name})
            if not dept_doc:
                res = db.departments.insert_one({
                    "name": self.department_name,
                    "is_active": True,
                    "created_at": datetime.datetime.now()
                })
                dept_id = res.inserted_id
            else:
                dept_id = dept_doc["_id"]

            self.data["department_id"] = dept_id

            if self.existing_id:
                emp_repo.collection.update_one({"_id": self.existing_id}, {"$set": self.data})
                self.save_success.emit(str(self.existing_id), True)
            else:
                self.data["created_at"] = datetime.datetime.now()
                self.data["has_fingerprint"] = False
                res = emp_repo.collection.insert_one(self.data)
                self.save_success.emit(str(res.inserted_id), False)
        except Exception as exc:
            self.save_failed.emit(str(exc))


class AddEmployeeDialog(QDialog):
    def __init__(self, parent=None, employee_doc=None):
        super().__init__(parent)
        self.employee_doc = employee_doc
        self.setWindowTitle("Edit Employee" if employee_doc else "Add New Employee")
        self.setMinimumSize(500, 650)
        self.emp_repo = EmployeeRepository()
        self.photo_bytes = None
        self.save_worker = None
        self.setup_ui()
        if self.employee_doc:
            self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        
        photo_layout = QHBoxLayout()
        self.photo_label = QLabel("No Photo")
        self.photo_label.setFixedSize(120, 120)
        self.photo_label.setStyleSheet("border: 1px solid #ccc; background-color: #eee;")
        self.photo_label.setAlignment(Qt.AlignCenter)
        
        photo_btn_layout = QVBoxLayout()
        self.upload_btn = QPushButton("Upload Photo")
        self.upload_btn.clicked.connect(self.upload_photo)
        photo_btn_layout.addWidget(self.upload_btn)
        photo_btn_layout.addStretch()
        
        photo_layout.addWidget(self.photo_label)
        photo_layout.addLayout(photo_btn_layout)
        photo_layout.addStretch()
        layout.addLayout(photo_layout)

        
        self.first_name_input = QLineEdit()
        layout.addWidget(QLabel("First Name:"))
        layout.addWidget(self.first_name_input)
        
        self.last_name_input = QLineEdit()
        layout.addWidget(QLabel("Last Name:"))
        layout.addWidget(self.last_name_input)
        
        self.emp_id_input = QLineEdit()
        layout.addWidget(QLabel("Employee ID (Leave blank to auto-generate):"))
        layout.addWidget(self.emp_id_input)
        
        self.job_title_input = QLineEdit()
        layout.addWidget(QLabel("Job Title:"))
        layout.addWidget(self.job_title_input)
        
        self.dept_input = QComboBox()
        self.dept_input.setEditable(True)
        self.dept_input.addItems(["Engineering", "HR", "Groups", "Logistics", "Institute", "IT"])
        layout.addWidget(QLabel("Department:"))
        layout.addWidget(self.dept_input)
        from src.client import api, ClientDatabase
        from src.offices import OFFICES, sync_offices
        try:
            db_offices = list(ClientDatabase.get_db().offices.find({}))
            sync_offices(db_offices)
        except Exception:
            pass
        self.office_input = QComboBox()
        for office in OFFICES:
            if api.user and (api.user.get('role') == 'main_admin' or office['_id'] == api.user.get('office_id')):
                self.office_input.addItem(office['name'], office['_id'])
        if self.employee_doc:
            self.office_input.setCurrentIndex(self.office_input.findData(self.employee_doc.get('office_id')))
            self.office_input.setEnabled(False)
        layout.addWidget(QLabel('Office:'))
        layout.addWidget(self.office_input)

        
        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn = QPushButton("Save Employee")
        self.save_btn.clicked.connect(self.on_save)
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        
        layout.addStretch()
        layout.addLayout(btn_layout)

    def load_data(self):
        self.first_name_input.setText(self.employee_doc.get("first_name", ""))
        self.last_name_input.setText(self.employee_doc.get("last_name", ""))
        self.emp_id_input.setText(str(self.employee_doc.get("employee_id", self.employee_doc.get("employee_no", ""))))
        self.job_title_input.setText(self.employee_doc.get("job_title", ""))
        
        dept_name = "Engineering"
        dept_id = self.employee_doc.get("department_id")
        if dept_id:
            from src.client import ClientDatabase as DatabaseManager
            db = DatabaseManager.get_db()
            dept_doc = db.departments.find_one({"_id": dept_id})
            if dept_doc:
                dept_name = dept_doc.get("name", "Engineering")
        self.dept_input.setCurrentText(dept_name)
        
        if self.employee_doc.get("photo_bytes"):
            self.photo_bytes = self.employee_doc["photo_bytes"]
            pm = QPixmap()
            pm.loadFromData(self.photo_bytes)
            self.photo_label.setPixmap(pm.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def upload_photo(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Photo", "", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            with open(file_path, 'rb') as f:
                self.photo_bytes = f.read()
            pm = QPixmap()
            pm.loadFromData(self.photo_bytes)
            self.photo_label.setPixmap(pm.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def on_save(self):
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        job_title = self.job_title_input.text().strip()
        emp_id = self.emp_id_input.text().strip()
        department = self.dept_input.currentText().strip()

        if not first_name or not last_name:
            QMessageBox.warning(self, "Error", "First Name and Last Name are required.")
            return

        if not emp_id:
            import random
            import string
            emp_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        data = {
            "office_id": self.office_input.currentData(),
            "first_name": first_name,
            "last_name": last_name,
            "full_name": f"{first_name} {last_name}",
            "employee_id": emp_id,
            "employee_no": emp_id,
            "job_title": job_title,
            "status": self.employee_doc.get("status", "active") if self.employee_doc else "active",
            "photo_bytes": self.photo_bytes,
            "updated_at": datetime.datetime.now()
        }

        self.save_btn.setEnabled(False)
        self.save_btn.setText("Saving Employee...")
        self.cancel_btn.setEnabled(False)

        existing_id = self.employee_doc["_id"] if self.employee_doc else None
        self.save_worker = EmployeeSaveWorker(data, existing_id, department)
        self.save_worker.save_success.connect(self.on_save_success)
        self.save_worker.save_failed.connect(self.on_save_failed)
        self.save_worker.start()

    def on_save_success(self, new_id, is_edit):
        self.save_btn.setEnabled(True)
        self.save_btn.setText("Save Employee")
        self.cancel_btn.setEnabled(True)
        self.new_employee_id = new_id
        msg = "Employee updated successfully." if is_edit else "Employee added successfully."
        QMessageBox.information(self, "Success", msg)
        self.accept()

    def on_save_failed(self, err_msg):
        self.save_btn.setEnabled(True)
        self.save_btn.setText("Save Employee")
        self.cancel_btn.setEnabled(True)
        QMessageBox.critical(self, "Error", f"Failed to save: {err_msg}")
