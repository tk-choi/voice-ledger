"""오디오 파일을 Whisper 입력용 WAV로 변환하는 AudioConverter"""
import os
import sys
import subprocess
import tempfile
from contextlib import contextmanager
from src.engine.exceptions import FFmpegNotFoundError, FFmpegConversionError


class AudioConverter:
    @staticmethod
    def get_ffmpeg_path() -> str:
        """ffmpeg 실행 파일 경로를 반환한다.

        py2app으로 패키징된 경우 번들 내 ffmpeg를 사용한다.
        개발 환경에서는 시스템 PATH의 ffmpeg를 사용한다.
        """
        if getattr(sys, "frozen", False):
            bundle_dir = os.path.dirname(sys.executable)
            return os.path.join(bundle_dir, "..", "Resources", "bin", "ffmpeg")
        return "ffmpeg"

    @staticmethod
    def get_duration(file_path: str) -> float:
        """오디오 파일의 총 길이를 초 단위로 반환한다 (ffprobe 사용).

        Raises:
            FFmpegNotFoundError: ffprobe 실행 파일 없음
            FFmpegConversionError: 길이 측정 실패
        """
        ffmpeg_path = AudioConverter.get_ffmpeg_path()
        ffprobe_path = ffmpeg_path.replace("ffmpeg", "ffprobe")

        try:
            result = subprocess.run(
                [
                    ffprobe_path,
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    file_path,
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0 or not result.stdout.strip():
                raise FFmpegConversionError(
                    f"오디오 길이를 측정할 수 없습니다: {result.stderr}"
                )
            return float(result.stdout.strip())
        except FileNotFoundError as e:
            raise FFmpegNotFoundError(
                "ffmpeg/ffprobe를 찾을 수 없습니다. brew install ffmpeg를 실행해 주세요."
            ) from e

    @staticmethod
    def to_wav(input_path: str, output_path: str) -> None:
        """m4a/mp4 파일을 Whisper 입력용 16kHz mono WAV로 변환한다.

        Raises:
            FFmpegNotFoundError: ffmpeg 실행 파일 없음
            FFmpegConversionError: 변환 실패
        """
        ffmpeg_path = AudioConverter.get_ffmpeg_path()

        try:
            subprocess.run(
                [
                    ffmpeg_path,
                    "-y",           # 기존 파일 덮어쓰기
                    "-i", input_path,
                    "-ar", "16000", # Whisper 요구: 16kHz
                    "-ac", "1",     # mono
                    "-f", "wav",
                    output_path,
                ],
                check=True,
                capture_output=True,
            )
        except FileNotFoundError as e:
            raise FFmpegNotFoundError(
                "ffmpeg를 찾을 수 없습니다. brew install ffmpeg를 실행해 주세요."
            ) from e
        except subprocess.CalledProcessError as e:
            raise FFmpegConversionError(
                "오디오 변환에 실패했습니다. 파일이 손상되었거나 오디오 트랙이 없을 수 있습니다."
            ) from e

    @staticmethod
    @contextmanager
    def temp_wav_file():
        """임시 WAV 파일을 생성하고 블록 종료 시 자동 삭제하는 컨텍스트 매니저."""
        fd, path = tempfile.mkstemp(suffix=".wav", prefix="voice_ledger_")
        os.close(fd)
        try:
            yield path
        finally:
            try:
                os.remove(path)
            except OSError:
                pass
