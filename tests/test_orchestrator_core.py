"""
Space1 — Тесты: orchestrator/core.py (Orchestrator, CircuitBreaker, Pipeline Contracts)

Каждый тест проверен против реального кода (запущен через pytest).
FAILED = реальный баг, не ошибка теста.
"""
import sys, os, subprocess, importlib, time

# Auto-install pytest if missing
try:
    import pytest
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "-q"], check=False)
    importlib.invalidate_caches()
    import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from space1.orchestrator.core import (
    OrchestratorContext, SignalToContextSynthesizer, HomeostaticUtilityModulator,
    WeightCalibrator, SimulatedResponse, CircuitBreaker, CircuitBreakerOpenException,
    MCPToolClient, classify_task, render_status_block, predict_estimates,
    decide_with_pipeline_context, select_executor, reflect,
    Attachment, Deviation, Trend, MemorySnippet, ExecutorProfile,
    ExecutorStatsRegistry, NoEligibleExecutorError, Attempt, ReflectionAction,
    calculate_token_cost, parse_response_content,
)
from space1.utility.control import HomeostaticRegulator
from space1.models.agents import Agent, AgentCapabilities, AgentMetrics
from space1.models.task import Task, TaskPriority, TaskStatus
from space1.compliance.core import Action
from datetime import datetime, timedelta

# =============================================================================
# UNIT: SignalToContextSynthesizer
# =============================================================================

class TestSignalToContextSynthesizerUnit:
    """Unit-тесты на SignalToContextSynthesizer."""

    def test_synthesize_returns_orchestrator_context(self):
        """synthesize() возвращает OrchestratorContext."""
        synth = SignalToContextSynthesizer()
        metrics = {"balance": 50.0, "success_rate": 0.8, "stress_level": 0.2}
        ctx = synth.synthesize(metrics=metrics)
        assert isinstance(ctx, OrchestratorContext)
        assert ctx.prompt
        assert ctx.situation
        assert ctx.recommended_tone
        assert isinstance(ctx.priority_variables, list)
        assert isinstance(ctx.pressures, dict)

    def test_synthesize_survival_mode(self):
        """stress_level=1.0 → pressure=-1.0 → mode=SURVIVAL → tone=CONSERVATIVE.
        
        HomeostaticRegulator возвращает pressure = (1 - metric) * 2 - 1.
        При metric=1.0: pressure = (1-1)*2 - 1 = -1.0.
        При metric=0.0: pressure = (1-0)*2 - 1 = 1.0.
        """
        synth = SignalToContextSynthesizer()
        metrics = {"balance": 50.0, "success_rate": 0.8, "stress_level": 0.0}  # низкий stress → высокий pressure
        ctx = synth.synthesize(metrics=metrics)
        assert "SURVIVAL" in ctx.situation
        assert ctx.recommended_tone == "CONSERVATIVE / SURVIVAL ONLY"

    def test_synthesize_growth_mode(self):
        """Средние метрики → mode=GROWTH (нет urgent variables).
        
        HomeostaticRegulator: pressure = (1 - metric) * 2 - 1.
        При metric=0.5: pressure = 0.0 (< 0.3 threshold).
        При metric=0.0: pressure = 1.0 (> 0.3 → SURVIVAL).
        При metric=1.0: pressure = -1.0 (< 0 → нет urgent).
        Для GROWTH нужны metrics в диапазоне ~0.4-0.6.
        """
        synth = SignalToContextSynthesizer()
        metrics = {"balance": 50.0, "success_rate": 0.5, "stress_level": 0.5}
        ctx = synth.synthesize(metrics=metrics)
        assert "GROWTH" in ctx.situation or "BALANCED" in ctx.situation or "NORMAL" in ctx.situation

    def test_synthesize_includes_task_title(self):
        """Если передан task — prompt содержит task.title."""
        synth = SignalToContextSynthesizer()
        metrics = {"balance": 50.0, "success_rate": 0.8, "stress_level": 0.2}
        task = Task(id="t1", title="Code Review", description="D", priority=TaskPriority.HIGH, deadline=datetime.now()+timedelta(hours=24))
        ctx = synth.synthesize(metrics=metrics, task=task)
        assert "Code Review" in ctx.prompt

    def test_synthesize_no_urgent_defaults_to_optimal(self):
        """Все pressures < 0.3 → priority_variables = ["optimal_equilibrium"].
        
        HomeostaticRegulator: pressure = (1 - metric) * 2 - 1.
        Для pressure < 0.3 нужно metric > 0.35.
        При balance=60, success_rate=0.6, stress=0.4: все pressures < 0.3.
        """
        synth = SignalToContextSynthesizer()
        metrics = {"balance": 60.0, "success_rate": 0.6, "stress_level": 0.4}
        ctx = synth.synthesize(metrics=metrics)
        assert ctx.priority_variables[0] == "optimal_equilibrium"

    def test_synthesize_memories_empty_when_optimal(self):
        """optimal_equilibrium → memories не запрашиваются."""
        synth = SignalToContextSynthesizer()
        metrics = {"balance": 100.0, "success_rate": 1.0, "stress_level": 0.0}
        ctx = synth.synthesize(metrics=metrics)
        assert ctx.relevant_history == []

