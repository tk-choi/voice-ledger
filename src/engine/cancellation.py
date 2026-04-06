"""변환 취소 토큰"""


class CancellationToken:
    """협력적 취소를 위한 토큰.

    Engine 파이프라인의 단계 간에서 is_cancelled를 체크하여
    InterruptedError를 발생시키는 데 사용한다.
    """

    def __init__(self) -> None:
        self._cancelled = False

    def cancel(self) -> None:
        """취소 요청. 멱등적 (여러 번 호출해도 안전)."""
        self._cancelled = True

    @property
    def is_cancelled(self) -> bool:
        """취소 요청 여부."""
        return self._cancelled
