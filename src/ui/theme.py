from PySide6.QtWidgets import QApplication, QPushButton
from PySide6.QtCore import QObject, Signal, QSettings, Qt
from PySide6.QtGui import QColor, QFont, QPalette


DARK_STYLESHEET = """
QMainWindow, QStackedWidget, #centralStacked, #loginWidget, #kioskWidget, #dashboardWidget, QWidget#centralWidget {
    background-color: #000000;
    color: #ffffff;
    font-family: 'Segoe UI', Arial, sans-serif;
}

QWidget {
    color: #ffffff;
    font-family: 'Segoe UI', Arial, sans-serif;
}

QDialog {
    background-color: #121212;
    color: #ffffff;
}

QLabel {
    color: #ffffff;
}

QGroupBox {
    background-color: #121212;
    border: 1px solid #333333;
    border-radius: 8px;
    margin-top: 16px;
    font-weight: bold;
    color: #cccccc;
    padding-top: 14px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    left: 12px;
    color: #3b82f6;
}

QLineEdit, QComboBox, QDateEdit, QTimeEdit, QDateTimeEdit, QSpinBox {
    background-color: #1a1a1a;
    color: #ffffff;
    border: 1px solid #444444;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}

QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTimeEdit:focus, QDateTimeEdit:focus {
    border: 1px solid #2563eb;
    background-color: #222222;
    color: #ffffff;
}

QTimeEdit::up-button, QTimeEdit::down-button, QDateEdit::up-button, QDateEdit::down-button {
    background-color: #262626;
    border: 1px solid #3f3f46;
    border-radius: 2px;
    width: 18px;
}

QTimeEdit::up-button:hover, QTimeEdit::down-button:hover, QDateEdit::up-button:hover, QDateEdit::down-button:hover {
    background-color: #3b82f6;
}

QRadioButton, QCheckBox {
    color: #e2e8f0;
    font-size: 13px;
    spacing: 8px;
    background: transparent;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border: 2px solid #64748b;
    border-radius: 9px;
    background: #18181b;
}

QRadioButton::indicator:checked {
    border: 2px solid #3b82f6;
    background: #2563eb;
}

QRadioButton::indicator:hover {
    border-color: #93c5fd;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #64748b;
    border-radius: 4px;
    background: #18181b;
}

QCheckBox::indicator:checked {
    background: #2563eb;
    border-color: #3b82f6;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #1a1a1a;
    color: #ffffff;
    border: 1px solid #444444;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}

QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 7px 16px;
    font-size: 13px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #1d4ed8;
}

QPushButton:pressed {
    background-color: #1e40af;
}

QPushButton:disabled {
    background-color: #2a2a2a;
    color: #666666;
}

QTableWidget {
    background-color: #121212;
    color: #ffffff;
    gridline-color: #222222;
    border: 1px solid #333333;
    border-radius: 6px;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
    font-size: 13px;
}

QTableWidget::item {
    padding: 4px 8px;
    border-bottom: 1px solid #222222;
}

QTableWidget::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}

QHeaderView::section {
    background-color: #1c1c1c;
    color: #cccccc;
    padding: 6px 8px;
    font-weight: bold;
    border: none;
    border-right: 1px solid #333333;
    border-bottom: 2px solid #2563eb;
}

QTabWidget::pane {
    border: 1px solid #333333;
    background-color: #121212;
    border-radius: 6px;
}

QTabBar::tab {
    background-color: #1a1a1a;
    color: #888888;
    border: 1px solid #333333;
    padding: 8px 20px;
    font-weight: 600;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #2563eb;
    color: #ffffff;
    border: 1px solid #2563eb;
}

QTabBar::tab:hover:!selected {
    background-color: #2a2a2a;
    color: #ffffff;
}

QScrollBar:vertical {
    background: #000000;
    width: 10px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #333333;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #555555;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QMessageBox {
    background-color: #121212;
    color: #ffffff;
}
"""

