# 시스템 아키텍처 설계
# Voice Ledger

**버전:** 2.0  
**작성일:** 2026-04-05

---

## 1. 아키텍처 개요

Voice Ledger는 단일 프로세스 macOS 데스크톱 앱이다. GUI 레이어와 변환 엔진 레이어를 명확히 분리하여 향후 CLI 버전이나 다른 프론트엔드로의 전환을 용이하게 한다.

```
┌─────────────────────────────────────────────────┐
│                  macOS App                       │
│                                                  │
│  ┌─────────────────────────────────────────┐    │
│  │           GUI Layer (PyQt6)              │    │
│  │  - DropZone (드래그앤드롭 영역)           │    │
│  │  - ProgressBar (진행 표시)               │    │
│  │  - StatusLabel (상태 메시지)             │    │
│  └───────────────────┬─────────────────────┘    │
│                      │ TranscriptionRequest      │
│  ┌───────────────────▼─────────────────────┐    │
│  │         Transcription Engine             │    │
│  │  - FileValidator (형식 검증)             │    │
│  │  - AudioConverter (ffmpeg 래퍼)          │    │
│  │  - WhisperRunner (Whisper 실행)          │    │
│  │  - OutputFormatter (타임스탬프 포맷)      │    │
│  │  - FileWriter (txt 파일 저장)            │    │
│  └───────────────────┬─────────────────────┘    │
│                      │                           │
│  ┌───────────────────▼─────────────────────┐    │
│  │         External Dependencies            │    │
│  │  - openai-whisper (medium model)         │    │
│  │  - ffmpeg (오디오 디코딩)                │    │
│  └─────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
```

---

## 2. 레이어 설계

### 2.1 GUI Layer

**책임:** 사용자 인터페이스 렌더링 및 이벤트 처리

**컴포넌트:**

| 컴포넌트 | 역할 |
|----------|------|
| `MainWindow` | 앱 메인 창, 레이아웃 관리 |
| `DropZone` | 드래그앤드롭 감지, 파일 경로 추출 |
| `ProgressBar` | 변환 진행률 시각화 |
| `StatusLabel` | 상태 메시지 표시 (대기/변환 중/완료/오류) |
| `OutputPathLabel` | 출력 파일 경로 표시 |

**UI 프레임워크 결정:** PyQt6
- 드래그앤드롭 네이티브 지원
- QThread/Signal-Slot 비동기 패턴 내장
- macOS 네이티브 스타일 지원

### 2.2 Transcription Engine Layer

**책임:** 오디오 파일을 텍스트로 변환하는 핵심 비즈니스 로직

**컴포넌트:**

| 컴포넌트 | 역할 |
|----------|------|
| `FileValidator` | 파일 존재 확인, 확장자 검증 (m4a/mp4) |
| `AudioConverter` | ffmpeg로 m4a/mp4 → wav 변환 (Whisper 입력용) |
| `WhisperRunner` | Whisper 모델 로딩 및 transcribe 실행 |
| `OutputFormatter` | Whisper 세그먼트 → `[HH:MM:SS] text` 형식 변환 |
| `FileWriter` | 포맷된 텍스트를 .txt 파일로 저장 |

### 2.3 데이터 흐름

```
사용자가 m4a/mp4 파일 드롭
        │
        ▼
FileValidator.validate(path)
  - 파일 존재 확인
  - 확장자 검증
        │
        ▼
AudioConverter.to_wav(path) → temp_wav_path
  - ffmpeg: m4a/mp4 → 16kHz mono wav
  - 시스템 임시 디렉터리에 저장 (tempfile.mkstemp)
        │
        ▼
WhisperRunner.transcribe(temp_wav_path)
  - model.transcribe(audio, language=None)  # 자동 감지
  - segments 리스트 반환: [{start, end, text}, ...]
        │
        ▼
OutputFormatter.format(segments) → lines
  - 각 segment: "[HH:MM:SS] {text}"
  - 빈 text 제외
        │
        ▼
FileWriter.write(lines, output_path)
  - 원본 파일 경로 기반 .txt 경로 결정
  - UTF-8 인코딩으로 저장
        │
        ▼
GUI에 완료 알림 + 출력 파일 경로 표시
```

