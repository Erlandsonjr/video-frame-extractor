"""Application-wide constants."""

import os

APP_NAME = "Frame Extractor"
APP_VERSION = "2.0.0"
ORG_NAME = "FrameExtractorOrg"

VIDEO_EXTENSIONS = {
    ".mp4", ".avi", ".mkv", ".mov", ".webm", ".flv",
    ".wmv", ".m4v", ".mpg", ".mpeg", ".3gp", ".ts",
}

VIDEO_FILTER = "Videos (*.mp4 *.avi *.mkv *.mov *.webm *.flv *.wmv *.m4v *.mpg *.mpeg *.3gp *.ts)"

EXPORT_FORMATS = {
    "PNG": {"ext": ".png", "cv2_params": []},
    "JPEG": {"ext": ".jpg", "cv2_params_key": "cv2.IMWRITE_JPEG_QUALITY"},
    "WebP": {"ext": ".webp", "cv2_params_key": "cv2.IMWRITE_WEBP_QUALITY"},
    "BMP":  {"ext": ".bmp", "cv2_params": []},
}

DEFAULT_FILENAME_PATTERN = "frame_{time}_{index}"

THUMBNAIL_MAX_WIDTH = 400
THUMBNAIL_MAX_HEIGHT = 400

ZOOM_MIN = 100
ZOOM_MAX = 500
ZOOM_DEFAULT = 200

DEFAULT_INTERVAL = 1.0
MIN_INTERVAL = 0.1
MAX_INTERVAL = 3600.0
INTERVAL_STEP = 0.5

TEMP_DIR_PREFIX = "frame_extractor_"
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP_DIR = os.path.join(PROJECT_DIR, "temp_frames")
