"""파일 유효성 검증"""
import os
from src.engine.exceptions import UnsupportedFormatError

SUPPORTED_EXTENSIONS = {".m4a", ".mp4"}


class FileValidator:
    @staticmethod
    def validate(file_path: str) -> None:
        """파일 경로의 유효성을 검증한다.

        Args:
            file_path: 검증할 파일의 절대 경로

        Raises:
            FileNotFoundError: 파일이 존재하지 않음
            UnsupportedFormatError: 지원하지 않는 형식이거나 0바이트 파일
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

        _, ext = os.path.splitext(file_path)
        if ext.lower() not in SUPPORTED_EXTENSIONS:
            raise UnsupportedFormatError(
                f"지원하지 않는 파일 형식입니다 ({ext}). "
                f".m4a 또는 .mp4 파일을 사용해 주세요."
            )

        if os.path.getsize(file_path) == 0:
            raise UnsupportedFormatError(
                "파일 크기가 0바이트입니다. 유효한 오디오 파일을 사용해 주세요."
            )
