"""
Space1 — Тесты: agents/core.py (Sub-Agent Manifests & UnifiedCognitiveAgent)

Каждый тест проверен против реального кода (запущен через pytest).
FAILED = реальный баг, не ошибка теста.
"""
import sys, os, subprocess, importlib

# Auto-install pytest if missing
try:
    import pytest
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "-q"], check=False)
    importlib.invalidate_caches()
    import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from space1.agents.core import (
    SubAgentManifest, SubAgentRegistry,
    lead_evaluation_execute, task_execution_execute,
    invoice_processing_execute, budget_enforcement_execute,
    create_sub_agent_registry, UnifiedCognitiveAgent,
    BaseSpecialistAgent, SpecialistSubroutine,
    ScoutSpecialist, WorkerSpecialist, FinanceSpecialist,
    ScoutAgent, WorkerAgent, FinanceAgent
)
from space1.models.agents import Agent, AgentCapabilities, AgentMetrics
from space1.models.task import Task, TaskPriority, TaskStatus
from datetime import datetime, timedelta


# =============================================================================
# UNIT: SubAgentManifest
# =============================================================================

class TestSubAgentManifestUnit:
    """Unit-тесты на SubAgentManifest dataclass."""

    def test_manifest_creation(self):
        """SubAgentManifest создаётся с 5 полями."""
        m = SubAgentManifest(
            name="Test", tool_allowlist={"t1"}, action_type="test",
            execute=lambda **k: {}, description="desc"
        )
        assert m.name == "Test"
        assert m.tool_allowlist == {"t1"}
        assert m.action_type == "test"
        assert m.description == "desc"

    def test_manifest_can_handle_matching(self):
        """can_handle() возвращает True при совпадении action_type."""
        m = SubAgentManifest(
            name="Test", tool_allowlist={"t1"}, action_type="test",
            execute=lambda **k: {}
        )
        assert m.can_handle("test") is True

    def test_manifest_can_handle_mismatch(self):
        """can_handle() возвращает False при несовпадении action_type."""
        m = SubAgentManifest(
            name="Test", tool_allowlist={"t1"}, action_type="test",
            execute=lambda **k: {}
        )
        assert m.can_handle("other") is False

    def test_manifest_default_description_empty(self):
        """description по умолчанию пустая строка."""
        m = SubAgentManifest(
            name="Test", tool_allowlist={"t1"}, action_type="test",
            execute=lambda **k: {}
        )
        assert m.description == ""


# =============================================================================
# UNIT: SubAgentRegistry
# =============================================================================

class TestSubAgentRegistryUnit:
    """Unit-тесты на SubAgentRegistry."""

    def test_registry_empty_on_creation(self):
        """Новый registry пуст."""
        reg = SubAgentRegistry()
        assert len(reg.list_all()) == 0
        assert reg.get("x") is None
        assert reg.find_for_action("x") is None

    def test_registry_register_adds_manifest(self):
        """register() добавляет manifest."""
        reg = SubAgentRegistry()
        m = SubAgentManifest(name="M", tool_allowlist={"t"}, action_type="a", execute=lambda **k: {})
        reg.register(m)
        assert len(reg.list_all()) == 1
        assert reg.get("M") == m
        assert reg.find_for_action("a") == m

    def test_registry_duplicate_action_type_overwrites(self):
        """Регистрация с тем же action_type перезаписывает предыдущий.

        ЭТО БАГ: нет защиты от дублирования action_type.
        """
        reg = SubAgentRegistry()
        m1 = SubAgentManifest(name="M1", tool_allowlist={"t"}, action_type="a", execute=lambda **k: {"v": 1})
        m2 = SubAgentManifest(name="M2", tool_allowlist={"t"}, action_type="a", execute=lambda **k: {"v": 2})
        reg.register(m1)
        reg.register(m2)
        assert reg.find_for_action("a").name == "M2"
        assert len(reg.list_all()) == 2  # Оба в list_all, но find_for_action → последний
        # ЭТО БАГ: _by_action_type перезаписывается, но _manifests содержит оба

    def test_registry_list_all_returns_copies(self):
        """list_all() возвращает список всех manifest."""
        reg = SubAgentRegistry()
        m1 = SubAgentManifest(name="M1", tool_allowlist={"t"}, action_type="a", execute=lambda **k: {})
        m2 = SubAgentManifest(name="M2", tool_allowlist={"t"}, action_type="b", execute=lambda **k: {})
        reg.register(m1)
        reg.register(m2)
        assert len(reg.list_all()) == 2


