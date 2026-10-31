"""Token Bucket Rate Limiter for high-concurrency traffic protection.

Ensures that even under extreme load (e.g., millions of fans querying simultaneously),
individual users or bots cannot exhaust system resources.
"""

import time
from collections import defaultdict
from typing import NamedTuple

from fastapi import HTTPException, Request, status


class BucketState(NamedTuple):
    tokens: float
    last_updated: float


class TokenBucketRateLimiter:
    def __init__(self, capacity: int = 15, refill_rate: float = 1.5) -> None:
        """
        capacity: Maximum burst capacity of tokens
        refill_rate: Tokens added per second
        """
        self.capacity = float(capacity)
        self.refill_rate = float(refill_rate)
        self.buckets: dict[str, BucketState] = defaultdict(
            lambda: BucketState(tokens=self.capacity, last_updated=time.monotonic())
        )

    def check_rate_limit(self, client_id: str, cost: float = 1.0) -> bool:
        now = time.monotonic()
        state = self.buckets[client_id]

        # Calculate refilled tokens based on elapsed time
        elapsed = now - state.last_updated
        new_tokens = min(self.capacity, state.tokens + (elapsed * self.refill_rate))

        if new_tokens >= cost:
            # Consume tokens
            self.buckets[client_id] = BucketState(tokens=new_tokens - cost, last_updated=now)
            return True
        else:
            # Rate limit exceeded
            self.buckets[client_id] = BucketState(tokens=new_tokens, last_updated=now)
            return False

    def get_retry_after(self, client_id: str, cost: float = 1.0) -> int:
        state = self.buckets[client_id]
        needed = cost - state.tokens
        if needed <= 0:
            return 0
        return max(1, int(needed / self.refill_rate))


# Default global instance (15 request burst, 1.5 req/sec sustained)
global_rate_limiter = TokenBucketRateLimiter(capacity=15, refill_rate=1.5)


async def rate_limit_dependency(request: Request) -> None:
    # Identify client by IP or forwarding header
    client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    client_ip = client_ip.split(",")[0].strip()

    if not global_rate_limiter.check_rate_limit(client_ip):
        retry_after = global_rate_limiter.get_retry_after(client_ip)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Too many concurrent requests. Please retry in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )
