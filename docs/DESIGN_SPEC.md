# 디자인 시스템 명세서
# Voice Ledger

**버전:** 1.0  
**작성일:** 2026-04-06  
**상태:** 최종 명세  

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| 1.0 | 2026-04-06 | 초판: PyQt6 마이그레이션 기반 완전 디자인 명세 |

---

## 1. 디자인 철학 & 원칙

Voice Ledger는 **정밀한 기계 도구(Precision Instrument)**로서의 미학을 추구한다. Logic Pro, Leica 카메라, 오디오 장비 같은 고급 도구의 단정함과 기능성을 본받는다.

### 1.1 핵심 4가지 원칙

#### Precision (정확성)
- 모든 상호작용은 예측 가능하고 명확하다.
- 상태 표시는 정확하고 실시간으로 반영된다.
- 타이밍과 애니메이션은 정밀하게 측정된다(밀리초 단위).
- 사용자가 앱의 현재 상태를 항상 파악할 수 있어야 한다.

#### Restraint (절제)
- 모든 시각적 요소는 기능적 이유로만 존재한다.
- 장식적 색상, 과도한 둥근 모서리, 글래스모피즘 금지.
- 단일 액센트 컬러(Apple Blue)만 사용.
- 여백과 공간은 의도적으로 설계된다.

#### Clarity (명확성)
- 사용자 피드백은 즉각적이고 이해하기 쉽다.
- 에러 메시지는 원인을 명시하고 다음 행동을 안내한다.
- 타이포그래피는 계층 구조를 명확히 한다.
- 색상은 의미를 전달한다(파란색=작업, 초록색=완료, 빨간색=오류).

#### Native (네이티브)
- Apple Human Interface Guidelines 엄격히 준수.
- macOS의 표준 폰트, 색상, 인터랙션 패턴 사용.
- 시스템 다크 모드 완벽 지원.
- 사용자가 macOS 앱이라고 자연스럽게 느낄 수 있어야 한다.

### 1.2 금지 사항 (Anti-patterns)

다음 요소들을 절대 사용하지 말 것:

| 금지 항목 | 이유 | 대체 방안 |
|----------|------|----------|
| 보라색/핑크 그라디언트 | AI 앱의 과도한 마케팅 미학 | 단색 또는 시스템 색상만 사용 |
| 글래스모피즘(반투명) | 현대적이지 않고 가독성 해침 | 명확한 배경색 사용 |
| 과도한 둥근 모서리 (>8px) | 부정확해 보임 | 8px 이하, 또는 정사각형(선명함) |
| 이모지 또는 장식 아이콘 | 비전문적으로 보임 | SF Symbol만 사용 |
| 다중 액센트 색상 | 초점 분산, 혼란 초래 | Apple Blue 한 가지만 |
| 그림자 남용 | 계층이 불명확함 | 1px 구분선으로 충분 |
| 무한 로딩 애니메이션 | 진행 상황을 알 수 없음 | 백분율 진행 바 사용 |
| 자동 재생 사운드 | 예측 불가능한 경험 | 명시적 사용자 작업만 반응 |

---

## 2. 프레임워크 결정: Tkinter → PyQt6

### 2.1 마이그레이션 근거

**현재 (MVP):** Tkinter
- 장점: 표준 라이브러리, 추가 설치 불필요
- 단점: 커스텀 스타일링 제한, macOS HIG 준수 어려움, 상태 관리 복잡

**업그레이드 대상:** PyQt6
- 산업 표준 GUI 프레임워크 (데스크톱 앱)
- 완벽한 CSS 기반 스타일시트 (QSS) 지원
- 네이티브 macOS QStyle 활용
- 비동기/스레딩 개선 (QThread)
- 애니메이션 프레임워크 (QPropertyAnimation, QSequentialAnimationGroup)
- 접근성 (QAccessibleInterface) 완벽 지원

### 2.2 PyQt6 + macOS QStyle

```bash
# 설치
pip install PyQt6 PyQt6-addons
```

**macOS 네이티브 룩앤필 활용:**

```python
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import Qt

app = QApplication([])

# macOS 시스템 스타일 자동 적용
app.setStyle("Macintosh")  # 또는 시스템 기본값

# 다크 모드 감지
from PyQt6.QtGui import QPalette, QColor
palette = app.palette()
is_dark = palette.color(QPalette.ColorRole.Base).lightness() < 128

main_window = QMainWindow()
main_window.show()
app.exec()
```

**QStyle::StandardPixmap을 통한 시스템 아이콘:**

```python
from PyQt6.QtWidgets import QStyle
from PyQt6.QtGui import QIcon

# 시스템 제공 아이콘 (각 플랫폼에 맞게 자동 선택)
icon = style.standardIcon(QStyle.StandardPixmap.SP_DialogYesButton)
```

---

## 3. 타이포그래피 시스템

### 3.1 폰트 선택

| 용도 | 폰트 | 이유 |
|------|------|------|
| **UI 텍스트 (모든 라벨, 버튼, 상태)** | SF Pro (`.AppleSystemUIFont`) | macOS 시스템 폰트, 최고의 가독성 |
| **코드/경로 (파일명, 타임스탬프, 경로)** | SF Mono | 고정폭, 기술적 내용 강조 |

**PyQt6 구현:**

```python
from PyQt6.QtGui import QFont

# UI 폰트 (SF Pro)
def get_system_font():
    font = QFont()
    font.setFamily(".AppleSystemUIFont")
    return font

# 모노스페이스 폰트 (SF Mono)
def get_monospace_font():
    font = QFont()
    font.setFamily("SF Mono")
    if not font.exactMatch():
        font.setFamily("Monaco")  # Fallback
    font.setFixedPitch(True)
    return font
```

### 3.2 폰트 사이즈 스케일 (pt)

| 역할 | 크기 | 용도 | 예시 |
|------|------|------|------|
| Caption (자막) | 11px | 보조 텍스트, 파일 정보 | "~/Downloads · 48 KB · 방금 전" |
| Body (본문) | 13px | 일반 라벨, 상태 메시지 | "변환 중 · 00:23:15 / 01:00:00" |
| Title (제목) | 15px | 주 상태 텍스트 | "변환이 완료되었습니다" |
| Hero (강조) | 20px | 온보딩 제목 | "음성 인식 엔진을 준비하고 있어요" |
| Display (대제목) | 28px | 앱 이름 (경우에 따라) | 타이틀 바에서 사용하지 않음 (정책) |

### 3.3 폰트 웨이트

**사용 규칙:** Regular(400) / Medium(500) / Semibold(600)만 사용