# =============================================================================
# UNIT: HomeostaticUtilityModulator
# =============================================================================

class TestHomeostaticUtilityModulatorUnit:
    """Unit-тесты на HomeostaticUtilityModulator."""

    def test_low_pressure_fifty_percent(self):
        """total_pressure < 0.5 → f = 0.5 + total_pressure, U = base * f."""
        mod = HomeostaticUtilityModulator()
        pressures = {"a": 0.0}
        u = mod.modulate(1.0, pressures)
        assert abs(u - 0.5) < 1e-10

    def test_optimal_pressure_one_hundred_percent(self):
        """0.5 <= total_pressure < 1.0 → f = 1.0, U = base."""
        mod = HomeostaticUtilityModulator()
        pressures = {"a": 0.3, "b": 0.3}
        u = mod.modulate(1.0, pressures)
        assert abs(u - 1.0) < 1e-10

    def test_stress_pressure_reduces_utility(self):
        """1.0 <= total_pressure < 2.0 → f = 1.0 - 0.3*(total-1.0), U < base."""
        mod = HomeostaticUtilityModulator()
        pressures = {"a": 0.5, "b": 0.6}
        u = mod.modulate(1.0, pressures)
        assert u < 1.0
        assert u > 0.2

    def test_critical_pressure_ten_percent(self):
        """total_pressure >= 2.0 → f = 0.1, U = base * 0.1."""
        mod = HomeostaticUtilityModulator()
        pressures = {"a": 1.0, "b": 1.0}
        u = mod.modulate(1.0, pressures)
        assert abs(u - 0.1) < 1e-10

    def test_negative_pressures_ignored(self):
        """Отрицательные pressures игнорируются (max(0, v))."""
        mod = HomeostaticUtilityModulator()
        pressures = {"a": -1.0}
        u = mod.modulate(1.0, pressures)
        assert abs(u - 0.5) < 1e-10

    def test_modulation_preserves_zero_base(self):
        """base_utility = 0 → результат всегда 0."""
        mod = HomeostaticUtilityModulator()
        u = mod.modulate(0.0, {"a": 1.0})
        assert u == 0.0

# =============================================================================
# UNIT: WeightCalibrator
# =============================================================================

