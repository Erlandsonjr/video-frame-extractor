import os
import shutil
import tempfile
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QDoubleSpinBox, QListWidget, QListWidgetItem,
    QAbstractItemView, QTimeEdit, QProgressBar, QMessageBox, QStyle, QSlider
)
from PySide6.QtCore import Qt, QTime, QSize
from PySide6.QtGui import QPixmap, QIcon

from widgets import DropLabel
from video_processor import VideoProcessor

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Frame Extractor")
        self.resize(900, 700)
        
        self.video_path = None
        self.processor_thread = None
        self.temp_storage = tempfile.TemporaryDirectory()
        
        self._setup_ui()

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self._build_file_input_section(main_layout)
        self._build_controls_section(main_layout)
        self._build_progress_bar(main_layout)
        self._build_zoom_section(main_layout)
        self._build_gallery_section(main_layout)
        self._build_export_section(main_layout)

    def _build_file_input_section(self, parent_layout):
        layout = QHBoxLayout()
        
        self.drop_label = DropLabel()
        self.drop_label.file_dropped.connect(self.load_video)
        
        btn_browse = QPushButton("Browse File")
        btn_browse.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        btn_browse.setMinimumHeight(40)
        btn_browse.clicked.connect(self._browse_file)
        
        layout.addWidget(self.drop_label, stretch=3)
        layout.addWidget(btn_browse, stretch=1)
        parent_layout.addLayout(layout)

    def _build_controls_section(self, parent_layout):
        layout = QHBoxLayout()
        
        layout.addWidget(QLabel("Start:"))
        self.time_start = QTimeEdit()
        self.time_start.setDisplayFormat("HH:mm:ss")
        self.time_start.setTime(QTime(0, 0, 0))
        layout.addWidget(self.time_start)

        layout.addWidget(QLabel("End:"))
        self.time_end = QTimeEdit()
        self.time_end.setDisplayFormat("HH:mm:ss")
        self.time_end.setTime(QTime(0, 0, 0))
        self.time_end.setToolTip("Leave 00:00:00 to process until the end.")
        layout.addWidget(self.time_end)

        layout.addWidget(QLabel("Interval (sec):"))
        self.spin_interval = QDoubleSpinBox()
        self.spin_interval.setRange(0.1, 3600.0)
        self.spin_interval.setValue(1.0)
        self.spin_interval.setSingleStep(0.5)
        layout.addWidget(self.spin_interval)

        self.btn_process = QPushButton("Process Video")
        self.btn_process.setMinimumHeight(35)
        self.btn_process.clicked.connect(self._start_processing)
        layout.addWidget(self.btn_process)

        parent_layout.addLayout(layout)

    def _build_progress_bar(self, parent_layout):
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        parent_layout.addWidget(self.progress_bar)

    def _build_zoom_section(self, parent_layout):
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Thumbnail Size:"))
        
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(100, 400)
        self.zoom_slider.setValue(200)
        self.zoom_slider.valueChanged.connect(self._update_thumbnail_size)
        
        layout.addWidget(self.zoom_slider)
        parent_layout.addLayout(layout)

    def _build_gallery_section(self, parent_layout):
        self.gallery = QListWidget()
        self.gallery.setViewMode(QListWidget.IconMode)
        self.gallery.setResizeMode(QListWidget.Adjust)
        self.gallery.setSpacing(10)
        self.gallery.setSelectionMode(QAbstractItemView.MultiSelection)
        self.gallery.setStyleSheet("""
            QListWidget::item:selected {
                background-color: #0078d7;
                border: 2px solid #005a9e;
                border-radius: 5px;
            }
        """)
        parent_layout.addWidget(self.gallery)
        
        self._update_thumbnail_size(self.zoom_slider.value())

    def _update_thumbnail_size(self, width: int):
        height = int(width * 0.75)  
        self.gallery.setIconSize(QSize(width, height))
        self.gallery.setGridSize(QSize(width + 20, height + 40))

    def _build_export_section(self, parent_layout):
        layout = QHBoxLayout()
        
        btn_select_all = QPushButton("Select All")
        btn_select_all.clicked.connect(self.gallery.selectAll)
        layout.addWidget(btn_select_all)

        btn_clear_selection = QPushButton("Clear Selection")
        btn_clear_selection.clicked.connect(self.gallery.clearSelection)
        layout.addWidget(btn_clear_selection)

        layout.addStretch()

        btn_save = QPushButton("Save Selected Frames")
        btn_save.setMinimumHeight(40)
        btn_save.setStyleSheet("background-color: #28a745; color: white; font-weight: bold;")
        btn_save.clicked.connect(self._save_frames)
        layout.addWidget(btn_save)

        parent_layout.addLayout(layout)

    def _browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Video", "", "Videos (*.mp4 *.avi *.mkv *.mov)"
        )
        if file_path:
            self.load_video(file_path)

    def load_video(self, file_path: str):
        self.video_path = file_path
        self.drop_label.setText(f"Video Loaded:\n{os.path.basename(file_path)}")
        self.gallery.clear()

    def _time_to_seconds(self, qtime: QTime) -> int:
        return qtime.hour() * 3600 + qtime.minute() * 60 + qtime.second()

    def _start_processing(self):
        if not self.video_path:
            QMessageBox.warning(self, "Warning", "Please select a video file first.")
            return

        self._reset_ui_for_processing()

        start_sec = self._time_to_seconds(self.time_start.time())
        end_sec = self._time_to_seconds(self.time_end.time())
        interval = self.spin_interval.value()

        self.processor_thread = VideoProcessor(
            self.video_path, start_sec, end_sec, interval, self.temp_storage.name
        )
        self._connect_thread_signals()
        self.processor_thread.start()

    def _reset_ui_for_processing(self):
        self.gallery.clear()
        self.btn_process.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.show()

    def _connect_thread_signals(self):
        self.processor_thread.frame_extracted.connect(self._add_frame_to_gallery)
        self.processor_thread.progress_updated.connect(self.progress_bar.setValue)
        self.processor_thread.finished_processing.connect(self._on_processing_finished)
        self.processor_thread.error_occurred.connect(self._on_processing_error)

    def _add_frame_to_gallery(self, thumbnail_qimg, temp_filepath: str, timestamp: float):
        time_str = self._format_timestamp(timestamp)
        
        item = QListWidgetItem()
        pixmap = QPixmap.fromImage(thumbnail_qimg)
        
        item.setIcon(QIcon(pixmap))
        item.setText(time_str)
        item.setTextAlignment(Qt.AlignCenter)
        
        item.setData(Qt.UserRole, (time_str, temp_filepath))
        self.gallery.addItem(item)

    def _format_timestamp(self, seconds_total: float) -> str:
        hours = int(seconds_total // 3600)
        minutes = int((seconds_total % 3600) // 60)
        seconds = seconds_total % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:04.1f}"

    def _on_processing_finished(self):
        self._restore_ui_after_processing()
        QMessageBox.information(self, "Done", "Frame extraction completed successfully.")

    def _on_processing_error(self, error_msg: str):
        self._restore_ui_after_processing()
        QMessageBox.critical(self, "Error", f"Processing failed:\n{error_msg}")

    def _restore_ui_after_processing(self):
        self.btn_process.setEnabled(True)
        self.progress_bar.hide()

    def _save_frames(self):
        selected_items = self.gallery.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "No frames selected for export.")
            return

        save_dir = QFileDialog.getExistingDirectory(self, "Select Destination Directory")
        if not save_dir:
            return

        saved_count = self._export_selected_images(selected_items, save_dir)
        QMessageBox.information(self, "Export Complete", f"Successfully saved {saved_count} frames.")

    def _export_selected_images(self, items: list, directory: str) -> int:
        saved_count = 0
        for item in items:
            time_str, temp_filepath = item.data(Qt.UserRole)
            safe_name = time_str.replace(":", "-").replace(".", "_")
            dest_filepath = os.path.join(directory, f"frame_{safe_name}.png")
            
            try:
                shutil.copy2(temp_filepath, dest_filepath)
                saved_count += 1
            except Exception as e:
                print(f"Error copying {temp_filepath}: {e}")
                
        return saved_count

    def closeEvent(self, event):
        if self.processor_thread and self.processor_thread.isRunning():
            self.processor_thread.stop()
            self.processor_thread.wait()
            
        try:
            self.temp_storage.cleanup()
        except Exception:
            pass
            
        event.accept()