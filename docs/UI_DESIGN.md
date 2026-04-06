# UI/UX 설계 문서
# Voice Ledger

**버전:** 2.0
**작성일:** 2026-04-06
**상태:** 개정됨 (PyQt6 전환 + Precision Design System 적용)

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| 1.0 | 2026-04-05 | 최초 작성 |
| 1.1 | 2026-04-05 | macOS HIG 반영, 창 크기 확대, 다크모드/온보딩/마이크로인터랙션 추가 |
| 1.2 | 2026-04-05 | 창 크기 resizable 설계 전환, 다크모드 색상 체계 완성, 드롭존 상태 애니메이션 상세화, 온보딩 UX 완성, 에러 메시지 톤 전면 개선, 접근성 명세 강화, 마이크로인터랙션 타이밍 명세, 완료 후 UX 흐름 상세화 |
| 2.0 | 2026-04-06 | PyQt6 전환, Precision Design System 도입 (극도의 미니멀리즘, Apple Blue 단일 액센트, 8px 그리드 기반) |

---

## 1. 디자인 원칙

- **Precision (정밀성):** 모든 수치는 8px 그리드에 근거하며, 불필요한 장식을 완전히 배제. 각 픽셀이 목적을 가짐.
- **Restraint (절제):** 색상은 Apple Blue 단일 액센트만 사용. 화면 요소를 최소화하고, 단색 기반 인터페이스로 시각적 정제함.
- **Clarity (명확성):** 앱 상태가 언제나 즉각적으로 파악 가능. 모호한 상태나 숨겨진 피드백 없음.
- **Native (네이티브):** macOS HIG를 준수하며, PyQt6의 네이티브 렌더링으로 시스템 룩앤필 최대한 활용.

---

## 2. 프레임워크 마이그레이션: Tkinter → PyQt6

### 2.1 변경 이유

- **Tkinter의 한계:** macOS에서 스타일 커스터마이징 부족, 시스템 룩앤필 제한
- **PyQt6의 이점:** 네이티브 렌더링, 고급 애니메이션 지원, 시스템 통합 우수

### 2.2 설치 및 의존성

```bash
pip install PyQt6
```

**requirements.txt 업데이트:**
```
PyQt6>=6.6.0
```

### 2.3 주요 변경점

| 항목 | Tkinter | PyQt6 |
|------|---------|-------|
| 창 생성 | `Tk()` | `QApplication` + `QMainWindow` |
| 레이아웃 | `pack()`, `grid()` | `QVBoxLayout`, `QHBoxLayout` |
| 애니메이션 | `after()` 루프 | `QPropertyAnimation`, `QSequentialAnimationGroup` |
| 스타일 | 색상 지정 | `QStyleFactory`, 팔레트 커스터마이징 |
| 드래그앤드롭 | `drop_target_register` | `QDropEvent`, `setAcceptDrops()` |
| 다크모드 감지 | `subprocess + defaults` | `QPalette`, `systemAppearance()` |

---

## 3. 창 스펙 및 외관

### 3.1 창 설정

| 항목 | 상세 내용 | 비고 |
|------|-----------|-----|
| **기본 크기** | 780 × 520 px | Precision 디자인에 최적 |
| **최소 크기** | 480 × 340 px | 이 미만으로는 레이아웃 붕괴 |
| **최대 크기** | 1000 × 640 px | 매우 넓은 모니터용 |
| **크기 조절** | 허용 (min/max 범위 내) | `setMinimumSize()`, `setMaximumSize()` |
| **다크 모드** | 완벽 지원 (시스템 설정 자동 추적) | 아래 3.2 색상 체계 참고 |
| **타이틀 바** | 통합 타이틀 바 (Unified) | `setUnifiedTitleAndToolBarOnMac(True)` |
| **타이틀** | "Voice Ledger" | 타이틀 바에만 표시, 창 내부 아이콘 없음 |

### 3.2 다크모드 색상 체계

PyQt6는 `QPalette`와 `QStyleFactory`를 통해 시스템 색상을 자동 추적한다.

