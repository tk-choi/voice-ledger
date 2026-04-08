"""Engine 파이프라인 단위 테스트 (모든 의존성 mock)"""
from contextlib import contextmanager
from unittest.mock import patch
import pytest

from src.engine import run_transcription
from src.engine.cancellation import CancellationToken
from src.engine.exceptions import UnsupportedFormatError


SAMPLE_SEGMENTS = [
    {"start": 0.0, "end": 5.0, "text": "안녕하세요"},
    {"start": 5.0, "end": 10.0, "text": "테스트입니다"},
]

SAMPLE_LINES = ["[00:00:00] 안녕하세요", "[00:00:05] 테스트입니다"]


@contextmanager
def _temp_wav_ctx(wav_path):
    yield wav_path


def _make_pipeline_patches(tmp_path, segments=None, lines=None, output_path=None):
    """공통 mock 패치 팩토리: validate, AudioConverter, WhisperRunner, formatter, writer"""
    if segments is None:
        segments = SAMPLE_SEGMENTS
    if lines is None:
        lines = SAMPLE_LINES
    if output_path is None:
        output_path = str(tmp_path / "audio.txt")

    wav_path = str(tmp_path / "audio.wav")

    patches = {
        "validate": patch("src.engine.validator.FileValidator.validate"),
        "temp_wav": patch(
            "src.engine.converter.AudioConverter.temp_wav_file",
            return_value=_temp_wav_ctx(wav_path),
        ),
        "to_wav": patch("src.engine.converter.AudioConverter.to_wav"),
        "get_duration": patch(
            "src.engine.converter.AudioConverter.get_duration", return_value=10.0
        ),
        "transcribe": patch(
            "src.engine.whisper_runner.WhisperRunner.transcribe",
            return_value=segments,
        ),
        "format_segments": patch(
            "src.engine.formatter.OutputFormatter.format_segments",
            return_value=lines,
        ),
        "derive_output_path": patch(
            "src.engine.writer.FileWriter.derive_output_path",
            return_value=output_path,
        ),
        "write": patch(
            "src.engine.writer.FileWriter.write",
            return_value=output_path,
        ),
    }
    return patches


class TestRunTranscriptionHappyPath:
    def test_returns_output_path(self, tmp_path):
        input_file = tmp_path / "audio.m4a"
        input_file.write_bytes(b"dummy")
        expected_output = str(tmp_path / "audio.txt")
        patches = _make_pipeline_patches(tmp_path, output_path=expected_output)

        with patches["validate"], patches["temp_wav"], patches["to_wav"], \
             patches["get_duration"], patches["transcribe"], \
             patches["format_segments"], patches["derive_output_path"], \
             patches["write"]:
            result = run_transcription(str(input_file))

        assert result == expected_output

    def test_validate_called_with_input_path(self, tmp_path):
        input_file = tmp_path / "audio.m4a"
        input_file.write_bytes(b"dummy")
        patches = _make_pipeline_patches(tmp_path)

        with patches["validate"] as mock_validate, patches["temp_wav"], \
             patches["to_wav"], patches["get_duration"], patches["transcribe"], \
             patches["format_segments"], patches["derive_output_path"], \
             patches["write"]:
            run_transcription(str(input_file))

        mock_validate.assert_called_once_with(str(input_file))

    def test_transcribe_called_with_wav_path_and_duration(self, tmp_path):
        input_file = tmp_path / "audio.m4a"
        input_file.write_bytes(b"dummy")
        wav_path = str(tmp_path / "audio.wav")
        patches = _make_pipeline_patches(tmp_path)

        with patches["validate"], patches["temp_wav"], patches["to_wav"], \
             patches["get_duration"], patches["transcribe"] as mock_transcribe, \
             patches["format_segments"], patches["derive_output_path"], \
             patches["write"]:
            run_transcription(str(input_file))

        call_args = mock_transcribe.call_args
        assert call_args[0][0] == wav_path
        assert call_args[1]["duration"] == 10.0

    def test_format_segments_called_with_transcription_result(self, tmp_path):
        input_file = tmp_path / "audio.m4a"
        input_file.write_bytes(b"dummy")
        patches = _make_pipeline_patches(tmp_path)

        with patches["validate"], patches["temp_wav"], patches["to_wav"], \
             patches["get_duration"], patches["transcribe"], \
             patches["format_segments"] as mock_format, \
             patches["derive_output_path"], patches["write"]:
            run_transcription(str(input_file))

        mock_format.assert_called_once_with(SAMPLE_SEGMENTS)

    def test_write_called_with_lines_and_output_path(self, tmp_path):
        input_file = tmp_path / "audio.m4a"
        input_file.write_bytes(b"dummy")
        expected_output = str(tmp_path / "audio.txt")
        patches = _make_pipeline_patches(tmp_path, output_path=expected_output)

        with patches["validate"], patches["temp_wav"], patches["to_wav"], \
             patches["get_duration"], patches["transcribe"], \
             patches["format_segments"], patches["derive_output_path"], \
             patches["write"] as mock_write:
            run_transcription(str(input_file))

        mock_write.assert_called_once_with(SAMPLE_LINES, expected_output, overwrite=False)


class TestRunTranscriptionCancellation:
    def test_raises_interrupted_error_when_token_cancelled_before_start(self, tmp_path):
        input_file = tmp_path / "audio.m4a"
        input_file.write_bytes(b"dummy")
        token = CancellationToken()
        token.cancel()

        with pytest.raises(InterruptedError):
            run_transcription(str(input_file), cancel_token=token)

    def test_no_validate_called_when_already_cancelled(self, tmp_path):
        input_file = tmp_path / "audio.m4a"
        input_file.write_bytes(b"dummy")
        token = CancellationToken()
        token.cancel()

        with patch("src.engine.validator.FileValidator.validate") as mock_validate:
            with pytest.raises(InterruptedError):
                run_transcription(str(input_file), cancel_token=token)

        mock_validate.assert_not_called()


class TestRunTranscriptionFileExists:
    def test_raises_file_exists_error_when_overwrite_false_and_file_exists(self, tmp_path):
        input_file = tmp_path / "audio.m4a"
        input_file.write_bytes(b"dummy")
        output_file = tmp_path / "audio.txt"
        output_file.write_text("existing content")
        patches = _make_pipeline_patches(tmp_path, output_path=str(output_file))

        with patches["validate"], patches["temp_wav"], patches["to_wav"], \
             patches["get_duration"], patches["transcribe"], \
             patches["format_segments"], patches["derive_output_path"]:
            with pytest.raises(FileExistsError):
                run_transcription(str(input_file), overwrite=False)

    def test_no_file_exists_error_when_overwrite_true(self, tmp_path):
        input_file = tmp_path / "audio.m4a"
        input_file.write_bytes(b"dummy")
        output_file = tmp_path / "audio.txt"
        output_file.write_text("existing content")
        expected_output = str(output_file)
        patches = _make_pipeline_patches(tmp_path, output_path=expected_output)

        with patches["validate"], patches["temp_wav"], patches["to_wav"], \
             patches["get_duration"], patches["transcribe"], \
             patches["format_segments"], patches["derive_output_path"], \
             patches["write"]:
            result = run_transcription(str(input_file), overwrite=True)

        assert result == expected_output

    def test_unsupported_format_raises_before_any_conversion(self, tmp_path):
        input_file = tmp_path / "audio.mp3"
        input_file.write_bytes(b"dummy")

        with patch("src.engine.converter.AudioConverter.to_wav") as mock_to_wav:
            with pytest.raises(UnsupportedFormatError):
                run_transcription(str(input_file))

        mock_to_wav.assert_not_called()
