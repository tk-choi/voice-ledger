# UX 개선: 인라인 결과 뷰 + macOS 알림 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 변환 완료 후 앱 안에서 텍스트를 바로 확인하고 클립보드에 복사할 수 있도록 인라인 결과 뷰를 추가하고, macOS 시스템 알림을 발송한다.

**Architecture:** `DropZone` 위젯과 `QTextEdit`을 `QStackedWidget`으로 묶어 완료 시 텍스트 뷰로 전환한다. 엔진 레이어는 건드리지 않으며 `src/ui/main_window.py`와 `src/ui/drop_zone.py`만 수정한다.

**Tech Stack:** PyQt6 (`QStackedWidget`, `QTextEdit`, `QApplication.clipboard`), Python `subprocess` (osascript)

---

## 수정 파일 목록

| 파일 | 변경 유형 | 내용 |
|------|-----------|------|
| `src/ui/drop_zone.py` | Modify | `DropZoneState.SUCCESS` 및 관련 메서드 제거 |
| `src/ui/main_window.py` | Modify | `QStackedWidget`, `QTextEdit`, 복사 버튼, 알림 추가 |

엔진, 테스트 파일 — **변경 없음**

---

## Task 1: `DropZoneState.SUCCESS` 제거

`DropZone`에서 `SUCCESS` 상태를 완전히 제거한다. `main_window.py`에서 해당 상태를 참조하는 두 곳도 함께 수정한다.

**Files:**
- Modify: `src/ui/drop_zone.py` (lines 14–22, 79–81, 143–158)
- Modify: `src/ui/main_window.py` (lines 314–328, 248–250)

- [ ] **Step 1: `drop_zone.py` — `SUCCESS` enum 값 제거**

`src/ui/drop_zone.py` line 19를 삭제한다:

```python
# 변경 전
class DropZoneState(Enum):
    IDLE = auto()
    DRAG_HOVER = auto()
    PROCESSING = auto()
    CANCELLING = auto()
    SUCCESS = auto()      # ← 삭제
    ERROR = auto()
    MODEL_DOWNLOAD = auto()

# 변경 후
class DropZoneState(Enum):
    IDLE = auto()
    DRAG_HOVER = auto()
    PROCESSING = auto()
    CANCELLING = auto()
    ERROR = auto()
    MODEL_DOWNLOAD = auto()
```

- [ ] **Step 2: `drop_zone.py` — `set_state`의 SUCCESS 분기 제거**

`src/ui/drop_zone.py` `set_state` 메서드에서 아래 두 줄을 삭제한다:

```python
# 삭제할 줄 (현재 79–81번째 줄 부근)
elif state == DropZoneState.SUCCESS:
    self._apply_success_style(message)
```

- [ ] **Step 3: `drop_zone.py` — `_apply_success_style` 메서드 전체 제거**

`src/ui/drop_zone.py`에서 아래 메서드 전체를 삭제한다:

```python
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
```

- [ ] **Step 4: `main_window.py` — SUCCESS 참조 제거 (두 곳)**

`src/ui/main_window.py`에서 아래 줄을 찾아 제거 또는 수정한다.

**제거 (현재 line 317 부근):**
```python
# 삭제할 줄
self._drop_zone.set_state(DropZoneState.SUCCESS, os.path.basename(output_path))
```

**수정 (현재 line 248 부근 `keyPressEvent`):**
```python
# 변경 전
if self._drop_zone.current_state in (DropZoneState.ERROR, DropZoneState.SUCCESS):
    self._reset_to_idle()

# 변경 후 (SUCCESS 제거 — RESULT 스택 체크는 Task 4에서 추가)
if self._drop_zone.current_state == DropZoneState.ERROR:
    self._reset_to_idle()
```

- [ ] **Step 5: 기존 테스트 통과 확인**

```bash
python -m pytest tests/ -v
```

기대 결과: 모든 기존 테스트 PASS (GUI가 아닌 엔진 테스트이므로 영향 없음)

- [ ] **Step 6: 커밋**

