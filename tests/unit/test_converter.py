"""AudioConverter 단위 테스트 (mock 기반)"""
import os
from unittest.mock import patch, MagicMock
import pytest
from src.engine.exceptions import FFmpegNotFoundError, FFmpegConversionError
from src.engine.converter import AudioConverter


class TestGetFfmpegPath:
    def test_returns_string(self):
        path = AudioConverter.get_ffmpeg_path()
        assert isinstance(path, str)

    def test_frozen_app_uses_bundle_path(self):
        import sys
        with patch.object(sys, "frozen", True, create=True):
            with patch.object(sys, "executable", "/app/MacOS/VoiceLedger"):
                path = AudioConverter.get_ffmpeg_path()
                assert "ffmpeg" in path


class TestGetDuration:
    def test_returns_float_on_success(self):
        mock_result = MagicMock()
        mock_result.stdout = "123.456\n"
        mock_result.returncode = 0
        with patch("subprocess.run", return_value=mock_result):
            result = AudioConverter.get_duration("/fake/audio.wav")
            assert isinstance(result, float)
            assert abs(result - 123.456) < 0.001

    def test_raises_on_ffprobe_failure(self):
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.returncode = 1
        mock_result.stderr = "error"
        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(FFmpegConversionError):
                AudioConverter.get_duration("/fake/audio.wav")

    def test_ffprobe_not_found_raises_ffmpeg_error(self):
        with patch("subprocess.run", side_effect=FileNotFoundError("ffmpeg not found")):
            with pytest.raises(FFmpegNotFoundError):
                AudioConverter.get_duration("/fake/audio.wav")


class TestToWav:
    def test_calls_ffmpeg_with_correct_args(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            AudioConverter.to_wav("/input/audio.m4a", "/output/audio.wav")
            call_args = mock_run.call_args[0][0]
            assert "-ar" in call_args
            assert "16000" in call_args
            assert "-ac" in call_args
            assert "1" in call_args
            assert "/input/audio.m4a" in call_args
            assert "/output/audio.wav" in call_args

    def test_ffmpeg_failure_raises_conversion_error(self):
        import subprocess
        with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "ffmpeg")):
            with pytest.raises(FFmpegConversionError):
                AudioConverter.to_wav("/input/audio.m4a", "/output/audio.wav")

    def test_ffmpeg_not_found_raises_not_found_error(self):
        with patch("subprocess.run", side_effect=FileNotFoundError("ffmpeg not found")):
            with pytest.raises(FFmpegNotFoundError):
                AudioConverter.to_wav("/input/audio.m4a", "/output/audio.wav")


class TestTempWavFile:
    def test_creates_and_deletes_temp_file(self):
        temp_path = None
        with AudioConverter.temp_wav_file() as path:
            temp_path = path
            assert os.path.exists(path)
            assert path.endswith(".wav")
        assert not os.path.exists(temp_path)

    def test_deletes_temp_file_on_exception(self):
        temp_path = None
        try:
            with AudioConverter.temp_wav_file() as path:
                temp_path = path
                raise RuntimeError("simulated error")
        except RuntimeError:
            pass
        assert not os.path.exists(temp_path)