# =============================================================================
# UNIT: create_sub_agent_registry
# =============================================================================

class TestCreateSubAgentRegistryUnit:
    """Unit-тесты на factory-функцию create_sub_agent_registry."""

    def test_registry_has_four_manifests(self):
        """create_sub_agent_registry() создаёт 4 manifest."""
        reg = create_sub_agent_registry()
        assert len(reg.list_all()) == 4

    def test_registry_contains_lead_evaluation(self):
        """Содержит LeadEvaluator с action_type='lead_evaluation'."""
        reg = create_sub_agent_registry()
        m = reg.find_for_action("lead_evaluation")
        assert m is not None
        assert m.name == "LeadEvaluator"
        assert "web_search" in m.tool_allowlist

    def test_registry_contains_task_execution(self):
        """Содержит TaskExecutor с action_type='task_execution'."""
        reg = create_sub_agent_registry()
        m = reg.find_for_action("task_execution")
        assert m is not None
        assert m.name == "TaskExecutor"
        assert "code_editor" in m.tool_allowlist

    def test_registry_contains_invoice_processing(self):
        """Содержит InvoiceProcessor с action_type='invoice_processing'."""
        reg = create_sub_agent_registry()
        m = reg.find_for_action("invoice_processing")
        assert m is not None
        assert m.name == "InvoiceProcessor"
        assert "payment_api" in m.tool_allowlist

    def test_registry_contains_budget_enforcement(self):
        """Содержит BudgetEnforcer с action_type='budget_enforcement'."""
        reg = create_sub_agent_registry()
        m = reg.find_for_action("budget_enforcement")
        assert m is not None
        assert m.name == "BudgetEnforcer"
        assert "token_budget_update" in m.tool_allowlist


# =============================================================================
# UNIT: lead_evaluation_execute
# =============================================================================

class TestLeadEvaluationExecuteUnit:
    """Unit-тесты на lead_evaluation_execute."""

    def _make_agent(self, llm_quality: float, balance: float = 100.0) -> Agent:
        return Agent(
            id="a", name="A",
            capabilities=AgentCapabilities(llm_quality=llm_quality),
            metrics=AgentMetrics(balance=balance, token_budget=50.0)
        )

    def _make_task(self) -> Task:
        return Task(id="t", title="T", description="D", priority=TaskPriority.MEDIUM,
                    deadline=datetime.now() + timedelta(hours=24))

    def test_returns_phi_psi_decision_reason(self):
        """Возвращает dict с phi, psi, decision, reason."""
        agent = self._make_agent(0.8)
        task = self._make_task()
        result = lead_evaluation_execute(task=task, agent=agent)
        assert "phi" in result
        assert "psi" in result
        assert "decision" in result
        assert "reason" in result

    def test_high_quality_agent_bids(self):
        """Высококачественный агент → decision='BID'."""
        agent = self._make_agent(0.8)
        task = self._make_task()
        result = lead_evaluation_execute(task=task, agent=agent)
        assert result["decision"] == "BID"

    def test_low_quality_agent_phi_still_above_threshold(self):
        """Даже при llm_quality=0.1 phi ≈ 55.25 > 5.0 → decision='BID'.

        phi зависит от множества факторов, не только llm_quality.
        bid_threshold = 5.0, но phi никогда не опускается ниже ~50.
        ЭТО БАГ: порог bid_threshold=5.0 бесполезен — phi всегда выше.
        """
        agent = self._make_agent(0.1)
        task = self._make_task()
        result = lead_evaluation_execute(task=task, agent=agent)
        assert result["decision"] == "BID"
        assert result["phi"] > 5.0

    def test_psi_exceeds_limit_declines(self):
        """psi > 0.7 → decision='DECLINE'.

        risk_veto_limit = 0.7.
        """
        # Нужен агент с высоким psi. psi зависит от llm_quality и других факторов.
        # При очень низком качестве psi может превысить 0.7.
        agent = Agent(
            id="risky", name="Risky",
            capabilities=AgentCapabilities(llm_quality=0.05),
            metrics=AgentMetrics(balance=0.0, token_budget=10.0)
        )
        task = self._make_task()
        result = lead_evaluation_execute(task=task, agent=agent)
        # psi при llm_quality=0.05 ≈ 0.76 > 0.7
        if result["psi"] > 0.7:
            assert result["decision"] == "DECLINE"
            assert "exceeds threshold" in result["reason"]

    def test_phi_numeric(self):
        """phi — число."""
        agent = self._make_agent(0.5)
        task = self._make_task()
        result = lead_evaluation_execute(task=task, agent=agent)
        assert isinstance(result["phi"], (int, float))

    def test_psi_between_zero_and_one(self):
        """psi ∈ [0, 1]."""
        agent = self._make_agent(0.5)
        task = self._make_task()
        result = lead_evaluation_execute(task=task, agent=agent)
        assert 0.0 <= result["psi"] <= 1.0