---

## 3. 비동기 처리 및 동시성 안전성

변환 작업은 GUI 스레드를 블로킹하지 않도록 `QThread`에서 실행된다.

```python
# 개념적 흐름 (PyQt6)
from PyQt6.QtCore import QThread, pyqtSignal

class TranscriptionWorker(QThread):
    progress = pyqtSignal(int)      # 진행률 (0~100)
    finished = pyqtSignal(str)      # 출력 파일 경로
    error = pyqtSignal(str)         # 에러 메시지

    def __init__(self, file_path: str):
        super().__init__()
        self._file_path = file_path

    def run(self):
        # Engine 레이어 호출
        # Signal로 GUI 진행률 업데이트
        pass
```

**스레드 간 통신:** Qt Signal/Slot 패턴 사용 — `worker.progress.connect(progress_bar.setValue)`

### 3.1 동시성 안전성 정책

**중복 실행 방지:** MVP에서는 단일 변환 작업만 허용한다. 변환 진행 중 새 파일 드롭은 무시하거나 경고 메시지를 표시한다.

```python
from PyQt6.QtCore import QObject, pyqtSignal

class TranscriptionController(QObject):
    status_changed = pyqtSignal(str, str)  # (level, message)

    def __init__(self):
        super().__init__()
        self._worker: TranscriptionWorker | None = None

    def start(self, file_path: str):
        if self._worker is not None and self._worker.isRunning():
            self.status_changed.emit("error", "이미 변환 중입니다. 완료 후 다시 시도하세요.")
            return
        self._worker = TranscriptionWorker(file_path)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_finished(self, output_path: str):
        self._worker = None

    def _on_error(self, message: str):
        self._worker = None
```

**GUI 업데이트 안전성:** PyQt6 Signal은 스레드 경계를 안전하게 넘는다. `QMetaObject.invokeMethod()` 또는 Signal emit을 통해 메인 스레드에서 위젯이 업데이트된다.

```python
# 안전한 GUI 업데이트 패턴 (Signal-Slot)
worker.progress.connect(progress_bar.setValue)   # 자동으로 메인 스레드에서 실행
worker.finished.connect(self._show_output_path)
```

### 3.2 WhisperRunner 진행률 추정 전략

Whisper `transcribe()`는 내부적으로 진행률 콜백을 제공하지 않는다. 다음 전략으로 진행률을 추정한다.

**방법: 세그먼트 콜백 기반 추정**

```python
from PyQt6.QtCore import QThread, pyqtSignal
import whisper

class WhisperWorker(QThread):
    progress = pyqtSignal(int)   # 0-100
    finished = pyqtSignal(list)  # segments
    error = pyqtSignal(str)

    def __init__(self, audio_path: str, duration_seconds: float):
        super().__init__()
        self.audio_path = audio_path
        self.duration = duration_seconds
        self._cancelled = False

    def run(self):
        try:
            model = whisper.load_model("medium", device=get_device())
            result = model.transcribe(
                self.audio_path,
                language=None,  # 자동 감지
                verbose=False,
            )
            # 완료 후 segments 전달 (세그먼트별 진행률은 callback_on_progress로 대체)
            self.progress.emit(100)
            self.finished.emit(result["segments"])
        except Exception as e:
            self.error.emit(str(e))

    def cancel(self):
        """취소 요청 — run() 루프에서 확인 후 중단"""
        self._cancelled = True
```

**진행률 근사:** `transcribe()` 완료 전까지는 처리된 오디오 시간 기반으로 추정한다.
- `whisper` 라이브러리의 `decode_options`에 `condition_on_previous_text=False` 설정 시 세그먼트 단위 처리
- 실용적 대안: `ffprobe`로 총 오디오 길이 측정 → 경과 시간 / 총 길이로 진행률 표시

### 3.3 변환 취소 메커니즘

`QThread.terminate()`는 CPython GIL로 인해 C 확장(PyTorch/Whisper) 실행 중 동작하지 않는다. 대신 `CancellationToken` 기반 협력적 취소를 사용한다.

