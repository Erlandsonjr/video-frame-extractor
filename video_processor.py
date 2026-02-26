import os
import cv2
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage

class VideoProcessor(QThread):
    frame_extracted = Signal(QImage, str, float)
    progress_updated = Signal(int)
    finished_processing = Signal()
    error_occurred = Signal(str)

    def __init__(self, video_path: str, start_sec: int, end_sec: int, interval_sec: float, temp_dir: str):
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
                self.error_occurred.emit("Start time must be less than end time.")
                cap.release()
                return

            self._process_frames(cap, actual_end_sec)

        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            if 'cap' in locals() and cap.isOpened():
                cap.release()

    def _calculate_actual_end_time(self, cap: cv2.VideoCapture) -> float:
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration_sec = total_frames / fps if fps > 0 else 0

        if self.end_sec == 0 or self.end_sec > duration_sec:
            return duration_sec
        return self.end_sec

    def _process_frames(self, cap: cv2.VideoCapture, end_sec: float):
        current_sec = self.start_sec
        total_steps = int((end_sec - self.start_sec) / self.interval_sec) + 1
        step = 0

        while current_sec <= end_sec and self._is_running:
            cap.set(cv2.CAP_PROP_POS_MSEC, current_sec * 1000.0)
            ret, frame = cap.read()
            
            if not ret:
                break

            safe_time_str = str(current_sec).replace(".", "_")
            temp_filename = f"temp_frame_{safe_time_str}.png"
            temp_filepath = os.path.join(self.temp_dir, temp_filename)
            cv2.imwrite(temp_filepath, frame)

            thumbnail_cv2 = cv2.resize(frame, (400, 300), interpolation=cv2.INTER_AREA)
            thumbnail_qimg = self._convert_cv2_to_qimage(thumbnail_cv2)

            self.frame_extracted.emit(thumbnail_qimg, temp_filepath, current_sec)

            step += 1
            self.progress_updated.emit(int((step / total_steps) * 100))
            current_sec += self.interval_sec

        self.finished_processing.emit()

    def _convert_cv2_to_qimage(self, frame) -> QImage:
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        return QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()

    def stop(self):
        self._is_running = False