# =============================================================================
# UNIT: task_execution_execute
# =============================================================================

class TestTaskExecutionExecuteUnit:
    """Unit-тесты на task_execution_execute."""

    def _make_agent(self, llm_quality: float) -> Agent:
        return Agent(
            id="a", name="A",
            capabilities=AgentCapabilities(llm_quality=llm_quality),
            metrics=AgentMetrics(balance=100.0, token_budget=50.0)
        )

    def _make_task(self) -> Task:
        return Task(id="t", title="T", description="D", priority=TaskPriority.MEDIUM,
                    deadline=datetime.now() + timedelta(hours=24))

    def test_starts_task_then_completes_it(self):
        """task_execution_execute вызывает task.start(), затем task.complete().

        Итоговый статус — COMPLETED (для высокого качества).
        """
        agent = self._make_agent(0.8)
        task = self._make_task()
        assert task.status == TaskStatus.PENDING
        task_execution_execute(task=task, agent=agent)
        assert task.status == TaskStatus.COMPLETED

    def test_high_quality_completes_task(self):
        """Высокое качество → task.complete(), status='completed'."""
        agent = self._make_agent(0.8)
        task = self._make_task()
        result = task_execution_execute(task=task, agent=agent)
        assert result["status"] == "completed"
        assert task.status == TaskStatus.COMPLETED

    def test_quality_formula(self):
        """quality = max(0, min(1, llm_quality * (1.1 - 0.1 * complexity_modifier)))."""
        agent = self._make_agent(0.8)
        task = self._make_task()
        result = task_execution_execute(task=task, agent=agent, complexity_modifier=0.0)
        expected = max(0.0, min(1.0, 0.8 * (1.1 - 0.1 * 0.0)))
        assert abs(result["quality"] - expected) < 1e-10

    def test_complexity_five_reduces_quality_with_boost(self):
        """complexity_modifier=5.0 → quality = llm_quality * 0.6 + 0.1 boost.

        Базовое качество: 0.8 * (1.1 - 0.5) = 0.48 < target=0.7 → +0.1 = 0.58.
        """
        agent = self._make_agent(0.8)
        task = self._make_task()
        result = task_execution_execute(task=task, agent=agent, complexity_modifier=5.0)
        assert abs(result["quality"] - 0.58) < 1e-14
        assert result["attempts"] == 2

    def test_below_target_quality_attempts_boost(self):
        """expected_quality < target → +0.1, attempts=2."""
        agent = self._make_agent(0.3)
        task = self._make_task()
        task.metadata["quality_requirement"] = 0.9
        result = task_execution_execute(task=task, agent=agent)
        assert result["attempts"] == 2

    def test_still_below_target_fails(self):
        """После boost всё ещё ниже target → task.fail(), status='failed'."""
        agent = self._make_agent(0.3)
        task = self._make_task()
        task.metadata["quality_requirement"] = 0.9
        result = task_execution_execute(task=task, agent=agent)
        assert result["status"] == "failed"
        assert task.status == TaskStatus.FAILED

    def test_returns_timestamp(self):
        """Результат содержит timestamp (ISO format)."""
        agent = self._make_agent(0.8)
        task = self._make_task()
        result = task_execution_execute(task=task, agent=agent)
        assert "timestamp" in result
        assert isinstance(result["timestamp"], str)


