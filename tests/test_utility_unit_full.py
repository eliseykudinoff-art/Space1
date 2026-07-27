"""
Space1 — UNIT-тесты для utility/__init__.py (отдельный тест на каждую функцию)

Правила:
- Имя теста = утверждение (test_<глагол>_<что>_<условие>)
- Докстринг = контракт + границы + обоснование
- Проверяем значения, не типы
- Граничные значения: 0, None, пустые, отрицательные
- # ЭТО БАГ при расхождении с документацией
"""
import pytest
from space1.utility import (
    compute_phi, compute_psi, compute_quality,
    check_gamma_hard, check_gamma_soft,
    compute_h, compute_omega, compute_learning_rate,
    compute_upsilon_scalar, update_upsilon, update_phi_historical,
    evaluate_decision_rule
)
from space1.models.agents import ReputationVector


# ============================================================
# compute_phi
# ============================================================

class TestComputePhiUnit:
    """UNIT-тесты для compute_phi."""

    def test_compute_phi_returns_positive_when_profit(self):
        """
        Проверяем: compute_phi(100, 20, 2) возвращает Φ > 0 при доходе > издержек.

        Границы: price=100, cost=20, duration=2.
        Φ = (100*(1+0.05) - 20) / 2 = 42.5.
        Почему: базовый случай — положительная доходность.
        """
        result = compute_phi(100.0, 20.0, 2.0)
        assert result > 0.0, f"Φ должен быть > 0, получено {result}"

    def test_compute_phi_returns_zero_at_breakeven(self):
        """
        Проверяем: compute_phi(100, 100, 2) возвращает Φ ≈ 0 при равенстве дохода и издержек.

        Границы: price=cost=100.
        Φ = (100 - 100) / 2 = 0.
        Почему: точка безубыточности — граница между прибылью и убытком.
        """
        result = compute_phi(100.0, 100.0, 2.0)
        assert result == pytest.approx(0.0, abs=0.01), f"Φ должен быть ~0, получено {result}"

    def test_compute_phi_zero_duration_no_crash(self):
        """
        Проверяем: compute_phi(100, 20, 0) не падает с ZeroDivisionError.

        Границы: duration=0 — минимальное значение.
        # ЭТО БАГ: документация требует max(ε_T, T), но реализация может не защищать.
        Почему: деление на ноль — критическая ошибка, должна быть защита.
        """
        try:
            result = compute_phi(100.0, 20.0, 0.0)
            assert result >= 0.0, f"Φ должен быть >= 0, получено {result}"
        except ZeroDivisionError:
            pytest.fail("ZeroDivisionError при duration=0 — нет защиты от деления на ноль")

    def test_compute_phi_negative_cost_increases_profit(self):
        """
        Проверяем: compute_phi(100, -10, 2) возвращает Φ > 50 при отрицательной стоимости.

        Границы: cost=-10 (убыток превращается в доход).
        Φ = (100 - (-10)) / 2 = 55.
        Почему: отрицательные издержки = субсидия, должна увеличивать Φ.
        """
        result = compute_phi(100.0, -10.0, 2.0)
        assert result > 50.0, f"Φ должен быть > 50, получено {result}"

    def test_compute_phi_none_price_raises_error(self):
        """
        Проверяем: compute_phi(None, 20, 2) вызывает TypeError.

        Границы: price=None — невалидный вход.
        Почему: None вместо числа — ошибка вызывающего, должна всплыть.
        """
        with pytest.raises(TypeError):
            compute_phi(None, 20.0, 2.0)


# ============================================================
# compute_psi
# ============================================================

