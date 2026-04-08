"""WhisperRunner 단위 테스트 (mock 기반)"""
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
import pytest
from src.engine.exceptions import WhisperModelError, WhisperTranscribeError
from src.engine.cancellation import CancellationToken
from src.engine.whisper_runner import WhisperRunner


class TestIsModelAvailable:
    def test_returns_true_when_snapshots_dir_exists(self, tmp_path):
        model_dir = tmp_path / "model"
        snapshots_dir = model_dir / "snapshots"
        snapshots_dir.mkdir(parents=True)
        with patch.object(WhisperRunner, "get_model_path", return_value=str(model_dir)):
            assert WhisperRunner.is_model_available() is True

    def test_returns_false_when_snapshots_dir_missing(self, tmp_path):
        model_dir = str(tmp_path / "model")
        with patch.object(WhisperRunner, "get_model_path", return_value=model_dir):
            assert WhisperRunner.is_model_available() is False


class TestGetModelPath:
    def test_returns_string(self):
        path = WhisperRunner.get_model_path()
        assert isinstance(path, str)

    def test_path_contains_huggingface_and_large_v3(self):
        path = WhisperRunner.get_model_path()
        assert "huggingface" in path.lower()
        assert "large-v3" in path


class TestTranscribe:
    def setup_method(self):
        WhisperRunner._model = None

    def _make_mock_segments(self, segments=None):
        if segments is None:
            segments = [
                SimpleNamespace(start=0.0, end=5.0, text="안녕하세요"),
                SimpleNamespace(start=5.0, end=10.0, text="테스트입니다"),
            ]
        info = SimpleNamespace(language="ko", language_probability=0.95, duration=10.0)
        return (iter(segments), info)

    def _make_mock_model(self, segments=None):
        mock_model = MagicMock()
        mock_model.transcribe.return_value = self._make_mock_segments(segments)
        return mock_model

    def test_returns_segments_list(self, tmp_path):
        audio = tmp_path / "audio.wav"
        audio.write_bytes(b"dummy")
        mock_model = self._make_mock_model()
        with patch("src.engine.whisper_runner.WhisperModel", return_value=mock_model):
            result = WhisperRunner.transcribe(str(audio), duration=10.0)
            assert isinstance(result, list)
            assert len(result) == 2

    def test_segments_have_required_keys(self, tmp_path):
        audio = tmp_path / "audio.wav"
        audio.write_bytes(b"dummy")
        mock_model = self._make_mock_model()
        with patch("src.engine.whisper_runner.WhisperModel", return_value=mock_model):
            result = WhisperRunner.transcribe(str(audio), duration=10.0)
            for seg in result:
                assert "start" in seg
                assert "end" in seg
                assert "text" in seg

    def test_loads_large_v3_model(self, tmp_path):
        audio = tmp_path / "audio.wav"
        audio.write_bytes(b"dummy")
        mock_model = self._make_mock_model()
        with patch("src.engine.whisper_runner.WhisperModel", return_value=mock_model) as mock_cls:
            WhisperRunner.transcribe(str(audio), duration=10.0)
            call_args = mock_cls.call_args
            assert call_args[0][0] == "large-v3"

    def test_calls_progress_callback(self, tmp_path):
        audio = tmp_path / "audio.wav"
        audio.write_bytes(b"dummy")
        mock_model = self._make_mock_model()
        progress_values = []
        with patch("src.engine.whisper_runner.WhisperModel", return_value=mock_model):
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
        with patch("src.engine.whisper_runner.WhisperModel", side_effect=RuntimeError("모델 로딩 실패")):
            with pytest.raises(WhisperModelError):
                WhisperRunner.transcribe(str(audio), duration=10.0)

    def test_transcribe_failure_raises_whisper_transcribe_error(self, tmp_path):
        audio = tmp_path / "audio.wav"
        audio.write_bytes(b"dummy")
        mock_model = MagicMock()
        mock_model.transcribe.side_effect = RuntimeError("변환 중 오류")
        with patch("src.engine.whisper_runner.WhisperModel", return_value=mock_model):
            with pytest.raises(WhisperTranscribeError):
                WhisperRunner.transcribe(str(audio), duration=10.0)

    def test_cancel_before_transcribe_raises_interrupted(self, tmp_path):
        audio = tmp_path / "audio.wav"
        audio.write_bytes(b"dummy")
        mock_model = self._make_mock_model()
        token = CancellationToken()
        token.cancel()
        with patch("src.engine.whisper_runner.WhisperModel", return_value=mock_model):
            with pytest.raises(InterruptedError):
                WhisperRunner.transcribe(str(audio), duration=10.0, cancel_token=token)

    def test_progress_callback_called_with_0_and_100(self, tmp_path):
        audio = tmp_path / "audio.wav"
        audio.write_bytes(b"dummy")
        mock_model = self._make_mock_model()
        progress_values = []
        with patch("src.engine.whisper_runner.WhisperModel", return_value=mock_model):
            WhisperRunner.transcribe(
                str(audio),
                duration=10.0,
                progress_callback=lambda p: progress_values.append(p),
            )
        assert progress_values[0] == 0
        assert progress_values[-1] == 100

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
