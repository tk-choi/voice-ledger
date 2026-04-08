"""Whisper STT 모델 로딩 및 변환 실행"""
import os
from typing import Callable, Optional

from faster_whisper import WhisperModel

from src.engine.exceptions import WhisperModelError, WhisperTranscribeError
from src.engine.cancellation import CancellationToken

MODEL_NAME = "large-v3"


class WhisperRunner:
    _model = None

    @classmethod
    def _get_model(cls):
        if cls._model is None:
            cls._model = WhisperModel(MODEL_NAME, device="auto", compute_type="int8")
        return cls._model

    @staticmethod
    def get_model_path() -> str:
        """faster-whisper 모델 캐시 디렉토리 경로를 반환한다."""
        return os.path.expanduser(
            f"~/.cache/huggingface/hub/models--Systran--faster-whisper-{MODEL_NAME}/"
        )

    @staticmethod
    def is_model_available() -> bool:
        """faster-whisper large-v3 모델이 로컬에 캐시되어 있는지 확인한다."""
        model_path = WhisperRunner.get_model_path()
        snapshots_path = os.path.join(model_path, "snapshots")
        return os.path.isdir(snapshots_path)

    @staticmethod
    def transcribe(
        audio_path: str,
        duration: float,
        progress_callback: Optional[Callable[[int], None]] = None,
        cancel_token: Optional[CancellationToken] = None,
    ) -> list[dict]:
        """WAV 파일을 faster-whisper로 변환하여 세그먼트 리스트를 반환한다.

        Args:
            audio_path: 입력 WAV 파일 경로
            duration: 오디오 총 길이 (초). 진행률 계산에 사용.
            progress_callback: 진행률(0-100) 콜백. 세그먼트별 실시간 호출.
            cancel_token: 취소 토큰. 세그먼트 사이에 is_cancelled 체크.

        Returns:
            세그먼트 리스트 [{"start": float, "end": float, "text": str}, ...]

        Raises:
            InterruptedError: cancel_token이 취소된 경우
            WhisperModelError: 모델 로딩 실패
            WhisperTranscribeError: 변환 중 예외
        """
        if cancel_token and cancel_token.is_cancelled:
            raise InterruptedError("변환이 취소되었습니다.")

        if progress_callback:
            progress_callback(0)

        try:
            model = WhisperRunner._get_model()
        except Exception as e:
            raise WhisperModelError(
                f"Whisper 모델 로딩에 실패했습니다. 앱을 재시작해 주세요: {e}"
            ) from e

        if cancel_token and cancel_token.is_cancelled:
            raise InterruptedError("변환이 취소되었습니다.")

        try:
            segments_gen, _info = model.transcribe(
                audio_path, beam_size=5, language=None, vad_filter=True
            )
            segments = []
            last_pct = -1
            for segment in segments_gen:
                if cancel_token and cancel_token.is_cancelled:
                    raise InterruptedError("변환이 취소되었습니다.")
                segments.append(
                    {"start": segment.start, "end": segment.end, "text": segment.text}
                )
                if progress_callback and duration > 0:
                    pct = min(int(segment.end / duration * 100), 100)
                    if pct != last_pct:
                        progress_callback(pct)
                        last_pct = pct
        except InterruptedError:
            raise
        except Exception as e:
            raise WhisperTranscribeError(
                f"변환 중 문제가 발생했습니다: {e}"
            ) from e

        if progress_callback:
            progress_callback(100)

        return segments
