# UX 개선: 인라인 결과 뷰 + macOS 알림

**날짜:** 2026-04-11  
**범위:** `src/ui/main_window.py` (GUI 레이어만, 엔진 변경 없음)

---

## 1. 배경 및 목표

**문제:** 변환 완료 후 결과 텍스트를 앱 안에서 바로 확인하거나 복사할 수 없다. 사용자가 Finder나 텍스트 에디터를 별도로 열어야 한다.

**목표:** 변환 완료 즉시 앱 안에서 텍스트를 확인하고 클립보드에 복사할 수 있도록 한다. 추가로 macOS 시스템 알림으로 완료를 알린다.

**대상 사용자:** 개인 메모·회의 녹음을 텍스트로 변환하는 단일 사용자.

---

## 2. 범위

### 포함

- 변환 완료 후 인라인 텍스트 뷰 표시 (DropZone 자리 교체)
- "전체 복사" 버튼 + "복사됨 ✓" 1.5초 시각 피드백
- "새 파일 변환" 버튼으로 IDLE 복귀
- macOS 시스템 알림 (변환 완료 시)

### 제외

- 텍스트 편집 기능
- 부분 선택 복사 (텍스트 드래그 선택은 OS 기본 동작으로 지원됨)
- 변환 기록 저장/관리
- 여러 파일 배치 처리

---

## 3. UI 상태 머신

```
IDLE → PROCESSING → RESULT   (성공)
                  → ERROR    (실패)
PROCESSING → CANCELLING → IDLE
RESULT → IDLE               (새 파일 변환 버튼)
```

**`RESULT` 상태 추가:** 기존 `SUCCESS` 상태를 `RESULT`로 교체. DropZone 숨김, 텍스트 뷰 표시.

---

## 4. 컴포넌트 구조 변경

### 레이아웃

```
QVBoxLayout
  └─ QStackedWidget          ← 신규
       ├─ [0] DropZone        (IDLE / PROCESSING / CANCELLING / ERROR)
       └─ [1] QTextEdit       (RESULT 상태, readOnly=True)
  └─ QProgressBar            (기존 유지)
  └─ QLabel (status)         (기존 유지)
  └─ QHBoxLayout (buttons)   (버튼 추가)
```

### 신규 위젯

| 위젯 | 타입 | 설명 |
|------|------|------|
| `self._stack` | `QStackedWidget` | DropZone / 텍스트 뷰 전환 |
| `self._result_text` | `QTextEdit` | 변환 결과 표시, 읽기 전용 |
| `self._copy_btn` | `QPushButton` | "전체 복사" — primary 버튼 |
| `self._new_file_btn` | `QPushButton` | "새 파일 변환" — IDLE 복귀 |

### 제거

- `DropZoneState.SUCCESS` 열거값 삭제 — 더 이상 사용하지 않음  
  `_on_transcription_finished`에서 `set_state(SUCCESS)` 호출을 제거하고, 스택 전환(`setCurrentIndex(1)`)만 수행한다.

---

## 5. 동작 상세

### 5.1 변환 완료 시 (`_on_transcription_finished`)

1. 출력 `.txt` 파일을 읽어 `QTextEdit`에 로드
2. `QStackedWidget` 인덱스를 1(텍스트 뷰)로 전환
3. 버튼 표시: `_copy_btn`, `_new_file_btn`, `_finder_btn`
4. macOS 알림 발송

```python
def _on_transcription_finished(self, output_path: str) -> None:
    self._stop_all_animation_timers()
    self._output_path = output_path
    # 텍스트 로드
    with open(output_path, encoding="utf-8") as f:
        self._result_text.setPlainText(f.read())
    # 뷰 전환
    self._stack.setCurrentIndex(1)
    # 버튼
    self._progress_bar.setValue(100)
    self._status_label.hide()
    self._cancel_btn.hide()
    self._copy_btn.show()
    self._new_file_btn.show()
    self._finder_btn.show()
    self._open_btn.show()
    # 알림
    _notify_completion(os.path.basename(output_path))
    self._idle_timer.start(60000)
```

### 5.2 전체 복사 (`_on_copy`)

```python
def _on_copy(self) -> None:
    QApplication.clipboard().setText(self._result_text.toPlainText())
    self._copy_btn.setText("복사됨 ✓")
    QTimer.singleShot(1500, lambda: self._copy_btn.setText("전체 복사"))
```

### 5.3 새 파일 변환 (`_reset_to_idle` 재사용)

`_reset_to_idle()`에 스택 인덱스를 0으로 복귀하는 로직 추가:

```python
def _reset_to_idle(self) -> None:
    # 기존 로직 ...
    self._stack.setCurrentIndex(0)
    self._result_text.clear()
    self._copy_btn.hide()
    self._new_file_btn.hide()
```

### 5.4 macOS 알림

```python
def _notify_completion(filename: str) -> None:
    try:
        subprocess.run(
            ["osascript", "-e",
             f'display notification "변환 완료: {filename}" with title "Voice Ledger"'],
            timeout=3,
        )
    except Exception:
        pass  # 알림 실패는 무시
```

- `subprocess`는 이미 `_reveal_in_finder` 등에서 사용 중 — 일관된 패턴
- `timeout=3` 으로 블로킹 방지
- 실패해도 핵심 기능에 영향 없음

---

## 6. 에러 처리

- 텍스트 파일 읽기 실패 시: `_on_transcription_error` 호출 (기존 에러 경로 재사용), 텍스트 뷰 표시하지 않음
- macOS 알림 실패: 무시 (try/except)
- 취소 후 RESULT 상태 잔류 없음: `_on_transcription_cancelled` → `_reset_to_idle` 경로 유지

---

## 7. 테스트 체크리스트

수동 테스트 (GUI 자동화 없음):

- [ ] 변환 완료 → 텍스트 뷰 나타남, 내용 정확함
- [ ] 긴 텍스트 → 스크롤 동작
- [ ] "전체 복사" → 클립보드에 전체 텍스트 (다른 앱 붙여넣기 확인)
- [ ] "복사됨 ✓" → 1.5초 후 "전체 복사"로 복귀
- [ ] "새 파일 변환" → DropZone 복귀, 새 파일 드롭 가능
- [ ] macOS 알림 표시
- [ ] 오류 발생 시 텍스트 뷰 표시 안 됨
- [ ] 취소 → IDLE 복귀, 텍스트 뷰 없음
- [ ] 60초 자동 IDLE 복귀 시 스택 정리됨

기존 엔진 테스트: 변경 없음 (`tests/unit/`, `tests/integration/` 영향 없음)
