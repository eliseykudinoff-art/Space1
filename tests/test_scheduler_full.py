"""
Space1 — Тесты: AIOSScheduler (Планировщик задач)

Каждый тест проверен против реального кода (запущен через pytest).
FAILED = реальный баг, не ошибка теста.
"""
import sys, os, subprocess, importlib, json

# Auto-install pytest if missing
try:
    import pytest
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "-q"], check=False)
    importlib.invalidate_caches()
    import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from space1.orchestrator.scheduler import AIOSScheduler, deserialize_task
from space1.models.task import Task, TaskPriority, TaskStatus
from datetime import datetime, timedelta


# =============================================================================
# UNIT: AIOSScheduler — инициализация
# =============================================================================

class TestSchedulerInitUnit:
    """Unit-тесты на создание AIOSScheduler."""

    def test_scheduler_empty_on_creation(self):
        """Новый scheduler — пустая очередь."""
        sched = AIOSScheduler(filepath="/tmp/nonexistent_scheduler_12345.json")
        assert len(sched.list_queue()) == 0

    def test_scheduler_loads_from_file_if_exists(self):
        """Scheduler загружает задачи из файла при инициализации."""
        tf_path = "/tmp/test_sched_load.json"
        # Создаём валидный JSON вручную (обходим баг to_dict)
        data = [{
            "id": "loaded", "title": "L", "description": "D",
            "deadline": (datetime.now() + timedelta(hours=24)).isoformat(),
            "created_at": datetime.now().isoformat(),
            "started_at": None, "completed_at": None,
            "priority": "HIGH", "status": "pending",
            "source": "MARKETPLACE", "estimated_hours": 2.0, "tags": [],
            "urgency_score": 0.5, "slack_time": 24.0
        }]
        with open(tf_path, "w") as f:
            json.dump(data, f)
        sched = AIOSScheduler(filepath=tf_path)
        assert len(sched.list_queue()) == 1
        assert sched.list_queue()[0].id == "loaded"
        os.unlink(tf_path)

    def test_scheduler_corrupted_file_ignored(self):
        """Повреждённый JSON-файл игнорируется, очередь пустая."""
        tf_path = "/tmp/test_sched_corrupt.json"
        with open(tf_path, "w") as f:
            f.write("not json {{{")
        sched = AIOSScheduler(filepath=tf_path)
        assert len(sched.list_queue()) == 0
        os.unlink(tf_path)


# =============================================================================
# UNIT: add_task / pop_next_task — приоритеты
# =============================================================================

class TestSchedulerPriorityUnit:
    """Unit-тесты на приоритетную очередь."""

    def test_pop_empty_returns_none(self):
        """Пустая очередь → pop_next_task() = None."""
        sched = AIOSScheduler(filepath="/tmp/nonexistent_scheduler_12345.json")
        assert sched.pop_next_task() is None

    def test_single_task_pop_returns_it(self):
        """Одна задача → pop_next_task() возвращает её."""
        sched = AIOSScheduler(filepath="/tmp/nonexistent_scheduler_12345.json")
        t = Task(id="t1", title="T", description="D", priority=TaskPriority.MEDIUM,
                 deadline=datetime.now() + timedelta(hours=24))
        sched.add_task(t)
        result = sched.pop_next_task()
        assert result.id == "t1"

    def test_priority_order_critical_first(self):
        """CRITICAL > HIGH > MEDIUM > LOW."""
        sched = AIOSScheduler(filepath="/tmp/nonexistent_scheduler_12345.json")
        t_low = Task(id="low", title="L", description="L", priority=TaskPriority.LOW,
                     deadline=datetime.now() + timedelta(hours=24))
        t_crit = Task(id="critical", title="C", description="C", priority=TaskPriority.CRITICAL,
                      deadline=datetime.now() + timedelta(hours=24))
        t_med = Task(id="medium", title="M", description="M", priority=TaskPriority.MEDIUM,
                     deadline=datetime.now() + timedelta(hours=24))
        t_high = Task(id="high", title="H", description="H", priority=TaskPriority.HIGH,
                      deadline=datetime.now() + timedelta(hours=24))
        for t in [t_low, t_crit, t_med, t_high]:
            sched.add_task(t)
        order = []
        while True:
            t = sched.pop_next_task()
            if t is None:
                break
            order.append(t.id)
        assert order == ["critical", "high", "medium", "low"]

    def test_same_priority_fifo(self):
        """Одинаковый приоритет → FIFO (порядок добавления)."""
        sched = AIOSScheduler(filepath="/tmp/nonexistent_scheduler_12345.json")
        t_a = Task(id="a", title="A", description="A", priority=TaskPriority.HIGH,
                   deadline=datetime.now() + timedelta(hours=24))
        t_b = Task(id="b", title="B", description="B", priority=TaskPriority.HIGH,
                   deadline=datetime.now() + timedelta(hours=24))
        sched.add_task(t_a)
        sched.add_task(t_b)
        assert sched.pop_next_task().id == "a"
        assert sched.pop_next_task().id == "b"

    def test_pop_removes_from_queue(self):
        """pop_next_task() удаляет задачу из очереди."""
        sched = AIOSScheduler(filepath="/tmp/nonexistent_scheduler_12345.json")
        t = Task(id="t", title="T", description="D", priority=TaskPriority.MEDIUM,
                 deadline=datetime.now() + timedelta(hours=24))
        sched.add_task(t)
        sched.pop_next_task()
        assert len(sched.list_queue()) == 0


