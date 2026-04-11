"""Voice Ledger 메인 창 — PyQt6 기반"""
from __future__ import annotations
import logging
import math
import os
import random
from typing import Optional

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QProgressBar, QMessageBox, QFileDialog,
)

from src.engine import run_transcription
from src.engine.cancellation import CancellationToken
from src.engine.whisper_runner import WhisperRunner
from src.engine.writer import FileWriter
from src.ui.drop_zone import DropZone, DropZoneState
from src.ui.styles import Palette

logger = logging.getLogger(__name__)

# ── 단계별 친근한 상태 메시지 ──────────────────────────────────────
_FRIENDLY_MESSAGES: dict[str, list[str]] = {
    "validating": [
        "파일을 확인하고 있어요",
    ],
    "converting": [
        "오디오를 준비하고 있어요",
        "소리를 분석할 준비를 하는 중이에요",
    ],
    "transcribing": [
        "음성을 텍스트로 바꾸는 중이에요",
        "열심히 듣고 있어요",
        "하나하나 꼼꼼히 확인 중이에요",
        "잘 진행되고 있어요",
        "꼼꼼하게 확인 중입니다",
        "AI가 열심히 일하고 있어요",
    ],
    "transcribing_late": [
        "거의 다 됐어요!",
        "마무리 작업 중이에요",
        "조금만 더 기다려 주세요",
        "끝이 보여요!",
    ],
    "saving": [
        "텍스트를 저장하고 있어요",
        "마지막 정리 중이에요",
        "곧 완료됩니다!",
    ],
    "cancelling": [
        "취소하고 있어요",
        "정리하는 중이에요",
        "곧 돌아갈게요",
    ],
}


class TranscriptionWorker(QThread):
    """Engine run_transcription()을 QThread에서 실행하는 워커."""

    progress = pyqtSignal(int)      # 0-100
    stage_changed = pyqtSignal(str) # 현재 파이프라인 단계
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
                stage_callback=lambda s: self.stage_changed.emit(s),
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


