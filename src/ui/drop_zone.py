"""드래그앤드롭 영역 위젯 — 6가지 상태 지원"""
from __future__ import annotations
import os
from enum import Enum, auto

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel

from src.engine.validator import SUPPORTED_EXTENSIONS
from src.ui.styles import Palette


class DropZoneState(Enum):
    IDLE = auto()
    DRAG_HOVER = auto()
    PROCESSING = auto()
    CANCELLING = auto()
    SUCCESS = auto()
    ERROR = auto()
    MODEL_DOWNLOAD = auto()


class DropZone(QFrame):
    """드래그앤드롭 영역 위젯.

    Signals:
        file_dropped(str): 유효한 파일이 드롭되었을 때 파일 경로 전달
        error_occurred(str): 잘못된 파일 드롭 시 에러 메시지 전달
    """

    file_dropped = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._state = DropZoneState.IDLE
        self._palette = Palette()
        self._error_timer = QTimer(self)
        self._error_timer.setSingleShot(True)
        self._error_timer.timeout.connect(lambda: self.set_state(DropZoneState.IDLE))
        self._setup_ui()
        self._apply_idle_style()
        self.setAcceptDrops(True)

    # ── UI 초기화 ──────────────────────────────────────────────

    def _setup_ui(self) -> None:
        self.setMinimumHeight(200)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._icon_label = QLabel("↓", self)
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_label.setStyleSheet("font-size: 32px;")

        self._main_label = QLabel("파일을 드롭하거나 Cmd+O로 선택", self)
        self._main_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._sub_label = QLabel(".m4a · .mp4 지원", self)
        self._sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self._icon_label)
        layout.addWidget(self._main_label)
        layout.addWidget(self._sub_label)

    # ── 상태 전환 ──────────────────────────────────────────────

    def set_state(self, state: DropZoneState, message: str = "") -> None:
        self._state = state
        if state == DropZoneState.IDLE:
            self._apply_idle_style()
        elif state == DropZoneState.DRAG_HOVER:
            self._apply_hover_style()
        elif state == DropZoneState.PROCESSING:
            self._apply_processing_style(message)
        elif state == DropZoneState.CANCELLING:
            self._apply_cancelling_style(message)
        elif state == DropZoneState.SUCCESS:
            self._apply_success_style(message)
        elif state == DropZoneState.ERROR:
            self._apply_error_style(message)
            self._error_timer.stop()
            self._error_timer.start(4000)
        elif state == DropZoneState.MODEL_DOWNLOAD:
            self._apply_model_download_style(message)

    @property
    def current_state(self) -> DropZoneState:
        return self._state

    # ── 스타일 적용 ────────────────────────────────────────────

    def _apply_idle_style(self) -> None:
        p = self._palette
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {p.dropzone_bg()};
                border: 1px dashed {p.dropzone_border()};
                border-radius: 8px;
            }}
        """)
        self._icon_label.setText("↓")
        self._icon_label.setStyleSheet(f"font-size: 32px; color: {p.text_secondary()};")
        self._main_label.setText("파일을 드롭하거나 Cmd+O로 선택")
        self._main_label.setStyleSheet(f"font-size: 13px; color: {p.text_secondary()};")
        self._sub_label.setText(".m4a · .mp4 지원")
        self._sub_label.setStyleSheet(f"font-size: 11px; color: {p.text_tertiary()};")
        self.setAcceptDrops(True)

    def _apply_hover_style(self) -> None:
        p = self._palette
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {p.dropzone_bg_hover()};
                border: 2px solid {p.accent()};
                border-radius: 8px;
            }}
        """)
        self._icon_label.setText("+")
        self._icon_label.setStyleSheet(f"font-size: 32px; color: {p.accent()};")
        self._main_label.setText("여기에 파일을 드롭하세요")
        self._main_label.setStyleSheet(f"font-size: 13px; color: {p.accent()};")
        self._sub_label.setText("")

    def _apply_processing_style(self, filename: str = "") -> None:
        p = self._palette
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {p.dropzone_bg()};
                border: 1px solid {p.dropzone_border()};
                border-radius: 8px;
            }}
        """)
        self._icon_label.setText("◎")
        self._icon_label.setStyleSheet(f"font-size: 32px; color: {p.accent()};")
        self._main_label.setText(f"변환 중{(' — ' + filename) if filename else '...'}")
        self._main_label.setStyleSheet(f"font-size: 13px; color: {p.text_primary()};")
        self._sub_label.setText("완료될 때까지 기다려 주세요")
        self._sub_label.setStyleSheet(f"font-size: 11px; color: {p.text_secondary()};")
        self.setAcceptDrops(False)

    def _apply_success_style(self, filename: str = "") -> None:
        p = self._palette
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {p.dropzone_bg()};
                border: 1px solid {p.success()};
                border-radius: 8px;
            }}
        """)
        self._icon_label.setText("✓")
        self._icon_label.setStyleSheet(f"font-size: 32px; color: {p.success()};")
        self._main_label.setText("완료")
        self._main_label.setStyleSheet(f"font-size: 14px; color: {p.success()};")
        self._sub_label.setText(filename if filename else "")
        self._sub_label.setStyleSheet(f"font-size: 12px; color: {p.text_secondary()};")
        self.setAcceptDrops(False)

    def _apply_error_style(self, message: str = "") -> None:
        p = self._palette
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {p.dropzone_bg()};
                border: 2px solid {p.error()};
                border-radius: 8px;
            }}
        """)
        self._icon_label.setText("✕")
        self._icon_label.setStyleSheet(f"font-size: 32px; color: {p.error()};")
        self._main_label.setText(message or "오류가 발생했습니다")
        self._main_label.setStyleSheet(f"font-size: 12px; color: {p.error()};")
        self._sub_label.setText("4초 후 자동으로 돌아갑니다")
        self._sub_label.setStyleSheet(f"font-size: 11px; color: {p.text_tertiary()};")
        self.setAcceptDrops(False)

    def _apply_cancelling_style(self, message: str = "") -> None:
        p = self._palette
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {p.dropzone_bg()};
                border: 1px solid {p.text_tertiary()};
                border-radius: 8px;
            }}
        """)
        self._icon_label.setText("◎")
        self._icon_label.setStyleSheet(f"font-size: 32px; color: {p.text_secondary()};")
        self._main_label.setText("취소 중")
        self._main_label.setStyleSheet(f"font-size: 13px; color: {p.text_secondary()};")
        self._sub_label.setText(message or "정리하는 중이에요")
        self._sub_label.setStyleSheet(f"font-size: 11px; color: {p.text_tertiary()};")
        self.setAcceptDrops(False)

    def _apply_model_download_style(self, progress_text: str = "") -> None:
        p = self._palette
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {p.dropzone_bg()};
                border: 1px dashed {p.dropzone_border()};
                border-radius: 8px;
            }}
        """)
        self._icon_label.setText("⬇")
        self._icon_label.setStyleSheet(f"font-size: 32px; color: {p.accent()};")
        self._main_label.setText("Whisper 모델 준비 중")
        self._main_label.setStyleSheet(f"font-size: 14px; color: {p.text_primary()};")
        self._sub_label.setText(progress_text or "다운로드 중...")
        self._sub_label.setStyleSheet(f"font-size: 11px; color: {p.text_secondary()};")
        self.setAcceptDrops(False)

    # ── 드래그앤드롭 이벤트 ────────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if (
            self._state == DropZoneState.IDLE
            and event.mimeData().hasUrls()
        ):
            event.acceptProposedAction()
            self.set_state(DropZoneState.DRAG_HOVER)
        else:
            event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        if self._state == DropZoneState.DRAG_HOVER:
            self.set_state(DropZoneState.IDLE)

    def dropEvent(self, event: QDropEvent) -> None:
        if self._state != DropZoneState.DRAG_HOVER:
            event.ignore()
            return

        urls = event.mimeData().urls()
        if not urls:
            self.set_state(DropZoneState.IDLE)
            return

        if len(urls) > 1:
            self.set_state(DropZoneState.IDLE)
            self.error_occurred.emit(
                "한 번에 하나의 파일만 변환할 수 있습니다. 파일을 하나씩 드래그해 주세요."
            )
            return

        file_path = urls[0].toLocalFile()
        _, ext = os.path.splitext(file_path)
        if ext.lower() not in SUPPORTED_EXTENSIONS:
            self.set_state(DropZoneState.ERROR,
                "이 파일 형식은 지원하지 않습니다. .m4a 또는 .mp4 파일을 사용해 주세요.")
            event.ignore()
            return

        event.acceptProposedAction()
        self.file_dropped.emit(file_path)
