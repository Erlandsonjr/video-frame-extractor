import logging
import os
import cv2
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage

from utils.constants import THUMBNAIL_MAX_WIDTH, THUMBNAIL_MAX_HEIGHT, SEQUENTIAL_READ_THRESHOLD

logger = logging.getLogger(__name__)


class VideoProcessor(QThread):
    frame_extracted = Signal(QImage, str, float)
    progress_updated = Signal(int)
    finished_processing = Signal()
    error_occurred = Signal(str)

    def __init__(
        self,
        video_path: str,
        start_sec: float,
        end_sec: float,
        interval_sec: float,
        temp_dir: str,
    ):
        super().__init__()
        self.video_path = video_path
        self.start_sec = start_sec
        self.end_sec = end_sec
        self.interval_sec = interval_sec
        self.temp_dir = temp_dir
        self._is_running = True

    def run(self):
        try:
            cap = cv2.VideoCapture(self.video_path)
            if not cap.isOpened():
                self.error_occurred.emit("Could not open the video file.")
                return

            actual_end_sec = self._calculate_actual_end_time(cap)

            if self.start_sec >= actual_end_sec:
                self.error_occurred.emit("Start time must be less than end time / video duration.")
                cap.release()
                return

            self._process_frames(cap, actual_end_sec)

        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            if "cap" in locals() and cap.isOpened():
                cap.release()

    def _calculate_actual_end_time(self, cap: cv2.VideoCapture) -> float:
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration_sec = total_frames / fps if fps > 0 else 0

        if self.end_sec == 0 or self.end_sec > duration_sec:
            return duration_sec
        return self.end_sec

    def _process_frames(self, cap: cv2.VideoCapture, end_sec: float):
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_gap = self.interval_sec * fps if fps > 0 else float("inf")
        use_sequential = frame_gap <= SEQUENTIAL_READ_THRESHOLD and fps > 0

        current_sec = self.start_sec
        total_steps = max(int((end_sec - self.start_sec) / self.interval_sec) + 1, 1)
        step = 0

        if use_sequential:
            self._process_sequential(cap, end_sec, fps, total_steps)
        else:
            self._process_seek(cap, end_sec, total_steps)

    def _process_seek(self, cap: cv2.VideoCapture, end_sec: float, total_steps: int):
        current_sec = self.start_sec
        step = 0

        while current_sec <= end_sec and self._is_running:
            cap.set(cv2.CAP_PROP_POS_MSEC, current_sec * 1000.0)
            ret, frame = cap.read()

            if not ret:
                break

            actual_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
            if abs(actual_ms - current_sec * 1000.0) > 500:
                logger.debug(
                    "Seek drift: requested %.1fs, got %.1fs",
                    current_sec, actual_ms / 1000.0,
                )

            self._emit_frame(frame, current_sec)

            step += 1
            progress = min(int((step / total_steps) * 100), 100)
            self.progress_updated.emit(progress)
            current_sec += self.interval_sec

        if self._is_running:
            self.finished_processing.emit()

    def _process_sequential(self, cap: cv2.VideoCapture, end_sec: float, fps: float, total_steps: int):
        frames_per_interval = max(int(round(self.interval_sec * fps)), 1)
        start_frame = int(round(self.start_sec * fps))
        end_frame = int(round(end_sec * fps))

        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        current_frame = start_frame
        step = 0

        while current_frame <= end_frame and self._is_running:
            ret = cap.grab()
            if not ret:
                break

            if (current_frame - start_frame) % frames_per_interval == 0:
                ret, frame = cap.retrieve()
                if not ret:
                    break

                timestamp = current_frame / fps
                self._emit_frame(frame, timestamp)

                step += 1
                progress = min(int((step / total_steps) * 100), 100)
                self.progress_updated.emit(progress)

            current_frame += 1

        if self._is_running:
            self.finished_processing.emit()

    def _emit_frame(self, frame, timestamp: float):
        safe_time_str = str(timestamp).replace(".", "_")
        temp_filename = f"temp_frame_{safe_time_str}.png"
        temp_filepath = os.path.join(self.temp_dir, temp_filename)
        cv2.imwrite(temp_filepath, frame)

        thumbnail_cv2 = self._make_thumbnail(frame)
        thumbnail_qimg = self._convert_cv2_to_qimage(thumbnail_cv2)

        self.frame_extracted.emit(thumbnail_qimg, temp_filepath, timestamp)

    @staticmethod
    def _make_thumbnail(frame) -> any:
        h, w = frame.shape[:2]
        if w == 0 or h == 0:
            return frame

        scale = min(THUMBNAIL_MAX_WIDTH / w, THUMBNAIL_MAX_HEIGHT / h)
        new_w = max(int(w * scale), 1)
        new_h = max(int(h * scale), 1)
        return cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

    @staticmethod
    def _convert_cv2_to_qimage(frame) -> QImage:
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        return QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()

    def stop(self):
        self._is_running = False
