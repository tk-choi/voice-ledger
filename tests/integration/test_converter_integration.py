"""AudioConverter 통합 테스트 (ffmpeg 필요)"""
import os
import shutil
import pytest
from src.engine.converter import AudioConverter
from src.engine.exceptions import FFmpegConversionError

pytestmark = pytest.mark.skipif(
    shutil.which("ffmpeg") is None,
    reason="ffmpeg가 설치되지 않은 환경에서는 스킵"
)


class TestToWavIntegration:
    def test_converts_silence_m4a_to_wav(self):
        fixture = os.path.join(
            os.path.dirname(__file__), "..", "fixtures", "sample_audio", "silence_3s.m4a"
        )
        if not os.path.exists(fixture):
            pytest.skip("silence_3s.m4a 픽스처 없음 (generate_fixtures.sh 실행 필요)")

        with AudioConverter.temp_wav_file() as wav_path:
            AudioConverter.to_wav(fixture, wav_path)
            assert os.path.exists(wav_path)
            assert os.path.getsize(wav_path) > 0

    def test_get_duration_on_silence(self):
        fixture = os.path.join(
            os.path.dirname(__file__), "..", "fixtures", "sample_audio", "silence_3s.m4a"
        )
        if not os.path.exists(fixture):
            pytest.skip("silence_3s.m4a 픽스처 없음")

        duration = AudioConverter.get_duration(fixture)
        assert 2.5 <= duration <= 3.5  # 약 3초

    def test_corrupt_file_raises_conversion_error(self, corrupt_audio_file):
        with AudioConverter.temp_wav_file() as wav_path:
            with pytest.raises(FFmpegConversionError):
                AudioConverter.to_wav(corrupt_audio_file, wav_path)
