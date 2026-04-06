"""pytest 공용 픽스처"""
import os
import pytest


@pytest.fixture
def sample_audio_dir():
    """테스트용 오디오 파일 디렉토리 경로."""
    return os.path.join(os.path.dirname(__file__), "fixtures", "sample_audio")


@pytest.fixture
def sample_segments():
    """Whisper transcribe() 반환 형식과 동일한 샘플 세그먼트."""
    return [
        {"start": 0.0, "end": 5.0, "text": "안녕하세요, 오늘 회의를 시작하겠습니다."},
        {"start": 5.0, "end": 10.0, "text": "첫 번째 안건은 3분기 실적 검토입니다."},
        {"start": 3661.5, "end": 3665.0, "text": "Q3 revenue was up 15%."},
        {"start": 3665.0, "end": 3668.0, "text": "  "},  # 공백만 있는 세그먼트 (제외 대상)
    ]


@pytest.fixture
def empty_segments():
    """빈 세그먼트 리스트."""
    return []


@pytest.fixture
def corrupt_audio_file(tmp_path):
    """유효하지 않은 바이너리 오디오 파일."""
    f = tmp_path / "corrupt.m4a"
    f.write_bytes(b"not a valid audio file - just random bytes")
    return str(f)


@pytest.fixture
def readonly_dir(tmp_path):
    """쓰기 권한이 없는 디렉토리."""
    d = tmp_path / "readonly"
    d.mkdir()
    os.chmod(d, 0o444)
    yield str(d)
    os.chmod(d, 0o755)  # 정리를 위해 권한 복원


@pytest.fixture
def sample_m4a_path(tmp_path):
    """존재하는 m4a 파일 경로 (내용은 더미)."""
    f = tmp_path / "sample.m4a"
    f.write_bytes(b"dummy m4a content")
    return str(f)


@pytest.fixture
def sample_mp4_path(tmp_path):
    """존재하는 mp4 파일 경로 (내용은 더미)."""
    f = tmp_path / "sample.mp4"
    f.write_bytes(b"dummy mp4 content")
    return str(f)
