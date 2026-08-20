"""
main.py — entry point: AppContext init → MainWindow show.
"""
from __future__ import annotations

import logging
import sys

from core.paths import get_data_dir


def _setup_logging() -> None:
    log_dir = get_data_dir("logs")
    log_path = log_dir / "app.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def main() -> int:
    _setup_logging()
    import time
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication
    from app import AppContext
    from main_window import MainWindow
    from widgets.splash import SplashScreen

    app = QApplication(sys.argv)
    app.setApplicationName("ZZLUXORA")
    app.setApplicationVersion("8.5.0")
    app.setOrganizationName("zzluxora")

    # Splash screen 3 detik (feedback §2)
    splash = SplashScreen()
    splash.show()
    app.processEvents()

    ctx = AppContext()
    window = MainWindow(ctx)
    window.show()

    # Tutup splash setelah 3 detik (minimal durasi visual)
    def _finish_splash() -> None:
        if splash.isVisible():
            splash.finish(window)
    QTimer.singleShot(3000, _finish_splash)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
