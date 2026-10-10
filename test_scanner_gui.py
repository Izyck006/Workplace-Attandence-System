import sys
import ctypes
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPixmap
from src.scanner.kojack import KojackScanner

class ScannerTestApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kojack Scanner Live Preview")
        self.setFixedSize(800, 600)
        
        self.scanner = KojackScanner()
        if not self.scanner.open_device(0):
            print("Failed to open scanner! Is it plugged in?")
            sys.exit(1)
            
        
        self.scanner.begin_capture(3)
        
        self.label = QLabel("Waiting for scanner...")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("background-color: black; color: white; font-size: 20px;")
        self.label.setScaledContents(False) 
        
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(50) 
        
    def update_frame(self):
        
        success, img_bytes, w, h, is_final, finger_state = self.scanner.block_get_image(ignore_preview=False)
        
        if success and img_bytes and w > 0 and h > 0:
            
            img = QImage(img_bytes, w, h, w, QImage.Format_Grayscale8)
            pixmap = QPixmap.fromImage(img)
            
            
            scaled_pixmap = pixmap.scaled(self.label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.label.setPixmap(scaled_pixmap)
            
            if is_final:
                print("Final Image Captured! Restarting preview...")
                
                self.scanner.begin_capture(3)

    def closeEvent(self, event):
        self.scanner.close_device()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScannerTestApp()
    window.show()
    sys.exit(app.exec())
