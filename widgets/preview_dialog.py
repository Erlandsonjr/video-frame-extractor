from collections import OrderedDict

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QSizePolicy, QWidget,
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QWheelEvent, QKeySequence, QShortcut

_PIXMAP_CACHE_SIZE = 5


class PreviewDialog(QDialog):
    export_requested = Signal(int)

    def __init__(self, frames: list[tuple[str, str]], start_index: int = 0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Frame Preview")
        self.resize(1000, 700)
        self.setMinimumSize(500, 400)

        self._frames = frames
        self._current_index = start_index
        self._zoom_factor = 1.0
        self._pixmap_cache: OrderedDict[int, QPixmap] = OrderedDict()
        self._scroll_target_y = 0
        self._scroll_anim: QPropertyAnimation | None = None

        self._setup_ui()
        self._setup_shortcuts()
        self._show_frame(self._current_index)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setAlignment(Qt.AlignCenter)

        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignCenter)
        self._image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self._scroll.setWidget(self._image_label)
        layout.addWidget(self._scroll, stretch=1)

        bar = QHBoxLayout()
        bar.setContentsMargins(8, 4, 8, 8)

        self._btn_prev = QPushButton("◀ Previous")
        self._btn_prev.clicked.connect(self._prev)
        bar.addWidget(self._btn_prev)

        self._lbl_info = QLabel()
        self._lbl_info.setAlignment(Qt.AlignCenter)
        bar.addWidget(self._lbl_info, stretch=1)

        self._lbl_zoom = QLabel("100%")
        self._lbl_zoom.setAlignment(Qt.AlignCenter)
        self._lbl_zoom.setFixedWidth(60)
        bar.addWidget(self._lbl_zoom)

        btn_fit = QPushButton("Fit")
        btn_fit.setFixedWidth(50)
        btn_fit.setToolTip("Fit to window (F)")
        btn_fit.clicked.connect(self._fit_to_window)
        bar.addWidget(btn_fit)

        self._btn_next = QPushButton("Next ▶")
        self._btn_next.clicked.connect(self._next)
        bar.addWidget(self._btn_next)

        btn_export = QPushButton("Export This Frame")
        btn_export.setObjectName("btn_save")
        btn_export.clicked.connect(lambda: self.export_requested.emit(self._current_index))
        bar.addWidget(btn_export)

        bar_widget = QWidget()
        bar_widget.setLayout(bar)
        layout.addWidget(bar_widget)

    def _setup_shortcuts(self):
        QShortcut(QKeySequence(Qt.Key_Left), self, self._prev)
        QShortcut(QKeySequence(Qt.Key_Right), self, self._next)
        QShortcut(QKeySequence(Qt.Key_Plus), self, self._zoom_in)
        QShortcut(QKeySequence(Qt.Key_Minus), self, self._zoom_out)
        QShortcut(QKeySequence(Qt.Key_Equal), self, self._zoom_in)
        QShortcut(QKeySequence(Qt.Key_F), self, self._fit_to_window)
        QShortcut(QKeySequence(Qt.Key_Escape), self, self.close)

    def _load_pixmap(self, index: int) -> QPixmap:
        if index in self._pixmap_cache:
            self._pixmap_cache.move_to_end(index)
            return self._pixmap_cache[index]

        file_path, _ = self._frames[index]
        pixmap = QPixmap(file_path)
        self._pixmap_cache[index] = pixmap
        while len(self._pixmap_cache) > _PIXMAP_CACHE_SIZE:
            self._pixmap_cache.popitem(last=False)
        return pixmap

    def _show_frame(self, index: int):
        self._current_pixmap = self._load_pixmap(index)
        self._current_index = index
        self._zoom_factor = 1.0
        self._apply_zoom()

        _, label_text = self._frames[index]
        total = len(self._frames)
        self._lbl_info.setText(f"{label_text}  ({index + 1} / {total})")
        self._btn_prev.setEnabled(index > 0)
        self._btn_next.setEnabled(index < total - 1)

    def _apply_zoom(self):
        scaled = self._current_pixmap.scaled(
            self._current_pixmap.size() * self._zoom_factor,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self._image_label.setPixmap(scaled)
        self._image_label.resize(scaled.size())
        self._lbl_zoom.setText(f"{int(self._zoom_factor * 100)}%")

    def _fit_to_window(self):
        viewport = self._scroll.viewport().size()
        pw = self._current_pixmap.width()
        ph = self._current_pixmap.height()
        if pw > 0 and ph > 0:
            self._zoom_factor = min(viewport.width() / pw, viewport.height() / ph)
            self._apply_zoom()

    def _prev(self):
        if self._current_index > 0:
            self._show_frame(self._current_index - 1)

    def _next(self):
        if self._current_index < len(self._frames) - 1:
            self._show_frame(self._current_index + 1)

    def _zoom_in(self):
        self._zoom_factor = min(self._zoom_factor * 1.25, 10.0)
        self._apply_zoom()

    def _zoom_out(self):
        self._zoom_factor = max(self._zoom_factor / 1.25, 0.1)
        self._apply_zoom()

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() & Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self._zoom_in()
            else:
                self._zoom_out()
            event.accept()
        else:
            scrollbar = self._scroll.verticalScrollBar()
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
