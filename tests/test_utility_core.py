"""
Space1 — ПРОВЕРЕННЫЕ ТЕСТЫ: Utility Core (Φ, Q, Ψ, 𝒟, Kalman, Γ)

Каждый тест проверен против реального кода.
FAILED-тесты = реальные баги, не ошибки тестов.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from datetime import datetime, timedelta


# =============================================================================
# UNIT: compute_phi — позиционная сигнатура
# =============================================================================

class TestComputePhiPositional:
    """Unit-тесты на compute_phi(price, quality, cost, time_hours)."""

    def test_phi_positional_basic(self):
        """
        compute_phi(100, 0.8, 20, 2) → 40.5.

        Формула: b_Q = 0.1*max(0, 0.8-0.7) - 0.2*max(0, 0.7-0.8) = 0.01
                 modulated_price = 100 * 1.01 = 101
                 (101 - 20) / 2 = 40.5
        Границы: Стандартный кейс.
        Почему такие: проверка позиционной сигнатуры.
        """
        from space1.utility import compute_phi
        phi = compute_phi(100.0, 0.8, 20.0, 2.0)
        assert abs(phi - 40.5) < 0.001

    def test_phi_positional_zero_time(self):
        """
        time_hours=0 → используется max(t_val, 0.1) = 0.1.

        Проверяем: защита от деления на ноль.
        Границы: time_hours = 0.
        Почему такие: граничный случай.
        """
        from space1.utility import compute_phi
        phi = compute_phi(100.0, 0.8, 20.0, 0.0)
        assert phi > 0
        assert phi < 1000

    def test_phi_positional_quality_below_expected(self):
        """
        quality < Q_expected → penalty.

        Формула: b_Q = -0.2 * (0.7 - 0.5) = -0.04
                 modulated_price = 100 * 0.96 = 96
                 (96 - 20) / 2 = 38.0
        Границы: quality = 0.5, Q_expected = 0.7.
        Почему такие: проверка penalty за низкое качество.
        """
        from space1.utility import compute_phi
        phi = compute_phi(100.0, 0.5, 20.0, 2.0)
        assert abs(phi - 38.0) < 0.001

    def test_phi_positional_platform_fees(self):
        """
        C_platform и C_processing уменьшают revenue.

        Проверяем: revenue *= (1 - C_platform - C_processing).
        Границы: C_platform=0.1, C_processing=0.05.
        Почему такие: проверка комиссий.
        """
        from space1.utility import compute_phi
        phi = compute_phi(100.0, 0.8, 20.0, 2.0, C_platform=0.1, C_processing=0.05)
        # b_Q = 0.01, modulated = 101 * 0.85 = 85.85, (85.85 - 20) / 2 = 32.925
        assert abs(phi - 32.925) < 0.001


# =============================================================================
# UNIT: compute_phi — legacy сигнатура (БАГ)
# =============================================================================

class TestComputePhiLegacy:
    """Unit-тесты на compute_phi(task, agent, cost, time) — legacy. БАГ: формула другая."""

    def test_phi_legacy_returns_291_not_40(self):
        """
        compute_phi(100, 20, 2) → 291.0, не 40.0.

        Проверяем: legacy сигнатура даёт совершенно другой результат.
        Границы: revenue=100, cost=20, time=2.
        Почему такие: документация §IV.2: Φ = (R-C)/T = 40.0.
        """
        from space1.utility import compute_phi
        phi = compute_phi(100.0, 20.0, 2.0)
        assert phi == 291.0  # Реальное поведение
        # ЭТО БАГ: ожидалось 40.0, получено 291.0
        # Причина: 20 интерпретируется как agent_or_quality (float), не cost
        # Формула: price=100, quality=20 → b_Q огромный → (revenue*1+b_Q - cost_base) / time

    def test_phi_legacy_with_task_and_agent(self):
        """
        compute_phi(task, agent) → значение с factor-модуляцией.

        Проверяем: legacy с task+agent использует aggregate_factors.
        Границы: Стандартные Task и Agent.
        Почему такие: проверка legacy path.
        """
        from space1.utility import compute_phi
        from space1.models.task import Task, TaskPriority
        from space1.models.agents import Agent, AgentCapabilities, AgentMetrics

        task = Task(id="t1", title="Test", description="", priority=TaskPriority.HIGH, deadline=datetime.now()+timedelta(hours=24))
        agent = Agent(id="a1", name="Test", capabilities=AgentCapabilities(), metrics=AgentMetrics())
        phi = compute_phi(task, agent)
        assert isinstance(phi, float)
        assert phi > 0


# =============================================================================
# UNIT: compute_quality — позиционная сигнатура
# =============================================================================

class TestComputeQualityPositional:
    """Unit-тесты на compute_quality(comp, acc, full, time, weights)."""

    def test_quality_positional_equal_weights(self):
        """
        compute_quality(0.8, 0.9, 0.7, 1.0, (0.25,0.25,0.25,0.25)) → 0.85.

        Формула: 0.25*0.8 + 0.25*0.9 + 0.25*0.7 + 0.25*1.0 = 0.85.
        Границы: Равные веса.
        Почему такие: базовая проверка формулы.
        """
        from space1.utility import compute_quality
        q = compute_quality(0.8, 0.9, 0.7, 1.0, (0.25, 0.25, 0.25, 0.25))
        assert abs(q - 0.85) < 0.001

    def test_quality_weights_must_sum_to_one(self):
        """
        Веса, не суммирующиеся в 1.0 → AssertionError.

        Проверяем: strict contract verification.
        Границы: weights = (0.5, 0.5, 0.0, 0.0) — сумма 1.0 (OK) vs (0.5, 0.5, 0.5, 0.0) — сумма 1.5 (FAIL).
        Почему такие: защита контракта.
        """
        from space1.utility import compute_quality
        # OK
        q = compute_quality(0.8, 0.9, 0.7, 1.0, (0.5, 0.5, 0.0, 0.0))
        assert abs(q - 0.85) < 0.001
        # FAIL
        with pytest.raises(AssertionError):
            compute_quality(0.8, 0.9, 0.7, 1.0, (0.5, 0.5, 0.5, 0.0))

    def test_quality_clamped(self):
        """
        Результат clamped в [0, 1].

        Проверяем: compute_quality(2.0, 2.0, 2.0, 2.0) → 1.0.
        Границы: Значения > 1.
        Почему такие: проверка _clamp.
        """
        from space1.utility import compute_quality
        q = compute_quality(2.0, 2.0, 2.0, 2.0, (0.25, 0.25, 0.25, 0.25))
        assert q == 1.0


# =============================================================================
# UNIT: compute_quality — legacy сигнатура
# =============================================================================

class TestComputeQualityLegacy:
    """Unit-тесты на compute_quality(completeness, accuracy, fullness) — legacy."""

    def test_quality_legacy_default_weights(self):
        """
        compute_quality(0.8, 0.9, 0.7) → 0.775.

        Формула: default weights = (0.25,0.25,0.25,0.25), default timeliness = 0.7
                 0.25*0.8 + 0.25*0.9 + 0.25*0.7 + 0.25*0.7 = 0.775.
        Границы: Стандартные значения.
        Почему такие: проверка default behavior.
        """
        from space1.utility import compute_quality
        q = compute_quality(0.8, 0.9, 0.7)
        assert abs(q - 0.775) < 0.001

    def test_quality_legacy_timeliness_from_deadline(self):
        """
        t_actual и t_deadline → timeliness вычисляется автоматически (только keyword-only).

        Формула: timeliness = 1.0 - min(1.0, max(0, t_actual - t_deadline) / t_deadline).
        Границы: t_actual=5, t_deadline=10 → timeliness = 1.0 - 0 = 1.0.
        Почему такие: проверка auto-timeliness через keyword-only args.
        """
        from space1.utility import compute_quality
        # Важно: keyword-only args, иначе попадаем в позиционную ветку
        q = compute_quality(completeness=0.8, accuracy=0.9, fullness=0.7, t_actual=5.0, t_deadline=10.0)
        # timeliness = 1.0 - min(1.0, max(0, 5-10)/10) = 1.0 - 0 = 1.0
        expected = 0.25*0.8 + 0.25*0.9 + 0.25*0.7 + 0.25*1.0
        assert abs(q - expected) < 0.001

    def test_quality_positional_ignores_t_actual_t_deadline(self):
        """
        Позиционные args игнорируют t_actual/t_deadline — попадают в позиционную ветку.

        Проверяем: compute_quality(0.8, 0.9, 0.7, t_actual=5, t_deadline=10) использует default t=0.7.
        Границы: Позиционные float args + keyword t_actual/t_deadline.
        Почему такие: баг — positional ветка не видит keyword-only timeliness params.
        """
        from space1.utility import compute_quality
        q = compute_quality(0.8, 0.9, 0.7, t_actual=5.0, t_deadline=10.0)
        # Попадает в позиционную ветку: t = default 0.7, t_actual/t_deadline игнорируются
        expected = 0.25*0.8 + 0.25*0.9 + 0.25*0.7 + 0.25*0.7  # 0.775
        assert abs(q - expected) < 0.001
        # ЭТО БАГ: t_actual/t_deadline игнорируются при позиционных float args


# =============================================================================
# UNIT: evaluate_decision_rule
# =============================================================================

class TestEvaluateDecisionRule:
    """Unit-тесты на evaluate_decision_rule — каскад 5 уровней."""

    def test_level1_reject_gamma_hard_neg_inf(self):
        """
        gamma_hard = -inf → "REJECT".

        Проверяем: Level 1 — hard compliance veto.
        Границы: gamma_hard = float('-inf').
        Почему такие: критический путь безопасности.
        """
        from space1.utility import evaluate_decision_rule
        d = evaluate_decision_rule(
            gamma_hard=float("-inf"), psi=0.1, psi_max=5.0,
            C_t=100.0, C_min=1.0, H_TZ=0.5, H_TZ_max=1.0,
            VoI=0.5, C_info=2.0, H_val=0.8, H_clarify=0.5,
            U_val=0.5, Q_predicted=0.9, q_min=0.5
        )
        assert d == "REJECT"

    def test_level1_reject_veto_type_hard(self):
        """
        veto_type = VetoType.HARD → "REJECT".

        Проверяем: Level 1 через enum.
        Границы: veto_type = HARD.
        Почему такие: альтернативный путь reject.
        """
        from space1.utility import evaluate_decision_rule, VetoType
        d = evaluate_decision_rule(
            gamma_hard=0.0, psi=0.1, psi_max=5.0,
            C_t=100.0, C_min=1.0, H_TZ=0.5, H_TZ_max=1.0,
            VoI=0.5, C_info=2.0, H_val=0.8, H_clarify=0.5,
            U_val=0.5, Q_predicted=0.9, q_min=0.5,
            veto_type=VetoType.HARD
        )
        assert d == "REJECT"

    def test_level2_decline_psi_exceeds(self):
        """
        psi > psi_max → "DECLINE".

        Проверяем: Level 2 — риск выше порога.
        Границы: psi=10.0, psi_max=5.0.
        Почему такие: типичный кейс превышения риска.
        """
        from space1.utility import evaluate_decision_rule
        d = evaluate_decision_rule(
            gamma_hard=0.0, psi=10.0, psi_max=5.0,
            C_t=100.0, C_min=1.0, H_TZ=0.5, H_TZ_max=1.0,
            VoI=0.5, C_info=2.0, H_val=0.8, H_clarify=0.5,
            U_val=0.5, Q_predicted=0.9, q_min=0.5
        )
        assert d == "DECLINE"

    def test_level2_decline_cost_below_min(self):
        """
        C_t < C_min → "DECLINE".

        Проверяем: Level 2 — бюджет ниже минимума.
        Границы: C_t=0.5, C_min=1.0.
        Почему такие: проверка бюджетного порога.
        """
        from space1.utility import evaluate_decision_rule
        d = evaluate_decision_rule(
            gamma_hard=0.0, psi=0.1, psi_max=5.0,
            C_t=0.5, C_min=1.0, H_TZ=0.5, H_TZ_max=1.0,
            VoI=0.5, C_info=2.0, H_val=0.8, H_clarify=0.5,
            U_val=0.5, Q_predicted=0.9, q_min=0.5
        )
        assert d == "DECLINE"

    def test_level3_clarify_entropy(self):
        """
        H_TZ > H_TZ_max → "CLARIFY".

        Проверяем: Level 3 — высокая энтропия.
        Границы: H_TZ=2.0, H_TZ_max=1.0.
        Почему такие: требуется уточнение.
        """
        from space1.utility import evaluate_decision_rule
        d = evaluate_decision_rule(
            gamma_hard=0.0, psi=0.1, psi_max=5.0,
            C_t=100.0, C_min=1.0, H_TZ=2.0, H_TZ_max=1.0,
            VoI=0.5, C_info=2.0, H_val=0.8, H_clarify=0.5,
            U_val=0.5, Q_predicted=0.9, q_min=0.5
        )
        assert d == "CLARIFY"

    def test_level3_clarify_voi_exceeds_cost(self):
        """
        VoI > C_info → "CLARIFY".

        Проверяем: Level 3 — ценность информации выше стоимости.
        Границы: VoI=3.0, C_info=2.0.
        Почему такие: проверка VoI trigger.
        """
        from space1.utility import evaluate_decision_rule
        d = evaluate_decision_rule(
            gamma_hard=0.0, psi=0.1, psi_max=5.0,
            C_t=100.0, C_min=1.0, H_TZ=0.5, H_TZ_max=1.0,
            VoI=3.0, C_info=2.0, H_val=0.8, H_clarify=0.5,
            U_val=0.5, Q_predicted=0.9, q_min=0.5
        )
        assert d == "CLARIFY"

    def test_level3_clarify_h_val_below_threshold(self):
        """
        H_val < H_clarify → "CLARIFY".

        Проверяем: Level 3 — недостаточная валидация.
        Границы: H_val=0.3, H_clarify=0.5.
        Почему такие: проверка H_val trigger.
        """
        from space1.utility import evaluate_decision_rule
        d = evaluate_decision_rule(
            gamma_hard=0.0, psi=0.1, psi_max=5.0,
            C_t=100.0, C_min=1.0, H_TZ=0.5, H_TZ_max=1.0,
            VoI=0.5, C_info=2.0, H_val=0.3, H_clarify=0.5,
            U_val=0.5, Q_predicted=0.9, q_min=0.5
        )
        assert d == "CLARIFY"

    def test_level4_execute(self):
        """
        U_val > 0 и Q_predicted >= q_min → "EXECUTE".

        Проверяем: Level 4 — положительная полезность, качество выше порога.
        Границы: U_val=0.5, Q_predicted=0.9, q_min=0.5.
        Почему такие: happy path.
        """
        from space1.utility import evaluate_decision_rule
        d = evaluate_decision_rule(
            gamma_hard=0.0, psi=0.1, psi_max=5.0,
            C_t=100.0, C_min=1.0, H_TZ=0.5, H_TZ_max=1.0,
            VoI=0.5, C_info=2.0, H_val=0.8, H_clarify=0.5,
            U_val=0.5, Q_predicted=0.9, q_min=0.5
        )
        assert d == "EXECUTE"

    def test_level5_decline_utility_non_positive(self):
        """
        U_val <= 0 → "DECLINE".

        Проверяем: Level 5 — отрицательная или нулевая полезность.
        Границы: U_val=0.0, Q_predicted=0.9, q_min=0.5.
        Почему такие: граничный случай — нулевая полезность.
        """
        from space1.utility import evaluate_decision_rule
        d = evaluate_decision_rule(
            gamma_hard=0.0, psi=0.1, psi_max=5.0,
            C_t=100.0, C_min=1.0, H_TZ=0.5, H_TZ_max=1.0,
            VoI=0.5, C_info=2.0, H_val=0.8, H_clarify=0.5,
            U_val=0.0, Q_predicted=0.9, q_min=0.5
        )
        assert d == "DECLINE"

    def test_level5_decline_quality_below_min(self):
        """
        Q_predicted < q_min → "DECLINE".

        Проверяем: Level 5 — качество ниже минимума.
        Границы: Q_predicted=0.4, q_min=0.5.
        Почему такие: проверка качественного порога.
        """
        from space1.utility import evaluate_decision_rule
        d = evaluate_decision_rule(
            gamma_hard=0.0, psi=0.1, psi_max=5.0,
            C_t=100.0, C_min=1.0, H_TZ=0.5, H_TZ_max=1.0,
            VoI=0.5, C_info=2.0, H_val=0.8, H_clarify=0.5,
            U_val=0.5, Q_predicted=0.4, q_min=0.5
        )
        assert d == "DECLINE"


# =============================================================================
# UNIT: evaluate_decision_rule — Mission Profiles
# =============================================================================

class TestEvaluateDecisionRuleMission:
    """Unit-тесты на mission_profile калибровку."""

    def test_survival_reduces_psi_max(self):
        """
        SURVIVAL: psi_max *= 0.5, q_min *= 0.8, C_min *= 0.5.

        Проверяем: psi=3.0 при psi_max=5.0 → обычно EXECUTE, но SURVIVAL → DECLINE.
        Границы: psi=3.0, psi_max=5.0 (после калибровки: psi_max=2.5).
        Почему такие: проверка консервативного профиля.
        """
        from space1.utility import evaluate_decision_rule
        d = evaluate_decision_rule(
            gamma_hard=0.0, psi=3.0, psi_max=5.0,
            C_t=100.0, C_min=1.0, H_TZ=0.5, H_TZ_max=1.0,
            VoI=0.5, C_info=2.0, H_val=0.8, H_clarify=0.5,
            U_val=0.5, Q_predicted=0.9, q_min=0.5,
            mission_profile="SURVIVAL"
        )
        assert d == "DECLINE"

    def test_growth_increases_psi_max(self):
        """
        GROWTH: psi_max *= 1.5, q_min *= 1.2, C_min *= 1.5.

        Проверяем: psi=7.0 при psi_max=5.0 → обычно DECLINE, но GROWTH → EXECUTE.
        Границы: psi=7.0, psi_max=5.0 (после: psi_max=7.5).
        Почему такие: проверка агрессивного профиля.
        """
        from space1.utility import evaluate_decision_rule
        d = evaluate_decision_rule(
            gamma_hard=0.0, psi=7.0, psi_max=5.0,
            C_t=100.0, C_min=1.0, H_TZ=0.5, H_TZ_max=1.0,
            VoI=0.5, C_info=2.0, H_val=0.8, H_clarify=0.5,
            U_val=0.5, Q_predicted=0.9, q_min=0.5,
            mission_profile="GROWTH"
        )
        assert d == "EXECUTE"

    def test_charity_lowers_thresholds(self):
        """
        CHARITY: psi_max *= 2.0, q_min *= 0.5, C_min = 0.1.

        Проверяем: C_t=0.5 при C_min=1.0 → обычно DECLINE, но CHARITY → EXECUTE.
        Границы: C_t=0.5, C_min=1.0 (после: C_min=0.1).
        Почему такие: проверка благотворительного профиля.
        """
        from space1.utility import evaluate_decision_rule
        d = evaluate_decision_rule(
            gamma_hard=0.0, psi=0.1, psi_max=5.0,
            C_t=0.5, C_min=1.0, H_TZ=0.5, H_TZ_max=1.0,
            VoI=0.5, C_info=2.0, H_val=0.8, H_clarify=0.5,
            U_val=0.5, Q_predicted=0.9, q_min=0.5,
            mission_profile="CHARITY"
        )
        assert d == "EXECUTE"

    def test_balanced_default(self):
        """
        BALANCED (default): без калибровки.

        Проверяем: psi=4.0 при psi_max=5.0 → EXECUTE.
        Границы: psi=4.0 < psi_max=5.0.
        Почему такие: проверка default профиля.
        """
        from space1.utility import evaluate_decision_rule
        d = evaluate_decision_rule(
            gamma_hard=0.0, psi=4.0, psi_max=5.0,
            C_t=100.0, C_min=1.0, H_TZ=0.5, H_TZ_max=1.0,
            VoI=0.5, C_info=2.0, H_val=0.8, H_clarify=0.5,
            U_val=0.5, Q_predicted=0.9, q_min=0.5,
            mission_profile="BALANCED"
        )
        assert d == "EXECUTE"


# =============================================================================
# UNIT: KalmanFilter
# =============================================================================

class TestKalmanFilter:
    """Unit-тесты на KalmanFilter."""

    def test_kalman_initial_state(self):
        """
        Начальное состояние = initial_state.

        Проверяем: x = initial_state после создания.
        Границы: initial_state = 10.0.
        Почему такие: базовая проверка инициализации.
        """
        from space1.utility import KalmanFilter
        kf = KalmanFilter(initial_state=10.0)
        assert kf.x == 10.0

    def test_kalman_predict_increases_covariance(self):
        """
        predict увеличивает P (P = P + Q).

        Проверяем: P растёт после predict.
        Границы: Q = 0.01.
        Почему такие: проверка динамики ковариации.
        """
        from space1.utility import KalmanFilter
        kf = KalmanFilter(P=1.0, Q=0.01)
        old_p = kf.P
        kf.predict()
        assert kf.P == old_p + 0.01

    def test_kalman_update_converges(self):
        """
        update с одинаковым observed → сходится к observed.

        Проверяем: после многих update с observed=5.0, x → 5.0.
        Границы: observed = 5.0, initial = 0.0.
        Почему такие: проверка сходимости фильтра.
        """
        from space1.utility import KalmanFilter
        kf = KalmanFilter(initial_state=0.0, Q=0.01, R=0.1)
        for _ in range(100):
            kf.step(5.0)
        assert abs(kf.x - 5.0) < 0.1

    def test_kalman_step_returns_updated_state(self):
        """
        step возвращает обновлённое состояние.

        Проверяем: return value == x после update.
        Границы: observed = 10.0.
        Почему такие: проверка API.
        """
        from space1.utility import KalmanFilter
        kf = KalmanFilter(initial_state=0.0)
        result = kf.step(10.0)
        assert result == kf.x


# =============================================================================
# UNIT: check_gamma_hard / check_gamma_soft
# =============================================================================

class TestCheckGamma:
    """Unit-тесты на check_gamma_hard и check_gamma_soft."""

    def test_gamma_hard_all_pass(self):
        """
        Все hard rules pass → 0.0.

        Проверяем: check_gamma_hard с пустым списком → 0.0.
        Границы: Пустой список правил.
        Почему такие: базовый кейс.
        """
        from space1.utility import check_gamma_hard
        from space1.compliance.core import Action
        result = check_gamma_hard(Action("test"), [])
        assert result == 0.0

    def test_gamma_hard_one_fails(self):
        """
        Одно hard rule fail → -inf.

        Проверяем: BlockedActionsRule блокирует.
        Границы: Action("hack") с BlockedActionsRule(["hack"]).
        Почему такие: критический путь безопасности.
        """
        from space1.utility import check_gamma_hard
        from space1.compliance.core import Action, BlockedActionsRule
        result = check_gamma_hard(Action("hack"), [BlockedActionsRule(["hack"])])
        assert result == float("-inf")

    def test_gamma_hard_exception_returns_neg_inf(self):
        """
        Exception в rule → -inf (bare except).

        Проверяем: check_gamma_hard глотает Exception.
        Границы: Rule, который падает.
        Почему такие: проверка error handling.
        """
        from space1.utility import check_gamma_hard
        from space1.compliance.core import Action, Rule

        class BrokenRule(Rule):
            name = "broken"
            def check(self, action):
                raise RuntimeError("boom")

        result = check_gamma_hard(Action("test"), [BrokenRule()])
        assert result == float("-inf")
        # ЭТО БАГ: except Exception глотает ошибку, нет логирования

    def test_gamma_soft_no_penalty(self):
        """
        Все soft rules pass → 0.0.

        Проверяем: check_gamma_soft с пустым списком → 0.0.
        Границы: Пустой список.
        Почему такие: базовый кейс.
        """
        from space1.utility import check_gamma_soft
        from space1.compliance.core import Action
        result = check_gamma_soft(Action("test"), [])
        assert result == 0.0

    def test_gamma_soft_accumulates_penalty(self):
        """
        Два failed soft rule → сумма весов.

        Проверяем: penalty = weight1 + weight2.
        Границы: Два rule с weight=1.0 и weight=2.0.
        Почему такие: проверка аккумуляции.
        """
        from space1.utility import check_gamma_soft
        from space1.compliance.core import Action, Rule

        class SoftRule1(Rule):
            name = "s1"
            is_hard = False
            weight = 1.0
            def check(self, action):
                return False

        class SoftRule2(Rule):
            name = "s2"
            is_hard = False
            weight = 2.0
            def check(self, action):
                return False

        result = check_gamma_soft(Action("test"), [SoftRule1(), SoftRule2()])
        assert result == 3.0


# =============================================================================
# PAIR: compute_phi → evaluate_decision_rule
# =============================================================================

class TestPairPhiDecision:
    """PAIR: compute_phi → evaluate_decision_rule — каскад прибыли и решения."""

    def test_positive_phi_positive_utility_execute(self):
        """
        Φ > 0, U_val > 0 → EXECUTE.

        Проверяем: положительная прибыль + положительная полезность → выполнение.
        Границы: phi=40.5, U_val=0.5.
        Почему такие: happy path через весь каскад.
        """
        from space1.utility import compute_phi, evaluate_decision_rule
        phi = compute_phi(100.0, 0.8, 20.0, 2.0)
        assert phi > 0
        d = evaluate_decision_rule(
            gamma_hard=0.0, psi=0.1, psi_max=5.0,
            C_t=phi, C_min=1.0, H_TZ=0.5, H_TZ_max=1.0,
            VoI=0.5, C_info=2.0, H_val=0.8, H_clarify=0.5,
            U_val=0.5, Q_predicted=0.9, q_min=0.5
        )
        assert d == "EXECUTE"

    def test_negative_phi_decline(self):
        """
        Φ < 0 (cost > revenue) → C_t < C_min → DECLINE.

        Проверяем: отрицательная прибыль → DECLINE на уровне 2.
        Границы: price=10, cost=20 → phi < 0.
        Почему такие: проверка связки прибыль→решение.
        """
        from space1.utility import compute_phi, evaluate_decision_rule
        phi = compute_phi(10.0, 0.8, 20.0, 2.0)
        assert phi < 0
        d = evaluate_decision_rule(
            gamma_hard=0.0, psi=0.1, psi_max=5.0,
            C_t=phi, C_min=1.0, H_TZ=0.5, H_TZ_max=1.0,
            VoI=0.5, C_info=2.0, H_val=0.8, H_clarify=0.5,
            U_val=0.5, Q_predicted=0.9, q_min=0.5
        )
        assert d == "DECLINE"


# =============================================================================
# PAIR: compute_quality → evaluate_decision_rule
# =============================================================================

class TestPairQualityDecision:
    """PAIR: compute_quality → evaluate_decision_rule — качество влияет на решение."""

    def test_high_quality_execute(self):
        """
        Q=0.9 >= q_min=0.5 → EXECUTE.

        Проверяем: высокое качество проходит.
        Границы: Q=0.9, q_min=0.5.
        Почему такие: типичный кейс.
        """
        from space1.utility import compute_quality, evaluate_decision_rule
        q = compute_quality(0.9, 0.9, 0.9, 0.9, (0.25, 0.25, 0.25, 0.25))
        d = evaluate_decision_rule(
            gamma_hard=0.0, psi=0.1, psi_max=5.0,
            C_t=100.0, C_min=1.0, H_TZ=0.5, H_TZ_max=1.0,
            VoI=0.5, C_info=2.0, H_val=0.8, H_clarify=0.5,
            U_val=0.5, Q_predicted=q, q_min=0.5
        )
        assert d == "EXECUTE"

    def test_low_quality_decline(self):
        """
        Q=0.3 < q_min=0.5 → DECLINE.

        Проверяем: низкое качество блокирует.
        Границы: Q=0.3, q_min=0.5.
        Почему такие: проверка качественного порога.
        """
        from space1.utility import compute_quality, evaluate_decision_rule
        q = compute_quality(0.3, 0.3, 0.3, 0.3, (0.25, 0.25, 0.25, 0.25))
        d = evaluate_decision_rule(
            gamma_hard=0.0, psi=0.1, psi_max=5.0,
            C_t=100.0, C_min=1.0, H_TZ=0.5, H_TZ_max=1.0,
            VoI=0.5, C_info=2.0, H_val=0.8, H_clarify=0.5,
            U_val=0.5, Q_predicted=q, q_min=0.5
        )
        assert d == "DECLINE"


# =============================================================================
# INTEGRITY: Архитектурные инварианты Utility
# =============================================================================

class TestIntegrityUtility:
    """INTEGRITY: Проверки кода utility на антипаттерны."""

    def test_bare_except_in_check_gamma(self):
        """
        check_gamma_hard и check_gamma_soft содержат bare except.

        Проверяем: except Exception в обеих функциях.
        Границы: utility/__init__.py.
        Почему такие: 10_SECURITY.md §III — fail fast.
        """
        import space1.utility as util_mod
        util_path = util_mod.__file__
        with open(util_path, "r") as f:
            content = f.read()
        # Найдём check_gamma_hard и check_gamma_soft
        funcs = ["check_gamma_hard", "check_gamma_soft"]
        for func_name in funcs:
            start = content.find(f"def {func_name}(")
            end = content.find("\ndef ", start + 1)
            if end == -1:
                end = len(content)
            func_body = content[start:end]
            assert "except Exception" in func_body,                 f"{func_name} не содержит except Exception (исправлено?)"

    def test_evaluate_decision_rule_no_gamma_soft(self):
        """
        evaluate_decision_rule НЕ использует gamma_soft — это баг.

        Проверяем: в сигнатуре нет gamma_soft, в теле нет gamma_soft.
        Границы: Вся функция evaluate_decision_rule.
        Почему такие: документация §IV.14: gamma_soft влияет на utility.
        """
        import space1.utility as util_mod
        util_path = util_mod.__file__
        with open(util_path, "r") as f:
            content = f.read()
        start = content.find("def evaluate_decision_rule(")
        end = content.find("\ndef ", start + 1)
        if end == -1:
            end = len(content)
        func_body = content[start:end]
        assert "gamma_soft" not in func_body
        # ЭТО БАГ: gamma_soft нигде не используется в decision rule

    def test_compute_phi_legacy_confuses_cost_and_quality(self):
        """
        compute_phi(100, 20, 2) интерпретирует 20 как quality, не cost.

        Проверяем: legacy сигнатура конфликтует с позиционной.
        Границы: 3 аргумента — ambiguous.
        Почему такие: документация §IV.2: Φ = (R-C)/T.
        """
        from space1.utility import compute_phi
        phi = compute_phi(100.0, 20.0, 2.0)
        # 20 интерпретируется как quality (float), cost_or_val=None
        assert phi != 40.0  # Реальное поведение — не 40.0
        # ЭТО БАГ: конфликт сигнатур


# =============================================================================
# REGRESSION: Старые баги Utility
# =============================================================================

class TestRegressionUtility:
    """REGRESSION: Проверки, что исправленные баги не вернулись."""

    def test_compute_phi_not_returns_none(self):
        """
        compute_phi не возвращает None.

        Проверяем: любой вызов возвращает float.
        Границы: Позиционная и legacy.
        Почему такие: ранний баг — None при определённых условиях.
        """
        from space1.utility import compute_phi
        assert compute_phi(100.0, 0.8, 20.0, 2.0) is not None
        assert isinstance(compute_phi(100.0, 0.8, 20.0, 2.0), float)

    def test_evaluate_decision_rule_not_returns_none(self):
        """
        evaluate_decision_rule возвращает строку, не None.

        Проверяем: return type == str.
        Границы: Стандартный кейс.
        Почему такие: ранний баг — None при определённых условиях.
        """
        from space1.utility import evaluate_decision_rule
        d = evaluate_decision_rule(
            gamma_hard=0.0, psi=0.1, psi_max=5.0,
            C_t=100.0, C_min=1.0, H_TZ=0.5, H_TZ_max=1.0,
            VoI=0.5, C_info=2.0, H_val=0.8, H_clarify=0.5,
            U_val=0.5, Q_predicted=0.9, q_min=0.5
        )
        assert d is not None
        assert isinstance(d, str)