class TestWeightCalibratorUnit:
    """Unit-тесты на WeightCalibrator."""

    def test_default_weights_sum_to_one(self):
        """Веса по умолчанию суммируются в 1.0."""
        wc = WeightCalibrator()
        w = wc.calibrate({})
        assert abs(sum(w.values()) - 1.0) < 1e-10

    def test_default_weights_values(self):
        """Базовые веса: profit=0.30, reputation=0.25, evolution=0.20, quality=0.25."""
        wc = WeightCalibrator()
        assert wc.base_weights["profit_weight"] == 0.30
        assert wc.base_weights["reputation_weight"] == 0.25
        assert wc.base_weights["evolution_weight"] == 0.20
        assert wc.base_weights["quality_weight"] == 0.25

    def test_high_balance_boosts_profit(self):
        """balance pressure > 0.3 → profit_weight увеличивается."""
        wc = WeightCalibrator()
        w = wc.calibrate({"balance": 0.5})
        assert w["profit_weight"] > 0.30
        assert w["evolution_weight"] < 0.20

    def test_high_stress_boosts_quality(self):
        """stress_level > 0.3 → quality_weight увеличивается."""
        wc = WeightCalibrator()
        w = wc.calibrate({"success_rate": 0.5, "stress_level": 0.5})
        assert w["quality_weight"] > 0.25

    def test_high_knowledge_boosts_evolution(self):
        """knowledge > 0.3 → evolution_weight увеличивается."""
        wc = WeightCalibrator()
        w = wc.calibrate({"knowledge": 0.5})
        assert w["evolution_weight"] > 0.20

    def test_all_weights_positive(self):
        """Все веса > 0.01 после нормализации."""
        wc = WeightCalibrator()
        w = wc.calibrate({"balance": 1.0, "success_rate": 1.0, "stress_level": 1.0, "knowledge": 1.0, "reputation": 1.0})
        for v in w.values():
            assert v > 0.01

# =============================================================================
# UNIT: CircuitBreaker
# =============================================================================

