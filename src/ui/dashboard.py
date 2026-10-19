import csv
from datetime import datetime, timedelta, timezone
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QComboBox, QDateEdit, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFileDialog, QInputDialog)
from PySide6.QtCore import Qt, QDate, Signal
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


class DashboardWidget(QWidget):
    logout_requested = Signal()
    kiosk_requested = Signal()

    def __init__(self, scanner_provider=None, parent=None):
        super().__init__(parent)
        self.scanner_provider = scanner_provider
        self.user = None
        self.employees = {}
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
        layout.addWidget(self.summary)
        filters = QHBoxLayout()
        self.location_filter = QComboBox()
        self.location_filter.addItem('All locations', None)
        for location in sorted({o['location'] for o in OFFICES}):
            self.location_filter.addItem(location, location)
        self.office_filter = QComboBox()
        self.office_filter.addItem('All offices', None)
        for office in OFFICES:
            self.office_filter.addItem(office['name'], office['_id'])
        filters.addWidget(QLabel('Location:'))
        filters.addWidget(self.location_filter)
        filters.addWidget(QLabel('Office:'))
        filters.addWidget(self.office_filter)
        self.refresh_button = QPushButton('Refresh')
        self.refresh_button.clicked.connect(self.refresh)
        filters.addWidget(self.refresh_button)
        layout.addLayout(filters)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        reports = QWidget()
        report_layout = QVBoxLayout(reports)
        dates = QHBoxLayout()
        self.from_date = QDateEdit(QDate.currentDate().addDays(-30))
        self.to_date = QDateEdit(QDate.currentDate())
        for label, field in [('From:', self.from_date), ('To:', self.to_date)]:
            field.setCalendarPopup(True)
            dates.addWidget(QLabel(label))
            dates.addWidget(field)
        self.search = QLineEdit()
        self.search.setPlaceholderText('Search name or employee ID')
        dates.addWidget(self.search)
        export = QPushButton('Export displayed sheet (CSV)')
        export.clicked.connect(self.export_reports)
        dates.addWidget(export)
        report_layout.addLayout(dates)
        self.attendance_table = self.table(['Location', 'Office', 'Name', 'Employee ID', 'Job Title',
                                            'Date', 'Time In (WAT)', 'Time Out (WAT)', 'Minutes', 'Status'])
        report_layout.addWidget(self.attendance_table)
        self.tabs.addTab(reports, 'General attendance sheet')
        employees = QWidget()
        employee_layout = QVBoxLayout(employees)
        actions = QHBoxLayout()
        for label, action in [('+ Add employee', self.open_add_employee), ('Edit employee', self.edit_employee),
                              ('Enroll fingerprint', self.enroll), ('Deactivate employee', self.deactivate)]:
            button = QPushButton(label)
            button.clicked.connect(action)
            actions.addWidget(button)
        employee_layout.addLayout(actions)
        self.emp_table = self.table(['Office', 'Employee ID', 'Name', 'Job Title', 'Status', 'Fingerprint'])
        employee_layout.addWidget(self.emp_table)
        self.tabs.addTab(employees, 'Manage employees')
        self.reset_button = QPushButton('Reset selected office login password')
        self.reset_button.clicked.connect(self.reset_office_password)
        layout.addWidget(self.reset_button)
        self.location_filter.currentIndexChanged.connect(self.refresh)
        self.office_filter.currentIndexChanged.connect(self.refresh)

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
        master = user['role'] == 'main_admin'
        self.title.setText('Master admin — all offices' if master else OFFICE_MAP[user['office_id']]['name'])
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
        self.user = None
        self.employees = {}
        self.emp_table.setRowCount(0)
        self.attendance_table.setRowCount(0)
        self.summary.clear()

    def query(self):
        selected = self.office_filter.currentData()
        location = self.location_filter.currentData()
        ids = [o['_id'] for o in OFFICES if (not selected or o['_id'] == selected)
               and (not location or o['location'] == location)]
        return {'office_id': {'$in': ids}}

    def refresh(self):
        if not self.user or not api.token:
            return
        self.emp_table.setRowCount(0)
        self.attendance_table.setRowCount(0)
        self.summary.clear()
        try:
            if self.from_date.date() > self.to_date.date():
                raise ValueError('The start date must be before the end date.')
            db = ClientDatabase.get_db()
            employees = list(db.employees.find(self.query()))
            self.employees = {str(e['_id']): e for e in employees}
            for employee in sorted(employees, key=lambda e: (e.get('office_id', ''), e.get('full_name', ''))):
                values = [OFFICE_MAP.get(employee.get('office_id'), {}).get('name', 'Unassigned'),
                          employee.get('employee_no'), employee.get('full_name'), employee.get('job_title'),
                          employee.get('status'), 'Enrolled' if employee.get('has_fingerprint') else 'Needs enrollment']
                self.add_row(self.emp_table, values, str(employee['_id']))
            query = dict(self.query(), work_date={'$gte': self.from_date.date().toString('yyyy-MM-dd'),
                                                  '$lte': self.to_date.date().toString('yyyy-MM-dd')})
            records = list(db.attendance_records.find(query))
            search = self.search.text().strip().lower()
            records.sort(key=lambda r: (OFFICE_MAP.get(r.get('office_id'), {}).get('location', ''),
                                       r.get('office_id', ''), r.get('work_date', '')))
            for record in records:
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
            today = datetime.now(LAGOS).strftime('%Y-%m-%d')
            active_ids = {e['_id'] for e in employees if e.get('status') == 'active'}
            present_ids = set(db.attendance_records.distinct('employee_id', dict(self.query(), work_date=today,
                                                                                 clock_in_at={'$ne': None})))
            self.summary.setText(f'Active staff: {len(active_ids)}   |   Checked in today: {len(active_ids & present_ids)}'
                                 f'   |   Not checked in: {len(active_ids - present_ids)}'
                                 f'   |   Displayed records: {self.attendance_table.rowCount()}')
        except Exception as exc:
            self.employees = {}
            self.emp_table.setRowCount(0)
            self.attendance_table.setRowCount(0)
            self.summary.setText('Could not load records. Check connection and refresh.')
            QMessageBox.warning(self, 'Could not refresh', str(exc))

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
        try:
            ClientDatabase.get_db().employees.update_one({'_id': employee['_id']}, {'$set': {'status': 'inactive'}})
            self.refresh()
        except ValueError as exc:
            QMessageBox.warning(self, 'Could not deactivate', str(exc))

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
            QMessageBox.information(self, 'Choose office', 'Select one office in the office filter first.')
            return
        if QMessageBox.question(self, 'Reset office password', 'This will sign out all terminals for this office. Continue?') != QMessageBox.Yes:
            return
        try:
            result = api.call(f'/offices/{office}/reset-password')
            QMessageBox.information(self, 'Deliver privately', f"Username: {result['username']}\nTemporary password: {result['password']}\nShown once. Password change is required at next login.")
        except ValueError as exc:
            QMessageBox.warning(self, 'Reset failed', str(exc))

    def change_password(self):
        password, ok = QInputDialog.getText(self, 'Change password', 'At least 10 characters, letters, numbers and !@#$%&*?', QLineEdit.Password)
        if ok:
            try:
                api.call('/password', {'password': password})
                QMessageBox.information(self, 'Password updated', 'Your password was changed.')
            except ValueError as exc:
                QMessageBox.warning(self, 'Password not changed', str(exc))
