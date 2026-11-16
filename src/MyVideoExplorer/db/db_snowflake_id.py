from __future__ import annotations

import threading
import time


class SnowflakeIdGenerator:
    """Generate 64-bit snowflake IDs that are unique, positive, and time-ordered.

    ID layout (64-bit signed, always positive in practice):
        [1 sign bit][41 bits epoch_ms][10 bits worker_id][13 bits per-ms sequence]

    - Epoch: 2024-01-01T00:00:00Z (1704067200000 ms)
    - Worker ID: fixed 0 (single-instance desktop app)
    - Per-ms sequence: 13-bit counter (0–8191 per millisecond)
    - Thread-safe via ``threading.Lock``
    - Blocks until the next millisecond on sequence overflow.
    """

    EPOCH_MS: int = 1704067200000  # 2024-01-01T00:00:00Z
    WORKER_ID: int = 0

    _SEQUENCE_BITS: int = 13
    _WORKER_BITS: int = 10
    _TIMESTAMP_BITS: int = 41

    _SEQUENCE_MASK: int = (1 << _SEQUENCE_BITS) - 1  # 8191

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._last_timestamp = 0
        self._sequence = 0

    def generate(self) -> int:
        """Generate a new unique snowflake ID."""
        with self._lock:
            now_ms = self._now_ms()
            timestamp = now_ms - self.EPOCH_MS

            if timestamp == self._last_timestamp:
                self._sequence = (self._sequence + 1) & self._SEQUENCE_MASK
                if self._sequence == 0:
                    # Sequence overflow — wait for the next millisecond
                    now_ms = self._wait_for_next_ms(now_ms)
                    timestamp = now_ms - self.EPOCH_MS
            else:
                self._sequence = 0

            self._last_timestamp = timestamp
            return (
                (timestamp << (self._SEQUENCE_BITS + self._WORKER_BITS))
                | (self.WORKER_ID << self._SEQUENCE_BITS)
                | self._sequence
            )

    @staticmethod
    def _now_ms() -> int:
        return int(time.time() * 1000)

    @staticmethod
    def _wait_for_next_ms(last_ms: int) -> int:
        while True:
            now_ms = int(time.time() * 1000)
            if now_ms > last_ms:
                return now_ms