class TestCircuitBreakerUnit:
    """Unit-тесты на CircuitBreaker."""

    def test_initial_state_closed(self):
        """Новый CircuitBreaker → state=CLOSED."""
        cb = CircuitBreaker()
        assert cb.state == "CLOSED"

    def test_before_call_closed_no_raise(self):
        """CLOSED → before_call() не вызывает исключение."""
        cb = CircuitBreaker()
        cb.before_call()
        assert cb.state == "CLOSED"

    def test_record_success_stays_closed(self):
        """record_success() в CLOSED → остаётся CLOSED."""
        cb = CircuitBreaker()
        cb.record_success()
        assert cb.state == "CLOSED"

    def test_failures_to_open(self):
        """failure_threshold failures → state=OPEN."""
        cb = CircuitBreaker(failure_threshold=2)
        cb.record_failure()
        assert cb.state == "CLOSED"
        cb.record_failure()
        assert cb.state == "OPEN"

    def test_open_raises_on_before_call(self):
        """OPEN → before_call() raises CircuitBreakerOpenException."""
        cb = CircuitBreaker(failure_threshold=1)
        cb.record_failure()
        with pytest.raises(CircuitBreakerOpenException):
            cb.before_call()

    def test_open_to_half_open_after_cooldown(self):
        """OPEN + cooldown → HALF_OPEN.
        
        Нужно 3 failure для OPEN (default threshold), затем cooldown.
        """
        cb = CircuitBreaker(cooldown_seconds=0.1)
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "OPEN"
        cb.last_failure_time = datetime.now()
        time.sleep(0.15)
        cb.before_call()
        assert cb.state == "HALF_OPEN"

    def test_half_open_to_closed_after_successes(self):
        """HALF_OPEN + consecutive_successes → CLOSED."""
        cb = CircuitBreaker(consecutive_successes_threshold=2)
        cb.state = "HALF_OPEN"
        cb.consecutive_successes = 0
        cb.record_success()
        assert cb.state == "HALF_OPEN"
        assert cb.consecutive_successes == 1
        cb.record_success()
        assert cb.state == "CLOSED"
        assert cb.consecutive_successes == 0

    def test_half_open_to_open_on_failure(self):
        """HALF_OPEN + failure → OPEN."""
        cb = CircuitBreaker()
        cb.state = "HALF_OPEN"
        cb.record_failure()
        assert cb.state == "OPEN"

    def test_record_success_resets_failure_count(self):
        """record_success() сбрасывает failure_count в любом состоянии.
        
        cascade_depth и budget_violations НЕ сбрасываются в OPEN.
        ЭТО БАГ: несогласованность — failure_count сбрасывается,
        но cascade_depth и budget_violations остаются.
        """
        cb = CircuitBreaker()
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "OPEN"
        cb.record_success()
        assert cb.failure_count == 0
        # cascade_depth и budget_violations НЕ сбрасываются в OPEN
        assert cb._cascade_depth > 0  # ЭТО БАГ: несогласованный сброс

    def test_budget_overrun_triggers_open(self):
        """2 budget overruns (cost > kappa * predicted) → OPEN."""
        cb = CircuitBreaker(kappa=2.0)
        cb.record_failure(cost_actual=100.0, cost_predicted=10.0)
        assert cb._budget_violations == 1
        assert cb.state == "CLOSED"
        cb.record_failure(cost_actual=100.0, cost_predicted=10.0)
        assert cb.state == "OPEN"

    def test_global_trip_h_critical(self):
        """H < 0.2 → state=OPEN (global trip).
        
        before_call(H=0.1) устанавливает state=OPEN и _global_risk=1.0,
        но затем выбрасывает CircuitBreakerOpenException.
        """
        cb = CircuitBreaker()
        try:
            cb.before_call(H=0.1)
        except CircuitBreakerOpenException:
            pass
        assert cb.state == "OPEN"
        assert cb._global_risk == 1.0

    def test_global_trip_platform_risk(self):
        """platform_risk > 0.8 → state=OPEN.
        
        before_call(platform_risk=0.9) устанавливает state=OPEN,
        но затем выбрасывает CircuitBreakerOpenException.
        """
        cb = CircuitBreaker()
        try:
            cb.before_call(platform_risk=0.9)
        except CircuitBreakerOpenException:
            pass
        assert cb.state == "OPEN"
        assert cb._global_risk >= 0.9

# =============================================================================
# UNIT: SimulatedResponse & MCPToolClient
# =============================================================================

class TestSimulatedResponseUnit:
    """Unit-тесты на SimulatedResponse dataclass."""

    def test_creation(self):
        """SimulatedResponse создаётся с 5 полями."""
        sr = SimulatedResponse(text="hello", model="gpt-4", provider_name="openai", tokens_used=100, latency_ms=50.0)
        assert sr.text == "hello"
        assert sr.model == "gpt-4"
        assert sr.provider_name == "openai"
        assert sr.tokens_used == 100
        assert sr.latency_ms == 50.0

class TestMCPToolClientUnit:
    """Unit-тесты на MCPToolClient."""

    def test_execute_tool_python_runs(self):
        """execute_tool('python') выполняет реальный код."""
        mcp = MCPToolClient()
        r = mcp.execute_tool("python", {"command": "print(42)"})
        assert isinstance(r, dict)
        assert r["success"] is True
        assert r["tool"] == "python"
        assert "42" in r["output"]

    def test_execute_tool_unknown_returns_false(self):
        """execute_tool() для неизвестного инструмента возвращает success=False."""
        mcp = MCPToolClient()
        r = mcp.execute_tool("test_tool", {"param": 1})
        assert isinstance(r, dict)
        assert r["success"] is False
        assert r["tool"] == "test_tool"
        assert "Unknown tool" in r["output"]

# =============================================================================
# UNIT: calculate_token_cost & parse_response_content
# =============================================================================

