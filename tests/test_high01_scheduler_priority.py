"""
Тесты для проверки [HIGH-01]: Scheduler OWNER_DIRECT priority.

AIOSScheduler.pop_next_task() должен:
1. Всегда отдавать OWNER_DIRECT задачи перед MARKETPLACE
2. Внутри каждой группы сортировать по priority.value (descending)
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from space1.orchestrator.scheduler import AIOSScheduler
from space1.models.task import Task, TaskPriority


class TestSchedulerOwnerDirectPriority:
    """Проверка [HIGH-01]: OWNER_DIRECT всегда приоритетнее MARKETPLACE,
    внутри группы — сортировка по priority.value (descending)."""

    def _make_sched(self):
        """Создать scheduler с уникальным временным файлом + cleanup."""
        import tempfile
        fd, path = tempfile.mkstemp(suffix="_sched.json")
        os.close(fd)
        sched = AIOSScheduler(filepath=path)
        # Очищаем, если файл был создан до этого (маловероятно для mkstemp)
        sched.clear()
        return sched, path

    def _cleanup(self, sched, path):
        """Удалить временный файл."""
        sched.clear()
        if os.path.exists(path):
            os.remove(path)

    def test_owner_direct_overrides_marketplace(self):
        """OWNER_DIRECT с LOW priority > MARKETPLACE с CRITICAL priority."""
        sched, path = self._make_sched()
        try:
            market_critical = Task(
                id="m_crit", title="Market critical",
                priority=TaskPriority.CRITICAL,
                metadata={"source": "MARKETPLACE"}
            )
            owner_low = Task(
                id="o_low", title="Owner low",
                priority=TaskPriority.LOW,
                metadata={"source": "OWNER_DIRECT"}
            )

            sched.add_task(market_critical)
            sched.add_task(owner_low)

            next_task = sched.pop_next_task()
            assert next_task.id == "o_low", \
                f"OWNER_DIRECT должен иметь приоритет над MARKETPLACE, получили {next_task.id}"
        finally:
            self._cleanup(sched, path)

    def test_owner_direct_sorted_by_priority(self):
        """Среди OWNER_DIRECT — CRITICAL > HIGH > MEDIUM > LOW."""
        sched, path = self._make_sched()
        try:
            for prio in [TaskPriority.LOW, TaskPriority.CRITICAL, TaskPriority.MEDIUM]:
                sched.add_task(Task(
                    id=f"o_{prio.name.lower()}",
                    title=f"Owner {prio.name}",
                    priority=prio,
                    metadata={"source": "OWNER_DIRECT"}
                ))

            order = []
            while True:
                t = sched.pop_next_task()
                if t is None:
                    break
                order.append(t.priority)

            assert order == [TaskPriority.CRITICAL, TaskPriority.MEDIUM, TaskPriority.LOW]
        finally:
            self._cleanup(sched, path)

    def test_marketplace_sorted_by_priority(self):
        """Среди MARKETPLACE — тоже CRITICAL > HIGH > MEDIUM > LOW."""
        sched, path = self._make_sched()
        try:
            for prio in [TaskPriority.HIGH, TaskPriority.LOW, TaskPriority.CRITICAL]:
                sched.add_task(Task(
                    id=f"m_{prio.name.lower()}",
                    title=f"Market {prio.name}",
                    priority=prio,
                    metadata={"source": "MARKETPLACE"}
                ))

            order = []
            while True:
                t = sched.pop_next_task()
                if t is None:
                    break
                order.append(t.priority)

            assert order == [TaskPriority.CRITICAL, TaskPriority.HIGH, TaskPriority.LOW]
        finally:
            self._cleanup(sched, path)

    def test_mixed_owner_and_market(self):
        """OWNER_DIRECT (любой priority) всегда перед MARKETPLACE (любой priority)."""
        sched, path = self._make_sched()
        try:
            tasks = [
                Task("m1", "M LOW", priority=TaskPriority.LOW, metadata={"source": "MARKETPLACE"}),
                Task("o1", "O CRIT", priority=TaskPriority.CRITICAL, metadata={"source": "OWNER_DIRECT"}),
                Task("m2", "M CRIT", priority=TaskPriority.CRITICAL, metadata={"source": "MARKETPLACE"}),
                Task("o2", "O LOW", priority=TaskPriority.LOW, metadata={"source": "OWNER_DIRECT"}),
            ]
            for t in tasks:
                sched.add_task(t)

            order = []
            while True:
                t = sched.pop_next_task()
                if t is None:
                    break
                order.append((t.id, t.metadata.get("source"), t.priority.name))

            # Первые два — OWNER_DIRECT (CRITICAL, затем LOW)
            assert order[0][0] == "o1"
            assert order[1][0] == "o2"
            # Затем — MARKETPLACE (CRITICAL, затем LOW)
            assert order[2][0] == "m2"
            assert order[3][0] == "m1"
        finally:
            self._cleanup(sched, path)

    def test_empty_queue_returns_none(self):
        sched, path = self._make_sched()
        try:
            assert sched.pop_next_task() is None
        finally:
            self._cleanup(sched, path)
