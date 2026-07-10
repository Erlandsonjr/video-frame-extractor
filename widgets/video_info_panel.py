import cv2
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel
from PySide6.QtCore import Qt

from utils.timecode import seconds_to_hms


class VideoInfoPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("video_info_panel")
        self.setFixedHeight(44)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)

        self._lbl_resolution = self._make_label("Resolution: —")
        self._lbl_fps = self._make_label("FPS: —")
        self._lbl_duration = self._make_label("Duration: —")
        self._lbl_codec = self._make_label("Codec: —")

        for lbl in (self._lbl_resolution, self._lbl_fps, self._lbl_duration, self._lbl_codec):
            layout.addWidget(lbl)
            layout.addStretch()

        layout.takeAt(layout.count() - 1)

        self.hide()

    @staticmethod
    def _make_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignCenter)
        return lbl

    @staticmethod
    def _fourcc_to_str(code: float) -> str:
        code = int(code)
        chars = [chr((code >> 8 * i) & 0xFF) for i in range(4)]
        s = "".join(chars).strip()
        return s if s else "Unknown"

    def load_video_info(self, path: str) -> dict:
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            self.hide()
            return {}

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fourcc = cap.get(cv2.CAP_PROP_FOURCC)
        cap.release()

        duration = total_frames / fps if fps > 0 else 0
        codec_str = self._fourcc_to_str(fourcc)
        aspect = width / height if height > 0 else 16 / 9

        self._lbl_resolution.setText(f"Resolution: {width}×{height}")
        self._lbl_fps.setText(f"FPS: {fps:.2f}")
        self._lbl_duration.setText(f"Duration: {seconds_to_hms(duration, decimals=2)}")
        self._lbl_codec.setText(f"Codec: {codec_str}")

        self.show()

        return {
            "width": width,
            "height": height,
            "fps": fps,
            "duration": duration,
            "codec": codec_str,
            "aspect_ratio": aspect,
        }

    def clear_info(self):
        self._lbl_resolution.setText("Resolution: —")
        self._lbl_fps.setText("FPS: —")
        self._lbl_duration.setText("Duration: —")
        self._lbl_codec.setText("Codec: —")
        self.hide()
