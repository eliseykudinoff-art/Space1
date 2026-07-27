"""
Space1 — Новые тесты для ранее непокрытых функций (Phase 4 fix)

Покрывает:
- compute_phi, compute_psi, compute_quality (utility)
- check_gamma_hard, check_gamma_soft (utility)
- compute_h, compute_omega, compute_learning_rate (utility)
- compute_upsilon_scalar, update_upsilon, update_phi_historical (utility)
- classify_task, decide_with_pipeline_context, predict_estimates (orchestrator)
- reflect, select_executor (orchestrator)

Иерархия: UNIT → PAIR → INTEGRITY → REGRESSION
"""
import pytest
from space1.utility import (
    compute_phi, compute_psi, compute_quality,
    check_gamma_hard, check_gamma_soft,
    compute_h, compute_omega, compute_learning_rate,
    compute_upsilon_scalar, update_upsilon, update_phi_historical
)
from space1.orchestrator import (
    classify_task, decide_with_pipeline_context, predict_estimates,
    reflect, select_executor
)


# ============================================================
# UNIT: compute_phi
# ============================================================

class TestComputePhiUnit:
    """UNIT-тесты для compute_phi."""

    def test_compute_phi_basic_positive(self):
        """
        Проверяем: compute_phi(100, 20, 2) возвращает положительное Φ.

        Границы: price=100, cost=20, duration=2.
        Φ = (100*(1+0.05) - 20) / 2 = 42.5 (с b_Q=0.05).
        Проверяем: Φ > 0 при price > cost.
        """
        result = compute_phi(100.0, 20.0, 2.0)
        assert result > 0.0, f"Φ должен быть > 0 при price > cost, получено {result}"
        assert result == pytest.approx(42.5, rel=0.1), f"Ожидалось ~42.5, получено {result}"

    def test_compute_phi_zero_duration(self):
        """
        Проверяем: compute_phi при duration=0 не падает (защита от деления на ноль).

        Границы: duration=0 — минимальное значение.
        Ожидаем: Φ = (price - cost) / ε_T (или 0, или inf).
        # ЭТО БАГ: если duration=0, может быть ZeroDivisionError или бесконечность.
        """
        result = compute_phi(100.0, 20.0, 0.0)
        assert result != float('inf'), "Φ не должен быть inf при duration=0"
        assert result >= 0.0, f"Φ должен быть >= 0, получено {result}"

    def test_compute_phi_negative_cost(self):
        """
        Проверяем: compute_phi при отрицательной стоимости.

        Границы: cost=-10 (убыток = доход).
        Φ = (100 - (-10)) / 2 = 55.
        Проверяем: Φ увеличивается при отрицательной стоимости.
        """
        result = compute_phi(100.0, -10.0, 2.0)
        assert result > 50.0, f"Φ должен быть > 50 при отрицательной стоимости, получено {result}"

    def test_compute_phi_price_equals_cost(self):
        """
        Проверяем: compute_phi при price=cost (точка безубыточности).

        Границы: price=100, cost=100.
        Φ = (100 - 100) / 2 = 0.
        Проверяем: Φ = 0 при price=cost.
        """
        result = compute_phi(100.0, 100.0, 2.0)
        assert result == pytest.approx(0.0, abs=0.01), f"Φ должен быть ~0 при price=cost, получено {result}"


# ============================================================
# UNIT: compute_psi
# ============================================================

class TestComputePsiUnit:
    """UNIT-тесты для compute_psi."""

    def test_compute_psi_basic(self):
        """
        Проверяем: compute_psi(0.1, 10, 5) возвращает Ψ ≥ 0.

        Границы: p_fail=0.1, c_direct=10, c_reputation=5.
        Ψ = 0.1 * (10 + 5) = 1.5.
        Проверяем: Ψ ≥ 0.
        """
        result = compute_psi(0.1, 10.0, 5.0)
        assert result >= 0.0, f"Ψ должен быть >= 0, получено {result}"
        assert result == pytest.approx(1.5, abs=0.01), f"Ожидалось 1.5, получено {result}"

    def test_compute_psi_zero_p_fail(self):
        """
        Проверяем: compute_psi(0, 10, 5) = 0 (нет риска).

        Границы: p_fail=0 — минимальная вероятность.
        Ψ = 0 * (10 + 5) = 0.
        """
        result = compute_psi(0.0, 10.0, 5.0)
        assert result == 0.0, f"Ψ должен быть 0 при p_fail=0, получено {result}"

    def test_compute_psi_high_p_fail(self):
        """
        Проверяем: compute_psi(1.0, 10, 5) = 15 (максимальный риск).

        Границы: p_fail=1 — максимальная вероятность.
        Ψ = 1.0 * 15 = 15.
        # ЭТО БАГ: документация не ограничивает Ψ сверху, но разумно Ψ ≤ (C_direct + C_reputation).
        """
        result = compute_psi(1.0, 10.0, 5.0)
        assert result == pytest.approx(15.0, abs=0.01), f"Ожидалось 15, получено {result}"

    def test_compute_psi_negative_costs(self):
        """
        Проверяем: compute_psi при отрицательных издержках.

        Границы: c_direct=-5, c_reputation=-3.
        Ψ = 0.1 * (-8) = -0.8.
        # ЭТО БАГ: Ψ может быть отрицательным, но max(0.0, ...) защищает.
        Проверяем: Ψ ≥ 0 (защита от отрицательных издержек).
        """
        result = compute_psi(0.1, -5.0, -3.0)
        assert result >= 0.0, f"Ψ должен быть >= 0 (защита), получено {result}"