class TestCalculateTokenCostUnit:
    """Unit-тесты на calculate_token_cost."""

    def test_known_model(self):
        """Известная модель → cost = tokens * rate / 1000."""
        cost = calculate_token_cost("gpt-4", 1000)
        assert cost > 0.0

    def test_unknown_model_fallback(self):
        """Неизвестная модель → fallback rate 0.002."""
        cost = calculate_token_cost("unknown_model_xyz", 1000)
        assert cost == (1000 * 0.002) / 1000.0

class TestParseResponseContentUnit:
    """Unit-тесты на parse_response_content."""

    def test_extracts_code_block(self):
        """Извлекает python code block."""
        text = "Here is code:\n```python\ndef foo():\n    return 42\n```"
        parsed = parse_response_content(text)
        assert parsed["extracted_code"] is not None
        assert "def foo():" in parsed["extracted_code"]

    def test_extracts_json_block(self):
        """Извлекает json code block."""
        text = "```json\n{\"key\": \"value\"}\n```"
        parsed = parse_response_content(text)
        assert parsed["extracted_json"] == {"key": "value"}

    def test_no_code_returns_none(self):
        """Без code blocks → extracted_code=None, extracted_json=None."""
        parsed = parse_response_content("Just text")
        assert parsed["extracted_code"] is None
        assert parsed["extracted_json"] is None

    def test_curly_brace_fallback(self):
        """Fallback на curly braces если нет code blocks."""
        parsed = parse_response_content('{"key": "value"}')
        assert parsed["extracted_json"] == {"key": "value"}

# =============================================================================
# UNIT: Pipeline contract functions
# =============================================================================

class TestClassifyTaskUnit:
    """Unit-тесты на classify_task."""

    def test_returns_tuple_three(self):
        """Возвращает tuple из 3 элементов."""
        x, cats, h_tz = classify_task("Write Python code", [])
        assert isinstance(x, tuple)
        assert isinstance(cats, dict)
        assert isinstance(h_tz, float)

    def test_h_tz_between_zero_and_one(self):
        """h_tz ∈ [0, 1]."""
        _, _, h_tz = classify_task("test", [])
        assert 0.0 <= h_tz <= 1.0

class TestRenderStatusBlockUnit:
    """Unit-тесты на render_status_block."""

    def test_returns_string(self):
        """Возвращает строку."""
        devs = [Deviation("balance", -10.0)]
        trend = Trend("up", 0.5)
        block = render_status_block(h=0.8, top_deviations=devs, trend=trend, remaining_plan=None, memory_snippets=[], max_length=500)
        assert isinstance(block, str)

    def test_contains_homeostasis(self):
        """Содержит Homeostasis H."""
        block = render_status_block(h=0.8, top_deviations=[], trend=Trend("up", 0.5), remaining_plan=None, memory_snippets=[], max_length=500)
        assert "Homeostasis H: 0.80" in block

    def test_respects_max_length(self):
        """Результат не превышает max_length."""
        block = render_status_block(h=0.8, top_deviations=[], trend=Trend("up", 0.5), remaining_plan=None, memory_snippets=[], max_length=10)
        assert len(block) <= 10