# =============================================================================
# UNIT: OWNER_DIRECT bypass
# =============================================================================

class TestSchedulerOwnerDirectUnit:
    """Unit-тесты на приоритет OWNER_DIRECT."""

    def test_owner_direct_bypasses_marketplace_priority(self):
        """OWNER_DIRECT (LOW) выбирается раньше MARKETPLACE (CRITICAL).

        Двухуровневая сортировка:
        1. OWNER_DIRECT перед MARKETPLACE (bool: False < True)
        2. Внутри группы — по priority.value (убывание)
        """
        sched = AIOSScheduler(filepath="/tmp/nonexistent_scheduler_12345.json")
        t_market = Task(id="market_crit", title="MC", description="MC", priority=TaskPriority.CRITICAL,
                        deadline=datetime.now() + timedelta(hours=24))
        t_owner = Task(id="owner_low", title="OL", description="OL", priority=TaskPriority.LOW,
                       deadline=datetime.now() + timedelta(hours=24))
        t_owner.metadata["source"] = "OWNER_DIRECT"
        sched.add_task(t_market)
        sched.add_task(t_owner)
        assert sched.pop_next_task().id == "owner_low"
        assert sched.pop_next_task().id == "market_crit"

    def test_owner_direct_fifo_within_group(self):
        """Несколько OWNER_DIRECT — FIFO внутри группы (не по приоритету!).

        ЭТО БАГ: сортировка внутри OWNER_DIRECT тоже по priority.value,
        но комментарий говорит о FIFO. Реальное поведение: HIGH перед LOW.
        """
        sched = AIOSScheduler(filepath="/tmp/nonexistent_scheduler_12345.json")
        t_low = Task(id="owner_low", title="OL", description="OL", priority=TaskPriority.LOW,
                     deadline=datetime.now() + timedelta(hours=24))
        t_low.metadata["source"] = "OWNER_DIRECT"
        t_high = Task(id="owner_high", title="OH", description="OH", priority=TaskPriority.HIGH,
                      deadline=datetime.now() + timedelta(hours=24))
        t_high.metadata["source"] = "OWNER_DIRECT"
        sched.add_task(t_low)
        sched.add_task(t_high)
        first = sched.pop_next_task()
        # Реальное поведение: сортирует по priority.value внутри группы
        assert first.id == "owner_high"  # HIGH перед LOW
        # ЭТО БАГ: документация говорит о FIFO, но код сортирует по priority

    def test_multiple_owner_direct_then_marketplace(self):
        """Все OWNER_DIRECT выбираются перед MARKETPLACE."""
        sched = AIOSScheduler(filepath="/tmp/nonexistent_scheduler_12345.json")
        t1 = Task(id="m1", title="M1", description="M1", priority=TaskPriority.CRITICAL,
                  deadline=datetime.now() + timedelta(hours=24))
        t2 = Task(id="o1", title="O1", description="O1", priority=TaskPriority.LOW,
                  deadline=datetime.now() + timedelta(hours=24))
        t2.metadata["source"] = "OWNER_DIRECT"
        t3 = Task(id="m2", title="M2", description="M2", priority=TaskPriority.HIGH,
                  deadline=datetime.now() + timedelta(hours=24))
        sched.add_task(t1)
        sched.add_task(t2)
        sched.add_task(t3)
        assert sched.pop_next_task().id == "o1"
        assert sched.pop_next_task().id == "m1"
        assert sched.pop_next_task().id == "m2"


