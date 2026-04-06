"""출력 .txt 파일 생성 및 경로 관리"""
import os
from src.engine.exceptions import OutputWriteError


class FileWriter:
    @staticmethod
    def derive_output_path(input_path: str) -> str:
        """입력 파일 경로에서 출력 .txt 파일 경로를 생성한다.

        예: /path/to/meeting.m4a → /path/to/meeting.txt
        """
        base, _ = os.path.splitext(input_path)
        return base + ".txt"

    @staticmethod
    def check_existing(output_path: str) -> bool:
        """출력 경로에 파일이 이미 존재하는지 확인한다."""
        return os.path.exists(output_path)

    @staticmethod
    def write(
        lines: list[str],
        output_path: str,
        overwrite: bool = False,
    ) -> str:
        """포맷된 텍스트를 UTF-8 인코딩으로 .txt 파일에 저장한다.

        Args:
            lines: '[HH:MM:SS] text' 형식 문자열 리스트
            output_path: 출력 파일 경로
            overwrite: True면 기존 파일 덮어쓰기, False면 FileExistsError 발생

        Returns:
            저장된 파일의 경로

        Raises:
            FileExistsError: overwrite=False이고 파일이 이미 존재할 때
            OutputWriteError: 쓰기 권한 부재 또는 기타 I/O 오류
        """
        if not overwrite and os.path.exists(output_path):
            raise FileExistsError(f"파일이 이미 존재합니다: {output_path}")

        try:
            with open(output_path, "w", encoding="utf-8", newline="\n") as f:
                for line in lines:
                    f.write(line + "\n")
        except PermissionError as e:
            raise OutputWriteError(
                f"파일을 저장할 수 없습니다. 저장 위치 권한을 확인해 주세요: {output_path}"
            ) from e
        except OSError as e:
            raise OutputWriteError(f"파일 저장 중 오류가 발생했습니다: {e}") from e

        return output_path
