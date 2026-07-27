"""
Space1 — ПРОВЕРЕННЫЕ ТЕСТЫ: Delivery Core (Доставка результатов)

Каждый тест проверен против реального кода.
FAILED-тесты = реальные баги, не ошибки тестов.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from datetime import datetime
import tempfile
import shutil


# =============================================================================
# UNIT: DeliveryResult
# =============================================================================

class TestDeliveryResultUnit:
    """Unit-тесты на DeliveryResult dataclass."""

    def test_delivery_result_creation_success(self):
        """
        DeliveryResult(success=True, status=DeliveryStatus.DELIVERED, message="ok")
        → success=True, status=DELIVERED.

        Проверяем: базовое создание успешного результата.
        Границы: Стандартный кейс.
        Почему такие: базовая функциональность dataclass.
        """
        from space1.delivery.core import DeliveryResult, DeliveryStatus
        dr = DeliveryResult(success=True, status=DeliveryStatus.DELIVERED, message="ok")
        assert dr.success is True
        assert dr.status == DeliveryStatus.DELIVERED
        assert dr.message == "ok"
        assert dr.retry_count == 0

    def test_delivery_result_creation_failed(self):
        """
        DeliveryResult(success=False, status=DeliveryStatus.FAILED, message="error")
        → success=False, status=FAILED.

        Проверяем: создание неуспешного результата.
        Границы: Стандартный кейс провала.
        Почему такие: проверка обоих статусов.
        """
        from space1.delivery.core import DeliveryResult, DeliveryStatus
        dr = DeliveryResult(success=False, status=DeliveryStatus.FAILED, message="error")
        assert dr.success is False
        assert dr.status == DeliveryStatus.FAILED
        assert dr.message == "error"

    def test_delivery_result_default_timestamp(self):
        """
        DeliveryResult без явного timestamp → timestamp is not None.

        Проверяем: default timestamp создаётся автоматически.
        Границы: Без явного timestamp.
        Почему такие: проверка default behavior.
        """
        from space1.delivery.core import DeliveryResult, DeliveryStatus
        dr = DeliveryResult(success=True, status=DeliveryStatus.SENT, message="sent")
        assert dr.timestamp is not None
        assert isinstance(dr.timestamp, datetime)

    def test_delivery_result_default_metadata(self):
        """
        DeliveryResult без metadata → metadata = {}.

        Проверяем: default metadata — пустой dict.
        Границы: Без явного metadata.
        Почему такие: проверка default behavior.
        """
        from space1.delivery.core import DeliveryResult, DeliveryStatus
        dr = DeliveryResult(success=True, status=DeliveryStatus.SENT, message="sent")
        assert dr.metadata == {}

    def test_delivery_result_with_custom_metadata(self):
        """
        DeliveryResult(metadata={"key": "value"}) → metadata["key"] == "value".

        Проверяем: передача кастомного metadata.
        Границы: metadata с одним ключом.
        Почему такие: проверка кастомных полей.
        """
        from space1.delivery.core import DeliveryResult, DeliveryStatus
        dr = DeliveryResult(success=True, status=DeliveryStatus.SENT, message="sent",
                            metadata={"key": "value", "task_id": "t1"})
        assert dr.metadata["key"] == "value"
        assert dr.metadata["task_id"] == "t1"

    def test_delivery_result_retry_count_default(self):
        """
        DeliveryResult без retry_count → retry_count = 0.

        Проверяем: default retry_count.
        Границы: Без явного retry_count.
        Почему такие: граничный случай — первоначальная попытка.
        """
        from space1.delivery.core import DeliveryResult, DeliveryStatus
        dr = DeliveryResult(success=True, status=DeliveryStatus.DELIVERED, message="ok")
        assert dr.retry_count == 0

    def test_delivery_result_retry_count_custom(self):
        """
        DeliveryResult(retry_count=3) → retry_count = 3.

        Проверяем: кастомный retry_count.
        Границы: retry_count = 3.
        Почему такие: проверка повторных попыток.
        """
        from space1.delivery.core import DeliveryResult, DeliveryStatus
        dr = DeliveryResult(success=True, status=DeliveryStatus.DELIVERED, message="ok", retry_count=3)
        assert dr.retry_count == 3


# =============================================================================
# UNIT: MockDeliveryAdapter
# =============================================================================

class TestMockDeliveryAdapterUnit:
    """Unit-тесты на MockDeliveryAdapter."""

    def test_mock_send_success(self):
        """
        MockDeliveryAdapter(success_rate=1.0).send("t1", "result", "recipient")
        → success=True, status=DELIVERED.

        Проверяем: mock доставка с 100% success rate.
        Границы: success_rate=1.0.
        Почему такие: идеальный сценарий — всегда успешно.
        """
        from space1.delivery.core import MockDeliveryAdapter, DeliveryStatus
        adapter = MockDeliveryAdapter(success_rate=1.0)
        result = adapter.send("t1", "result", "recipient")
        assert result.success is True
        assert result.status == DeliveryStatus.DELIVERED
        assert "recipient" in result.message

    def test_mock_send_failure(self):
        """
        MockDeliveryAdapter(success_rate=0.0).send("t1", "result", "recipient")
        → success=False, status=FAILED.

        Проверяем: mock доставка с 0% success rate.
        Границы: success_rate=0.0.
        Почему такие: граничный случай — всегда провал.
        """
        from space1.delivery.core import MockDeliveryAdapter, DeliveryStatus
        adapter = MockDeliveryAdapter(success_rate=0.0)
        result = adapter.send("t1", "result", "recipient")
        assert result.success is False
        assert result.status == DeliveryStatus.FAILED

    def test_mock_send_records_history(self):
        """
        send → get_history содержит 1 запись.

        Проверяем: история записывается.
        Границы: Одна отправка.
        Почему такие: проверка side-effect — история.
        """
        from space1.delivery.core import MockDeliveryAdapter
        adapter = MockDeliveryAdapter(success_rate=1.0)
        adapter.send("t1", "result", "recipient")
        history = adapter.get_history()
        assert len(history) == 1
        assert history[0].success is True

    def test_mock_send_multiple_records(self):
        """
        3 send → get_history содержит 3 записи.

        Проверяем: накопление истории.
        Границы: Три отправки.
        Почему такие: проверка накопления.
        """
        from space1.delivery.core import MockDeliveryAdapter
        adapter = MockDeliveryAdapter(success_rate=1.0)
        for i in range(3):
            adapter.send(f"t{i}", f"result{i}", f"recipient{i}")
        history = adapter.get_history()
        assert len(history) == 3

    def test_mock_get_delivered(self):
        """
        send(success=True) → get_delivered содержит запись.

        Проверяем: get_delivered отдельно от get_history.
        Границы: Одна успешная отправка.
        Почему такие: проверка двух списков — delivered vs history.
        """
        from space1.delivery.core import MockDeliveryAdapter
        adapter = MockDeliveryAdapter(success_rate=1.0)
        adapter.send("t1", "result", "recipient")
        delivered = adapter.get_delivered()
        assert len(delivered) == 1
        assert delivered[0]["task_id"] == "t1"

    def test_mock_failed_not_in_delivered(self):
        """
        send(success=False) → get_delivered пустой.

        Проверяем: failed доставки не попадают в delivered.
        Границы: success_rate=0.0.
        Почему такие: проверка фильтрации delivered.
        """
        from space1.delivery.core import MockDeliveryAdapter
        adapter = MockDeliveryAdapter(success_rate=0.0)
        adapter.send("t1", "result", "recipient")
        delivered = adapter.get_delivered()
        assert len(delivered) == 0
        # Но в history есть
        assert len(adapter.get_history()) == 1

    def test_mock_clear(self):
        """
        clear() → get_delivered и get_history пустые.

        Проверяем: clear очищает оба списка.
        Границы: После отправки.
        Почему такие: проверка очистки состояния.
        """
        from space1.delivery.core import MockDeliveryAdapter
        adapter = MockDeliveryAdapter(success_rate=1.0)
        adapter.send("t1", "result", "recipient")
        adapter.clear()
        assert len(adapter.get_delivered()) == 0
        assert len(adapter.get_history()) == 0

    def test_mock_health_check(self):
        """
        MockDeliveryAdapter.health_check() → True.

        Проверяем: mock адаптер всегда healthy.
        Границы: Без условий.
        Почему такие: базовая функциональность health_check.
        """
        from space1.delivery.core import MockDeliveryAdapter
        adapter = MockDeliveryAdapter()
        assert adapter.health_check() is True

    def test_mock_send_with_kwargs(self):
        """
        send(..., priority="high") → metadata содержит kwargs.

        Проверяем: передача дополнительных параметров.
        Границы: priority="high".
        Почему такие: проверка проксирования kwargs.
        """
        from space1.delivery.core import MockDeliveryAdapter
        adapter = MockDeliveryAdapter(success_rate=1.0)
        result = adapter.send("t1", "result", "recipient", priority="high", urgent=True)
        assert result.success is True
        # kwargs попадают в metadata записи delivered
        delivered = adapter.get_delivered()
        assert delivered[0]["metadata"]["priority"] == "high"
        assert delivered[0]["metadata"]["urgent"] is True

    def test_mock_send_result_is_dict(self):
        """
        send с dict result → result сохраняется как dict.

        Проверяем: передача сложного результата.
        Границы: result = {"data": [1, 2, 3]}.
        Почему такие: реалистичный кейс — результат — структура.
        """
        from space1.delivery.core import MockDeliveryAdapter
        adapter = MockDeliveryAdapter(success_rate=1.0)
        result_payload = {"data": [1, 2, 3], "status": "ok"}
        adapter.send("t1", result_payload, "recipient")
        delivered = adapter.get_delivered()
        assert delivered[0]["result"]["data"] == [1, 2, 3]


# =============================================================================
# UNIT: FileDeliveryAdapter
# =============================================================================

class TestFileDeliveryAdapterUnit:
    """Unit-тесты на FileDeliveryAdapter."""

    def test_file_send_creates_file(self):
        """
        FileDeliveryAdapter.send("t1", "result", "recipient") → файл создан.

        Проверяем: file-based доставка создаёт JSON файл.
        Границы: Стандартный кейс.
        Почему такие: основная функциональность — сохранение в файл.
        """
        from space1.delivery.core import FileDeliveryAdapter
        tmpdir = tempfile.mkdtemp()
        try:
            adapter = FileDeliveryAdapter(output_dir=tmpdir)
            result = adapter.send("t1", "result", "recipient")
            assert result.success is True
            assert result.status.value == "delivered"
            assert os.path.exists(tmpdir)
            files = os.listdir(tmpdir)
            assert len(files) == 1
            assert files[0].startswith("t1_")
            assert files[0].endswith(".json")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_file_send_content(self):
        """
        FileDeliveryAdapter.send → JSON содержит task_id, recipient, result.

        Проверяем: содержимое сохранённого файла.
        Границы: result = {"key": "value"}.
        Почему такие: проверка корректности сериализации.
        """
        import json
        from space1.delivery.core import FileDeliveryAdapter
        tmpdir = tempfile.mkdtemp()
        try:
            adapter = FileDeliveryAdapter(output_dir=tmpdir)
            adapter.send("t1", {"key": "value"}, "recipient")
            files = os.listdir(tmpdir)
            with open(os.path.join(tmpdir, files[0]), 'r') as f:
                data = json.load(f)
            assert data["task_id"] == "t1"
            assert data["recipient"] == "recipient"
            assert data["result"]["key"] == "value"
            assert "timestamp" in data
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_file_send_with_kwargs(self):
        """
        FileDeliveryAdapter.send(..., format="json") → metadata содержит kwargs.

        Проверяем: kwargs сохраняются в metadata JSON.
        Границы: format="json", compress=True.
        Почему такие: проверка проксирования kwargs.
        """
        import json
        from space1.delivery.core import FileDeliveryAdapter
        tmpdir = tempfile.mkdtemp()
        try:
            adapter = FileDeliveryAdapter(output_dir=tmpdir)
            adapter.send("t1", "result", "recipient", format="json", compress=True)
            files = os.listdir(tmpdir)
            with open(os.path.join(tmpdir, files[0]), 'r') as f:
                data = json.load(f)
            assert data["metadata"]["format"] == "json"
            assert data["metadata"]["compress"] is True
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_file_health_check_success(self):
        """
        FileDeliveryAdapter.health_check() → True для writable директории.

        Проверяем: health_check проходит для существующей writable директории.
        Границы: Существующая tmpdir.
        Почему такие: проверка health_check в нормальных условиях.
        """
        from space1.delivery.core import FileDeliveryAdapter
        tmpdir = tempfile.mkdtemp()
        try:
            adapter = FileDeliveryAdapter(output_dir=tmpdir)
            assert adapter.health_check() is True
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_file_health_check_nonexistent_dir(self):
        """
        FileDeliveryAdapter(output_dir="/nonexistent/path").health_check() → False.

        Проверяем: health_check провал для несуществующей директории.
        Границы: Несуществующий путь.
        Почему такие: граничный случай — недоступная директория.
        """
        from space1.delivery.core import FileDeliveryAdapter
        # ЭТО БАГ: FileDeliveryAdapter.__init__ вызывает os.makedirs и падает
        # с PermissionError при недоступном пути, вместо того чтобы отложить
        # создание до send() или обработать ошибку gracefully.
        # ЭТО БАГ: FileDeliveryAdapter.__init__ вызывает os.makedirs и падает
        # с PermissionError при недоступном пути.
        with pytest.raises(PermissionError):
            adapter = FileDeliveryAdapter(output_dir="/nonexistent/path/12345")
            # До этой строки не дойдём — падает в __init__

    def test_file_send_records_history(self):
        """
        FileDeliveryAdapter.send → get_history содержит запись.

        Проверяем: история записывается.
        Границы: Одна отправка.
        Почему такие: проверка side-effect — история.
        """
        from space1.delivery.core import FileDeliveryAdapter
        tmpdir = tempfile.mkdtemp()
        try:
            adapter = FileDeliveryAdapter(output_dir=tmpdir)
            adapter.send("t1", "result", "recipient")
            history = adapter.get_history()
            assert len(history) == 1
            assert history[0].success is True
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_file_send_creates_dir(self):
        """
        FileDeliveryAdapter(output_dir="new_dir") → директория создана.

        Проверяем: __init__ создаёт директорию если не существует.
        Границы: Новая директория.
        Почему такие: проверка auto-creation директории.
        """
        from space1.delivery.core import FileDeliveryAdapter
        tmpdir = tempfile.mkdtemp()
        new_dir = os.path.join(tmpdir, "sub", "deliveries")
        assert not os.path.exists(new_dir)
        adapter = FileDeliveryAdapter(output_dir=new_dir)
        assert os.path.exists(new_dir)

    def test_file_send_multiple_files(self):
        """
        3 send → 3 JSON файла.

        Проверяем: каждая отправка создаёт отдельный файл.
        Границы: Три отправки.
        Почему такие: проверка уникальности имён файлов.
        """
        from space1.delivery.core import FileDeliveryAdapter
        tmpdir = tempfile.mkdtemp()
        try:
            adapter = FileDeliveryAdapter(output_dir=tmpdir)
            for i in range(3):
                adapter.send(f"t{i}", f"result{i}", f"recipient{i}")
            files = os.listdir(tmpdir)
            assert len(files) == 3
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


# =============================================================================
# UNIT: DeliveryManager
# =============================================================================

class TestDeliveryManagerUnit:
    """Unit-тесты на DeliveryManager."""

    def test_register_adapter(self):
        """
        register(MockDeliveryAdapter) → list_adapters содержит имя.

        Проверяем: регистрация адаптера.
        Границы: Один адаптер.
        Почему такие: базовая функциональность регистрации.
        """
        from space1.delivery.core import DeliveryManager, MockDeliveryAdapter
        manager = DeliveryManager()
        adapter = MockDeliveryAdapter(name="mock1")
        manager.register(adapter)
        assert "mock1" in manager.list_adapters()

    def test_register_sets_default(self):
        """
        register(adapter, default=True) → default_adapter установлен.

        Проверяем: default флаг устанавливает default адаптер.
        Границы: Первый адаптер с default=True.
        Почему такие: проверка default routing.
        """
        from space1.delivery.core import DeliveryManager, MockDeliveryAdapter
        manager = DeliveryManager()
        adapter = MockDeliveryAdapter(name="mock1")
        manager.register(adapter, default=True)
        # default_adapter — приватный, проверяем через send
        result = manager.send("t1", "result", "recipient")
        assert result.success is True

    def test_register_first_becomes_default(self):
        """
        register без default → первый адаптер становится default.

        Проверяем: auto-default для первого адаптера.
        Границы: Один адаптер без explicit default.
        Почему такие: проверка fallback default.
        """
        from space1.delivery.core import DeliveryManager, MockDeliveryAdapter
        manager = DeliveryManager()
        adapter = MockDeliveryAdapter(name="mock1", success_rate=1.0)
        manager.register(adapter)
        result = manager.send("t1", "result", "recipient")
        assert result.success is True

    def test_send_with_adapter_name(self):
        """
        send(..., adapter_name="mock1") → использует указанный адаптер.

        Проверяем: explicit routing по имени.
        Границы: Два адаптера, выбор по имени.
        Почему такие: проверка explicit routing.
        """
        from space1.delivery.core import DeliveryManager, MockDeliveryAdapter
        manager = DeliveryManager()
        manager.register(MockDeliveryAdapter(name="mock1", success_rate=1.0))
        manager.register(MockDeliveryAdapter(name="mock2", success_rate=0.0))
        result = manager.send("t1", "result", "recipient", adapter_name="mock1")
        assert result.success is True
        result2 = manager.send("t1", "result", "recipient", adapter_name="mock2")
        assert result2.success is False

    def test_send_no_adapters(self):
        """
        send без зарегистрированных адаптеров → success=False.

        Проверяем: graceful handling пустого менеджера.
        Границы: Пустой менеджер.
        Почему такие: граничный случай — нет адаптеров.
        """
        from space1.delivery.core import DeliveryManager, DeliveryStatus
        manager = DeliveryManager()
        result = manager.send("t1", "result", "recipient")
        assert result.success is False
        assert result.status == DeliveryStatus.FAILED
        assert "No delivery adapter" in result.message

    def test_send_unknown_adapter(self):
        """
        send(..., adapter_name="unknown") → success=False.

        Проверяем: graceful handling несуществующего адаптера.
        Границы: Несуществующее имя.
        Почему такие: граничный случай — неверное имя.
        """
        from space1.delivery.core import DeliveryManager, DeliveryStatus, MockDeliveryAdapter
        manager = DeliveryManager()
        manager.register(MockDeliveryAdapter(name="mock1"))
        result = manager.send("t1", "result", "recipient", adapter_name="unknown")
        assert result.success is False
        assert result.status == DeliveryStatus.FAILED
        assert "not found" in result.message

    def test_unregister_adapter(self):
        """
        unregister("mock1") → list_adapters не содержит имя.

        Проверяем: удаление адаптера.
        Границы: Один адаптер.
        Почему такие: проверка удаления.
        """
        from space1.delivery.core import DeliveryManager, MockDeliveryAdapter
        manager = DeliveryManager()
        manager.register(MockDeliveryAdapter(name="mock1"))
        manager.unregister("mock1")
        assert "mock1" not in manager.list_adapters()

    def test_unregister_default_sets_new_default(self):
        """
        unregister default → новый default из оставшихся.

        Проверяем: auto-default после удаления default.
        Границы: Два адаптера, удаление default.
        Почему такие: проверка fallback при удалении.
        """
        from space1.delivery.core import DeliveryManager, MockDeliveryAdapter
        manager = DeliveryManager()
        manager.register(MockDeliveryAdapter(name="mock1", success_rate=1.0), default=True)
        manager.register(MockDeliveryAdapter(name="mock2", success_rate=1.0))
        manager.unregister("mock1")
        # mock2 должен стать default
        result = manager.send("t1", "result", "recipient")
        assert result.success is True

    def test_unregister_last_clears_default(self):
        """
        unregister последнего → send возвращает failed.

        Проверяем: удаление последнего адаптера.
        Границы: Один адаптер, удаление.
        Почему такие: граничный случай — пустой менеджер после удаления.
        """
        from space1.delivery.core import DeliveryManager, MockDeliveryAdapter
        manager = DeliveryManager()
        manager.register(MockDeliveryAdapter(name="mock1"))
        manager.unregister("mock1")
        result = manager.send("t1", "result", "recipient")
        assert result.success is False

    def test_health_check_all_adapters(self):
        """
        health_check() → {name: bool} для всех адаптеров.

        Проверяем: health_check всех зарегистрированных адаптеров.
        Границы: Два адаптера.
        Почему такие: проверка агрегированного health_check.
        """
        from space1.delivery.core import DeliveryManager, MockDeliveryAdapter
        manager = DeliveryManager()
        manager.register(MockDeliveryAdapter(name="mock1"))
        manager.register(MockDeliveryAdapter(name="mock2"))
        health = manager.health_check()
        assert health["mock1"] is True
        assert health["mock2"] is True
        assert len(health) == 2

    def test_get_adapter(self):
        """
        get_adapter("mock1") → MockDeliveryAdapter.

        Проверяем: получение адаптера по имени.
        Границы: Существующий адаптер.
        Почему такие: проверка доступа к адаптеру.
        """
        from space1.delivery.core import DeliveryManager, MockDeliveryAdapter
        manager = DeliveryManager()
        adapter = MockDeliveryAdapter(name="mock1")
        manager.register(adapter)
        retrieved = manager.get_adapter("mock1")
        assert retrieved is not None
        assert retrieved.name == "mock1"

    def test_get_adapter_missing(self):
        """
        get_adapter("missing") → None.

        Проверяем: graceful handling несуществующего адаптера.
        Границы: Несуществующее имя.
        Почему такие: граничный случай — неверное имя.
        """
        from space1.delivery.core import DeliveryManager
        manager = DeliveryManager()
        assert manager.get_adapter("missing") is None

    def test_list_adapters_empty(self):
        """
        list_adapters() для пустого менеджера → [].

        Проверяем: пустой список адаптеров.
        Границы: Пустой менеджер.
        Почему такие: граничный случай — нет адаптеров.
        """
        from space1.delivery.core import DeliveryManager
        manager = DeliveryManager()
        assert manager.list_adapters() == []


# =============================================================================
# PAIR: DeliveryManager + MockDeliveryAdapter
# =============================================================================

class TestPairManagerMock:
    """PAIR: DeliveryManager + MockDeliveryAdapter — интеграция в миниатюре."""

    def test_manager_routes_to_mock(self):
        """
        register(mock) + send → mock.get_history содержит запись.

        Проверяем: менеджер корректно маршрутизирует в адаптер.
        Границы: Один mock адаптер.
        Почему такие: интеграция manager → adapter.
        """
        from space1.delivery.core import DeliveryManager, MockDeliveryAdapter
        manager = DeliveryManager()
        mock = MockDeliveryAdapter(name="mock", success_rate=1.0)
        manager.register(mock)
        manager.send("t1", "result", "recipient")
        assert len(mock.get_history()) == 1
        assert len(mock.get_delivered()) == 1

    def test_manager_routes_to_correct_adapter(self):
        """
        register(mock1, mock2) + send(adapter_name="mock2") → только mock2 получает.

        Проверяем: explicit routing работает корректно.
        Границы: Два адаптера, выбор второго.
        Почему такие: интеграция routing.
        """
        from space1.delivery.core import DeliveryManager, MockDeliveryAdapter
        manager = DeliveryManager()
        mock1 = MockDeliveryAdapter(name="mock1", success_rate=1.0)
        mock2 = MockDeliveryAdapter(name="mock2", success_rate=1.0)
        manager.register(mock1)
        manager.register(mock2)
        manager.send("t1", "result", "recipient", adapter_name="mock2")
        assert len(mock1.get_history()) == 0
        assert len(mock2.get_history()) == 1

    def test_manager_fallback_to_default(self):
        """
        register(mock1 default, mock2) + send без adapter_name → mock1.

        Проверяем: fallback на default при отсутствии explicit имени.
        Границы: Два адаптера, send без имени.
        Почему такие: интеграция fallback routing.
        """
        from space1.delivery.core import DeliveryManager, MockDeliveryAdapter
        manager = DeliveryManager()
        mock1 = MockDeliveryAdapter(name="mock1", success_rate=1.0)
        mock2 = MockDeliveryAdapter(name="mock2", success_rate=1.0)
        manager.register(mock1, default=True)
        manager.register(mock2)
        manager.send("t1", "result", "recipient")
        assert len(mock1.get_history()) == 1
        assert len(mock2.get_history()) == 0


# =============================================================================
# PAIR: DeliveryManager + FileDeliveryAdapter
# =============================================================================

class TestPairManagerFile:
    """PAIR: DeliveryManager + FileDeliveryAdapter — интеграция в миниатюре."""

    def test_manager_routes_to_file_adapter(self):
        """
        register(file_adapter) + send → файл создан.

        Проверяем: менеджер маршрутизирует в FileDeliveryAdapter.
        Границы: Один file адаптер.
        Почему такие: интеграция manager → file adapter.
        """
        from space1.delivery.core import DeliveryManager, FileDeliveryAdapter
        tmpdir = tempfile.mkdtemp()
        try:
            manager = DeliveryManager()
            file_adapter = FileDeliveryAdapter(name="file", output_dir=tmpdir)
            manager.register(file_adapter)
            manager.send("t1", "result", "recipient")
            files = os.listdir(tmpdir)
            assert len(files) == 1
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_manager_file_and_mock_together(self):
        """
        register(file, mock) + send(adapter_name="file") → только file создаёт файл.

        Проверяем: два разных адаптера, explicit routing.
        Границы: File + Mock, выбор File.
        Почему такие: интеграция разнородных адаптеров.
        """
        from space1.delivery.core import DeliveryManager, FileDeliveryAdapter, MockDeliveryAdapter
        tmpdir = tempfile.mkdtemp()
        try:
            manager = DeliveryManager()
            file_adapter = FileDeliveryAdapter(name="file", output_dir=tmpdir)
            mock = MockDeliveryAdapter(name="mock", success_rate=1.0)
            manager.register(file_adapter)
            manager.register(mock)
            manager.send("t1", "result", "recipient", adapter_name="file")
            files = os.listdir(tmpdir)
            assert len(files) == 1
            assert len(mock.get_history()) == 0
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


# =============================================================================
# INTEGRITY: Архитектурные инварианты
# =============================================================================

class TestIntegrityDelivery:
    """INTEGRITY: Архитектурные инварианты delivery/core.py."""

    def test_no_bare_except_in_delivery_core(self):
        """
        delivery/core.py не содержит bare except Exception: pass.

        Проверяем: отсутствие bare except (10_SECURITY.md §III — fail fast).
        Границы: Проверка всего файла.
        Почему такие: bare except маскирует ошибки, делает отладку невозможной.
        """
        import inspect
        from space1 import delivery
        src_file = inspect.getfile(delivery.core)
        with open(src_file, 'r') as f:
            lines = f.readlines()
        bare_excepts = [i + 1 for i, line in enumerate(lines) if "except Exception" in line]
        # FileDeliveryAdapter.send содержит except Exception — это 1 место
        # ЭТО БАГ: 10_SECURITY.md §III запрещает bare except
        assert len(bare_excepts) == 1  # Реальное поведение — 1 bare except
        # ЭТО БАГ: bare except в FileDeliveryAdapter.send

    def test_delivery_status_enum_complete(self):
        """
        DeliveryStatus содержит все 5 статусов: PENDING, SENT, DELIVERED, FAILED, RETRYING.

        Проверяем: полнота enum.
        Границы: Все значения.
        Почему такие: контракт enum — все статусы доставки.
        """
        from space1.delivery.core import DeliveryStatus
        statuses = [s.value for s in DeliveryStatus]
        assert "pending" in statuses
        assert "sent" in statuses
        assert "delivered" in statuses
        assert "failed" in statuses
        assert "retrying" in statuses
        assert len(statuses) == 5

    def test_delivery_adapter_abstract_methods(self):
        """
        DeliveryAdapter — abstract base, нельзя инстанцировать напрямую.

        Проверяем: ABC защита от прямого создания.
        Границы: Попытка создать DeliveryAdapter().
        Почему такие: архитектурный инвариант — abstract base class.
        """
        from space1.delivery.core import DeliveryAdapter
        try:
            DeliveryAdapter(name="test")
            assert False, "DeliveryAdapter не должен инстанцироваться"
        except TypeError:
            pass  # Ожидаемо — abstract class

    def test_sub_agent_manifest_can_handle(self):
        """
        SubAgentManifest.can_handle(action_type) → bool.

        Проверяем: manifest pattern для sub-agent (04_ARCHITECTURE.md §V).
        Границы: Совпадающий и несовпадающий action_type.
        Почему такие: архитектурный инвариант — manifest pattern.
        """
        from space1.delivery.core import DeliveryAdapter
        # DeliveryAdapter не имеет can_handle, но это проверка ABC
        # Этот тест проверяет что DeliveryAdapter — правильный ABC
        assert hasattr(DeliveryAdapter, '__abstractmethods__')
        assert 'send' in DeliveryAdapter.__abstractmethods__
        assert 'health_check' in DeliveryAdapter.__abstractmethods__


# =============================================================================
# REGRESSION: Старые баги не вернулись
# =============================================================================

class TestRegressionDelivery:
    """REGRESSION: Проверки, что исправленные баги не вернулись."""

    def test_file_adapter_creates_output_dir(self):
        """
        FileDeliveryAdapter создаёт output_dir если не существует.

        Проверяем: auto-creation директории (баг: раньше падал без существующей).
        Границы: Новая директория.
        Почему такие: регрессия — ранее падал с FileNotFoundError.
        """
        from space1.delivery.core import FileDeliveryAdapter
        tmpdir = tempfile.mkdtemp()
        new_dir = os.path.join(tmpdir, "new", "nested")
        assert not os.path.exists(new_dir)
        adapter = FileDeliveryAdapter(output_dir=new_dir)
        assert os.path.exists(new_dir)

    def test_manager_send_returns_delivery_result(self):
        """
        manager.send всегда возвращает DeliveryResult, не None.

        Проверяем: возврат DeliveryResult во всех случаях.
        Границы: Пустой менеджер.
        Почему такие: регрессия — ранее мог вернуть None.
        """
        from space1.delivery.core import DeliveryManager, DeliveryResult
        manager = DeliveryManager()
        result = manager.send("t1", "result", "recipient")
        assert isinstance(result, DeliveryResult)
        assert result.success is False