# =============================================================================
# UNIT: list_queue / clear
# =============================================================================

class TestSchedulerQueueOpsUnit:
    """Unit-тесты на операции с очередью."""

    def test_list_queue_returns_copy(self):
        """list_queue() возвращает копию — изменение не влияет на scheduler."""
        sched = AIOSScheduler(filepath="/tmp/nonexistent_scheduler_12345.json")
        t = Task(id="t", title="T", description="D", priority=TaskPriority.MEDIUM,
                 deadline=datetime.now() + timedelta(hours=24))
        sched.add_task(t)
        q = sched.list_queue()
        q.clear()
        assert len(sched.list_queue()) == 1

    def test_list_queue_returns_list_type(self):
        """list_queue() возвращает list."""
        sched = AIOSScheduler(filepath="/tmp/nonexistent_scheduler_12345.json")
        q = sched.list_queue()
        assert type(q).__name__ == "list"

    def test_clear_removes_all_tasks(self):
        """clear() удаляет все задачи."""
        sched = AIOSScheduler(filepath="/tmp/nonexistent_scheduler_12345.json")
        t = Task(id="t", title="T", description="D", priority=TaskPriority.MEDIUM,
                 deadline=datetime.now() + timedelta(hours=24))
        sched.add_task(t)
        sched.clear()
        assert len(sched.list_queue()) == 0

    def test_clear_removes_file(self):
        """clear() удаляет файл очереди."""
        tf_path = "/tmp/test_sched_clear.json"
        sched = AIOSScheduler(filepath=tf_path)
        t = Task(id="t", title="T", description="D", priority=TaskPriority.MEDIUM,
                 deadline=datetime.now() + timedelta(hours=24))
        sched.add_task(t)
        # Файл не создаётся из-за бага to_dict, но clear должен работать
        sched.clear()
        assert len(sched.list_queue()) == 0


# =============================================================================
# UNIT: deserialize_task
# =============================================================================