class TestComputePsiUnit:
    """UNIT-тесты для compute_psi."""

    def test_compute_psi_returns_nonnegative(self):
        """
        Проверяем: compute_psi(0.1, 10, 5) возвращает Ψ >= 0.

        Границы: p_fail=0.1, c_direct=10, c_reputation=5.
        Ψ = 0.1 * 15 = 1.5.
        Почему: риск не может быть отрицательным.
        """
        result = compute_psi(0.1, 10.0, 5.0)
        assert result >= 0.0, f"Ψ должен быть >= 0, получено {result}"

    def test_compute_psi_zero_risk_is_zero(self):
        """
        Проверяем: compute_psi(0, 10, 5) возвращает Ψ = 0.

        Границы: p_fail=0 — нет риска.
        Ψ = 0 * 15 = 0.
        Почему: нулевая вероятность = нулевой риск.
        """
        result = compute_psi(0.0, 10.0, 5.0)
        assert result == 0.0, f"Ψ должен быть 0, получено {result}"

    def test_compute_psi_max_risk_equals_total_cost(self):
        """
        Проверяем: compute_psi(1.0, 10, 5) возвращает Ψ = 15.

        Границы: p_fail=1 — максимальный риск.
        Ψ = 1.0 * 15 = 15.
        Почему: гарантированный провал = полные издержки.
        """
        result = compute_psi(1.0, 10.0, 5.0)
        assert result == pytest.approx(15.0, abs=0.01), f"Ψ должен быть 15, получено {result}"

    def test_compute_psi_negative_costs_clamped_to_zero(self):
        """
        Проверяем: compute_psi(0.1, -5, -3) возвращает Ψ >= 0 (защита от отрицательных издержек).

        Границы: c_direct=-5, c_reputation=-3.
        # ЭТО БАГ: документация не описывает отрицательные издержки, но max(0.0, ...) защищает.
        Почему: отрицательные издержки — невалидный вход, но не должны ломать систему.
        """
        result = compute_psi(0.1, -5.0, -3.0)
        assert result >= 0.0, f"Ψ должен быть >= 0 (защита), получено {result}"

    def test_compute_psi_none_p_fail_raises_error(self):
        """
        Проверяем: compute_psi(None, 10, 5) вызывает TypeError.

        Границы: p_fail=None — невалидный вход.
        Почему: None вместо числа — ошибка вызывающего.
        """
        with pytest.raises(TypeError):
            compute_psi(None, 10.0, 5.0)


# ============================================================
# compute_quality
# ============================================================

class TestComputeQualityUnit:
    """UNIT-тесты для compute_quality."""

    def test_compute_quality_maximum_is_one(self):
        """
        Проверяем: compute_quality(1,1,1,1,0) возвращает Q = 1.0.

        Границы: все параметры = 1.0.
        Почему: максимальное качество = 1.0.
        """
        result = compute_quality(1.0, 1.0, 1.0, 1.0, 0.0)
        assert result == pytest.approx(1.0, abs=0.01), f"Q должен быть ~1.0, получено {result}"

    def test_compute_quality_minimum_is_zero(self):
        """
        Проверяем: compute_quality(0,0,0,0,0) возвращает Q = 0.0.

        Границы: все параметры = 0.0.
        Почему: минимальное качество = 0.0.
        """
        result = compute_quality(0.0, 0.0, 0.0, 0.0, 0.0)
        assert result == pytest.approx(0.0, abs=0.01), f"Q должен быть ~0, получено {result}"

    def test_compute_quality_clamped_above_one(self):
        """
        Проверяем: compute_quality(1,1,1,1,2) возвращает Q <= 1.0 (quality_bonus=2.0).

        Границы: quality_bonus=2.0 — выше нормы.
        Почему: Q не может превышать 1.0, должен быть clamped.
        """
        result = compute_quality(1.0, 1.0, 1.0, 1.0, 2.0)
        assert result <= 1.0, f"Q должен быть clamped до 1.0, получено {result}"

    def test_compute_quality_none_input_raises_error(self):
        """
        Проверяем: compute_quality(None, 1, 1, 1, 0) вызывает TypeError.

        Границы: completeness=None — невалидный вход.
        Почему: None вместо числа — ошибка вызывающего.
        """
        with pytest.raises(TypeError):
            compute_quality(None, 1.0, 1.0, 1.0, 0.0)


# ============================================================
# check_gamma_hard
# ============================================================

class TestCheckGammaHardUnit:
    """UNIT-тесты для check_gamma_hard."""

    def test_check_gamma_hard_no_violation_returns_zero(self):
        """
        Проверяем: check_gamma_hard([], [], 0) возвращает 0.0.

        Границы: пустые списки — нет правил, нет нарушений.
        Γ_hard = 0.0.
        Почему: отсутствие правил = отсутствие нарушений.
        """
        result = check_gamma_hard([], [], 0)
        assert result == 0.0, f"Γ_hard должен быть 0.0, получено {result}"

    def test_check_gamma_hard_violation_returns_negative_inf(self):
        """
        Проверяем: check_gamma_hard(['r1'], ['r1'], 0) возвращает -inf.

        Границы: одно правило, одно нарушение.
        Γ_hard = -inf (жёсткое нарушение).
        Почему: жёсткое правило нарушено = полный запрет.
        """
        result = check_gamma_hard(["rule1"], ["rule1"], 0)
        assert result == float('-inf'), f"Γ_hard должен быть -inf, получено {result}"

    def test_check_gamma_hard_none_input_raises_error(self):
        """
        Проверяем: check_gamma_hard(None, [], 0) вызывает TypeError.

        Границы: hard_rules=None — невалидный вход.
        Почему: None вместо списка — ошибка вызывающего.
        """
        with pytest.raises(TypeError):
            check_gamma_hard(None, [], 0)


