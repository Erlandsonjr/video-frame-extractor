import sys
import logging

from app import FrameExtractorApp
from main_window import MainWindow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main():
    app = FrameExtractorApp(sys.argv)

    window = MainWindow(app=app)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()