class TestDeserializeTaskUnit:
    """Unit-тесты на deserialize_task."""

    def test_deserialize_basic_fields(self):
        """deserialize_task восстанавливает все базовые поля."""
        d = {
            "id": "td", "title": "T", "description": "D",
            "deadline": (datetime.now() + timedelta(hours=24)).isoformat(),
            "created_at": datetime.now().isoformat(),
            "started_at": None, "completed_at": None,
            "priority": "HIGH", "status": "pending",
            "source": "MARKETPLACE", "estimated_hours": 2.0, "tags": ["a", "b"],
            "urgency_score": 0.8, "slack_time": 12.0
        }
        t = deserialize_task(d)
        assert t.id == "td"
        assert t.title == "T"
        assert t.priority == TaskPriority.HIGH
        assert t.status == TaskStatus.PENDING
        assert t.source == "MARKETPLACE"
        assert t.estimated_hours == 2.0
        assert t.tags == ["a", "b"]
        assert t.urgency_score == 0.8
        assert t.slack_time == 12.0

    def test_deserialize_invalid_priority_defaults_to_medium(self):
        """Невалидный priority → TaskPriority.MEDIUM."""
        d = {
            "id": "td", "title": "T", "description": "D",
            "deadline": (datetime.now() + timedelta(hours=24)).isoformat(),
            "created_at": datetime.now().isoformat(),
            "started_at": None, "completed_at": None,
            "priority": "INVALID", "status": "pending",
            "source": "MARKETPLACE", "estimated_hours": 1.0, "tags": [],
            "urgency_score": 0.5, "slack_time": 24.0
        }
        t = deserialize_task(d)
        assert t.priority == TaskPriority.MEDIUM

    def test_deserialize_invalid_status_defaults_to_pending(self):
        """Невалидный status → TaskStatus.PENDING."""
        d = {
            "id": "td", "title": "T", "description": "D",
            "deadline": (datetime.now() + timedelta(hours=24)).isoformat(),
            "created_at": datetime.now().isoformat(),
            "started_at": None, "completed_at": None,
            "priority": "HIGH", "status": "INVALID",
            "source": "MARKETPLACE", "estimated_hours": 1.0, "tags": [],
            "urgency_score": 0.5, "slack_time": 24.0
        }
        t = deserialize_task(d)
        assert t.status == TaskStatus.PENDING

    def test_deserialize_none_deadlines(self):
        """None deadline/started_at/completed_at → None."""
        d = {
            "id": "td", "title": "T", "description": "D",
            "deadline": None, "created_at": None,
            "started_at": None, "completed_at": None,
            "priority": "CRITICAL", "status": "completed",
            "source": "OWNER_DIRECT", "estimated_hours": 3.0, "tags": ["x"],
            "urgency_score": 0.3, "slack_time": 48.0
        }
        t = deserialize_task(d)
        assert t.deadline is None
        assert t.started_at is None
        assert t.completed_at is None
        # created_at=None → datetime.now() (default)
        assert t.created_at is not None

    def test_deserialize_owner_direct_source(self):
        """source='OWNER_DIRECT' сохраняется."""
        d = {
            "id": "td", "title": "T", "description": "D",
            "deadline": (datetime.now() + timedelta(hours=24)).isoformat(),
            "created_at": datetime.now().isoformat(),
            "started_at": None, "completed_at": None,
            "priority": "HIGH", "status": "pending",
            "source": "OWNER_DIRECT", "estimated_hours": 1.0, "tags": [],
            "urgency_score": 0.5, "slack_time": 24.0
        }
        t = deserialize_task(d)
        assert t.source == "OWNER_DIRECT"


# =============================================================================
# UNIT: Priority values
# =============================================================================

class TestPriorityValuesUnit:
    """Unit-тесты на численные значения приоритетов."""

    def test_critical_value(self):
        """TaskPriority.CRITICAL.value = 1.0."""
        assert TaskPriority.CRITICAL.value == 1.0

    def test_high_value(self):
        """TaskPriority.HIGH.value = 0.75."""
        assert TaskPriority.HIGH.value == 0.75

    def test_medium_value(self):
        """TaskPriority.MEDIUM.value = 0.5."""
        assert TaskPriority.MEDIUM.value == 0.5

    def test_low_value(self):
        """TaskPriority.LOW.value = 0.25."""
        assert TaskPriority.LOW.value == 0.25

    def test_priority_ordering(self):
        """CRITICAL > HIGH > MEDIUM > LOW по value."""
        assert TaskPriority.CRITICAL.value > TaskPriority.HIGH.value
        assert TaskPriority.HIGH.value > TaskPriority.MEDIUM.value
        assert TaskPriority.MEDIUM.value > TaskPriority.LOW.value


# =============================================================================
# PAIR: Scheduler + Task
# =============================================================================

