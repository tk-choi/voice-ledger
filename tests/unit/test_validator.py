"""FileValidator 단위 테스트"""
import os
import pytest
from src.engine.exceptions import UnsupportedFormatError
from src.engine.validator import FileValidator


class TestFileValidator:
    def test_valid_m4a_file(self, tmp_path):
        f = tmp_path / "audio.m4a"
        f.write_bytes(b"dummy")
        FileValidator.validate(str(f))  # 예외 없어야 함

    def test_valid_mp4_file(self, tmp_path):
        f = tmp_path / "video.mp4"
        f.write_bytes(b"dummy")
        FileValidator.validate(str(f))

    def test_uppercase_extension(self, tmp_path):
        f = tmp_path / "audio.M4A"
        f.write_bytes(b"dummy")
        FileValidator.validate(str(f))  # 대소문자 무시

    def test_mixed_case_extension(self, tmp_path):
        f = tmp_path / "audio.Mp4"
        f.write_bytes(b"dummy")
        FileValidator.validate(str(f))

    def test_unsupported_mp3(self, tmp_path):
        f = tmp_path / "audio.mp3"
        f.write_bytes(b"dummy")
        with pytest.raises(UnsupportedFormatError):
            FileValidator.validate(str(f))

    def test_unsupported_wav(self, tmp_path):
        f = tmp_path / "audio.wav"
        f.write_bytes(b"dummy")
        with pytest.raises(UnsupportedFormatError):
            FileValidator.validate(str(f))

    def test_no_extension(self, tmp_path):
        f = tmp_path / "audiofile"
        f.write_bytes(b"dummy")
        with pytest.raises(UnsupportedFormatError):
            FileValidator.validate(str(f))

    def test_nonexistent_file(self, tmp_path):
        path = str(tmp_path / "nonexistent.m4a")
        with pytest.raises(FileNotFoundError):
            FileValidator.validate(path)

    def test_zero_byte_file(self, tmp_path):
        f = tmp_path / "empty.m4a"
        f.write_bytes(b"")
        with pytest.raises(UnsupportedFormatError):
            FileValidator.validate(str(f))

    def test_error_message_contains_extension(self, tmp_path):
        f = tmp_path / "audio.mp3"
        f.write_bytes(b"dummy")
        with pytest.raises(UnsupportedFormatError, match=r"\.mp3"):
            FileValidator.validate(str(f))
