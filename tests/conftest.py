import cv2
import numpy as np
import pytest

from utils.settings import AppSettings


@pytest.fixture()
def tmp_video(tmp_path):
    video_path = str(tmp_path / "test_video.avi")
    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    fps = 30.0
    width, height = 640, 480
    writer = cv2.VideoWriter(video_path, fourcc, fps, (width, height))

    colours = [
        (0, 0, 255), (0, 255, 0), (255, 0, 0),
        (255, 255, 0), (0, 255, 255), (255, 0, 255),
        (128, 128, 0), (0, 128, 128), (128, 0, 128),
        (64, 64, 64),
    ]

    for colour in colours:
        frame = np.full((height, width, 3), colour, dtype=np.uint8)
        writer.write(frame)

    writer.release()
    return video_path


@pytest.fixture()
def tmp_output_dir(tmp_path):
    out = tmp_path / "output"
    out.mkdir()
    return str(out)


@pytest.fixture()
def settings(tmp_path):
    from PySide6.QtCore import QSettings

    QSettings.setDefaultFormat(QSettings.IniFormat)
    ini_path = str(tmp_path / "test_settings.ini")
    s = AppSettings()
    s._s = QSettings(ini_path, QSettings.IniFormat)
    return s