```bash
git add src/ui/drop_zone.py src/ui/main_window.py
git commit -m "refactor(ui): DropZoneState.SUCCESS 제거 — 인라인 결과 뷰 전환 준비"
```

---

## Task 2: `QStackedWidget` + `QTextEdit` + 새 버튼 추가

`_setup_ui`를 수정하여 DropZone과 텍스트 뷰를 스택으로 묶고, 복사/새 변환 버튼을 추가한다.

**Files:**
- Modify: `src/ui/main_window.py`

- [ ] **Step 1: import에 `QStackedWidget`, `QTextEdit`, `QApplication` 추가**

`src/ui/main_window.py` 상단 import를 수정한다:

```python
# 변경 전
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QProgressBar, QMessageBox, QFileDialog,
)

# 변경 후
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QProgressBar, QMessageBox, QFileDialog,
    QStackedWidget, QTextEdit,
)
```

- [ ] **Step 2: `_setup_ui` — DropZone을 QStackedWidget으로 교체**

`src/ui/main_window.py`의 `_setup_ui` 메서드에서 아래를 수정한다.

```python
# 변경 전
# DropZone
self._drop_zone = DropZone()
layout.addWidget(self._drop_zone, stretch=1)

# 변경 후
# DropZone + 결과 텍스트 뷰 스택
self._drop_zone = DropZone()

self._result_text = QTextEdit()
self._result_text.setReadOnly(True)
self._result_text.setFont(self.font())  # 시스템 폰트 유지

self._stack = QStackedWidget()
self._stack.addWidget(self._drop_zone)   # index 0 — 기본 뷰
self._stack.addWidget(self._result_text) # index 1 — 결과 뷰

layout.addWidget(self._stack, stretch=1)
```

- [ ] **Step 3: `_setup_ui` — 결과 텍스트 스타일 적용**

`QStackedWidget` 생성 직후에 추가한다:

```python
p = self._palette
self._result_text.setStyleSheet(
    f"QTextEdit {{"
    f"  background-color: {p.dropzone_bg()};"
    f"  color: {p.text_primary()};"
    f"  border: 1px solid {p.dropzone_border()};"
    f"  border-radius: 8px;"
    f"  padding: 12px;"
    f"  font-size: 12px;"
    f"  line-height: 1.6;"
    f"}}"
)
```

- [ ] **Step 4: `_setup_ui` — `_copy_btn`, `_new_file_btn` 추가**

`bottom_layout` 구성 부분에서 기존 버튼 사이에 새 버튼을 추가한다.  
버튼 순서(좌→우): `cancel` · `new_file` · `finder` · `open` · `copy` · `retry`

```python
# 기존 self._cancel_btn 추가 코드 아래에 삽입
self._new_file_btn = QPushButton("새 파일 변환")
self._new_file_btn.setFixedHeight(44)
self._new_file_btn.hide()
bottom_layout.addWidget(self._new_file_btn)

# 기존 self._finder_btn, self._open_btn 추가 코드는 그대로 유지

# 기존 self._open_btn 추가 코드 아래에 삽입
self._copy_btn = QPushButton("전체 복사")
self._copy_btn.setFixedHeight(44)
self._copy_btn.hide()
p2 = self._palette
self._copy_btn.setStyleSheet(
    f"QPushButton {{ background-color: {p2.accent()}; color: #1e1e2e;"
    f"  border: none; border-radius: 6px; font-weight: bold; padding: 0 16px; }}"
    f"QPushButton:pressed {{ opacity: 0.8; }}"
)
bottom_layout.addWidget(self._copy_btn)
```

- [ ] **Step 5: 앱 실행하여 레이아웃 확인**

```bash
PYTHONPATH=. uv run python src/main.py
```

기대 결과: 앱이 정상 실행됨. 기능은 아직 미완성이나 레이아웃 깨짐 없음.

- [ ] **Step 6: 커밋**

```bash
git add src/ui/main_window.py
git commit -m "feat(ui): QStackedWidget + QTextEdit + 복사/새변환 버튼 골격 추가"
```

---

