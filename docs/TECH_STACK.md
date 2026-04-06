# 기술 스택 결정 문서
# Voice Ledger

**버전:** 2.0  
**작성일:** 2026-04-05

---

## 1. 기술 선택 요약

| 범주 | 선택 | 이유 |
|------|------|------|
| 언어 | Python 3.11+ | Whisper 공식 지원, 생태계 풍부 |
| STT 엔진 | openai-whisper (medium) | 로컬 실행, 오프라인, 무료 |
| GUI | PyQt6 | 네이티브 macOS 렌더링, 애니메이션 지원, 드래그앤드롭 내장 |
| 오디오 처리 | ffmpeg | 업계 표준, m4a/mp4 디코딩 지원 |
| ML 백엔드 | PyTorch (MPS) | Apple Silicon GPU 가속 |
| 패키지 관리 | pip + requirements.txt | 표준적이고 단순 |
| 테스트 | pytest + pytest-cov | 파이썬 표준, 간결한 문법 |
| 패키징/배포 | py2app | macOS 전용 `.app` 번들 생성 |

---

## 2. 핵심 의존성 상세

### 2.1 openai-whisper

**선택 이유:**
- OpenAI가 공개한 오픈소스 음성 인식 모델
- 완전 로컬 실행 → 프라이버시 보장
- 한국어 + 영어 혼합 자동 감지 우수
- 무료 (API 키 불필요)

**모델 크기별 비교 (M4 Mac 추정):**

| 모델 | 크기 | VRAM | 1시간 변환 속도 | 정확도 |
|------|------|------|----------------|--------|
| tiny | 39MB | ~1GB | ~2분 | 낮음 |
| base | 74MB | ~1GB | ~4분 | 보통 |
| small | 244MB | ~2GB | ~8분 | 좋음 |
| **medium** | **769MB** | **~5GB** | **~15분** | **매우 좋음** ✅ |
| large | 1550MB | ~10GB | ~30분 | 최상 |

**선택: medium** — 속도/정확도 균형, M4 Mac에서 25분 목표 충족

**설치:**
```bash
pip install openai-whisper
```

**첫 실행 시 모델 자동 다운로드:**
```
~/.cache/whisper/medium.pt (약 1.5GB)
```

### 2.2 PyTorch (MPS 백엔드)

**Apple Silicon 가속:**
```python
import torch
device = "mps" if torch.backends.mps.is_available() else "cpu"
model = whisper.load_model("medium", device=device)
```

- MPS(Metal Performance Shaders): Apple GPU 활용
- M4 Mac에서 CPU 대비 2-3배 속도 향상 예상

**설치:**
```bash
pip install torch torchvision torchaudio
```

### 2.3 ffmpeg

**선택 이유:**
- m4a(AAC) 디코딩: Python 표준 라이브러리로 불가능
- mp4 컨테이너에서 오디오 트랙 추출
- Whisper 입력용 16kHz mono WAV 변환

**사용 방식:**
```python
import subprocess

def to_wav(input_path: str, output_path: str):
    subprocess.run([
        "ffmpeg", "-i", input_path,
        "-ar", "16000",  # 16kHz (Whisper 요구사항)
        "-ac", "1",      # mono
        "-f", "wav",
        output_path
    ], check=True)
```

**배포 전략 (MVP 확정):**
- **앱 번들 포함 (기본):** 정적 빌드 ffmpeg 바이너리를 앱 번들(`Resources/bin/ffmpeg`)에 포함 — 사용자가 별도 설치 불필요
- **개발 환경:** `brew install ffmpeg`로 시스템 ffmpeg 사용

이 결정은 핵심 가치 "단순성"을 우선한다. 비기술 사용자에게 Homebrew 설치를 요구하지 않는다.

### 2.4 PyQt6 (GUI)