# ============================================================
# check_gamma_soft
# ============================================================

class TestCheckGammaSoftUnit:
    """UNIT-тесты для check_gamma_soft."""

    def test_check_gamma_soft_half_violation_returns_half(self):
        """
        Проверяем: check_gamma_soft(['r1','r2'], ['r1']) возвращает 0.5.

        Границы: 2 правила, 1 нарушение.
        Γ_soft = 1/2 = 0.5.
        Почему: мягкое нарушение 50% = 50% штраф.
        """
        result = check_gamma_soft(["rule1", "rule2"], ["rule1"])
        assert result == pytest.approx(0.5, abs=0.01), f"Γ_soft должен быть 0.5, получено {result}"

    def test_check_gamma_soft_empty_returns_zero(self):
        """
        Проверяем: check_gamma_soft([], []) возвращает 0.0.

        Границы: пустые списки.
        Γ_soft = 0 / max(1, 0) = 0.0.
        Почему: отсутствие правил = отсутствие нарушений.
        """
        result = check_gamma_soft([], [])
        assert result == 0.0, f"Γ_soft должен быть 0.0, получено {result}"

    def test_check_gamma_soft_none_input_raises_error(self):
        """
        Проверяем: check_gamma_soft(None, []) вызывает TypeError.

        Границы: soft_rules=None — невалидный вход.
        Почему: None вместо списка — ошибка вызывающего.
        """
        with pytest.raises(TypeError):
            check_gamma_soft(None, [])


# ============================================================
# compute_h
# ============================================================

class TestComputeHUnit:
    """UNIT-тесты для compute_h (homeostasis)."""

    def test_compute_h_balanced_returns_midpoint(self):
        """
        Проверяем: compute_h(0.5, 0.5, 0.5, 0.5) возвращает h ≈ 0.5.

        Границы: все ratio = 0.5 (сбалансировано).
        stress = 0.3*0.5 + 0.3*0.5 + 0.2*0.5 + 0.2*0.5 = 0.5.
        h = 1 - 0.5 = 0.5.
        Почему: баланс = среднее значение.
        """
        result = compute_h(0.5, 0.5, 0.5, 0.5)
        assert result == pytest.approx(0.5, abs=0.01), f"h должен быть ~0.5, получено {result}"

    def test_compute_h_high_stress_returns_low(self):
        """
        Проверяем: compute_h(0, 0, 1, 0) возвращает h < 0.5 (высокий стресс).

        Границы: balance=0, rating=0, workload=1, quality=0.
        stress = 0.3*1 + 0.3*1 + 0.2*1 + 0.2*1 = 1.0.
        h = 1 - 1.0 = 0.0.
        Почему: максимальный стресс = минимальная homeostasis.
        """
        result = compute_h(0.0, 0.0, 1.0, 0.0)
        assert result == pytest.approx(0.0, abs=0.01), f"h должен быть ~0, получено {result}"

    def test_compute_h_low_stress_returns_high(self):
        """
        Проверяем: compute_h(1, 1, 0, 1) возвращает h > 0.5 (низкий стресс).

        Границы: balance=1, rating=1, workload=0, quality=1.
        stress = 0.3*0 + 0.3*0 + 0.2*0 + 0.2*0 = 0.0.
        h = 1 - 0.0 = 1.0.
        Почему: минимальный стресс = максимальная homeostasis.
        """
        result = compute_h(1.0, 1.0, 0.0, 1.0)
        assert result == pytest.approx(1.0, abs=0.01), f"h должен быть ~1, получено {result}"

    def test_compute_h_none_input_raises_error(self):
        """
        Проверяем: compute_h(None, 0.5, 0.5, 0.5) вызывает TypeError.

        Границы: balance_ratio=None — невалидный вход.
        Почему: None вместо числа — ошибка вызывающего.
        """
        with pytest.raises(TypeError):
            compute_h(None, 0.5, 0.5, 0.5)


# ============================================================
# compute_omega
# ============================================================

