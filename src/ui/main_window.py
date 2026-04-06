"""Voice Ledger 메인 창 — PyQt6 기반"""
from __future__ import annotations
import logging
import os
from typing import Optional

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QProgressBar, QMessageBox, QFileDialog,
)

from src.engine import run_transcription
from src.engine.cancellation import CancellationToken
from src.engine.whisper_runner import WhisperRunner
from src.ui.drop_zone import DropZone, DropZoneState
from src.ui.styles import Palette

logger = logging.getLogger(__name__)


class TranscriptionWorker(QThread):
    """Engine run_transcription()을 QThread에서 실행하는 워커."""

    progress = pyqtSignal(int)      # 0-100
    finished = pyqtSignal(str)      # 출력 파일 경로
    cancelled = pyqtSignal()
    error = pyqtSignal(str)         # 에러 메시지

    def __init__(self, input_path: str, overwrite: bool = False) -> None:
        super().__init__()
        self.input_path = input_path
        self.overwrite = overwrite
        self._cancel_token = CancellationToken()

    def run(self) -> None:
        try:
            result = run_transcription(
                self.input_path,
                overwrite=self.overwrite,
                progress_callback=lambda p: self.progress.emit(p),
                cancel_token=self._cancel_token,
            )
            if self._cancel_token.is_cancelled:
                self.cancelled.emit()
            else:
                self.finished.emit(result)
        except InterruptedError:
            self.cancelled.emit()
        except FileExistsError as e:
            self.error.emit(str(e))
        except Exception as e:
            logger.exception("변환 중 예외 발생")
            self.error.emit(str(e))

    def cancel(self) -> None:
        """취소 요청 — 파이프라인 단계 간에서 InterruptedError 발생."""
        self._cancel_token.cancel()
        self.wait(5000)


class ModelDownloadWorker(QThread):
    """Whisper 모델 다운로드를 백그라운드에서 실행하는 워커."""

    progress = pyqtSignal(int)   # 0-100 (추정)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def run(self) -> None:
        try:
            import whisper
            # whisper.load_model이 자동으로 다운로드 수행
            # 진행률은 추정값으로 표시 (whisper 내부 콜백 없음)
            self.progress.emit(10)
            whisper.load_model("medium")
            self.progress.emit(100)
            self.finished.emit()
        except Exception as e:
            logger.exception("모델 다운로드 중 예외 발생")
            self.error.emit(f"인터넷 연결 문제로 다운로드가 중단되었습니다. 연결 상태를 확인한 뒤 다시 시도해 주세요.\n\n오류: {e}")


