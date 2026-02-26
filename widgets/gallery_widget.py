"""Enhanced gallery widget with context menu, selection tracking, and double-click preview."""

from PySide6.QtWidgets import (
    QListWidget, QListWidgetItem, QAbstractItemView, QMenu,
)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QPixmap, QIcon, QAction


class GalleryWidget(QListWidget):
    """Thumbnail gallery with multi-selection, context menu, and preview support."""

    preview_requested = Signal(int)
    selection_changed_count = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setViewMode(QListWidget.IconMode)
        self.setResizeMode(QListWidget.Adjust)
        self.setSpacing(10)
        self.setSelectionMode(QAbstractItemView.MultiSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setUniformItemSizes(False)
        self.setWordWrap(True)

        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemDoubleClicked.connect(self._on_double_click)
        self.itemSelectionChanged.connect(self._emit_selection_count)

        self._aspect_ratio = 16 / 9

    def set_aspect_ratio(self, ratio: float):
        """Set the video aspect ratio for proper thumbnail sizing."""
        self._aspect_ratio = ratio if ratio > 0 else 16 / 9

    def update_thumbnail_size(self, width: int):
        """Resize gallery icons to the given width, maintaining the video's aspect ratio."""
        height = int(width / self._aspect_ratio)
        self.setIconSize(QSize(width, height))
        self.setGridSize(QSize(width + 20, height + 40))

    def add_frame(self, thumbnail_qimg, temp_filepath: str, timestamp: float, time_str: str):
        """Add a frame thumbnail to the gallery."""
        item = QListWidgetItem()
        pixmap = QPixmap.fromImage(thumbnail_qimg)
        item.setIcon(QIcon(pixmap))
        item.setText(time_str)
        item.setTextAlignment(Qt.AlignCenter)
        item.setData(Qt.UserRole, (time_str, temp_filepath))
        self.addItem(item)

    def get_selected_frame_data(self) -> list[tuple[str, str]]:
        """Return list of (time_str, temp_filepath) for all selected items."""
        return [item.data(Qt.UserRole) for item in self.selectedItems()]

    def get_all_frame_data(self) -> list[tuple[str, str]]:
        """Return list of (time_str, temp_filepath) for all items."""
        return [self.item(i).data(Qt.UserRole) for i in range(self.count())]

    def remove_selected(self):
        """Remove selected items from the gallery."""
        for item in self.selectedItems():
            self.takeItem(self.row(item))

    def _show_context_menu(self, pos):
        menu = QMenu(self)

        item = self.itemAt(pos)
        if item:
            act_preview = QAction("Preview", self)
            act_preview.triggered.connect(lambda: self.preview_requested.emit(self.row(item)))
            menu.addAction(act_preview)
            menu.addSeparator()

        act_select_all = QAction("Select All", self)
        act_select_all.triggered.connect(self.selectAll)
        menu.addAction(act_select_all)

        act_clear = QAction("Clear Selection", self)
        act_clear.triggered.connect(self.clearSelection)
        menu.addAction(act_clear)

        if self.selectedItems():
            menu.addSeparator()
            act_remove = QAction("Remove Selected", self)
            act_remove.triggered.connect(self.remove_selected)
            menu.addAction(act_remove)

        menu.exec(self.mapToGlobal(pos))

    def _on_double_click(self, item: QListWidgetItem):
        self.preview_requested.emit(self.row(item))

    def _emit_selection_count(self):
        self.selection_changed_count.emit(len(self.selectedItems()))