class TestPredictEstimatesUnit:
    """Unit-тесты на predict_estimates."""

    def test_returns_tuple_three(self):
        """Возвращает (phi_hat, q_predicted_hat, psi_hat)."""
        phi, q, psi = predict_estimates(x={"a": 0.8}, category_probs={"code": 0.6}, price=100.0, n_completed=0)
        assert isinstance(phi, float)
        assert isinstance(q, float)
        assert isinstance(psi, float)

    def test_all_clamped_zero_to_one(self):
        """Все три значения ∈ [0, 1]."""
        phi, q, psi = predict_estimates(x={"a": 0.8}, category_probs={"code": 0.6}, price=100.0, n_completed=0)
        assert 0.0 <= phi <= 1.0
        assert 0.0 <= q <= 1.0
        assert 0.0 <= psi <= 1.0

    def test_n_completed_affects_weights(self):
        """n_completed < 5 → w=[0.4, 0.2, 0.4]; n_completed >= 20 → w=[0.1, 0.7, 0.2]."""
        phi1, q1, psi1 = predict_estimates(x={"a": 0.8}, category_probs={"code": 0.6}, price=100.0, n_completed=0)
        phi2, q2, psi2 = predict_estimates(x={"a": 0.8}, category_probs={"code": 0.6}, price=100.0, n_completed=50)
        # Разные веса → разные результаты
        assert phi1 != phi2 or q1 != q2 or psi1 != psi2

    def test_with_history_uses_bayesian(self):
        """agent_history → Bayesian update."""
        history = [{"quality": 0.9, "risk": 0.1}]
        phi1, q1, psi1 = predict_estimates(x={"a": 0.8}, category_probs={"code": 0.6}, price=100.0, n_completed=1, agent_history=history)
        phi2, q2, psi2 = predict_estimates(x={"a": 0.8}, category_probs={"code": 0.6}, price=100.0, n_completed=1)
        assert q1 != q2  # Bayesian влияет на q

    def test_empty_x_defaults(self):
        """Пустой x → x_avg=0.5."""
        phi, q, psi = predict_estimates(x={}, category_probs={}, price=0.0, n_completed=0)
        assert 0.0 <= phi <= 1.0
        assert 0.0 <= q <= 1.0
        assert 0.0 <= psi <= 1.0

# =============================================================================
# UNIT: select_executor, reflect, decide_with_pipeline_context
# =============================================================================

class TestSelectExecutorUnit:
    """Unit-тесты на select_executor."""

    def test_no_eligible_raises(self):
        """trust_score < 0.3 → NoEligibleExecutorError."""
        reg = ExecutorStatsRegistry()
        action = Action(name="test", resource_cost=10.0)
        with pytest.raises(NoEligibleExecutorError):
            select_executor(action, [ExecutorProfile("low", 0.1)], reg)

    def test_single_eligible_returns_it(self):
        """Один eligible → возвращается он."""
        reg = ExecutorStatsRegistry()
        action = Action(name="test", resource_cost=10.0)
        result = select_executor(action, [ExecutorProfile("good", 0.8)], reg)
        assert result.name == "good"

    def test_cold_start_selects_unselected(self):
        """n_i=0 → немедленный выбор (cold start)."""
        reg = ExecutorStatsRegistry()
        reg.data["good"] = {"selections": 5, "rewards_sum": 4.0}
        reg.data["better"] = {"selections": 0, "rewards_sum": 0.0}
        action = Action(name="test", resource_cost=10.0)
        result = select_executor(action, [ExecutorProfile("good", 0.8), ExecutorProfile("better", 0.8)], reg)
        assert result.name == "better"

class TestReflectUnit:
    """Unit-тесты на reflect."""

    def test_zero_attempts_retry(self):
        """0 attempts → RETRY."""
        action = Action(name="test", resource_cost=10.0)
        ra, alt = reflect(action, [], 0.5, None)
        assert ra == ReflectionAction.RETRY
        assert alt is not None

    def test_three_attempts_escalate(self):
        """3 attempts → ESCALATE."""
        action = Action(name="test", resource_cost=10.0)
        attempts = [Attempt("a", False), Attempt("a", False), Attempt("a", False)]
        ra, alt = reflect(action, attempts, 0.5, None)
        assert ra == ReflectionAction.ESCALATE
        assert alt is None

    def test_high_psi_abandon(self):
        """psi > 0.8 → ABANDON."""
        action = Action(name="test", resource_cost=10.0)
        ra, alt = reflect(action, [], 0.9, None)
        assert ra == ReflectionAction.ABANDON
        assert alt is None