class TestComputeOmegaUnit:
    """UNIT-тесты для compute_omega (evolution score)."""

    def test_compute_omega_equal_weights_returns_average(self):
        """
        Проверяем: compute_omega(0.6, 0.8, (0.5, 0.5)) возвращает 0.7.

        Границы: skill=0.6, knowledge=0.8, w=(0.5, 0.5).
        Ω = 0.5*0.6 + 0.5*0.8 = 0.7.
        Почему: равные веса = среднее.
        """
        result = compute_omega(0.6, 0.8, (0.5, 0.5))
        assert result == pytest.approx(0.7, abs=0.01), f"Ω должен быть 0.7, получено {result}"

    def test_compute_omega_clamped_above_one(self):
        """
        Проверяем: compute_omega(1.0, 1.0) возвращает Ω <= 1.0.

        Границы: skill=1.0, knowledge=1.0 (максимум).
        Ω = 0.5*1.0 + 0.5*1.0 = 1.0.
        Почему: максимум = 1.0, clamped.
        """
        result = compute_omega(1.0, 1.0)
        assert result <= 1.0, f"Ω должен быть <= 1.0, получено {result}"

    def test_compute_omega_clamped_below_zero(self):
        """
        Проверяем: compute_omega(-0.5, -0.5) возвращает Ω >= 0.0.

        Границы: отрицательные входы.
        # ЭТО БАГ: документация не описывает отрицательные входы, но _clamp защищает.
        Почему: отрицательные входы — невалидны, но не должны ломать систему.
        """
        result = compute_omega(-0.5, -0.5)
        assert result >= 0.0, f"Ω должен быть >= 0 (clamp), получено {result}"

    def test_compute_omega_none_input_raises_error(self):
        """
        Проверяем: compute_omega(None, 0.5) вызывает TypeError.

        Границы: skill_level=None — невалидный вход.
        Почему: None вместо числа — ошибка вызывающего.
        """
        with pytest.raises(TypeError):
            compute_omega(None, 0.5)


# ============================================================
# compute_learning_rate
# ============================================================

class TestComputeLearningRateUnit:
    """UNIT-тесты для compute_learning_rate."""

    def test_compute_learning_rate_high_homeostasis_returns_full_eta(self):
        """
        Проверяем: compute_learning_rate(0.1, 1.0) возвращает η ≈ 0.1.

        Границы: eta_0=0.1, homeostasis=1.0 (максимум).
        multiplier = max(0.2, min(1.0, 1.0)) = 1.0.
        η = 0.1 * 1.0 = 0.1.
        Почему: высокая homeostasis = полная скорость обучения.
        """
        result = compute_learning_rate(0.1, 1.0)
        assert result == pytest.approx(0.1, abs=0.001), f"η должен быть ~0.1, получено {result}"

    def test_compute_learning_rate_low_homeostasis_returns_floor(self):
        """
        Проверяем: compute_learning_rate(0.1, 0.0) возвращает η ≈ 0.02.

        Границы: eta_0=0.1, homeostasis=0.0 (минимум).
        multiplier = max(0.2, min(1.0, 0.0)) = 0.2.
        η = 0.1 * 0.2 = 0.02.
        Почему: низкая homeostasis = минимальная скорость обучения (floor=0.2).
        """
        result = compute_learning_rate(0.1, 0.0)
        assert result == pytest.approx(0.02, abs=0.001), f"η должен быть ~0.02, получено {result}"

    def test_compute_learning_rate_none_input_raises_error(self):
        """
        Проверяем: compute_learning_rate(None, 0.5) вызывает TypeError.

        Границы: eta_0=None — невалидный вход.
        Почему: None вместо числа — ошибка вызывающего.
        """
        with pytest.raises(TypeError):
            compute_learning_rate(None, 0.5)


# ============================================================
# compute_upsilon_scalar
# ============================================================

