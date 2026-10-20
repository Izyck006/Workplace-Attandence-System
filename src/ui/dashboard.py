import csv
from datetime import datetime, timedelta, timezone
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QTabWidget, QComboBox, QDateEdit, QLineEdit, QTableWidget,
                             QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog, QInputDialog,
                             QDialog, QRadioButton, QButtonGroup, QGroupBox)
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


class DeleteAttendanceWorker(QThread):
    finished_success = Signal(int)
    finished_error = Signal(str)

    def __init__(self, record_id=None, employee_id=None, work_date=None, before_date=None, from_date=None, to_date=None, office_id=None, delete_all=False):
        super().__init__()
        self.record_id = record_id
        self.employee_id = employee_id
        self.work_date = work_date
        self.before_date = before_date
        self.from_date = from_date
        self.to_date = to_date
        self.office_id = office_id
        self.delete_all = delete_all

    def run(self):
        try:
            res = api.delete_attendance(
                record_id=self.record_id,
                employee_id=self.employee_id,
                work_date=self.work_date,
                before_date=self.before_date,
                from_date=self.from_date,
                to_date=self.to_date,
                office_id=self.office_id,
                delete_all=self.delete_all
            )
            self.finished_success.emit(res.get("deleted_count", 0))
        except Exception as exc:
            self.finished_error.emit(str(exc))


