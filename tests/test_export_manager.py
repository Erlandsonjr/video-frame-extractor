import os
import cv2
import numpy as np
import pytest
from PySide6.QtCore import QCoreApplication

from processing.export_manager import ExportManager


@pytest.fixture(autouse=True)
def _ensure_qapp():
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    yield


@pytest.fixture()
def sample_frames(tmp_path):
    frames = []
    for i in range(3):
        frame_path = str(tmp_path / f"frame_{i}.png")
        img = np.full((100, 160, 3), (i * 80, 255 - i * 80, 128), dtype=np.uint8)
        cv2.imwrite(frame_path, img)
        frames.append((f"00:00:0{i}.0", frame_path))
    return frames


class TestExportManager:

    @pytest.mark.parametrize("fmt,ext", [
        ("PNG", ".png"),
        ("JPEG", ".jpg"),
        ("WEBP", ".webp"),
        ("BMP", ".bmp"),
    ])
    def test_export_formats(self, sample_frames, tmp_output_dir, fmt, ext):
        results = {"success": 0, "total": 0}
        em = ExportManager(
            frames=sample_frames,
            output_dir=tmp_output_dir,
            video_name="test",
            fmt=fmt,
        )
        em.finished.connect(lambda s, t: results.update(success=s, total=t))
        em.run()

        assert results["success"] == 3
        exported = [f for f in os.listdir(tmp_output_dir) if f.endswith(ext)]
        assert len(exported) == 3

    def test_export_with_scaling(self, sample_frames, tmp_output_dir):
        em = ExportManager(
            frames=sample_frames,
            output_dir=tmp_output_dir,
            video_name="test",
            fmt="PNG",
            scale_percent=50,
        )
        em.run()

        exported = [f for f in os.listdir(tmp_output_dir) if f.endswith(".png")]
        assert len(exported) == 3
        img = cv2.imread(os.path.join(tmp_output_dir, exported[0]))
        assert img.shape[1] == 80
        assert img.shape[0] == 50

    def test_filename_pattern(self, sample_frames, tmp_output_dir):
        em = ExportManager(
            frames=sample_frames,
            output_dir=tmp_output_dir,
            video_name="myvideo",
            fmt="PNG",
            filename_pattern="{video}_f{index}",
        )
        em.run()

        files = sorted(os.listdir(tmp_output_dir))
        assert files[0] == "myvideo_f0001.png"

    def test_missing_source_frame(self, tmp_output_dir):
        bad_frames = [("00:00:00.0", "/nonexistent/frame.png")]
        results = {"success": 0, "total": 0}
        em = ExportManager(
            frames=bad_frames,
            output_dir=tmp_output_dir,
            video_name="test",
            fmt="PNG",
        )
        em.finished.connect(lambda s, t: results.update(success=s, total=t))
        em.run()

        assert results["success"] == 0
        assert results["total"] == 1

    def test_colliding_pattern_produces_unique_files(self, sample_frames, tmp_output_dir):
        # A pattern with no {index}/{time} would map every frame to the same
        # name; the manager must suffix duplicates instead of overwriting.
        results = {"success": 0, "total": 0}
        em = ExportManager(
            frames=sample_frames,
            output_dir=tmp_output_dir,
            video_name="clip",
            fmt="PNG",
            filename_pattern="{video}",
        )
        em.finished.connect(lambda s, t: results.update(success=s, total=t))
        em.run()

        assert results["success"] == 3
        files = sorted(os.listdir(tmp_output_dir))
        assert files == ["clip.png", "clip_1.png", "clip_2.png"]

    def test_avoids_overwriting_existing_file(self, sample_frames, tmp_output_dir):
        existing = os.path.join(tmp_output_dir, "clip.png")
        with open(existing, "wb") as f:
            f.write(b"sentinel")

        em = ExportManager(
            frames=sample_frames[:1],
            output_dir=tmp_output_dir,
            video_name="clip",
            fmt="PNG",
            filename_pattern="{video}",
        )
        em.run()

        # The pre-existing file is untouched; the export lands beside it.
        with open(existing, "rb") as f:
            assert f.read() == b"sentinel"
        assert os.path.exists(os.path.join(tmp_output_dir, "clip_1.png"))

    def test_stop_cancels_export(self, sample_frames, tmp_output_dir):
        em = ExportManager(
            frames=sample_frames,
            output_dir=tmp_output_dir,
            video_name="test",
            fmt="PNG",
        )
        em.stop()
        results = {"success": 0, "total": 0}
        em.finished.connect(lambda s, t: results.update(success=s, total=t))
        em.run()

        assert results["success"] == 0
