import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from datetime import datetime
from bson import ObjectId
from src.client import api, Cursor


def test_dashboard_grouping_office_selection_and_clear(qtbot, monkeypatch):
    from src.ui.dashboard import DashboardWidget, local_time, csv_safe
    kano, abuja = ObjectId(), ObjectId()
    def call(path, body=None):
        assert path == '/read'
        if body['collection'] == 'employees':
            return [{'office_id': 'engineering-kano', '_id': kano, 'employee_no': 'K1', 'full_name': 'Kano Staff', 'status': 'active'},
                    {'office_id': 'logistics-abuja', '_id': abuja, 'employee_no': 'A1', 'full_name': 'Abuja Staff', 'status': 'active'}]
        return [{'office_id': 'engineering-kano', 'employee_id': kano, 'work_date': '2026-10-19', 'clock_in_at': datetime(2026, 10, 19, 8)},
                {'office_id': 'logistics-abuja', 'employee_id': abuja, 'work_date': '2026-10-19', 'clock_in_at': datetime(2026, 10, 19, 7)}]
    monkeypatch.setattr(api, 'call', call)
    monkeypatch.setattr(api, 'token', 'test-token')
    dashboard = DashboardWidget()
    qtbot.addWidget(dashboard)
    dashboard.set_user({'role': 'main_admin'})
    assert dashboard.attendance_table.rowCount() == 2
    assert dashboard.attendance_table.item(0, 0).text() == 'Abuja'
    assert dashboard.attendance_table.item(1, 0).text() == 'Kano'
    assert local_time(datetime(2026, 10, 19, 8)) == '09:00:00'
    assert csv_safe('=BAD()') == "'=BAD()"
    dashboard.clear_data()
    assert dashboard.attendance_table.rowCount() == dashboard.emp_table.rowCount() == 0
    dashboard.set_user({'role': 'office_admin', 'office_id': 'engineering-kano'})
    assert not dashboard.office_filter.isEnabled()
    assert dashboard.office_filter.currentData() == 'engineering-kano'


def test_main_window_starts_with_login_without_database(qtbot, monkeypatch):
    from src.scanner.provider import KojackVendorProvider
    monkeypatch.setattr(KojackVendorProvider, 'initialize', lambda self: False)
    monkeypatch.setattr(api, 'token', None)
    from main import MainWindow
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.stacked_widget.currentWidget() is window.login_view
    assert window.dashboard_view.emp_table.rowCount() == 0


def test_legacy_conversion_preserves_templates_and_rejects_code():
    import io
    import pickle
    import zlib
    import numpy as np
    import mongomock
    import pytest
    from src.server.legacy import convert_templates, TemplateReader
    db = mongomock.MongoClient().test
    sample = np.ones((100, 32), dtype=np.uint8)
    emp = db.employees.insert_one({'fingerprint_descriptors': zlib.compress(pickle.dumps([sample]))}).inserted_id
    assert convert_templates(db) == (1, 0)
    assert db.employees.find_one({'_id': emp})['fingerprint_samples'] == [sample.tolist()]
    assert convert_templates(db) == (0, 0)
    with pytest.raises(ValueError):
        TemplateReader(io.BytesIO(b'cos\nsystem\n.')).load()


def test_dashboard_session_timeout_and_deletion_controls(qtbot, monkeypatch):
    from src.ui.dashboard import DashboardWidget, DeleteHistoryDialog
    kano = ObjectId()
    def call(path, body=None):
        if body['collection'] == 'employees':
            return [{'office_id': 'engineering-kano', '_id': kano, 'employee_no': 'K1', 'full_name': 'Kano Staff', 'status': 'active'}]
        return [{'office_id': 'engineering-kano', 'employee_id': kano, 'work_date': '2026-10-19', 'clock_in_at': datetime(2026, 10, 19, 8)}]
    monkeypatch.setattr(api, 'call', call)
    monkeypatch.setattr(api, 'token', 'test-token')

    dashboard = DashboardWidget()
    qtbot.addWidget(dashboard)

    # 1. Verify 10-minute session idle timeout (600,000 ms)
    assert dashboard.inactivity_timer.interval() == 600_000

    # 2. Master Admin controls
    dashboard.set_user({'role': 'main_admin'})
    dashboard.show()
    assert dashboard.inactivity_timer.isActive()
    assert dashboard.delete_history_btn.isVisible()
    assert dashboard.delete_selected_btn.isVisible()
    assert not dashboard.delete_selected_btn.isEnabled()

    # Selecting row enables the sleek Delete Selected Log button
    dashboard.attendance_table.selectRow(0)
    assert dashboard.delete_selected_btn.isEnabled()

    # Deselecting disables it
    dashboard.attendance_table.clearSelection()
    assert not dashboard.delete_selected_btn.isEnabled()

    # 3. Office Admin cannot see deletion controls
    dashboard.set_user({'role': 'office_admin', 'office_id': 'engineering-kano'})
    assert not dashboard.delete_history_btn.isVisible()
    assert not dashboard.delete_selected_btn.isVisible()

    # 4. Verify DeleteHistoryDialog criteria and params
    emps = {str(kano): {'_id': kano, 'employee_no': 'K1', 'full_name': 'Kano Staff', 'office_id': 'engineering-kano'}}
    dialog = DeleteHistoryDialog(employees=emps)
    qtbot.addWidget(dialog)

    assert dialog.radio_staff.isChecked()
    assert not dialog.delete_btn.isEnabled()
    dialog.confirm_input.setText("DELETE")
    assert dialog.delete_btn.isEnabled()

    params = dialog.get_delete_params()
    assert params.get('employee_id') == str(kano)
    assert 'work_date' in params

