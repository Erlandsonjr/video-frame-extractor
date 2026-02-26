"""Application class with theme management."""

import os
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal

from utils.constants import APP_NAME, ORG_NAME, APP_VERSION
from utils.settings import AppSettings


class ThemeManager(QObject):
    """Loads and applies QSS themes."""

    theme_changed = Signal(str)

    def __init__(self, app: QApplication, settings: AppSettings):
        super().__init__()
        self._app = app
        self._settings = settings
        self._styles_dir = os.path.join(os.path.dirname(__file__), "resources", "styles")

    @property
    def current_theme(self) -> str:
        return self._settings.theme

    def apply_theme(self, theme_name: str):
        """Apply a theme by name ('dark' or 'light')."""
        qss_path = os.path.join(self._styles_dir, f"{theme_name}.qss")
        if os.path.isfile(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                self._app.setStyleSheet(f.read())
        else:
            self._app.setStyleSheet("")
        self._settings.theme = theme_name
        self.theme_changed.emit(theme_name)

    def toggle_theme(self):
        """Switch between dark and light."""
        new_theme = "light" if self.current_theme == "dark" else "dark"
        self.apply_theme(new_theme)

    def apply_saved_theme(self):
        """Apply the theme stored in settings."""
        self.apply_theme(self.current_theme)


class FrameExtractorApp(QApplication):
    """Custom QApplication with settings and theme management."""

    def __init__(self, argv: list[str] | None = None):
        super().__init__(argv or sys.argv)

        self.setApplicationName(APP_NAME)
        self.setOrganizationName(ORG_NAME)
        self.setApplicationVersion(APP_VERSION)
        self.setStyle("Fusion")

        self.settings = AppSettings()
        self.theme_manager = ThemeManager(self, self.settings)
        self.theme_manager.apply_saved_theme()
