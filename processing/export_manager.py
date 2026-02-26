"""Threaded export manager supporting multiple formats, quality settings, and filename patterns."""

import os
import cv2
from PySide6.QtCore import QThread, Signal


class ExportManager(QThread):
    """Export frames to disk in a background thread with configurable format/quality.

    Signals:
        progress_updated(int): 0-100
        frame_exported(str): destination path of last exported frame
        finished(int, int): (success_count, total_count)
        error_occurred(str): error message
    """

    progress_updated = Signal(int)
    frame_exported = Signal(str)
    finished = Signal(int, int)
    error_occurred = Signal(str)

    def __init__(
        self,
        frames: list[tuple[str, str]],
        output_dir: str,
        video_name: str = "",
        fmt: str = "PNG",
        quality: int = 95,
        filename_pattern: str = "frame_{time}_{index}",
        scale_percent: int = 100,
    ):
        super().__init__()
        self._frames = frames
        self._output_dir = output_dir
        self._video_name = video_name
        self._fmt = fmt.upper()
        self._quality = quality
        self._pattern = filename_pattern
        self._scale_percent = scale_percent
        self._is_running = True

    def run(self):
        total = len(self._frames)
        if total == 0:
            self.finished.emit(0, 0)
            return

        ext_map = {"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp", "BMP": ".bmp"}
        ext = ext_map.get(self._fmt, ".png")

        success = 0
        for i, (time_str, temp_filepath) in enumerate(self._frames):
            if not self._is_running:
                break

            try:
                safe_time = time_str.replace(":", "-").replace(".", "_")
                filename = self._pattern.format(
                    video=self._video_name,
                    time=safe_time,
                    index=f"{i + 1:04d}",
                )
                dest_path = os.path.join(self._output_dir, f"{filename}{ext}")

                frame = cv2.imread(temp_filepath, cv2.IMREAD_UNCHANGED)
                if frame is None:
                    continue

                if self._scale_percent != 100:
                    scale = self._scale_percent / 100.0
                    new_w = max(int(frame.shape[1] * scale), 1)
                    new_h = max(int(frame.shape[0] * scale), 1)
                    frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

                params = self._get_write_params()
                cv2.imwrite(dest_path, frame, params)

                success += 1
                self.frame_exported.emit(dest_path)

            except Exception as e:
                self.error_occurred.emit(f"Frame {i + 1}: {e}")

            progress = min(int(((i + 1) / total) * 100), 100)
            self.progress_updated.emit(progress)

        self.finished.emit(success, total)

    def _get_write_params(self) -> list:
        if self._fmt == "JPEG":
            return [cv2.IMWRITE_JPEG_QUALITY, self._quality]
        elif self._fmt == "WEBP":
            return [cv2.IMWRITE_WEBP_QUALITY, self._quality]
        return []

    def stop(self):
        self._is_running = False
