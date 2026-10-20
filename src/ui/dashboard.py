import csv
from datetime import datetime, timedelta, timezone
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QTabWidget, QComboBox, QDateEdit, QLineEdit, QTableWidget,
                             QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog, QInputDialog)
from PySide6.QtCore import Qt, QDate, Signal, QThread, QTimer
from PySide6.QtGui import QGuiApplication
from bson import ObjectId
from src.client import api, ClientDatabase
from src.offices import OFFICES, OFFICE_MAP

LAGOS = timezone(timedelta(hours=1))


def local_time(value):
    if not value:
        return '--:--'
    return value.replace(tzinfo=timezone.utc).astimezone(LAGOS).strftime('%H:%M:%S')


def csv_safe(value):
    text = str(value or '')
    return "'" + text if text.lstrip().startswith(('=', '+', '-', '@', '\t', '\r', '\n')) else text


class DashboardLoader(QThread):
    data_loaded = Signal(list, list, int)
    load_failed = Signal(str)

    def __init__(self, emp_query, att_query):
        super().__init__()
        self.emp_query = emp_query
        self.att_query = att_query

    def run(self):
        try:
            db = ClientDatabase.get_db()
            employees = list(db.employees.find(self.emp_query))
            records = list(db.attendance_records.find(self.att_query))
            today = datetime.now(LAGOS).strftime('%Y-%m-%d')
            present_count = len({r['employee_id'] for r in records if r.get('work_date') == today and r.get('clock_in_at')})
            self.data_loaded.emit(employees, records, present_count)
        except Exception as exc:
            self.load_failed.emit(str(exc))


class PasswordResetWorker(QThread):
    reset_success = Signal(dict, str)
    reset_failed = Signal(str)

    def __init__(self, office_id, office_name):
        super().__init__()
        self.office_id = office_id
        self.office_name = office_name

    def run(self):
        try:
            result = api.call(f'/offices/{self.office_id}/reset-password')
            self.reset_success.emit(result, self.office_name)
        except Exception as exc:
            self.reset_failed.emit(str(exc))


class PasswordChangeWorker(QThread):
    change_success = Signal()
    change_failed = Signal(str)

    def __init__(self, password):
        super().__init__()
        self.password = password

    def run(self):
        try:
            api.call('/password', {'password': self.password})
            self.change_success.emit()
        except Exception as exc:
            self.change_failed.emit(str(exc))


class DeactivateWorker(QThread):
    deactivate_success = Signal()
    deactivate_failed = Signal(str)

    def __init__(self, employee_id):
        super().__init__()
        self.employee_id = employee_id

    def run(self):
        try:
            ClientDatabase.get_db().employees.update_one(
                {'_id': self.employee_id},
                {'$set': {'status': 'inactive'}}
            )
            self.deactivate_success.emit()
        except Exception as exc:
            self.deactivate_failed.emit(str(exc))


