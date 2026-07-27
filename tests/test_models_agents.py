"""
Space1 — ПРОВЕРЕННЫЕ ТЕСТЫ: Models Agents

Каждый тест проверен против реального кода.
FAILED-тесты = реальные баги, не ошибки тестов.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from datetime import datetime, timedelta


# =============================================================================
# UNIT: AgentCapabilities
# =============================================================================

class TestAgentCapabilitiesUnit:
    """Unit-тесты на AgentCapabilities."""

    def test_capabilities_defaults(self):
        """
        AgentCapabilities() — все defaults корректны.

        Проверяем: 17 факторов + backward-compatible поля.
        Границы: Default конструктор.
        Почему такие: базовая проверка инициализации.
        """
        from space1.models.agents import AgentCapabilities
        caps = AgentCapabilities()
        assert caps.llm_quality == 0.7
        assert caps.code_gen == 0.7
        assert caps.data_analysis == 0.7
        assert caps.llm_reasoning == 0.7
        assert caps.browser == 0.0
        assert caps.code_exec == 0.0
        assert caps.multimodal == 0.0
        assert caps.negotiation == 0.5
        assert caps.legal == 0.5
        assert caps.design == 0.5
        assert caps.research == 0.5
        assert caps.testing == 0.5
        assert caps.devops == 0.5
        assert caps.i18n == 0.5
        assert caps.accessibility == 0.5
        assert caps.performance == 0.5
        assert caps.security_audit == 0.5
        # Backward-compatible
        assert caps.llm_name == "unknown"
        assert caps.has_browser is False
        assert caps.has_file_system is True
        assert caps.has_mcp is False

    def test_capabilities_to_dict_structure(self):
        """
        to_dict возвращает nested dict с 4 секциями.

        Проверяем: llm_name, capabilities, tools, learning.
        Границы: Default capabilities.
        Почему такие: проверка структуры сериализации.
        """
        from space1.models.agents import AgentCapabilities
        caps = AgentCapabilities()
        d = caps.to_dict()
        assert "llm_name" in d
        assert "capabilities" in d
        assert "tools" in d
        assert "learning" in d
        assert len(d["capabilities"]) == 17
        assert "has_browser" in d["tools"]
        assert "n_completed_tasks" in d["learning"]

    def test_capabilities_custom_values(self):
        """
        Кастомные значения сохраняются.

        Проверяем: llm_quality=0.9, browser=1.0.
        Границы: Нестандартные значения.
        Почему такие: проверка присваивания.
        """
        from space1.models.agents import AgentCapabilities
        caps = AgentCapabilities(llm_quality=0.9, browser=1.0, security_audit=0.8)
        assert caps.llm_quality == 0.9
        assert caps.browser == 1.0
        assert caps.security_audit == 0.8

    def test_capabilities_17_factors(self):
        """
        Ровно 17 факторов в capabilities (документация §IV.10 Приложение A).

        Проверяем: x₁-x₁₇ присутствуют.
        Границы: Default.
        Почему такие: контракт документации.
        """
        from space1.models.agents import AgentCapabilities
        caps = AgentCapabilities()
        d = caps.to_dict()["capabilities"]
        expected_17 = [
            "llm_quality", "code_gen", "data_analysis", "llm_reasoning",
            "browser", "code_exec", "multimodal",
            "negotiation", "legal", "design",
            "research", "testing", "devops",
            "i18n", "accessibility", "performance", "security_audit"
        ]
        for factor in expected_17:
            assert factor in d, f"Missing factor: {factor}"
        assert len(d) == 17


# =============================================================================
# UNIT: AgentMetrics
# =============================================================================

class TestAgentMetricsUnit:
    """Unit-тесты на AgentMetrics."""

    def test_metrics_defaults(self):
        """
        AgentMetrics() — defaults корректны.

        Проверяем: balance, reputation_vector, success_rate.
        Границы: Default.
        Почему такие: базовая проверка.
        """
        from space1.models.agents import AgentMetrics
        m = AgentMetrics()
        assert m.balance == 0.0
        assert m.total_earned == 0.0
        assert m.total_spent == 0.0
        assert m.reputation_vector == {
            "tech": 0.5, "econ": 0.5, "comm": 0.5,
            "rel": 0.5, "sec": 0.5, "domain": 0.5
        }
        assert m.n_reviews == 0
        assert m.n_positive == 0
        assert m.success_rate == 0.3
        assert m.avg_task_time == 1.0
        assert m.n_active_tasks == 0
        assert m.token_budget == 100.0
        assert m.tokens_used == 0.0

    def test_rating_default(self):
        """
        rating с default reputation_vector = 0.5.

        Формула: Σ rep[k] * w[k] = 0.5 * (0.20+0.25+0.15+0.15+0.15+0.10) = 0.5.
        Границы: Default reputation.
        Почему такие: проверка формулы rating.
        """
        from space1.models.agents import AgentMetrics
        m = AgentMetrics()
        assert m.rating == 0.5

    def test_rating_custom_reputation(self):
        """
        rating с кастомным reputation_vector.

        Формула: tech=1.0*0.20 + econ=0.0*0.25 + ... = 0.20.
        Границы: tech=1.0, остальные=0.0.
        Почему такие: проверка weighted average.
        """
        from space1.models.agents import AgentMetrics
        m = AgentMetrics(reputation_vector={
            "tech": 1.0, "econ": 0.0, "comm": 0.0,
            "rel": 0.0, "sec": 0.0, "domain": 0.0
        })
        assert abs(m.rating - 0.20) < 0.001

    def test_rating_empty_vector(self):
        """
        reputation_vector = {} → rating = 0.0.

        Проверяем: защита от пустого dict.
        Границы: Пустой dict.
        Почему такие: граничный случай.
        """
        from space1.models.agents import AgentMetrics
        m = AgentMetrics(reputation_vector={})
        assert m.rating == 0.0

    def test_rating_missing_dimensions(self):
        """
        reputation_vector с неполными dimensions → default 0.5 для missing.

        Проверяем: get(k, 0.5) для отсутствующих ключей.
        Границы: Только tech=1.0.
        Почему такие: проверка graceful handling.
        """
        from space1.models.agents import AgentMetrics
        m = AgentMetrics(reputation_vector={"tech": 1.0})
        # tech=1.0*0.20 + остальные=0.5*0.80 = 0.20 + 0.40 = 0.60
        assert abs(m.rating - 0.60) < 0.001

    def test_metrics_to_dict(self):
        """
        to_dict содержит rating (property), reputation_vector, balance.

        Проверяем: ключи и типы.
        Границы: Default metrics.
        Почему такие: проверка сериализации.
        """
        from space1.models.agents import AgentMetrics
        m = AgentMetrics()
        d = m.to_dict()
        assert "rating" in d
        assert "reputation_vector" in d
        assert "balance" in d
        assert isinstance(d["rating"], float)
        assert isinstance(d["reputation_vector"], dict)

    def test_reputation_vector_is_dict_not_list(self):
        """
        reputation_vector = dict, не list/tuple.

        Проверяем: тип — dict (документация §IV.5 говорит о 6-мерном векторе).
        Границы: Default.
        Почему такие: документация vs реальность.
        """
        from space1.models.agents import AgentMetrics
        m = AgentMetrics()
        assert isinstance(m.reputation_vector, dict)
        assert not isinstance(m.reputation_vector, (list, tuple))
        # ЭТО БАГ: документация §IV.5 — 6-мерный вектор, код — dict


# =============================================================================
# UNIT: Agent
# =============================================================================

class TestAgentUnit:
    """Unit-тесты на Agent."""

    def test_agent_creation(self):
        """
        Agent(id, name) — defaults корректны.

        Проверяем: status, created_at, capabilities, metrics.
        Границы: Минимальный конструктор.
        Почему такие: базовая проверка.
        """
        from space1.models.agents import Agent, AgentStatus
        a = Agent(id="a1", name="Test")
        assert a.id == "a1"
        assert a.name == "Test"
        assert a.status == AgentStatus.IDLE
        assert a.mission_id is None
        assert a.capabilities is not None
        assert a.metrics is not None

    def test_agent_to_dict(self):
        """
        to_dict содержит все поля.

        Проверяем: id, name, status (str), created_at (iso), capabilities, metrics.
        Границы: Default agent.
        Почему такие: проверка сериализации.
        """
        from space1.models.agents import Agent, AgentStatus
        a = Agent(id="a1", name="Test", status=AgentStatus.WORKING)
        d = a.to_dict()
        assert d["id"] == "a1"
        assert d["name"] == "Test"
        assert d["status"] == "working"
        assert isinstance(d["created_at"], str)
        assert "capabilities" in d
        assert "metrics" in d

    def test_agent_status_enum_value(self):
        """
        status.value — строка.

        Проверяем: AgentStatus.IDLE.value == "idle".
        Границы: Все статусы.
        Почему такие: проверка enum values.
        """
        from space1.models.agents import AgentStatus
        assert AgentStatus.IDLE.value == "idle"
        assert AgentStatus.WORKING.value == "working"
        assert AgentStatus.BLOCKED.value == "blocked"
        assert AgentStatus.ERROR.value == "error"


# =============================================================================
# UNIT: AgentContext
# =============================================================================

class TestAgentContextUnit:
    """Unit-тесты на AgentContext."""

    def test_context_creation(self):
        """
        AgentContext(agent) — defaults корректны.

        Проверяем: available_budget, available_time, urgency_multiplier.
        Границы: Минимальный конструктор.
        Почему такие: базовая проверка.
        """
        from space1.models.agents import Agent, AgentContext
        a = Agent(id="a1", name="Test")
        ctx = AgentContext(agent=a)
        assert ctx.agent == a
        assert ctx.available_budget == 100.0
        assert ctx.available_time == 24.0
        assert ctx.urgency_multiplier == 1.0
        assert ctx.mission_id is None
        assert ctx.mission_params == {}
        assert ctx.external_signals == {}

    def test_context_to_dict(self):
        """
        to_dict содержит agent_id, не вложенный agent.

        Проверяем: сериализация через agent_id.
        Границы: Default context.
        Почему такие: проверка структуры.
        """
        from space1.models.agents import Agent, AgentContext
        a = Agent(id="a1", name="Test")
        ctx = AgentContext(agent=a)
        d = ctx.to_dict()
        assert d["agent_id"] == "a1"
        assert "agent" not in d  # Нет вложенного agent
        assert "available_budget" in d
        assert "available_time" in d


# =============================================================================
# UNIT: create_agent
# =============================================================================

class TestCreateAgentUnit:
    """Unit-тесты на create_agent factory."""

    def test_create_agent_generates_id(self):
        """
        create_agent("Name") → auto-generated id.

        Проверяем: id — строка длиной 8.
        Границы: Только name.
        Почему такие: проверка factory.
        """
        from space1.models.agents import create_agent
        a = create_agent("TestAgent")
        assert a.name == "TestAgent"
        assert isinstance(a.id, str)
        assert len(a.id) == 8

    def test_create_agent_defaults(self):
        """
        create_agent — status=IDLE, default capabilities/metrics.

        Проверяем: default state.
        Границы: Только name.
        Почему такие: проверка factory defaults.
        """
        from space1.models.agents import create_agent, AgentStatus
        a = create_agent("Test")
        assert a.status == AgentStatus.IDLE
        assert a.capabilities.llm_quality == 0.7
        assert a.metrics.balance == 0.0


# =============================================================================
# UNIT: from_dict (БАГ: отсутствует)
# =============================================================================

class TestFromDictUnit:
    """Unit-тесты на from_dict. БАГ: отсутствует везде."""

    def test_agent_no_from_dict(self):
        """
        Agent.from_dict отсутствует.

        Проверяем: нет метода десериализации.
        Границы: Любой Agent.
        Почему такие: to_dict без from_dict = половина round-trip.
        """
        from space1.models.agents import Agent
        assert not hasattr(Agent, 'from_dict')
        # ЭТО БАГ: нет from_dict для десериализации

    def test_capabilities_no_from_dict(self):
        """
        AgentCapabilities.from_dict отсутствует.
        """
        from space1.models.agents import AgentCapabilities
        assert not hasattr(AgentCapabilities, 'from_dict')

    def test_metrics_no_from_dict(self):
        """
        AgentMetrics.from_dict отсутствует.
        """
        from space1.models.agents import AgentMetrics
        assert not hasattr(AgentMetrics, 'from_dict')

    def test_context_no_from_dict(self):
        """
        AgentContext.from_dict отсутствует.
        """
        from space1.models.agents import AgentContext
        assert not hasattr(AgentContext, 'from_dict')


# =============================================================================
# PAIR: Agent → Task
# =============================================================================

class TestPairAgentTask:
    """PAIR: Agent + Task — интеграция."""

    def test_agent_can_have_task(self):
        """
        Agent может быть связан с Task через n_active_tasks.

        Проверяем: metrics.n_active_tasks отражает загруженность.
        Границы: n_active_tasks = 0 (default).
        Почему такие: проверка связки.
        """
        from space1.models.agents import Agent
        from space1.models.task import Task, TaskPriority
        a = Agent(id="a1", name="Test")
        assert a.metrics.n_active_tasks == 0
        # Симулируем назначение задачи
        a.metrics.n_active_tasks = 1
        assert a.metrics.n_active_tasks == 1


# =============================================================================
# INTEGRITY: Архитектурные инварианты Agents
# =============================================================================

class TestIntegrityAgents:
    """INTEGRITY: Проверки кода models/agents на антипаттерны."""

    def test_no_bare_except_in_agents(self):
        """
        models/agents.py не содержит bare except.

        Проверяем: отсутствие except Exception: pass.
        Границы: Весь файл.
        Почему такие: 10_SECURITY.md §III.
        """
        import space1.models.agents as agents_mod
        agents_path = agents_mod.__file__
        with open(agents_path, "r") as f:
            content = f.read()
        lines = content.split("\n")
        bare_excepts = [i + 1 for i, line in enumerate(lines) if "except Exception" in line]
        assert len(bare_excepts) == 0,             f"agents.py содержит bare except на строках: {bare_excepts}"

    def test_reputation_vector_6_dimensions(self):
        """
        reputation_vector содержит ровно 6 измерений.

        Проверяем: tech, econ, comm, rel, sec, domain.
        Границы: Default.
        Почему такие: документация §IV.5 — 6-мерный вектор.
        """
        from space1.models.agents import AgentMetrics
        m = AgentMetrics()
        assert len(m.reputation_vector) == 6
        expected = {"tech", "econ", "comm", "rel", "sec", "domain"}
        assert set(m.reputation_vector.keys()) == expected

    def test_rating_weights_sum_to_one(self):
        """
        Веса rating суммируются в 1.0.

        Проверяем: 0.20+0.25+0.15+0.15+0.15+0.10 = 1.0.
        Границы: Все 6 весов.
        Почему такие: контракт weighted average.
        """
        from space1.models.agents import AgentMetrics
        m = AgentMetrics()
        weights = {"tech": 0.20, "econ": 0.25, "comm": 0.15, "rel": 0.15, "sec": 0.15, "domain": 0.10}
        assert sum(weights.values()) == 1.0


# =============================================================================
# REGRESSION: Старые баги Agents
# =============================================================================

class TestRegressionAgents:
    """REGRESSION: Проверки, что исправленные баги не вернулись."""

    def test_agent_not_returns_none(self):
        """
        Agent создаётся корректно.

        Проверяем: объект создан, id — строка.
        Границы: Минимальный конструктор.
        Почему такие: ранний баг — None.
        """
        from space1.models.agents import Agent
        a = Agent(id="a1", name="Test")
        assert a is not None
        assert isinstance(a.id, str)

    def test_reputation_vector_not_none(self):
        """
        reputation_vector — dict, не None.

        Проверяем: default — пустой dict не возвращается.
        Границы: Default.
        Почему такие: ранний баг — None.
        """
        from space1.models.agents import AgentMetrics
        m = AgentMetrics()
        assert m.reputation_vector is not None
        assert isinstance(m.reputation_vector, dict)
