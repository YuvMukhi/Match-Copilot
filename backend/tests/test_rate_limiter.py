from app.core.rate_limiter import TokenBucketRateLimiter


def test_token_bucket_burst_and_exhaustion():
    # Capacity 3, refill 1 token/sec
    limiter = TokenBucketRateLimiter(capacity=3, refill_rate=1.0)
    client_id = "test_user_1"

    # Should allow 3 requests in burst
    assert limiter.check_rate_limit(client_id) is True
    assert limiter.check_rate_limit(client_id) is True
    assert limiter.check_rate_limit(client_id) is True

    # 4th immediate request should be rejected
    assert limiter.check_rate_limit(client_id) is False
    assert limiter.get_retry_after(client_id) >= 1


def test_token_bucket_isolated_clients():
    limiter = TokenBucketRateLimiter(capacity=2, refill_rate=1.0)

    # Client A consumes all tokens
    assert limiter.check_rate_limit("client_a") is True
    assert limiter.check_rate_limit("client_a") is True
    assert limiter.check_rate_limit("client_a") is False

    # Client B should still have full quota
    assert limiter.check_rate_limit("client_b") is True
    assert limiter.check_rate_limit("client_b") is True