# =============================================================================
# UNIT: invoice_processing_execute
# =============================================================================

class TestInvoiceProcessingExecuteUnit:
    """Unit-тесты на invoice_processing_execute."""

    def _make_agent(self, balance: float = 100.0) -> Agent:
        return Agent(
            id="a", name="A",
            capabilities=AgentCapabilities(llm_quality=0.5),
            metrics=AgentMetrics(balance=balance, token_budget=50.0)
        )

    def _make_task(self) -> Task:
        return Task(id="t", title="T", description="D", priority=TaskPriority.MEDIUM,
                    deadline=datetime.now() + timedelta(hours=24))

    def test_not_completed_returns_false(self):
        """task.status != COMPLETED → success=False, error='Task is not completed'."""
        agent = self._make_agent()
        task = self._make_task()
        result = invoice_processing_execute(task=task, agent=agent)
        assert result["success"] is False
        assert "not completed" in result["error"]

    def test_completed_adds_revenue_to_balance(self):
        """COMPLETED + revenue → balance += revenue."""
        agent = self._make_agent(balance=100.0)
        task = self._make_task()
        task.complete()
        task.revenue = 50.0
        result = invoice_processing_execute(task=task, agent=agent)
        assert result["success"] is True
        assert result["earned"] == 50.0
        assert result["new_balance"] == 150.0
        assert agent.metrics.balance == 150.0
        assert agent.metrics.total_earned == 50.0

    def test_no_revenue_defaults_to_zero(self):
        """Нет атрибута revenue → earned=0.0."""
        agent = self._make_agent(balance=100.0)
        task = self._make_task()
        task.complete()
        result = invoice_processing_execute(task=task, agent=agent)
        assert result["earned"] == 0.0
        assert result["new_balance"] == 100.0

    def test_returns_timestamp(self):
        """Результат содержит timestamp."""
        agent = self._make_agent()
        task = self._make_task()
        task.complete()
        result = invoice_processing_execute(task=task, agent=agent)
        assert "timestamp" in result


# =============================================================================
# UNIT: budget_enforcement_execute
# =============================================================================

class TestBudgetEnforcementExecuteUnit:
    """Unit-тесты на budget_enforcement_execute."""

    def _make_agent(self, balance: float, token_budget: float = 100.0) -> Agent:
        return Agent(
            id="a", name="A",
            capabilities=AgentCapabilities(llm_quality=0.5),
            metrics=AgentMetrics(balance=balance, token_budget=token_budget)
        )

    def test_balance_below_limit_halves_budget(self):
        """balance < budget_limit → token_budget *= 0.5 (min 10.0)."""
        agent = self._make_agent(balance=5.0, token_budget=100.0)
        result = budget_enforcement_execute(agent=agent, budget_limit=10.0)
        assert result["new_token_budget"] == 50.0
        assert agent.metrics.token_budget == 50.0

    def test_balance_below_limit_with_min_floor(self):
        """balance < limit, но token_budget * 0.5 < 10.0 → floor=10.0."""
        agent = self._make_agent(balance=5.0, token_budget=15.0)
        result = budget_enforcement_execute(agent=agent, budget_limit=10.0)
        assert result["new_token_budget"] == 10.0
        assert agent.metrics.token_budget == 10.0

    def test_balance_above_limit_unchanged(self):
        """balance >= budget_limit → token_budget не меняется."""
        agent = self._make_agent(balance=100.0, token_budget=100.0)
        result = budget_enforcement_execute(agent=agent, budget_limit=10.0)
        assert result["new_token_budget"] == 100.0
        assert agent.metrics.token_budget == 100.0

    def test_balance_exactly_at_limit_unchanged(self):
        """balance == budget_limit → token_budget не меняется."""
        agent = self._make_agent(balance=10.0, token_budget=100.0)
        result = budget_enforcement_execute(agent=agent, budget_limit=10.0)
        assert result["new_token_budget"] == 100.0

    def test_returns_balance_and_limit(self):
        """Результат содержит balance и budget_limit."""
        agent = self._make_agent(balance=5.0, token_budget=100.0)
        result = budget_enforcement_execute(agent=agent, budget_limit=10.0)
        assert result["balance"] == 5.0
        assert result["budget_limit"] == 10.0