class MainWindow(QMainWindow):
    """Voice Ledger 메인 창."""

    def __init__(self) -> None:
        super().__init__()
        self._palette = Palette()
        self._worker: Optional[TranscriptionWorker] = None
        self._download_worker: Optional[ModelDownloadWorker] = None
        self._output_path: Optional[str] = None

        self._setup_window()
        self._setup_ui()
        self._connect_signals()
        self._check_model_on_startup()

    # ── 창 설정 ────────────────────────────────────────────────

    def _setup_window(self) -> None:
        self.setWindowTitle("Voice Ledger")
        self.setMinimumSize(480, 340)
        self.setMaximumSize(1000, 640)
        self.resize(780, 520)
        self.setUnifiedTitleAndToolBarOnMac(True)
        self._apply_window_style()

    def _apply_window_style(self) -> None:
        p = self._palette
        self.setStyleSheet(f"QMainWindow {{ background-color: {p.window_bg()}; }}")

    # ── UI 구성 ────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # DropZone
        self._drop_zone = DropZone()
        layout.addWidget(self._drop_zone, stretch=1)

        # 진행 바
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setFixedHeight(6)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.hide()
        layout.addWidget(self._progress_bar)

        # 상태 레이블
        self._status_label = QLabel("")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        p = self._palette
        self._status_label.setStyleSheet(f"font-size: 11px; color: {p.text_secondary()};")
        self._status_label.hide()
        layout.addWidget(self._status_label)

        # 하단 버튼 영역
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()

        self._cancel_btn = QPushButton("취소")
        self._cancel_btn.setFixedHeight(44)
        self._cancel_btn.hide()
        bottom_layout.addWidget(self._cancel_btn)

        self._finder_btn = QPushButton("Finder에서 보기")
        self._finder_btn.setFixedHeight(44)
        self._finder_btn.hide()
        bottom_layout.addWidget(self._finder_btn)

        self._open_btn = QPushButton("파일 열기")
        self._open_btn.setFixedHeight(44)
        self._open_btn.hide()
        bottom_layout.addWidget(self._open_btn)

        self._retry_btn = QPushButton("다시 시도")
        self._retry_btn.setFixedHeight(44)
        self._retry_btn.hide()
        bottom_layout.addWidget(self._retry_btn)

        layout.addLayout(bottom_layout)

    def _connect_signals(self) -> None:
        self._drop_zone.file_dropped.connect(self._on_file_dropped)
        self._drop_zone.error_occurred.connect(self._show_error)
        self._cancel_btn.clicked.connect(self._on_cancel)
        self._finder_btn.clicked.connect(self._reveal_in_finder)
        self._open_btn.clicked.connect(self._open_file)
        self._retry_btn.clicked.connect(self._check_model_on_startup)

    # ── 키보드 단축키 ──────────────────────────────────────────

    def keyPressEvent(self, event) -> None:
        from PyQt6.QtCore import Qt
        if event.key() == Qt.Key.Key_O and event.modifiers() == Qt.KeyboardModifier.MetaModifier:
            self._open_file_dialog()
        elif event.key() == Qt.Key.Key_Period and event.modifiers() == Qt.KeyboardModifier.MetaModifier:
            self._on_cancel()
        elif event.key() == Qt.Key.Key_Escape:
            if self._drop_zone.current_state in (DropZoneState.ERROR, DropZoneState.SUCCESS):
                self._reset_to_idle()
        else:
            super().keyPressEvent(event)

    def _open_file_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "파일 선택", "", "오디오/비디오 파일 (*.m4a *.mp4)"
        )
        if path:
            self._on_file_dropped(path)

    # ── 파일 변환 ──────────────────────────────────────────────

    def _on_file_dropped(self, file_path: str) -> None:
        if self._drop_zone.current_state == DropZoneState.PROCESSING:
            self._show_error("지금 변환이 진행 중입니다. 완료 후 다음 파일을 드래그해 주세요.")
            return

        # 덮어쓰기 확인
        output_path = file_path.rsplit(".", 1)[0] + ".txt"
        overwrite = False
        if os.path.exists(output_path):
            reply = QMessageBox.question(
                self, "파일 덮어쓰기",
                f"'{os.path.basename(output_path)}' 파일이 이미 존재합니다. 덮어쓰시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                return
            overwrite = True

        self._start_transcription(file_path, overwrite)

    def _start_transcription(self, file_path: str, overwrite: bool) -> None:
        filename = os.path.basename(file_path)
        self._drop_zone.set_state(DropZoneState.PROCESSING, filename)
        self._progress_bar.setValue(0)
        self._progress_bar.show()
        self._status_label.setText(f"변환 중 · {filename}")
        self._status_label.show()
        self._cancel_btn.show()
        self._finder_btn.hide()
        self._open_btn.hide()

        self._worker = TranscriptionWorker(file_path, overwrite)
        self._worker.progress.connect(self._progress_bar.setValue)
        self._worker.finished.connect(self._on_transcription_finished)
        self._worker.cancelled.connect(self._on_transcription_cancelled)
        self._worker.error.connect(self._on_transcription_error)
        self._worker.start()

    def _on_transcription_finished(self, output_path: str) -> None:
        self._output_path = output_path
        self._drop_zone.set_state(DropZoneState.SUCCESS, os.path.basename(output_path))
        self._progress_bar.setValue(100)
        p = self._palette
        self._progress_bar.setStyleSheet(
            f"QProgressBar::chunk {{ background-color: {p.success()}; border-radius: 3px; }}"
        )
        self._status_label.setText(f"완료 — {output_path}")
        self._cancel_btn.hide()
        self._finder_btn.show()
        self._open_btn.show()
        QTimer.singleShot(60000, self._reset_to_idle)

    def _on_transcription_cancelled(self) -> None:
        self._reset_to_idle()

    def _on_transcription_error(self, message: str) -> None:
        self._drop_zone.set_state(DropZoneState.ERROR, message)
        self._progress_bar.hide()
        self._status_label.hide()
        self._cancel_btn.hide()

    def _on_cancel(self) -> None:
        if self._worker and self._worker.isRunning():
            self._status_label.setText("취소 중...")
            self._worker.cancel()

    def _reset_to_idle(self) -> None:
        self._drop_zone.set_state(DropZoneState.IDLE)
        self._progress_bar.hide()
        self._progress_bar.setValue(0)
        self._progress_bar.setStyleSheet("")
        self._status_label.hide()
        self._cancel_btn.hide()
        self._finder_btn.hide()
        self._open_btn.hide()
        self._retry_btn.hide()
        self._output_path = None

    def _show_error(self, message: str) -> None:
        self._drop_zone.set_state(DropZoneState.ERROR, message)

    # ── 완료 후 액션 ───────────────────────────────────────────

    def _reveal_in_finder(self) -> None:
        if self._output_path:
            import subprocess
            subprocess.run(["open", "-R", self._output_path])

    def _open_file(self) -> None:
        if self._output_path:
            import subprocess
            subprocess.run(["open", self._output_path])

    # ── 모델 다운로드 ──────────────────────────────────────────

    def _check_model_on_startup(self) -> None:
        if WhisperRunner.is_model_available():
            self._reset_to_idle()
        else:
            self._start_model_download()

    def _start_model_download(self) -> None:
        self._drop_zone.set_state(DropZoneState.MODEL_DOWNLOAD, "다운로드 준비 중...")
        self._progress_bar.setValue(0)
        self._progress_bar.show()
        self._retry_btn.hide()

        self._download_worker = ModelDownloadWorker()
        self._download_worker.progress.connect(self._on_download_progress)
        self._download_worker.finished.connect(self._on_download_finished)
        self._download_worker.error.connect(self._on_download_error)
        self._download_worker.start()

    def _on_download_progress(self, value: int) -> None:
        self._progress_bar.setValue(value)
        self._drop_zone.set_state(
            DropZoneState.MODEL_DOWNLOAD,
            f"Whisper medium 모델 다운로드 중... (~1.5 GB)"
        )

    def _on_download_finished(self) -> None:
        self._reset_to_idle()

    def _on_download_error(self, message: str) -> None:
        self._drop_zone.set_state(DropZoneState.ERROR, message)
        self._progress_bar.hide()
        self._retry_btn.show()
        self._retry_btn.setText("다시 시도")
