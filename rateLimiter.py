"""
Rate Limiter Algorithms — minimal Python implementations
"""

import time
from collections import deque


# ─────────────────────────────────────────────
#  1. Token Bucket
# ─────────────────────────────────────────────

class TokenBucket:
    def __init__(self, capacity: int, rate: float):
        self.capacity = capacity   # max tokens
        self.rate     = rate       # tokens added per second
        self.tokens   = capacity   # start full
        self.last     = time.time()

    def allow(self) -> bool:
        now   = time.time()
        delta = now - self.last
        # refill tokens proportional to elapsed time
        self.tokens = min(self.capacity, self.tokens + delta * self.rate)
        self.last   = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


# ─────────────────────────────────────────────
#  2. Leaky Bucket
# ─────────────────────────────────────────────

class LeakyBucket:
    def __init__(self, capacity: int, rate: float):
        self.capacity = capacity   # max queue size
        self.rate     = rate       # requests drained per second
        self.queue    = deque()
        self.last     = time.time()

    def allow(self) -> bool:
        now    = time.time()
        leaked = (now - self.last) * self.rate
        # drain processed requests
        for _ in range(int(leaked)):
            if self.queue:
                self.queue.popleft()
        self.last = now
        if len(self.queue) < self.capacity:
            self.queue.append(now)
            return True
        return False


# ─────────────────────────────────────────────
#  3. Fixed Window Counter
# ─────────────────────────────────────────────

class FixedWindowCounter:
    def __init__(self, limit: int, window: float):
        self.limit  = limit    # max requests per window
        self.window = window   # window size in seconds
        self.count  = 0
        self.start  = time.time()

    def allow(self) -> bool:
        now = time.time()
        # reset counter when window expires
        if now - self.start >= self.window:
            self.count = 0
            self.start = now
        if self.count < self.limit:
            self.count += 1
            return True
        return False


# ─────────────────────────────────────────────
#  4. Sliding Window Log
# ─────────────────────────────────────────────

class SlidingWindowLog:
    def __init__(self, limit: int, window: float):
        self.limit  = limit    # max requests in window
        self.window = window   # window size in seconds
        self.log    = deque()  # timestamps of allowed requests

    def allow(self) -> bool:
        now    = time.time()
        cutoff = now - self.window
        # evict timestamps outside the window
        while self.log and self.log[0] < cutoff:
            self.log.popleft()
        if len(self.log) < self.limit:
            self.log.append(now)
            return True
        return False


# ─────────────────────────────────────────────
#  5. Sliding Window Counter
# ─────────────────────────────────────────────

class SlidingWindowCounter:
    def __init__(self, limit: int, window: float):
        self.limit     = limit    # max requests per window
        self.window    = window   # window size in seconds
        self.prev      = 0        # previous window count
        self.curr      = 0        # current window count
        self.win_start = time.time()

    def allow(self) -> bool:
        now     = time.time()
        elapsed = now - self.win_start

        if elapsed >= self.window * 2:
            # both windows expired — full reset
            self.prev, self.curr = 0, 0
            self.win_start = now
            elapsed = 0
        elif elapsed >= self.window:
            # slide forward one window
            self.prev = self.curr
            self.curr = 0
            self.win_start += self.window
            elapsed -= self.window

        # weight previous window by how much it overlaps the current sliding window
        overlap  = 1 - elapsed / self.window
        estimate = self.prev * overlap + self.curr

        if estimate < self.limit:
            self.curr += 1
            return True
        return False


# ─────────────────────────────────────────────
#  Quick demo
# ─────────────────────────────────────────────

if __name__ == "__main__":
    limiters = {
        "TokenBucket":          TokenBucket(capacity=5, rate=1),
        "LeakyBucket":          LeakyBucket(capacity=5, rate=1),
        "FixedWindowCounter":   FixedWindowCounter(limit=5, window=5),
        "SlidingWindowLog":     SlidingWindowLog(limit=5, window=5),
        "SlidingWindowCounter": SlidingWindowCounter(limit=5, window=5),
    }

    print(f"{'Algorithm':<25} {'Results (10 rapid requests)'}")
    print("─" * 60)
    for name, limiter in limiters.items():
        results = ["✓" if limiter.allow() else "✗" for _ in range(10)]
        print(f"{name:<25} {'  '.join(results)}")