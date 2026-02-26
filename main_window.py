"""Main window — fully rebuilt with menu bar, status bar, video info, cancel button,
keyboard shortcuts, preview dialog, export dialog, batch support, and settings persistence."""

import os
import shutil
import logging

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QDoubleSpinBox, QTimeEdit, QProgressBar, QMessageBox,
    QStyle, QSlider, QStatusBar,
)
from PySide6.QtCore import Qt, QTime
from PySide6.QtGui import QPixmap, QAction, QKeySequence, QShortcut

from widgets import DropLabel, VideoInfoPanel, PreviewDialog, GalleryWidget
from processing import VideoProcessor, ExportManager
from dialogs import ExportDialog, SettingsDialog, BatchDialog
from utils.constants import (
    APP_NAME, APP_VERSION, VIDEO_FILTER, ZOOM_MIN, ZOOM_MAX,
    MIN_INTERVAL, MAX_INTERVAL, INTERVAL_STEP, TEMP_DIR,
)
from utils.settings import AppSettings

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self, app=None):
        super().__init__()
        self._app = app 
        self._settings = app.settings if app else AppSettings()

        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(1000, 750)

        self.video_path: str | None = None
        self.video_info: dict = {}
        self.processor_thread: VideoProcessor | None = None
        self.export_thread: ExportManager | None = None
        self.temp_dir = TEMP_DIR
        os.makedirs(self.temp_dir, exist_ok=True)

        self._build_menu_bar()
        self._build_status_bar()
        self._setup_ui()
        self._setup_shortcuts()
        self._restore_geometry()

    def _build_menu_bar(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&File")

        act_open = QAction("&Open Video...", self)
        act_open.setShortcut(QKeySequence.Open)
        act_open.triggered.connect(self._browse_file)
        file_menu.addAction(act_open)

        act_batch = QAction("&Batch Processing...", self)
        act_batch.setShortcut(QKeySequence("Ctrl+B"))
        act_batch.triggered.connect(self._open_batch_dialog)
        file_menu.addAction(act_batch)

        file_menu.addSeparator()

        act_export = QAction("&Export Selected...", self)
        act_export.setShortcut(QKeySequence.Save)
        act_export.triggered.connect(self._save_frames)
        file_menu.addAction(act_export)

        file_menu.addSeparator()

        act_exit = QAction("E&xit", self)
        act_exit.setShortcut(QKeySequence("Ctrl+Q"))
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        view_menu = menu_bar.addMenu("&View")

        act_theme = QAction("Toggle &Theme", self)
        act_theme.setShortcut(QKeySequence("Ctrl+T"))
        act_theme.triggered.connect(self._toggle_theme)
        view_menu.addAction(act_theme)

        view_menu.addSeparator()

        act_zoom_in = QAction("Zoom &In", self)
        act_zoom_in.setShortcut(QKeySequence("Ctrl+="))
        act_zoom_in.triggered.connect(lambda: self._adjust_zoom(+25))
        view_menu.addAction(act_zoom_in)

        act_zoom_out = QAction("Zoom &Out", self)
        act_zoom_out.setShortcut(QKeySequence("Ctrl+-"))
        act_zoom_out.triggered.connect(lambda: self._adjust_zoom(-25))
        view_menu.addAction(act_zoom_out)

        edit_menu = menu_bar.addMenu("&Edit")

        act_select_all = QAction("Select &All", self)
        act_select_all.setShortcut(QKeySequence.SelectAll)
        act_select_all.triggered.connect(lambda: self.gallery.selectAll())
        edit_menu.addAction(act_select_all)

        act_clear_sel = QAction("&Clear Selection", self)
        act_clear_sel.setShortcut(QKeySequence("Ctrl+Shift+A"))
        act_clear_sel.triggered.connect(lambda: self.gallery.clearSelection())
        edit_menu.addAction(act_clear_sel)

        act_delete = QAction("&Remove Selected Frames", self)
        act_delete.setShortcut(QKeySequence.Delete)
        act_delete.triggered.connect(lambda: self.gallery.remove_selected())
        edit_menu.addAction(act_delete)

        edit_menu.addSeparator()

        act_settings = QAction("&Settings...", self)
        act_settings.triggered.connect(self._open_settings)
        edit_menu.addAction(act_settings)

        help_menu = menu_bar.addMenu("&Help")

        act_about = QAction("&About", self)
        act_about.triggered.connect(self._show_about)
        help_menu.addAction(act_about)

    def _build_status_bar(self):
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._lbl_status = QLabel("Ready")
        self._lbl_selection = QLabel("")
        self._status_bar.addWidget(self._lbl_status, stretch=1)
        self._status_bar.addPermanentWidget(self._lbl_selection)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)

        self._build_file_input_section(layout)
        self._build_video_info_panel(layout)
        self._build_controls_section(layout)
        self._build_progress_section(layout)
        self._build_zoom_section(layout)
        self._build_gallery_section(layout)
        self._build_export_section(layout)

    def _build_file_input_section(self, parent_layout):
        row = QHBoxLayout()

        self.drop_label = DropLabel()
        self.drop_label.file_dropped.connect(self.load_video)

        btn_browse = QPushButton("Browse File")
        btn_browse.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        btn_browse.setMinimumHeight(40)
        btn_browse.clicked.connect(self._browse_file)

        row.addWidget(self.drop_label, stretch=3)
        row.addWidget(btn_browse, stretch=1)
        parent_layout.addLayout(row)

    def _build_video_info_panel(self, parent_layout):
        self.info_panel = VideoInfoPanel()
        parent_layout.addWidget(self.info_panel)

    def _build_controls_section(self, parent_layout):
        row = QHBoxLayout()

        row.addWidget(QLabel("Start:"))
        self.time_start = QTimeEdit()
        self.time_start.setDisplayFormat("HH:mm:ss")
        self.time_start.setTime(QTime(0, 0, 0))
        row.addWidget(self.time_start)

        row.addWidget(QLabel("End:"))
        self.time_end = QTimeEdit()
        self.time_end.setDisplayFormat("HH:mm:ss")
        self.time_end.setTime(QTime(0, 0, 0))
        self.time_end.setToolTip("Leave at 00:00:00 to process until end of video")
        row.addWidget(self.time_end)

        row.addWidget(QLabel("Interval (sec):"))
        self.spin_interval = QDoubleSpinBox()
        self.spin_interval.setRange(MIN_INTERVAL, MAX_INTERVAL)
        self.spin_interval.setValue(self._settings.default_interval)
        self.spin_interval.setSingleStep(INTERVAL_STEP)
        row.addWidget(self.spin_interval)

        self.btn_process = QPushButton("Process Video")
        self.btn_process.setObjectName("btn_process")
        self.btn_process.setMinimumHeight(35)
        self.btn_process.clicked.connect(self._start_processing)
        row.addWidget(self.btn_process)

        parent_layout.addLayout(row)

    def _build_progress_section(self, parent_layout):
        row = QHBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        row.addWidget(self.progress_bar, stretch=1)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("btn_cancel")
        self.btn_cancel.setMinimumHeight(30)
        self.btn_cancel.hide()
        self.btn_cancel.clicked.connect(self._cancel_processing)
        row.addWidget(self.btn_cancel)

        parent_layout.addLayout(row)

    def _build_zoom_section(self, parent_layout):
        row = QHBoxLayout()
        row.addWidget(QLabel("Thumbnail Size:"))

        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(ZOOM_MIN, ZOOM_MAX)
        self.zoom_slider.setValue(self._settings.thumbnail_size)
        self.zoom_slider.valueChanged.connect(self._on_zoom_changed)
        row.addWidget(self.zoom_slider)

        self._lbl_zoom_val = QLabel(f"{self.zoom_slider.value()}px")
        self._lbl_zoom_val.setFixedWidth(50)
        row.addWidget(self._lbl_zoom_val)

        parent_layout.addLayout(row)

    def _build_gallery_section(self, parent_layout):
        self.gallery = GalleryWidget()
        self.gallery.preview_requested.connect(self._open_preview)
        self.gallery.selection_changed_count.connect(self._on_selection_changed)
        parent_layout.addWidget(self.gallery)

        self._on_zoom_changed(self.zoom_slider.value())

    def _build_export_section(self, parent_layout):
        row = QHBoxLayout()

        btn_select_all = QPushButton("Select All")
        btn_select_all.clicked.connect(self.gallery.selectAll)
        row.addWidget(btn_select_all)

        btn_clear = QPushButton("Clear Selection")
        btn_clear.clicked.connect(self.gallery.clearSelection)
        row.addWidget(btn_clear)

        row.addStretch()

        self._lbl_frame_count = QLabel("")
        row.addWidget(self._lbl_frame_count)

        btn_save = QPushButton("Save Selected Frames")
        btn_save.setObjectName("btn_save")
        btn_save.setMinimumHeight(40)
        btn_save.clicked.connect(self._save_frames)
        row.addWidget(btn_save)

        parent_layout.addLayout(row)

    def _setup_shortcuts(self):
        QShortcut(QKeySequence(Qt.Key_Escape), self, self._cancel_processing)

    def _browse_file(self):
        start_dir = self._settings.last_open_dir or ""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Video", start_dir, VIDEO_FILTER
        )
        if file_path:
            self._settings.last_open_dir = os.path.dirname(file_path)
            self.load_video(file_path)

    def load_video(self, file_path: str):
        self.video_path = file_path
        self.drop_label.setText(f"Video Loaded:\n{os.path.basename(file_path)}")
        self.gallery.clear()

        self.video_info = self.info_panel.load_video_info(file_path)
        if self.video_info:
            aspect = self.video_info.get("aspect_ratio", 16 / 9)
            self.gallery.set_aspect_ratio(aspect)
            self._on_zoom_changed(self.zoom_slider.value())

            duration = self.video_info.get("duration", 0)
            self._lbl_status.setText(
                f"Loaded: {os.path.basename(file_path)} — "
                f"{self.video_info['width']}×{self.video_info['height']} — "
                f"{duration:.1f}s"
            )
        else:
            self._lbl_status.setText(f"Loaded: {os.path.basename(file_path)}")

    def _time_to_seconds(self, qtime: QTime) -> float:
        return qtime.hour() * 3600 + qtime.minute() * 60 + qtime.second()

    def _start_processing(self):
        if not self.video_path:
            QMessageBox.warning(self, "Warning", "Please select a video file first.")
            return

        start_sec = self._time_to_seconds(self.time_start.time())
        end_sec = self._time_to_seconds(self.time_end.time())

        if end_sec != 0 and start_sec >= end_sec:
            QMessageBox.warning(
                self, "Invalid Range",
                "Start time must be earlier than end time.\n"
                "Set end to 00:00:00 to process until the end of the video."
            )
            return

        self._reset_ui_for_processing()

        interval = self.spin_interval.value()
        self.processor_thread = VideoProcessor(
            self.video_path, start_sec, end_sec, interval, self.temp_dir
        )
        self._connect_processor_signals()
        self.processor_thread.start()
        self._lbl_status.setText("Processing...")

    def _cancel_processing(self):
        if self.processor_thread and self.processor_thread.isRunning():
            self.processor_thread.stop()
            self.processor_thread.wait(3000)
            self._restore_ui_after_processing()
            self._lbl_status.setText("Processing cancelled.")

    def _reset_ui_for_processing(self):
        self.gallery.clear()
        self.btn_process.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.btn_cancel.show()

    def _connect_processor_signals(self):
        self.processor_thread.frame_extracted.connect(self._add_frame_to_gallery)
        self.processor_thread.progress_updated.connect(self.progress_bar.setValue)
        self.processor_thread.finished_processing.connect(self._on_processing_finished)
        self.processor_thread.error_occurred.connect(self._on_processing_error)

    def _add_frame_to_gallery(self, thumbnail_qimg, temp_filepath: str, timestamp: float):
        time_str = self._format_timestamp(timestamp)
        self.gallery.add_frame(thumbnail_qimg, temp_filepath, timestamp, time_str)

    @staticmethod
    def _format_timestamp(seconds_total: float) -> str:
        hours = int(seconds_total // 3600)
        minutes = int((seconds_total % 3600) // 60)
        seconds = seconds_total % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:04.1f}"

    def _on_processing_finished(self):
        self._restore_ui_after_processing()
        count = self.gallery.count()
        self._lbl_status.setText(f"Extraction complete — {count} frame(s) captured.")
        QMessageBox.information(self, "Done", f"Frame extraction completed.\n{count} frame(s) extracted.")

    def _on_processing_error(self, error_msg: str):
        self._restore_ui_after_processing()
        self._lbl_status.setText("Processing failed.")
        QMessageBox.critical(self, "Error", f"Processing failed:\n{error_msg}")

    def _restore_ui_after_processing(self):
        self.btn_process.setEnabled(True)
        self.progress_bar.hide()
        self.btn_cancel.hide()

    def _on_zoom_changed(self, width: int):
        self.gallery.update_thumbnail_size(width)
        self._lbl_zoom_val.setText(f"{width}px")
        self._settings.thumbnail_size = width

    def _adjust_zoom(self, delta: int):
        new_val = max(ZOOM_MIN, min(ZOOM_MAX, self.zoom_slider.value() + delta))
        self.zoom_slider.setValue(new_val)

    def _on_selection_changed(self, count: int):
        total = self.gallery.count()
        if total > 0:
            self._lbl_selection.setText(f"{count} / {total} selected")
        else:
            self._lbl_selection.setText("")

    def _open_preview(self, index: int):
        """Open full-resolution preview for the frame at the given gallery index."""
        frames = []
        for i in range(self.gallery.count()):
            item = self.gallery.item(i)
            time_str, temp_filepath = item.data(Qt.UserRole)
            pixmap = QPixmap(temp_filepath)
            frames.append((pixmap, time_str))

        if not frames:
            return

        dialog = PreviewDialog(frames, index, self)
        dialog.export_requested.connect(self._export_single_frame)
        dialog.exec()

    def _export_single_frame(self, index: int):
        """Quick-export a single frame from the preview dialog."""
        item = self.gallery.item(index)
        if not item:
            return
        time_str, temp_filepath = item.data(Qt.UserRole)
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Frame", f"frame_{time_str.replace(':', '-')}.png",
            "PNG (*.png);;JPEG (*.jpg);;WebP (*.webp);;BMP (*.bmp)"
        )
        if save_path:
            import shutil
            try:
                shutil.copy2(temp_filepath, save_path)
                self._lbl_status.setText(f"Saved: {os.path.basename(save_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))

    def _save_frames(self):
        selected = self.gallery.get_selected_frame_data()
        if not selected:
            QMessageBox.warning(self, "Warning", "No frames selected for export.")
            return

        video_name = os.path.basename(self.video_path) if self.video_path else ""
        dialog = ExportDialog(len(selected), video_name, self._settings, self)
        if dialog.exec() != ExportDialog.Accepted:
            return

        self._lbl_status.setText("Exporting...")
        self.progress_bar.setValue(0)
        self.progress_bar.show()

        self.export_thread = ExportManager(
            frames=selected,
            output_dir=dialog.output_dir,
            video_name=os.path.splitext(os.path.basename(video_name))[0],
            fmt=dialog.export_format,
            quality=dialog.quality,
            filename_pattern=dialog.filename_pattern,
            scale_percent=dialog.scale_percent,
        )
        self.export_thread.progress_updated.connect(self.progress_bar.setValue)
        self.export_thread.error_occurred.connect(
            lambda msg: logger.warning(f"Export warning: {msg}")
        )
        self.export_thread.finished.connect(self._on_export_finished)
        self.export_thread.start()

    def _on_export_finished(self, success: int, total: int):
        self.progress_bar.hide()
        if success == total:
            self._lbl_status.setText(f"Exported {success} frame(s) successfully.")
            QMessageBox.information(self, "Export Complete", f"Successfully saved {success} frame(s).")
        else:
            self._lbl_status.setText(f"Exported {success}/{total} frame(s) — some failed.")
            QMessageBox.warning(
                self, "Export Partial",
                f"Exported {success} of {total} frame(s).\n"
                f"{total - success} frame(s) failed — check the source files."
            )

    def _open_batch_dialog(self):
        dialog = BatchDialog(self._settings, self)
        dialog.exec()

    def _open_settings(self):
        theme_cb = self._app.theme_manager.apply_theme if self._app else None
        dialog = SettingsDialog(self._settings, theme_callback=theme_cb, parent=self)
        if dialog.exec() == SettingsDialog.Accepted:
            self.spin_interval.setValue(self._settings.default_interval)

    def _toggle_theme(self):
        if self._app:
            self._app.theme_manager.toggle_theme()

    def _show_about(self):
        QMessageBox.about(
            self, f"About {APP_NAME}",
            f"<h3>{APP_NAME} v{APP_VERSION}</h3>"
            f"<p>Extract frames from video files with ease.</p>"
            f"<p>Built with PySide6 &amp; OpenCV.</p>"
        )

    def _restore_geometry(self):
        geo = self._settings.window_geometry
        if geo:
            self.restoreGeometry(geo)
        state = self._settings.window_state
        if state:
            self.restoreState(state)

    def closeEvent(self, event):
        self._settings.window_geometry = self.saveGeometry()
        self._settings.window_state = self.saveState()

        if self.processor_thread and self.processor_thread.isRunning():
            self.processor_thread.stop()
            self.processor_thread.wait(3000)
        if self.export_thread and self.export_thread.isRunning():
            self.export_thread.stop()
            self.export_thread.wait(3000)

        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception:
            pass

        event.accept()