"""Drag-and-drop label with video file MIME validation."""

import os
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt, Signal

from utils.constants import VIDEO_EXTENSIONS


class DropLabel(QLabel):
    """A label that accepts drag-and-drop of video files only."""

    file_dropped = Signal(str)

    def __init__(self, parent=None):
        super().__init__("Drag and drop video here\nor use the Browse button", parent)
        self.setObjectName("drop_label")
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(60)
        self.setAcceptDrops(True)
        self._default_text = "Drag and drop video here\nor use the Browse button"

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            file_path = url.toLocalFile()
            ext = os.path.splitext(file_path)[1].lower()
            if ext in VIDEO_EXTENSIONS:
                event.acceptProposedAction()
                self.setProperty("drag_hover", True)
                self.style().unpolish(self)
                self.style().polish(self)
                return
        event.ignore()

    def dragLeaveEvent(self, event):
        self.setProperty("drag_hover", False)
        self.style().unpolish(self)
        self.style().polish(self)

    def dropEvent(self, event):
        self.setProperty("drag_hover", False)
        self.style().unpolish(self)
        self.style().polish(self)

        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            ext = os.path.splitext(file_path)[1].lower()
            if ext in VIDEO_EXTENSIONS:
                self.file_dropped.emit(file_path)
            else:
                self.setText(f"Unsupported format: {ext}\nDrop a video file instead.")

    def reset(self):
        self.setText(self._default_text)
