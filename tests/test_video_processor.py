import os
import re
import pytest
from PySide6.QtCore import QCoreApplication

from processing.video_processor import VideoProcessor


@pytest.fixture(autouse=True)
def _ensure_qapp():
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    yield


class TestVideoProcessor:

    def test_extracts_expected_frame_count(self, tmp_video, tmp_path):
        temp_dir = str(tmp_path / "frames")
        os.makedirs(temp_dir)

        extracted = []
        proc = VideoProcessor(tmp_video, 0, 0, 0.1, temp_dir)
        proc.frame_extracted.connect(lambda _img, path, ts: extracted.append(path))

        proc.run()

        assert len(extracted) > 0
        for p in extracted:
            assert os.path.isfile(p)

    def test_temp_filenames_are_indexed_and_unique(self, tmp_video, tmp_path):
        temp_dir = str(tmp_path / "frames")
        os.makedirs(temp_dir)

        paths = []
        proc = VideoProcessor(tmp_video, 0, 0, 0.1, temp_dir)
        proc.frame_extracted.connect(lambda _img, path, ts: paths.append(path))

        proc.run()

        names = [os.path.basename(p) for p in paths]
        assert len(names) == len(set(names))  # no collisions
        assert all(re.fullmatch(r"temp_frame_\d{6}\.png", n) for n in names)

    def test_start_end_range(self, tmp_video, tmp_path):
        temp_dir = str(tmp_path / "frames")
        os.makedirs(temp_dir)

        errors = []
        proc = VideoProcessor(tmp_video, 999, 0, 1.0, temp_dir)
        proc.error_occurred.connect(errors.append)

        proc.run()

        assert len(errors) == 1

    def test_stop_cancels_processing(self, tmp_video, tmp_path):
        temp_dir = str(tmp_path / "frames")
        os.makedirs(temp_dir)

        finished = []
        proc = VideoProcessor(tmp_video, 0, 0, 0.01, temp_dir)
        proc.finished_processing.connect(lambda: finished.append(True))
        proc.stop()

        proc.run()

        assert len(finished) == 0

    def test_invalid_video_path(self, tmp_path):
        temp_dir = str(tmp_path / "frames")
        os.makedirs(temp_dir)

        errors = []
        proc = VideoProcessor("/nonexistent/video.mp4", 0, 0, 1.0, temp_dir)
        proc.error_occurred.connect(errors.append)

        proc.run()

        assert len(errors) == 1
        assert "Could not open" in errors[0]
