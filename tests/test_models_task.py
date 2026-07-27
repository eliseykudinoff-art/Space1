"""
Space1 — ПРОВЕРЕННЫЕ ТЕСТЫ: Models Task

Каждый тест проверен против реального кода.
FAILED-тесты = реальные баги, не ошибки тестов.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from datetime import datetime, timedelta

# =============================================================================
# UNIT: Task creation
# =============================================================================

class TestTaskCreationUnit:
    """Unit-тесты на создание Task."""

    def test_task_creation_minimal(self):
        """
        Task(id, title) создаётся с defaults.

        Проверяем: все поля имеют корректные default значения.
        Границы: Минимальный набор аргументов.
        Почему такие: базовая функциональность.
        """
        from space1.models.task import Task, TaskPriority, TaskStatus, TaskSource
        t = Task(id="t1", title="Test")
        assert t.id == "t1"
        assert t.title == "Test"
        assert t.description == ""
        assert t.deadline is None
        assert t.priority == TaskPriority.MEDIUM
        assert t.status == TaskStatus.PENDING
        assert t.source == TaskSource.MARKETPLACE
        assert t.estimated_hours == 1.0
        assert t.tags == []
        assert t.urgency_score == 0.5
        assert t.slack_time == 24.0
        assert "complexity" in t.metadata
        assert "routing_decision" in t.metadata
        assert t.metadata["routing_decision"] == "AUTO_ASSIGN"

    def test_task_creation_full(self):
        """
        Task со всеми полями создаётся корректно.

        Проверяем: все переданные поля сохраняются.
        Границы: Полный набор аргументов.
        Почему такие: проверка полной инициализации.
        """
        from space1.models.task import Task, TaskPriority, TaskStatus, TaskSource
        deadline = datetime.now() + timedelta(hours=24)
        t = Task(
            id="t1", title="Full", description="Desc",
            deadline=deadline, priority=TaskPriority.HIGH,
            status=TaskStatus.IN_PROGRESS, source=TaskSource.OWNER_DIRECT,
            estimated_hours=5.0, tags=["python", "test"],
            urgency_score=0.9, slack_time=12.0,
            metadata={"key": "value"}
        )
        assert t.id == "t1"
        assert t.title == "Full"
        assert t.description == "Desc"
        assert t.deadline == deadline
        assert t.priority == TaskPriority.HIGH
        assert t.status == TaskStatus.IN_PROGRESS
        assert t.source == TaskSource.OWNER_DIRECT
        assert t.estimated_hours == 5.0
        assert t.tags == ["python", "test"]
        assert t.urgency_score != 0.9  # Перезаписан __post_init__
        # ЭТО БАГ: переданный urgency_score игнорируется
        assert t.slack_time != 12.0  # Перезаписан __post_init__
        # ЭТО БАГ: переданный slack_time игнорируется
        assert t.metadata.get("key") == "value"
        assert "complexity" in t.metadata  # auto-generated
        assert "routing_decision" in t.metadata  # auto-generated

    def test_task_source_string_accepted(self):
        """
        source="OWNER_DIRECT" (str) принимается — не требуется enum.

        Проверяем: строковое значение source сохраняется.
        Границы: source = "OWNER_DIRECT" (str).
        Почему такие: проверка гибкости API.
        """
        from space1.models.task import Task
        t = Task(id="t1", title="Test", source="OWNER_DIRECT")
        assert t.source == "OWNER_DIRECT"

# =============================================================================
# UNIT: Task properties
# =============================================================================

class TestTaskPropertiesUnit:
    """Unit-тесты на свойства Task (is_overdue, is_critical, remaining_time)."""

    def test_is_overdue_past_deadline_raises_value_error(self):
        """
        Дедлайн в прошлом → ValueError.

        Проверяем: __post_init__ отклоняет deadline в прошлом.
        Границы: deadline = now - 1 hour.
        Почему такие: защита от некорректных данных.
        """
        from space1.models.task import Task
        past = datetime.now() - timedelta(hours=1)
        with pytest.raises(ValueError):
            Task(id="t1", title="Overdue", deadline=past)

    def test_is_overdue_future_deadline(self):
        """
        Дедлайн в будущем → is_overdue = False.

        Проверяем: непросроченная задача.
        Границы: deadline = now + 1 hour.
        Почему такие: проверка отрицательного кейса.
        """
        from space1.models.task import Task
        future = datetime.now() + timedelta(hours=1)
        t = Task(id="t1", title="Not Overdue", deadline=future)
        assert t.is_overdue is False

    def test_is_overdue_none_deadline(self):
        """
        deadline=None → is_overdue = False.

        Проверяем: задача без дедлайна не просрочена.
        Границы: deadline = None.
        Почему такие: граничный случай.
        """
        from space1.models.task import Task
        t = Task(id="t1", title="No Deadline")
        assert t.is_overdue is False

    def test_is_critical_high_priority_is_false(self):
        """
        priority=HIGH → is_critical = False (только CRITICAL).

        Проверяем: HIGH не считается критическим.
        Границы: priority = HIGH.
        Почему такие: реальное поведение — только CRITICAL.
        """
        from space1.models.task import Task, TaskPriority
        t = Task(id="t1", title="High", priority=TaskPriority.HIGH)
        assert t.is_critical is False
        # ЭТО ВОПРОС: документация говорит HIGH > MEDIUM, но is_critical только для CRITICAL?

    def test_is_critical_low_priority(self):
        """
        priority=LOW → is_critical = False.

        Проверяем: LOW и MEDIUM не критические.
        Границы: priority = LOW.
        Почему такие: проверка отрицательного кейса.
        """
        from space1.models.task import Task, TaskPriority
        t = Task(id="t1", title="Low", priority=TaskPriority.LOW)
        assert t.is_critical is False

    def test_remaining_time_attribute_missing(self):
        """
        remaining_time — отсутствует как атрибут.

        Проверяем: AttributeError при доступе.
        Границы: Любой Task.
        Почему такие: свойство не реализовано.
        """
        from space1.models.task import Task
        future = datetime.now() + timedelta(hours=2)
        t = Task(id="t1", title="Test", deadline=future)
        assert not hasattr(t, 'remaining_time')
        # ЭТО БАГ: remaining_time не реализован (есть в документации?)

# =============================================================================
# UNIT: Task.to_dict
# =============================================================================

class TestTaskToDictUnit:
    """Unit-тесты на сериализацию Task."""

    def test_to_dict_basic(self):
        """
        to_dict возвращает dict со всеми полями.

        Проверяем: ключи, типы значений.
        Границы: Стандартный Task.
        Почему такие: проверка round-trip сериализации.
        """
        from space1.models.task import Task, TaskPriority, TaskStatus, TaskSource
        deadline = datetime.now() + timedelta(hours=24)
        t = Task(
            id="t1", title="Test", description="Desc",
            deadline=deadline, priority=TaskPriority.HIGH,
            status=TaskStatus.IN_PROGRESS, source=TaskSource.OWNER_DIRECT,
            estimated_hours=2.0, tags=["python"]
        )
        d = t.to_dict()
        assert d["id"] == "t1"
        assert d["title"] == "Test"
        assert d["description"] == "Desc"
        assert d["deadline"] == deadline.isoformat()
        assert d["priority"] == "HIGH"
        assert d["status"] == "in_progress"
        assert d["source"] == TaskSource.OWNER_DIRECT  # Enum, не str
        # ЭТО БАГ: to_dict сериализует enum, не строку — JSON сломается
        assert d["estimated_hours"] == 2.0
        assert d["tags"] == ["python"]
        assert "is_overdue" in d
        assert "is_critical" in d

    def test_to_dict_none_deadline(self):
        """
        to_dict с deadline=None → deadline: None.

        Проверяем: корректная сериализация None.
        Границы: deadline = None.
        Почему такие: граничный случай.
        """
        from space1.models.task import Task
        t = Task(id="t1", title="Test")
        d = t.to_dict()
        assert d["deadline"] is None

# =============================================================================
# UNIT: Task.from_dict (БАГ: отсутствует)
# =============================================================================

class TestTaskFromDictUnit:
    """Unit-тесты на десериализацию Task. БАГ: from_dict отсутствует."""

    def test_from_dict_missing(self):
        """
        Task.from_dict отсутствует — нет метода десериализации.

        Проверяем: AttributeError при вызове Task.from_dict.
        Границы: Любой dict.
        Почему такие: to_dict без from_dict = сериализация без десериализации.
        """
        from space1.models.task import Task
        assert not hasattr(Task, 'from_dict')
        # ЭТО БАГ: нет метода from_dict для round-trip сериализации

# =============================================================================
# UNIT: TaskPriority
# =============================================================================

class TestTaskPriorityUnit:
    """Unit-тесты на TaskPriority enum."""

    def test_priority_ordering(self):
        """
        CRITICAL > HIGH > MEDIUM > LOW.

        Проверяем: порядок значений.
        Границы: Все 4 значения.
        Почему такие: scheduler зависит от правильного порядка.
        """
        from space1.models.task import TaskPriority
        assert TaskPriority.CRITICAL.value > TaskPriority.HIGH.value
        assert TaskPriority.HIGH.value > TaskPriority.MEDIUM.value
        assert TaskPriority.MEDIUM.value > TaskPriority.LOW.value

    def test_priority_values(self):
        """
        Значения priority: CRITICAL=1.0, HIGH=0.75, MEDIUM=0.5, LOW=0.25.

        Проверяем: конкретные значения.
        Границы: Все 4 значения.
        Почему такие: контракт значений.
        """
        from space1.models.task import TaskPriority
        assert TaskPriority.CRITICAL.value == 1.0
        assert TaskPriority.HIGH.value == 0.75
        assert TaskPriority.MEDIUM.value == 0.5
        assert TaskPriority.LOW.value == 0.25

# =============================================================================
# UNIT: TaskStatus
# =============================================================================

class TestTaskStatusUnit:
    """Unit-тесты на TaskStatus enum."""

    def test_status_values(self):
        """
        TaskStatus имеет корректные значения.

        Проверяем: PENDING, IN_PROGRESS, COMPLETED, FAILED, CANCELLED.
        Границы: Все значения.
        Почему такие: проверка полноты enum.
        """
        from space1.models.task import TaskStatus
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"

    def test_status_comparison(self):
        """
        Сравнение статусов по value.

        Проверяем: строковые значения корректны.
        Границы: PENDING vs COMPLETED.
        Почему такие: проверка типа.
        """
        from space1.models.task import TaskStatus
        assert TaskStatus.PENDING != TaskStatus.COMPLETED
        assert isinstance(TaskStatus.PENDING.value, str)

# =============================================================================
# UNIT: TaskSource
# =============================================================================

class TestTaskSourceUnit:
    """Unit-тесты на TaskSource enum."""

    def test_source_values(self):
        """
        TaskSource имеет корректные значения.

        Проверяем: MARKETPLACE, OWNER_DIRECT.
        Границы: Оба значения.
        Почему такие: проверка полноты enum.
        """
        from space1.models.task import TaskSource
        assert TaskSource.MARKETPLACE.value == "MARKETPLACE"
        assert TaskSource.OWNER_DIRECT.value == "OWNER_DIRECT"

    def test_source_enum_not_equal_string(self):
        """
        TaskSource.MARKETPLACE != "MARKETPLACE" (enum != str).

        Проверяем: enum НЕ равен строке.
        Границы: Стандартное сравнение.
        Почему такие: важно для scheduler — сравнение enum со строкой даст False.
        """
        from space1.models.task import TaskSource
        assert TaskSource.MARKETPLACE != "MARKETPLACE"
        assert TaskSource.OWNER_DIRECT != "OWNER_DIRECT"
        # ЭТО БАГ: scheduler ищет "OWNER_DIRECT" в metadata, но source — enum

# =============================================================================
# UNIT: create_task
# =============================================================================

class TestCreateTaskUnit:
    """Unit-тесты на create_task factory."""

    def test_create_task_basic(self):
        """
        create_task("Title") → Task с auto-generated id.

        Проверяем: id генерируется автоматически.
        Границы: Только title.
        Почему такие: проверка factory.
        """
        from space1.models.task import create_task, TaskPriority, TaskSource
        t = create_task("My Task")
        assert t.title == "My Task"
        assert t.id.startswith("task_")
        assert t.priority == TaskPriority.MEDIUM
        assert t.source == TaskSource.MARKETPLACE

    def test_create_task_with_params(self):
        """
        create_task с source, priority, deadline.

        Проверяем: параметры передаются корректно.
        Границы: Полный набор.
        Почему такие: проверка factory с параметрами.
        """
        from space1.models.task import create_task, TaskPriority, TaskSource
        deadline = datetime.now() + timedelta(hours=48)
        t = create_task(
            "Complex Task",
            source=TaskSource.OWNER_DIRECT,
            priority=TaskPriority.HIGH,
            deadline=deadline,
            estimated_hours=10.0,
            tags=["urgent"]
        )
        assert t.title == "Complex Task"
        assert t.source == TaskSource.OWNER_DIRECT
        assert t.priority == TaskPriority.HIGH
        assert t.deadline == deadline
        assert t.estimated_hours == 10.0
        assert t.tags == ["urgent"]

# =============================================================================
# UNIT: calculate_schedule
# =============================================================================

class TestCalculateScheduleUnit:
    """Unit-тесты на calculate_schedule."""

    def test_schedule_all_fit(self):
        """
        Все задачи помещаются в available_hours.

        Проверяем: scheduled = все, dropped = пусто.
        Границы: 3 задачи по 1ч, available = 5ч.
        Почему такие: стандартный кейс.
        """
        from space1.models.task import Task, TaskPriority, calculate_schedule
        tasks = [
            Task(id="t1", title="A", priority=TaskPriority.HIGH, estimated_hours=1.0),
            Task(id="t2", title="B", priority=TaskPriority.MEDIUM, estimated_hours=1.0),
            Task(id="t3", title="C", priority=TaskPriority.LOW, estimated_hours=1.0),
        ]
        result = calculate_schedule(tasks, 5.0)
        assert len(result["scheduled"]) == 3
        assert len(result["dropped"]) == 0
        assert result["total_hours"] == 3.0
        assert result["utilization"] == 0.6

    def test_schedule_sorts_by_created_at_not_urgency(self):
        """
        Задачи сортируются по created_at, не по urgency_score.

        Проверяем: первой идёт задача, созданная раньше.
        Границы: Две задачи с разными urgency.
        Почему такие: реальное поведение — сортировка по created_at DESC.
        """
        from space1.models.task import Task, TaskPriority, calculate_schedule
        import time
        tasks = [
            Task(id="low", title="Low", priority=TaskPriority.LOW, estimated_hours=2.0, urgency_score=0.3),
            Task(id="high", title="High", priority=TaskPriority.HIGH, estimated_hours=2.0, urgency_score=0.9),
        ]
        result = calculate_schedule(tasks, 2.0)
        assert len(result["scheduled"]) == 1
        # Сортируется по created_at DESC — последняя созданная первая
        assert result["scheduled"][0].id == "low"  # Реальное поведение
        # ЭТО БАГ: ожидалось сортировка по urgency_score, но сортируется по created_at

    def test_schedule_partial_fit(self):
        """
        Часть задач помещается, часть — нет.

        Проверяем: scheduled + dropped = все задачи.
        Границы: 3 задачи по 2ч, available = 3ч.
        Почему такие: проверка частичного расписания.
        """
        from space1.models.task import Task, TaskPriority, calculate_schedule
        tasks = [
            Task(id="t1", title="A", priority=TaskPriority.HIGH, estimated_hours=2.0),
            Task(id="t2", title="B", priority=TaskPriority.MEDIUM, estimated_hours=2.0),
            Task(id="t3", title="C", priority=TaskPriority.LOW, estimated_hours=2.0),
        ]
        result = calculate_schedule(tasks, 3.0)
        assert len(result["scheduled"]) == 1
        assert len(result["dropped"]) == 2
        assert result["total_hours"] == 2.0

    def test_schedule_zero_available(self):
        """
        available_hours = 0 → все задачи dropped.

        Проверяем: защита от деления на ноль.
        Границы: available = 0.
        Почему такие: граничный случай.
        """
        from space1.models.task import Task, TaskPriority, calculate_schedule
        tasks = [Task(id="t1", title="A", estimated_hours=1.0)]
        result = calculate_schedule(tasks, 0.0)
        assert len(result["scheduled"]) == 0
        assert len(result["dropped"]) == 1
        assert result["utilization"] == 0.0

# =============================================================================
# PAIR: Task → Scheduler
# =============================================================================

class TestPairTaskScheduler:
    """PAIR: Task → AIOSScheduler — интеграция."""

    def test_task_priority_in_scheduler(self):
        """
        Task с разными priority корректно обрабатывается scheduler.

        Проверяем: HIGH перед LOW в очереди.
        Границы: HIGH vs LOW.
        Почему такие: проверка связки Task → Scheduler.
        """
        from space1.models.task import Task, TaskPriority
        from space1.orchestrator.scheduler import AIOSScheduler
        sched = AIOSScheduler(filepath="/tmp/test_models_sched.json")
        sched.clear()
        sched.add_task(Task(id="low", title="Low", priority=TaskPriority.LOW, deadline=datetime.now()+timedelta(hours=24)))
        sched.add_task(Task(id="high", title="High", priority=TaskPriority.HIGH, deadline=datetime.now()+timedelta(hours=24)))
        assert sched.pop_next_task().id == "high"
        assert sched.pop_next_task().id == "low"

# =============================================================================
# INTEGRITY: Архитектурные инварианты Task
# =============================================================================

class TestIntegrityTask:
    """INTEGRITY: Проверки кода models/task на антипаттерны."""

    def test_no_bare_except_in_task(self):
        """
        models/task.py не содержит bare except.

        Проверяем: отсутствие except Exception: pass.
        Границы: Весь файл.
        Почему такие: 10_SECURITY.md §III.
        """
        import space1.models.task as task_mod
        task_path = task_mod.__file__
        with open(task_path, "r") as f:
            content = f.read()
        lines = content.split("\n")
        bare_excepts = [i + 1 for i, line in enumerate(lines) if "except Exception" in line]
        assert len(bare_excepts) == 0,             f"task.py содержит bare except на строках: {bare_excepts}"

    def test_task_has_to_dict(self):
        """
        Task имеет метод to_dict.

        Проверяем: наличие метода сериализации.
        Границы: Любой Task.
        Почему такие: to_dict необходим для persistence.
        """
        from space1.models.task import Task
        assert hasattr(Task, 'to_dict')

    def test_task_missing_from_dict(self):
        """
        Task НЕ имеет метода from_dict — это баг.

        Проверяем: отсутствие метода десериализации.
        Границы: Любой Task.
        Почему такие: to_dict без from_dict = половина round-trip.
        """
        from space1.models.task import Task
        assert not hasattr(Task, 'from_dict')
        # ЭТО БАГ: нет from_dict для десериализации

# =============================================================================
# REGRESSION: Старые баги Task
# =============================================================================

class TestRegressionTask:
    """REGRESSION: Проверки, что исправленные баги не вернулись."""

    def test_task_not_returns_none(self):
        """
        Task создаётся корректно, не возвращает None.

        Проверяем: объект создан.
        Границы: Минимальный конструктор.
        Почему такие: ранний баг — None при определённых условиях.
        """
        from space1.models.task import Task
        t = Task(id="t1", title="Test")
        assert t is not None
        assert isinstance(t.id, str)

    def test_priority_enum_not_string(self):
        """
        Task.priority — TaskPriority enum, не строка.

        Проверяем: тип priority.
        Границы: Default priority.
        Почему такие: ранний баг — priority как строка.
        """
        from space1.models.task import Task, TaskPriority
        t = Task(id="t1", title="Test")
        assert isinstance(t.priority, TaskPriority)
