import cv2

APP_NAME = "Frame Extractor"
APP_VERSION = "2.1.0"
ORG_NAME = "FrameExtractorOrg"

VIDEO_EXTENSIONS = {
    ".mp4", ".avi", ".mkv", ".mov", ".webm", ".flv",
    ".wmv", ".m4v", ".mpg", ".mpeg", ".3gp", ".ts",
}

VIDEO_FILTER = "Videos (*.mp4 *.avi *.mkv *.mov *.webm *.flv *.wmv *.m4v *.mpg *.mpeg *.3gp *.ts)"

EXPORT_FORMATS = {
    "PNG":  {"ext": ".png",  "cv2_params": []},
    "JPEG": {"ext": ".jpg",  "cv2_params": [cv2.IMWRITE_JPEG_QUALITY]},
    "WebP": {"ext": ".webp", "cv2_params": [cv2.IMWRITE_WEBP_QUALITY]},
    "BMP":  {"ext": ".bmp",  "cv2_params": []},
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

SEQUENTIAL_READ_THRESHOLD = 30

# Extracting beyond this many frames builds that many thumbnails/widgets and can
# use a lot of memory, so the UI asks the user to confirm first.
LARGE_EXTRACTION_WARNING = 2000
