"""Export options dialog — format, quality, naming, resolution."""

import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QComboBox, QSlider, QSpinBox, QLineEdit,
    QPushButton, QFileDialog, QDialogButtonBox,
)
from PySide6.QtCore import Qt

from utils.settings import AppSettings
from utils.constants import DEFAULT_FILENAME_PATTERN


class ExportDialog(QDialog):
    """Let the user configure export format, quality, naming, and resolution before saving."""

    def __init__(self, frame_count: int, video_name: str = "", settings: AppSettings | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Options")
        self.setMinimumWidth(480)
        self._settings = settings or AppSettings()
        self._video_name = os.path.splitext(os.path.basename(video_name))[0] if video_name else "video"
        self._frame_count = frame_count

        self._build_ui()
        self._load_settings()
        self._update_preview()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        dir_layout = QHBoxLayout()
        self._txt_dir = QLineEdit()
        self._txt_dir.setPlaceholderText("Choose output directory...")
        self._txt_dir.setReadOnly(True)
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self._browse_dir)
        dir_layout.addWidget(QLabel("Folder:"))
        dir_layout.addWidget(self._txt_dir, stretch=1)
        dir_layout.addWidget(btn_browse)
        layout.addLayout(dir_layout)

        fmt_group = QGroupBox("Format")
        fmt_layout = QFormLayout(fmt_group)

        self._cmb_format = QComboBox()
        self._cmb_format.addItems(["PNG", "JPEG", "WebP", "BMP"])
        self._cmb_format.currentTextChanged.connect(self._on_format_changed)
        fmt_layout.addRow("Format:", self._cmb_format)

        self._sld_quality = QSlider(Qt.Horizontal)
        self._sld_quality.setRange(1, 100)
        self._sld_quality.setValue(95)
        self._lbl_quality_val = QLabel("95")
        self._sld_quality.valueChanged.connect(lambda v: self._lbl_quality_val.setText(str(v)))

        quality_row = QHBoxLayout()
        quality_row.addWidget(self._sld_quality, stretch=1)
        quality_row.addWidget(self._lbl_quality_val)
        self._quality_label = QLabel("Quality:")
        fmt_layout.addRow(self._quality_label, quality_row)

        layout.addWidget(fmt_group)

        res_group = QGroupBox("Resolution")
        res_layout = QFormLayout(res_group)

        self._cmb_scale = QComboBox()
        self._cmb_scale.addItems(["100% (Original)", "75%", "50%", "25%"])
        res_layout.addRow("Scale:", self._cmb_scale)

        layout.addWidget(res_group)

        name_group = QGroupBox("File Naming")
        name_layout = QFormLayout(name_group)

        self._txt_pattern = QLineEdit()
        self._txt_pattern.setPlaceholderText("frame_{time}_{index}")
        self._txt_pattern.textChanged.connect(self._update_preview)
        name_layout.addRow("Pattern:", self._txt_pattern)

        self._lbl_preview = QLabel()
        self._lbl_preview.setWordWrap(True)
        name_layout.addRow("Preview:", self._lbl_preview)

        hint = QLabel("Placeholders: {video}, {time}, {index}")
        hint.setStyleSheet("font-size: 11px; opacity: 0.7;")
        name_layout.addRow("", hint)

        layout.addWidget(name_group)

        self._lbl_summary = QLabel(f"Exporting {self._frame_count} frame(s)")
        layout.addWidget(self._lbl_summary)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._on_format_changed(self._cmb_format.currentText())

    def _browse_dir(self):
        start = self._settings.last_export_dir or ""
        d = QFileDialog.getExistingDirectory(self, "Select Export Directory", start)
        if d:
            self._txt_dir.setText(d)

    def _on_format_changed(self, fmt: str):
        needs_quality = fmt in ("JPEG", "WebP")
        self._sld_quality.setEnabled(needs_quality)
        self._quality_label.setEnabled(needs_quality)
        self._lbl_quality_val.setEnabled(needs_quality)
        self._update_preview()

    def _update_preview(self):
        pattern = self._txt_pattern.text() or DEFAULT_FILENAME_PATTERN
        ext_map = {"PNG": ".png", "JPEG": ".jpg", "WebP": ".webp", "BMP": ".bmp"}
        ext = ext_map.get(self._cmb_format.currentText(), ".png")
        try:
            example = pattern.format(video=self._video_name, time="00-05-30_0", index="0001")
        except (KeyError, IndexError, ValueError):
            example = pattern
        self._lbl_preview.setText(f"{example}{ext}")

    def _load_settings(self):
        self._cmb_format.setCurrentText(self._settings.export_format)
        self._sld_quality.setValue(self._settings.export_quality)
        self._txt_pattern.setText(self._settings.filename_pattern)
        if self._settings.last_export_dir:
            self._txt_dir.setText(self._settings.last_export_dir)

    def _save_settings(self):
        self._settings.export_format = self._cmb_format.currentText()
        self._settings.export_quality = self._sld_quality.value()
        self._settings.filename_pattern = self._txt_pattern.text() or DEFAULT_FILENAME_PATTERN
        if self._txt_dir.text():
            self._settings.last_export_dir = self._txt_dir.text()

    def _accept(self):
        if not self._txt_dir.text():
            self._browse_dir()
            if not self._txt_dir.text():
                return
        self._save_settings()
        self.accept()

    @property
    def output_dir(self) -> str:
        return self._txt_dir.text()

    @property
    def export_format(self) -> str:
        return self._cmb_format.currentText().upper()

    @property
    def quality(self) -> int:
        return self._sld_quality.value()

    @property
    def filename_pattern(self) -> str:
        return self._txt_pattern.text() or DEFAULT_FILENAME_PATTERN

    @property
    def scale_percent(self) -> int:
        text = self._cmb_scale.currentText()
        return int(text.split("%")[0])