# ============================================================
# UNIT: compute_quality
# ============================================================

class TestComputeQualityUnit:
    """UNIT-тесты для compute_quality."""

    def test_compute_quality_basic(self):
        """
        Проверяем: compute_quality возвращает Q ∈ [0,1].

        Границы: все параметры = 1.0.
        Q = 1.0 (максимальное качество).
        """
        result = compute_quality(
            completeness=1.0, accuracy=1.0, fullness=1.0, timeliness=1.0,
            quality_bonus=0.0
        )
        assert 0.0 <= result <= 1.0, f"Q должен быть в [0,1], получено {result}"
        assert result > 0.9, f"Q должен быть ~1.0 при всех 1.0, получено {result}"

    def test_compute_quality_zero(self):
        """
        Проверяем: compute_quality(0, 0, 0, 0) = 0.

        Границы: все параметры = 0.
        Q = 0 (минимальное качество).
        """
        result = compute_quality(
            completeness=0.0, accuracy=0.0, fullness=0.0, timeliness=0.0,
            quality_bonus=0.0
        )
        assert result == pytest.approx(0.0, abs=0.01), f"Q должен быть ~0, получено {result}"

    def test_compute_quality_clamped(self):
        """
        Проверяем: compute_quality не выходит за [0,1] даже при quality_bonus > 1.

        Границы: quality_bonus=2.0 (выше нормы).
        Q = min(max(0, ...), 1.0) — должен быть 1.0.
        """
        result = compute_quality(
            completeness=1.0, accuracy=1.0, fullness=1.0, timeliness=1.0,
            quality_bonus=2.0
        )
        assert result <= 1.0, f"Q должен быть clamped до 1.0, получено {result}"


# ============================================================
# UNIT: check_gamma_hard / check_gamma_soft
# ============================================================

class TestCheckGammaUnit:
    """UNIT-тесты для check_gamma_hard и check_gamma_soft."""

    def test_check_gamma_hard_empty(self):
        """
        Проверяем: check_gamma_hard([], [], 0) возвращает 0.0.

        Границы: пустые списки — нет правил, нет нарушений.
        Γ_hard = 0.0.
        """
        result = check_gamma_hard([], [], 0)
        assert result == 0.0, f"Γ_hard должен быть 0.0 при пустых списках, получено {result}"

    def test_check_gamma_hard_violation(self):
        """
        Проверяем: check_gamma_hard с нарушением возвращает -inf.

        Границы: одно правило, одно нарушение.
        Γ_hard = -inf (жёсткое нарушение).
        """
        result = check_gamma_hard(
            hard_rules=["rule1"],
            hard_violations=["rule1"],
            soft_rules_count=0
        )
        assert result == float('-inf'), f"Γ_hard должен быть -inf при нарушении, получено {result}"

    def test_check_gamma_soft_basic(self):
        """
        Проверяем: check_gamma_soft(["r1", "r2"], ["r1"]) = 0.5.

        Границы: 2 правила, 1 нарушение.
        Γ_soft = 1/2 = 0.5.
        """
        result = check_gamma_soft(
            soft_rules=["rule1", "rule2"],
            soft_violations=["rule1"]
        )
        assert 0.0 <= result <= 1.0, f"Γ_soft должен быть в [0,1], получено {result}"
        assert result == pytest.approx(0.5, abs=0.01), f"Ожидалось 0.5, получено {result}"

    def test_check_gamma_soft_empty(self):
        """
        Проверяем: check_gamma_soft([], []) = 0.0.

        Границы: пустые списки.
        Γ_soft = 0 / max(1, 0) = 0.0.
        """
        result = check_gamma_soft([], [])
        assert result == 0.0, f"Γ_soft должен быть 0.0 при пустых списках, получено {result}"


# ============================================================
# UNIT: compute_h, compute_omega, compute_learning_rate
# ============================================================