#### 색상 팔레트

| 역할 | 라이트모드 | 다크모드 | 용도 |
|------|-----------|---------|------|
| **창 배경** | `#F2F2F2` | `#1E1E1E` | 창 전체 배경 |
| **드롭존 배경 (기본)** | `#FFFFFF` | `#2A2A2A` | 드롭존 영역 |
| **드롭존 배경 (Hover)** | `#EBF3FF` | `#1A2E44` | 마우스 오버 시 5% tint |
| **드롭존 테두리 (기본)** | `#D1D1D6` | `#484848` | 1px dashed |
| **드롭존 테두리 (Hover)** | `#007AFF` | `#0A84FF` | 2px solid, Apple Blue |
| **주 텍스트** | `#1C1C1E` | `#F2F2F7` | 제목, 주요 문구 |
| **보조 텍스트** | `#6C6C70` | `#8E8E93` | 상태, 설명 문구 |
| **터셔리 텍스트** | `#A2A2A7` | `#5E5E62` | 안내, 보조 설명 |
| **진행 바 트랙** | `#D1D1D6` | `#3A3A3C` | 진행 바 배경 |
| **진행 바 필** | `#007AFF` | `#0A84FF` | 진행 바 채우기 (Apple Blue) |
| **성공 강조** | `#34C759` | `#30D158` | 완료 상태 |
| **에러 강조** | `#FF3B30` | `#FF453A` | 에러 상태 |

#### PyQt6 색상 구현

```python
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication
import subprocess

def is_dark_mode() -> bool:
    result = subprocess.run(
        ["defaults", "read", "-g", "AppleInterfaceStyle"],
        capture_output=True, text=True
    )
    return result.stdout.strip() == "Dark"

def create_palette() -> QPalette:
    palette = QPalette()
    
    if is_dark_mode():
        palette.setColor(QPalette.ColorRole.Window, QColor("#1E1E1E"))
        palette.setColor(QPalette.ColorRole.Base, QColor("#2A2A2A"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#F2F2F7"))
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#8E8E93"))
    else:
        palette.setColor(QPalette.ColorRole.Window, QColor("#F2F2F2"))
        palette.setColor(QPalette.ColorRole.Base, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#1C1C1E"))
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#6C6C70"))
    
    return palette
```

---

## 4. 화면 구성 및 레이아웃

### 4.1 메인 창 레이아웃 (ASCII 목업)

```
┌─────────────────────────────────────────────────────────────┐
│ Voice Ledger                                     − □ × │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                     │   │
│  │              ↓ (32px 아이콘)                        │   │
│  │     파일을 드롭하거나 Cmd+O로 선택                   │   │
│  │     .m4a · .mp4 지원                                │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  진행률: 변환 중 · 00:23:15 / 01:00:00                     │
│                                                             │
│  ████████████████████████░░░░░░░░  72%                     │
│                                                             │
│                               [ 취소 ]                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 온보딩 화면 레이아웃 (최초 실행)

```
┌─────────────────────────────────────────────────────────────┐
│ Voice Ledger                                     − □ × │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│        Whisper 모델 준비 중                                  │
│                                                             │
│  ████████████████░░░░░░░░░░░░░░░░  48%                     │
│  745 MB / 1.5 GB · 남은 시간 약 3분                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 완료 화면 레이아웃

```
┌─────────────────────────────────────────────────────────────┐
│ Voice Ledger                                     − □ × │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ✓ 완료                                                      │
│                                                             │
│  meeting_20260405.txt                                       │
│                                                             │
│  [ Finder에서 보기 ]  [ 파일 열기 ]                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. 화면 상태 명세 (State Machine)

### STATE 1: IDLE

**화면 구성:**
- Drop Zone: 중앙 화살표 아이콘 (크기 32px, secondary text color)
- 텍스트 행 1: "파일을 드롭하거나 Cmd+O로 선택" (13px, secondary)
- 텍스트 행 2: ".m4a · .mp4 지원" (11px, tertiary)
- Progress Bar: 숨김
- Status 레이블: 없음

**스타일:**
- Drop Zone 테두리: 1px dashed `#D1D1D6` (라이트) / `#484848` (다크)
- 배경: `#FFFFFF` (라이트) / `#2A2A2A` (다크)

