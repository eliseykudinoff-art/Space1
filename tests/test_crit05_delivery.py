"""Тесты [CRIT-05]: Delivery module — отправка результатов клиенту."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from datetime import datetime

from space1.delivery.core import (
    DeliveryAdapter, MockDeliveryAdapter, FileDeliveryAdapter,
    DeliveryManager, DeliveryResult, DeliveryStatus
)


class TestCrit05DeliveryModule:
    """Модуль delivery должен отправлять результаты клиенту."""

    def test_mock_adapter_sends_successfully(self):
        """MockDeliveryAdapter должен успешно "отправлять" результаты."""
        adapter = MockDeliveryAdapter(name="test_mock", success_rate=1.0)
        result = adapter.send(
            task_id="task-001",
            result={"code": "print('hello')"},
            recipient="client_123"
        )
        assert result.success is True
        assert result.status == DeliveryStatus.DELIVERED
        assert "client_123" in result.message

    def test_mock_adapter_records_history(self):
        """Адаптер должен записывать историю доставок."""
        adapter = MockDeliveryAdapter(success_rate=1.0)
        adapter.send("task-1", "result1", "client_a")
        adapter.send("task-2", "result2", "client_b")

        history = adapter.get_history()
        assert len(history) == 2
        assert all(h.success for h in history)

    def test_mock_adapter_failure_simulation(self):
        """Mock с success_rate=0 должен всегда возвращать FAILED."""
        adapter = MockDeliveryAdapter(success_rate=0.0)
        result = adapter.send("task-1", "result", "client")
        assert result.success is False
        assert result.status == DeliveryStatus.FAILED

    def test_file_adapter_saves_to_disk(self, tmp_path):
        """FileDeliveryAdapter должен сохранять результаты в JSON."""
        output_dir = str(tmp_path / "deliveries")
        adapter = FileDeliveryAdapter(output_dir=output_dir)

        result = adapter.send(
            task_id="task-001",
            result={"output": "success"},
            recipient="client_123"
        )

        assert result.success is True
        assert result.status == DeliveryStatus.DELIVERED
        assert os.path.exists(output_dir)
        assert len(os.listdir(output_dir)) == 1

    def test_delivery_manager_routing(self):
        """DeliveryManager должен маршрутизировать на нужный адаптер."""
        mgr = DeliveryManager()
        mock = MockDeliveryAdapter(name="mock", success_rate=1.0)
        mgr.register(mock, default=True)

        result = mgr.send("task-1", "result", "client_a")
        assert result.success is True

        # Проверим, что использовался mock
        assert len(mock.get_history()) == 1

    def test_delivery_manager_fallback_to_default(self):
        """Если adapter_name не указан — использовать default."""
        mgr = DeliveryManager()
        mock = MockDeliveryAdapter(name="mock")
        mgr.register(mock, default=True)

        result = mgr.send("task-1", "result", "client")
        assert result.success is True

    def test_delivery_manager_no_adapter_error(self):
        """Без зарегистрированных адаптеров — возвращать ошибку."""
        mgr = DeliveryManager()
        result = mgr.send("task-1", "result", "client")
        assert result.success is False
        assert "No delivery adapter" in result.message

    def test_delivery_manager_health_check(self):
        """Health check должен проверять все адаптеры."""
        mgr = DeliveryManager()
        mock = MockDeliveryAdapter(name="mock")
        mgr.register(mock)

        health = mgr.health_check()
        assert health == {"mock": True}

    def test_abstract_adapter_cannot_instantiate(self):
        """DeliveryAdapter (ABC) нельзя инстанцировать."""
        with pytest.raises(TypeError):
            DeliveryAdapter(name="test")

    def test_delivery_status_enum_values(self):
        """DeliveryStatus должен иметь правильные значения."""
        assert DeliveryStatus.PENDING.value == "pending"
        assert DeliveryStatus.SENT.value == "sent"
        assert DeliveryStatus.DELIVERED.value == "delivered"
        assert DeliveryStatus.FAILED.value == "failed"
        assert DeliveryStatus.RETRYING.value == "retrying"
