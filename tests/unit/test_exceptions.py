"""예외 계층 단위 테스트"""
import pytest
from src.engine.exceptions import (
    VoiceLedgerError,
    UnsupportedFormatError,
    FFmpegNotFoundError,
    FFmpegConversionError,
    WhisperModelError,
    WhisperTranscribeError,
    OutputWriteError,
)
from src.engine.cancellation import CancellationToken


class TestExceptionHierarchy:
    def test_all_exceptions_inherit_from_base(self):
        for exc_class in [
            UnsupportedFormatError,
            FFmpegNotFoundError,
            FFmpegConversionError,
            WhisperModelError,
            WhisperTranscribeError,
            OutputWriteError,
        ]:
            assert issubclass(exc_class, VoiceLedgerError)

    def test_base_inherits_from_exception(self):
        assert issubclass(VoiceLedgerError, Exception)

    def test_can_raise_and_catch_specific(self):
        with pytest.raises(UnsupportedFormatError):
            raise UnsupportedFormatError("지원하지 않는 형식")

    def test_can_catch_as_base(self):
        with pytest.raises(VoiceLedgerError):
            raise FFmpegNotFoundError("ffmpeg 없음")

    def test_exception_message_preserved(self):
        msg = "테스트 메시지"
        exc = WhisperModelError(msg)
        assert str(exc) == msg


class TestCancellationToken:
    def test_initial_state_not_cancelled(self):
        token = CancellationToken()
        assert token.is_cancelled is False

    def test_cancel_sets_flag(self):
        token = CancellationToken()
        token.cancel()
        assert token.is_cancelled is True

    def test_cancel_is_idempotent(self):
        token = CancellationToken()
        token.cancel()
        token.cancel()
        assert token.is_cancelled is True

    def test_independent_tokens(self):
        token1 = CancellationToken()
        token2 = CancellationToken()
        token1.cancel()
        assert token2.is_cancelled is False