```python
# src/engine/cancellation.py
class CancellationToken:
    def __init__(self): self._cancelled = False
    def cancel(self): self._cancelled = True
    @property
    def is_cancelled(self) -> bool: return self._cancelled
```

**취소 흐름:**

1. 사용자가 취소 버튼 클릭 → `cancel_token.cancel()` 호출
2. `run_transcription()` 내 `_check_cancel()` 헬퍼가 파이프라인 단계 간에서 `InterruptedError` 발생
3. 파이프라인 중단 → `temp_wav_file()` 컨텍스트 매니저가 임시 파일 정리
4. GUI는 `_cancelled` 상태를 감지하여 IDLE로 복귀

**제약:** Whisper `transcribe()` 실행 중(C 확장 실행 중)에는 취소 체크 불가. 세그먼트 단위 루프(`whisper.decode()` 직접 제어)로 구현하면 세그먼트 간 체크 가능 — 구현 시 검토.

```python
# GUI: TranscriptionWorker
class TranscriptionWorker(QThread):
    def __init__(self, input_path, overwrite):
        super().__init__()
        self._cancel_token = CancellationToken()

    def run(self):
        try:
            result = run_transcription(
                self.input_path,
                overwrite=self.overwrite,
                progress_callback=lambda p: self.progress.emit(p),
                cancel_token=self._cancel_token,
            )
            self.finished.emit(result)
        except InterruptedError:
            self.cancelled.emit()
        except Exception as e:
            self.error.emit(str(e))

    def cancel(self):
        self._cancel_token.cancel()
        self.wait(5000)  # 현재 단계 완료 대기 (최대 5초)
```

---

## 4. 임시 파일 관리 전략

변환 과정에서 생성되는 임시 WAV 파일은 반드시 정리되어야 한다. 정상 완료 및 예외 상황 모두에서 누락 없이 삭제된다.

### 4.1 컨텍스트 매니저 기반 정리

```python
import tempfile
import os
from contextlib import contextmanager

@contextmanager
def temp_wav_file():
    """임시 WAV 파일을 생성하고 블록 종료 시 자동 삭제한다."""
    fd, path = tempfile.mkstemp(suffix=".wav", prefix="voice_ledger_")
    os.close(fd)  # AudioConverter가 직접 파일을 열기 위해 fd를 먼저 닫음
    try:
        yield path
    finally:
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError:
            pass  # 삭제 실패는 무시 (이미 삭제됐거나 권한 문제)

# 사용 예시
def run_transcription(input_path, callback):
    with temp_wav_file() as wav_path:
        AudioConverter.to_wav(input_path, wav_path)
        segments = WhisperRunner.transcribe(wav_path)
    # with 블록 종료 시 wav_path 자동 삭제
    lines = OutputFormatter.format(segments)
    FileWriter.write(lines, derive_output_path(input_path))
```

### 4.2 임시 파일 명명 규칙

- 위치: `tempfile.gettempdir()` (macOS 기준 `/var/folders/...`)
- 접두사: `voice_ledger_` (식별 용이)
- 앱 강제 종료 시 OS가 다음 재부팅 때 `/tmp` 정리 → 장기 잔류 없음

---

## 5. 에러 처리 및 복구 전략

### 5.1 에러 분류 및 처리

| 에러 유형 | 원인 | 사용자 메시지 | 복구 방법 |
|-----------|------|--------------|----------|
| `UnsupportedFormatError` | 지원하지 않는 확장자 | "지원 형식: m4a, mp4" | 다른 파일 드롭 안내 |
| `FFmpegNotFoundError` | ffmpeg 미설치 | "brew install ffmpeg 실행 필요" | 설치 후 재시도 안내 |
| `FFmpegConversionError` | 파일 손상/암호화 | "파일 변환 실패. 파일을 확인하세요" | 임시 파일 정리 후 대기 상태로 복귀 |
| `WhisperModelError` | 모델 다운로드 실패 | "인터넷 연결 확인 후 재시도하세요" | 재시도 가능 상태로 복귀 |
| `WhisperTranscribeError` | 변환 중 예외 | "변환 중 오류가 발생했습니다" | 임시 파일 정리 후 대기 상태로 복귀 |
| `OutputWriteError` | 쓰기 권한 부재 | "저장 위치 권한을 확인하세요" | 다른 저장 위치 안내 |