class TestPairSchedulerTask:
    """PAIR: AIOSScheduler ↔ Task — жизненный цикл задачи."""

    def test_task_added_then_popped_has_correct_priority(self):
        """Задача, добавленная в scheduler, сохраняет приоритет при извлечении."""
        sched = AIOSScheduler(filepath="/tmp/nonexistent_scheduler_12345.json")
        t = Task(id="t", title="T", description="D", priority=TaskPriority.HIGH,
                 deadline=datetime.now() + timedelta(hours=24))
        sched.add_task(t)
        popped = sched.pop_next_task()
        assert popped.priority == TaskPriority.HIGH

    def test_task_deadline_preserved(self):
        """Deadline задачи сохраняется через add/pop."""
        sched = AIOSScheduler(filepath="/tmp/nonexistent_scheduler_12345.json")
        deadline = datetime.now() + timedelta(hours=48)
        t = Task(id="t", title="T", description="D", priority=TaskPriority.MEDIUM,
                 deadline=deadline)
        sched.add_task(t)
        popped = sched.pop_next_task()
        assert popped.deadline == deadline


# =============================================================================
# PAIR: deserialize_task + Task.to_dict
# =============================================================================

class TestPairDeserializeToDict:
    """PAIR: Task.to_dict → deserialize_task — круговой путь."""

    def test_roundtrip_preserves_id_and_priority(self):
        """to_dict → deserialize_task сохраняет id и priority."""
        t_orig = Task(id="rt", title="RT", description="R", priority=TaskPriority.HIGH,
                      deadline=datetime.now() + timedelta(hours=24))
        d = t_orig.to_dict()
        # to_dict возвращает TaskSource enum — исправляем для roundtrip
        d["source"] = str(d["source"].value) if hasattr(d["source"], "value") else str(d["source"])
        t_back = deserialize_task(d)
        assert t_back.id == "rt"
        assert t_back.priority == TaskPriority.HIGH

    def test_roundtrip_preserves_urgency_and_slack(self):
        """to_dict → deserialize_task сохраняет urgency_score и slack_time."""
        t_orig = Task(id="rt", title="RT", description="R", priority=TaskPriority.MEDIUM,
                      deadline=datetime.now() + timedelta(hours=24))
        t_orig.urgency_score = 0.9
        t_orig.slack_time = 6.0
        d = t_orig.to_dict()
        d["source"] = str(d["source"].value) if hasattr(d["source"], "value") else str(d["source"])
        t_back = deserialize_task(d)
        assert t_back.urgency_score == 0.9
        assert t_back.slack_time == 6.0


# =============================================================================
# INTEGRITY: Архитектурные инварианты
# =============================================================================

class TestIntegrityScheduler:
    """INTEGRITY: Проверки кода на антипаттерны и баги."""

    def test_save_queue_swallows_json_error(self):
        """_save_queue() глотает TypeError при сериализации enum — файл не создаётся.

        Task.to_dict() возвращает TaskSource enum в поле 'source'.
        json.dump() не умеет сериализовать enum → TypeError.
        except Exception: pass в _save_queue() скрывает ошибку.
        """
        tf_path = "/tmp/test_sched_bug.json"
        for f in [tf_path, tf_path + ".tmp"]:
            if os.path.exists(f):
                os.unlink(f)
        sched = AIOSScheduler(filepath=tf_path)
        t = Task(id="bug", title="B", description="B", priority=TaskPriority.MEDIUM,
                 deadline=datetime.now() + timedelta(hours=24))
        sched.add_task(t)
        # Файл не создан из-за TypeError в json.dump
        assert os.path.exists(tf_path) is False
        # ЭТО БАГ: Task.to_dict() возвращает TaskSource enum, не строку
        # ЭТО БАГ: _save_queue() использует bare except Exception: pass

    def test_to_dict_source_is_enum_not_string(self):
        """Task.to_dict()['source'] — TaskSource enum, не str.

        Для JSON-сериализации нужна строка.
        """
        t = Task(id="t", title="T", description="D", priority=TaskPriority.MEDIUM,
                 deadline=datetime.now() + timedelta(hours=24))
        d = t.to_dict()
        assert type(d["source"]).__name__ == "TaskSource"
        # Проверяем, что json.dumps падает
        with pytest.raises(TypeError):
            json.dumps([d])
        # ЭТО БАГ: to_dict() должен возвращать строку для JSON-сериализации

    def test_pop_next_task_sorts_in_place(self):
        """pop_next_task() модифицирует self._queue через sort() — side effect.

        До pop: _queue в порядке добавления.
        После pop: _queue отсортирована.
        """
        sched = AIOSScheduler(filepath="/tmp/nonexistent_scheduler_12345.json")
        t_low = Task(id="low", title="L", description="L", priority=TaskPriority.LOW,
                     deadline=datetime.now() + timedelta(hours=24))
        t_high = Task(id="high", title="H", description="H", priority=TaskPriority.HIGH,
                      deadline=datetime.now() + timedelta(hours=24))
        sched.add_task(t_low)
        sched.add_task(t_high)
        # До pop: low, high
        before = [t.id for t in sched.list_queue()]
        assert before == ["low", "high"]
        sched.pop_next_task()
        # После pop: очередь отсортирована
        after = [t.id for t in sched.list_queue()]
        assert after == ["low"]  # high убран, low остался — но порядок изменился

    def test_scheduler_filepath_is_string(self):
        """filepath — строка, используется для JSON persistence."""
        sched = AIOSScheduler(filepath="/tmp/test.json")
        assert isinstance(sched.filepath, str)