### STATE 2: DRAG HOVER

**시각 변화:**
- Drop Zone 테두리: 2px solid Apple Blue (`#007AFF` 라이트 / `#0A84FF` 다크)
- 배경: Apple Blue 5% tint (`#EBF3FF` 라이트 / `#1A2E44` 다크)
- 아이콘: 화살표 → "+" 아이콘으로 즉시 교체
- 애니메이션: 150ms `QEasingCurve.OutCubic`

**구현:**
```python
anim = QPropertyAnimation(drop_zone, b"borderColor")
anim.setDuration(150)
anim.setStartValue(QColor("#D1D1D6"))
anim.setEndValue(QColor("#007AFF"))
anim.setEasingCurve(QEasingCurve.Type.OutCubic)
anim.start()
```

### STATE 3: PROCESSING

**화면 구성:**
- Drop Zone 영역: waveform 아이콘 + 상태 텍스트
- Progress Bar: fade-in 표시, Apple Blue fill
- Status 텍스트: "변환 중 · 00:23:15 / 01:00:00" (SF Mono, 11px)
- Cancel 버튼: 우측 하단에 표시 (borderless)

**스타일:**
- Drop Zone: 상호작용 불가 (`setAcceptDrops(False)`)
- 커서: `Qt.CursorShape.WaitCursor`

### STATE 4: SUCCESS

**시각 변화:**
- Progress Bar: Apple Blue → Green 전환 (400ms linear)
- 아이콘: checkmark (✓)
- 텍스트: "완료 — meeting_20260405.txt" (green accent, 12px)
- 3초 후 자동으로 IDLE로 복귀 (카운트다운 없음, 조용히 전환)

**구현:**
```python
color_anim = QPropertyAnimation(progress_bar, b"fillColor")
color_anim.setDuration(400)
color_anim.setStartValue(QColor("#007AFF"))
color_anim.setEndValue(QColor("#34C759"))
color_anim.setEasingCurve(QEasingCurve.Type.Linear)
color_anim.start()

# 3초 후 IDLE로 복귀
QTimer.singleShot(3000, self.reset_to_idle)
```

### STATE 5: ERROR

**시각 변화:**
- Drop Zone 테두리: 2px solid Red (`#FF3B30` 라이트 / `#FF453A` 다크)
- shake 애니메이션 (3회, 4px 좌우, 200ms 총 소요)
- 에러 텍스트: "지원하지 않는 파일 형식입니다 (.m4a, .mp4 사용)" (red, 12px)
- 4초 후 IDLE 복귀

**shake 구현:**
```python
def shake_animation(widget):
    offsets = [4, -4, 3, -3, 2, -2, 1, -1, 0]
    interval = 25  # ms per step
    original_x = widget.geometry().x()
    
    def step(i):
        if i < len(offsets):
            widget.move(original_x + offsets[i], widget.geometry().y())
            QTimer.singleShot(interval, lambda: step(i + 1))
        else:
            widget.move(original_x, widget.geometry().y())
    
    step(0)
```

### STATE 6: MODEL DOWNLOAD (최초 실행)

**화면 구성:**
- 타이틀: "Whisper 모델 준비 중" (14px, primary text)
- Progress Bar: fade-in 표시
- Status 텍스트: "742 MB / 1.5 GB · 남은 시간 약 3분" (SF Mono, 11px)
- 별도 창이 아닌 메인 창 안에서 표시

**스타일:**
- 배경: 투명 처리 없음, 일반 창 배경 사용
- Drop Zone 영역: 숨김 (프로그레스 영역으로 대체)

---

## 6. 컴포넌트 상세 가이드라인

### 6.1 DropZone

#### 기본 명세