### 5.2 에러 복구 흐름

모든 에러는 다음 흐름을 따른다:

```
에러 발생
    │
    ▼
임시 파일 정리 (temp_wav_file 컨텍스트 매니저가 보장)
    │
    ▼
GUI 상태를 "대기" 상태로 복귀
    │
    ▼
사용자에게 구체적인 에러 메시지 표시
    │
    ▼
재시도 가능 상태 유지 (앱 재시작 불필요)
```

### 5.3 사용자 정의 예외 계층

```python
class VoiceLedgerError(Exception):
    """앱 전용 기본 예외"""
    pass

class UnsupportedFormatError(VoiceLedgerError):
    pass

class FFmpegNotFoundError(VoiceLedgerError):
    pass

class FFmpegConversionError(VoiceLedgerError):
    pass

class WhisperModelError(VoiceLedgerError):
    pass

class OutputWriteError(VoiceLedgerError):
    pass
```

---

## 6. 파일 구조

```
voice-ledger/
├── docs/                          # 기획/설계 문서
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── TECH_STACK.md
│   └── UI_DESIGN.md
├── src/
│   ├── main.py                    # 앱 진입점
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py         # MainWindow 클래스
│   │   ├── drop_zone.py           # DropZone 위젯
│   │   └── styles.py              # 스타일 상수/헬퍼
│   ├── resources/
│   │   └── styles.qss             # Qt 스타일시트
│   └── engine/
│       ├── __init__.py
│       ├── exceptions.py          # 사용자 정의 예외 계층
│       ├── validator.py           # FileValidator
│       ├── converter.py           # AudioConverter (ffmpeg 래퍼)
│       ├── whisper_runner.py      # WhisperRunner
│       ├── formatter.py           # OutputFormatter
│       └── writer.py              # FileWriter
├── tests/
│   ├── unit/
│   │   ├── test_validator.py
│   │   ├── test_formatter.py
│   │   ├── test_converter.py
│   │   └── test_writer.py
│   ├── integration/
│   │   └── test_transcription_pipeline.py
│   └── fixtures/
│       └── sample_audio/          # 테스트용 샘플 파일 (m4a, mp4)
├── requirements.txt
├── requirements-dev.txt           # 개발/테스트 전용 의존성
└── README.md
```

---

## 7. Apple Silicon 최적화

M4 Mac의 Neural Engine을 활용하기 위해 다음을 고려한다:

### 옵션 A: 표준 openai-whisper (기본)
```
openai-whisper → PyTorch MPS 백엔드 → Apple GPU
```
- 설치 단순
- MPS(Metal Performance Shaders) 자동 활용

### 옵션 B: faster-whisper (권장 성능 최적화)
```
faster-whisper → CTranslate2 → CPU 최적화
```
- openai-whisper 대비 2-4배 빠름
- 메모리 사용량 더 적음
- M4 CPU 최적화 활용

**결정:** MVP는 `openai-whisper`로 시작, 성능 이슈 시 `faster-whisper`로 전환

---

## 8. 테스트 전략

### 8.1 테스트 레이어

| 레이어 | 대상 | 도구 | 비고 |
|--------|------|------|------|
| 단위 테스트 | `FileValidator`, `OutputFormatter`, `FileWriter` | pytest | 외부 의존성 없이 독립 실행 |
| 통합 테스트 | `AudioConverter` (ffmpeg 연동) | pytest + 샘플 파일 | ffmpeg 설치 환경 필요 |
| 엔드투엔드 | 전체 파이프라인 (파일 드롭 → txt 생성) | pytest + 샘플 파일 | Whisper 모델 다운로드 필요 |
| GUI 테스트 | `MainWindow`, `DropZone` | 수동 테스트 | Tkinter 자동화 어려움 |

### 8.2 단위 테스트 가능 컴포넌트 설계 원칙

- `FileValidator`, `OutputFormatter`, `FileWriter`는 외부 시스템에 의존하지 않아 순수 단위 테스트 가능
- `AudioConverter`와 `WhisperRunner`는 ffmpeg/Whisper 의존성이 있어 통합 테스트로 분류
- Engine 레이어는 GUI와 완전히 분리되어 헤드리스 테스트 환경에서 독립 실행 가능

