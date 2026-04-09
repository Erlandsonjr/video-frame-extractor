import logging
import os
import shutil
import tempfile
import time

from utils.constants import TEMP_DIR_PREFIX

logger = logging.getLogger(__name__)

_MAX_AGE_SECONDS = 3600


def create_temp_dir() -> str:
    return tempfile.mkdtemp(prefix=TEMP_DIR_PREFIX)


def cleanup_orphaned_temp_dirs() -> None:
    base = tempfile.gettempdir()
    now = time.time()
    for name in os.listdir(base):
        if not name.startswith(TEMP_DIR_PREFIX):
            continue
        path = os.path.join(base, name)
        if not os.path.isdir(path):
            continue
        try:
            age = now - os.path.getmtime(path)
            if age > _MAX_AGE_SECONDS:
                shutil.rmtree(path, ignore_errors=True)
                logger.info("Cleaned orphaned temp dir: %s", path)
        except Exception:
            pass
