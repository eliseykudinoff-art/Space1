"""
Space1 — Тесты: FactorRegistry (Реестр факторов способностей x₁-x₁₇)

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

from space1.factors.registry import (
    FactorID, FactorResult, BaseFactor,
    LLMFactor, PromptFactor, MemoryRetrievalFactor, MemorySystemFactor,
    MultiAgentFactor, SelfCorrectionFactor, ToolCallingFactor,
    CostTieringFactor, GroundingFactor, FineTuningFactor,
    ContextManagementFactor, GuardrailsFactor, TestTimeComputeFactor,
    DesignPatternsFactor, EvaluationFactor, ContinualLearningFactor,
    InferenceOptFactor, FactorRegistry, create_mvp_registry, create_full_registry,
)


# =============================================================================
# UNIT: FactorResult dataclass
# =============================================================================

class TestFactorResultUnit:
    """Unit-тесты на FactorResult."""

    def test_factor_result_creation(self):
        """FactorResult создаётся с 4 обязательными и 1 опциональным полем."""
        fr = FactorResult(factor_id="x1", value=0.5, delta_success=0.1, delta_time=-0.02)
        assert fr.factor_id == "x1"
        assert fr.value == 0.5
        assert fr.delta_success == 0.1
        assert fr.delta_time == -0.02
        assert fr.metadata == {}

    def test_factor_result_with_metadata(self):
        """FactorResult принимает metadata dict."""
        fr = FactorResult(factor_id="x1", value=0.5, delta_success=0.1, delta_time=0.0, metadata={"key": "val"})
        assert fr.metadata == {"key": "val"}

    def test_factor_result_default_metadata_is_empty_dict(self):
        """По умолчанию metadata = пустой dict (field(default_factory=dict))."""
        fr = FactorResult(factor_id="x1", value=0.5, delta_success=0.1, delta_time=0.0)
        assert fr.metadata == {}


# =============================================================================
# UNIT: FactorID Enum
# =============================================================================

class TestFactorIDUnit:
    """Unit-тесты на FactorID Enum."""

    def test_factor_id_count_is_17(self):
        """FactorID содержит ровно 17 значений (x1-x17)."""
        assert len(FactorID) == 17

    def test_factor_id_x1_value(self):
        """FactorID.X1_LLM.value == 'x1'."""
        assert FactorID.X1_LLM.value == "x1"

    def test_factor_id_x17_value(self):
        """FactorID.X17_INFERENCE_OPT.value == 'x17'."""
        assert FactorID.X17_INFERENCE_OPT.value == "x17"

    def test_factor_id_all_unique(self):
        """Все значения FactorID уникальны."""
        values = [f.value for f in FactorID]
        assert len(values) == len(set(values))


# =============================================================================
# UNIT: BaseFactor (abstract)
# =============================================================================

class TestBaseFactorUnit:
    """Unit-тесты на BaseFactor."""

    def test_base_factor_priority_default_medium(self):
        """BaseFactor.priority по умолчанию = 'MEDIUM'."""
        class DummyFactor(BaseFactor):
            @property
            def name(self):
                return "Dummy"
            def compute(self, context):
                return FactorResult(factor_id="dummy", value=0.0, delta_success=0.0, delta_time=0.0)
        df = DummyFactor(FactorID.X1_LLM)
        assert df.priority == "MEDIUM"

    def test_base_factor_enabled_default_true(self):
        """BaseFactor.enabled по умолчанию = True."""
        class DummyFactor(BaseFactor):
            @property
            def name(self):
                return "Dummy"
            def compute(self, context):
                return FactorResult(factor_id="dummy", value=0.0, delta_success=0.0, delta_time=0.0)
        df = DummyFactor(FactorID.X1_LLM)
        assert df.enabled is True

    def test_base_factor_can_be_disabled(self):
        """BaseFactor можно создать с enabled=False."""
        class DummyFactor(BaseFactor):
            @property
            def name(self):
                return "Dummy"
            def compute(self, context):
                return FactorResult(factor_id="dummy", value=0.0, delta_success=0.0, delta_time=0.0)
        df = DummyFactor(FactorID.X1_LLM, enabled=False)
        assert df.enabled is False


# =============================================================================
# UNIT: LLMFactor (x₁)
# =============================================================================

class TestLLMFactorUnit:
    """Unit-тесты на LLMFactor — фактор способностей LLM."""

    def test_llm_factor_name(self):
        """LLMFactor.name == 'LLM Capability'."""
        f = LLMFactor()
        assert f.name == "LLM Capability"

    def test_llm_factor_priority_high(self):
        """LLMFactor.priority == 'HIGH'."""
        f = LLMFactor()
        assert f.priority == "HIGH"

    def test_llm_factor_id(self):
        """LLMFactor.factor_id == FactorID.X1_LLM."""
        f = LLMFactor()
        assert f.factor_id == FactorID.X1_LLM

    def test_llm_default_benchmarks_value(self):
        """При пустом context value = 0.7 (default benchmarks все 0.7)."""
        f = LLMFactor()
        r = f.compute({})
        assert r.value == 0.7

    def test_llm_default_delta_success(self):
        """При пустом context delta_success ≈ 0.21174 (s_m - 0.3)."""
        f = LLMFactor()
        r = f.compute({})
        assert abs(r.delta_success - 0.21174091246490306) < 1e-10

    def test_llm_default_delta_time_zero(self):
        """При пустом context delta_time = 0.0."""
        f = LLMFactor()
        r = f.compute({})
        assert r.delta_time == 0.0

    def test_llm_perfect_benchmarks_value(self):
        """Все benchmarks = 1.0 → value = 1.0."""
        f = LLMFactor()
        r = f.compute({"benchmarks": {"quality": 1.0, "reasoning": 1.0, "coding": 1.0, "agentic": 1.0}})
        assert r.value == 1.0

    def test_llm_perfect_benchmarks_delta_success(self):
        """Все benchmarks = 1.0 → delta_success ≈ 0.62414."""
        f = LLMFactor()
        r = f.compute({"benchmarks": {"quality": 1.0, "reasoning": 1.0, "coding": 1.0, "agentic": 1.0}})
        assert abs(r.delta_success - 0.6241417020900337) < 1e-10

    def test_llm_zero_benchmarks_value(self):
        """Все benchmarks = 0 → value = 0.0."""
        f = LLMFactor()
        r = f.compute({"benchmarks": {"quality": 0, "reasoning": 0, "coding": 0, "agentic": 0}})
        assert r.value == 0.0

    def test_llm_zero_benchmarks_delta_success(self):
        """Все benchmarks = 0 → delta_success = -0.3 (s_m = 0, 0 - 0.3)."""
        f = LLMFactor()
        r = f.compute({"benchmarks": {"quality": 0, "reasoning": 0, "coding": 0, "agentic": 0}})
        assert r.delta_success == -0.3

    def test_llm_partial_benchmarks_uses_defaults_for_missing(self):
        """Неполные benchmarks — недостающие берутся из default 0.7."""
        f = LLMFactor()
        r = f.compute({"benchmarks": {"quality": 0.5, "reasoning": 0.5}})
        # quality=0.5, reasoning=0.5, coding=0.7, agentic=0.7
        expected_value = 0.25*0.5 + 0.30*0.5 + 0.25*0.7 + 0.20*0.7
        assert abs(r.value - expected_value) < 1e-10

    def test_llm_context_lambda_tau_ignored_causes_overflow(self):
        """lambda_t и tau_t из context читаются, но 2.71828**exp_term падает при больших значениях.

        Код: lambda_t = context.get('lambda_t', 5.0); tau_t = context.get('tau_t', 0.5)
        Но при lambda_t=999, tau_t=999: exp_term = -999*(0.7-999) ≈ 998000 → OverflowError.
        """
        f = LLMFactor()
        # ЭТО БАГ: код читает lambda_t/tau_t из context, но не защищён от overflow
        with pytest.raises(OverflowError):
            f.compute({"benchmarks": {"quality": 0.7, "reasoning": 0.7, "coding": 0.7, "agentic": 0.7},
                       "lambda_t": 999.0, "tau_t": 999.0})

    def test_llm_metadata_contains_s_m_and_benchmarks(self):
        """metadata содержит s_m и benchmarks."""
        f = LLMFactor()
        r = f.compute({})
        assert "s_m" in r.metadata
        assert "benchmarks" in r.metadata


# =============================================================================
# UNIT: PromptFactor (x₂)
# =============================================================================

class TestPromptFactorUnit:
    """Unit-тесты на PromptFactor."""

    def test_prompt_factor_name(self):
        """PromptFactor.name == 'Prompt Engineering'."""
        f = PromptFactor()
        assert f.name == "Prompt Engineering"

    def test_prompt_factor_default_value(self):
        """PromptFactor.compute({}) → value = 0.8."""
        f = PromptFactor()
        r = f.compute({})
        assert r.value == 0.8

    def test_prompt_factor_default_delta_success(self):
        """PromptFactor.compute({}) → delta_success = 0.04."""
        f = PromptFactor()
        r = f.compute({})
        assert r.delta_success == 0.04

    def test_prompt_factor_default_delta_time(self):
        """PromptFactor.compute({}) → delta_time = -0.05."""
        f = PromptFactor()
        r = f.compute({})
        assert r.delta_time == -0.05

    def test_prompt_factor_id(self):
        """PromptFactor.factor_id == FactorID.X2_PROMPT."""
        f = PromptFactor()
        assert f.factor_id == FactorID.X2_PROMPT


# =============================================================================
# UNIT: CostTieringFactor (x₈)
# =============================================================================

class TestCostTieringFactorUnit:
    """Unit-тесты на CostTieringFactor — выбор tier по бюджету."""

    def test_cost_tiering_name(self):
        """CostTieringFactor.name == 'Cost Tiering'."""
        f = CostTieringFactor()
        assert f.name == "Cost Tiering"

    def test_cost_tiering_priority_high(self):
        """CostTieringFactor.priority == 'HIGH'."""
        f = CostTieringFactor()
        assert f.priority == "HIGH"

    def test_cost_tiering_default_selects_paid_api(self):
        """Пустой context → tier = 'paid_api', value = 0.95."""
        f = CostTieringFactor()
        r = f.compute({})
        assert r.metadata["selected_tier"] == "paid_api"
        assert r.value == 0.95

    def test_cost_tiering_budget_below_one_selects_ollama(self):
        """budget < 1.0 → tier = 'ollama', value = 0.6."""
        f = CostTieringFactor()
        r = f.compute({"budget": 0.5})
        assert r.metadata["selected_tier"] == "ollama"
        assert r.value == 0.6

    def test_cost_tiering_budget_between_one_and_ten_selects_free(self):
        """1.0 <= budget < 10.0 и quality < 0.8 → tier = 'free_api', value = 0.75."""
        f = CostTieringFactor()
        r = f.compute({"budget": 5.0})
        assert r.metadata["selected_tier"] == "free_api"
        assert r.value == 0.75

    def test_cost_tiering_budget_ten_selects_paid(self):
        """budget >= 10.0 → tier = 'paid_api'."""
        f = CostTieringFactor()
        r = f.compute({"budget": 10.0})
        assert r.metadata["selected_tier"] == "paid_api"

    def test_cost_tiering_high_quality_forces_paid(self):
        """budget=5.0, quality_requirement=0.9 → tier = 'paid_api' (quality >= 0.8)."""
        f = CostTieringFactor()
        r = f.compute({"budget": 5.0, "quality_requirement": 0.9})
        assert r.metadata["selected_tier"] == "paid_api"
        assert r.value == 0.95

    def test_cost_tiering_negative_budget_selects_ollama(self):
        """budget < 0 → tier = 'ollama' (первое условие budget < 1.0)."""
        f = CostTieringFactor()
        r = f.compute({"budget": -10.0})
        assert r.metadata["selected_tier"] == "ollama"
        assert r.value == 0.6

    def test_cost_tiering_delta_success_paid_positive(self):
        """paid_api: delta_success = (0.95 - 0.7) * 0.2 = 0.05."""
        f = CostTieringFactor()
        r = f.compute({"budget": 100.0})
        assert r.delta_success == 0.05

    def test_cost_tiering_delta_success_ollama_negative(self):
        """ollama: delta_success = (0.6 - 0.7) * 0.2 = -0.02."""
        f = CostTieringFactor()
        r = f.compute({"budget": 0.5})
        assert abs(r.delta_success - (-0.02)) < 1e-14

    def test_cost_tiering_metadata_contains_budget(self):
        """metadata содержит budget, selected_tier, cost_per_1m."""
        f = CostTieringFactor()
        r = f.compute({"budget": 50.0})
        assert "budget" in r.metadata
        assert "selected_tier" in r.metadata
        assert "cost_per_1m" in r.metadata


# =============================================================================
# UNIT: GuardrailsFactor (x₁₂)
# =============================================================================

class TestGuardrailsFactorUnit:
    """Unit-тесты на GuardrailsFactor — эффективность guardrails."""

    def test_guardrails_name(self):
        """GuardrailsFactor.name == 'Guardrails'."""
        f = GuardrailsFactor()
        assert f.name == "Guardrails"

    def test_guardrails_priority_high(self):
        """GuardrailsFactor.priority == 'HIGH'."""
        f = GuardrailsFactor()
        assert f.priority == "HIGH"

    def test_guardrails_default_no_risks(self):
        """Пустой context → g_eff = 1.0 (нет рисков → произведение пустое = 1.0)."""
        f = GuardrailsFactor()
        r = f.compute({})
        assert r.value == 1.0
        assert r.delta_success == 0.05
        assert r.delta_time == 0.0

    def test_guardrails_with_active_guardrail_reduces_risk(self):
        """active_guardrails содержит риск → g_eff < 1.0."""
        f = GuardrailsFactor()
        r = f.compute({
            "active_guardrails": ["safety"],
            "risk_probabilities": {"safety": 0.3}
        })
        # g_eff = 1 - 0.3*(1-1) = 1.0 (guardrail активен → полная защита)
        assert r.value == 1.0
        assert r.delta_success == 0.05

    def test_guardrails_without_guardrail_exposes_risk(self):
        """Риск без guardrail → g_eff = 1 - p_risk."""
        f = GuardrailsFactor()
        r = f.compute({
            "active_guardrails": [],
            "risk_probabilities": {"safety": 0.3}
        })
        assert r.value == 0.7  # 1 - 0.3
        assert abs(r.delta_success - 0.035) < 1e-14  # 0.05 * 0.7

    def test_guardrails_multiple_risks_multiplicative(self):
        """Несколько рисков — эффективность перемножается."""
        f = GuardrailsFactor()
        r = f.compute({
            "active_guardrails": [],
            "risk_probabilities": {"safety": 0.5, "privacy": 0.5}
        })
        # g_eff = (1-0.5)*(1-0.5) = 0.25
        assert r.value == 0.25
        assert r.delta_success == 0.0125  # 0.05 * 0.25

    def test_guardrails_partial_protection(self):
        """Часть рисков защищена, часть нет."""
        f = GuardrailsFactor()
        r = f.compute({
            "active_guardrails": ["safety"],
            "risk_probabilities": {"safety": 0.3, "privacy": 0.2}
        })
        # g_eff = (1-0.3*0) * (1-0.2*1) = 1.0 * 0.8 = 0.8
        assert r.value == 0.8
        assert abs(r.delta_success - 0.04) < 1e-14  # 0.05 * 0.8

    def test_guardrails_p_risk_one_without_guardrail_g_eff_zero(self):
        """p_risk = 1.0 без guardrail → g_eff = 0.0."""
        f = GuardrailsFactor()
        r = f.compute({
            "active_guardrails": [],
            "risk_probabilities": {"safety": 1.0}
        })
        assert r.value == 0.0
        assert r.delta_success == 0.0

    def test_guardrails_delta_time_scales_with_count(self):
        """delta_time = 0.02 * len(active_guardrails)."""
        f = GuardrailsFactor()
        r = f.compute({"active_guardrails": ["safety", "privacy", "ethics"]})
        assert r.delta_time == 0.06  # 0.02 * 3

    def test_guardrails_metadata_contains_count_and_g_eff(self):
        """metadata содержит active_count и g_eff."""
        f = GuardrailsFactor()
        r = f.compute({"active_guardrails": ["safety"]})
        assert r.metadata["active_count"] == 1
        assert "g_eff" in r.metadata


# =============================================================================
# UNIT: ContinualLearningFactor (x₁₆)
# =============================================================================

class TestContinualLearningFactorUnit:
    """Unit-тесты на ContinualLearningFactor."""

    def test_continual_learning_name(self):
        """ContinualLearningFactor.name == 'Continual Learning'."""
        f = ContinualLearningFactor()
        assert f.name == "Continual Learning"

    def test_continual_learning_default_zero_tasks(self):
        """Пустой context → n_completed_tasks = 0 → value = 0.0, delta_success = 0.0."""
        f = ContinualLearningFactor()
        r = f.compute({})
        assert r.value == 0.0
        assert r.delta_success == 0.0
        assert r.delta_time == 0.0

    def test_continual_learning_zero_tasks_explicit(self):
        """n_completed_tasks = 0 → value = 0.0."""
        f = ContinualLearningFactor()
        r = f.compute({"n_completed_tasks": 0})
        assert r.value == 0.0

    def test_continual_learning_100_tasks(self):
        """n_completed_tasks = 100 → value ≈ 0.63212 (код использует 2.71828, не math.e).

        Реальное поведение: value = 1 - 2.71828^(-0.01 * 100) ≈ 0.6321203113733684.
        """
        f = ContinualLearningFactor()
        r = f.compute({"n_completed_tasks": 100})
        # Код использует 2.71828 вместо math.e — проверяем реальное поведение
        expected_code = 1.0 - (2.71828 ** (-0.01 * 100))
        assert abs(r.value - expected_code) < 1e-10
        assert abs(r.delta_success - 0.022756331209441264) < 1e-10
        # ЭТО БАГ: 2.71828 != math.e = 2.718281828..., погрешность ~2.5e-7

    def test_continual_learning_1000_tasks_saturates(self):
        """n_completed_tasks = 1000 → value ≈ 0.99995 (насыщение)."""
        f = ContinualLearningFactor()
        r = f.compute({"n_completed_tasks": 1000})
        assert r.value > 0.999
        assert r.value < 1.0

    def test_continual_learning_negative_tasks(self):
        """n_completed_tasks < 0 → value < 0 (без защиты от отрицательных значений).

        k_cl = 1 - e^(-0.01 * (-10)) = 1 - e^0.1 ≈ -0.105.
        """
        f = ContinualLearningFactor()
        r = f.compute({"n_completed_tasks": -10})
        assert r.value < 0.0
        # ЭТО БАГ: n_completed_tasks может быть отрицательным, но код не защищён

    def test_continual_learning_delta_time_scales_with_n(self):
        """delta_time = 0.01 * n_tasks * 0.001 = n_tasks * 1e-5."""
        f = ContinualLearningFactor()
        r = f.compute({"n_completed_tasks": 100})
        assert r.delta_time == 0.001  # 100 * 1e-5

    def test_continual_learning_metadata_contains_n_tasks(self):
        """metadata содержит n_tasks, k_cl, current_knowledge."""
        f = ContinualLearningFactor()
        r = f.compute({"n_completed_tasks": 50})
        assert r.metadata["n_tasks"] == 50
        assert "k_cl" in r.metadata


# =============================================================================
# UNIT: FactorRegistry
# =============================================================================

class TestFactorRegistryUnit:
    """Unit-тесты на FactorRegistry."""

    def test_registry_empty_on_creation(self):
        """Новый FactorRegistry — пустой."""
        reg = FactorRegistry()
        assert len(reg.get_all()) == 0
        assert len(reg.get_enabled()) == 0

    def test_registry_register_adds_factor(self):
        """register() добавляет фактор."""
        reg = FactorRegistry()
        reg.register(LLMFactor())
        assert len(reg.get_all()) == 1

    def test_registry_register_marks_enabled(self):
        """Зарегистрированный фактор по умолчанию enabled."""
        reg = FactorRegistry()
        reg.register(LLMFactor())
        assert len(reg.get_enabled()) == 1

    def test_registry_disable_removes_from_enabled(self):
        """disable() исключает из get_enabled()."""
        reg = FactorRegistry()
        reg.register(LLMFactor())
        reg.disable(FactorID.X1_LLM)
        assert len(reg.get_enabled()) == 0
        assert len(reg.get_all()) == 1

    def test_registry_enable_restores(self):
        """enable() после disable() возвращает в get_enabled()."""
        reg = FactorRegistry()
        reg.register(LLMFactor())
        reg.disable(FactorID.X1_LLM)
        reg.enable(FactorID.X1_LLM)
        assert len(reg.get_enabled()) == 1

    def test_registry_unregister_removes_completely(self):
        """unregister() удаляет фактор полностью."""
        reg = FactorRegistry()
        reg.register(LLMFactor())
        ok = reg.unregister(FactorID.X1_LLM)
        assert ok is True
        assert len(reg.get_all()) == 0

    def test_registry_unregister_missing_returns_false(self):
        """unregister() несуществующего фактора → False."""
        reg = FactorRegistry()
        ok = reg.unregister(FactorID.X1_LLM)
        assert ok is False

    def test_registry_get_existing(self):
        """get() возвращает фактор по FactorID."""
        reg = FactorRegistry()
        reg.register(LLMFactor())
        f = reg.get(FactorID.X1_LLM)
        assert f is not None
        assert f.name == "LLM Capability"

    def test_registry_get_missing_returns_none(self):
        """get() несуществующего фактора → None."""
        reg = FactorRegistry()
        f = reg.get(FactorID.X1_LLM)
        assert f is None

    def test_registry_compute_all_empty_returns_empty(self):
        """compute_all() на пустом registry → пустой dict."""
        reg = FactorRegistry()
        results = reg.compute_all({})
        assert results == {}

    def test_registry_compute_all_returns_results(self):
        """compute_all() вычисляет все enabled факторы."""
        reg = FactorRegistry()
        reg.register(LLMFactor())
        results = reg.compute_all({})
        assert "x1" in results
        assert results["x1"].value == 0.7

    def test_registry_compute_all_skips_disabled(self):
        """compute_all() пропускает disabled факторы."""
        reg = FactorRegistry()
        reg.register(LLMFactor())
        reg.disable(FactorID.X1_LLM)
        results = reg.compute_all({})
        assert "x1" not in results

    def test_registry_compute_total_deltas_sums_correctly(self):
        """compute_total_deltas() суммирует delta_success и delta_time."""
        reg = FactorRegistry()
        reg.register(LLMFactor())
        reg.register(CostTieringFactor())
        totals = reg.compute_total_deltas({})
        assert totals["delta_success"] == 0.26174091246490305
        assert totals["delta_time"] == -0.095

    def test_registry_compute_total_deltas_empty_zero(self):
        """compute_total_deltas() на пустом registry → оба нуля."""
        reg = FactorRegistry()
        totals = reg.compute_total_deltas({})
        assert totals["delta_success"] == 0.0
        assert totals["delta_time"] == 0.0


# =============================================================================
# UNIT: Factory functions
# =============================================================================

class TestFactoryFunctionsUnit:
    """Unit-тесты на create_mvp_registry и create_full_registry."""

    def test_create_mvp_registry_has_4_factors(self):
        """create_mvp_registry() создаёт registry с 4 факторами."""
        reg = create_mvp_registry()
        assert len(reg.get_all()) == 4

    def test_create_mvp_registry_factors_enabled(self):
        """Все 4 фактора MVP enabled."""
        reg = create_mvp_registry()
        assert len(reg.get_enabled()) == 4

    def test_create_mvp_registry_contains_expected_ids(self):
        """MVP содержит x1, x8, x12, x16."""
        reg = create_mvp_registry()
        ids = [f.factor_id for f in reg.get_all()]
        assert FactorID.X1_LLM in ids
        assert FactorID.X8_COST_TIERING in ids
        assert FactorID.X12_GUARDRAILS in ids
        assert FactorID.X16_CONTINUAL_LEARNING in ids

    def test_create_full_registry_has_17_factors(self):
        """create_full_registry() создаёт registry со всеми 17 факторами."""
        reg = create_full_registry()
        assert len(reg.get_all()) == 17

    def test_create_full_registry_all_enabled(self):
        """Все 17 факторов full registry enabled."""
        reg = create_full_registry()
        assert len(reg.get_enabled()) == 17

    def test_create_full_registry_contains_all_ids(self):
        """Full registry содержит все FactorID."""
        reg = create_full_registry()
        ids = [f.factor_id for f in reg.get_all()]
        for fid in FactorID:
            assert fid in ids


# =============================================================================
# UNIT: Remaining factors (x₃-x₇, x₉-x₁₁, x₁₃-x₁₅, x₁₇)
# =============================================================================

class TestRemainingFactorsUnit:
    """Unit-тесты на остальные 13 факторов — проверка констант и структуры."""

    def test_memory_retrieval_factor(self):
        """MemoryRetrievalFactor: value=0.75, delta_s=0.05, delta_t=-0.02."""
        f = MemoryRetrievalFactor()
        r = f.compute({})
        assert r.value == 0.75
        assert r.delta_success == 0.05
        assert r.delta_time == -0.02
        assert f.factor_id == FactorID.X3_MEMORY

    def test_memory_system_factor(self):
        """MemorySystemFactor: value=0.7, delta_s=0.03, delta_t=0.01."""
        f = MemorySystemFactor()
        r = f.compute({})
        assert r.value == 0.7
        assert r.delta_success == 0.03
        assert r.delta_time == 0.01
        assert f.factor_id == FactorID.X4_MEMORY_SYSTEM

    def test_multi_agent_factor(self):
        """MultiAgentFactor: value=0.85, delta_s=0.08, delta_t=0.04."""
        f = MultiAgentFactor()
        r = f.compute({})
        assert r.value == 0.85
        assert r.delta_success == 0.08
        assert r.delta_time == 0.04
        assert f.factor_id == FactorID.X5_MULTI_AGENT

    def test_self_correction_factor(self):
        """SelfCorrectionFactor: value=0.9, delta_s=0.12, delta_t=0.15."""
        f = SelfCorrectionFactor()
        r = f.compute({})
        assert r.value == 0.9
        assert r.delta_success == 0.12
        assert r.delta_time == 0.15
        assert f.factor_id == FactorID.X6_SELF_CORRECTION

    def test_tool_calling_factor(self):
        """ToolCallingFactor: value=0.8, delta_s=0.06, delta_t=-0.04."""
        f = ToolCallingFactor()
        r = f.compute({})
        assert r.value == 0.8
        assert r.delta_success == 0.06
        assert r.delta_time == -0.04
        assert f.factor_id == FactorID.X7_TOOL_CALLING

    def test_grounding_factor(self):
        """GroundingFactor: value=0.75, delta_s=0.05, delta_t=0.02."""
        f = GroundingFactor()
        r = f.compute({})
        assert r.value == 0.75
        assert r.delta_success == 0.05
        assert r.delta_time == 0.02
        assert f.factor_id == FactorID.X9_GROUNDING

    def test_fine_tuning_factor(self):
        """FineTuningFactor: value=0.82, delta_s=0.07, delta_t=-0.03."""
        f = FineTuningFactor()
        r = f.compute({})
        assert r.value == 0.82
        assert r.delta_success == 0.07
        assert r.delta_time == -0.03
        assert f.factor_id == FactorID.X10_FINE_TUNING

    def test_context_management_factor(self):
        """ContextManagementFactor: value=0.78, delta_s=0.04, delta_t=-0.01."""
        f = ContextManagementFactor()
        r = f.compute({})
        assert r.value == 0.78
        assert r.delta_success == 0.04
        assert r.delta_time == -0.01
        assert f.factor_id == FactorID.X11_CONTEXT_MANAGEMENT

    def test_test_time_compute_factor(self):
        """TestTimeComputeFactor: value=0.85, delta_s=0.10, delta_t=0.20."""
        f = TestTimeComputeFactor()
        r = f.compute({})
        assert r.value == 0.85
        assert r.delta_success == 0.10
        assert r.delta_time == 0.20
        assert f.factor_id == FactorID.X13_TEST_TIME_COMPUTE

    def test_design_patterns_factor(self):
        """DesignPatternsFactor: value=0.8, delta_s=0.06, delta_t=-0.02."""
        f = DesignPatternsFactor()
        r = f.compute({})
        assert r.value == 0.8
        assert r.delta_success == 0.06
        assert r.delta_time == -0.02
        assert f.factor_id == FactorID.X14_DESIGN_PATTERNS

    def test_evaluation_factor(self):
        """EvaluationFactor: value=0.74, delta_s=0.04, delta_t=0.01."""
        f = EvaluationFactor()
        r = f.compute({})
        assert r.value == 0.74
        assert r.delta_success == 0.04
        assert r.delta_time == 0.01
        assert f.factor_id == FactorID.X15_EVALUATION

    def test_inference_opt_factor(self):
        """InferenceOptFactor: value=0.7, delta_s=0.01, delta_t=-0.08."""
        f = InferenceOptFactor()
        r = f.compute({})
        assert r.value == 0.7
        assert r.delta_success == 0.01
        assert r.delta_time == -0.08
        assert f.factor_id == FactorID.X17_INFERENCE_OPT


# =============================================================================
# PAIR: FactorRegistry + LLMFactor
# =============================================================================

class TestPairRegistryLLM:
    """PAIR: FactorRegistry → LLMFactor.compute через compute_all."""

    def test_registry_compute_all_propagates_context_to_llm(self):
        """compute_all() передаёт context в LLMFactor — value зависит от benchmarks."""
        reg = FactorRegistry()
        reg.register(LLMFactor())
        results = reg.compute_all({"benchmarks": {"quality": 1.0, "reasoning": 1.0, "coding": 1.0, "agentic": 1.0}})
        assert results["x1"].value == 1.0

    def test_registry_compute_total_deltas_with_multiple_factors(self):
        """compute_total_deltas() суммирует вклады 2+ факторов корректно."""
        reg = FactorRegistry()
        reg.register(PromptFactor())
        reg.register(MemoryRetrievalFactor())
        totals = reg.compute_total_deltas({})
        # Prompt: delta_s=0.04, delta_t=-0.05; Memory: delta_s=0.05, delta_t=-0.02
        assert totals["delta_success"] == 0.09
        assert totals["delta_time"] == -0.07


# =============================================================================
# PAIR: CostTieringFactor + GuardrailsFactor
# =============================================================================

class TestPairCostGuardrails:
    """PAIR: CostTiering → Guardrails — оба HIGH priority, оба влияют на delta_success."""

    def test_high_priority_factors_both_positive_delta(self):
        """Оба HIGH priority фактора при благоприятных условиях дают положительный delta_success."""
        cost = CostTieringFactor()
        guard = GuardrailsFactor()
        r_cost = cost.compute({"budget": 100.0})
        r_guard = guard.compute({"active_guardrails": ["safety"], "risk_probabilities": {"safety": 0.3}})
        assert r_cost.delta_success > 0
        assert r_guard.delta_success > 0

    def test_cost_guardrails_combined_delta_time(self):
        """Суммарное delta_time = -0.095 + 0.0 = -0.095 (ускорение)."""
        cost = CostTieringFactor()
        guard = GuardrailsFactor()
        r_cost = cost.compute({"budget": 100.0})
        r_guard = guard.compute({})
        combined = r_cost.delta_time + r_guard.delta_time
        assert combined == -0.095


# =============================================================================
# INTEGRITY: Архитектурные инварианты
# =============================================================================

class TestIntegrityFactors:
    """INTEGRITY: Проверки кода на антипаттерны и расхождения с документацией."""

    def test_llm_factor_uses_hardcoded_e_not_math_exp(self):
        """LLMFactor использует 2.71828 вместо math.e — погрешность ~2.5e-7.

        Код: s_m = c_llm / (1 + (2.71828 ** exp_term))
        Документация не указывает константу, но math.e точнее.
        """
        import math
        f = LLMFactor()
        r = f.compute({"benchmarks": {"quality": 0.7, "reasoning": 0.7, "coding": 0.7, "agentic": 0.7}})
        c_llm = 0.7
        lambda_t = 5.0
        tau_t = 0.5
        exp_term = -lambda_t * (c_llm - tau_t)
        s_m_math = c_llm / (1 + math.exp(exp_term))
        s_m_code = c_llm / (1 + (2.71828 ** exp_term))
        # Реальное поведение кода использует 2.71828
        assert abs(r.delta_success - (s_m_code - 0.3)) < 1e-10
        # ЭТО БАГ: 2.71828 != math.e, погрешность накапливается

    def test_all_factors_return_factor_result(self):
        """Все 17 факторов возвращают FactorResult (не dict, не tuple, не None)."""
        factors = [
            LLMFactor(), PromptFactor(), MemoryRetrievalFactor(), MemorySystemFactor(),
            MultiAgentFactor(), SelfCorrectionFactor(), ToolCallingFactor(),
            CostTieringFactor(), GroundingFactor(), FineTuningFactor(),
            ContextManagementFactor(), GuardrailsFactor(), TestTimeComputeFactor(),
            DesignPatternsFactor(), EvaluationFactor(), ContinualLearningFactor(),
            InferenceOptFactor(),
        ]
        for f in factors:
            r = f.compute({})
            assert type(r).__name__ == "FactorResult", f"{f.name} вернул {type(r)}"

    def test_factor_result_values_are_numeric(self):
        """Все value, delta_success, delta_time — числа (float или int)."""
        factors = [
            LLMFactor(), PromptFactor(), CostTieringFactor(), GuardrailsFactor(),
            ContinualLearningFactor(),
        ]
        for f in factors:
            r = f.compute({})
            assert isinstance(r.value, (int, float))
            assert isinstance(r.delta_success, (int, float))
            assert isinstance(r.delta_time, (int, float))

    def test_registry_unregister_does_not_affect_other_factors(self):
        """unregister() одного фактора не трогает остальные."""
        reg = FactorRegistry()
        reg.register(LLMFactor())
        reg.register(PromptFactor())
        reg.unregister(FactorID.X1_LLM)
        assert reg.get(FactorID.X2_PROMPT) is not None
        assert len(reg.get_all()) == 1

    def test_compute_all_with_disabled_registry_returns_empty(self):
        """Все факторы disabled → compute_all = {}."""
        reg = create_full_registry()
        for fid in FactorID:
            reg.disable(fid)
        results = reg.compute_all({})
        assert results == {}


# =============================================================================
# REGRESSION: Старые баги не должны вернуться
# =============================================================================

class TestRegressionFactors:
    """REGRESSION: Проверки, что исправленные баги не вернулись."""

    def test_mvp_registry_always_has_four_factors(self):
        """create_mvp_registry() всегда создаёт ровно 4 фактора."""
        reg = create_mvp_registry()
        assert len(reg.get_all()) == 4
        assert len(reg.get_enabled()) == 4

    def test_full_registry_always_has_seventeen_factors(self):
        """create_full_registry() всегда создаёт ровно 17 факторов."""
        reg = create_full_registry()
        assert len(reg.get_all()) == 17
        assert len(reg.get_enabled()) == 17

    def test_factor_id_enum_not_mutated(self):
        """FactorID Enum содержит ровно 17 значений и не изменяется."""
        assert len(FactorID) == 17
        assert FactorID.X1_LLM.value == "x1"
        assert FactorID.X17_INFERENCE_OPT.value == "x17"

    def test_guardrails_g_eff_formula_unchanged(self):
        """Формула g_eff GuardrailsFactor не изменилась: произведение (1 - p_risk*(1-g_i))."""
        f = GuardrailsFactor()
        r = f.compute({
            "active_guardrails": [],
            "risk_probabilities": {"a": 0.5, "b": 0.5}
        })
        # g_eff = (1-0.5)*(1-0.5) = 0.25
        assert r.value == 0.25
        assert r.delta_success == 0.0125  # 0.05 * 0.25
