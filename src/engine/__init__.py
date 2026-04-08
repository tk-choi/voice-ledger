"""Voice Ledger Engine — 변환 파이프라인"""
from typing import Callable, Optional

from src.engine import converter, formatter, validator, whisper_runner, writer
from src.engine.cancellation import CancellationToken
from src.engine.exceptions import VoiceLedgerError


def run_transcription(
    input_path: str,
    overwrite: bool = False,
    progress_callback: Optional[Callable[[int], None]] = None,
    cancel_token: Optional[CancellationToken] = None,
    stage_callback: Optional[Callable[[str], None]] = None,
) -> str:
    """음성 파일을 텍스트로 변환하는 전체 파이프라인.

    Args:
        input_path: 입력 m4a/mp4 파일의 절대 경로
        overwrite: True면 기존 .txt 덮어쓰기, False면 FileExistsError
        progress_callback: 진행률(0-100) 콜백. GUI의 Signal emit에 연결됨.
        cancel_token: 취소 토큰. 단계 간 is_cancelled를 체크한다.
        stage_callback: 현재 단계 이름 콜백. GUI에서 단계별 메시지 표시에 사용.
            단계: "validating", "converting", "transcribing", "saving"

    Returns:
        생성된 출력 .txt 파일의 경로

    Raises:
        InterruptedError: cancel_token이 취소된 경우
        FileExistsError: overwrite=False이고 출력 파일이 이미 존재할 때
        UnsupportedFormatError: 지원하지 않는 파일 형식
        FFmpegNotFoundError: ffmpeg 없음
        FFmpegConversionError: 오디오 변환 실패
        WhisperModelError: 모델 로딩 실패
        WhisperTranscribeError: 변환 중 예외
        OutputWriteError: 파일 쓰기 실패
    """
    def _check_cancel() -> None:
        if cancel_token and cancel_token.is_cancelled:
            raise InterruptedError("변환이 취소되었습니다.")

    def _emit_stage(name: str) -> None:
        if stage_callback:
            stage_callback(name)

    def _emit_progress(value: int) -> None:
        if progress_callback:
            progress_callback(value)

    _check_cancel()

    # 1. 파일 유효성 검증
    _emit_stage("validating")
    _emit_progress(2)
    validator.FileValidator.validate(input_path)
    _check_cancel()

    # 2. 출력 경로 확인 및 덮어쓰기 검사 (변환 전에 수행)
    output_path = writer.FileWriter.derive_output_path(input_path)
    if not overwrite and writer.FileWriter.check_existing(output_path):
        raise FileExistsError(f"파일이 이미 존재합니다: {output_path}")
    _check_cancel()

    # 3. WAV 변환 → Whisper 변환 (임시 파일은 컨텍스트 매니저가 보장)
    _emit_stage("converting")
    _emit_progress(5)
    with converter.AudioConverter.temp_wav_file() as wav_path:
        converter.AudioConverter.to_wav(input_path, wav_path)
        _emit_progress(10)
        _check_cancel()

        _emit_stage("transcribing")
        duration = converter.AudioConverter.get_duration(wav_path)

        def _map_progress(p):
            mapped = 10 + int(p * 0.79)  # 0-100 → 10-89
            _emit_progress(min(mapped, 89))

        segments = whisper_runner.WhisperRunner.transcribe(
            wav_path, duration=duration,
            progress_callback=_map_progress,
            cancel_token=cancel_token,
        )
        _emit_progress(90)

    # 4. 포맷 → 저장
    _emit_stage("saving")
    _emit_progress(95)
    lines = formatter.OutputFormatter.format_segments(segments)
    writer.FileWriter.write(lines, output_path, overwrite=overwrite)
    _emit_progress(100)

    return output_path