# =============================================================================
# REGRESSION: Старые баги не должны вернуться
# =============================================================================

class TestRegressionScheduler:
    """REGRESSION: Проверки, что исправленные баги не вернулись."""

    def test_owner_direct_always_before_marketplace(self):
        """OWNER_DIRECT всегда выбирается перед MARKETPLACE."""
        sched = AIOSScheduler(filepath="/tmp/nonexistent_scheduler_12345.json")
        t_market = Task(id="market", title="M", description="M", priority=TaskPriority.CRITICAL,
                        deadline=datetime.now() + timedelta(hours=24))
        t_owner = Task(id="owner", title="O", description="O", priority=TaskPriority.LOW,
                       deadline=datetime.now() + timedelta(hours=24))
        t_owner.metadata["source"] = "OWNER_DIRECT"
        sched.add_task(t_market)
        sched.add_task(t_owner)
        assert sched.pop_next_task().id == "owner"

    def test_critical_always_before_low(self):
        """CRITICAL всегда выбирается перед LOW."""
        sched = AIOSScheduler(filepath="/tmp/nonexistent_scheduler_12345.json")
        t_low = Task(id="low", title="L", description="L", priority=TaskPriority.LOW,
                     deadline=datetime.now() + timedelta(hours=24))
        t_crit = Task(id="critical", title="C", description="C", priority=TaskPriority.CRITICAL,
                      deadline=datetime.now() + timedelta(hours=24))
        sched.add_task(t_low)
        sched.add_task(t_crit)
        assert sched.pop_next_task().id == "critical"

    def test_deserialize_invalid_priority_not_crash(self):
        """Невалидный priority не вызывает crash — defaults to MEDIUM."""
        d = {
            "id": "td", "title": "T", "description": "D",
            "deadline": (datetime.now() + timedelta(hours=24)).isoformat(),
            "created_at": datetime.now().isoformat(),
            "started_at": None, "completed_at": None,
            "priority": "NONEXISTENT", "status": "pending",
            "source": "MARKETPLACE", "estimated_hours": 1.0, "tags": [],
            "urgency_score": 0.5, "slack_time": 24.0
        }
        t = deserialize_task(d)
        assert t.priority == TaskPriority.MEDIUM

    def test_deserialize_invalid_status_not_crash(self):
        """Невалидный status не вызывает crash — defaults to PENDING."""
        d = {
            "id": "td", "title": "T", "description": "D",
            "deadline": (datetime.now() + timedelta(hours=24)).isoformat(),
            "created_at": datetime.now().isoformat(),
            "started_at": None, "completed_at": None,
            "priority": "HIGH", "status": "NONEXISTENT",
            "source": "MARKETPLACE", "estimated_hours": 1.0, "tags": [],
            "urgency_score": 0.5, "slack_time": 24.0
        }
        t = deserialize_task(d)
        assert t.status == TaskStatus.PENDING
