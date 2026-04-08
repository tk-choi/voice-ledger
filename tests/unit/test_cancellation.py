"""CancellationToken 단위 테스트"""
from src.engine.cancellation import CancellationToken


class TestCancellationToken:
    def test_initial_state_is_not_cancelled(self):
        token = CancellationToken()
        assert token.is_cancelled is False

    def test_cancel_sets_is_cancelled_to_true(self):
        token = CancellationToken()
        token.cancel()
        assert token.is_cancelled is True

    def test_double_cancel_is_safe(self):
        token = CancellationToken()
        token.cancel()
        token.cancel()  # 두 번 호출해도 예외 없음
        assert token.is_cancelled is True

    def test_independent_tokens_do_not_share_state(self):
        token1 = CancellationToken()
        token2 = CancellationToken()
        token1.cancel()
        assert token2.is_cancelled is False

    def test_new_token_after_cancel_starts_fresh(self):
        token1 = CancellationToken()
        token1.cancel()
        token2 = CancellationToken()
        assert token2.is_cancelled is False
