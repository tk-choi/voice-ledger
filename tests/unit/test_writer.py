"""FileWriter 단위 테스트"""
import os
import pytest
from src.engine.exceptions import OutputWriteError
from src.engine.writer import FileWriter


class TestDeriveOutputPath:
    def test_m4a_to_txt(self):
        result = FileWriter.derive_output_path("/path/to/meeting.m4a")
        assert result == "/path/to/meeting.txt"

    def test_mp4_to_txt(self):
        result = FileWriter.derive_output_path("/path/to/video.mp4")
        assert result == "/path/to/video.txt"

    def test_preserves_directory(self):
        result = FileWriter.derive_output_path("/Users/user/Downloads/audio.m4a")
        assert result == "/Users/user/Downloads/audio.txt"

    def test_filename_with_dots(self):
        result = FileWriter.derive_output_path("/path/meeting.2026.04.m4a")
        assert result == "/path/meeting.2026.04.txt"


class TestCheckExisting:
    def test_existing_file_returns_true(self, tmp_path):
        f = tmp_path / "output.txt"
        f.write_text("existing content")
        assert FileWriter.check_existing(str(f)) is True

    def test_nonexistent_file_returns_false(self, tmp_path):
        path = str(tmp_path / "nonexistent.txt")
        assert FileWriter.check_existing(path) is False


class TestWrite:
    def test_creates_file(self, tmp_path):
        output_path = str(tmp_path / "output.txt")
        FileWriter.write(["[00:00:00] hello"], output_path)
        assert os.path.exists(output_path)

    def test_utf8_encoding(self, tmp_path):
        output_path = str(tmp_path / "output.txt")
        lines = ["[00:00:00] 안녕하세요"]
        FileWriter.write(lines, output_path)
        content = open(output_path, encoding="utf-8").read()
        assert "안녕하세요" in content

    def test_lf_line_endings(self, tmp_path):
        output_path = str(tmp_path / "output.txt")
        lines = ["line1", "line2"]
        FileWriter.write(lines, output_path)
        raw = open(output_path, "rb").read()
        assert b"\r\n" not in raw
        assert b"\n" in raw

    def test_multiple_lines(self, tmp_path):
        output_path = str(tmp_path / "output.txt")
        lines = ["[00:00:00] first", "[00:00:05] second"]
        FileWriter.write(lines, output_path)
        content = open(output_path, encoding="utf-8").read()
        assert "[00:00:00] first\n[00:00:05] second\n" == content

    def test_empty_lines_creates_empty_file(self, tmp_path):
        output_path = str(tmp_path / "output.txt")
        FileWriter.write([], output_path)
        assert os.path.exists(output_path)
        assert open(output_path).read() == ""

    def test_overwrite_true_replaces_content(self, tmp_path):
        output_path = str(tmp_path / "output.txt")
        open(output_path, "w").write("old content")
        FileWriter.write(["new content"], output_path, overwrite=True)
        assert open(output_path, encoding="utf-8").read() == "new content\n"

    def test_overwrite_false_raises_on_existing(self, tmp_path):
        output_path = str(tmp_path / "output.txt")
        open(output_path, "w").write("existing")
        with pytest.raises(FileExistsError):
            FileWriter.write(["new"], output_path, overwrite=False)

    def test_write_permission_error(self, readonly_dir):
        output_path = os.path.join(readonly_dir, "output.txt")
        with pytest.raises(OutputWriteError):
            FileWriter.write(["content"], output_path)

    def test_returns_output_path(self, tmp_path):
        output_path = str(tmp_path / "output.txt")
        result = FileWriter.write(["hello"], output_path)
        assert result == output_path