## Task 3: 변환 완료 흐름 구현 (텍스트 로드 + 스택 전환 + macOS 알림)

**Files:**
- Modify: `src/ui/main_window.py`

- [ ] **Step 1: 모듈 레벨에 `_notify_completion` 함수 추가**

`src/ui/main_window.py`에서 `_FRIENDLY_MESSAGES` 딕셔너리 바로 아래에 추가한다:

```python
def _notify_completion(filename: str) -> None:
    """macOS 시스템 알림을 발송한다. 실패해도 무시."""
    try:
        import subprocess
        subprocess.run(
            [
                "osascript", "-e",
                f'display notification "변환 완료: {filename}" with title "Voice Ledger"',
            ],
            timeout=3,
            check=False,
        )
    except Exception:
        pass
```

- [ ] **Step 2: `_on_transcription_finished` 전체 교체**

`src/ui/main_window.py`의 `_on_transcription_finished` 메서드를 아래로 교체한다:

```python
def _on_transcription_finished(self, output_path: str) -> None:
    self._stop_all_animation_timers()
    self._output_path = output_path

    # 텍스트 로드
    try:
        with open(output_path, encoding="utf-8") as f:
            self._result_text.setPlainText(f.read())
    except OSError as e:
        self._on_transcription_error(f"결과 파일을 읽을 수 없습니다: {e}")
        return

    # 스택 전환: DropZone → 텍스트 뷰
    self._drop_zone.set_state(DropZoneState.IDLE)  # 복귀 시 IDLE 준비
    self._stack.setCurrentIndex(1)

    # 진행 바 완료 표시
    self._progress_bar.setValue(100)
    p = self._palette
    self._progress_bar.setStyleSheet(
        f"QProgressBar {{ background-color: {p.progress_track()}; border-radius: 3px; }}"
        f"QProgressBar::chunk {{ background-color: {p.success()}; border-radius: 3px; }}"
    )

    # 상태 레이블 숨기기
    self._status_label.hide()

    # 버튼 상태
    self._cancel_btn.hide()
    self._new_file_btn.show()
    self._finder_btn.show()
    self._open_btn.show()
    self._copy_btn.show()

    # macOS 알림
    _notify_completion(os.path.basename(output_path))

    # 60초 후 자동 IDLE 복귀
    self._idle_timer.start(60000)
```

- [ ] **Step 3: 앱 실행 후 변환 완료 흐름 수동 확인**

```bash
PYTHONPATH=. uv run python src/main.py
```

1. `.m4a` 또는 `.mp4` 파일을 드롭
2. 변환 완료 후 텍스트 뷰가 나타나는지 확인
3. macOS 알림이 뜨는지 확인 (시스템 알림 권한이 필요할 수 있음)

- [ ] **Step 4: 커밋**

```bash
git add src/ui/main_window.py
git commit -m "feat(ui): 변환 완료 시 인라인 텍스트 뷰 전환 + macOS 알림"
```

---

## Task 4: 복사 기능 + IDLE 복귀 + Escape 키 업데이트

**Files:**
- Modify: `src/ui/main_window.py`

- [ ] **Step 1: `_on_copy` 메서드 추가**

`src/ui/main_window.py`에서 `_open_file` 메서드 아래에 추가한다:

```python
def _on_copy(self) -> None:
    """전체 텍스트를 클립보드에 복사하고 1.5초간 피드백을 표시한다."""
    QApplication.clipboard().setText(self._result_text.toPlainText())
    self._copy_btn.setText("복사됨 ✓")
    QTimer.singleShot(1500, lambda: self._copy_btn.setText("전체 복사"))
```

- [ ] **Step 2: `_reset_to_idle` — 스택 초기화 로직 추가**

`src/ui/main_window.py`의 `_reset_to_idle` 메서드에서 기존 숨기기 로직 끝부분에 추가한다:

```python
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
    self._copy_btn.hide()        # ← 추가
    self._new_file_btn.hide()    # ← 추가
    self._stack.setCurrentIndex(0)   # ← 추가: DropZone으로 복귀
    self._result_text.clear()        # ← 추가: 이전 결과 초기화
    self._output_path = None
```

