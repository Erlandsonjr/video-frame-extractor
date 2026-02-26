"""Batch processing dialog — queue multiple videos for frame extraction."""

import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QFileDialog, QProgressBar, QLabel, QDoubleSpinBox, QMessageBox,
)
from PySide6.QtCore import Qt

from utils.constants import VIDEO_FILTER, DEFAULT_INTERVAL, MIN_INTERVAL, MAX_INTERVAL, INTERVAL_STEP, TEMP_DIR
from utils.settings import AppSettings
from processing.video_processor import VideoProcessor

import shutil


class BatchDialog(QDialog):
    """Dialog for queueing and processing multiple videos."""

    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Batch Processing")
        self.resize(700, 500)
        self.setMinimumSize(500, 350)
        self._settings = settings
        self._queue: list[dict] = []
        self._current_index = -1
        self._processor: VideoProcessor | None = None

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["Video File", "Interval (s)", "Status", "Frames"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self._table)

        btn_row = QHBoxLayout()

        btn_add = QPushButton("Add Videos...")
        btn_add.clicked.connect(self._add_videos)
        btn_row.addWidget(btn_add)

        btn_remove = QPushButton("Remove Selected")
        btn_remove.clicked.connect(self._remove_selected)
        btn_row.addWidget(btn_remove)

        btn_row.addStretch()

        btn_row.addWidget(QLabel("Default Interval:"))
        self._spn_interval = QDoubleSpinBox()
        self._spn_interval.setRange(MIN_INTERVAL, MAX_INTERVAL)
        self._spn_interval.setValue(self._settings.default_interval)
        self._spn_interval.setSingleStep(INTERVAL_STEP)
        self._spn_interval.setSuffix(" s")
        btn_row.addWidget(self._spn_interval)

        layout.addLayout(btn_row)

        self._progress = QProgressBar()
        self._progress.hide()
        layout.addWidget(self._progress)

        self._lbl_status = QLabel("")
        layout.addWidget(self._lbl_status)

        action_row = QHBoxLayout()
        action_row.addStretch()

        self._btn_start = QPushButton("Start Batch")
        self._btn_start.setObjectName("btn_process")
        self._btn_start.clicked.connect(self._start_batch)
        action_row.addWidget(self._btn_start)

        self._btn_cancel = QPushButton("Cancel")
        self._btn_cancel.setObjectName("btn_cancel")
        self._btn_cancel.clicked.connect(self._cancel_batch)
        self._btn_cancel.hide()
        action_row.addWidget(self._btn_cancel)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        action_row.addWidget(btn_close)

        layout.addLayout(action_row)

    def _add_videos(self):
        start_dir = self._settings.last_open_dir or ""
        files, _ = QFileDialog.getOpenFileNames(self, "Select Videos", start_dir, VIDEO_FILTER)
        if not files:
            return
        self._settings.last_open_dir = os.path.dirname(files[0])
        for f in files:
            self._add_to_queue(f)

    def _add_to_queue(self, path: str):
        row = self._table.rowCount()
        self._table.insertRow(row)

        self._table.setItem(row, 0, QTableWidgetItem(os.path.basename(path)))
        self._table.setItem(row, 1, QTableWidgetItem(str(self._spn_interval.value())))
        self._table.setItem(row, 2, QTableWidgetItem("Pending"))
        self._table.setItem(row, 3, QTableWidgetItem("0"))

        self._queue.append({
            "path": path,
            "interval": self._spn_interval.value(),
            "temp_dir": None,
            "frame_count": 0,
            "status": "pending",
        })

    def _remove_selected(self):
        rows = sorted(set(idx.row() for idx in self._table.selectedIndexes()), reverse=True)
        for row in rows:
            self._table.removeRow(row)
            self._queue.pop(row)

    def _start_batch(self):
        if not self._queue:
            QMessageBox.warning(self, "Empty Queue", "Add videos to the queue first.")
            return

        self._btn_start.setEnabled(False)
        self._btn_cancel.show()
        self._progress.show()
        self._progress.setValue(0)
        self._current_index = -1
        self._process_next()

    def _process_next(self):
        self._current_index += 1
        if self._current_index >= len(self._queue):
            self._on_batch_complete()
            return

        entry = self._queue[self._current_index]
        entry["temp_dir"] = os.path.join(TEMP_DIR, f"batch_{self._current_index}")
        os.makedirs(entry["temp_dir"], exist_ok=True)
        entry["status"] = "processing"
        self._table.item(self._current_index, 2).setText("Processing...")

        self._lbl_status.setText(
            f"Processing {self._current_index + 1}/{len(self._queue)}: "
            f"{os.path.basename(entry['path'])}"
        )

        self._processor = VideoProcessor(
            entry["path"], 0, 0, entry["interval"], entry["temp_dir"]
        )
        self._processor.frame_extracted.connect(self._on_frame)
        self._processor.progress_updated.connect(self._progress.setValue)
        self._processor.finished_processing.connect(self._on_video_done)
        self._processor.error_occurred.connect(self._on_video_error)
        self._processor.start()

    def _on_frame(self, qimg, path, ts):
        entry = self._queue[self._current_index]
        entry["frame_count"] += 1
        self._table.item(self._current_index, 3).setText(str(entry["frame_count"]))

    def _on_video_done(self):
        self._queue[self._current_index]["status"] = "done"
        self._table.item(self._current_index, 2).setText("Done ✓")
        self._process_next()

    def _on_video_error(self, msg: str):
        self._queue[self._current_index]["status"] = "error"
        self._table.item(self._current_index, 2).setText(f"Error")
        self._process_next()

    def _cancel_batch(self):
        if self._processor and self._processor.isRunning():
            self._processor.stop()
            self._processor.wait(3000)
        self._on_batch_complete(cancelled=True)

    def _on_batch_complete(self, cancelled=False):
        self._btn_start.setEnabled(True)
        self._btn_cancel.hide()
        self._progress.hide()

        done = sum(1 for e in self._queue if e["status"] == "done")
        total = len(self._queue)

        if cancelled:
            self._lbl_status.setText(f"Batch cancelled. {done}/{total} videos processed.")
        else:
            self._lbl_status.setText(f"Batch complete: {done}/{total} videos processed successfully.")

    def get_results(self) -> list[dict]:
        """Return the queue with temp_dir paths for frames that were extracted."""
        return [e for e in self._queue if e["status"] == "done" and e["temp_dir"]]

    def closeEvent(self, event):
        if self._processor and self._processor.isRunning():
            self._processor.stop()
            self._processor.wait(3000)
        for entry in self._queue:
            td = entry.get("temp_dir")
            if td and os.path.exists(td):
                shutil.rmtree(td, ignore_errors=True)
        super().closeEvent(event)