class TestComputeUpsilonScalarUnit:
    """UNIT-тесты для compute_upsilon_scalar."""

    def test_compute_upsilon_scalar_equal_weights_returns_average(self):
        """
        Проверяем: compute_upsilon_scalar с равными весами возвращает среднее.

        Границы: ReputationVector(tech=0.8, econ=0.8, ...), weights равные.
        Почему: равные веса = среднее репутации.
        """
        rep = ReputationVector(tech=0.8, econ=0.8, comm=0.8, rel=0.8, sec=0.8, domain=0.8)
        weights = {'tech': 0.2, 'econ': 0.2, 'comm': 0.15, 'rel': 0.15, 'sec': 0.15, 'domain': 0.15}
        result = compute_upsilon_scalar(rep, weights)
        assert 0.0 <= result <= 1.0, f"Υ должен быть в [0,1], получено {result}"
        assert result > 0.5, f"Υ должен быть > 0.5 при high rep, получено {result}"

    def test_compute_upsilon_scalar_zero_reputation_returns_low(self):
        """
        Проверяем: compute_upsilon_scalar с нулевой репутацией возвращает Υ ≈ 0.

        Границы: ReputationVector(0,0,0,0,0,0).
        Почему: нулевая репутация = нулевой скаляр.
        """
        rep = ReputationVector(tech=0.0, econ=0.0, comm=0.0, rel=0.0, sec=0.0, domain=0.0)
        weights = {'tech': 0.2, 'econ': 0.2, 'comm': 0.15, 'rel': 0.15, 'sec': 0.15, 'domain': 0.15}
        result = compute_upsilon_scalar(rep, weights)
        assert result == pytest.approx(0.0, abs=0.01), f"Υ должен быть ~0, получено {result}"

    def test_compute_upsilon_scalar_none_reputation_raises_error(self):
        """
        Проверяем: compute_upsilon_scalar(None, {}) вызывает TypeError.

        Границы: rep=None — невалидный вход.
        Почему: None вместо ReputationVector — ошибка вызывающего.
        """
        with pytest.raises(TypeError):
            compute_upsilon_scalar(None, {})


# ============================================================
# update_upsilon
# ============================================================

class TestUpdateUpsilonUnit:
    """UNIT-тесты для update_upsilon."""

    def test_update_upsilon_rating_only_returns_scalar(self):
        """
        Проверяем: update_upsilon(rating=0.8, n_reviews=10) возвращает float.

        Границы: rating=0.8, n_reviews=10.
        Почему: legacy-режим — скалярная репутация.
        """
        result = update_upsilon(rating=0.8, n_reviews=10)
        assert isinstance(result, float), f"Должен быть float, получено {type(result)}"
        assert 0.0 <= result <= 1.0, f"Репутация должна быть в [0,1], получено {result}"

    def test_update_upsilon_zero_reviews_returns_low(self):
        """
        Проверяем: update_upsilon(rating=0.8, n_reviews=0) возвращает низкое значение.

        Границы: n_reviews=0 — нет отзывов.
        Почему: нет отзывов = нет доверия = низкая репутация.
        """
        result = update_upsilon(rating=0.8, n_reviews=0)
        assert result < 0.5, f"При 0 отзывов репутация должна быть низкой, получено {result}"

    def test_update_upsilon_none_rating_raises_error(self):
        """
        Проверяем: update_upsilon(rating=None, n_reviews=10) вызывает TypeError.

        Границы: rating=None — невалидный вход.
        Почему: None вместо числа — ошибка вызывающего.
        """
        with pytest.raises(TypeError):
            update_upsilon(rating=None, n_reviews=10)


# ============================================================
# update_phi_historical
# ============================================================

class TestUpdatePhiHistoricalUnit:
    """UNIT-тесты для update_phi_historical."""

    def test_update_phi_historical_kalman_zero_returns_prev(self):
        """
        Проверяем: update_phi_historical(100, 50, 0) возвращает prev=100.

        Границы: kalman_gain=0 — не доверяем наблюдению.
        Φ_new = 100 + 0*(50-100) = 100.
        Почему: нулевой gain = полное доверие истории.
        """
        result = update_phi_historical(100.0, 50.0, 0.0)
        assert result == pytest.approx(100.0, abs=0.01), f"Φ должен быть 100, получено {result}"

    def test_update_phi_historical_kalman_one_returns_observed(self):
        """
        Проверяем: update_phi_historical(100, 50, 1) возвращает observed=50.

        Границы: kalman_gain=1 — полное доверие наблюдению.
        Φ_new = 100 + 1*(50-100) = 50.
        Почему: максимальный gain = полное доверие новым данным.
        """
        result = update_phi_historical(100.0, 50.0, 1.0)
        assert result == pytest.approx(50.0, abs=0.01), f"Φ должен быть 50, получено {result}"

    def test_update_phi_historical_kalman_clamped_above_one(self):
        """
        Проверяем: update_phi_historical(100, 50, 2) возвращает Φ ≈ 50 (gain clamped).

        Границы: kalman_gain=2 — выше максимума.
        # ЭТО БАГ: gain должен быть в [0,1], но _clamp защищает.
        Почему: gain > 1 — невалиден, но не должен ломать систему.
        """
        result = update_phi_historical(100.0, 50.0, 2.0)
        assert result == pytest.approx(50.0, abs=0.01), f"Φ должен быть ~50 (clamped), получено {result}"

    def test_update_phi_historical_none_input_raises_error(self):
        """
        Проверяем: update_phi_historical(None, 50, 0.5) вызывает TypeError.

        Границы: prev=None — невалидный вход.
        Почему: None вместо числа — ошибка вызывающего.
        """
        with pytest.raises(TypeError):
            update_phi_historical(None, 50.0, 0.5)


