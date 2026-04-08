"""OutputFormatter 단위 테스트"""
from src.engine.formatter import OutputFormatter


class TestOutputFormatter:
    def test_basic_segment(self):
        segments = [{"start": 0.0, "end": 5.0, "text": "안녕하세요"}]
        result = OutputFormatter.format_segments(segments)
        assert result == ["[00:00:00] 안녕하세요"]

    def test_timestamp_format_minutes(self):
        segments = [{"start": 65.0, "end": 70.0, "text": "hello"}]
        result = OutputFormatter.format_segments(segments)
        assert result == ["[00:01:05] hello"]

    def test_timestamp_format_hours(self):
        segments = [{"start": 3661.5, "end": 3665.0, "text": "test"}]
        result = OutputFormatter.format_segments(segments)
        assert result == ["[01:01:01] test"]

    def test_empty_text_excluded(self):
        segments = [{"start": 0.0, "end": 5.0, "text": ""}]
        result = OutputFormatter.format_segments(segments)
        assert result == []

    def test_whitespace_only_text_excluded(self):
        segments = [{"start": 0.0, "end": 5.0, "text": "   "}]
        result = OutputFormatter.format_segments(segments)
        assert result == []

    def test_text_stripped(self):
        segments = [{"start": 0.0, "end": 5.0, "text": "  hello world  "}]
        result = OutputFormatter.format_segments(segments)
        assert result == ["[00:00:00] hello world"]

    def test_empty_segments_list(self):
        result = OutputFormatter.format_segments([])
        assert result == []

    def test_multiple_segments(self):
        segments = [
            {"start": 0.0, "end": 5.0, "text": "첫 번째"},
            {"start": 5.0, "end": 10.0, "text": "두 번째"},
        ]
        result = OutputFormatter.format_segments(segments)
        assert result == ["[00:00:00] 첫 번째", "[00:00:05] 두 번째"]

    def test_mixed_valid_and_empty(self):
        segments = [
            {"start": 0.0, "end": 5.0, "text": "valid"},
            {"start": 5.0, "end": 10.0, "text": ""},
            {"start": 10.0, "end": 15.0, "text": "also valid"},
        ]
        result = OutputFormatter.format_segments(segments)
        assert result == ["[00:00:00] valid", "[00:00:10] also valid"]

    def test_zero_seconds(self):
        segments = [{"start": 0.0, "end": 1.0, "text": "start"}]
        result = OutputFormatter.format_segments(segments)
        assert result[0].startswith("[00:00:00]")

    def test_exactly_one_hour(self):
        segments = [{"start": 3600.0, "end": 3605.0, "text": "one hour"}]
        result = OutputFormatter.format_segments(segments)
        assert result == ["[01:00:00] one hour"]
