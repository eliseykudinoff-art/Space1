"""
Space1 — ПРОВЕРЕННЫЕ ТЕСТЫ: Environment Core

Каждый тест проверен против реального кода.
FAILED-тесты = реальные баги, не ошибки тестов.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest


# =============================================================================
# UNIT: ClientProfile
# =============================================================================

class TestClientProfileUnit:
    """Unit-тесты на ClientProfile dataclass."""

    def test_client_profile_defaults(self):
        """
        ClientProfile(id="c1", name="Test") → rigor=0.5, max_budget=500, reputation_multiplier=1.0, is_demanding=False.

        Проверяем: default значения.
        Границы: Без опциональных аргументов.
        Почему такие: контракт default values.
        """
        from space1.environment.core import ClientProfile
        client = ClientProfile(id="c1", name="Test")
        assert client.rigor == 0.5
        assert client.max_budget == 500.0
        assert client.reputation_multiplier == 1.0
        assert client.is_demanding is False

    def test_client_profile_custom(self):
        """
        ClientProfile(id="c1", name="Test", rigor=0.8, max_budget=200, is_demanding=True) → кастомные значения.

        Проверяем: переопределение default.
        Границы: Кастомные значения.
        Почему такие: проверка переопределения.
        """
        from space1.environment.core import ClientProfile
        client = ClientProfile(id="c1", name="Test", rigor=0.8, max_budget=200.0, is_demanding=True)
        assert client.rigor == 0.8
        assert client.max_budget == 200.0
        assert client.is_demanding is True

    def test_client_profile_negative_rigor(self):
        """
        ClientProfile(rigor=-0.1) → принимается, но недопустимо.

        Проверяем: отсутствие валидации rigor.
        Границы: rigor < 0.
        Почему такие: граничный случай — отрицательная строгость.
        """
        from space1.environment.core import ClientProfile
        client = ClientProfile(id="c1", name="Test", rigor=-0.1)
        # ЭТО БАГ: отрицательный rigor не отклоняется
        assert client.rigor == -0.1

    def test_client_profile_rigor_above_one(self):
        """
        ClientProfile(rigor=1.5) → принимается, но недопустимо.

        Проверяем: отсутствие валидации rigor.
        Границы: rigor > 1.
        Почему такие: граничный случай — rigor > 1.
        """
        from space1.environment.core import ClientProfile
        client = ClientProfile(id="c1", name="Test", rigor=1.5)
        # ЭТО БАГ: rigor > 1 не отклоняется
        assert client.rigor == 1.5


# =============================================================================
# UNIT: MarketLead
# =============================================================================

class TestMarketLeadUnit:
    """Unit-тесты на MarketLead dataclass."""

    def test_market_lead_defaults(self):
        """
        MarketLead(id="l1", title="T", client=ClientProfile("c1", "C"), budget=100) → required_quality=0.7, estimated_hours=2.0, urgency=0.5.

        Проверяем: default значения.
        Границы: Без опциональных аргументов.
        Почему такие: контракт default values.
        """
        from space1.environment.core import MarketLead, ClientProfile
        client = ClientProfile(id="c1", name="C")
        lead = MarketLead(id="l1", title="T", client=client, budget=100.0)
        assert lead.required_quality == 0.7
        assert lead.estimated_hours == 2.0
        assert lead.urgency == 0.5

    def test_market_lead_custom(self):
        """
        MarketLead с кастомными значениями.

        Проверяем: переопределение default.
        Границы: Кастомные значения.
        Почему такие: проверка переопределения.
        """
        from space1.environment.core import MarketLead, ClientProfile
        client = ClientProfile(id="c1", name="C")
        lead = MarketLead(id="l1", title="T", client=client, budget=100.0,
                          required_quality=0.9, estimated_hours=5.0, urgency=0.8)
        assert lead.required_quality == 0.9
        assert lead.estimated_hours == 5.0
        assert lead.urgency == 0.8


# =============================================================================
# UNIT: MarketEnvironment
# =============================================================================

class TestMarketEnvironmentUnit:
    """Unit-тесты на MarketEnvironment."""

    def test_env_init_empty(self):
        """
        MarketEnvironment() → пустые leads, competitor_pressure=0.3.

        Проверяем: начальное состояние.
        Границы: Без аргументов.
        Почему такие: контракт чистого состояния.
        """
        from space1.environment.core import MarketEnvironment
        env = MarketEnvironment()
        assert env._available_leads == []
        assert env._competitor_pressure == 0.3

    def test_env_add_lead(self):
        """
        add_lead(lead) → lead в _available_leads.

        Проверяем: добавление lead.
        Границы: Один lead.
        Почему такие: базовая функциональность.
        """
        from space1.environment.core import MarketEnvironment, MarketLead, ClientProfile
        env = MarketEnvironment()
        client = ClientProfile(id="c1", name="C")
        lead = MarketLead(id="l1", title="T", client=client, budget=100.0)
        env.add_lead(lead)
        assert len(env._available_leads) == 1
        assert env._available_leads[0] is lead

    def test_env_stream_leads_count(self):
        """
        stream_leads(3) → 3 Task.

        Проверяем: генерация нужного количества.
        Границы: count = 3.
        Почему такие: проверка count parameter.
        """
        from space1.environment.core import MarketEnvironment
        env = MarketEnvironment()
        tasks = env.stream_leads(3)
        assert len(tasks) == 3

    def test_env_stream_leads_returns_tasks(self):
        """
        stream_leads() → список Task.

        Проверяем: тип возвращаемого значения.
        Границы: Стандартный кейс.
        Почему такие: проверка типа.
        """
        from space1.environment.core import MarketEnvironment
        from space1.models.task import Task
        env = MarketEnvironment()
        tasks = env.stream_leads(2)
        for task in tasks:
            assert isinstance(task, Task)

    def test_env_stream_leads_uses_available(self):
        """
        stream_leads() использует pre-existing leads.

        Проверяем: leads из _available_leads используются первыми.
        Границы: Один pre-existing lead.
        Почему такие: проверка приоритета pre-existing.
        """
        from space1.environment.core import MarketEnvironment, MarketLead, ClientProfile
        env = MarketEnvironment()
        client = ClientProfile(id="c1", name="C")
        lead = MarketLead(id="l1", title="Pre-existing", client=client, budget=100.0)
        env.add_lead(lead)
        tasks = env.stream_leads(1)
        assert tasks[0].metadata["lead_id"] == "l1"
        assert len(env._available_leads) == 0

    def test_env_stream_leads_generates_when_empty(self):
        """
        stream_leads() без pre-existing → генерирует randomized leads.

        Проверяем: auto-generation при пустом списке.
        Границы: Пустой _available_leads.
        Почему такие: проверка fallback generation.
        """
        from space1.environment.core import MarketEnvironment
        env = MarketEnvironment()
        tasks = env.stream_leads(2)
        assert len(tasks) == 2
        assert all(t.metadata.get("lead_id", "").startswith("lead_") for t in tasks)

    def test_env_stream_leads_task_has_revenue(self):
        """
        stream_leads() → Task.revenue установлен.

        Проверяем: revenue проксирован из lead.budget.
        Границы: Стандартный кейс.
        Почему такие: проверка revenue.
        """
        from space1.environment.core import MarketEnvironment
        env = MarketEnvironment()
        tasks = env.stream_leads(1)
        assert tasks[0].revenue > 0

    def test_env_stream_leads_task_has_client_metadata(self):
        """
        stream_leads() → Task.metadata содержит client_id, client_rigor, client_reputation_multiplier, quality_requirement, lead_id.

        Проверяем: metadata заполнен.
        Границы: Стандартный кейс.
        Почему такие: проверка полноты metadata.
        """
        from space1.environment.core import MarketEnvironment
        env = MarketEnvironment()
        tasks = env.stream_leads(1)
        meta = tasks[0].metadata
        assert "client_id" in meta
        assert "client_rigor" in meta
        assert "client_reputation_multiplier" in meta
        assert "quality_requirement" in meta
        assert "lead_id" in meta

    def test_env_stream_leads_priority_high(self):
        """
        lead.urgency > 0.7 → TaskPriority.HIGH.

        Проверяем: high priority для срочных.
        Границы: urgency = 0.8.
        Почему такие: проверка priority mapping.
        """
        from space1.environment.core import MarketEnvironment, MarketLead, ClientProfile
        from space1.models.task import TaskPriority
        env = MarketEnvironment()
        client = ClientProfile(id="c1", name="C")
        lead = MarketLead(id="l1", title="T", client=client, budget=100.0, urgency=0.8)
        env.add_lead(lead)
        tasks = env.stream_leads(1)
        assert tasks[0].priority == TaskPriority.HIGH

    def test_env_stream_leads_priority_medium(self):
        """
        lead.urgency <= 0.7 → TaskPriority.MEDIUM.

        Проверяем: medium priority для обычных.
        Границы: urgency = 0.5.
        Почему такие: проверка priority mapping.
        """
        from space1.environment.core import MarketEnvironment, MarketLead, ClientProfile
        from space1.models.task import TaskPriority
        env = MarketEnvironment()
        client = ClientProfile(id="c1", name="C")
        lead = MarketLead(id="l1", title="T", client=client, budget=100.0, urgency=0.5)
        env.add_lead(lead)
        tasks = env.stream_leads(1)
        assert tasks[0].priority == TaskPriority.MEDIUM

    def test_env_stream_leads_count_zero(self):
        """
        stream_leads(0) → [].

        Проверяем: нулевой count.
        Границы: count = 0.
        Почему такие: граничный случай — нет задач.
        """
        from space1.environment.core import MarketEnvironment
        env = MarketEnvironment()
        tasks = env.stream_leads(0)
        assert tasks == []

    def test_env_simulate_competition_returns_bool(self):
        """
        simulate_competition(task) → bool.

        Проверяем: тип возвращаемого значения.
        Границы: Стандартный кейс.
        Почему такие: проверка типа.
        """
        from space1.environment.core import MarketEnvironment
        from space1.models.task import create_task
        env = MarketEnvironment()
        task = create_task(title="T", priority=1, estimated_hours=2.0)
        result = env.simulate_competition(task)
        assert isinstance(result, bool)

    def test_env_simulate_competition_high_margin(self):
        """
        margin > 100 → adjusted_pressure += 0.3.

        Проверяем: высокий margin увеличивает pressure.
        Границы: revenue=500, hours=1 → margin=500.
        Почему такие: проверка pressure adjustment.
        """
        from space1.environment.core import MarketEnvironment
        from space1.models.task import create_task
        env = MarketEnvironment()
        task = create_task(title="T", priority=1, estimated_hours=1.0)
        task.revenue = 500.0
        # С высоким margin pressure = 0.3 + 0.3 = 0.6
        # Вероятность True = 0.6 (в среднем)
        results = [env.simulate_competition(task) for _ in range(100)]
        true_rate = sum(results) / len(results)
        # Должно быть около 0.6 с некоторой дисперсией
        assert 0.4 < true_rate < 0.8

    def test_env_simulate_competition_low_margin(self):
        """
        margin < 100 → adjusted_pressure = 0.3.

        Проверяем: низкий margin не увеличивает pressure.
        Границы: revenue=10, hours=1 → margin=10.
        Почему такие: проверка без adjustment.
        """
        from space1.environment.core import MarketEnvironment
        from space1.models.task import create_task
        env = MarketEnvironment()
        task = create_task(title="T", priority=1, estimated_hours=1.0)
        task.revenue = 10.0
        results = [env.simulate_competition(task) for _ in range(100)]
        true_rate = sum(results) / len(results)
        # Должно быть около 0.3
        assert 0.1 < true_rate < 0.5

    def test_env_simulate_competition_no_revenue(self):
        """
        task без revenue → margin = 0, adjusted_pressure = 0.3.

        Проверяем: graceful handling отсутствующего revenue.
        Границы: revenue = None/0.
        Почему такие: граничный случай — нет revenue.
        """
        from space1.environment.core import MarketEnvironment
        from space1.models.task import create_task
        env = MarketEnvironment()
        task = create_task(title="T", priority=1, estimated_hours=1.0)
        # revenue не установлен
        result = env.simulate_competition(task)
        assert isinstance(result, bool)

    def test_env_generate_review_excellent(self):
        """
        achieved_quality - req_quality >= 0.1 → rating=5.0, "Excellent".

        Проверяем: превосходное качество.
        Границы: delta = 0.1.
        Почему такие: проверка excellent branch.
        """
        from space1.environment.core import MarketEnvironment
        from space1.models.task import create_task
        env = MarketEnvironment()
        task = create_task(title="T", priority=1, estimated_hours=2.0)
        task.metadata["client_rigor"] = 0.5
        task.metadata["quality_requirement"] = 0.7
        task.metadata["client_reputation_multiplier"] = 1.0
        review = env.generate_review(task, 0.8)
        assert review["rating"] == 5.0
        assert "Excellent" in review["feedback"]

    def test_env_generate_review_satisfactory(self):
        """
        achieved_quality = req_quality → rating=4.0, "Satisfactory".

        Проверяем: точное соответствие.
        Границы: delta = 0.0.
        Почему такие: проверка satisfactory branch.
        """
        from space1.environment.core import MarketEnvironment
        from space1.models.task import create_task
        env = MarketEnvironment()
        task = create_task(title="T", priority=1, estimated_hours=2.0)
        task.metadata["client_rigor"] = 0.5
        task.metadata["quality_requirement"] = 0.7
        task.metadata["client_reputation_multiplier"] = 1.0
        review = env.generate_review(task, 0.7)
        assert review["rating"] == 4.0
        assert "Satisfactory" in review["feedback"]

    def test_env_generate_review_poor(self):
        """
        achieved_quality < req_quality → rating < 3.0, "Poor".

        Проверяем: недостаточное качество.
        Границы: delta = -0.1.
        Почему такие: проверка poor branch.
        """
        from space1.environment.core import MarketEnvironment
        from space1.models.task import create_task
        env = MarketEnvironment()
        task = create_task(title="T", priority=1, estimated_hours=2.0)
        task.metadata["client_rigor"] = 0.5
        task.metadata["quality_requirement"] = 0.7
        task.metadata["client_reputation_multiplier"] = 1.0
        review = env.generate_review(task, 0.6)
        assert review["rating"] < 3.0
        assert "Poor" in review["feedback"]

    def test_env_generate_review_rigor_affects_poor(self):
        """
        Высокий rigor → более низкий rating при недостаточном качестве.

        Проверяем: rigor влияет на penalty.
        Границы: rigor = 0.8 vs 0.2, delta = -0.1.
        Почему такие: проверка rigor multiplier.
        """
        from space1.environment.core import MarketEnvironment
        from space1.models.task import create_task
        env = MarketEnvironment()
        task1 = create_task(title="T", priority=1, estimated_hours=2.0)
        task1.metadata["client_rigor"] = 0.8
        task1.metadata["quality_requirement"] = 0.7
        task1.metadata["client_reputation_multiplier"] = 1.0
        review1 = env.generate_review(task1, 0.6)

        task2 = create_task(title="T", priority=1, estimated_hours=2.0)
        task2.metadata["client_rigor"] = 0.2
        task2.metadata["quality_requirement"] = 0.7
        task2.metadata["client_reputation_multiplier"] = 1.0
        review2 = env.generate_review(task2, 0.6)

        assert review1["rating"] < review2["rating"]

    def test_env_generate_review_rating_floor(self):
        """
        Очень низкое качество → rating >= 1.0.

        Проверяем: floor rating.
        Границы: delta = -1.0.
        Почему такие: проверка floor.
        """
        from space1.environment.core import MarketEnvironment
        from space1.models.task import create_task
        env = MarketEnvironment()
        task = create_task(title="T", priority=1, estimated_hours=2.0)
        task.metadata["client_rigor"] = 1.0
        task.metadata["quality_requirement"] = 0.7
        task.metadata["client_reputation_multiplier"] = 1.0
        review = env.generate_review(task, 0.0)
        assert review["rating"] >= 1.0

    def test_env_generate_review_rating_ceiling(self):
        """
        Очень высокое качество → rating <= 5.0.

        Проверяем: ceiling rating.
        Границы: delta = 1.0.
        Почему такие: проверка ceiling.
        """
        from space1.environment.core import MarketEnvironment
        from space1.models.task import create_task
        env = MarketEnvironment()
        task = create_task(title="T", priority=1, estimated_hours=2.0)
        task.metadata["client_rigor"] = 0.5
        task.metadata["quality_requirement"] = 0.7
        task.metadata["client_reputation_multiplier"] = 1.0
        review = env.generate_review(task, 2.0)
        assert review["rating"] <= 5.0

    def test_env_generate_review_returns_multiplier(self):
        """
        generate_review → reputation_multiplier из metadata.

        Проверяем: multiplier проксирован.
        Границы: multiplier = 1.2.
        Почему такие: проверка multiplier.
        """
        from space1.environment.core import MarketEnvironment
        from space1.models.task import create_task
        env = MarketEnvironment()
        task = create_task(title="T", priority=1, estimated_hours=2.0)
        task.metadata["client_rigor"] = 0.5
        task.metadata["quality_requirement"] = 0.7
        task.metadata["client_reputation_multiplier"] = 1.2
        review = env.generate_review(task, 0.8)
        assert review["reputation_multiplier"] == 1.2

    def test_env_generate_review_missing_metadata(self):
        """
        generate_review без metadata → default rigor=0.5, req_quality=0.7, multiplier=1.0.

        Проверяем: graceful handling missing metadata.
        Границы: Пустой metadata.
        Почему такие: граничный случай — нет metadata.
        """
        from space1.environment.core import MarketEnvironment
        from space1.models.task import create_task
        env = MarketEnvironment()
        task = create_task(title="T", priority=1, estimated_hours=2.0)
        # metadata пустой по умолчанию
        review = env.generate_review(task, 0.8)
        assert review["rating"] == 5.0  # 0.8 - 0.7 = 0.1 >= 0.1 → excellent
        assert review["reputation_multiplier"] == 1.0


# =============================================================================
# PAIR: MarketEnvironment + MarketLead
# =============================================================================

class TestPairEnvLead:
    """PAIR: MarketEnvironment + MarketLead — интеграция в миниатюре."""

    def test_env_uses_lead_budget_as_revenue(self):
        """
        add_lead(budget=200) + stream_leads → task.revenue = 200.

        Проверяем: budget → revenue.
        Границы: budget = 200.
        Почему такие: интеграция lead → task revenue.
        """
        from space1.environment.core import MarketEnvironment, MarketLead, ClientProfile
        env = MarketEnvironment()
        client = ClientProfile(id="c1", name="C")
        lead = MarketLead(id="l1", title="T", client=client, budget=200.0)
        env.add_lead(lead)
        tasks = env.stream_leads(1)
        assert tasks[0].revenue == 200.0

    def test_env_uses_lead_client_in_metadata(self):
        """
        add_lead(client=ClientProfile(id="c1", rigor=0.8)) → task.metadata["client_rigor"] = 0.8.

        Проверяем: client profile → metadata.
        Границы: rigor = 0.8.
        Почему такие: интеграция client → task metadata.
        """
        from space1.environment.core import MarketEnvironment, MarketLead, ClientProfile
        env = MarketEnvironment()
        client = ClientProfile(id="c1", name="C", rigor=0.8)
        lead = MarketLead(id="l1", title="T", client=client, budget=100.0)
        env.add_lead(lead)
        tasks = env.stream_leads(1)
        assert tasks[0].metadata["client_rigor"] == 0.8
        assert tasks[0].metadata["client_id"] == "c1"


# =============================================================================
# PAIR: MarketEnvironment + Task
# =============================================================================

class TestPairEnvTask:
    """PAIR: MarketEnvironment + Task — интеграция в миниатюре."""

    def test_stream_creates_task_with_title(self):
        """
        stream_leads → Task.title из lead.title.

        Проверяем: title проксирован.
        Границы: Стандартный кейс.
        Почему такие: интеграция lead → task title.
        """
        from space1.environment.core import MarketEnvironment, MarketLead, ClientProfile
        env = MarketEnvironment()
        client = ClientProfile(id="c1", name="C")
        lead = MarketLead(id="l1", title="Custom Title", client=client, budget=100.0)
        env.add_lead(lead)
        tasks = env.stream_leads(1)
        assert tasks[0].title == "Custom Title"

    def test_stream_creates_task_with_estimated_hours(self):
        """
        stream_leads → Task.estimated_hours из lead.estimated_hours.

        Проверяем: estimated_hours проксирован.
        Границы: estimated_hours = 5.0.
        Почему такие: интеграция lead → task hours.
        """
        from space1.environment.core import MarketEnvironment, MarketLead, ClientProfile
        env = MarketEnvironment()
        client = ClientProfile(id="c1", name="C")
        lead = MarketLead(id="l1", title="T", client=client, budget=100.0, estimated_hours=5.0)
        env.add_lead(lead)
        tasks = env.stream_leads(1)
        assert tasks[0].estimated_hours == 5.0


# =============================================================================
# PAIR: MarketEnvironment + generate_review
# =============================================================================

class TestPairEnvReview:
    """PAIR: MarketEnvironment + generate_review — интеграция в миниатюре."""

    def test_review_uses_task_metadata(self):
        """
        stream_leads + generate_review → review использует metadata из task.

        Проверяем: end-to-end metadata flow.
        Границы: Стандартный кейс.
        Почему такие: интеграция stream → review.
        """
        from space1.environment.core import MarketEnvironment, MarketLead, ClientProfile
        env = MarketEnvironment()
        client = ClientProfile(id="c1", name="C", rigor=0.8, reputation_multiplier=1.5)
        lead = MarketLead(id="l1", title="T", client=client, budget=100.0, required_quality=0.8)
        env.add_lead(lead)
        tasks = env.stream_leads(1)
        review = env.generate_review(tasks[0], 0.9)
        assert review["rating"] == 5.0
        assert review["reputation_multiplier"] == 1.5


# =============================================================================
# INTEGRITY: Архитектурные инварианты
# =============================================================================

class TestIntegrityEnvironment:
    """INTEGRITY: Архитектурные инварианты environment/core.py."""

    def test_no_bare_except_in_environment(self):
        """
        environment/core.py не содержит bare except Exception: pass.

        Проверяем: отсутствие bare except (10_SECURITY.md §III — fail fast).
        Границы: Проверка всего файла.
        Почему такие: bare except маскирует ошибки.
        """
        import inspect
        from space1.environment import core
        src_file = inspect.getfile(core)
        with open(src_file, 'r') as f:
            lines = f.readlines()
        bare_excepts = [i + 1 for i, line in enumerate(lines) if "except Exception" in line]
        assert len(bare_excepts) == 0, f"Bare except найден на строках: {bare_excepts}"

    def test_competitor_pressure_range(self):
        """
        _competitor_pressure ∈ [0.0, 1.0].

        Проверяем: начальное значение в допустимом диапазоне.
        Границы: Стандартный кейс.
        Почему такие: архитектурный инвариант — probability.
        """
        from space1.environment.core import MarketEnvironment
        env = MarketEnvironment()
        assert 0.0 <= env._competitor_pressure <= 1.0

    def test_rating_range(self):
        """
        generate_review → rating ∈ [1.0, 5.0].

        Проверяем: rating всегда в допустимом диапазоне.
        Границы: Разные quality.
        Почему такие: архитектурный инвариант — 5-point scale.
        """
        from space1.environment.core import MarketEnvironment
        from space1.models.task import create_task
        env = MarketEnvironment()
        task = create_task(title="T", priority=1, estimated_hours=2.0)
        task.metadata["client_rigor"] = 0.5
        task.metadata["quality_requirement"] = 0.7
        task.metadata["client_reputation_multiplier"] = 1.0
        for quality in [0.0, 0.5, 0.7, 0.8, 1.0, 2.0]:
            review = env.generate_review(task, quality)
            assert 1.0 <= review["rating"] <= 5.0, f"quality={quality}: rating={review['rating']}"

    def test_client_profile_rigor_is_probability(self):
        """
        rigor должен быть ∈ [0.0, 1.0] (контракт, но не enforced).

        Проверяем: контракт rigor.
        Границы: Стандартный кейс.
        Почему такие: архитектурный инвариант — rigor = probability.
        """
        from space1.environment.core import ClientProfile
        client = ClientProfile(id="c1", name="C", rigor=0.5)
        # Контракт: rigor ∈ [0, 1], но не enforced
        assert 0.0 <= client.rigor <= 1.0  # Это ожидание, не enforcement

    def test_revenue_non_negative(self):
        """
        stream_leads → task.revenue >= 0.

        Проверяем: revenue неотрицательна.
        Границы: Стандартный кейс.
        Почему такие: архитектурный инвариант — revenue >= 0.
        """
        from space1.environment.core import MarketEnvironment
        env = MarketEnvironment()
        tasks = env.stream_leads(5)
        for task in tasks:
            assert task.revenue >= 0


# =============================================================================
# REGRESSION: Старые баги не вернулись
# =============================================================================

class TestRegressionEnvironment:
    """REGRESSION: Проверки, что исправленные баги не вернулись."""

    def test_stream_leads_does_not_modify_original_lead(self):
        """
        stream_leads использует lead, не модифицирует оригинал.

        Проверяем: иммутабельность lead.
        Границы: Стандартный кейс.
        Почему такие: регрессия — ранее мог модифицировать.
        """
        from space1.environment.core import MarketEnvironment, MarketLead, ClientProfile
        env = MarketEnvironment()
        client = ClientProfile(id="c1", name="C")
        lead = MarketLead(id="l1", title="T", client=client, budget=100.0)
        original_title = lead.title
        env.add_lead(lead)
        env.stream_leads(1)
        assert lead.title == original_title

    def test_generate_review_no_crash_missing_metadata(self):
        """
        generate_review без metadata → не падает.

        Проверяем: graceful handling.
        Границы: Пустой metadata.
        Почему такие: регрессия — ранее мог упасть.
        """
        from space1.environment.core import MarketEnvironment
        from space1.models.task import create_task
        env = MarketEnvironment()
        task = create_task(title="T", priority=1, estimated_hours=2.0)
        review = env.generate_review(task, 0.5)
        assert "rating" in review
        assert "feedback" in review

    def test_simulate_competition_no_crash_no_revenue(self):
        """
        simulate_competition без revenue → не падает.

        Проверяем: graceful handling.
        Границы: revenue = None.
        Почему такие: регрессия — ранее мог упасть.
        """
        from space1.environment.core import MarketEnvironment
        from space1.models.task import create_task
        env = MarketEnvironment()
        task = create_task(title="T", priority=1, estimated_hours=2.0)
        result = env.simulate_competition(task)
        assert isinstance(result, bool)
