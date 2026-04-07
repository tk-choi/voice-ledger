# Voice Ledger

음성·영상 파일을 타임스탬프 포함 텍스트로 변환하는 macOS 데스크톱 앱.  
외부 API 없이 로컬에서 완전 오프라인으로 동작합니다.

## 주요 기능

- **드래그앤드롭** — `.m4a`, `.mp4` 파일을 창에 드롭하면 즉시 변환 시작
- **완전 오프라인** — 최초 모델 다운로드 이후 인터넷 불필요
- **다국어 자동 감지** — 한국어·영어(혼합 포함) 자동 인식
- **Apple Silicon 최적화** — MPS 가속으로 M1/M2/M3/M4에서 빠른 변환
- **타임스탬프 출력** — `[HH:MM:SS]` 형식으로 세그먼트별 기록
- **취소 지원** — 변환 중 언제든 취소 가능, 임시 파일 자동 정리

## 요구 사항

| 항목 | 버전 |
|------|------|
| macOS | 13 Ventura 이상 |
| Python | 3.11 이상 |
| ffmpeg | 시스템 설치 필요 (개발 환경) |

> [!NOTE]
> Apple Silicon(M1~M4)에서 최적 성능을 발휘합니다. Intel Mac에서도 동작하나 변환 속도가 느릴 수 있습니다.

## 설치

### 1. 저장소 클론

```bash
git clone https://github.com/tk-choi/voice-ledger.git
cd voice-ledger
```

### 2. ffmpeg 설치

```bash
brew install ffmpeg
```

### 3. 의존성 설치

[uv](https://github.com/astral-sh/uv)를 사용하는 경우:

```bash
uv sync
```

pip를 사용하는 경우:

```bash
pip install -r requirements.txt
```

### 4. 앱 실행

```bash
uv run python -m src.main
# 또는
python -m src.main
```

> [!NOTE]
> 최초 실행 시 Whisper medium 모델(~1.5 GB)을 자동으로 다운로드합니다.  
> 다운로드는 한 번만 수행되며, 이후 `~/.cache/whisper/`에 캐시됩니다.

## 사용 방법

1. 앱을 실행합니다.
2. `.m4a` 또는 `.mp4` 파일을 창에 드래그앤드롭합니다.  
   또는 `Cmd+O`로 파일을 선택할 수 있습니다.
3. 진행 바에서 변환 진행률을 확인합니다.
4. 변환이 완료되면 입력 파일과 동일한 폴더에 `.txt` 파일이 생성됩니다.
5. **Finder에서 보기** 또는 **파일 열기** 버튼으로 결과를 바로 확인합니다.

## 출력 형식

입력 파일(`meeting.m4a`)과 같은 위치에 `meeting.txt`가 생성됩니다.

```
[00:00:00] 안녕하세요, 오늘 회의를 시작하겠습니다.
[00:00:05] 첫 번째 안건은 3분기 실적 검토입니다.
[00:00:12] Q3 revenue was up 15% compared to last year.
[00:00:18] 감사합니다. 다음 안건으로 넘어가겠습니다.
```

- 인코딩: UTF-8 (BOM 없음)
- 줄바꿈: LF
- 무음·공백 세그먼트는 자동으로 제외됩니다.

## 아키텍처

```
GUI Layer (PyQt6)
    └─ DropZone / MainWindow / ProgressBar
          │ (QThread + Signal-Slot)
Transcription Engine
    ├─ FileValidator   — 확장자·파일 크기 검증
    ├─ AudioConverter  — ffmpeg: m4a/mp4 → 16kHz mono WAV
    ├─ WhisperRunner   — Whisper medium 로컬 추론 (MPS/CPU)
    ├─ OutputFormatter — 세그먼트 → [HH:MM:SS] 형식
    └─ FileWriter      — UTF-8 .txt 저장
```

Engine 레이어는 GUI와 완전히 분리되어 있어 헤드리스 환경에서도 독립적으로 테스트 가능합니다.

## 개발 환경 설정

```bash
# 개발 의존성 포함 설치
uv sync --dev
# 또는
pip install -r requirements-dev.txt

# 테스트 실행
python -m pytest tests/ -v
```

> [!NOTE]
> ffmpeg가 설치되지 않은 환경에서는 통합 테스트 일부가 자동으로 스킵됩니다.

## 기술 스택

| 역할 | 라이브러리 |
|------|-----------|
| GUI | PyQt6 |
| 음성 인식 | openai-whisper (medium 모델) |
| 딥러닝 백엔드 | PyTorch (MPS / CPU) |
| 오디오 처리 | ffmpeg |
| 테스트 | pytest |
