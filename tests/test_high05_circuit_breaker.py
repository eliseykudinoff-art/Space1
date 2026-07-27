"""
Тесты для проверки [HIGH-05]: CircuitBreaker — стабилизация HALF_OPEN.

Проблема: HALF_OPEN → 1 success = CLOSED, 1 failure = OPEN (мигание).
Исправление: consecutive_successes_threshold = 3 (нужно 3 подряд success).
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from space1.orchestrator.core import CircuitBreaker, CircuitBreakerOpenException


class TestCircuitBreakerStabilization:
    """Проверка [HIGH-05]: HALF_OPEN стабилизирован через consecutive_successes."""

    def test_half_open_needs_three_consecutive_successes(self):
        """В HALF_OPEN нужно 3 подряд success для перехода в CLOSED."""
        cb = CircuitBreaker(failure_threshold=3, cooldown_seconds=0.1)

        # Переводим в OPEN
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "OPEN"

        # Ждём cooldown и переводим в HALF_OPEN
        import time
        time.sleep(0.15)
        cb.before_call()  # Переходит в HALF_OPEN
        assert cb.state == "HALF_OPEN"

        # 1 success — всё ещё HALF_OPEN
        cb.record_success()
        assert cb.state == "HALF_OPEN"
        assert cb.consecutive_successes == 1

        # 2 success — всё ещё HALF_OPEN
        cb.record_success()
        assert cb.state == "HALF_OPEN"
        assert cb.consecutive_successes == 2

        # 3 success — CLOSED
        cb.record_success()
        assert cb.state == "CLOSED"
        assert cb.consecutive_successes == 0  # Сброшено

    def test_half_open_one_failure_goes_open(self):
        """В HALF_OPEN 1 failure = OPEN (безопасность сохранена)."""
        cb = CircuitBreaker(failure_threshold=3, cooldown_seconds=0.1)

        # Переводим в OPEN
        for _ in range(3):
            cb.record_failure()
        assert cb.state == "OPEN"

        # HALF_OPEN
        import time
        time.sleep(0.15)
        cb.before_call()
        assert cb.state == "HALF_OPEN"

        # 2 success
        cb.record_success()
        cb.record_success()
        assert cb.state == "HALF_OPEN"

        # 1 failure = OPEN
        cb.record_failure()
        assert cb.state == "OPEN"

    def test_closed_resets_consecutive_successes(self):
        """В CLOSED consecutive_successes не накапливается."""
        cb = CircuitBreaker()
        assert cb.state == "CLOSED"

        cb.record_success()
        assert cb.state == "CLOSED"
        assert cb.consecutive_successes == 0

        cb.record_success()
        assert cb.state == "CLOSED"
        assert cb.consecutive_successes == 0

    def test_half_open_resets_on_entry(self):
        """При входе в HALF_OPEN consecutive_successes сбрасывается в 0."""
        cb = CircuitBreaker(failure_threshold=1, cooldown_seconds=0.1)

        cb.record_failure()
        assert cb.state == "OPEN"

        # Симулируем: consecutive_successes мог быть не 0
        cb.consecutive_successes = 999

        import time
        time.sleep(0.15)
        cb.before_call()
        assert cb.state == "HALF_OPEN"
        assert cb.consecutive_successes == 0

    def test_configurable_threshold(self):
        """Порог можно настроить через конструктор."""
        cb = CircuitBreaker(consecutive_successes_threshold=5)
        assert cb.consecutive_successes_threshold == 5

        cb = CircuitBreaker(consecutive_successes_threshold=1)
        assert cb.consecutive_successes_threshold == 1