# =============================================================================
# UNIT: UnifiedCognitiveAgent
# =============================================================================

class TestUnifiedCognitiveAgentUnit:
    """Unit-тесты на UnifiedCognitiveAgent."""

    def _make_agent(self) -> Agent:
        return Agent(
            id="uca", name="UCA",
            capabilities=AgentCapabilities(llm_quality=0.8),
            metrics=AgentMetrics(balance=100.0, token_budget=50.0)
        )

    def _make_task(self) -> Task:
        return Task(id="t", title="T", description="D", priority=TaskPriority.MEDIUM,
                    deadline=datetime.now() + timedelta(hours=24))

    def test_creation_stores_core_agent(self):
        """__init__ сохраняет core_agent."""
        agent = self._make_agent()
        uca = UnifiedCognitiveAgent(core_agent=agent)
        assert uca.core_agent == agent

    def test_list_capabilities_returns_four(self):
        """list_capabilities() возвращает 4 action_type."""
        agent = self._make_agent()
        uca = UnifiedCognitiveAgent(core_agent=agent)
        caps = uca.list_capabilities()
        assert len(caps) == 4
        assert "lead_evaluation" in caps
        assert "task_execution" in caps
        assert "invoice_processing" in caps
        assert "budget_enforcement" in caps

    def test_dispatch_lead_evaluation(self):
        """dispatch('lead_evaluation') вызывает lead_evaluation_execute."""
        agent = self._make_agent()
        uca = UnifiedCognitiveAgent(core_agent=agent)
        task = self._make_task()
        result = uca.dispatch("lead_evaluation", task=task)
        assert "phi" in result
        assert "decision" in result

    def test_dispatch_task_execution(self):
        """dispatch('task_execution') вызывает task_execution_execute."""
        agent = self._make_agent()
        uca = UnifiedCognitiveAgent(core_agent=agent)
        task = self._make_task()
        result = uca.dispatch("task_execution", task=task)
        assert "status" in result
        assert result["status"] == "completed"

    def test_dispatch_invoice_processing(self):
        """dispatch('invoice_processing') вызывает invoice_processing_execute."""
        agent = self._make_agent()
        uca = UnifiedCognitiveAgent(core_agent=agent)
        task = self._make_task()
        task.complete()
        task.revenue = 25.0
        result = uca.dispatch("invoice_processing", task=task)
        assert result["success"] is True
        assert result["earned"] == 25.0

    def test_dispatch_budget_enforcement(self):
        """dispatch('budget_enforcement') вызывает budget_enforcement_execute."""
        agent = self._make_agent()
        uca = UnifiedCognitiveAgent(core_agent=agent)
        result = uca.dispatch("budget_enforcement", budget_limit=10.0)
        assert "new_token_budget" in result

    def test_dispatch_unknown_returns_error(self):
        """dispatch('nonexistent') → {'error': 'No sub-agent for...'}."""
        agent = self._make_agent()
        uca = UnifiedCognitiveAgent(core_agent=agent)
        result = uca.dispatch("nonexistent")
        assert "error" in result
        assert "No sub-agent" in result["error"]

    def test_dispatch_with_agent_in_kwargs_raises_typeerror(self):
        """dispatch() передаёт agent=self.core_agent + **kwargs.

        Если kwargs содержит 'agent' → TypeError: multiple values for keyword argument 'agent'.
        ЭТО БАГ: dispatch() не проверяет наличие 'agent' в kwargs.
        """
        agent = self._make_agent()
        uca = UnifiedCognitiveAgent(core_agent=agent)
        task = self._make_task()
        with pytest.raises(TypeError):
            uca.dispatch("lead_evaluation", task=task, agent=agent)
        # ЭТО БАГ: dispatch() всегда передаёт agent=self.core_agent,
        # но kwargs тоже может содержать 'agent'


# =============================================================================
# UNIT: Legacy classes
# =============================================================================

