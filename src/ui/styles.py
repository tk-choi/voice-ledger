"""Voice Ledger 디자인 시스템 — Precision Design System"""
import subprocess
from PyQt6.QtGui import QColor


# ── Apple Blue 액센트 ──────────────────────────────────────────
ACCENT_LIGHT = "#007AFF"
ACCENT_DARK = "#0A84FF"

# ── 성공 / 에러 ───────────────────────────────────────────────
SUCCESS_LIGHT = "#34C759"
SUCCESS_DARK = "#30D158"
ERROR_LIGHT = "#FF3B30"
ERROR_DARK = "#FF453A"

# ── 창 배경 ───────────────────────────────────────────────────
WINDOW_BG_LIGHT = "#F2F2F2"
WINDOW_BG_DARK = "#1E1E1E"

# ── 드롭존 ────────────────────────────────────────────────────
DROPZONE_BG_LIGHT = "#FFFFFF"
DROPZONE_BG_DARK = "#2A2A2A"
DROPZONE_BG_HOVER_LIGHT = "#EBF3FF"
DROPZONE_BG_HOVER_DARK = "#1A2E44"
DROPZONE_BORDER_LIGHT = "#D1D1D6"
DROPZONE_BORDER_DARK = "#484848"

# ── 텍스트 ────────────────────────────────────────────────────
TEXT_PRIMARY_LIGHT = "#1C1C1E"
TEXT_PRIMARY_DARK = "#F2F2F7"
TEXT_SECONDARY_LIGHT = "#6C6C70"
TEXT_SECONDARY_DARK = "#8E8E93"
TEXT_TERTIARY_LIGHT = "#A2A2A7"
TEXT_TERTIARY_DARK = "#5E5E62"

# ── 진행 바 ───────────────────────────────────────────────────
PROGRESS_TRACK_LIGHT = "#D1D1D6"
PROGRESS_TRACK_DARK = "#3A3A3C"


_dark_mode_cache: bool | None = None


def is_dark_mode() -> bool:
    """macOS 시스템 다크 모드 여부를 반환한다."""
    global _dark_mode_cache
    if _dark_mode_cache is None:
        try:
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            _dark_mode_cache = result.stdout.strip() == "Dark"
        except Exception:
            _dark_mode_cache = False
    return _dark_mode_cache


class Palette:
    """현재 시스템 모드에 따라 적절한 색상을 반환하는 팔레트."""

    def __init__(self) -> None:
        self._dark = is_dark_mode()

    @property
    def is_dark(self) -> bool:
        return self._dark

    def accent(self) -> str:
        return ACCENT_DARK if self._dark else ACCENT_LIGHT

    def success(self) -> str:
        return SUCCESS_DARK if self._dark else SUCCESS_LIGHT

    def error(self) -> str:
        return ERROR_DARK if self._dark else ERROR_LIGHT

    def window_bg(self) -> str:
        return WINDOW_BG_DARK if self._dark else WINDOW_BG_LIGHT

    def dropzone_bg(self) -> str:
        return DROPZONE_BG_DARK if self._dark else DROPZONE_BG_LIGHT

    def dropzone_bg_hover(self) -> str:
        return DROPZONE_BG_HOVER_DARK if self._dark else DROPZONE_BG_HOVER_LIGHT

    def dropzone_border(self) -> str:
        return DROPZONE_BORDER_DARK if self._dark else DROPZONE_BORDER_LIGHT

    def text_primary(self) -> str:
        return TEXT_PRIMARY_DARK if self._dark else TEXT_PRIMARY_LIGHT

    def text_secondary(self) -> str:
        return TEXT_SECONDARY_DARK if self._dark else TEXT_SECONDARY_LIGHT

    def text_tertiary(self) -> str:
        return TEXT_TERTIARY_DARK if self._dark else TEXT_TERTIARY_LIGHT

    def progress_track(self) -> str:
        return PROGRESS_TRACK_DARK if self._dark else PROGRESS_TRACK_LIGHT