- **형태:** 둥근 모서리 8pt (`setRadius(8)`)
- **테두리:** 기본 1px dashed, hover 시 2px solid
- **크기:** 창 너비에서 좌우 패딩 24px 제외한 전체 폭, 높이는 창 높이의 약 40~45%
- **구현:** `QFrame` + `QVBoxLayout`

#### 드롭 오버 시 Visual Affordance

1. **테두리 색상 변경:** `#007AFF` (Apple Blue)
2. **배경 tint:** Apple Blue 5% opacity
3. **아이콘 교체:** ↓ → + 아이콘
4. **커서 변경:** `Qt.CursorShape.DragCopyCursor`

```python
def dragEnterEvent(self, event: QDragEnterEvent):
    if event.mimeData().hasUrls():
        event.acceptProposedAction()
        self.set_state(DropZoneState.HOVER)

def dragLeaveEvent(self, event: QDragLeaveEvent):
    self.set_state(DropZoneState.IDLE)
```

### 6.2 ProgressBar

**명세:**
- **높이:** 6pt (pill shape, 양끝 둥근 형태)
- **구현:** `QProgressBar` + 커스텀 `QProxyStyle`
- **색상:** Apple Blue 기본, 완료 시 Green 전환
- **애니메이션:** 목표값으로의 smooth interpolation (0.15 lerp per frame)

```python
class CustomProgressBar(QProgressBar):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #D1D1D6;
                border-radius: 3px;
                height: 6px;
            }
            QProgressBar::chunk {
                background-color: #007AFF;
                border-radius: 3px;
            }
        """)
```

### 6.3 에러 메시지 (Tone of Voice)

**원칙:**
- 기술적 용어 노출 금지
- 무엇이 잘못되었는지보다 무엇을 하면 되는지 먼저 안내
- 사용자 실수가 아닌 경우 공감 표현 포함

#### 에러 메시지 대조표

| 상황 | 메시지 | 액션 |
|------|--------|------|
| 지원하지 않는 파일 형식 | "이 파일 형식은 지원하지 않습니다. .m4a 또는 .mp4 파일을 사용해 주세요." | — |
| 파일 읽기 권한 부족 | "이 파일에 접근할 수 없습니다. Finder에서 파일을 우클릭 후 정보를 확인해 주세요." | — |
| 오디오 트랙 없음 | "이 파일에는 오디오가 포함되어 있지 않습니다. 화면 녹화 파일이라면 오디오 포함 여부를 확인해 주세요." | — |
| 모델 다운로드 실패 | "인터넷 연결 문제로 다운로드가 중단되었습니다. 연결 상태를 확인한 뒤 다시 시도해 주세요." | [다시 시도] |
| 메모리 부족 | "변환에 필요한 메모리가 부족합니다. 다른 앱을 종료한 뒤 다시 시도해 주세요." | — |
| 변환 중 예외 | "변환 중 문제가 발생했습니다. 로그 파일을 첨부해 문의하시면 빠르게 도와드리겠습니다." | [로그 폴더 열기] |
| 다중 파일 드롭 | "한 번에 하나의 파일만 변환할 수 있습니다. 파일을 하나씩 드래그해 주세요." | — |
| 변환 중 새 파일 드롭 | "지금 변환이 진행 중입니다. 완료 후 다음 파일을 드래그해 주세요." | — |

---

## 7. 마이크로인터랙션 및 애니메이션

### 7.1 상태 전환 타이밍

| 전환 | 방식 | 시간 | PyQt6 구현 |
|------|------|------|-----------|
| IDLE → DRAG HOVER | 테두리 색상 + 배경 tint | 150ms | `QPropertyAnimation` + `OutCubic` |
| DRAG HOVER → IDLE | 테두리 색상 복귀 | 150ms | `QPropertyAnimation` + `InCubic` |
| IDLE → PROCESSING | 드롭존 dim + 상태 영역 나타남 | 200ms | `QParallelAnimationGroup` |
| PROCESSING → SUCCESS | 진행 바 색상 변환 + checkmark | 400ms | `QSequentialAnimationGroup` |
| SUCCESS → IDLE | UI fade-out + 드롭존 fade-in | 300ms | `QParallelAnimationGroup` |
| IDLE → ERROR | 에러 텍스트 + shake | 즉시 + 200ms | `shake_animation()` + 타이머 |
| ERROR → IDLE | 에러 상태 fade-out | 300ms | `QPropertyAnimation` |