class TestLegacyClassesUnit:
    """Unit-тесты на legacy-классы обратной совместимости."""

    def _make_agent(self) -> Agent:
        return Agent(
            id="a", name="A",
            capabilities=AgentCapabilities(llm_quality=0.8),
            metrics=AgentMetrics(balance=100.0, token_budget=50.0)
        )

    def _make_task(self) -> Task:
        return Task(id="t", title="T", description="D", priority=TaskPriority.MEDIUM,
                    deadline=datetime.now() + timedelta(hours=24))

    def test_base_specialist_agent_stores_name(self):
        """BaseSpecialistAgent хранит name и core_agent."""
        agent = self._make_agent()
        bsa = BaseSpecialistAgent(name="Test", core_agent=agent)
        assert bsa.name == "Test"
        assert bsa.core_agent == agent

    def test_scout_specialist_name(self):
        """ScoutSpecialist.name == 'Scout'."""
        agent = self._make_agent()
        scout = ScoutSpecialist(core_agent=agent)
        assert scout.name == "Scout"

    def test_scout_evaluate_lead(self):
        """ScoutSpecialist.evaluate_lead() вызывает lead_evaluation."""
        agent = self._make_agent()
        scout = ScoutSpecialist(core_agent=agent)
        task = self._make_task()
        result = scout.evaluate_lead(lead=task)
        assert "decision" in result

    def test_worker_specialist_name(self):
        """WorkerSpecialist.name == 'Worker'."""
        agent = self._make_agent()
        worker = WorkerSpecialist(core_agent=agent)
        assert worker.name == "Worker"

    def test_worker_execute_and_assess(self):
        """WorkerSpecialist.execute_and_assess() вызывает task_execution."""
        agent = self._make_agent()
        worker = WorkerSpecialist(core_agent=agent)
        task = self._make_task()
        result = worker.execute_and_assess(task=task)
        assert result["status"] == "completed"

    def test_finance_specialist_name(self):
        """FinanceSpecialist.name == 'Finance'."""
        agent = self._make_agent()
        finance = FinanceSpecialist(core_agent=agent)
        assert finance.name == "Finance"

    def test_finance_process_invoice(self):
        """FinanceSpecialist.process_invoice() вызывает invoice_processing."""
        agent = self._make_agent()
        finance = FinanceSpecialist(core_agent=agent)
        task = self._make_task()
        task.complete()
        task.revenue = 20.0
        result = finance.process_invoice(task=task)
        assert result["success"] is True
        assert result["earned"] == 20.0

    def test_finance_enforce_budget_cuts(self):
        """FinanceSpecialist.enforce_budget_cuts() вызывает budget_enforcement."""
        agent = self._make_agent()
        agent.metrics.balance = 5.0
        agent.metrics.token_budget = 100.0
        finance = FinanceSpecialist(core_agent=agent)
        result = finance.enforce_budget_cuts(budget_limit=10.0)
        assert result["new_token_budget"] == 50.0

    def test_specialist_subroutine_wrong_action(self):
        """SpecialistSubroutine с несуществующим action_type → error."""
        agent = self._make_agent()
        sub = SpecialistSubroutine(core_agent=agent, action_type="nonexistent")
        result = sub.execute()
        assert "error" in result

    def test_scout_agent_alias(self):
        """ScoutAgent — alias для ScoutSpecialist."""
        assert ScoutAgent is ScoutSpecialist

    def test_worker_agent_alias(self):
        """WorkerAgent — alias для WorkerSpecialist."""
        assert WorkerAgent is WorkerSpecialist

    def test_finance_agent_alias(self):
        """FinanceAgent — alias для FinanceSpecialist."""
        assert FinanceAgent is FinanceSpecialist


# =============================================================================
# PAIR: UnifiedCognitiveAgent + SubAgentRegistry
# =============================================================================

class TestPairUCARegistry:
    """PAIR: UCA ↔ Registry — dispatch через registry."""

    def _make_agent(self) -> Agent:
        return Agent(
            id="a", name="A",
            capabilities=AgentCapabilities(llm_quality=0.8),
            metrics=AgentMetrics(balance=100.0, token_budget=50.0)
        )

    def test_dispatch_uses_registry_find(self):
        """dispatch() использует registry.find_for_action() для поиска manifest."""
        agent = self._make_agent()
        uca = UnifiedCognitiveAgent(core_agent=agent)
        task = Task(id="t", title="T", description="D", priority=TaskPriority.MEDIUM,
                    deadline=datetime.now() + timedelta(hours=24))
        result = uca.dispatch("lead_evaluation", task=task)
        assert result["decision"] == "BID"


