"""Typed wrapper around QSettings for persistent user preferences."""

from PySide6.QtCore import QSettings
from utils.constants import (
    APP_NAME, ORG_NAME, ZOOM_DEFAULT, DEFAULT_INTERVAL, DEFAULT_FILENAME_PATTERN,
)


class AppSettings:
    """Read/write application settings backed by QSettings (registry on Windows, INI elsewhere)."""

    def __init__(self):
        self._s = QSettings(ORG_NAME, APP_NAME)

    @property
    def theme(self) -> str:
        return self._s.value("appearance/theme", "dark")

    @theme.setter
    def theme(self, value: str):
        self._s.setValue("appearance/theme", value)

    @property
    def last_open_dir(self) -> str:
        return self._s.value("paths/last_open_dir", "")

    @last_open_dir.setter
    def last_open_dir(self, value: str):
        self._s.setValue("paths/last_open_dir", value)

    @property
    def last_export_dir(self) -> str:
        return self._s.value("paths/last_export_dir", "")

    @last_export_dir.setter
    def last_export_dir(self, value: str):
        self._s.setValue("paths/last_export_dir", value)

    @property
    def default_interval(self) -> float:
        return float(self._s.value("processing/interval", DEFAULT_INTERVAL))

    @default_interval.setter
    def default_interval(self, value: float):
        self._s.setValue("processing/interval", value)

    @property
    def export_format(self) -> str:
        return self._s.value("export/format", "PNG")

    @export_format.setter
    def export_format(self, value: str):
        self._s.setValue("export/format", value)

    @property
    def export_quality(self) -> int:
        return int(self._s.value("export/quality", 95))

    @export_quality.setter
    def export_quality(self, value: int):
        self._s.setValue("export/quality", value)

    @property
    def filename_pattern(self) -> str:
        return self._s.value("export/filename_pattern", DEFAULT_FILENAME_PATTERN)

    @filename_pattern.setter
    def filename_pattern(self, value: str):
        self._s.setValue("export/filename_pattern", value)

    @property
    def thumbnail_size(self) -> int:
        return int(self._s.value("gallery/thumbnail_size", ZOOM_DEFAULT))

    @thumbnail_size.setter
    def thumbnail_size(self, value: int):
        self._s.setValue("gallery/thumbnail_size", value)

    @property
    def window_geometry(self) -> bytes | None:
        return self._s.value("window/geometry", None)

    @window_geometry.setter
    def window_geometry(self, value: bytes):
        self._s.setValue("window/geometry", value)

    @property
    def window_state(self) -> bytes | None:
        return self._s.value("window/state", None)

    @window_state.setter
    def window_state(self, value: bytes):
        self._s.setValue("window/state", value)