### 7.2 Spring 애니메이션 (완료 checkmark)

```python
def show_checkmark():
    animation_group = QSequentialAnimationGroup()
    
    scale_anim = QPropertyAnimation(checkmark_icon, b"scale")
    scale_anim.setDuration(200)
    scale_anim.setStartValue(0.0)
    scale_anim.setEndValue(1.2)
    scale_anim.setEasingCurve(QEasingCurve.Type.OutBack)
    
    final_anim = QPropertyAnimation(checkmark_icon, b"scale")
    final_anim.setDuration(100)
    final_anim.setStartValue(1.2)
    final_anim.setEndValue(1.0)
    final_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
    
    animation_group.addAnimation(scale_anim)
    animation_group.addAnimation(final_anim)
    animation_group.start()
```

---

## 8. 최초 실행 온보딩

### 8.1 온보딩 UX 흐름

```
[앱 실행]
    │
    ├─ 모델 있음 ──→ [메인 화면 (IDLE)]
    │
    └─ 모델 없음
           │
           ▼
    [온보딩: 모델 다운로드]
    ─ 제목: "Whisper 모델 준비 중"
    ─ 진행 바 + 다운로드 진행률
    ─ 텍스트: "742 MB / 1.5 GB · 남은 시간 약 3분"
           │
           ├─ 다운로드 실패 ──→ [에러 메시지 + 재시도 버튼]
           │
           └─ 다운로드 완료
                  │
                  ▼
           [완료 전환 애니메이션]
           ─ checkmark 나타남 (300ms spring)
           ─ 1500ms 후 메인 화면으로 fade-in (400ms)
```

### 8.2 다운로드 진행률 계산

```python
import time

class DownloadProgress:
    def __init__(self, total_bytes: int):
        self.total = total_bytes
        self.downloaded = 0
        self.start_time = time.time()
        self.speed_samples: list[float] = []

    def update(self, chunk_size: int):
        self.downloaded += chunk_size
        elapsed = time.time() - self.start_time
        if elapsed > 0:
            speed = self.downloaded / elapsed
            self.speed_samples.append(speed)
            if len(self.speed_samples) > 10:
                self.speed_samples.pop(0)

    @property
    def eta_seconds(self) -> float | None:
        if not self.speed_samples:
            return None
        avg_speed = sum(self.speed_samples) / len(self.speed_samples)
        remaining = self.total - self.downloaded
        return remaining / avg_speed if avg_speed > 0 else None

    @property
    def percent(self) -> float:
        return (self.downloaded / self.total * 100) if self.total > 0 else 0
```

---

## 9. 완료 후 UX 흐름

### 9.1 완료 화면 구성

```
✓ 완료

meeting_20260405.txt

[ Finder에서 보기 ]  [ 파일 열기 ]
```

**상세 명세:**
- 제목: "✓ 완료" (14px, primary text)
- 파일명: "meeting_20260405.txt" (13px, primary text)
- 버튼: 좌우 정렬, 각 44px 높이 (터치 타겟)

### 9.2 "Finder에서 보기" 동작

```python
import subprocess

def reveal_in_finder(file_path: str):
    """파일을 Finder에서 선택 상태로 표시"""
    subprocess.run(["open", "-R", file_path])
```

### 9.3 "파일 열기" 동작

```python
import subprocess

def open_file(file_path: str):
    """기본 앱으로 파일 열기"""
    subprocess.run(["open", file_path])
```

### 9.4 자동 복귀

- 완료 화면은 **60초 후** 자동으로 IDLE로 복귀
- 복귀 10초 전부터 희미한 카운트다운 표시 없음 (조용한 전환)

---

## 10. 접근성 (Accessibility)