| 웨이트 | 사용 | 예시 |
|--------|------|------|
| Regular (400) | 일반 텍스트, 설명 | 상태 메시지, 파일 경로 |
| Medium (500) | 강조가 필요한 텍스트 | 주 상태 메시지 ("변환 중") |
| Semibold (600) | 주요 헤딩, 버튼 | "Voice Ledger", 완료 메시지 |

**금지:** Light(300), Bold(700), Black(900) — 과도한 대비나 약한 시각 계층 생성

### 3.4 줄 높이 & 자간

| 용도 | 줄 높이 | 자간 | 설명 |
|------|--------|------|------|
| 단일 라인 | 1.2 (130% of height) | 0 | 일반적인 UI 텍스트 |
| 다중 라인 | 1.5 (150% of height) | -0.2px | 온보딩 설명, 긴 메시지 |
| 고정폭 (코드) | 1.4 | 0 | 타이밍 코드, 파일 경로 |

**PyQt6 QSS 예시:**

```css
QLabel {
    font-family: ".AppleSystemUIFont";
    font-size: 13px;
    line-height: 1.2;
    letter-spacing: 0px;
}

QLabel#status {
    font-size: 13px;
    font-weight: 500;  /* Medium */
}

QLabel#filepath {
    font-family: "SF Mono";
    font-size: 11px;
    line-height: 1.4;
}
```

---

## 4. 컬러 시스템 (라이트 / 다크 모드)

### 4.1 배경 레이어

| 역할 | 라이트 모드 | 다크 모드 | NSColor 레퍼런스 | HEX 코드 |
|------|-----------|---------|-----------------|---------|
| **WindowBackground** | `#ECECEC` | `#1E1E1E` | `windowBackgroundColor` | 라이트: ECECEC / 다크: 1E1E1E |
| **Surface (기본 백그라운드)** | `#F5F5F5` | `#2A2A2A` | `controlBackgroundColor` | 라이트: F5F5F5 / 다크: 2A2A2A |
| **Elevated Surface** | `#FFFFFF` | `#3A3A3C` | `windowBackgroundColor` + elevation | 라이트: FFFFFF / 다크: 3A3A3C |

### 4.2 텍스트 색상

| 역할 | 라이트 모드 | 다크 모드 | NSColor 레퍼런스 |
|------|-----------|---------|-----------------|
| **Primary (주 텍스트)** | `#1C1C1E` | `#F2F2F7` | `labelColor` |
| **Secondary (보조 텍스트)** | `#6C6C70` | `#8E8E93` | `secondaryLabelColor` |
| **Tertiary (약한 텍스트)** | `#A2A2A7` | `#6C6C70` | `tertiaryLabelColor` |
| **Disabled** | `#C0C0C0` | `#5A5A5C` | `disabledControlTextColor` |

### 4.3 액센트 컬러 (Apple Blue만 사용)

| 상황 | 라이트 | 다크 | NSColor 레퍼런스 |
|------|--------|------|-----------------|
| **Primary Accent (작업 상태, 진행 바)** | `#007AFF` | `#0A84FF` | `systemBlue` |
| **Hover/Active 상태** | `#0051D5` (20% 어둡게) | `#147FFF` (10% 밝게) | systemBlue (alpha) |

**규칙:** 절대로 다른 컬러 변형(Red, Green 등) 사용 금지. 시맨틱 컬러는 별도(아래).

### 4.4 시맨틱 컬러

| 의미 | 라이트 | 다크 | NSColor | 용도 |
|------|--------|------|---------|------|
| **Success (완료)** | `#34C759` | `#30D158` | `systemGreen` | 진행 바 완료, 체크마크 |
| **Error (오류)** | `#FF3B30` | `#FF453A` | `systemRed` | 오류 메시지, 드롭존 오류 상태 |
| **Warning (경고)** | `#FF9F0A` | `#FF9500` | `systemOrange` | 경고 아이콘 (덮어쓰기 확인) |

### 4.5 Drop Zone 상태별 색상

