import time
from dataclasses import dataclass, field


@dataclass
class CircuitBreaker:
    name: str
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    _failures: int = field(default=0, init=False)
    _last_failure: float = field(default=0.0, init=False)
    _open: bool = field(default=False, init=False)

    def allow(self) -> bool:
        if not self._open:
            return True
        if time.time() - self._last_failure >= self.recovery_timeout:
            self._open = False
            self._failures = 0
            return True
        return False

    def record_success(self) -> None:
        self._failures = 0
        self._open = False

    def record_failure(self) -> None:
        self._failures += 1
        self._last_failure = time.time()
        if self._failures >= self.failure_threshold:
            self._open = True


razorpay_circuit = CircuitBreaker(name="razorpay")
