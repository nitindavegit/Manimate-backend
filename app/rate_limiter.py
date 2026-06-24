import time
import logging
from collections import defaultdict, deque

class RateLimiter:
    def __init__(self, max_requests: int = 5, window_seconds: int = 900):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, deque] = defaultdict(deque)

    def is_allowed(self, key: str) -> tuple[bool, int]:
        now = time.time()
        window_start = now - self.window_seconds
        reqs = self._requests[key]

        while reqs and reqs[0] < window_start:
            reqs.popleft()

        if len(reqs) >= self.max_requests:
            wait_time = int(reqs[0] + self.window_seconds - now)
            return False, max(wait_time, 1)

        reqs.append(now)
        return True, 0

rate_limiter = RateLimiter(max_requests=2, window_seconds=86400)
