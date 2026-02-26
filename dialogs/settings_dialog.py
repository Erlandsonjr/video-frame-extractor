"""Application settings dialog — theme, defaults, behavior."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QGroupBox,
    QComboBox, QDoubleSpinBox, QDialogButtonBox, QLabel,
)

from utils.settings import AppSettings
from utils.constants import MIN_INTERVAL, MAX_INTERVAL, INTERVAL_STEP


class SettingsDialog(QDialog):
    """Preferences dialog for theme, default interval, and other settings."""

    def __init__(self, settings: AppSettings, theme_callback=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(400)
        self._settings = settings
        self._theme_callback = theme_callback

        self._build_ui()
        self._load_current()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        appear_group = QGroupBox("Appearance")
        appear_layout = QFormLayout(appear_group)

        self._cmb_theme = QComboBox()
        self._cmb_theme.addItems(["dark", "light"])
        appear_layout.addRow("Theme:", self._cmb_theme)

        layout.addWidget(appear_group)

        proc_group = QGroupBox("Processing Defaults")
        proc_layout = QFormLayout(proc_group)

        self._spn_interval = QDoubleSpinBox()
        self._spn_interval.setRange(MIN_INTERVAL, MAX_INTERVAL)
        self._spn_interval.setSingleStep(INTERVAL_STEP)
        self._spn_interval.setSuffix(" sec")
        proc_layout.addRow("Default Interval:", self._spn_interval)

        layout.addWidget(proc_group)

        export_group = QGroupBox("Export Defaults")
        export_layout = QFormLayout(export_group)

        self._cmb_format = QComboBox()
        self._cmb_format.addItems(["PNG", "JPEG", "WebP", "BMP"])
        export_layout.addRow("Default Format:", self._cmb_format)

        layout.addWidget(export_group)

        info = QLabel("Settings are saved automatically when you click OK.")
        info.setStyleSheet("font-size: 11px; opacity: 0.7;")
        layout.addWidget(info)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._apply)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_current(self):
        self._cmb_theme.setCurrentText(self._settings.theme)
        self._spn_interval.setValue(self._settings.default_interval)
        self._cmb_format.setCurrentText(self._settings.export_format)

    def _apply(self):
        self._settings.default_interval = self._spn_interval.value()
        self._settings.export_format = self._cmb_format.currentText()

        new_theme = self._cmb_theme.currentText()
        if new_theme != self._settings.theme and self._theme_callback:
            self._theme_callback(new_theme)

        self.accept()