class ModelDownloadWorker(QThread):
    """Whisper 모델 다운로드를 백그라운드에서 실행하는 워커."""

    progress = pyqtSignal(int)   # 0-100 (추정)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def run(self) -> None:
        try:
            from faster_whisper import WhisperModel
            # WhisperModel 생성 시 huggingface hub에서 자동 다운로드
            # 진행률은 추정값으로 표시 (faster-whisper 내부 콜백 없음)
            self.progress.emit(10)
            WhisperModel("large-v3", device="auto", compute_type="int8")
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
        self._idle_timer = QTimer(self)
        self._idle_timer.setSingleShot(True)
        self._idle_timer.timeout.connect(self._reset_to_idle)

        # 진행률 UX 상태
        self._current_stage: str = ""
        self._last_message: str = ""
        self._last_pulse_rgb: tuple[int, int, int] = (0, 0, 0)
        self._is_cancelling: bool = False

        # 친근한 메시지 로테이션 타이머 (3.5초)
        self._message_timer = QTimer(self)
        self._message_timer.timeout.connect(self._rotate_message)

        # 진행률 바 펄스 애니메이션 타이머 (100ms = 10fps)
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._update_pulse)
        self._pulse_phase: float = 0.0

        # 취소 도트 애니메이션 타이머 (500ms)
        self._cancel_dot_timer = QTimer(self)
        self._cancel_dot_timer.timeout.connect(self._update_cancel_dots)
        self._cancel_dot_count: int = 0
        self._cancel_message: str = ""

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
        if event.key() == Qt.Key.Key_O and event.modifiers() == Qt.KeyboardModifier.MetaModifier:
            self._open_file_dialog()
        elif event.key() == Qt.Key.Key_Period and event.modifiers() == Qt.KeyboardModifier.MetaModifier:
            self._on_cancel()
        elif event.key() == Qt.Key.Key_Escape:
            if self._drop_zone.current_state == DropZoneState.ERROR:
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
        output_path = FileWriter.derive_output_path(file_path)
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
        self._idle_timer.stop()
        self._is_cancelling = False
        self._current_stage = "validating"
        self._pulse_phase = 0.0
        self._last_pulse_rgb = (0, 0, 0)
        filename = os.path.basename(file_path)
        self._drop_zone.set_state(DropZoneState.PROCESSING, filename)
        self._progress_bar.setValue(0)
        p = self._palette
        self._progress_bar.setStyleSheet(
            f"QProgressBar {{ background-color: {p.progress_track()}; border-radius: 3px; }}"
        )
        self._progress_bar.show()
        self._status_label.setText("파일을 확인하고 있어요")
        self._status_label.show()
        self._cancel_btn.show()
        self._finder_btn.hide()
        self._open_btn.hide()

        # 애니메이션 타이머 시작
        self._message_timer.start(3500)
        self._pulse_timer.start(100)

        self._worker = TranscriptionWorker(file_path, overwrite)
        self._worker.progress.connect(self._on_progress_updated)
        self._worker.stage_changed.connect(self._on_stage_changed)
        self._worker.finished.connect(self._on_transcription_finished)
        self._worker.cancelled.connect(self._on_transcription_cancelled)
        self._worker.error.connect(self._on_transcription_error)
        self._worker.start()

    def _on_transcription_finished(self, output_path: str) -> None:
        self._stop_all_animation_timers()
        self._output_path = output_path
        self._progress_bar.setValue(100)
        p = self._palette
        self._progress_bar.setStyleSheet(
            f"QProgressBar {{ background-color: {p.progress_track()}; border-radius: 3px; }}"
            f"QProgressBar::chunk {{ background-color: {p.success()}; border-radius: 3px; }}"
        )
        self._status_label.setText(f"완료 — {output_path}")
        self._cancel_btn.hide()
        self._finder_btn.show()
        self._open_btn.show()
        self._idle_timer.start(60000)

    def _on_transcription_cancelled(self) -> None:
        self._reset_to_idle()

    def _on_transcription_error(self, message: str) -> None:
        self._stop_all_animation_timers()
        self._drop_zone.set_state(DropZoneState.ERROR, message)
        self._progress_bar.hide()
        self._status_label.hide()
        self._cancel_btn.hide()

    def _on_cancel(self) -> None:
        if self._worker and self._worker.isRunning():
            self._is_cancelling = True
            # 메시지/펄스 타이머 중지, 취소 전용 애니메이션 시작
            self._message_timer.stop()
            self._pulse_timer.stop()
            self._drop_zone.set_state(DropZoneState.CANCELLING)
            self._cancel_btn.hide()
            # 취소 메시지 초기화 및 도트 애니메이션 시작
            messages = _FRIENDLY_MESSAGES["cancelling"]
            self._cancel_message = random.choice(messages)
            self._cancel_dot_count = 0
            self._status_label.setText(self._cancel_message)
            self._cancel_dot_timer.start(500)
            self._worker.cancel()

    def _reset_to_idle(self) -> None:
        self._stop_all_animation_timers()
        self._is_cancelling = False
        self._current_stage = ""
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

    # ── 진행률 UX ─────────────────────────────────────────────────

    def _on_progress_updated(self, value: int) -> None:
        """엔진에서 진행률이 업데이트될 때 호출. 단조증가만 허용."""
        if value > self._progress_bar.value():
            self._progress_bar.setValue(value)

    def _on_stage_changed(self, stage: str) -> None:
        """엔진에서 파이프라인 단계가 바뀔 때 호출."""
        self._current_stage = stage
        # 단계 전환 시 즉시 새 메시지 표시
        self._rotate_message()

    def _get_message_key(self) -> str:
        """현재 상태에 맞는 메시지 풀 키를 반환."""
        if self._is_cancelling:
            return "cancelling"
        if self._current_stage == "transcribing" and self._progress_bar.value() >= 70:
            return "transcribing_late"
        return self._current_stage or "validating"

    def _rotate_message(self) -> None:
        """친근한 상태 메시지를 랜덤하게 교체."""
        if self._is_cancelling:
            return
        key = self._get_message_key()
        messages = _FRIENDLY_MESSAGES.get(key, _FRIENDLY_MESSAGES["transcribing"])
        candidates = [m for m in messages if m != self._last_message] or messages
        msg = random.choice(candidates)
        self._last_message = msg
        self._status_label.setText(msg)

    def _update_pulse(self) -> None:
        """진행률 바에 부드러운 펄스 글로우 효과 적용."""
        self._pulse_phase += 0.06
        t = (math.sin(self._pulse_phase) + 1) / 2  # 0.0 ~ 1.0

        if self._palette.is_dark:
            r = int(10 + 32 * t)
            g = int(132 + 18 * t)
            b = 255
        else:
            r = int(0 + 31 * t)
            g = int(122 + 16 * t)
            b = 255

        rgb = (r, g, b)
        if rgb == self._last_pulse_rgb:
            return
        self._last_pulse_rgb = rgb
        track = self._palette.progress_track()
        self._progress_bar.setStyleSheet(
            f"QProgressBar {{ background-color: {track}; border-radius: 3px; }}"
            f"QProgressBar::chunk {{ background-color: rgb({r}, {g}, {b}); border-radius: 3px; }}"
        )

    def _update_cancel_dots(self) -> None:
        """취소 중 도트 애니메이션 업데이트."""
        self._cancel_dot_count = (self._cancel_dot_count + 1) % 4
        dots = "." * self._cancel_dot_count
        self._status_label.setText(f"{self._cancel_message}{dots}")

    def _stop_all_animation_timers(self) -> None:
        """모든 애니메이션 타이머를 정지."""
        self._message_timer.stop()
        self._pulse_timer.stop()
        self._cancel_dot_timer.stop()

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        """macOS 닫기 버튼 클릭 시 앱을 완전히 종료."""
        self._stop_all_animation_timers()
        self._idle_timer.stop()
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(3000)
        if self._download_worker and self._download_worker.isRunning():
            self._download_worker.wait(3000)
        event.accept()

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
            "Whisper large-v3 모델 다운로드 중... (~3 GB)"
        )

    def _on_download_finished(self) -> None:
        self._reset_to_idle()

    def _on_download_error(self, message: str) -> None:
        self._drop_zone.set_state(DropZoneState.ERROR, message)
        self._progress_bar.hide()
        self._retry_btn.show()
        self._retry_btn.setText("다시 시도")
