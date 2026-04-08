"""Engine 파이프라인 통합 테스트 (whisper mock)"""
import os
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
import pytest
from src.engine import run_transcription
from src.engine.cancellation import CancellationToken


def make_mock_whisper(segments=None):
    if segments is None:
        segments = [
            SimpleNamespace(start=0.0, end=5.0, text="안녕하세요"),
            SimpleNamespace(start=5.0, end=10.0, text="테스트입니다"),
        ]
    info = SimpleNamespace(language="ko", language_probability=0.95, duration=10.0)
    mock_model = MagicMock()
    mock_model.transcribe.return_value = (iter(segments), info)
    return mock_model


class TestRunTranscription:
    def setup_method(self):
        from src.engine.whisper_runner import WhisperRunner
        WhisperRunner._model = None

    def test_creates_txt_file(self, tmp_path):
        input_file = tmp_path / "audio.m4a"
        input_file.write_bytes(b"dummy audio")

        with patch("src.engine.whisper_runner.WhisperModel", return_value=make_mock_whisper()):
            with patch("subprocess.run") as mock_run:
                # to_wav 성공 mock
                mock_run.return_value = MagicMock(returncode=0, stdout="10.0\n")
                result = run_transcription(str(input_file))

        expected_output = str(tmp_path / "audio.txt")
        assert result == expected_output
        assert os.path.exists(expected_output)

    def test_output_has_correct_format(self, tmp_path):
        input_file = tmp_path / "meeting.m4a"
        input_file.write_bytes(b"dummy audio")

        with patch("src.engine.whisper_runner.WhisperModel", return_value=make_mock_whisper()):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout="10.0\n")
                run_transcription(str(input_file))

        content = open(str(tmp_path / "meeting.txt"), encoding="utf-8").read()
        assert "[00:00:00] 안녕하세요" in content
        assert "[00:00:05] 테스트입니다" in content

    def test_no_txt_left_on_converter_failure(self, tmp_path):
        input_file = tmp_path / "audio.m4a"
        input_file.write_bytes(b"dummy audio")
        import subprocess

        with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "ffmpeg")):
            with pytest.raises(Exception):
                run_transcription(str(input_file))

        assert not os.path.exists(str(tmp_path / "audio.txt"))

    def test_no_txt_left_on_whisper_failure(self, tmp_path):
        input_file = tmp_path / "audio.m4a"
        input_file.write_bytes(b"dummy audio")

        mock_model = MagicMock()
        mock_model.transcribe.side_effect = RuntimeError("whisper 오류")

        with patch("src.engine.whisper_runner.WhisperRunner._get_model", return_value=mock_model):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout="10.0\n")
                with pytest.raises(Exception):
                    run_transcription(str(input_file))

        assert not os.path.exists(str(tmp_path / "audio.txt"))

    def test_progress_callback_called(self, tmp_path):
        input_file = tmp_path / "audio.m4a"
        input_file.write_bytes(b"dummy audio")
        progress_values = []

        with patch("src.engine.whisper_runner.WhisperModel", return_value=make_mock_whisper()):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout="10.0\n")
                run_transcription(
                    str(input_file),
                    progress_callback=lambda p: progress_values.append(p),
                )

        assert len(progress_values) > 0
        assert 100 in progress_values

    def test_overwrite_false_raises_on_existing(self, tmp_path):
        input_file = tmp_path / "audio.m4a"
        input_file.write_bytes(b"dummy audio")
        output_file = tmp_path / "audio.txt"
        output_file.write_text("existing content")

        with pytest.raises(FileExistsError):
            run_transcription(str(input_file), overwrite=False)

    def test_overwrite_true_replaces_file(self, tmp_path):
        input_file = tmp_path / "audio.m4a"
        input_file.write_bytes(b"dummy audio")
        output_file = tmp_path / "audio.txt"
        output_file.write_text("old content")

        with patch("src.engine.whisper_runner.WhisperModel", return_value=make_mock_whisper()):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout="10.0\n")
                run_transcription(str(input_file), overwrite=True)

        content = open(str(output_file), encoding="utf-8").read()
        assert "old content" not in content
        assert "안녕하세요" in content

    def test_cancel_before_pipeline_raises_interrupted(self, tmp_path):
        input_file = tmp_path / "audio.m4a"
        input_file.write_bytes(b"dummy audio")
        token = CancellationToken()
        token.cancel()

        with pytest.raises(InterruptedError):
            run_transcription(str(input_file), cancel_token=token)

    def test_unsupported_format_raises(self, tmp_path):
        input_file = tmp_path / "audio.mp3"
        input_file.write_bytes(b"dummy audio")

        from src.engine.exceptions import UnsupportedFormatError
        with pytest.raises(UnsupportedFormatError):
            run_transcription(str(input_file))