### 8.3 테스트 픽스처

```
tests/fixtures/sample_audio/
├── sample_ko.m4a     # 한국어 30초 샘플
├── sample_en.mp4     # 영어 30초 샘플
└── corrupt.m4a       # 손상된 파일 (에러 처리 테스트용)
```

### 8.4 CI 고려사항

- 단위 테스트: 모든 환경에서 실행 가능
- 통합/E2E 테스트: ffmpeg 설치 + Whisper 모델 다운로드 필요 → CI에서 별도 스텝으로 분리하거나 로컬 전용으로 운영

---

## 9. 배포 및 패키징

### 9.1 배포 대상

- macOS 13 (Ventura) 이상
- Apple Silicon (M1/M2/M3/M4) 우선, Intel Mac 지원 가능

### 9.2 패키징 방식: py2app (권장)

```bash
pip install py2app
python setup.py py2app
```

**결과물:** `dist/VoiceLedger.app` — 더블클릭으로 실행 가능한 macOS 앱 번들

**py2app 선택 이유:**
- macOS 전용이므로 플랫폼 네이티브 도구 사용
- `.app` 번들 형식으로 macOS 사용자에게 친숙

**대안:** PyInstaller (`pyinstaller main.py --onefile`) — 크로스 플랫폼 지원이 필요할 경우

### 9.3 ffmpeg 번들 전략

사용자가 ffmpeg를 별도 설치하지 않아도 앱이 동작하도록 ffmpeg 정적 바이너리를 앱 번들에 포함한다.

```
VoiceLedger.app/
└── Contents/
    ├── MacOS/
    │   └── VoiceLedger        # 메인 실행 파일
    ├── Resources/
    │   └── bin/
    │       └── ffmpeg          # 정적 빌드된 ffmpeg 바이너리
    └── Info.plist
```

```python
import os
import sys

def get_ffmpeg_path() -> str:
    """앱 번들 내 ffmpeg 경로를 반환한다. 번들 외부 실행 시 시스템 ffmpeg 사용."""
    if getattr(sys, "frozen", False):
        # py2app으로 패키징된 경우
        bundle_dir = os.path.dirname(sys.executable)
        return os.path.join(bundle_dir, "..", "Resources", "bin", "ffmpeg")
    return "ffmpeg"  # 개발 환경: 시스템 PATH에서 탐색
```

### 9.4 Whisper 모델 배포 전략

Whisper medium 모델(~1.5GB)은 앱 번들에 포함하지 않는다. 크기 제한과 배포 복잡성을 고려하여 첫 실행 시 다운로드한다.

- **최초 실행:** 모델 다운로드 진행 상태 표시 (프로그레스바 활용)
- **캐시 위치:** `~/.cache/whisper/medium.pt`
- **오프라인 환경:** 모델이 이미 캐시된 경우 인터넷 불필요

### 9.5 배포 체크리스트

- [ ] py2app 빌드 성공 확인
- [ ] 앱 번들에 ffmpeg 바이너리 포함 확인
- [ ] 최초 실행 시 Whisper 모델 다운로드 안내 UI 동작 확인
- [ ] macOS 보안 정책 (Gatekeeper) 통과 여부 확인
- [ ] `codesign` 서명 적용 (배포 시 필수)

---

## 10. 의존성 관리

```
# requirements.txt
openai-whisper>=20231117
torch>=2.2.0
torchvision>=0.17.0
torchaudio>=2.2.0
PyQt6>=6.6.0

# requirements-dev.txt
pytest>=8.0.0
pytest-cov>=5.0.0
```

**ffmpeg 시스템 의존성:**
- 개발 환경: `brew install ffmpeg`
- 배포 환경: 앱 번들에 정적 ffmpeg 바이너리 포함

---

## 11. 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| 2.0 | 2026-04-06 | PyQt6 전환, 비동기 패턴 QThread/Signal-Slot, 파일 구조 src/ui/ |
| 1.1 | 2026-04-05 | 초기 작성 |
