"""Voice Ledger — 앱 진입점"""
import logging
import os
import sys


def setup_logging() -> None:
    """로그 디렉토리 생성 및 파일 핸들러 설정."""
    log_dir = os.path.expanduser("~/Library/Logs/VoiceLedger")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "voice_ledger.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Voice Ledger 시작")

    from PyQt6.QtWidgets import QApplication
    from src.ui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("Voice Ledger")
    app.setApplicationVersion("1.0.0")

    def handle_exception(exc_type, exc_value, exc_traceback):
        logger.critical("미처리 예외", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