# ============================================================
# evaluate_decision_rule
# ============================================================

class TestEvaluateDecisionRuleUnit:
    """UNIT-тесты для evaluate_decision_rule."""

    def test_evaluate_decision_hard_veto_returns_reject(self):
        """
        Проверяем: evaluate_decision_rule с gamma_hard=-inf возвращает 'REJECT'.

        Границы: gamma_hard=-inf (жёсткое нарушение).
        Почему: жёсткое нарушение = немедленный отказ.
        """
        result = evaluate_decision_rule(
            gamma_hard=float('-inf'), psi=0.1, psi_max=1.0,
            C_t=100.0, C_min=10.0, H_TZ=0.5, H_TZ_max=1.0,
            VoI=0.5, C_info=1.0, H_val=0.5, H_clarify=0.3,
            U_val=1.0, Q_predicted=0.8, q_min=0.5
        )
        assert result == 'REJECT', f"Должен быть REJECT, получено {result}"

    def test_evaluate_decision_high_psi_returns_decline(self):
        """
        Проверяем: evaluate_decision_rule с psi > psi_max возвращает 'DECLINE'.

        Границы: psi=2.0, psi_max=1.0 (риск превышен).
        Почему: превышение риска = отклонение.
        """
        result = evaluate_decision_rule(
            gamma_hard=0.0, psi=2.0, psi_max=1.0,
            C_t=100.0, C_min=10.0, H_TZ=0.5, H_TZ_max=1.0,
            VoI=0.5, C_info=1.0, H_val=0.5, H_clarify=0.3,
            U_val=1.0, Q_predicted=0.8, q_min=0.5
        )
        assert result == 'DECLINE', f"Должен быть DECLINE, получено {result}"

    def test_evaluate_decision_high_homeostasis_returns_clarify(self):
        """
        Проверяем: evaluate_decision_rule с H_TZ > H_TZ_max возвращает 'CLARIFY'.

        Границы: H_TZ=2.0, H_TZ_max=1.0 (стресс превышен).
        Почему: высокий стресс = нужна дополнительная информация.
        """
        result = evaluate_decision_rule(
            gamma_hard=0.0, psi=0.1, psi_max=1.0,
            C_t=100.0, C_min=10.0, H_TZ=2.0, H_TZ_max=1.0,
            VoI=0.5, C_info=1.0, H_val=0.5, H_clarify=0.3,
            U_val=1.0, Q_predicted=0.8, q_min=0.5
        )
        assert result == 'CLARIFY', f"Должен быть CLARIFY, получено {result}"

    def test_evaluate_decision_positive_utility_returns_execute(self):
        """
        Проверяем: evaluate_decision_rule с U_val > 0 и Q >= q_min возвращает 'EXECUTE'.

        Границы: U_val=1.0, Q_predicted=0.8, q_min=0.5.
        Почему: положительная полезность и достаточное качество = выполнение.
        """
        result = evaluate_decision_rule(
            gamma_hard=0.0, psi=0.1, psi_max=1.0,
            C_t=100.0, C_min=10.0, H_TZ=0.5, H_TZ_max=1.0,
            VoI=0.5, C_info=1.0, H_val=0.5, H_clarify=0.3,
            U_val=1.0, Q_predicted=0.8, q_min=0.5
        )
        assert result == 'EXECUTE', f"Должен быть EXECUTE, получено {result}"

    def test_evaluate_decision_none_input_raises_error(self):
        """
        Проверяем: evaluate_decision_rule с gamma_hard=None вызывает TypeError.

        Границы: gamma_hard=None — невалидный вход.
        Почему: None вместо числа — ошибка вызывающего.
        """
        with pytest.raises(TypeError):
            evaluate_decision_rule(
                gamma_hard=None, psi=0.1, psi_max=1.0,
                C_t=100.0, C_min=10.0, H_TZ=0.5, H_TZ_max=1.0,
                VoI=0.5, C_info=1.0, H_val=0.5, H_clarify=0.3,
                U_val=1.0, Q_predicted=0.8, q_min=0.5
            )
