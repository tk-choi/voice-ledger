"""Whisper STT 모델 로딩 및 변환 실행"""
import os
from typing import Callable, Optional

import torch
import whisper

from src.engine.exceptions import WhisperModelError, WhisperTranscribeError
from src.engine.cancellation import CancellationToken

MODEL_NAME = "medium"


class WhisperRunner:
    _model = None
    _model_device: Optional[str] = None

    @classmethod
    def _get_model(cls):
        device = cls.get_device()
        if cls._model is None or cls._model_device != device:
            cls._model = whisper.load_model(MODEL_NAME, device=device)
            cls._model_device = device
        return cls._model

    @staticmethod
    def get_model_path() -> str:
        """Whisper 모델 캐시 파일 경로를 반환한다."""
        cache_dir = os.path.expanduser("~/.cache/whisper")
        return os.path.join(cache_dir, f"{MODEL_NAME}.pt")

    @staticmethod
    def is_model_available() -> bool:
        """Whisper medium 모델이 로컬에 캐시되어 있는지 확인한다."""
        return os.path.exists(WhisperRunner.get_model_path())

    @staticmethod
    def get_device() -> str:
        """사용 가능한 최적 디바이스를 반환한다 (mps > cpu)."""
        try:
            if (
                torch.backends.mps.is_available()
                and torch.backends.mps.is_built()
            ):
                return "mps"
        except Exception:
            pass
        return "cpu"

    @staticmethod
    def transcribe(
        audio_path: str,
        duration: float,
        progress_callback: Optional[Callable[[int], None]] = None,
        cancel_token: Optional[CancellationToken] = None,
    ) -> list[dict]:
        """WAV 파일을 Whisper로 변환하여 세그먼트 리스트를 반환한다.

        Args:
            audio_path: 입력 WAV 파일 경로
            duration: 오디오 총 길이 (초). 진행률 계산에 사용.
            progress_callback: 진행률(0-100) 콜백. Engine 레이어에서 Qt 의존 없음.
            cancel_token: 취소 토큰. transcribe 시작 전 is_cancelled 체크.

        Returns:
            Whisper 세그먼트 리스트 [{"start": float, "end": float, "text": str}, ...]

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
            result = model.transcribe(audio_path, language=None, verbose=False)
            segments = result.get("segments", [])
        except Exception as e:
            raise WhisperTranscribeError(
                f"변환 중 문제가 발생했습니다: {e}"
            ) from e

        if progress_callback:
            progress_callback(100)

        return segments
