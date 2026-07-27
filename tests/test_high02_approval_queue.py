"""
Тесты для проверки [HIGH-02]: Approval queue — утечка памяти.

Проблема: _approval_queue.append() без чистки, нет TTL, нет персистентности.
Исправление: cleanup_expired(), clear_approved(), max_queue_size, TTL, JSON persist.
"""

import sys
import os
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from datetime import datetime, timedelta
from space1.compliance.security import AIOSAccessManager
from space1.compliance.core import Action


class TestApprovalQueueMemoryLeak:
    """Проверка [HIGH-02]: Approval queue не утекает, имеет TTL и персистентность."""

    def test_max_queue_size_enforced(self):
        """Очередь не растёт больше max_queue_size (FIFO eviction)."""
        mgr = AIOSAccessManager(max_queue_size=5)

        for i in range(10):
            action = Action(name=f"action_{i}", resource_cost=200.0)
            mgr.requires_human_approval(action)

        # Проверяем что cleanup был вызван
        assert len(mgr._approval_queue) <= 5, f"Queue size: {len(mgr._approval_queue)}, expected <= 5"
        # Самые старые удалены, остались новые
        ids = [r["action_id"] for r in mgr._approval_queue]
        assert "action_0" not in ids
        assert "action_9" in ids

    def test_ttl_expires_pending(self):
        """PENDING запросы истекают по TTL."""
        mgr = AIOSAccessManager(pending_ttl_hours=0.0001)  # 0.36 секунды

        action = Action(name="old_action", resource_cost=200.0)
        mgr.requires_human_approval(action)
        assert len(mgr._approval_queue) == 1

        # Ждём истечения TTL
        time.sleep(0.5)

        # Добавляем новый — триггерит cleanup
        action2 = Action(name="new_action", resource_cost=200.0)
        mgr.requires_human_approval(action2)

        # Старый должен быть удалён
        assert len(mgr._approval_queue) == 1, f"Queue: {[r['action_id'] for r in mgr._approval_queue]}"
        assert mgr._approval_queue[0]["action_id"] == "new_action"

    def test_clear_approved_removes_non_pending(self):
        """clear_approved() удаляет APPROVED и REJECTED, оставляет PENDING."""
        mgr = AIOSAccessManager()

        # Создаём 3 запроса
        for i in range(3):
            action = Action(name=f"action_{i}", resource_cost=200.0)
            mgr.requires_human_approval(action)

        # Одобряем 2
        mgr.request_human_approval("action_0", approved=True)
        mgr.request_human_approval("action_1", approved=False)
        # action_2 остаётся PENDING

        assert len(mgr._approval_queue) == 3

        removed = mgr.clear_approved()
        assert removed == 2
        assert len(mgr._approval_queue) == 1
        assert mgr._approval_queue[0]["action_id"] == "action_2"
        assert mgr._approval_queue[0]["status"] == "PENDING"

    def test_persistence_save_and_load(self):
        """Состояние сохраняется и загружается из JSON."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            persist_path = f.name

        try:
            # Создаём и заполняем
            mgr1 = AIOSAccessManager(persist_path=persist_path)
            action = Action(name="persisted_action", resource_cost=200.0)
            mgr1.requires_human_approval(action)
            mgr1.request_human_approval("persisted_action", approved=True)

            # Создаём новый менеджер с тем же файлом
            mgr2 = AIOSAccessManager(persist_path=persist_path)
            assert len(mgr2._approval_queue) == 1
            assert mgr2._approval_queue[0]["action_id"] == "persisted_action"
            assert mgr2._human_approvals.get("persisted_action") == True

        finally:
            os.unlink(persist_path)

    def test_persistence_corrupt_file_ignored(self):
        """При повреждённом JSON файл игнорируется, начинаем с чистого листа."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode='w') as f:
            f.write("not json {{[")
            persist_path = f.name

        try:
            mgr = AIOSAccessManager(persist_path=persist_path)
            assert mgr._approval_queue == []
            assert mgr._human_approvals == {}
        finally:
            os.unlink(persist_path)

    def test_list_pending_only_returns_pending(self):
        """list_pending_approvals() возвращает только PENDING."""
        mgr = AIOSAccessManager()

        action1 = Action(name="pending_1", resource_cost=200.0)
        action2 = Action(name="approved_1", resource_cost=200.0)
        mgr.requires_human_approval(action1)
        mgr.requires_human_approval(action2)
        mgr.request_human_approval("approved_1", approved=True)

        pending = mgr.list_pending_approvals()
        assert len(pending) == 1
        assert pending[0]["action_id"] == "pending_1"

    def test_audit_log_persisted(self):
        """Audit log сохраняется вместе с очередью."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            persist_path = f.name

        try:
            mgr1 = AIOSAccessManager(persist_path=persist_path)
            action = Action(name="audit_test", resource_cost=200.0)
            mgr1.requires_human_approval(action)
            mgr1.request_human_approval("audit_test", approved=True, reason="test_reason")

            mgr2 = AIOSAccessManager(persist_path=persist_path)
            logs = mgr2.list_security_audit_log()
            assert len(logs) >= 1
            assert logs[-1]["action_id"] == "audit_test"
            assert logs[-1]["reason"] == "test_reason"
        finally:
            os.unlink(persist_path)
