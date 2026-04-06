"""Whisper 세그먼트를 타임스탬프 포함 텍스트로 포맷"""


class OutputFormatter:
    @staticmethod
    def format_segments(segments: list[dict]) -> list[str]:
        """Whisper segments를 '[HH:MM:SS] text' 형식 문자열 리스트로 변환한다.

        Args:
            segments: Whisper transcribe() 반환 세그먼트 리스트.
                      각 항목: {"start": float, "end": float, "text": str}

        Returns:
            빈 텍스트를 제외한 '[HH:MM:SS] text' 형식 문자열 리스트
        """
        lines = []
        for segment in segments:
            text = segment.get("text", "").strip()
            if not text:
                continue
            timestamp = OutputFormatter._format_timestamp(segment["start"])
            lines.append(f"[{timestamp}] {text}")
        return lines

    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """초 단위 시간을 'HH:MM:SS' 형식으로 변환한다."""
        total_seconds = int(seconds)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
