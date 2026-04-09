from PySide6.QtWidgets import (
    QListWidget, QListWidgetItem, QAbstractItemView, QMenu,
)
from PySide6.QtCore import Qt, QSize, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QIcon, QAction, QWheelEvent


class GalleryWidget(QListWidget):
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
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)

        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemDoubleClicked.connect(self._on_double_click)
        self.itemSelectionChanged.connect(self._emit_selection_count)

        self._aspect_ratio = 16 / 9
        self._scroll_target_y = 0
        self._scroll_anim: QPropertyAnimation | None = None

    def set_aspect_ratio(self, ratio: float):
        self._aspect_ratio = ratio if ratio > 0 else 16 / 9

    def update_thumbnail_size(self, width: int):
        height = int(width / self._aspect_ratio)
        self.setIconSize(QSize(width, height))
        self.setGridSize(QSize(width + 20, height + 40))

    def add_frame(self, thumbnail_qimg, temp_filepath: str, timestamp: float, time_str: str):
        item = QListWidgetItem()
        pixmap = QPixmap.fromImage(thumbnail_qimg)
        item.setIcon(QIcon(pixmap))
        item.setText(time_str)
        item.setTextAlignment(Qt.AlignCenter)
        item.setData(Qt.UserRole, (time_str, temp_filepath))
        self.addItem(item)

    def get_selected_frame_data(self) -> list[tuple[str, str]]:
        return [item.data(Qt.UserRole) for item in self.selectedItems()]

    def get_all_frame_data(self) -> list[tuple[str, str]]:
        return [self.item(i).data(Qt.UserRole) for i in range(self.count())]

    def remove_selected(self):
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

    def wheelEvent(self, event: QWheelEvent):
        scrollbar = self.verticalScrollBar()
        delta = -event.angleDelta().y()
        self._scroll_target_y = max(
            scrollbar.minimum(),
            min(scrollbar.maximum(), scrollbar.value() + delta),
        )
        if self._scroll_anim and self._scroll_anim.state() == QPropertyAnimation.Running:
            self._scroll_anim.stop()
        self._scroll_anim = QPropertyAnimation(scrollbar, b"value")
        self._scroll_anim.setDuration(300)
        self._scroll_anim.setStartValue(scrollbar.value())
        self._scroll_anim.setEndValue(self._scroll_target_y)
        self._scroll_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._scroll_anim.start()
        event.accept()
