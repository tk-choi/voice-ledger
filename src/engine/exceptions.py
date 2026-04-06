"""Voice Ledger 사용자 정의 예외 계층"""


class VoiceLedgerError(Exception):
    """앱 전용 기본 예외"""
    pass


class UnsupportedFormatError(VoiceLedgerError):
    """지원하지 않는 파일 형식"""
    pass


class FFmpegNotFoundError(VoiceLedgerError):
    """ffmpeg 실행 파일을 찾을 수 없음"""
    pass


class FFmpegConversionError(VoiceLedgerError):
    """ffmpeg 변환 실패"""
    pass


class WhisperModelError(VoiceLedgerError):
    """Whisper 모델 로딩 실패 또는 다운로드 실패"""
    pass


class WhisperTranscribeError(VoiceLedgerError):
    """Whisper 변환 중 예외"""
    pass


class OutputWriteError(VoiceLedgerError):
    """출력 파일 쓰기 실패"""
    pass