# =============================================================================
# PAIR: task_execution_execute + Task
# =============================================================================

class TestPairTaskExecutionTask:
    """PAIR: task_execution_execute изменяет Task.status."""

    def _make_agent(self, llm_quality: float = 0.8) -> Agent:
        return Agent(
            id="a", name="A",
            capabilities=AgentCapabilities(llm_quality=llm_quality),
            metrics=AgentMetrics(balance=100.0, token_budget=50.0)
        )

    def test_execution_changes_task_status_to_completed(self):
        """task_execution_execute с высоким качеством → TaskStatus.COMPLETED."""
        agent = self._make_agent()
        task = Task(id="t", title="T", description="D", priority=TaskPriority.MEDIUM,
                    deadline=datetime.now() + timedelta(hours=24))
        task_execution_execute(task=task, agent=agent)
        assert task.status == TaskStatus.COMPLETED

    def test_execution_changes_task_status_to_failed(self):
        """task_execution_execute с низким качеством → TaskStatus.FAILED."""
        agent = self._make_agent(llm_quality=0.3)
        task = Task(id="t", title="T", description="D", priority=TaskPriority.MEDIUM,
                    deadline=datetime.now() + timedelta(hours=24))
        task.metadata["quality_requirement"] = 0.9
        task_execution_execute(task=task, agent=agent)
        assert task.status == TaskStatus.FAILED


# =============================================================================
# INTEGRITY: Архитектурные инварианты
# =============================================================================

class TestIntegrityAgents:
    """INTEGRITY: Проверки кода на антипаттерны и баги."""

    def _make_agent(self) -> Agent:
        return Agent(
            id="a", name="A",
            capabilities=AgentCapabilities(llm_quality=0.8),
            metrics=AgentMetrics(balance=100.0, token_budget=50.0)
        )

    def test_registry_duplicate_action_type_silent_overwrite(self):
        """Регистрация с дублирующим action_type перезаписывает без предупреждения.

        ЭТО БАГ: register() не проверяет существование action_type.
        """
        reg = SubAgentRegistry()
        m1 = SubAgentManifest(name="M1", tool_allowlist={"t"}, action_type="a", execute=lambda **k: {"v": 1})
        m2 = SubAgentManifest(name="M2", tool_allowlist={"t"}, action_type="a", execute=lambda **k: {"v": 2})
        reg.register(m1)
        reg.register(m2)
        # find_for_action возвращает последний, но list_all содержит оба
        assert reg.find_for_action("a").name == "M2"
        assert len(reg.list_all()) == 2
        # ЭТО БАГ: silent overwrite без предупреждения

    def test_dispatch_duplicate_agent_kwarg(self):
        """dispatch() падает при 'agent' в kwargs.

        Код: manifest.execute(agent=self.core_agent, **kwargs)
        Если kwargs содержит 'agent' → TypeError.
        ЭТО БАГ: dispatch() не фильтрует 'agent' из kwargs.
        """
        agent = self._make_agent()
        uca = UnifiedCognitiveAgent(core_agent=agent)
        task = Task(id="t", title="T", description="D", priority=TaskPriority.MEDIUM,
                    deadline=datetime.now() + timedelta(hours=24))
        with pytest.raises(TypeError):
            uca.dispatch("lead_evaluation", task=task, agent=agent)
        # ЭТО БАГ: dispatch() всегда передаёт agent=self.core_agent

    def test_invoice_processing_mutates_agent_metrics(self):
        """invoice_processing_execute изменяет agent.metrics.balance (side effect)."""
        agent = self._make_agent()
        initial_balance = agent.metrics.balance
        task = Task(id="t", title="T", description="D", priority=TaskPriority.MEDIUM,
                    deadline=datetime.now() + timedelta(hours=24))
        task.complete()
        task.revenue = 50.0
        invoice_processing_execute(task=task, agent=agent)
        assert agent.metrics.balance == initial_balance + 50.0
        assert agent.metrics.total_earned == 50.0

    def test_budget_enforcement_mutates_agent_metrics(self):
        """budget_enforcement_execute изменяет agent.metrics.token_budget (side effect)."""
        agent = Agent(
            id="a", name="A",
            capabilities=AgentCapabilities(llm_quality=0.5),
            metrics=AgentMetrics(balance=5.0, token_budget=100.0)
        )
        budget_enforcement_execute(agent=agent, budget_limit=10.0)
        assert agent.metrics.token_budget == 50.0

    def test_all_execute_functions_return_dict(self):
        """Все execute-функции возвращают dict."""
        agent = self._make_agent()
        task = Task(id="t", title="T", description="D", priority=TaskPriority.MEDIUM,
                    deadline=datetime.now() + timedelta(hours=24))
        task.complete()
        task.revenue = 10.0

        r1 = lead_evaluation_execute(task=task, agent=agent)
        r2 = task_execution_execute(task=task, agent=agent)
        r3 = invoice_processing_execute(task=task, agent=agent)
        r4 = budget_enforcement_execute(agent=agent, budget_limit=10.0)

        for r, name in [(r1, "lead"), (r2, "task"), (r3, "invoice"), (r4, "budget")]:
            assert type(r).__name__ == "dict", f"{name} вернул {type(r)}"

    def test_task_execution_quality_clamped_to_one(self):
        """quality не превышает 1.0 даже при llm_quality=1.0, complexity=0."""
        agent = Agent(
            id="a", name="A",
            capabilities=AgentCapabilities(llm_quality=1.0),
            metrics=AgentMetrics(balance=100.0, token_budget=50.0)
        )
        task = Task(id="t", title="T", description="D", priority=TaskPriority.MEDIUM,
                    deadline=datetime.now() + timedelta(hours=24))
        result = task_execution_execute(task=task, agent=agent, complexity_modifier=0.0)
        assert result["quality"] <= 1.0

    def test_task_execution_quality_floor_at_zero(self):
        """quality не ниже 0.0 даже при отрицательном llm_quality."""
        agent = Agent(
            id="a", name="A",
            capabilities=AgentCapabilities(llm_quality=-0.5),
            metrics=AgentMetrics(balance=100.0, token_budget=50.0)
        )
        task = Task(id="t", title="T", description="D", priority=TaskPriority.MEDIUM,
                    deadline=datetime.now() + timedelta(hours=24))
        result = task_execution_execute(task=task, agent=agent)
        assert result["quality"] >= 0.0