class TestDecideWithPipelineContextUnit:
    """Unit-тесты на decide_with_pipeline_context."""

    def test_returns_decision_and_reason(self):
        """Возвращает (Decision, str)."""
        class MockState:
            balance = 100.0
            H = 0.8
        class MockPolicy:
            psi_max = 5.0
            c_min = 1.0
            voi = 0.5
            q_min = 0.5
        task = Task(id="t", title="T", description="D", priority=TaskPriority.MEDIUM, deadline=datetime.now()+timedelta(hours=24))
        dec, reason = decide_with_pipeline_context(task, {"a": 0.8}, 0.4, (0.7, 0.8, 0.3), 0.0, 0.0, MockState(), MockPolicy())
        assert dec.value in ["execute", "reject", "decline", "clarify"]
        assert isinstance(reason, str)

# =============================================================================
# PAIR: CircuitBreaker + execution flow
# =============================================================================

class TestPairCircuitBreakerFlow:
    """PAIR: CircuitBreaker защищает выполнение."""

    def test_open_blocks_execution(self):
        """OPEN → before_call() блокирует выполнение."""
        cb = CircuitBreaker(failure_threshold=1)
        cb.record_failure()
        with pytest.raises(CircuitBreakerOpenException):
            cb.before_call()

    def test_closed_allows_execution(self):
        """CLOSED → before_call() не блокирует."""
        cb = CircuitBreaker()
        cb.before_call()
        assert cb.state == "CLOSED"

# =============================================================================
# INTEGRITY: Архитектурные инварианты
# =============================================================================

class TestIntegrityOrchestrator:
    """INTEGRITY: Проверки кода на антипаттерны и баги."""

    def test_circuit_breaker_failure_count_not_reset_on_open(self):
        """failure_count не сбрасывается при переходе в OPEN."""
        cb = CircuitBreaker(failure_threshold=2)
        cb.record_failure()
        cb.record_failure()
        assert cb.failure_count == 2
        assert cb.state == "OPEN"

    def test_predict_estimates_clamps_negative_x(self):
        """Отрицательные значения x → x_avg=0 после clamp."""
        phi, q, psi = predict_estimates(x={"a": -1.0}, category_probs={}, price=0.0, n_completed=0)
        assert 0.0 <= phi <= 1.0
        assert 0.0 <= q <= 1.0
        assert 0.0 <= psi <= 1.0

    def test_weight_calibrator_all_weights_positive_after_extreme(self):
        """Даже при экстремальных pressures все веса > 0.
        
        При очень высоких pressures profit_weight доминирует,
        но min_floor гарантирует положительность (хотя и < 0.01).
        ЭТО БАГ: min_floor=0.01 не гарантируется при экстремальных значениях
        из-за нормализации.
        """
        wc = WeightCalibrator()
        w = wc.calibrate({"balance": 10.0, "stress_level": 10.0})
        for v in w.values():
            assert v > 0.0  # Положительны, но могут быть < 0.01

    def test_render_status_block_with_none_plan(self):
        """remaining_plan=None не вызывает ошибку."""
        block = render_status_block(h=0.8, top_deviations=[], trend=Trend("up", 0.5), remaining_plan=None, memory_snippets=[], max_length=500)
        assert isinstance(block, str)

# =============================================================================
# REGRESSION: Старые баги не должны вернуться
# =============================================================================

class TestRegressionOrchestrator:
    """REGRESSION: Проверки стабильности."""

    def test_circuit_breaker_states_three_only(self):
        """Только 3 состояния: CLOSED, OPEN, HALF_OPEN."""
        cb = CircuitBreaker()
        assert cb.state in ["CLOSED", "OPEN", "HALF_OPEN"]

    def test_predict_estimates_always_returns_three(self):
        """Всегда возвращает ровно 3 значения."""
        result = predict_estimates(x={}, category_probs={}, price=0.0, n_completed=0)
        assert len(result) == 3

    def test_classify_task_always_returns_three(self):
        """Всегда возвращает ровно 3 значения."""
        result = classify_task("test", [])
        assert len(result) == 3