**선택 이유:**
- 네이티브 macOS 렌더링으로 macOS HIG 준수
- QPropertyAnimation 등 풍부한 애니메이션 프레임워크 내장
- QDropEvent + setAcceptDrops(True)로 드래그앤드롭 내장 (별도 라이브러리 불필요)
- QThread + Signal/Slot 패턴으로 비동기 처리 용이
- QSS(CSS 기반) 스타일시트로 커스텀 UI 구현 가능

**설치:**
```bash
pip install PyQt6
```

**드래그앤드롭 지원:**
```python
class DropArea(QWidget):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            print(url.toLocalFile())
```

**대안으로 고려했으나 제외한 것:**

| 프레임워크 | 제외 이유 |
|-----------|----------|
| Tkinter | 커스텀 스타일 제한, macOS HIG 준수 어려움 |
| wxPython | macOS 지원 불안정 |
| PyObjC | Objective-C 바인딩, 복잡도 높음 |
| Electron | Node.js 의존성, 무거움 |

---

## 3. 개발 환경 설정

### 3.1 필수 설치

```bash
# 1. Python 3.11+ (Homebrew 권장)
brew install python@3.11

# 2. ffmpeg
brew install ffmpeg

# 3. 가상환경 생성
python3.11 -m venv .venv
source .venv/bin/activate

# 4. Python 패키지 설치 (런타임)
pip install openai-whisper torch torchvision torchaudio PyQt6

# 5. 개발/테스트 의존성 설치
pip install -r requirements-dev.txt
```

### 3.2 requirements.txt

```
openai-whisper>=20231117
torch>=2.2.0
torchvision>=0.17.0
torchaudio>=2.2.0
PyQt6>=6.6.0
```

### 3.3 requirements-dev.txt

```
pytest>=8.0.0
pytest-cov>=5.0.0
py2app>=0.28.0
```

### 3.4 환경 확인

```bash
# ffmpeg 설치 확인
ffmpeg -version

# MPS 가속 확인
python3 -c "import torch; print(torch.backends.mps.is_available())"
# → True (M4 Mac에서)

# Whisper 설치 확인
python3 -c "import whisper; print(whisper.available_models())"
```

---

## 4. 테스트 전략

### 4.1 pytest 선택 이유

- Python 생태계 표준 테스트 프레임워크
- 간결한 `assert` 문법, 자동 테스트 탐색
- 픽스처(fixture) 시스템으로 테스트 데이터 관리 용이
- `pytest-cov`로 커버리지 측정 가능

### 4.2 테스트 레이어 구성

| 레이어 | 대상 컴포넌트 | 실행 조건 |
|--------|-------------|----------|
| 단위 테스트 | `FileValidator`, `OutputFormatter`, `FileWriter` | 항상 실행 가능 |
| 통합 테스트 | `AudioConverter` (ffmpeg 연동) | ffmpeg 설치 필요 |
| E2E 테스트 | 전체 파이프라인 | ffmpeg + Whisper 모델 필요 |

### 4.3 테스트 실행

```bash
# 전체 단위 테스트 실행
pytest tests/unit/

# 커버리지 포함 실행
pytest tests/unit/ --cov=src --cov-report=term-missing

# 통합 테스트 (ffmpeg 필요)
pytest tests/integration/

# 특정 파일만 실행
pytest tests/unit/test_formatter.py -v
```

### 4.4 테스트 커버리지 목표

| 컴포넌트 | 목표 커버리지 | 비고 |
|---------|-------------|------|
| `FileValidator` | 100% | 외부 의존성 없음 |
| `OutputFormatter` | 100% | 순수 함수 |
| `FileWriter` | 90%+ | 파일 I/O 예외 포함 |
| `AudioConverter` | 70%+ | ffmpeg 통합 테스트 |
| `WhisperRunner` | 60%+ | 모델 로딩 포함 |

### 4.5 테스트 픽스처