- [ ] **Step 3: `_connect_signals` — 새 버튼 시그널 연결**

`src/ui/main_window.py`의 `_connect_signals` 메서드에 추가한다:

```python
def _connect_signals(self) -> None:
    self._drop_zone.file_dropped.connect(self._on_file_dropped)
    self._drop_zone.error_occurred.connect(self._show_error)
    self._cancel_btn.clicked.connect(self._on_cancel)
    self._finder_btn.clicked.connect(self._reveal_in_finder)
    self._open_btn.clicked.connect(self._open_file)
    self._retry_btn.clicked.connect(self._check_model_on_startup)
    self._copy_btn.clicked.connect(self._on_copy)           # ← 추가
    self._new_file_btn.clicked.connect(self._reset_to_idle) # ← 추가
```

- [ ] **Step 4: `keyPressEvent` — Escape 키가 결과 뷰에서도 동작하도록 수정**

`src/ui/main_window.py`의 `keyPressEvent`를 수정한다:

```python
def keyPressEvent(self, event) -> None:
    if event.key() == Qt.Key.Key_O and event.modifiers() == Qt.KeyboardModifier.MetaModifier:
        self._open_file_dialog()
    elif event.key() == Qt.Key.Key_Period and event.modifiers() == Qt.KeyboardModifier.MetaModifier:
        self._on_cancel()
    elif event.key() == Qt.Key.Key_Escape:
        # 에러 상태이거나 결과 뷰가 보이는 경우 IDLE로 복귀
        if (self._drop_zone.current_state == DropZoneState.ERROR
                or self._stack.currentIndex() == 1):
            self._reset_to_idle()
    else:
        super().keyPressEvent(event)
```

- [ ] **Step 5: 기존 테스트 통과 확인**

```bash
python -m pytest tests/ -v
```

기대 결과: 모든 기존 테스트 PASS

- [ ] **Step 6: 커밋**

```bash
git add src/ui/main_window.py
git commit -m "feat(ui): 전체 복사 + 새 파일 변환 + Escape 키 결과 뷰 지원"
```

---

## Task 5: 수동 테스트

**Files:** 없음 (검증 전용)

- [ ] **Step 1: 변환 완료 → 텍스트 뷰 확인**

```bash
PYTHONPATH=. uv run python src/main.py
```

`.m4a` 또는 `.mp4` 파일 드롭 후:
- 텍스트 뷰가 DropZone 자리에 나타남
- 타임스탬프 포함 전체 텍스트 표시
- 스크롤 동작

- [ ] **Step 2: "전체 복사" 확인**

- "전체 복사" 클릭 → "복사됨 ✓"로 변경
- 1.5초 후 "전체 복사"로 복원
- TextEdit(메모장 등) 앱에서 Cmd+V → 전체 텍스트 붙여넣기 확인

- [ ] **Step 3: "새 파일 변환" + Escape 확인**

- "새 파일 변환" 클릭 → DropZone 복귀, 새 파일 드롭 가능 확인
- 결과 뷰에서 Escape 키 → DropZone 복귀 확인

- [ ] **Step 4: macOS 알림 확인**

- 변환 완료 시 상단 우측에 "Voice Ledger — 변환 완료: 파일명" 알림 표시
- 시스템 환경설정 > 알림에서 Voice Ledger 권한이 없으면 최초 허용 필요

- [ ] **Step 5: 취소 + 오류 → IDLE 복귀 확인**

- 변환 중 취소 → 텍스트 뷰 없이 IDLE 복귀
- 오류 발생 → ERROR 상태 표시, 4초 후 IDLE 복귀

- [ ] **Step 6: 60초 자동 복귀 확인 (선택)**

- 결과 뷰에서 60초 대기 → DropZone 자동 복귀

- [ ] **Step 7: 최종 커밋 (변경 없음 시 스킵)**

테스트 중 발견된 버그 수정 후:

```bash
git add -p
git commit -m "fix(ui): 수동 테스트 후 발견된 버그 수정"
```