| 상태 | 배경색 | 테두리색 | 텍스트색 |
|------|--------|---------|---------|
| **Idle (대기)** | Surface (#F5F5F5 / #2A2A2A) | `#C0C0C0` / `#484848` | Secondary |
| **Hover (마우스 오버)** | Surface (변화 없음) | `#A0A0A0` / `#686868` | Secondary |
| **Active Drag (드래그 중)** | Tinted Blue (#EBF3FF / #1A2E44, 10% alpha) | `#007AFF` / `#0A84FF` (2px solid) | Primary |
| **Processing (변환 중)** | Tinted Blue (유지) | `#007AFF` / `#0A84FF` | Primary |
| **Success (완료)** | Tinted Green (#EBF5EB / #1A2E1A) | `#34C759` / `#30D158` | Primary |
| **Error (오류)** | Tinted Red (#FFF0F0 / #3A1A1A) | `#FF3B30` / `#FF453A` | Primary + Error |

**PyQt6 색상 정의:**

```python
from PyQt6.QtGui import QColor
from PyQt6.QtCore import QSettings

class ColorScheme:
    def __init__(self, is_dark=False):
        self.is_dark = is_dark
        self.colors = {
            # Background
            "window_bg": QColor("#1E1E1E") if is_dark else QColor("#ECECEC"),
            "surface": QColor("#2A2A2A") if is_dark else QColor("#F5F5F5"),
            # Text
            "text_primary": QColor("#F2F2F7") if is_dark else QColor("#1C1C1E"),
            "text_secondary": QColor("#8E8E93") if is_dark else QColor("#6C6C70"),
            # Accent
            "accent_blue": QColor("#0A84FF") if is_dark else QColor("#007AFF"),
            "accent_green": QColor("#30D158") if is_dark else QColor("#34C759"),
            "accent_red": QColor("#FF453A") if is_dark else QColor("#FF3B30"),
            # Borders
            "border_default": QColor("#484848") if is_dark else QColor("#C0C0C0"),
            "border_hover": QColor("#686868") if is_dark else QColor("#A0A0A0"),
        }

    def color(self, key):
        return self.colors.get(key, QColor("#000000"))
```

---

## 5. 스페이싱 & 그리드 시스템

### 5.1 8px 기반 그리드

모든 거리는 8px의 배수로 설정하여 일관성을 유지한다.

| 크기 | 용도 | 예시 |
|------|------|------|
| **4px** | 마이크로 간격 | 아이콘 내부 패딩 |
| **8px** | 최소 여백 | 컴포넌트 간 기본 간격 |
| **12px** | 보조 간격 | 텍스트와 아이콘 사이 |
| **16px** | 기본 패딩 | 창 여백, 섹션 간격 |
| **24px** | 주요 간격 | 섹션 분리 |
| **32px** | 큰 여백 | 영역 간 구분 |
| **48px** | 거대 여백 | 드롭존 내부 여백 |
| **64px** | 최대 여백 | 드롭존 높이 최소값 |

### 5.2 창 여백 (Padding)

- **좌우 여백:** 16px
- **상단 여백:** 12px (타이틀 바 포함)
- **하단 여백:** 16px
- **섹션 간 여백:** 24px

### 5.3 컴포넌트 내부 패딩

| 컴포넌트 | 수평 패딩 | 수직 패딩 |
|---------|---------|---------|
| Drop Zone | 48px | 48px |
| 버튼 | 16px | 8px |
| Status Label | 0 | 8px (위), 16px (아래) |
| Progress Bar | 0 (full width) | 6px (위/아래) |

---

## 6. 창 & 레이아웃

### 6.1 창 기본 스펙

| 항목 | 값 | 설명 |
|------|-----|------|
| **기본 크기** | 780 × 520 px | 드롭존과 상태 영역의 균형 |
| **최소 크기** | 480 × 340 px | UI 요소가 잘리지 않는 최소값 |
| **최대 크기** | 1200 × 800 px | 과도한 확대 방지 |
| **크기 조절** | Resizable (min/max 범위 내) | 사용자 화면 구성에 맞춤 |
| **타이틀 바** | Unified Title Bar (macOS 스타일) | 창 컨트롤(교통신호등) 포함 |
| **다크 모드** | 완벽 지원 (자동 감지) | 시스템 설정 따름 |

**PyQt6 창 설정:**

```python
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Voice Ledger")
        self.setGeometry(100, 100, 780, 520)
        self.setMinimumSize(480, 340)
        self.setMaximumSize(1200, 800)
        
        # macOS 통합 타이틀 바
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
```

### 6.2 레이아웃 구조

```
┌─────────────────────────────────────────┐  
│  🎙 Voice Ledger            — □ ⊡ ×    │  Unified Title Bar (높이: 28px)
├─────────────────────────────────────────┤  
│                                         │  
│  ┌───────────────────────────────────┐  │  
│  │                                   │  │  
│  │   DROP ZONE (55% of content)      │  │  높이: (total - 28 - 16*2) * 0.55
│  │                                   │  │  
│  │        ↓ 파일을 드롭하세요         │  │  
│  │                                   │  │  
│  └───────────────────────────────────┘  │  
│                                         │  
│  ─────────────────────────────────────  │  분리선 (1px, 색상: border_default)
│                                         │  
│  STATUS SECTION (45% of content)       │  높이: (total - 28 - 16*2) * 0.45
│                                         │  
│  상태: 변환 중 · 00:23:15 / 01:00:00    │  
│  ████████████████░░░░░░░░  72%          │  
│  출력: ~/Downloads/meeting_2026.txt     │  
│                                         │  
│  [ Finder에서 보기 ] [ 파일 열기 ]      │  
│                           [ 취소 ]      │  
│                                         │  
└─────────────────────────────────────────┘  
```

### 6.3 정확한 픽셀 명세

| 영역 | X | Y | Width | Height | 설명 |
|------|---|---|-------|--------|------|
| **창 전체** | 0 | 0 | 780 | 520 | 기본 크기 |
| **컨텐츠 영역** | 16 | 28+12 | 748 | 464 | 패딩 포함 |
| **Drop Zone** | 16 | 40 | 748 | 255 | 55% (content height) |
| **분리선** | 16 | 295 | 748 | 1 | 회색, border_default |
| **Status Section** | 16 | 308 | 748 | 209 | 45% (content height) |
| **Status Label** | 16 | 308 | 748 | 44 | 2줄 텍스트 |
| **Progress Bar** | 16 | 364 | 748 | 6 | full width |
| **Action Buttons** | 16 | 440 | 748 | 32 | 우측 정렬 |

### 6.4 반응형 레이아웃 규칙

창 크기가 변할 때:

1. **Drop Zone:** 좌우 여백(16px) 유지, 가로/세로 모두 신축
2. **Status Section:** 마찬가지로 신축
3. **Progress Bar:** 항상 full width 유지
4. **Action Buttons:** 우측 정렬 유지

```python
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        central_widget = QWidget()
        layout = QVBoxLayout()
        
        # Drop Zone (expanding)
        drop_zone = DropZoneWidget()
        layout.addWidget(drop_zone, stretch=55)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(separator)
        
        # Status Section (expanding)
        status_section = StatusSection()
        layout.addWidget(status_section, stretch=45)
        
        layout.setContentsMargins(16, 12, 16, 16)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
```

---

## 7. 컴포넌트 명세

### 7.1 Drop Zone

#### 외형

- **모양:** 둥근 사각형 (border-radius: 8px)
- **테두리:** 상태별 변경 (아래 참고)
- **배경색:** 상태별 변경

#### 상태별 완전 명세

**7.1.1 Idle (대기)**

```
외형:
┌─────────────────────────────────┐
│                                 │
│     ↓  파일을 드롭하세요        │
│                                 │
│   .m4a, .mp4 파일 (최대 2GB)    │
│  또는 Cmd+O로 파일 선택         │
│                                 │
└─────────────────────────────────┘

스펙:
- 테두리: 1px dashed, #C0C0C0 (라이트) / #484848 (다크)
- 배경: #F5F5F5 (라이트) / #2A2A2A (다크)
- 아이콘: SF Symbol "arrow.down.circle" (24px, Secondary 색상)
- 메인 텍스트: "파일을 드롭하세요" (15px, Medium, Primary)
- 보조 텍스트: ".m4a, .mp4 파일 (최대 2GB)\n또는 Cmd+O로 파일 선택" (13px, Regular, Secondary)
- 내부 패딩: 48px
```

**7.1.2 Hover (마우스 오버)**

```
변화:
- 테두리: #A0A0A0 (라이트) / #686868 (다크) + 1px (변화 없음)
- 배경: 동일 (변화 없음)
- 커서: 포인터(pointing hand)

애니메이션:
- 테두리 색상 전환: 150ms ease-out
- 아이콘 opacity: 1.0 (변화 없음)
```

**7.1.3 Active Drag (파일을 드래그하며 영역 위에 있음)**

```
변화:
- 테두리: 2px solid, #007AFF (라이트) / #0A84FF (다크)
- 배경: Tinted Blue (#EBF3FF / #1A2E44, 10% opacity)
- 아이콘: "waveform.circle.fill" (SF Symbol, 28px, Accent Blue)
- 메인 텍스트: "파일을 여기 놓으세요" (15px, Medium, Primary)
- 보조 텍스트: 숨김

애니메이션:
- 테두리 + 배경 즉시 전환 (0ms, 사용자 피드백 필수)
- 아이콘 scale: 1.0 → 1.1, 100ms ease-out
```

**7.1.4 Processing (변환 중)**

```
변화:
- 테두리: 1px dashed, #007AFF / #0A84FF (active 상태 유지)
- 배경: Tinted Blue (#EBF3FF / #1A2E44, 유지)
- 아이콘: "waveform.circle.fill" (숨김, 대신 회전 애니메이션)
  → "waveform.circle" + 회전 애니메이션 (1초 주기)
- 메인 텍스트: 숨김
- 보조 텍스트: 숨김
- Drop Zone 위에는 Status Section만 보임

애니메이션:
- 아이콘 회전: 0° → 360°, 1000ms loop, linear
- "breathing" 효과 (opacity): 1.0 ↔ 0.7, 2000ms ease-in-out loop
```

**7.1.5 Success (변환 완료)**

```
변화:
- 테두리: 1px solid, #34C759 (라이트) / #30D158 (다크)
- 배경: Tinted Green (#EBF5EB / #1A2E1A, 10% opacity)
- 아이콘: "checkmark.circle.fill" (SF Symbol, 32px, Green)
- 메인 텍스트: "변환이 완료되었습니다" (15px, Medium, Primary)
- 보조 텍스트: "파일명.txt · 크기 · 시간"

애니메이션:
- 아이콘 scale: 0.8 → 1.0, 300ms ease-out
- 배경 + 테두리 페이드인: 200ms ease-out
- 체크마크 "확인" 애니메이션 (선택): SVG 또는 path 애니메이션

유지 시간: 3초 후 자동으로 Idle 상태로 복귀 (단, 사용자가 파일을 드롭하면 즉시)
```

**7.1.6 Error (변환 실패)**

```
변화:
- 테두리: 1px solid, #FF3B30 (라이트) / #FF453A (다크)
- 배경: Tinted Red (#FFF0F0 / #3A1A1A, 10% opacity)
- 아이콘: "exclamationmark.circle.fill" (SF Symbol, 28px, Red)
- 메인 텍스트: "변환 실패" (15px, Medium, Red)
- 보조 텍스트: 에러 메시지 (13px, Regular, Secondary)

애니메이션:
- "shake" 애니메이션: ±4px 가로 흔들림, 200ms (3회 반복)
- 아이콘 scale: 1.0 → 1.1 → 1.0, 300ms ease-out
- 배경 색상 fade-in: 150ms ease-out

유지 시간: 무한 (사용자가 다시 파일을 드롭하거나 "다시 시도" 클릭 시까지)
```

#### Drop Zone 내부 요소 정렬

모든 요소는 **중앙 정렬 (vertical + horizontal center)**:

```python
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class DropZoneWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)
        
        # 아이콘
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 메인 텍스트
        self.main_text = QLabel("파일을 드롭하세요")
        self.main_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont(".AppleSystemUIFont")
        font.setPointSize(15)
        font.setWeight(QFont.Weight.Medium)
        self.main_text.setFont(font)
        
        # 보조 텍스트
        self.sub_text = QLabel(".m4a, .mp4 파일\n또는 Cmd+O로 파일 선택")
        self.sub_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.icon_label)
        layout.addWidget(self.main_text)
        layout.addWidget(self.sub_text)
        self.setLayout(layout)
```

---

### 7.2 Progress Indicator

#### 외형

- **스타일:** Thin (2px height), full width
- **모서리:** Pill shape (border-radius: height/2 = 1px)
- **트랙:** 배경색, 항상 보임
- **필:** 0% → 100%까지 증가

#### 색상

| 상황 | 트랙 | 필 |
|------|------|-----|
| **기본 상태** | #D1D1D6 (라이트) / #3A3A3C (다크) | #007AFF (라이트) / #0A84FF (다크) |
| **완료** | #D1D1D6 / #3A3A3C | #34C759 (라이트) / #30D158 (다크) |

#### 애니메이션

```
변수:
- 시작 애니메이션 (0% → 진행): fade-in 200ms ease-out
- 진행률 업데이트: 300ms ease-out (가속도 있는 부드러운 증가)
- 색상 변경 (blue → green, 100%): 400ms ease-out
- 완료 후 유지: 무한 (사용자가 다시 파일을 드롭할 때까지)
```

**PyQt6 구현 (QPropertyAnimation 사용):**

```python
from PyQt6.QtWidgets import QProgressBar
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve

class AnimatedProgressBar(QProgressBar):
    def __init__(self):
        super().__init__()
        self.setMaximum(100)
        self.setMinimumHeight(2)
        self.setMaximumHeight(2)
        
        self.animation = QPropertyAnimation(self, b"value")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuad)
    
    def set_progress(self, value):
        """진행률을 부드럽게 증가시킨다"""
        self.animation.setEndValue(value)
        self.animation.start()
    
    def complete(self):
        """완료 상태로 전환, 색상을 초록색으로 변경"""
        self.set_progress(100)
        # QSS로 색상 변경 (아래 참고)
        self.setStyleSheet("QProgressBar::chunk { background-color: #34C759; }")
```

**QSS 스타일시트:**

```css
QProgressBar {
    border: none;
    background-color: #D1D1D6;
    border-radius: 1px;
    height: 2px;
}

QProgressBar::chunk {
    background-color: #007AFF;
    border-radius: 1px;
    transition: background-color 400ms ease-out;
}

QProgressBar:dark {
    background-color: #3A3A3C;
}

QProgressBar:dark::chunk {
    background-color: #0A84FF;
}
```

#### 텍스트 없음

진행률 백분율 텍스트는 **표시하지 않음**. 대신 Status Label에서 시간 정보 제공.

---

### 7.3 Status Label

#### 구조

2줄 구조:
- **1줄:** 주 상태 메시지 (13px, Semibold, Primary)
- **2줄:** 부 정보 (11px, Regular, Secondary)

#### 상태별 텍스트 정확히 명시

| 상태 | 라인 1 | 라인 2 |
|------|--------|--------|
| **Idle (대기)** | "파일을 드롭하거나 Cmd+O로 선택하세요" | (없음) |
| **Processing (변환 중)** | "변환 중" | "00:23:15 / 01:00:00" |
| **Completed (완료)** | "변환이 완료되었습니다" | "[파일명].txt · 크기 · 방금 전" |
| **Error** | "변환 실패" | "오류 메시지 또는 원인" |
| **Model Download (최초)** | "Whisper 모델 준비 중" | "742 MB / 1.5 GB · 약 3분 남음" |

**예시:**

```
라이트 모드:
─────────────────────────────────
변환 중
00:23:15 / 01:00:00
─────────────────────────────────

다크 모드:
─────────────────────────────────
변환 중                       (F2F2F7, Semibold 13px)
00:23:15 / 01:00:00          (8E8E93, Regular 11px)
─────────────────────────────────
```

#### 레이아웃

```python
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class StatusLabel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setSpacing(4)  # 라인 간격
        
        # 주 상태
        self.main_label = QLabel()
        font_main = QFont(".AppleSystemUIFont")
        font_main.setPointSize(13)
        font_main.setWeight(QFont.Weight.Medium)
        self.main_label.setFont(font_main)
        self.main_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # 부 정보
        self.sub_label = QLabel()
        font_sub = QFont(".AppleSystemUIFont")
        font_sub.setPointSize(11)
        self.sub_label.setFont(font_sub)
        self.sub_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        layout.addWidget(self.main_label)
        layout.addWidget(self.sub_label)
        layout.setContentsMargins(0, 8, 0, 16)
        
        self.setLayout(layout)
    
    def set_status(self, main_text, sub_text=""):
        """상태를 업데이트한다"""
        self.main_label.setText(main_text)
        self.sub_label.setText(sub_text)
```

---

### 7.4 Action Button (취소 버튼)

#### 외형

- **텍스트:** "취소" (13px, Regular)
- **스타일:** Borderless (배경 없음)
- **색상:** Secondary text color (#6C6C70 / #8E8E93)
- **크기:** 최소 44×44px (터치 타겟)
- **위치:** Status Label 아래, 우측 정렬

#### 표시 조건

**변환 중(Processing)일 때만 표시**. 그 외는 숨김.

#### 인터랙션

```
기본:    "취소" (Secondary)
Hover:   "취소" (Primary, 약간 더 진함)
Pressed: "취소" (약간 더 밝음, 0.8 opacity)
```

**PyQt6 구현:**

```python
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt

class CancelButton(QPushButton):
    def __init__(self):
        super().__init__("취소")
        self.setFlat(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 스타일시트
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #6C6C70;
                border: none;
                font-size: 13px;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                color: #1C1C1E;
                background-color: rgba(0, 0, 0, 0.05);
            }
            QPushButton:pressed {
                opacity: 0.8;
            }
            
            QPushButton:dark {
                color: #8E8E93;
            }
            QPushButton:dark:hover {
                color: #F2F2F7;
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        
        self.hide()  # 기본 상태: 숨김
    
    def show_during_processing(self):
        self.show()
    
    def hide_after_processing(self):
        self.hide()
```

---

### 7.5 Toolbar/Header 영역

#### 레이아웃

```
┌─────────────────────────────────┐
│ 🎙 Voice Ledger         ⚙ 설정  │  Unified Title Bar
└─────────────────────────────────┘
```

#### 요소

| 요소 | 위치 | 스펙 |
|------|------|------|
| **앱 이름** | 좌측 | "Voice Ledger" (15px, Semibold, Primary) |
| **아이콘** | 우측 | "gear" SF Symbol (18px, Secondary) |

#### 구현

타이틀 바는 macOS **Unified Title Bar** 스타일을 사용하여 자동 렌더링.

```python
# PyQt6: setWindowTitle만으로 충분
main_window.setWindowTitle("Voice Ledger")

# 우측 아이콘은 메뉴 바 또는 별도 위젯으로 구현
from PyQt6.QtWidgets import QToolBar
from PyQt6.QtGui import QIcon

toolbar = QToolBar()
settings_action = toolbar.addAction(QIcon("gear"), "Settings")
main_window.addToolBar(toolbar)
```

---

## 8. 마이크로인터랙션 & 애니메이션 명세

모든 애니메이션은 정확한 밀리초 단위 명세를 따른다.

### 8.1 Drop Zone 상태 전환

#### Idle → Hover

```
트리거: 마우스 창 위로 진입
애니메이션:
  - 테두리 색상: #C0C0C0 → #A0A0A0 (150ms ease-out)
  - 배경: 무변화
시간: 150ms
```

#### Hover → Active Drag

```
트리거: 파일을 드래그하며 창 위에서 dragEnterEvent 발생
애니메이션:
  - 테두리: 1px → 2px, 색상 #A0A0A0 → #007AFF (즉시, 0ms)
  - 배경: #F5F5F5 → #EBF3FF, opacity 0 → 0.1 (100ms ease-out)
  - 아이콘: arrow.down.circle → waveform.circle.fill (변경 즉시)
  - 아이콘 scale: 1.0 → 1.1 (100ms ease-out)
시간: 100ms
```

#### Active Drag → 파일 드롭

```
트리거: dropEvent 발생
애니메이션:
  - 전환 및 백그라운드 작업 (임시 파일 생성, ffmpeg 실행 등)
  - Processing 상태로 전환
시간: 0ms (즉시)
```

#### Idle/Hover → Processing

```
트리거: 변환 시작 (백그라운드 스레드)
애니메이션:
  - 아이콘 회전: 0° → 360°, 1000ms loop (linear, 무한)
  - 아이콘 breathing: opacity 1.0 ↔ 0.7 (2000ms ease-in-out loop)
  - Drop Zone 배경 유지 (blue tint)
시간: 무한
```

#### Processing → Success

```
트리거: whisper.transcribe() 완료, OutputFormatter 처리 완료
애니메이션:
  - Drop Zone 페이드아웃: opacity 1.0 → 0.0 (200ms ease-out)
  - Status Section 페이드인: opacity 0.0 → 1.0 (200ms ease-out)
  - 체크마크 아이콘 스케일: 0.8 → 1.0 (300ms cubic-bezier(0.34, 1.56, 0.64, 1.0)) [spring]
  - 배경색 Tint Green: #EBF3FF → #EBF5EB (150ms ease-out)
시간: 400ms (모두 병렬)
```

#### Processing → Error

```
트리거: 예외 발생 (FFmpegError, WhisperError 등)
애니메이션:
  - Drop Zone shake: ±4px 좌우 흔들림, 3회, 200ms total (cubic-bezier(0.68, -0.55, 0.265, 1.55))
  - 테두리 색상 전환: #007AFF → #FF3B30 (150ms ease-out)
  - 배경 Tint: #EBF3FF → #FFF0F0 (150ms ease-out)
  - 아이콘 회전 멈춤, exclamationmark.circle.fill로 변경
시간: 200ms
```

#### Success/Error → Idle (자동 복귀)

```
Success 상태:
  - 3초 후 자동 복귀 (사용자 조작 없이)
  - 페이드아웃: opacity 1.0 → 0.0 (200ms ease-out)
  - Idle 상태로 전환

Error 상태:
  - 자동 복귀 없음 (사용자가 다시 시도할 때까지)
시간: 3초 (Success), 무한 (Error)
```

### 8.2 Progress Bar 애니메이션

#### 초기 페이드인

```
트리거: Processing 상태 진입
애니메이션:
  - Progress Bar opacity: 0.0 → 1.0 (200ms ease-out)
  - Progress Bar value: 0 → 1 (300ms ease-out)
시간: 200ms
```

#### 진행률 업데이트

```
트리거: Whisper 처리 중 매 세그먼트마다 콜백
애니메이션:
  - value: current → next (300ms ease-out)
시간: 300ms per update
```

#### 완료 (100%)

```
트리거: Whisper 완료, OutputFormatter 완료
애니메이션:
  - value: current → 100 (300ms ease-out)
  - 색상: #007AFF → #34C759 (400ms ease-out)
시간: 400ms (병렬)
```

### 8.3 버튼 인터랙션

#### Cancel 버튼 호버

```
트리거: 마우스 오버
애니메이션:
  - 배경색: transparent → rgba(0, 0, 0, 0.05) (100ms ease-out)
  - 텍스트 색상: #6C6C70 → #1C1C1E (100ms ease-out)
시간: 100ms
```

#### Cancel 버튼 클릭

```
트리거: 마우스 다운
애니메이션:
  - opacity: 1.0 → 0.8 (50ms ease-out)
  - 취소 작업 시작 (이전 작업 중단)
시간: 50ms
```

---

## 9. 온보딩 & 모델 다운로드 화면

### 9.1 온보딩 플로우

**최초 실행 시:**
1. 앱 시작 → Whisper 모델 확인
2. 모델 미설치 → 온보딩 화면 전환
3. 다운로드 진행 표시
4. 완료 후 메인 화면으로 자동 전환

### 9.2 모델 다운로드 화면 레이아웃

```
┌─────────────────────────────────┐
│  🎙 Voice Ledger            − □ × │
├─────────────────────────────────┤
│                                 │
│     음성 인식 엔진을 준비하고있어요 │  20px, Semibold
│                                 │
│  고품질 음성 인식을 위한 AI      │
│  모델을 한 번만 다운로드합니다.   │
│  이후에는 인터넷 연결 없이       │
│  모든 변환이 로컬에서 안전하게   │
│  처리됩니다.                   │
│                                 │  설명 텍스트: 13px, Regular
│  크기: 약 1.5 GB                │
│  예상 시간: 약 3분              │
│                                 │
│  ████████████░░░░░░░░  45%       │  Progress Bar
│                                 │
│  745 MB / 1.5 GB · 약 3분 남음   │  11px, Secondary
│                                 │
│                 [백그라운드 계속] │  버튼
│                                 │
└─────────────────────────────────┘
```

### 9.3 다운로드 진행 상태 텍스트

```
"Whisper 모델 준비 중 · 745 MB / 1.5 GB · 약 3분 남음"
```

- **Format:** `{상태} · {다운로드됨} MB / {전체} MB · 약 {분} 남음`
- **폰트:** 13px, Medium (상태), 11px Regular (세부)
- **색상:** Primary (상태), Secondary (세부)

### 9.4 백그라운드 계속 버튼

- **텍스트:** "백그라운드에서 계속"
- **위치:** 우측 정렬
- **스타일:** 파란색 버튼 (Apple Blue)
- **동작:** 클릭 시 메인 화면으로 즉시 전환, 다운로드는 백그라운드 계속

**PyQt6 구현:**

```python
class ModelDownloadDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Voice Ledger")
        
        layout = QVBoxLayout()
        
        # 제목
        title = QLabel("음성 인식 엔진을 준비하고 있어요")
        title_font = QFont(".AppleSystemUIFont")
        title_font.setPointSize(20)
        title_font.setWeight(QFont.Weight.Semibold)
        title.setFont(title_font)
        
        # 설명
        description = QLabel(
            "고품질 음성 인식을 위한 AI 모델을 한 번만 다운로드합니다.\n"
            "이후에는 인터넷 연결 없이 모든 변환이 로컬에서 안전하게 처리됩니다."
        )
        
        # 진행 바
        self.progress = QProgressBar()
        
        # 상태 라벨
        self.status_label = QLabel()
        
        # 백그라운드 계속 버튼
        continue_btn = QPushButton("백그라운드에서 계속")
        continue_btn.clicked.connect(self.accept)
        
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(self.progress)
        layout.addWidget(self.status_label)
        layout.addWidget(continue_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        self.setLayout(layout)
```

---

## 10. 다이얼로그 명세

### 10.1 덮어쓰기 확인 다이얼로그

**언제 표시:** 동일 이름의 `.txt` 파일이 이미 존재할 때

**스타일:** QMessageBox, macOS 네이티브 스타일

**내용:**

```
제목: "파일이 이미 존재합니다"
메시지: "'{파일명}.txt'가 이미 존재합니다.\n바꾸시겠습니까?"
버튼: [취소] [교체]
```

**PyQt6 구현:**

```python
from PyQt6.QtWidgets import QMessageBox

reply = QMessageBox.question(
    None,
    "파일이 이미 존재합니다",
    f"'{filename}.txt'가 이미 존재합니다.\n바꾸시겠습니까?",
    QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Ok,
    QMessageBox.StandardButton.Cancel
)

if reply == QMessageBox.StandardButton.Ok:
    # 덮어쓰기
    pass
```

### 10.2 에러 다이얼로그

**언제 표시:** 심각한 에러 (앱 실행 불가능, 모델 로드 실패 등)

**스타일:** QMessageBox, warning 아이콘

**예시:**

```
제목: "오류"
메시지: "ffmpeg이 설치되지 않았습니다.\n\nbrew install ffmpeg\n\n명령어를 터미널에서 실행하세요."
버튼: [확인]
```

### 10.3 파일 선택 다이얼로그 (Cmd+O)

**스타일:** QFileDialog, macOS 네이티브 스타일

**필터:** `.m4a`, `.mp4` 파일만 표시

```python
from PyQt6.QtWidgets import QFileDialog

filename, _ = QFileDialog.getOpenFileName(
    None,
    "오디오 파일 선택",
    os.path.expanduser("~/Downloads"),
    "오디오 파일 (*.m4a *.mp4);;모든 파일 (*)"
)
```

---

## 11. 접근성 (Accessibility)

### 11.1 키보드 네비게이션

모든 상호작용 요소는 **Tab 키로 접근 가능**:

1. Drop Zone (드래그 가능, Cmd+O로 파일 선택)
2. Cancel Button (Enter로 활성화)
3. 다이얼로그 버튼 (Tab + Enter)

**PyQt6:**

```python
widget.setFocusPolicy(Qt.FocusPolicy.TabFocus)
widget.setTabOrder(drop_zone, cancel_button)
```

### 11.2 VoiceOver 레이블

모든 위젯에 **접근성 설명** 추가:

| 위젯 | 영어 | 한국어 |
|------|------|--------|
| **Drop Zone** | "Drop zone. Drag and drop audio files to transcribe." | "드롭 영역. 오디오 파일을 드래그앤드롭하여 변환합니다." |
| **Progress Bar** | "Transcription progress. 45 percent." | "변환 진행률. 45 퍼센트." |
| **Status Label** | "Status. Transcribing audio. 12 minutes 30 seconds remaining." | "상태. 오디오 변환 중. 약 12분 30초 남음." |
| **Cancel Button** | "Cancel transcription." | "변환 취소." |

**PyQt6 구현:**

```python
from PyQt6.QtWidgets import QAccessibleWidget
from PyQt6.QtGui import QAccessible

class DropZoneWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setAccessibleName("드롭 영역")
        self.setAccessibleDescription("오디오 파일을 드래그앤드롭하여 변환합니다.")
        self.setAccessibleRole(QAccessible.Role.UserInterface)
```

### 11.3 최소 터치/클릭 타겟

모든 버튼 및 클릭 가능 영역: **최소 44×44px**

```python
cancel_button.setMinimumSize(44, 44)
```

### 11.4 색상 대비

- **텍스트/배경 명도 차이:** 최소 7:1 (WCAG AAA 표준)
- **라이트 모드:** 검은색(#1C1C1E) on 밝은 회색(#F5F5F5) ✓
- **다크 모드:** 흰색(#F2F2F7) on 어두운 회색(#2A2A2A) ✓

### 11.5 아이콘 + 색상 병행

상태를 **색상만으로 구분하지 않음**:

- 성공: 초록색 + 체크마크 아이콘
- 오류: 빨간색 + 느낌표 아이콘
- 진행 중: 파란색 + 파형 아이콘

---

## 12. PyQt6 구현 가이드

### 12.1 핵심 위젯 클래스 구조

```
QMainWindow (Main Application Window)
├── QWidget (Central Widget)
│   └── QVBoxLayout (Main Layout)
│       ├── DropZoneWidget (Custom)
│       │   ├── QLabel (Icon)
│       │   ├── QLabel (Main Text)
│       │   └── QLabel (Sub Text)
│       ├── QFrame (Separator)
│       ├── StatusSection (Custom)
│       │   ├── StatusLabel (Custom)
│       │   │   ├── QLabel (Main Status)
│       │   │   └── QLabel (Sub Info)
│       │   ├── QProgressBar
│       │   └── QHBoxLayout (Buttons)
│       │       ├── ActionButtons (Custom)
│       │       └── CancelButton
│       └── QDialog (Modal: File Selection, Overwrite Confirm, Error)
```

### 12.2 드래그앤드롭 구현

```python
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

class DropZoneWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """드래그 영역에 진입"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.enter_drag_state()
    
    def dragLeaveEvent(self, event):
        """드래그 영역 이탈"""
        self.exit_drag_state()
    
    def dropEvent(self, event: QDropEvent):
        """파일 드롭"""
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        if len(files) == 1:
            self.on_file_dropped(files[0])
        else:
            self.show_error("한 번에 하나의 파일만 변환할 수 있습니다.")
    
    def enter_drag_state(self):
        """Active Drag 상태로 전환"""
        # 애니메이션: 테두리 2px, 배경 blue tint
        self.setStyleSheet(self.get_drag_active_style())
    
    def exit_drag_state(self):
        """Idle 상태로 복귀"""
        self.setStyleSheet(self.get_idle_style())
    
    def on_file_dropped(self, filepath):
        """파일 드롭 처리 (transcription 시작)"""
        # 유효성 검사
        if not self.validate_file(filepath):
            self.show_error("지원하지 않는 파일 형식입니다.")
            return
        
        # 변환 시작 (백그라운드 스레드)
        self.parent().start_transcription(filepath)
```

### 12.3 다크 모드 감지 & QSS 동적 로딩

```python
from PyQt6.QtGui import QPalette
from PyQt6.QtWidgets import QApplication

def detect_dark_mode():
    palette = QApplication.instance().palette()
    is_dark = palette.color(QPalette.ColorRole.Base).lightness() < 128
    return is_dark

def load_stylesheet(is_dark):
    if is_dark:
        stylesheet = """
        QMainWindow {
            background-color: #1E1E1E;
        }
        QLabel {
            color: #F2F2F7;
        }
        """
    else:
        stylesheet = """
        QMainWindow {
            background-color: #ECECEC;
        }
        QLabel {
            color: #1C1C1E;
        }
        """
    return stylesheet

app = QApplication([])
is_dark = detect_dark_mode()
app.setStyleSheet(load_stylesheet(is_dark))
```

### 12.4 QPropertyAnimation을 사용한 Progress Bar 애니메이션

```python
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, Qt
from PyQt6.QtWidgets import QProgressBar

class AnimatedProgressBar(QProgressBar):
    def __init__(self):
        super().__init__()
        self.animation = QPropertyAnimation(self, b"value")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuad)
    
    def animate_to(self, value, duration=300):
        """값을 부드럽게 증가시킨다"""
        self.animation.setDuration(duration)
        self.animation.setEndValue(value)
        self.animation.start()
    
    def complete(self):
        """완료 상태로 전환 (색상 변경)"""
        self.animate_to(100, duration=400)
        # 색상 변경 (파란색 → 초록색)
        color_animation = QPropertyAnimation(self, b"palette")
        color_animation.setDuration(400)
        color_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        # 새 팔레트 설정
        new_palette = self.palette()
        new_palette.setColor(QPalette.ColorRole.Highlight, QColor("#34C759"))
        color_animation.setEndValue(new_palette)
        color_animation.start()
```

### 12.5 SF Symbol 대신 시스템 아이콘 사용

**SF Symbol을 직접 사용할 수 없으므로**, Phosphor Icons (MIT 라이선스)의 SVG를 QIcon으로 변환하거나, QStyle::StandardPixmap 활용:

```python
from PyQt6.QtWidgets import QStyle
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt

# 옵션 1: QStyle 표준 아이콘
style = QApplication.style()
icon = style.standardIcon(QStyle.StandardPixmap.SP_DialogYesButton)

# 옵션 2: 커스텀 SVG 로드 (Phosphor Icons)
def load_icon(name, size=24):
    # Phosphor Icons SVG를 QIcon으로 변환
    svg_path = f"resources/icons/{name}.svg"
    return QIcon(svg_path)

# 예시
down_icon = load_icon("arrow-down-circle", 24)
check_icon = load_icon("check-circle", 24)
error_icon = load_icon("warning-circle", 24)
```

### 12.6 QSS 커스텀 스타일시트 예시 (Drop Zone)

```css
/* Drop Zone - Idle */
DropZoneWidget {
    border: 1px dashed #C0C0C0;
    border-radius: 8px;
    background-color: #F5F5F5;
    padding: 48px;
}

/* Drop Zone - Dark Mode */
DropZoneWidget:dark {
    border: 1px dashed #484848;
    background-color: #2A2A2A;
}

/* Drop Zone - Hover */
DropZoneWidget:hover {
    border-color: #A0A0A0;
}

DropZoneWidget:dark:hover {
    border-color: #686868;
}

/* Drop Zone - Drag Active */
DropZoneWidget[dragActive="true"] {
    border: 2px solid #007AFF;
    background-color: #EBF3FF;
    border-radius: 8px;
}

DropZoneWidget:dark[dragActive="true"] {
    border: 2px solid #0A84FF;
    background-color: #1A2E44;
}

/* Drop Zone - Error */
DropZoneWidget[error="true"] {
    border: 1px solid #FF3B30;
    background-color: #FFF0F0;
}

DropZoneWidget:dark[error="true"] {
    border: 1px solid #FF453A;
    background-color: #3A1A1A;
}

/* Drop Zone - Success */
DropZoneWidget[success="true"] {
    border: 1px solid #34C759;
    background-color: #EBF5EB;
}

DropZoneWidget:dark[success="true"] {
    border: 1px solid #30D158;
    background-color: #1A2E1A;
}
```

---

## 13. 반응형 레이아웃

### 13.1 창 크기 변경 시 동작

창의 **최소 (480×340)** 에서 **최대 (1200×800)** 범위 내에서 크기 조절 가능.

#### 가로 크기 변경

- **Drop Zone:** 좌우 여백 유지 (16px), 나머지는 신축
- **Progress Bar:** 항상 full width
- **Status Label:** 텍스트 줄바꿈 가능 (width에 따라 동적 조정)
- **Action Buttons:** 우측 정렬 유지

#### 세로 크기 변경

- **Drop Zone:** 55% height 유지 (신축)
- **Status Section:** 45% height 유지 (신축)
- **Progress Bar:** 높이 고정 (2px)

### 13.2 QSizePolicy 설정

```python
from PyQt6.QtWidgets import QSizePolicy

# Drop Zone은 가로/세로 모두 expanding
drop_zone.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

# Progress Bar는 가로 expanding, 세로 fixed
progress_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

# Cancel Button은 fixed size
cancel_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
cancel_button.setFixedSize(100, 32)
```

### 13.3 최소 크기에서의 레이아웃 Fallback

최소 크기 (480×340)에서 UI 요소가 잘리지 않도록 보장:

- **Status Label 텍스트:** 2줄로 자동 wrap
- **Drop Zone 내부 텍스트:** 3줄 가능 (최소 폰트 크기 유지)
- **버튼 텍스트:** 필요시 생략 기호("…") 추가

```python
drop_zone_label = QLabel("파일을 드롭하세요\n또는 Cmd+O로 파일 선택")
drop_zone_label.setWordWrap(True)
drop_zone_label.setMaximumWidth(400)
```

---

## 14. 구현 체크리스트

개발자가 이 명세를 기반으로 구현할 때 확인해야 할 항목:

### 디자인 검증

- [ ] 모든 색상이 명세의 HEX 코드와 정확히 일치하는가?
- [ ] 폰트 사이즈가 픽셀 단위로 정확한가? (11, 13, 15, 20, 28px)
- [ ] 폰트 웨이트는 Regular/Medium/Semibold만 사용되었는가?
- [ ] 모든 여백이 8px 배수인가?
- [ ] 테두리 반지름이 8px 이하인가?
- [ ] 액센트 색상이 Apple Blue 한 가지만 사용되었는가?

### 애니메이션 검증

- [ ] Drop Zone 상태 전환이 명세된 ms 단위로 정확한가?
- [ ] Progress Bar 애니메이션이 ease-out 곡선을 따르는가?
- [ ] Success 상태 체크마크 spring 애니메이션이 적용되었는가?
- [ ] Error 상태 shake 애니메이션이 3회 반복되는가?

### 다크 모드 검증

- [ ] 라이트/다크 모드 색상이 모두 정의되었는가?
- [ ] 다크 모드에서 텍스트 대비가 충분한가 (7:1 이상)?
- [ ] 시스템 설정 변경 시 앱 재시작 후 테마가 적용되는가?

### 접근성 검증

- [ ] 모든 상호작용 요소가 44×44px 이상인가?
- [ ] VoiceOver 레이블이 영어와 한국어 모두 지정되었는가?
- [ ] Tab 키로 모든 버튼에 접근 가능한가?
- [ ] 색상만으로 상태를 구분하지 않는가 (아이콘 병행)?

### 반응형 레이아웃 검증

- [ ] 최소 크기 (480×340)에서 UI가 잘리지 않는가?
- [ ] 최대 크기 (1200×800)에서 과도하게 늘어나지 않는가?
- [ ] 창 크기 변경 시 Drop Zone과 Status Section이 55:45 비율을 유지하는가?

---

## 15. 개발 환경 설정

### 15.1 필수 패키지

```bash
pip install PyQt6 PyQt6-addons
```

### 15.2 프로젝트 구조

```
voice-ledger/
├── src/
│   ├── main.py                    # 앱 진입점
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py         # QMainWindow
│   │   ├── drop_zone.py           # DropZoneWidget
│   │   ├── status_section.py      # StatusSection, StatusLabel
│   │   └── styles.py              # QSS 스타일시트
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── transcriber.py         # 변환 로직
│   │   └── worker.py              # QThread 워커
│   └── resources/
│       ├── icons/                 # SVG 아이콘
│       └── styles.qss             # 전역 스타일시트
├── docs/
│   ├── DESIGN_SPEC.md             # 이 문서
│   └── ...
└── tests/
    └── test_ui.py
```

### 15.2 초기 코드 템플릿

**src/main.py:**

```python
from PyQt6.QtWidgets import QApplication, QMainWindow
from ui.main_window import MainWindow
import sys

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Voice Ledger")
    app.setApplicationVersion("1.0.0")
    
    # 스타일시트 로드
    with open("src/resources/styles.qss", "r") as f:
        app.setStyleSheet(f.read())
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

---

## 16. 참고 자료

### 공식 문서

- [Apple Human Interface Guidelines (macOS)](https://developer.apple.com/design/human-interface-guidelines/macos)
- [PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [Qt Stylesheets Reference](https://doc.qt.io/qt-6/stylesheet-reference.html)

### 디자인 리소스

- SF Symbols: macOS에서 기본 제공 (또는 Phosphor Icons 사용)
- 색상: macOS System Colors 참고
- 폰트: SF Pro / SF Mono (또는 시스템 기본 폰트 사용)

---

**문서 끝**

작성: 2026-04-06  
담당자: Design System Team  
검토: (예정)
