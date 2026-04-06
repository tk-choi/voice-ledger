"""WhisperRunner 단위 테스트 (mock 기반)"""
import os
from unittest.mock import patch, MagicMock
import pytest
from src.engine.exceptions import WhisperModelError, WhisperTranscribeError
from src.engine.cancellation import CancellationToken
from src.engine.whisper_runner import WhisperRunner


class TestIsModelAvailable:
    def test_returns_true_when_model_file_exists(self, tmp_path):
        model_file = tmp_path / "medium.pt"
        model_file.write_bytes(b"fake model")
        with patch.object(WhisperRunner, "get_model_path", return_value=str(model_file)):
            assert WhisperRunner.is_model_available() is True

    def test_returns_false_when_model_missing(self, tmp_path):
        missing_path = str(tmp_path / "medium.pt")
        with patch.object(WhisperRunner, "get_model_path", return_value=missing_path):
            assert WhisperRunner.is_model_available() is False


class TestGetModelPath:
    def test_returns_string(self):
        path = WhisperRunner.get_model_path()
        assert isinstance(path, str)

    def test_path_contains_whisper_and_medium(self):
        path = WhisperRunner.get_model_path()
        assert "whisper" in path.lower()
        assert "medium" in path


class TestGetDevice:
    def test_returns_mps_when_available(self):
        with patch("torch.backends.mps.is_available", return_value=True):
            with patch("torch.backends.mps.is_built", return_value=True):
                device = WhisperRunner.get_device()
                assert device in ("mps", "cpu")  # fallback 허용

    def test_returns_cpu_when_mps_unavailable(self):
        with patch("torch.backends.mps.is_available", return_value=False):
            device = WhisperRunner.get_device()
            assert device == "cpu"


class TestTranscribe:
    def setup_method(self):
        WhisperRunner._model = None
        WhisperRunner._model_device = None

    def _make_mock_model(self, segments=None):
        if segments is None:
            segments = [
                {"start": 0.0, "end": 5.0, "text": "안녕하세요"},
                {"start": 5.0, "end": 10.0, "text": "테스트입니다"},
            ]
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"segments": segments}
        return mock_model

    def test_returns_segments_list(self, tmp_path):
        audio = tmp_path / "audio.wav"
        audio.write_bytes(b"dummy")
        mock_model = self._make_mock_model()
        with patch("whisper.load_model", return_value=mock_model):
            result = WhisperRunner.transcribe(str(audio), duration=10.0)
            assert isinstance(result, list)
            assert len(result) == 2

    def test_segments_have_required_keys(self, tmp_path):
        audio = tmp_path / "audio.wav"
        audio.write_bytes(b"dummy")
        mock_model = self._make_mock_model()
        with patch("whisper.load_model", return_value=mock_model):
            result = WhisperRunner.transcribe(str(audio), duration=10.0)
            for seg in result:
                assert "start" in seg
                assert "end" in seg
                assert "text" in seg

    def test_loads_medium_model(self, tmp_path):
        audio = tmp_path / "audio.wav"
        audio.write_bytes(b"dummy")
        mock_model = self._make_mock_model()
        with patch("whisper.load_model", return_value=mock_model) as mock_load:
            WhisperRunner.transcribe(str(audio), duration=10.0)
            call_args = mock_load.call_args
            assert call_args[0][0] == "medium"

    def test_calls_progress_callback(self, tmp_path):
        audio = tmp_path / "audio.wav"
        audio.write_bytes(b"dummy")
        mock_model = self._make_mock_model()
        progress_values = []
        with patch("whisper.load_model", return_value=mock_model):
            WhisperRunner.transcribe(
                str(audio),
                duration=10.0,
                progress_callback=lambda p: progress_values.append(p),
            )
        assert len(progress_values) > 0
        assert progress_values[-1] == 100

    def test_model_load_failure_raises_whisper_model_error(self, tmp_path):
        audio = tmp_path / "audio.wav"
        audio.write_bytes(b"dummy")
        with patch("whisper.load_model", side_effect=RuntimeError("모델 로딩 실패")):
            with pytest.raises(WhisperModelError):
                WhisperRunner.transcribe(str(audio), duration=10.0)

    def test_transcribe_failure_raises_whisper_transcribe_error(self, tmp_path):
        audio = tmp_path / "audio.wav"
        audio.write_bytes(b"dummy")
        mock_model = MagicMock()
        mock_model.transcribe.side_effect = RuntimeError("변환 중 오류")
        with patch("whisper.load_model", return_value=mock_model):
            with pytest.raises(WhisperTranscribeError):
                WhisperRunner.transcribe(str(audio), duration=10.0)

    def test_cancel_before_transcribe_raises_interrupted(self, tmp_path):
        audio = tmp_path / "audio.wav"
        audio.write_bytes(b"dummy")
        mock_model = self._make_mock_model()
        token = CancellationToken()
        token.cancel()
        with patch("whisper.load_model", return_value=mock_model):
            with pytest.raises(InterruptedError):
                WhisperRunner.transcribe(str(audio), duration=10.0, cancel_token=token)

    def test_no_pyqt6_import_in_module(self):
        import ast
        import inspect
        import src.engine.whisper_runner as mod
        source = inspect.getsource(mod)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [alias.name for alias in node.names]
                module = getattr(node, "module", "") or ""
                assert "PyQt6" not in " ".join(names)
                assert "PyQt6" not in module
