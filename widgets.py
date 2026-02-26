from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt, Signal

class DropLabel(QLabel):
    file_dropped = Signal(str)

    def __init__(self):
        super().__init__("Drag and drop video here\nor use the Browse button")
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 8px;
                padding: 20px;
                background-color: #f8f9fa;
                color: #555;
                font-size: 14px;
            }
            QLabel:hover {
                background-color: #e9ecef;
                border-color: #888;
            }
        """)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            self.file_dropped.emit(urls[0].toLocalFile())