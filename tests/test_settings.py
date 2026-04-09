import pytest
from PySide6.QtCore import QCoreApplication


@pytest.fixture(autouse=True)
def _ensure_qapp():
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    yield


class TestAppSettings:

    def test_default_values(self, settings):
        assert settings.theme == "dark"
        assert settings.default_interval == 1.0
        assert settings.export_format == "PNG"
        assert settings.export_quality == 95
        assert settings.thumbnail_size == 200

    def test_roundtrip_theme(self, settings):
        settings.theme = "light"
        assert settings.theme == "light"
        settings.theme = "dark"
        assert settings.theme == "dark"

    def test_roundtrip_interval(self, settings):
        settings.default_interval = 2.5
        assert settings.default_interval == 2.5

    def test_roundtrip_export_format(self, settings):
        settings.export_format = "JPEG"
        assert settings.export_format == "JPEG"

    def test_roundtrip_quality(self, settings):
        settings.export_quality = 42
        assert settings.export_quality == 42

    def test_roundtrip_filename_pattern(self, settings):
        settings.filename_pattern = "{video}_{index}"
        assert settings.filename_pattern == "{video}_{index}"

    def test_roundtrip_paths(self, settings):
        settings.last_open_dir = "/some/path"
        assert settings.last_open_dir == "/some/path"
        settings.last_export_dir = "/export/path"
        assert settings.last_export_dir == "/export/path"

    def test_roundtrip_thumbnail_size(self, settings):
        settings.thumbnail_size = 350
        assert settings.thumbnail_size == 350

    def test_persistence_across_instances(self, tmp_path):
        from PySide6.QtCore import QSettings
        from utils.settings import AppSettings

        ini_path = str(tmp_path / "shared.ini")
        s1 = AppSettings()
        s1._s = QSettings(ini_path, QSettings.IniFormat)
        s1.theme = "light"
        s1._s.sync()

        s2 = AppSettings()
        s2._s = QSettings(ini_path, QSettings.IniFormat)
        assert s2.theme == "light"
