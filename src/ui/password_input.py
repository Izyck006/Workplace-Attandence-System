from PySide6.QtWidgets import QLineEdit
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QBrush, QAction
from PySide6.QtCore import Qt, QPointF


def create_eye_pixmap(visible: bool, is_dark: bool = True, size: int = 20) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    color = QColor("#94a3b8") if is_dark else QColor("#64748b")
    pen = QPen(color, 1.8)
    pen.setCapStyle(Qt.RoundCap)
    painter.setPen(pen)

    cx, cy = size / 2.0, size / 2.0
    painter.drawArc(int(cx - 8), int(cy - 5), 16, 10, 30 * 16, 120 * 16)
    painter.drawArc(int(cx - 8), int(cy - 5), 16, 10, 210 * 16, 120 * 16)

    painter.setBrush(QBrush(color))
    painter.drawEllipse(QPointF(cx, cy), 2.5, 2.5)

    if not visible:
        slash_pen = QPen(QColor("#ef4444") if is_dark else QColor("#dc2626"), 1.8)
        slash_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(slash_pen)
        painter.drawLine(int(cx - 7), int(cy - 6), int(cx + 7), int(cy + 6))

    painter.end()
    return pixmap


class PasswordLineEdit(QLineEdit):
    """
    Enterprise-grade password input with an interactive Eye visibility toggle icon.
    """
    def __init__(self, placeholder: str = "Password", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setEchoMode(QLineEdit.Password)
        self._is_visible = False
        self._is_dark = True
        try:
            from src.ui.theme import ThemeManager
            tm = ThemeManager.instance()
            self._is_dark = tm.is_dark
            tm.theme_changed.connect(self.set_dark_theme)
        except Exception:
            pass

        self.eye_action = self.addAction(QIcon(), QLineEdit.TrailingPosition)
        self.eye_action.setToolTip("Show password")
        self.eye_action.triggered.connect(self.toggle_visibility)
        self.update_icon()

    def set_dark_theme(self, is_dark: bool):
        self._is_dark = is_dark
        self.update_icon()

    def update_icon(self):
        pixmap = create_eye_pixmap(self._is_visible, self._is_dark, size=20)
        self.eye_action.setIcon(QIcon(pixmap))
        self.eye_action.setToolTip("Hide password" if self._is_visible else "Show password")

    def toggle_visibility(self):
        self._is_visible = not self._is_visible
        if self._is_visible:
            self.setEchoMode(QLineEdit.Normal)
        else:
            self.setEchoMode(QLineEdit.Password)
        self.update_icon()
        self.setFocus()