### 10.1 PyQt6 접근성 설정

```python
drop_zone.setAccessibleName("음성 파일 드롭 영역")
drop_zone.setAccessibleDescription(".m4a 또는 .mp4 파일을 드래그하거나 Cmd+O로 파일 선택")

progress_bar.setAccessibleName("변환 진행률")
progress_bar.setAccessibleDescription("{}퍼센트 완료. 예상 남은 시간 {}분".format(value, eta))

button.setAccessibleName("Finder에서 보기")
button.setAccessibleDescription("출력 파일이 있는 폴더를 엽니다")
```

### 10.2 키보드 포커스 순서 (Tab Order)

```
IDLE 상태:
  1. Drop Zone (Return으로 파일 선택 다이얼로그 열기)

PROCESSING 상태:
  1. Cancel 버튼

SUCCESS 상태:
  1. "Finder에서 보기" 버튼
  2. "파일 열기" 버튼

ERROR 상태:
  1. Drop Zone (Return으로 재시도)
```

**PyQt6 구현:**
```python
drop_zone.setFocusPolicy(Qt.FocusPolicy.TabFocus)
button1.setFocus()
button2.setTabOrder(button1, button2)
```

### 10.3 포커스 링

- **색상:** Apple Blue (`#007AFF` 라이트 / `#0A84FF` 다크)
- **두께:** 2pt
- **오프셋:** 요소 경계 2pt 외부

```python
def set_focus_ring(widget):
    widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    widget.setStyleSheet("""
        *:focus {
            outline: 2px solid #007AFF;
            outline-offset: 2px;
        }
    """)
```

### 10.4 최소 클릭 타겟 크기

macOS HIG 권장 최소 44×44pt 준수:

| 요소 | 최소 타겟 크기 |
|------|-------------|
| 버튼 | 120×44pt (패딩 포함) |
| Drop Zone | 창 전체 너비 × 180pt |

### 10.5 색상 대비

모든 텍스트는 WCAG AA 기준 이상 (최소 4.5:1) 만족

### 10.6 키보드 단축키

| 단축키 | 동작 |
|--------|------|
| `Cmd+O` | 파일 선택 대화상자 열기 |
| `Cmd+.` | 진행 중인 변환 취소 |
| `Return` | Drop Zone 포커스 시 파일 선택 |
| `Space` | 버튼 활성화 |
| `Tab` | 포커스 이동 (순방향) |
| `Shift+Tab` | 포커스 이동 (역방향) |
| `Escape` | 에러 해제 / 완료 화면 닫기 |

---

## 11. 상태 머신

```
[최초 실행]
    │
    ├─ 모델 있음 ──────────────→ [IDLE]
    │
    └─ 모델 없음
           │
           ▼
    [MODEL_DOWNLOAD]
           │
       실패/재시도
           │
           ▼
    [완료] ──────────────→ [IDLE]
                              │
        ┌──────────────────────┘
        │ 유효한 파일 드롭
        ▼
    [DRAG_HOVER]
        │
    [drop]
        ▼
    [PROCESSING] ← Cmd+. (취소)
        │                  │
        │          [IDLE] (임시파일 삭제)
        │
        ├─ 오류 발생 ──→ [ERROR]
        │                  │ (4초 후)
        │                  ▼
        │              [IDLE]
        │
        └─ 완료 ──→ [SUCCESS]
                        │ (3초 후)
                        ▼
                    [IDLE]
```

---

## 12. 미래 확장 고려사항

| 기능 | UI 영향 | 대응 방안 |
|------|--------|----------|
| 배치 처리 (다중 파일) | 파일 큐 표시 필요 | Drop Zone 아래 스크롤 영역 확장 |
| 모델 선택 | 설정 패널 필요 | `Cmd+,` 단축키에 설정 창 |
| 변환 이력 | 히스토리 표시 필요 | 사이드바 또는 별도 창 |
| 화자 분리 | 결과 형식 변경 | `[화자1 00:00:05]` 타임스탬프 확장 |