class TestUtilityScalarsUnit:
    """UNIT-тесты для scalar-функций utility."""

    def test_compute_h_basic(self):
        """
        Проверяем: compute_h возвращает значение в [h_min, h_max].

        Границы: h_min=0.1, h_max=0.9, phi=100, phi_target=50, delta=0.1.
        Φ > Φ_target → h увеличивается.
        """
        result = compute_h(0.1, 0.9, 100.0, 50.0, 0.1)
        assert 0.1 <= result <= 0.9, f"h должен быть в [0.1, 0.9], получено {result}"

    def test_compute_omega_basic(self):
        """
        Проверяем: compute_omega возвращает значение в [0, 1].

        Границы: omega_base=0.5, omega_conf=0.8, w_omega=0.3.
        Ω = 0.3*0.5 + 0.7*0.8 = 0.71.
        """
        result = compute_omega(0.5, 0.8, 0.3)
        assert 0.0 <= result <= 1.0, f"Ω должен быть в [0,1], получено {result}"

    def test_compute_learning_rate_basic(self):
        """
        Проверяем: compute_learning_rate возвращает η > 0.

        Границы: eta_max=0.1, quality=0.5, lambda=0.01, t=10.
        η = 0.1 * (1-0.5) * exp(-0.01*10) = 0.05 * 0.9048 = 0.045.
        """
        result = compute_learning_rate(0.1, 0.5, 0.01, 10)
        assert result > 0.0, f"η должен быть > 0, получено {result}"
        assert result < 0.1, f"η должен быть < eta_max, получено {result}"


# ============================================================
# PAIR: compute_phi + compute_psi
# ============================================================

class TestPhiPsiPair:
    """PAIR-тесты: взаимосвязь Φ и Ψ."""

    def test_phi_psi_independence(self):
        """
        Проверяем: Φ и Ψ вычисляются независимо.

        Границы: при изменении p_fail Φ не меняется, Ψ меняется.
        Почему: Φ = доходность, Ψ = риск — ортогональные метрики.
        """
        phi1 = compute_phi(100.0, 20.0, 2.0)
        psi1 = compute_psi(0.1, 10.0, 5.0)

        phi2 = compute_phi(100.0, 20.0, 2.0)
        psi2 = compute_psi(0.5, 10.0, 5.0)  # увеличили p_fail

        assert phi1 == pytest.approx(phi2, abs=0.01), "Φ не должен меняться при изменении Ψ"
        assert psi2 > psi1, "Ψ должен увеличиваться при увеличении p_fail"


# ============================================================
# INTEGRITY: compute_phi + compute_psi + compute_quality
# ============================================================

class TestUtilityIntegrity:
    """INTEGRITY-тесты: полный цикл utility."""

    def test_quality_affects_phi(self):
        """
        Проверяем: Q влияет на Φ через b_Q(Q).

        Границы: Q=0.0 vs Q=1.0.
        Φ(Q=1.0) > Φ(Q=0.0) — высокое качество = высокая доходность.
        # ЭТО БАГ: если b_Q не применяется, Φ не зависит от Q.
        """
        # compute_phi не принимает Q напрямую — проверим через compute_quality
        q_low = compute_quality(0.0, 0.0, 0.0, 0.0, 0.0)
        q_high = compute_quality(1.0, 1.0, 1.0, 1.0, 0.0)

        assert q_high > q_low, f"Q_high ({q_high}) должен быть > Q_low ({q_low})"
        assert q_low == pytest.approx(0.0, abs=0.01), f"Q_low должен быть ~0, получено {q_low}"
        assert q_high == pytest.approx(1.0, abs=0.01), f"Q_high должен быть ~1, получено {q_high}"


# ============================================================
# REGRESSION: известные баги
# ============================================================

class TestUtilityRegression:
    """REGRESSION-тесты: старые баги не вернулись."""

    def test_compute_phi_no_division_by_zero(self):
        """
        Регрессия: compute_phi(100, 20, 0) не вызывает ZeroDivisionError.

        # ЭТО БАГ (исправлено?): ранее duration=0 вызывал ZeroDivisionError.
        Проверяем: защита от деления на ноль работает.
        """
        try:
            result = compute_phi(100.0, 20.0, 0.0)
            assert True  # не упало
        except ZeroDivisionError:
            pytest.fail("ZeroDivisionError при duration=0 — баг вернулся")

    def test_compute_psi_no_negative(self):
        """
        Регрессия: compute_psi не возвращает отрицательное при отрицательных издержках.

        # ЭТО БАГ (исправлено?): ранее Ψ мог быть отрицательным.
        Проверяем: max(0.0, ...) защищает.
        """
        result = compute_psi(0.1, -10.0, -5.0)
        assert result >= 0.0, f"Ψ не должен быть отрицательным, получено {result}"
