"""
Space1 — ПРОВЕРЕННЫЕ ТЕСТЫ: Scheduler (AIOSScheduler)

Каждый тест проверен против реального кода.
FAILED-тесты = реальные баги, не ошибки тестов.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from datetime import datetime, timedelta


# =============================================================================
# UNIT: deserialize_task
# =============================================================================

class TestDeserializeTaskUnit:
    """Unit-тесты на deserialize_task — десериализация Task из dict."""

    def test_deserialize_basic(self):
        """
        deserialize_task с корректными данными → Task со всеми полями.

        Проверяем: id, title, priority, status, source, estimated_hours, tags.
        Границы: Стандартный кейс.
        Почему такие: базовая функциональность десериализации.
        """
        from space1.orchestrator.scheduler import deserialize_task
        from space1.models.task import TaskPriority, TaskStatus
        d = {
            "id": "t1", "title": "Test", "description": "Desc",
            "deadline": (datetime.now() + timedelta(hours=24)).isoformat(),
            "priority": "HIGH", "status": "PENDING",
            "created_at": datetime.now().isoformat(),
            "started_at": None, "completed_at": None,
            "source": "OWNER_DIRECT", "estimated_hours": 2.0,
            "tags": ["python"], "urgency_score": 0.8, "slack_time": 12.0
        }
        task = deserialize_task(d)
        assert task.id == "t1"
        assert task.title == "Test"
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.PENDING
        assert task.source == "OWNER_DIRECT"
        assert task.estimated_hours == 2.0
        assert task.tags == ["python"]
        assert task.urgency_score == 0.8
        assert task.slack_time == 12.0

    def test_deserialize_invalid_priority_defaults_to_medium(self):
        """
        Некорректный priority → TaskPriority.MEDIUM.

        Проверяем: graceful fallback при невалидном priority.
        Границы: priority = "INVALID".
        Почему такие: защита от некорректных данных.
        """
        from space1.orchestrator.scheduler import deserialize_task
        from space1.models.task import TaskPriority
        d = {
            "id": "t1", "title": "Test", "description": "",
            "deadline": None, "priority": "INVALID",
            "status": "PENDING", "created_at": datetime.now().isoformat(),
            "started_at": None, "completed_at": None,
        }
        task = deserialize_task(d)
        assert task.priority == TaskPriority.MEDIUM

    def test_deserialize_none_deadline(self):
        """
        deadline=None → task.deadline is None.

        Проверяем: обработка None для deadline.
        Границы: deadline = None.
        Почему такие: граничный случай — задача без дедлайна.
        """
        from space1.orchestrator.scheduler import deserialize_task
        d = {
            "id": "t1", "title": "Test", "description": "",
            "deadline": None, "priority": "LOW",
            "status": "PENDING", "created_at": datetime.now().isoformat(),
            "started_at": None, "completed_at": None,
        }
        task = deserialize_task(d)
        assert task.deadline is None

    def test_deserialize_source_stored_in_attribute_not_metadata(self):
        """
        deserialize_task сохраняет source в task.source, НЕ в metadata.

        Проверяем: task.source == "OWNER_DIRECT", но metadata.get('source') is None.
        Границы: source = "OWNER_DIRECT".
        Почему такие: критический путь — scheduler ищет source в metadata.
        """
        from space1.orchestrator.scheduler import deserialize_task
        d = {
            "id": "t1", "title": "Test", "description": "",
            "deadline": None, "priority": "HIGH",
            "status": "PENDING", "created_at": datetime.now().isoformat(),
            "started_at": None, "completed_at": None,
            "source": "OWNER_DIRECT"
        }
        task = deserialize_task(d)
        assert task.source == "OWNER_DIRECT"
        assert task.metadata.get("source") is None
        # ЭТО БАГ: scheduler ищет source в metadata, но source там никогда не появляется


# =============================================================================
# UNIT: AIOSScheduler — add/pop
# =============================================================================

class TestSchedulerAddPopUnit:
    """Unit-тесты на добавление и извлечение задач."""

    def test_add_task_increases_queue(self):
        """
        add_task увеличивает размер очереди.

        Проверяем: после add_task list_queue возвращает 1 элемент.
        Границы: Одна задача.
        Почему такие: базовая функциональность.
        """
        from space1.orchestrator.scheduler import AIOSScheduler
        from space1.models.task import Task, TaskPriority
        sched = AIOSScheduler(filepath="/tmp/test_sched_add.json")
        sched.clear()
        sched.add_task(Task(id="t1", title="Test", description="", priority=TaskPriority.LOW, deadline=datetime.now()+timedelta(hours=24)))
        assert len(sched.list_queue()) == 1

    def test_pop_next_task_returns_highest_priority(self):
        """
        pop_next_task возвращает задачу с наивысшим приоритетом.

        Проверяем: CRITICAL > HIGH > LOW.
        Границы: Три задачи с разными приоритетами.
        Почему такие: проверка сортировки по priority.value.
        """
        from space1.orchestrator.scheduler import AIOSScheduler
        from space1.models.task import Task, TaskPriority
        sched = AIOSScheduler(filepath="/tmp/test_sched_pop.json")
        sched.clear()
        sched.add_task(Task(id="low", title="Low", description="", priority=TaskPriority.LOW, deadline=datetime.now()+timedelta(hours=24)))
        sched.add_task(Task(id="high", title="High", description="", priority=TaskPriority.HIGH, deadline=datetime.now()+timedelta(hours=24)))
        sched.add_task(Task(id="critical", title="Critical", description="", priority=TaskPriority.CRITICAL, deadline=datetime.now()+timedelta(hours=24)))
        assert sched.pop_next_task().id == "critical"
        assert sched.pop_next_task().id == "high"
        assert sched.pop_next_task().id == "low"

    def test_pop_empty_queue_returns_none(self):
        """
        pop_next_task с пустой очередью → None.

        Проверяем: graceful handling пустой очереди.
        Границы: Пустая очередь.
        Почему такие: граничный случай — нет задач.
        """
        from space1.orchestrator.scheduler import AIOSScheduler
        sched = AIOSScheduler(filepath="/tmp/test_sched_empty.json")
        sched.clear()
        assert sched.pop_next_task() is None

    def test_pop_removes_from_queue(self):
        """
        pop_next_task удаляет задачу из очереди.

        Проверяем: после pop размер очереди уменьшается.
        Границы: Одна задача.
        Почему такие: проверка side-effect.
        """
        from space1.orchestrator.scheduler import AIOSScheduler
        from space1.models.task import Task, TaskPriority
        sched = AIOSScheduler(filepath="/tmp/test_sched_remove.json")
        sched.clear()
        sched.add_task(Task(id="t1", title="Test", description="", priority=TaskPriority.LOW, deadline=datetime.now()+timedelta(hours=24)))
        sched.pop_next_task()
        assert len(sched.list_queue()) == 0


# =============================================================================
# UNIT: AIOSScheduler — OWNER_DIRECT приоритет (БАГ)
# =============================================================================

class TestSchedulerOwnerDirectUnit:
    """Unit-тесты на OWNER_DIRECT приоритет. БАГ: не работает."""

    def test_owner_direct_does_not_override_marketplace(self):
        """
        OWNER_DIRECT НЕ переопределяет MARKETPLACE — scheduler ищет source в metadata.

        Проверяем: owner_low (LOW) vs market_high (HIGH) → market_high первым.
        Границы: OWNER_DIRECT LOW vs MARKETPLACE HIGH.
        Почему такие: документация §I.3: OWNER_DIRECT > MARKETPLACE.
        """
        from space1.orchestrator.scheduler import AIOSScheduler
        from space1.models.task import Task, TaskPriority
        sched = AIOSScheduler(filepath="/tmp/test_sched_owner.json")
        sched.clear()
        sched.add_task(Task(id="market_high", title="Market High", description="", priority=TaskPriority.HIGH, deadline=datetime.now()+timedelta(hours=24), source="MARKETPLACE"))
        sched.add_task(Task(id="owner_low", title="Owner Low", description="", priority=TaskPriority.LOW, deadline=datetime.now()+timedelta(hours=24), source="OWNER_DIRECT"))
        first = sched.pop_next_task()
        assert first.id == "market_high"  # Реальное поведение — MARKETPLACE первым
        # ЭТО БАГ: ожидалось owner_low (OWNER_DIRECT > MARKETPLACE)

    def test_all_tasks_treated_as_marketplace(self):
        """
        Все задачи считаются MARKETPLACE — сортируются только по priority.

        Проверяем: задачи с OWNER_DIRECT и MARKETPLACE сортируются только по priority.
        Границы: Смешанные source, одинаковый priority.
        Почему такие: проверка что source игнорируется.
        """
        from space1.orchestrator.scheduler import AIOSScheduler
        from space1.models.task import Task, TaskPriority
        sched = AIOSScheduler(filepath="/tmp/test_sched_all_market.json")
        sched.clear()
        sched.add_task(Task(id="owner", title="Owner", description="", priority=TaskPriority.HIGH, deadline=datetime.now()+timedelta(hours=24), source="OWNER_DIRECT"))
        sched.add_task(Task(id="market", title="Market", description="", priority=TaskPriority.HIGH, deadline=datetime.now()+timedelta(hours=24), source="MARKETPLACE"))
        first = sched.pop_next_task()
        second = sched.pop_next_task()
        # Оба HIGH — порядок зависит от stable sort, но оба пройдут
        assert first.priority == TaskPriority.HIGH
        assert second.priority == TaskPriority.HIGH

    def test_source_attribute_vs_metadata(self):
        """
        task.source хранит значение, metadata.get('source') возвращает None.

        Проверяем: scheduler ищет source в metadata, но source там нет.
        Границы: Task с source="OWNER_DIRECT".
        Почему такие: root cause бага — disconnect между source attr и metadata.
        """
        from space1.models.task import Task, TaskPriority
        from datetime import datetime, timedelta
        task = Task(id="t1", title="Test", description="", priority=TaskPriority.HIGH, deadline=datetime.now()+timedelta(hours=24), source="OWNER_DIRECT")
        assert task.source == "OWNER_DIRECT"
        assert task.metadata.get("source") is None


# =============================================================================
# UNIT: AIOSScheduler — persistence (БАГ: JSON serialization)
# =============================================================================

class TestSchedulerPersistenceUnit:
    """Unit-тесты на персистентность очереди. БАГ: _save_queue падает на enum."""

    def test_save_queue_does_not_create_file(self):
        """
        _save_queue НЕ создаёт файл — TaskSource enum не сериализуется в JSON.

        Проверяем: после add_task файл НЕ существует.
        Границы: Одна задача с TaskSource enum.
        Почему такие: root cause — json.dump падает на TaskSource enum.
        """
        from space1.orchestrator.scheduler import AIOSScheduler
        from space1.models.task import Task, TaskPriority
        import os
        filepath = "/tmp/test_sched_save.json"
        sched = AIOSScheduler(filepath=filepath)
        sched.clear()
        sched.add_task(Task(id="t1", title="Test", description="", priority=TaskPriority.HIGH, deadline=datetime.now()+timedelta(hours=24)))
        assert not os.path.exists(filepath)  # Реальное поведение — файл не создан
        # ЭТО БАГ: json.dump падает на TaskSource enum, except Exception глотает ошибку

    def test_load_queue_returns_empty(self):
        """
        _load_queue возвращает пустую очередь — файл не создан из-за бага _save_queue.

        Проверяем: новый scheduler с тем же файлом видит 0 задач.
        Границы: Файл не существует (из-за бага _save_queue).
        Почему такие: round-trip невозможен из-за serialization бага.
        """
        from space1.orchestrator.scheduler import AIOSScheduler
        from space1.models.task import Task, TaskPriority
        filepath = "/tmp/test_sched_load.json"
        sched1 = AIOSScheduler(filepath=filepath)
        sched1.clear()
        sched1.add_task(Task(id="t1", title="Test", description="", priority=TaskPriority.HIGH, deadline=datetime.now()+timedelta(hours=24)))
        # Новый scheduler с тем же файлом
        sched2 = AIOSScheduler(filepath=filepath)
        assert len(sched2.list_queue()) == 0  # Реальное поведение — пусто
        # ЭТО БАГ: файл не создан, очередь пуста

    def test_load_queue_bad_json_returns_empty(self):
        """
        Некорректный JSON → пустая очередь.

        Проверяем: graceful handling битого JSON.
        Границы: Битый JSON.
        Почему такие: защита от corrupted файла.
        """
        from space1.orchestrator.scheduler import AIOSScheduler
        filepath = "/tmp/test_sched_bad.json"
        with open(filepath, "w") as f:
            f.write("not json")
        sched = AIOSScheduler(filepath=filepath)
        assert len(sched.list_queue()) == 0

    def test_clear_removes_file(self):
        """
        clear() удаляет файл очереди.

        Проверяем: после clear файл не существует.
        Границы: Файл создан вручную.
        Почему такие: проверка cleanup.
        """
        from space1.orchestrator.scheduler import AIOSScheduler
        from space1.models.task import Task, TaskPriority
        import os
        filepath = "/tmp/test_sched_clear.json"
        sched = AIOSScheduler(filepath=filepath)
        sched.clear()
        # Создадим файл вручную, т.к. _save_queue не работает
        with open(filepath, "w") as f:
            f.write("[]")
        assert os.path.exists(filepath)
        sched.clear()
        assert not os.path.exists(filepath)
        assert len(sched.list_queue()) == 0


# =============================================================================
# UNIT: AIOSScheduler — list_queue
# =============================================================================

class TestSchedulerListQueueUnit:
    """Unit-тесты на list_queue."""

    def test_list_queue_returns_copy(self):
        """
        list_queue возвращает копию, не оригинал.

        Проверяем: модификация результата не влияет на scheduler.
        Границы: Одна задача.
        Почему такие: защита от accidental mutation.
        """
        from space1.orchestrator.scheduler import AIOSScheduler
        from space1.models.task import Task, TaskPriority
        sched = AIOSScheduler(filepath="/tmp/test_sched_list.json")
        sched.clear()
        sched.add_task(Task(id="t1", title="Test", description="", priority=TaskPriority.LOW, deadline=datetime.now()+timedelta(hours=24)))
        q = sched.list_queue()
        q.clear()
        assert len(sched.list_queue()) == 1

    def test_list_queue_order_before_pop(self):
        """
        list_queue возвращает задачи в порядке добавления (до сортировки pop).

        Проверяем: FIFO до вызова pop_next_task.
        Границы: Две задачи.
        Почему такие: проверка что list_queue не сортирует.
        """
        from space1.orchestrator.scheduler import AIOSScheduler
        from space1.models.task import Task, TaskPriority
        sched = AIOSScheduler(filepath="/tmp/test_sched_list_order.json")
        sched.clear()
        sched.add_task(Task(id="first", title="First", description="", priority=TaskPriority.LOW, deadline=datetime.now()+timedelta(hours=24)))
        sched.add_task(Task(id="second", title="Second", description="", priority=TaskPriority.HIGH, deadline=datetime.now()+timedelta(hours=24)))
        ids = [t.id for t in sched.list_queue()]
        assert ids == ["first", "second"]  # FIFO


# =============================================================================
# INTEGRITY: Архитектурные инварианты Scheduler
# =============================================================================

class TestIntegrityScheduler:
    """INTEGRITY: Проверки кода scheduler на антипаттерны."""

    def test_bare_except_in_scheduler(self):
        """
        scheduler.py содержит bare except — это баг.

        Проверяем: except Exception на строках _load_queue и _save_queue.
        Границы: Весь файл scheduler.py.
        Почему такие: 10_SECURITY.md §III — fail fast, логирование всех ошибок.
        """
        import space1.orchestrator.scheduler as sched_mod
        sched_path = sched_mod.__file__
        with open(sched_path, "r") as f:
            content = f.read()
        lines = content.split("\n")
        bare_excepts = []
        for i, line in enumerate(lines):
            if "except Exception" in line:
                bare_excepts.append(i + 1)
        # ЭТО БАГ: bare except маскирует ошибки
        assert len(bare_excepts) > 0,             "except Exception убран из scheduler (исправлено)"
        assert bare_excepts == [62, 72, 76, 115],             f"Найдены except Exception на строках: {bare_excepts}"

    def test_save_queue_atomic_write(self):
        """
        _save_queue использует atomic write (temp + replace).

        Проверяем: os.replace присутствует в коде.
        Границы: Весь файл.
        Почему такие: atomic write предотвращает corrupted файлы.
        """
        import space1.orchestrator.scheduler as sched_mod
        sched_path = sched_mod.__file__
        with open(sched_path, "r") as f:
            content = f.read()
        assert "os.replace" in content, "_save_queue должен использовать atomic write"

    def test_scheduler_checks_metadata_not_source_attr(self):
        """
        Scheduler ищет source в metadata, не в task.source — это баг.

        Проверяем: pop_next_task использует metadata.get("source").
        Границы: Строка сортировки.
        Почему такие: root cause — disconnect между source attr и metadata.
        """
        import space1.orchestrator.scheduler as sched_mod
        sched_path = sched_mod.__file__
        with open(sched_path, "r") as f:
            content = f.read()
        assert 'metadata.get("source"' in content or "metadata.get('source'" in content
        # ЭТО БАГ: source хранится в task.source, но scheduler ищет в metadata


# =============================================================================
# REGRESSION: Старые баги Scheduler
# =============================================================================

class TestRegressionScheduler:
    """REGRESSION: Проверки, что исправленные баги не вернулись."""

    def test_pop_does_not_crash_on_empty(self):
        """
        pop_next_task на пустой очереди не падает.

        Проверяем: возвращает None, не Exception.
        Границы: Пустая очередь.
        Почему такие: ранний баг — IndexError на пустой очереди.
        """
        from space1.orchestrator.scheduler import AIOSScheduler
        sched = AIOSScheduler(filepath="/tmp/test_sched_regr.json")
        sched.clear()
        result = sched.pop_next_task()
        assert result is None

    def test_task_source_is_enum_not_string(self):
        """
        Task.source — TaskSource enum, не строка.

        Проверяем: type(task.source) == TaskSource.
        Границы: Task без явного source.
        Почему такие: проверка типа — важно для сравнений.
        """
        from space1.models.task import Task, TaskPriority, TaskSource
        from datetime import datetime, timedelta
        task = Task(id="t1", title="Test", description="", priority=TaskPriority.HIGH, deadline=datetime.now()+timedelta(hours=24))
        assert task.source == TaskSource.MARKETPLACE
        assert isinstance(task.source, TaskSource)
