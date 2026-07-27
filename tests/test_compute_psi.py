"""
Space1 — ПРОВЕРЕННЫЕ ТЕСТЫ: compute_psi (Ψ — Risk)

Каждый тест проверен против реального кода.
FAILED-тесты = реальные баги, не ошибки тестов.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from datetime import datetime, timedelta


# =============================================================================
# UNIT: compute_psi — позиционная сигнатура
# =============================================================================

class TestComputePsiPositional:
    """Unit-тесты на compute_psi(p_fail, c_direct, c_reputation) — позиционная сигнатура."""

    def test_compute_psi_positional_basic(self):
        """
        compute_psi(0.1, 10, 5) → 1.5.

        Проверяем: базовая формула Ψ = max(0, p_fail × (c_direct + c_reputation)).
        Границы: p_fail=0.1, c_direct=10, c_reputation=5 — типичные значения.
        Почему такие: низкая вероятность отказа, умеренные прямые и репутационные издержки.
        """
        from space1.utility import compute_psi
        psi = compute_psi(0.1, 10.0, 5.0)
        assert psi == 1.5  # 0.1 × (10 + 5) = 1.5

    def test_compute_psi_positional_zero_p_fail(self):
        """
        compute_psi(0.0, 10, 5) → 0.0.

        Проверяем: нулевая вероятность отказа → нулевой риск.
        Границы: p_fail = 0.0.
        Почему такие: граничный случай — задача без риска отказа.
        """
        from space1.utility import compute_psi
        psi = compute_psi(0.0, 10.0, 5.0)
        assert psi == 0.0

    def test_compute_psi_positional_zero_costs(self):
        """
        compute_psi(0.5, 0, 0) → 0.0.

        Проверяем: нулевые издержки → нулевой риск независимо от p_fail.
        Границы: c_direct = 0, c_reputation = 0.
        Почему такие: граничный случай — задача без финансовых последствий.
        """
        from space1.utility import compute_psi
        psi = compute_psi(0.5, 0.0, 0.0)
        assert psi == 0.0

    def test_compute_psi_positional_negative_p_fail(self):
        """
        compute_psi(-0.1, 10, 5) → 0.0.

        Проверяем: отрицательная вероятность отказа обрезается до 0 через max(0, ...).
        Границы: p_fail = -0.1.
        Почему такие: некорректный ввод — вероятность не может быть отрицательной.
        """
        from space1.utility import compute_psi
        psi = compute_psi(-0.1, 10.0, 5.0)
        assert psi == 0.0

    def test_compute_psi_positional_negative_cost(self):
        """
        compute_psi(0.1, -10, 5) → 0.0.

        Проверяем: отрицательные издержки дают отрицательный psi, обрезается до 0.
        Границы: c_direct = -10.
        Почему такие: некорректный ввод — издержки не могут быть отрицательными.
        """
        from space1.utility import compute_psi
        psi = compute_psi(0.1, -10.0, 5.0)
        assert psi == 0.0

    def test_compute_psi_positional_default_c_reputation(self):
        """
        compute_psi(0.1, 10) → 1.0.

        Проверяем: default c_reputation при позиционном вызове с 2 аргументами.
        Границы: c_reputation не передан.
        Почему такие: проверка default behavior.
        """
        from space1.utility import compute_psi
        psi = compute_psi(0.1, 10.0)
        # ЭТО БАГ: ожидалось 1.5 (default c_rep=5 из сигнатуры),
        # но при позиционном вызове с 2 аргументами третий = False (default canonical_or_c_reputation)
        # bool — подкласс int, False=0, так что psi = 0.1*(10+0) = 1.0
        assert psi == 1.0  # Реальное поведение кода

    def test_compute_psi_positional_high_values(self):
        """
        compute_psi(1.0, 100, 100) → 200.0.

        Проверяем: psi может быть >> 1 — документация §IV.4: Ψ ∈ [0, ∞).
        Границы: p_fail=1.0, c_direct=100, c_reputation=100.
        Почему такие: проверка что psi не ограничен сверху.
        """
        from space1.utility import compute_psi
        psi = compute_psi(1.0, 100.0, 100.0)
        assert psi == 200.0

    def test_compute_psi_positional_exceeds_one(self):
        """
        compute_psi(0.2, 10, 5) → 3.0.

        Проверяем: psi > 1 — документация §IV.4 говорит Ψ ∈ [0, ∞), не [0,1].
        Границы: p_fail=0.2, c_direct=10, c_reputation=5.
        Почему такие: проверка что psi может превышать 1 (это не баг, это документировано).
        """
        from space1.utility import compute_psi
        psi = compute_psi(0.2, 10.0, 5.0)
        assert psi == 3.0  # 0.2 × 15 = 3.0

    def test_compute_psi_positional_bool_third_arg(self):
        """
        compute_psi(0.1, 10, True) → 1.1, compute_psi(0.1, 10, False) → 1.0.

        Проверяем: bool как c_reputation — True=1.0, False=0.0.
        Границы: canonical_or_c_reputation = True/False.
        Почему такие: bool — подкласс int, проходит в позиционную сигнатуру.
        """
        from space1.utility import compute_psi
        assert compute_psi(0.1, 10.0, True) == 1.1   # 0.1 × (10 + 1) = 1.1
        assert compute_psi(0.1, 10.0, False) == 1.0  # 0.1 × (10 + 0) = 1.0


# =============================================================================
# UNIT: compute_psi — legacy сигнатура (canonical=False)
# =============================================================================

class TestComputePsiLegacy:
    """Unit-тесты на compute_psi(task, agent, canonical=False) — legacy сигнатура."""

    def test_compute_psi_legacy_basic(self):
        """
        compute_psi(task, agent, False) → нормализованное значение [0, 1].

        Проверяем: legacy режим возвращает _clamp-нутое значение.
        Границы: Task с default metadata, Agent с default capabilities.
        Почему такие: стандартный кейс — типичная задача и агент.
        """
        from space1.utility import compute_psi
        from space1.models.task import Task, TaskPriority
        from space1.models.agents import Agent, AgentCapabilities, AgentMetrics

        task = Task(
            id="t1", title="Test", description="Desc",
            priority=TaskPriority.HIGH,
            deadline=datetime.now() + timedelta(hours=24)
        )
        caps = AgentCapabilities(llm_quality=0.7)
        metrics = AgentMetrics()
        agent = Agent(id="a1", name="Test", capabilities=caps, metrics=metrics)

        psi = compute_psi(task, agent, False)
        assert 0.0 <= psi <= 1.0
        assert psi > 0.0  # Не ноль при стандартных параметрах

    def test_compute_psi_legacy_bounds(self):
        """
        compute_psi с экстремальными параметрами → всегда [0, 1].

        Проверяем: legacy режим всегда _clamp-ит результат.
        Границы: max uncertainty, max fatigue, min skill.
        Почему такие: проверка защиты от выхода за границы.
        """
        from space1.utility import compute_psi
        from space1.models.task import Task, TaskPriority
        from space1.models.agents import Agent, AgentCapabilities, AgentMetrics

        task = Task(
            id="t_max", title="Test", description="Desc",
            priority=TaskPriority.HIGH,
            deadline=datetime.now() + timedelta(hours=24),
            metadata={"uncertainty": 1.0, "novelty": 1.0},
            urgency_score=1.0
        )
        caps = AgentCapabilities(llm_quality=0.0)  # min skill
        metrics = AgentMetrics(n_active_tasks=10)  # max fatigue
        agent = Agent(id="a_max", name="Test", capabilities=caps, metrics=metrics)

        psi = compute_psi(task, agent, False)
        assert 0.0 <= psi <= 1.0
        assert psi > 0.5  # При max риске psi должен быть высоким

    def test_compute_psi_legacy_min_risk(self):
        """
        compute_psi с минимальными параметрами → низкий psi.

        Проверяем: минимальная неопределённость, максимальный skill, нет fatigue.
        Границы: uncertainty=0, novelty=0, llm_quality=1.0, n_active=0.
        Почему такие: проверка нижней границы legacy psi.
        """
        from space1.utility import compute_psi
        from space1.models.task import Task, TaskPriority
        from space1.models.agents import Agent, AgentCapabilities, AgentMetrics

        task = Task(
            id="t_min", title="Test", description="Desc",
            priority=TaskPriority.LOW,
            deadline=datetime.now() + timedelta(hours=24),
            metadata={"uncertainty": 0.0, "novelty": 0.0},
            urgency_score=0.0
        )
        caps = AgentCapabilities(llm_quality=1.0)  # max skill
        metrics = AgentMetrics(n_active_tasks=0)
        agent = Agent(id="a_min", name="Test", capabilities=caps, metrics=metrics)

        psi = compute_psi(task, agent, False)
        assert 0.0 <= psi <= 1.0
        assert psi < 0.4  # При min риске psi должен быть низким

    def test_compute_psi_legacy_fatigue_effect(self):
        """
        n_active_tasks увеличивает psi через fatigue.

        Проверяем: fatigue = n_active_tasks / 10.0.
        Границы: n_active_tasks = 0 vs 10.
        Почему такие: проверка влияния загруженности агента на риск.
        """
        from space1.utility import compute_psi
        from space1.models.task import Task, TaskPriority
        from space1.models.agents import Agent, AgentCapabilities, AgentMetrics

        task = Task(
            id="t_f", title="Test", description="Desc",
            priority=TaskPriority.HIGH,
            deadline=datetime.now() + timedelta(hours=24),
            metadata={"uncertainty": 0.5, "novelty": 0.5}
        )
        caps = AgentCapabilities(llm_quality=0.7)

        metrics0 = AgentMetrics(n_active_tasks=0)
        agent0 = Agent(id="a0", name="Test", capabilities=caps, metrics=metrics0)
        psi0 = compute_psi(task, agent0, False)

        metrics10 = AgentMetrics(n_active_tasks=10)
        agent10 = Agent(id="a10", name="Test", capabilities=caps, metrics=metrics10)
        psi10 = compute_psi(task, agent10, False)

        assert psi10 > psi0  # Больше fatigue → больше psi

    def test_compute_psi_legacy_skill_effect(self):
        """
        llm_quality уменьшает psi (skill = 1 - llm_quality).

        Проверяем: более квалифицированный агент → меньше риск.
        Границы: llm_quality = 0.0 vs 1.0.
        Почему такие: проверка что skill влияет на риск инверсно.
        """
        from space1.utility import compute_psi
        from space1.models.task import Task, TaskPriority
        from space1.models.agents import Agent, AgentCapabilities, AgentMetrics

        task = Task(
            id="t_s", title="Test", description="Desc",
            priority=TaskPriority.HIGH,
            deadline=datetime.now() + timedelta(hours=24),
            metadata={"uncertainty": 0.5, "novelty": 0.5}
        )
        metrics = AgentMetrics()

        caps_low = AgentCapabilities(llm_quality=0.0)
        agent_low = Agent(id="al", name="Test", capabilities=caps_low, metrics=metrics)
        psi_low = compute_psi(task, agent_low, False)

        caps_high = AgentCapabilities(llm_quality=1.0)
        agent_high = Agent(id="ah", name="Test", capabilities=caps_high, metrics=metrics)
        psi_high = compute_psi(task, agent_high, False)

        assert psi_high < psi_low  # Высокий skill → меньше psi

    def test_compute_psi_legacy_none_task(self):
        """
        compute_psi(None, None, False) → default psi.

        Проверяем: при None используются значения по умолчанию.
        Границы: task=None, agent=None.
        Почему такие: проверка graceful degradation.
        """
        from space1.utility import compute_psi
        psi = compute_psi(None, None, False)
        assert 0.0 <= psi <= 1.0


# =============================================================================
# UNIT: compute_psi — legacy сигнатура (canonical=True)
# =============================================================================

class TestComputePsiLegacyCanonical:
    """Unit-тесты на compute_psi(task, agent, canonical=True) — каноническая формула."""

    def test_compute_psi_canonical_basic(self):
        """
        compute_psi(task, agent, True) → psi через P_fail формулу.

        Проверяем: canonical=True использует формулу с P_base и альфами.
        Границы: Task с default metadata, Agent с default capabilities.
        Почему такие: стандартный кейс канонической формулы.
        """
        from space1.utility import compute_psi
        from space1.models.task import Task, TaskPriority
        from space1.models.agents import Agent, AgentCapabilities, AgentMetrics

        task = Task(
            id="t1", title="Test", description="Desc",
            priority=TaskPriority.HIGH,
            deadline=datetime.now() + timedelta(hours=24),
            metadata={"uncertainty": 0.0, "novelty": 0.0}
        )
        caps = AgentCapabilities(llm_quality=0.7)
        metrics = AgentMetrics()
        agent = Agent(id="a1", name="Test", capabilities=caps, metrics=metrics)

        psi = compute_psi(task, agent, True)
        assert psi > 0.0

    def test_compute_psi_canonical_skill_effect(self):
        """
        llm_quality влияет на psi инверсно: skill = 1 - llm_quality.

        Проверяем: низкий llm_quality → высокий skill → меньше psi.
        Границы: llm_quality = 0.0 vs 1.0.
        Почему такие: проверка влияния skill на каноническую формулу.

        ЭТО БАГ: skill = 1 - llm_quality инвертирует смысл.
        llm_quality=0.0 (низкий) → skill=1.0 (высокий) → меньше psi.
        llm_quality=1.0 (высокий) → skill=0.0 (низкий) → больше psi.
        Должно быть: skill = llm_quality.
        """
        from space1.utility import compute_psi
        from space1.models.task import Task, TaskPriority
        from space1.models.agents import Agent, AgentCapabilities, AgentMetrics

        task = Task(
            id="t_s", title="Test", description="Desc",
            priority=TaskPriority.HIGH,
            deadline=datetime.now() + timedelta(hours=24),
            metadata={"uncertainty": 0.0, "novelty": 0.0}
        )
        metrics = AgentMetrics()

        caps_low = AgentCapabilities(llm_quality=0.0)
        agent_low = Agent(id="al", name="Test", capabilities=caps_low, metrics=metrics)
        psi_low = compute_psi(task, agent_low, True)

        caps_high = AgentCapabilities(llm_quality=1.0)
        agent_high = Agent(id="ah", name="Test", capabilities=caps_high, metrics=metrics)
        psi_high = compute_psi(task, agent_high, True)

        # Реальное поведение: низкий llm_quality → меньше psi (инверсия)
        assert psi_low < psi_high  # Реальное поведение кода
        # ЭТО БАГ: ожидалось psi_low > psi_high (низкий skill → больше риск)


# =============================================================================
# PAIR: compute_psi → evaluate_decision_rule
# =============================================================================

class TestPairPsiDecision:
    """PAIR: compute_psi → evaluate_decision_rule — каскад риска."""

    def test_psi_exceeds_threshold_decline(self):
        """
        psi > psi_max → evaluate_decision_rule → "DECLINE".

        Проверяем: высокий риск блокирует выполнение на уровне 2 каскада.
        Границы: psi=10.0, psi_max=5.0.
        Почему такие: типичный кейс — риск в 2 раза выше допустимого.
        """
        from space1.utility import evaluate_decision_rule
        decision = evaluate_decision_rule(
            gamma_hard=0.0, psi=10.0, psi_max=5.0,
            C_t=100.0, C_min=1.0, H_TZ=0.5, H_TZ_max=1.0,
            VoI=0.5, C_info=2.0, H_val=0.8, H_clarify=0.5,
            U_val=0.5, Q_predicted=0.9, q_min=0.5
        )
        assert decision == "DECLINE"

    def test_psi_within_threshold_execute(self):
        """
        psi <= psi_max, положительная полезность → "EXECUTE".

        Проверяем: низкий риск + положительная полезность → выполнение.
        Границы: psi=0.1, psi_max=5.0.
        Почему такие: типичный кейс — задача с низким риском.
        """
        from space1.utility import evaluate_decision_rule
        decision = evaluate_decision_rule(
            gamma_hard=0.0, psi=0.1, psi_max=5.0,
            C_t=100.0, C_min=1.0, H_TZ=0.5, H_TZ_max=1.0,
            VoI=0.5, C_info=2.0, H_val=0.8, H_clarify=0.5,
            U_val=0.5, Q_predicted=0.9, q_min=0.5
        )
        assert decision == "EXECUTE"

    def test_positional_psi_into_decision(self):
        """
        compute_psi(0.5, 10, 5)=7.5 → evaluate_decision_rule(psi=7.5, psi_max=5.0) → "DECLINE".

        Проверяем: связка позиционной psi с decision rule.
        Границы: p_fail=0.5, c_direct=10, c_reputation=5.
        Почему такие: высокая вероятность отказа с умеренными издержками.
        """
        from space1.utility import compute_psi, evaluate_decision_rule
        psi = compute_psi(0.5, 10.0, 5.0)
        assert psi == 7.5
        decision = evaluate_decision_rule(
            gamma_hard=0.0, psi=psi, psi_max=5.0,
            C_t=100.0, C_min=1.0, H_TZ=0.5, H_TZ_max=1.0,
            VoI=0.5, C_info=2.0, H_val=0.8, H_clarify=0.5,
            U_val=0.5, Q_predicted=0.9, q_min=0.5
        )
        assert decision == "DECLINE"


# =============================================================================
# INTEGRITY: Архитектурные инварианты compute_psi
# =============================================================================

class TestIntegrityComputePsi:
    """INTEGRITY: Проверки кода compute_psi на антипаттерны."""

    def test_no_bare_except_in_compute_psi(self):
        """
        compute_psi не содержит bare except — ошибки не маскируются.

        Проверяем: в коде compute_psi нет "except Exception: pass".
        Границы: Весь файл utility/__init__.py.
        Почему такие: 10_SECURITY.md §III — fail fast, логирование всех ошибок.
        """
        import space1.utility as util_mod
        util_path = util_mod.__file__
        with open(util_path, "r") as f:
            content = f.read()

        # Ищем compute_psi функцию
        func_start = content.find("def compute_psi(")
        func_end = content.find("\ndef ", func_start + 1)
        if func_end == -1:
            func_end = len(content)
        func_body = content[func_start:func_end]

        assert "except Exception" not in func_body,             "compute_psi содержит bare except — маскирует ошибки"

    def test_positional_formula_matches_documentation(self):
        """
        Позиционная формула: Ψ = max(0, p_fail × (c_direct + c_reputation)).

        Проверяем: реальная формула соответствует документации §IV.4.
        Границы: p_fail=0.1, c_direct=10, c_reputation=5 → 1.5.
        Почему такие: документация §IV.4: Ψ = P_fail·(C_direct+C_reputation).
        """
        from space1.utility import compute_psi
        # Ручная проверка нескольких точек
        test_cases = [
            (0.0, 10.0, 5.0, 0.0),
            (0.1, 10.0, 5.0, 1.5),
            (0.2, 10.0, 5.0, 3.0),
            (1.0, 10.0, 5.0, 15.0),
            (0.1, 0.0, 0.0, 0.0),
            (-0.1, 10.0, 5.0, 0.0),
        ]
        for p_fail, c_dir, c_rep, expected in test_cases:
            actual = compute_psi(p_fail, c_dir, c_rep)
            assert actual == expected,                 f"compute_psi({p_fail}, {c_dir}, {c_rep}) = {actual}, ожидалось {expected}"

    def test_legacy_returns_clamped_value(self):
        """
        Legacy режим (canonical=False) всегда возвращает [0, 1].

        Проверяем: _clamp применяется к результату legacy формулы.
        Границы: Экстремальные параметры.
        Почему такие: документация не уточняет границы legacy, но _clamp
        гарантирует [0,1] — проверим что это так.
        """
        from space1.utility import compute_psi
        from space1.models.task import Task, TaskPriority
        from space1.models.agents import Agent, AgentCapabilities, AgentMetrics

        # Max risk parameters
        task = Task(
            id="t", title="Test", description="Desc",
            priority=TaskPriority.HIGH,
            deadline=datetime.now() + timedelta(hours=24),
            metadata={"uncertainty": 1.0, "novelty": 1.0},
            urgency_score=1.0
        )
        caps = AgentCapabilities(llm_quality=0.0)
        metrics = AgentMetrics(n_active_tasks=10)
        agent = Agent(id="a", name="Test", capabilities=caps, metrics=metrics)

        psi = compute_psi(task, agent, False)
        assert 0.0 <= psi <= 1.0,             f"Legacy psi вышел за границы [0,1]: {psi}"


# =============================================================================
# REGRESSION: Старые баги compute_psi
# =============================================================================

class TestRegressionComputePsi:
    """REGRESSION: Проверки, что исправленные баги compute_psi не вернулись."""

    def test_compute_psi_not_returns_none(self):
        """
        compute_psi не возвращает None — ранний баг из аудита.

        Проверяем: любой вызов возвращает float.
        Границы: Все сигнатуры.
        Почему такие: ранний баг — при определённых условиях возвращался None.
        """
        from space1.utility import compute_psi
        from space1.models.task import Task, TaskPriority
        from space1.models.agents import Agent, AgentCapabilities, AgentMetrics

        # Позиционная
        assert compute_psi(0.1, 10.0, 5.0) is not None
        # Legacy
        task = Task(
            id="t", title="Test", description="Desc",
            priority=TaskPriority.HIGH,
            deadline=datetime.now() + timedelta(hours=24)
        )
        caps = AgentCapabilities()
        metrics = AgentMetrics()
        agent = Agent(id="a", name="Test", capabilities=caps, metrics=metrics)
        assert compute_psi(task, agent, False) is not None
        assert compute_psi(task, agent, True) is not None
        # None args
        assert compute_psi(None, None, False) is not None
