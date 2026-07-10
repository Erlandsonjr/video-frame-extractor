import os
import cv2
from PySide6.QtCore import QThread, Signal

from utils.constants import EXPORT_FORMATS


class ExportManager(QThread):
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
        self._fmt = fmt
        self._quality = quality
        self._pattern = filename_pattern
        self._scale_percent = scale_percent
        self._is_running = True

    @staticmethod
    def _resolve_format(fmt: str) -> dict:
        upper = fmt.upper()
        for key, val in EXPORT_FORMATS.items():
            if key.upper() == upper:
                return val
        return EXPORT_FORMATS["PNG"]

    def run(self):
        total = len(self._frames)
        if total == 0:
            self.finished.emit(0, 0)
            return

        fmt_info = self._resolve_format(self._fmt)
        ext = fmt_info["ext"]

        used_paths: set[str] = set()
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
                dest_path = self._unique_path(filename, ext, used_paths)

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

    def _unique_path(self, filename: str, ext: str, used_paths: set[str]) -> str:
        """Build a destination path that doesn't clash with an existing file or
        an earlier frame in this same export (e.g. patterns without ``{index}``)."""
        candidate = os.path.join(self._output_dir, f"{filename}{ext}")
        if candidate not in used_paths and not os.path.exists(candidate):
            used_paths.add(candidate)
            return candidate

        counter = 1
        while True:
            candidate = os.path.join(self._output_dir, f"{filename}_{counter}{ext}")
            if candidate not in used_paths and not os.path.exists(candidate):
                used_paths.add(candidate)
                return candidate
            counter += 1

    def _get_write_params(self) -> list:
        fmt_info = self._resolve_format(self._fmt)
        cv2_params = fmt_info["cv2_params"]
        if cv2_params:
            return [cv2_params[0], self._quality]
        return []

    def stop(self):
        self._is_running = False