class DeleteHistoryDialog(QDialog):
    def __init__(self, employees=None, parent=None):
        if isinstance(employees, QWidget) and parent is None:
            parent = employees
            employees = None
        super().__init__(parent)
        self.employees = employees or {}
        self.setWindowTitle("Batch Delete Attendance History")
        self.setFixedWidth(520)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("Delete Attendance History")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ff6b6b;")
        layout.addWidget(title)

        desc = QLabel("Permanently remove attendance records from the central database. Restricted to Master Administrator.")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #aaa; font-size: 12px; margin-bottom: 4px;")
        layout.addWidget(desc)

        group = QGroupBox("Deletion Target")
        g_layout = QVBoxLayout(group)
        g_layout.setSpacing(10)

        self.btn_group = QButtonGroup(self)
        self.radio_staff = QRadioButton("Particular staff log on a specific day")
        self.radio_before = QRadioButton("Records on or before cutoff date")
        self.radio_range = QRadioButton("Records within date range")
        self.radio_all = QRadioButton("ALL attendance records across all time")

        self.btn_group.addButton(self.radio_staff, 1)
        self.btn_group.addButton(self.radio_before, 2)
        self.btn_group.addButton(self.radio_range, 3)
        self.btn_group.addButton(self.radio_all, 4)

        today = QDate.currentDate()

        g_layout.addWidget(self.radio_staff)
        h_staff = QHBoxLayout()
        h_staff.setContentsMargins(24, 0, 0, 4)
        self.staff_combo = QComboBox()
        self.staff_combo.setFixedWidth(250)
        sorted_emps = sorted(self.employees.values(), key=lambda e: (e.get('office_id', ''), e.get('full_name', '')))
        for emp in sorted_emps:
            name = emp.get('full_name') or f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip()
            office = emp.get('office_id', '')
            emp_no = emp.get('employee_no', '')
            label = f"{name} ({emp_no}) - {office}"
            self.staff_combo.addItem(label, str(emp.get('_id', '')))
        if not sorted_emps:
            self.staff_combo.addItem("No staff records loaded", "")

        self.staff_date_edit = QDateEdit(today)
        self.staff_date_edit.setCalendarPopup(True)
        self.staff_date_edit.setFixedWidth(120)
        h_staff.addWidget(self.staff_combo)
        h_staff.addWidget(QLabel("Date:"))
        h_staff.addWidget(self.staff_date_edit)
        h_staff.addStretch()
        g_layout.addLayout(h_staff)

        g_layout.addWidget(self.radio_before)
        self.before_date_edit = QDateEdit(today.addDays(-30))
        self.before_date_edit.setCalendarPopup(True)
        self.before_date_edit.setFixedWidth(130)
        h_before = QHBoxLayout()
        h_before.setContentsMargins(24, 0, 0, 4)
        h_before.addWidget(QLabel("Cutoff Date:"))
        h_before.addWidget(self.before_date_edit)
        h_before.addStretch()
        g_layout.addLayout(h_before)

        g_layout.addWidget(self.radio_range)
        self.from_date_edit = QDateEdit(today.addDays(-60))
        self.from_date_edit.setCalendarPopup(True)
        self.from_date_edit.setFixedWidth(120)
        self.to_date_edit = QDateEdit(today.addDays(-30))
        self.to_date_edit.setCalendarPopup(True)
        self.to_date_edit.setFixedWidth(120)
        h_range = QHBoxLayout()
        h_range.setContentsMargins(24, 0, 0, 4)
        h_range.addWidget(QLabel("From:"))
        h_range.addWidget(self.from_date_edit)
        h_range.addWidget(QLabel("To:"))
        h_range.addWidget(self.to_date_edit)
        h_range.addStretch()
        g_layout.addLayout(h_range)

        g_layout.addWidget(self.radio_all)
        layout.addWidget(group)

        self.radio_staff.setChecked(True)
        self.radio_staff.toggled.connect(self._update_radio_states)
        self.radio_before.toggled.connect(self._update_radio_states)
        self.radio_range.toggled.connect(self._update_radio_states)
        self.radio_all.toggled.connect(self._update_radio_states)
        self._update_radio_states()

        h_office = QHBoxLayout()
        h_office.addWidget(QLabel("Target Office Filter:"))
        self.office_combo = QComboBox()
        self.office_combo.addItem("All Offices (Entire Company)", "")
        for o in OFFICES:
            self.office_combo.addItem(o["name"], o["_id"])
        h_office.addWidget(self.office_combo)
        layout.addLayout(h_office)

        confirm_box = QVBoxLayout()
        confirm_label = QLabel("Type DELETE to confirm permanent deletion:")
        confirm_label.setStyleSheet("font-weight: bold; color: #ff8888; font-size: 12px;")
        confirm_box.addWidget(confirm_label)

        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("DELETE")
        self.confirm_input.setStyleSheet("padding: 6px; font-weight: bold; font-size: 13px;")
        confirm_box.addWidget(self.confirm_input)
        layout.addLayout(confirm_box)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedHeight(34)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.delete_btn = QPushButton("Permanently Delete")
        self.delete_btn.setFixedHeight(34)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8a1d29, stop:1 #ad2637);
                color: #ffffff;
                border: 1px solid #c93b50;
                border-radius: 5px;
                padding: 0 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #a82333, stop:1 #c72b41);
                border: 1px solid #ff576f;
            }
            QPushButton:pressed {
                background-color: #63121d;
                border: 1px solid #d9384e;
            }
            QPushButton:disabled {
                background-color: #2b1d20;
                color: #6b5256;
                border-color: #3d282c;
            }
        """)
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.delete_btn)
        layout.addLayout(btn_layout)

        self.confirm_input.textChanged.connect(self._check_confirm)
        self.staff_combo.currentIndexChanged.connect(lambda: self._check_confirm(self.confirm_input.text()))

    def _update_radio_states(self):
        staff_active = self.radio_staff.isChecked()
        self.staff_combo.setEnabled(staff_active)
        self.staff_date_edit.setEnabled(staff_active)

        before_active = self.radio_before.isChecked()
        self.before_date_edit.setEnabled(before_active)

        range_active = self.radio_range.isChecked()
        self.from_date_edit.setEnabled(range_active)
        if hasattr(self, 'confirm_input'):
            self._check_confirm(self.confirm_input.text())

    def _check_confirm(self, text):
        confirmed = text.strip() == "DELETE"
        if self.radio_staff.isChecked() and not self.staff_combo.currentData():
            confirmed = False
        self.delete_btn.setEnabled(confirmed)

    def get_delete_params(self):
        office_id = self.office_combo.currentData() or None
        if self.radio_staff.isChecked():
            emp_id = self.staff_combo.currentData() or None
            work_date = self.staff_date_edit.date().toString("yyyy-MM-dd")
            return {"employee_id": emp_id, "work_date": work_date, "office_id": office_id}
        elif self.radio_all.isChecked():
            return {"delete_all": True, "office_id": office_id}
        elif self.radio_before.isChecked():
            before_str = self.before_date_edit.date().toString("yyyy-MM-dd")
            return {"before_date": before_str, "office_id": office_id}
        else:
            from_str = self.from_date_edit.date().toString("yyyy-MM-dd")
            to_str = self.to_date_edit.date().toString("yyyy-MM-dd")
            return {"from_date": from_str, "to_date": to_str, "office_id": office_id}


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
        self.inactivity_timer.setInterval(600_000)
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

        self.delete_selected_btn = QPushButton('Delete Selected Log')
        self.delete_selected_btn.setToolTip('Permanently delete the selected attendance entry (Master Admin only)')
        self.delete_selected_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3d141b, stop:0.5 #541b25, stop:1 #3d141b);
                color: #ff99a8;
                border: 1px solid #7c2431;
                border-radius: 5px;
                font-size: 12px;
                font-weight: 600;
                padding: 5px 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5e1c28, stop:0.5 #7a2233, stop:1 #5e1c28);
                color: #ffffff;
                border: 1px solid #ff4d6d;
            }
            QPushButton:pressed {
                background-color: #240c11;
                border: 1px solid #c92a43;
            }
            QPushButton:disabled {
                background: #1e191b;
                color: #554448;
                border: 1px solid #2d2225;
            }
        """)
        self.delete_selected_btn.setEnabled(False)
        self.delete_selected_btn.setVisible(False)
        self.delete_selected_btn.clicked.connect(self.delete_selected_log)
        filters.addWidget(self.delete_selected_btn)
        layout.addLayout(filters)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.attendance_table = self.table(['Location', 'Office', 'Name', 'Employee ID',
                                           'Job Title', 'Date', 'Time In', 'Time Out', 'Minutes', 'Status'])
        self.attendance_table.itemSelectionChanged.connect(self.on_attendance_selection_changed)
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

        master_actions = QHBoxLayout()
        master_actions.setContentsMargins(0, 10, 0, 4)
        master_actions.setSpacing(12)
        master_actions.addStretch()

        self.reset_button = QPushButton('Reset Office Password')
        self.reset_button.setFixedHeight(34)
        self.reset_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1e293b, stop:1 #0f172a);
                color: #94a3b8;
                border: 1px solid #334155;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                padding: 0 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #334155, stop:1 #1e293b);
                color: #e2e8f0;
                border: 1px solid #64748b;
            }
            QPushButton:pressed {
                background-color: #0b1120;
                border-color: #475569;
            }
        """)
        self.reset_button.clicked.connect(self.reset_office_password)
        master_actions.addWidget(self.reset_button)

        self.delete_history_btn = QPushButton('Batch Delete History...')
        self.delete_history_btn.setFixedHeight(34)
        self.delete_history_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2b1116, stop:0.5 #3d141e, stop:1 #2b1116);
                color: #ff99a8;
                border: 1px solid #6b1f2b;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                padding: 0 18px;
                letter-spacing: 0.3px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #421620, stop:0.5 #5e1c2b, stop:1 #421620);
                color: #ffffff;
                border: 1px solid #ff4d6d;
            }
            QPushButton:pressed {
                background-color: #1a080c;
                border: 1px solid #a82338;
            }
            QPushButton:disabled {
                background: #181214;
                color: #554448;
                border-color: #2b1c20;
            }
        """)
        self.delete_history_btn.clicked.connect(self.open_delete_history_dialog)
        master_actions.addWidget(self.delete_history_btn)
        layout.addLayout(master_actions)

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
        self.inactivity_timer.start(600_000)
        master = user['role'] == 'main_admin'
        self.title.setText('Master Admin (All Offices)' if master else OFFICE_MAP[user['office_id']]['name'])
        self.kiosk_button.setVisible(not master)
        self.reset_button.setVisible(master)
        self.delete_history_btn.setVisible(master)
        self.delete_selected_btn.setVisible(master)
        self.delete_selected_btn.setEnabled(False)
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
        self.delete_selected_btn.setEnabled(False)
        self.emp_table.setRowCount(0)
        self.attendance_table.setRowCount(0)

    def reset_inactivity_timer(self):
        if self.user:
            self.inactivity_timer.start(600_000)

    def on_inactivity_timeout(self):
        self.inactivity_timer.stop()
        if self.user:
            QMessageBox.warning(self, 'Session Expired', 'Your admin session has expired after 10 minutes of inactivity for security.')
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
            rec_id = str(record.get('_id', ''))
            self.add_row(self.attendance_table, values, record_id=rec_id)

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

    def on_attendance_selection_changed(self):
        is_master = bool(self.user and self.user.get('role') == 'main_admin')
        has_sel = bool(self.attendance_table.selectionModel() and self.attendance_table.selectionModel().hasSelection())
        self.delete_selected_btn.setEnabled(is_master and has_sel)

    def delete_selected_log(self):
        if not self.user or self.user.get('role') != 'main_admin':
            return
        row = self.attendance_table.currentRow()
        if row < 0:
            QMessageBox.information(self, 'Select Log', 'Select an attendance record from the table first.')
            return

        item0 = self.attendance_table.item(row, 0)
        record_id = item0.data(Qt.UserRole) if item0 else None
        location = self.attendance_table.item(row, 0).text() if self.attendance_table.item(row, 0) else ''
        office = self.attendance_table.item(row, 1).text() if self.attendance_table.item(row, 1) else ''
        staff_name = self.attendance_table.item(row, 2).text() if self.attendance_table.item(row, 2) else ''
        emp_no = self.attendance_table.item(row, 3).text() if self.attendance_table.item(row, 3) else ''
        work_date = self.attendance_table.item(row, 5).text() if self.attendance_table.item(row, 5) else ''
        time_in = self.attendance_table.item(row, 6).text() if self.attendance_table.item(row, 6) else ''

        msg = (f"Are you sure you want to permanently delete this attendance record?\n\n"
               f"• Staff: {staff_name} ({emp_no})\n"
               f"• Office: {office} ({location})\n"
               f"• Date: {work_date}\n"
               f"• Time In: {time_in or 'N/A'}\n\n"
               f"This action is immediate and cannot be undone.")

        if QMessageBox.question(self, 'Confirm Deletion', msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return

        self.reset_inactivity_timer()
        self.delete_selected_btn.setEnabled(False)
        self.summary.setText(f"Deleting record for {staff_name} on {work_date}...")

        emp_id = None
        for eid, edata in self.employees.items():
            if edata.get('employee_no') == emp_no or edata.get('full_name') == staff_name:
                emp_id = eid
                break

        self.del_worker = DeleteAttendanceWorker(
            record_id=record_id,
            employee_id=emp_id if not record_id else None,
            work_date=work_date if not record_id else None
        )
        self.del_worker.finished_success.connect(self.on_delete_history_success)
        self.del_worker.finished_error.connect(self.on_delete_history_error)
        self.del_worker.start()

    def open_delete_history_dialog(self):
        if not self.user or self.user.get('role') != 'main_admin':
            return
        self.reset_inactivity_timer()
        dialog = DeleteHistoryDialog(employees=self.employees, parent=self)
        if dialog.exec():
            params = dialog.get_delete_params()
            self.delete_history_btn.setEnabled(False)
            self.delete_history_btn.setText("Deleting...")
            self.summary.setText("Deleting attendance history...")
            self.del_worker = DeleteAttendanceWorker(**params)
            self.del_worker.finished_success.connect(self.on_delete_history_success)
            self.del_worker.finished_error.connect(self.on_delete_history_error)
            self.del_worker.start()

    def on_delete_history_success(self, count):
        self.delete_history_btn.setEnabled(True)
        self.delete_history_btn.setText("Batch Delete History...")
        self.on_attendance_selection_changed()
        self.summary.setText(f"Deleted {count} record(s).")
        QMessageBox.information(self, "Success", f"Successfully deleted {count} attendance record(s).")
        self.refresh()

    def on_delete_history_error(self, err_msg):
        self.delete_history_btn.setEnabled(True)
        self.delete_history_btn.setText("Batch Delete History...")
        self.on_attendance_selection_changed()
        self.summary.setText("Attendance deletion failed.")
        QMessageBox.critical(self, "Deletion Failed", err_msg)