```python
# tests/conftest.py
import pytest
import os

@pytest.fixture
def sample_m4a():
    return os.path.join(os.path.dirname(__file__), "fixtures", "sample_audio", "sample_ko.m4a")

@pytest.fixture
def corrupt_file(tmp_path):
    f = tmp_path / "corrupt.m4a"
    f.write_bytes(b"not a valid audio file")
    return str(f)
```

---

## 5. 패키징 및 배포

### 5.1 py2app 선택 이유

- macOS 전용 Python 앱 패키저
- `.app` 번들 생성 → 일반 사용자도 더블클릭으로 실행
- Tkinter 앱과의 호환성 검증됨
- macOS Gatekeeper 서명 프로세스와 통합 가능

**대안 비교:**

| 도구 | 장점 | 단점 |
|------|------|------|
| **py2app** ✅ | macOS 네이티브, .app 번들 | macOS 전용 |
| PyInstaller | 크로스 플랫폼 | macOS 앱 번들 품질 낮음 |
| Briefcase | 현대적 도구 | Tkinter 지원 불안정 |
| Nuitka | 성능 우수 | 설정 복잡 |

### 5.2 py2app 설정

```python
# setup.py
from setuptools import setup

APP = ["src/main.py"]
DATA_FILES = [
    ("bin", ["vendor/ffmpeg"]),  # 정적 빌드 ffmpeg 바이너리
]
OPTIONS = {
    "argv_emulation": False,
    "packages": ["whisper", "torch", "PyQt6"],
    "plist": {
        "CFBundleName": "Voice Ledger",
        "CFBundleDisplayName": "Voice Ledger",
        "CFBundleVersion": "1.0.0",
        "CFBundleShortVersionString": "1.0.0",
        "NSMicrophoneUsageDescription": "오디오 파일 변환에 사용합니다.",
    },
    "excludes": ["tkinter.test"],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
```

**빌드 명령:**
```bash
python setup.py py2app
# 결과물: dist/VoiceLedger.app
```

### 5.3 ffmpeg 정적 바이너리 번들

사용자가 Homebrew 없이도 앱이 동작하도록 ffmpeg를 번들에 포함한다.

```bash
# 정적 빌드 ffmpeg 다운로드 (evermeet.cx 제공 macOS 빌드)
# 또는 직접 정적 컴파일
mkdir -p vendor
# ffmpeg 정적 바이너리를 vendor/ffmpeg에 배치
```

앱 코드에서 번들 내 ffmpeg 경로를 동적으로 탐색한다:

```python
import os, sys

def get_ffmpeg_path() -> str:
    if getattr(sys, "frozen", False):
        bundle_dir = os.path.dirname(sys.executable)
        return os.path.join(bundle_dir, "..", "Resources", "bin", "ffmpeg")
    return "ffmpeg"
```

### 5.4 배포 체크리스트

- [ ] `python setup.py py2app` 빌드 성공
- [ ] `dist/VoiceLedger.app` 더블클릭 실행 확인
- [ ] ffmpeg 바이너리 번들 포함 및 동작 확인
- [ ] 최초 실행 시 Whisper 모델 다운로드 UI 동작 확인
- [ ] macOS Gatekeeper: `codesign` 서명 적용
- [ ] Intel Mac 호환성 확인 (필요 시 Universal Binary 빌드)

---

## 6. 향후 기술 업그레이드 경로

| 현재 (MVP) | 업그레이드 | 효과 |
|-----------|-----------|------|
| openai-whisper | faster-whisper | 2-4배 빠름, 메모리 절감 |
| 단일 파일 처리 | asyncio + 배치 처리 | 다중 파일 동시 처리 |
| pip | pyproject.toml (uv) | 현대적 패키지 관리 |
| py2app | Briefcase + notarization | 앱스토어 배포 가능 |

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| 2.0 | 2026-04-06 | PyQt6 전환, Tkinter 제거, requirements.txt 갱신 |
| 1.1 | 2026-04-05 | 최초 작성 |