LIGHT_STYLESHEET = """
QMainWindow, QStackedWidget, #centralStacked, #loginWidget, #kioskWidget, #dashboardWidget, QWidget#centralWidget {
    background-color: #f3f4f6;
    color: #111827;
    font-family: 'Segoe UI', Arial, sans-serif;
}

QWidget {
    color: #111827;
    font-family: 'Segoe UI', Arial, sans-serif;
}

QDialog {
    background-color: #ffffff;
    color: #111827;
}

QLabel {
    color: #111827;
}

QGroupBox {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    margin-top: 16px;
    font-weight: bold;
    color: #374151;
    padding-top: 14px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    left: 12px;
    color: #1d4ed8;
}

QLineEdit, QComboBox, QDateEdit, QTimeEdit, QDateTimeEdit, QSpinBox {
    background-color: #ffffff;
    color: #111827;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}

QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTimeEdit:focus, QDateTimeEdit:focus {
    border: 1px solid #2563eb;
    background-color: #ffffff;
    color: #111827;
}

QTimeEdit::up-button, QTimeEdit::down-button, QDateEdit::up-button, QDateEdit::down-button {
    background-color: #f1f5f9;
    border: 1px solid #cbd5e1;
    border-radius: 2px;
    width: 18px;
}

QTimeEdit::up-button:hover, QTimeEdit::down-button:hover, QDateEdit::up-button:hover, QDateEdit::down-button:hover {
    background-color: #e2e8f0;
}

QRadioButton, QCheckBox {
    color: #1f2937;
    font-size: 13px;
    spacing: 8px;
    background: transparent;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border: 2px solid #94a3b8;
    border-radius: 9px;
    background: #ffffff;
}

QRadioButton::indicator:checked {
    border: 2px solid #2563eb;
    background: #2563eb;
}

QRadioButton::indicator:hover {
    border-color: #3b82f6;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #94a3b8;
    border-radius: 4px;
    background: #ffffff;
}

QCheckBox::indicator:checked {
    background: #2563eb;
    border-color: #2563eb;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #111827;
    border: 1px solid #cbd5e1;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}

QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 7px 16px;
    font-size: 13px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #1d4ed8;
}

QPushButton:pressed {
    background-color: #1e40af;
}

QPushButton:disabled {
    background-color: #e5e7eb;
    color: #9ca3af;
}

QTableWidget {
    background-color: #ffffff;
    color: #111827;
    gridline-color: #e5e7eb;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    selection-background-color: #dbeafe;
    selection-color: #1e3a8a;
    font-size: 13px;
}

QTableWidget::item {
    padding: 4px 8px;
    border-bottom: 1px solid #f3f4f6;
}

QTableWidget::item:selected {
    background-color: #dbeafe;
    color: #1e3a8a;
}

QHeaderView::section {
    background-color: #f1f5f9;
    color: #1e293b;
    padding: 6px 8px;
    font-weight: bold;
    border: none;
    border-right: 1px solid #cbd5e1;
    border-bottom: 2px solid #2563eb;
}

QTabWidget::pane {
    border: 1px solid #cbd5e1;
    background-color: #ffffff;
    border-radius: 6px;
}

QTabBar::tab {
    background-color: #e2e8f0;
    color: #475569;
    border: 1px solid #cbd5e1;
    padding: 8px 20px;
    font-weight: 600;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #2563eb;
    color: #ffffff;
    border: 1px solid #2563eb;
}

QTabBar::tab:hover:!selected {
    background-color: #f1f5f9;
    color: #111827;
}

QScrollBar:vertical {
    background: #f3f4f6;
    width: 10px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #cbd5e1;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QMessageBox {
    background-color: #ffffff;
    color: #111827;
}
"""


class ThemeManager(QObject):
    theme_changed = Signal(bool)  # emits True for dark, False for light

    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = ThemeManager()
        return cls._instance

    def __init__(self):
        super().__init__()
        self.settings = QSettings("Randaframes", "AttendanceTheme")
        self._is_dark = self.settings.value("is_dark", True, type=bool)

    @property
    def is_dark(self) -> bool:
        return self._is_dark

    def apply(self, app=None):
        if app is None:
            app = QApplication.instance()
        if not app:
            return

        palette = QPalette()
        if self._is_dark:
            palette.setColor(QPalette.Window, QColor("#000000"))
            palette.setColor(QPalette.WindowText, QColor("#ffffff"))
            palette.setColor(QPalette.Base, QColor("#121212"))
            palette.setColor(QPalette.AlternateBase, QColor("#1e1e1e"))
            palette.setColor(QPalette.Text, QColor("#ffffff"))
            palette.setColor(QPalette.Button, QColor("#2563eb"))
            palette.setColor(QPalette.ButtonText, QColor("#ffffff"))
            app.setPalette(palette)
            app.setStyleSheet(DARK_STYLESHEET)
        else:
            palette.setColor(QPalette.Window, QColor("#f3f4f6"))
            palette.setColor(QPalette.WindowText, QColor("#111827"))
            palette.setColor(QPalette.Base, QColor("#ffffff"))
            palette.setColor(QPalette.AlternateBase, QColor("#f9fafb"))
            palette.setColor(QPalette.Text, QColor("#111827"))
            palette.setColor(QPalette.Button, QColor("#2563eb"))
            palette.setColor(QPalette.ButtonText, QColor("#ffffff"))
            app.setPalette(palette)
            app.setStyleSheet(LIGHT_STYLESHEET)

        self.theme_changed.emit(self._is_dark)

    def toggle(self):
        self._is_dark = not self._is_dark
        self.settings.setValue("is_dark", self._is_dark)
        self.apply()


class ThemeToggleButton(QPushButton):
    """
    Sleek executive Theme Switcher button (Light Mode / Dark Mode, no emojis).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(34)
        self.theme_mgr = ThemeManager.instance()
        self.theme_mgr.theme_changed.connect(self.on_theme_changed)
        self.clicked.connect(self.theme_mgr.toggle)
        self.update_appearance(self.theme_mgr.is_dark)

    def on_theme_changed(self, is_dark: bool):
        self.update_appearance(is_dark)

    def update_appearance(self, is_dark: bool):
        if is_dark:
            self.setText("Light Mode")
            self.setToolTip("Switch to Light Mode")
            self.setStyleSheet("""
                QPushButton {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    border: 1px solid #444444;
                    border-radius: 6px;
                    padding: 5px 14px;
                    font-size: 13px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #2a2a2a;
                    border-color: #666666;
                }
            """)
        else:
            self.setText("Dark Mode")
            self.setToolTip("Switch to Dark Mode")
            self.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff;
                    color: #111827;
                    border: 1px solid #cbd5e1;
                    border-radius: 6px;
                    padding: 5px 14px;
                    font-size: 13px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #f1f5f9;
                    border-color: #94a3b8;
                }
            """)