class DashboardWidget(QWidget):
    logout_requested = Signal()
    kiosk_requested = Signal()

    def __init__(self, scanner_provider=None, parent=None):
        super().__init__(parent)
        self.scanner_provider = scanner_provider
        self.user = None
        self.employees = {}
        self.loader = None
        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.setInterval(120_000)  # 2 minutes of inactivity auto-lock
        self.inactivity_timer.timeout.connect(self.on_inactivity_timeout)
        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        self.title = QLabel('Randaframes Attendance')
        self.title.setStyleSheet('font-size: 22px; font-weight: bold;')
        header.addWidget(self.title)
        header.addStretch()

        self.kiosk_button = QPushButton('Open attendance terminal')
        self.kiosk_button.clicked.connect(self.kiosk_requested.emit)
        header.addWidget(self.kiosk_button)

        password_button = QPushButton('Change password')
        password_button.clicked.connect(self.change_password)
        header.addWidget(password_button)

        logout = QPushButton('Log out')
        logout.clicked.connect(self.logout_requested.emit)
        header.addWidget(logout)
        layout.addLayout(header)

        self.summary = QLabel('')
        self.summary.setStyleSheet('font-size: 14px; font-weight: bold; color: #4CAF50; padding: 6px 0;')
        layout.addWidget(self.summary)

        filters = QHBoxLayout()
        self.location_filter = QComboBox()
        self.location_filter.addItem('All locations', '')
        for loc in sorted({o['location'] for o in OFFICES}):
            self.location_filter.addItem(loc, loc)
        filters.addWidget(QLabel('Location:'))
        filters.addWidget(self.location_filter)

        self.office_filter = QComboBox()
        self.office_filter.addItem('All offices', '')
        for o in OFFICES:
            self.office_filter.addItem(o['name'], o['_id'])
        filters.addWidget(QLabel('Office:'))
        filters.addWidget(self.office_filter)

        today = QDate.currentDate()
        self.from_date = QDateEdit(today.addDays(-7))
        self.from_date.setCalendarPopup(True)
        self.to_date = QDateEdit(today)
        self.to_date.setCalendarPopup(True)
        filters.addWidget(QLabel('From:'))
        filters.addWidget(self.from_date)
        filters.addWidget(QLabel('To:'))
        filters.addWidget(self.to_date)

        self.search = QLineEdit()
        self.search.setPlaceholderText('Search staff name or ID')
        self.search.textChanged.connect(self.apply_search_filter)
        filters.addWidget(self.search)

        refresh = QPushButton('Refresh')
        refresh.clicked.connect(self.refresh)
        filters.addWidget(refresh)

        export = QPushButton('Export CSV')
        export.clicked.connect(self.export_reports)
        filters.addWidget(export)
        layout.addLayout(filters)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.attendance_table = self.table(['Location', 'Office', 'Name', 'Employee ID',
                                           'Job Title', 'Date', 'Time In', 'Time Out', 'Minutes', 'Status'])
        self.tabs.addTab(self.attendance_table, 'Attendance sheet')

        employees = QWidget()
        employee_layout = QVBoxLayout(employees)
        emp_buttons = QHBoxLayout()

        add_emp = QPushButton('Register staff')
        add_emp.clicked.connect(self.open_add_employee)
        emp_buttons.addWidget(add_emp)

        edit_emp = QPushButton('Edit staff')
        edit_emp.clicked.connect(self.edit_employee)
        emp_buttons.addWidget(edit_emp)

        enroll_btn = QPushButton('Enroll fingerprint')
        enroll_btn.clicked.connect(self.enroll)
        emp_buttons.addWidget(enroll_btn)

        deactivate_btn = QPushButton('Deactivate staff')
        deactivate_btn.clicked.connect(self.deactivate)
        emp_buttons.addWidget(deactivate_btn)

        emp_buttons.addStretch()
        employee_layout.addLayout(emp_buttons)

        self.emp_table = self.table(['Office', 'Employee ID', 'Name', 'Job Title', 'Status', 'Fingerprint'])
        employee_layout.addWidget(self.emp_table)
        self.tabs.addTab(employees, 'Manage employees')

        self.reset_button = QPushButton('Reset selected office login password')
        self.reset_button.clicked.connect(self.reset_office_password)
        layout.addWidget(self.reset_button)

        self.location_filter.currentIndexChanged.connect(self.refresh)
        self.office_filter.currentIndexChanged.connect(self.refresh)
        self.cached_records = []

    @staticmethod
    def table(headers):
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setAlternatingRowColors(True)
        return table

    def set_user(self, user):
        self.user = user
        self.inactivity_timer.start(120_000)
        master = user['role'] == 'main_admin'
        self.title.setText('Master Admin (All Offices)' if master else OFFICE_MAP[user['office_id']]['name'])
        self.kiosk_button.setVisible(not master)
        self.reset_button.setVisible(master)
        self.location_filter.setEnabled(master)
        self.office_filter.setEnabled(master)
        self.location_filter.blockSignals(True)
        self.office_filter.blockSignals(True)
        self.location_filter.setCurrentIndex(0)
        self.office_filter.setCurrentIndex(0 if master else self.office_filter.findData(user['office_id']))
        self.location_filter.blockSignals(False)
        self.office_filter.blockSignals(False)
        self.refresh()

    def clear_data(self):
        self.inactivity_timer.stop()
        self.user = None
        self.employees = {}
        self.cached_records = []
        self.emp_table.setRowCount(0)
        self.attendance_table.setRowCount(0)

    def reset_inactivity_timer(self):
        if self.user:
            self.inactivity_timer.start(120_000)

    def on_inactivity_timeout(self):
        self.inactivity_timer.stop()
        if self.user:
            QMessageBox.warning(self, 'Session Expired', 'Your admin session has expired after 2 minutes of inactivity for security.')
            self.logout_requested.emit()

    def mousePressEvent(self, event):
        self.reset_inactivity_timer()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        self.reset_inactivity_timer()
        super().keyPressEvent(event)

    def query(self):
        if self.user and self.user['role'] == 'office_admin':
            return {'office_id': self.user['office_id']}
        selected = self.office_filter.currentData()
        location = self.location_filter.currentData()
        ids = [o['_id'] for o in OFFICES if (not selected or o['_id'] == selected)
               and (not location or o['location'] == location)]
        return {'office_id': {'$in': ids}}

    def refresh(self, sync=None):
        if not self.user or not api.token:
            return
        if self.from_date.date() > self.to_date.date():
            QMessageBox.warning(self, 'Invalid Date', 'The start date must be before the end date.')
            return

        import os
        is_sync = sync if sync is not None else (os.environ.get('QT_QPA_PLATFORM') == 'offscreen')
        emp_query = self.query()
        att_query = dict(self.query(), work_date={'$gte': self.from_date.date().toString('yyyy-MM-dd'),
                                                  '$lte': self.to_date.date().toString('yyyy-MM-dd')})

        if is_sync:
            try:
                db = ClientDatabase.get_db()
                employees = list(db.employees.find(emp_query))
                records = list(db.attendance_records.find(att_query))
                today = datetime.now(LAGOS).strftime('%Y-%m-%d')
                present_count = len({r['employee_id'] for r in records if r.get('work_date') == today and r.get('clock_in_at')})
                self.on_data_loaded(employees, records, present_count)
            except Exception as exc:
                self.on_load_failed(str(exc))
            return

        self.summary.setText('Loading records from server...')

        if self.loader and self.loader.isRunning():
            self.loader.terminate()
            self.loader.wait()

        self.loader = DashboardLoader(emp_query, att_query)
        self.loader.data_loaded.connect(self.on_data_loaded)
        self.loader.load_failed.connect(self.on_load_failed)
        self.loader.start()

    def on_data_loaded(self, employees, records, present_count):
        self.emp_table.setRowCount(0)
        self.employees = {str(e['_id']): e for e in employees}
        self.cached_records = records

        for employee in sorted(employees, key=lambda e: (e.get('office_id', ''), e.get('full_name', ''))):
            values = [OFFICE_MAP.get(employee.get('office_id'), {}).get('name', 'Unassigned'),
                      employee.get('employee_no'), employee.get('full_name'), employee.get('job_title'),
                      employee.get('status'), 'Enrolled' if employee.get('has_fingerprint') else 'Needs enrollment']
            self.add_row(self.emp_table, values, str(employee['_id']))

        self.populate_attendance_table(records)

        active_ids = {e['_id'] for e in employees if e.get('status') == 'active'}
        self.summary.setText(f'Active staff: {len(active_ids)}   |   Checked in today: {present_count}'
                             f'   |   Not checked in: {max(0, len(active_ids) - present_count)}'
                             f'   |   Displayed records: {self.attendance_table.rowCount()}')

    def populate_attendance_table(self, records):
        self.attendance_table.setRowCount(0)
        search = self.search.text().strip().lower()
        sorted_records = sorted(records, key=lambda r: (OFFICE_MAP.get(r.get('office_id'), {}).get('location', ''),
                                                        r.get('office_id', ''), r.get('work_date', '')))
        for record in sorted_records:
            employee = self.employees.get(str(record['employee_id']), {})
            name = employee.get('full_name', 'Archived employee')
            number = employee.get('employee_no', '')
            if search and search not in (name + ' ' + number).lower():
                continue
            office = OFFICE_MAP.get(record.get('office_id'), {})
            values = [office.get('location', 'Unassigned'), office.get('name', 'Unassigned'), name, number,
                      employee.get('job_title'), record.get('work_date'), local_time(record.get('clock_in_at')),
                      local_time(record.get('clock_out_at')), record.get('minutes_worked'), record.get('status')]
            self.add_row(self.attendance_table, values)

    def apply_search_filter(self):
        if hasattr(self, 'cached_records'):
            self.populate_attendance_table(self.cached_records)

    def on_load_failed(self, error_msg):
        self.employees = {}
        self.emp_table.setRowCount(0)
        self.attendance_table.setRowCount(0)
        self.summary.setText('Could not load records. Check connection and refresh.')
        QMessageBox.warning(self, 'Refresh Failed', error_msg)

    @staticmethod
    def add_row(table, values, record_id=None):
        row = table.rowCount()
        table.insertRow(row)
        for column, value in enumerate(values):
            item = QTableWidgetItem('' if value is None else str(value))
            if column == 0:
                item.setData(Qt.UserRole, record_id)
            table.setItem(row, column, item)

    def selected_employee(self):
        row = self.emp_table.currentRow()
        if row < 0:
            QMessageBox.information(self, 'Select employee', 'Select an employee first.')
            return None
        return self.employees.get(self.emp_table.item(row, 0).data(Qt.UserRole))

    def open_add_employee(self):
        from src.ui.add_employee import AddEmployeeDialog
        dialog = AddEmployeeDialog(self)
        if dialog.exec():
            self.refresh()

    def edit_employee(self):
        from src.ui.add_employee import AddEmployeeDialog
        employee = self.selected_employee()
        if employee and AddEmployeeDialog(self, employee).exec():
            self.refresh()

    def enroll(self):
        employee = self.selected_employee()
        if employee:
            from src.ui.enrollment import EnrollFingerprintDialog
            EnrollFingerprintDialog(str(employee['_id']), self.scanner_provider, self).exec()
            self.refresh()

    def deactivate(self):
        employee = self.selected_employee()
        if not employee:
            return
        if QMessageBox.question(self, 'Deactivate employee', 'Prevent future check-ins? Attendance history will be retained.') != QMessageBox.Yes:
            return

        self.summary.setText('Deactivating employee...')
        self.deact_worker = DeactivateWorker(employee['_id'])
        self.deact_worker.deactivate_success.connect(self.on_deactivate_success)
        self.deact_worker.deactivate_failed.connect(self.on_deactivate_failed)
        self.deact_worker.start()

    def on_deactivate_success(self):
        self.summary.setText('Employee deactivated successfully.')
        self.refresh()

    def on_deactivate_failed(self, error_msg):
        self.summary.setText('Could not deactivate employee.')
        QMessageBox.warning(self, 'Could not deactivate', error_msg)

    def export_reports(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Export sheet', 'Attendance.csv', 'CSV (*.csv)')
        if not path:
            return
        try:
            with open(path, 'w', newline='', encoding='utf-8-sig') as handle:
                writer = csv.writer(handle)
                table = self.attendance_table
                writer.writerow([table.horizontalHeaderItem(c).text() for c in range(table.columnCount())])
                for row in range(table.rowCount()):
                    writer.writerow([csv_safe(table.item(row, col).text()) for col in range(table.columnCount())])
            QMessageBox.information(self, 'Export complete', path)
        except OSError as exc:
            QMessageBox.warning(self, 'Export failed', str(exc))

    def reset_office_password(self):
        office = self.office_filter.currentData()
        if not office:
            items = [OFFICE_MAP[oid]['name'] for oid in OFFICE_MAP]
            item, ok = QInputDialog.getItem(self, 'Reset Office Password', 'Select Office Account:', items, 0, False)
            if not ok or not item:
                return
            office = next(oid for oid in OFFICE_MAP if OFFICE_MAP[oid]['name'] == item)

        office_name = OFFICE_MAP.get(office, {}).get('name', office)
        if QMessageBox.question(self, 'Reset Office Password',
                                f'This will generate a new temporary password for {office_name} and sign out all of its active terminals. Continue?') != QMessageBox.Yes:
            return

        self.summary.setText(f'Resetting password for {office_name}...')
        self.reset_worker = PasswordResetWorker(office, office_name)
        self.reset_worker.reset_success.connect(self.on_reset_success)
        self.reset_worker.reset_failed.connect(self.on_reset_failed)
        self.reset_worker.start()

    def on_reset_success(self, result, office_name):
        self.summary.setText('Password reset successfully.')
        QGuiApplication.clipboard().setText(result['password'])
        QMessageBox.information(
            self,
            'Password Reset Complete',
            f"Office: {office_name}\n"
            f"Username: {result['username']}\n"
            f"New Temporary Password: {result['password']}\n\n"
            f"(Copied to clipboard. Deliver to office admin securely. They will be prompted to change it at next login.)"
        )

    def on_reset_failed(self, error_msg):
        self.summary.setText('Password reset failed.')
        QMessageBox.warning(self, 'Reset Failed', error_msg)

    def change_password(self):
        password, ok = QInputDialog.getText(self, 'Change password', 'At least 10 characters, letters, numbers and !@#$%&*?', QLineEdit.Password)
        if ok and password:
            self.summary.setText('Updating your password...')
            self.pw_worker = PasswordChangeWorker(password)
            self.pw_worker.change_success.connect(self.on_change_password_success)
            self.pw_worker.change_failed.connect(self.on_change_password_failed)
            self.pw_worker.start()

    def on_change_password_success(self):
        self.summary.setText('Password updated successfully.')
        QMessageBox.information(self, 'Password updated', 'Your password was changed.')

    def on_change_password_failed(self, error_msg):
        self.summary.setText('Password change failed.')
        QMessageBox.warning(self, 'Password not changed', error_msg)