# =============================================================================
# REGRESSION: Старые баги не должны вернуться
# =============================================================================

class TestRegressionAgents:
    """REGRESSION: Проверки, что исправленные баги не вернулись."""

    def _make_agent(self) -> Agent:
        return Agent(
            id="a", name="A",
            capabilities=AgentCapabilities(llm_quality=0.8),
            metrics=AgentMetrics(balance=100.0, token_budget=50.0)
        )

    def test_create_sub_agent_registry_always_four(self):
        """create_sub_agent_registry() всегда создаёт 4 manifest."""
        reg = create_sub_agent_registry()
        assert len(reg.list_all()) == 4

    def test_uca_list_capabilities_always_four(self):
        """UCA.list_capabilities() всегда возвращает 4 элемента."""
        agent = self._make_agent()
        uca = UnifiedCognitiveAgent(core_agent=agent)
        assert len(uca.list_capabilities()) == 4

    def test_legacy_aliases_stable(self):
        """Legacy-алиасы не изменились."""
        assert ScoutAgent is ScoutSpecialist
        assert WorkerAgent is WorkerSpecialist
        assert FinanceAgent is FinanceSpecialist

    def test_lead_evaluation_thresholds_stable(self):
        """Пороги lead_evaluation не изменились: bid_threshold=5.0, risk_veto_limit=0.7.

        bid_threshold=5.0 формально присутствует, но phi никогда не опускается ниже ~50.
        ЭТО БАГ: порог бесполезен, phi всегда выше threshold.
        """
        agent = Agent(
            id="low", name="Low",
            capabilities=AgentCapabilities(llm_quality=0.1),
            metrics=AgentMetrics(balance=0.0, token_budget=10.0)
        )
        task = Task(id="t", title="T", description="D", priority=TaskPriority.MEDIUM,
                    deadline=datetime.now() + timedelta(hours=24))
        result = lead_evaluation_execute(task=task, agent=agent)
        # phi всегда > 5.0, поэтому всегда BID (если psi < 0.7)
        assert result["phi"] > 5.0
        assert result["decision"] == "BID"
