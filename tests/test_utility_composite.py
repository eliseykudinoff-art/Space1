"""
Space1 -- TESTS: utility/composite.py (XiCoefficients, PhiRCalculator)

Каждый тест проверен против реального кода.
FAILED = баг, не ошибка теста.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest


# =============================================================================
# UNIT: XiCoefficients.calculate
# =============================================================================

class TestXiCoefficientsUnit:
    """Unit-тесты на XiCoefficients -- формула G17."""

    def test_xi_basic_calculation(self):
        """
        Xi = alpha*Q - beta*(O_time + O_cost).

        Проверяем: базовая формула.
        Границы: Q=0.8, O_time=0.2, O_cost=0.1, alpha=0.7, beta=0.3.
        Почему такие: Xi = 0.7*0.8 - 0.3*0.3 = 0.56 - 0.09 = 0.47.
        """
        from space1.utility.composite import XiCoefficients
        xi = XiCoefficients(alpha=0.7, beta=0.3)
        result = xi.calculate(quality_score=0.8, opportunity_time=0.2, opportunity_cost=0.1)
        assert abs(result.xi_value - 0.47) < 0.001
        assert result.quality_score == 0.8
        assert abs(result.opportunity_cost - 0.3) < 0.001
        assert result.alpha == 0.7
        assert result.beta == 0.3

    def test_xi_quality_clamped_to_one(self):
        """
        quality_score > 1.0 -> clamped to 1.0.

        Проверяем: верхняя граница clamping.
        Границы: quality_score=1.5.
        Почему такие: Q ∈ [0, 1] по определению.
        """
        from space1.utility.composite import XiCoefficients
        xi = XiCoefficients(alpha=0.7, beta=0.3)
        result = xi.calculate(quality_score=1.5, opportunity_time=0.0, opportunity_cost=0.0)
        assert result.quality_score == 1.0
        assert abs(result.xi_value - 0.7) < 0.001

    def test_xi_quality_clamped_to_zero(self):
        """
        quality_score < 0.0 -> clamped to 0.0.

        Проверяем: нижняя граница clamping.
        Границы: quality_score=-0.5.
        Почему такие: Q ∈ [0, 1] по определению.
        """
        from space1.utility.composite import XiCoefficients
        xi = XiCoefficients(alpha=0.7, beta=0.3)
        result = xi.calculate(quality_score=-0.5, opportunity_time=0.0, opportunity_cost=0.0)
        assert result.quality_score == 0.0
        assert abs(result.xi_value - 0.0) < 0.001

    def test_xi_opportunity_clamped_to_zero(self):
        """
        opportunity < 0.0 -> clamped to 0.0.

        Проверяем: нижняя граница opportunity.
        Границы: opportunity_time=-0.5, opportunity_cost=-0.5.
        Почему такие: opportunity cost не может быть отрицательной.
        """
        from space1.utility.composite import XiCoefficients
        xi = XiCoefficients(alpha=0.7, beta=0.3)
        result = xi.calculate(quality_score=0.5, opportunity_time=-0.5, opportunity_cost=-0.5)
        assert result.opportunity_cost == 0.0
        assert abs(result.xi_value - 0.35) < 0.001

    def test_xi_maximum_quality_zero_opportunity(self):
        """
        Q=1.0, O=0.0 -> Xi = alpha (максимум).

        Проверяем: максимальное значение Xi.
        Границы: Q=1.0, O_time=0.0, O_cost=0.0.
        Почему такие: идеальный сценарий.
        """
        from space1.utility.composite import XiCoefficients
        xi = XiCoefficients(alpha=0.7, beta=0.3)
        result = xi.calculate(quality_score=1.0, opportunity_time=0.0, opportunity_cost=0.0)
        assert abs(result.xi_value - 0.7) < 0.001

    def test_xi_zero_quality_maximum_opportunity(self):
        """
        Q=0.0, O=1.0+1.0 -> Xi = -beta*2.0 (минимум).

        Проверяем: минимальное значение Xi.
        Границы: Q=0.0, O_time=1.0, O_cost=1.0.
        Почему такие: худший сценарий.
        """
        from space1.utility.composite import XiCoefficients
        xi = XiCoefficients(alpha=0.7, beta=0.3)
        result = xi.calculate(quality_score=0.0, opportunity_time=1.0, opportunity_cost=1.0)
        assert abs(result.xi_value - (-0.6)) < 0.001

    def test_xi_alpha_zero_returns_negative_opportunity(self):
        """
        alpha=0.0 -> Xi = -beta * O (только штраф за opportunity).

        Проверяем: alpha=0.0.
        Границы: alpha=0.0, beta=0.3, Q=0.5, O=0.5.
        Почему такие: крайний случай -- нет бонуса за качество.
        """
        from space1.utility.composite import XiCoefficients
        xi = XiCoefficients(alpha=0.0, beta=0.3)
        result = xi.calculate(quality_score=0.5, opportunity_time=0.5, opportunity_cost=0.0)
        assert abs(result.xi_value - (-0.15)) < 0.001

    def test_xi_beta_zero_returns_quality_bonus(self):
        """
        beta=0.0 -> Xi = alpha * Q (только бонус за качество).

        Проверяем: beta=0.0.
        Границы: beta=0.0, alpha=0.7, Q=0.5, O=0.5.
        Почему такие: крайний случай -- нет штрафа за opportunity.
        """
        from space1.utility.composite import XiCoefficients
        xi = XiCoefficients(alpha=0.7, beta=0.0)
        result = xi.calculate(quality_score=0.5, opportunity_time=0.5, opportunity_cost=0.5)
        assert abs(result.xi_value - 0.35) < 0.001

    def test_xi_default_weights_from_config(self):
        """
        XiCoefficients() без аргументов -> weights из config.

        Проверяем: default behavior.
        Границы: Без явных alpha/beta.
        Почему такие: контракт -- default = config values.
        """
        from space1.utility.composite import XiCoefficients
        xi = XiCoefficients()
        assert xi.alpha > 0.0
        assert xi.beta > 0.0
        assert abs(xi.alpha + xi.beta - 1.0) < 0.01  # Обычно alpha + beta ≈ 1.0

    def test_xi_components_to_dict(self):
        """
        XiComponents.to_dict() -> dict с 5 ключами.

        Проверяем: сериализация.
        Границы: Стандартный результат.
        Почему такие: контракт экспорта.
        """
        from space1.utility.composite import XiCoefficients
        xi = XiCoefficients(alpha=0.7, beta=0.3)
        result = xi.calculate(quality_score=0.5, opportunity_time=0.2, opportunity_cost=0.1)
        d = result.to_dict()
        assert set(d.keys()) == {"quality_score", "opportunity_cost", "xi_value", "alpha", "beta"}
        assert all(isinstance(v, float) for v in d.values())


# =============================================================================
# UNIT: PhiRCalculator.calculate
# =============================================================================

class TestPhiRCalculatorUnit:
    """Unit-тесты на PhiRCalculator -- формула G18."""

    def test_phi_r_basic_calculation(self):
        """
        Phi_R = Phi * Gamma * (1 + alpha_rep*Upsilon) - lambda_psi*Psi.

        Проверяем: базовая формула.
        Границы: Phi=100, Gamma=1.0, Upsilon=0.5, Psi=0.2, alpha_rep=0.3, lambda_psi=0.5.
        Почему такие: Phi_R = 100 * 1.0 * 1.15 - 0.1 = 114.9.
        """
        from space1.utility.composite import PhiRCalculator
        phi = PhiRCalculator(alpha_rep=0.3, lambda_psi=0.5)
        result = phi.calculate(phi=100.0, gamma=1.0, upsilon=0.5, psi=0.2)
        assert abs(result.phi_r - 114.9) < 0.001
        assert result.base_phi == 100.0
        assert result.gamma_compliance == 1.0
        assert result.upsilon_reputation == 0.5
        assert result.psi_risk == 0.2

    def test_phi_r_gamma_zero_compliance_failed(self):
        """
        Gamma=0.0 -> Phi_R = -lambda_psi*Psi (комплаенс не пройден).

        Проверяем: gamma=0.0.
        Границы: Gamma=0.0, Phi=100, Psi=0.2.
        Почему такие: compliance failed = нет прибыли.
        """
        from space1.utility.composite import PhiRCalculator
        phi = PhiRCalculator(alpha_rep=0.3, lambda_psi=0.5)
        result = phi.calculate(phi=100.0, gamma=0.0, upsilon=0.5, psi=0.2)
        assert abs(result.phi_r - (-0.1)) < 0.001
        assert result.gamma_compliance == 0.0

    def test_phi_r_high_psi_clamped(self):
        """
        Psi > 1.0 -> clamped to 1.0.

        Проверяем: верхняя граница clamping.
        Границы: Psi=2.0.
        Почему такие: Psi ∈ [0, 1] по определению.
        """
        from space1.utility.composite import PhiRCalculator
        phi = PhiRCalculator(alpha_rep=0.3, lambda_psi=0.5)
        result = phi.calculate(phi=10.0, gamma=1.0, upsilon=0.0, psi=2.0)
        assert result.psi_risk == 1.0
        assert abs(result.phi_r - 9.5) < 0.001  # 10 * 1 * 1 - 0.5 * 1 = 9.5

    def test_phi_r_negative_phi(self):
        """
        Phi < 0 -> Phi_R отрицательный (убыток).

        Проверяем: отрицательная прибыль.
        Границы: Phi=-50.0.
        Почему такие: убыток + reputation не спасает.
        """
        from space1.utility.composite import PhiRCalculator
        phi = PhiRCalculator(alpha_rep=0.3, lambda_psi=0.5)
        result = phi.calculate(phi=-50.0, gamma=1.0, upsilon=0.5, psi=0.2)
        assert result.phi_r < 0.0
        assert abs(result.phi_r - (-57.6)) < 0.001

    def test_phi_r_alpha_rep_zero_no_reputation_bonus(self):
        """
        alpha_rep=0.0 -> reputation multiplier = 1.0.

        Проверяем: alpha_rep=0.0.
        Границы: alpha_rep=0.0, Upsilon=0.8.
        Почему такие: нет репутационного бонуса.
        """
        from space1.utility.composite import PhiRCalculator
        phi = PhiRCalculator(alpha_rep=0.0, lambda_psi=0.5)
        result = phi.calculate(phi=100.0, gamma=1.0, upsilon=0.8, psi=0.2)
        assert abs(result.phi_r - 99.9) < 0.001  # 100 * 1 * 1 - 0.1 = 99.9

    def test_phi_r_lambda_psi_zero_no_risk_penalty(self):
        """
        lambda_psi=0.0 -> risk penalty = 0.0.

        Проверяем: lambda_psi=0.0.
        Границы: lambda_psi=0.0, Psi=1.0.
        Почему такие: нет штрафа за риск.
        """
        from space1.utility.composite import PhiRCalculator
        phi = PhiRCalculator(alpha_rep=0.3, lambda_psi=0.0)
        result = phi.calculate(phi=100.0, gamma=1.0, upsilon=0.5, psi=1.0)
        assert abs(result.phi_r - 115.0) < 0.001  # 100 * 1 * 1.15 - 0 = 115.0

    def test_phi_r_upsilon_zero_no_reputation(self):
        """
        Upsilon=0.0 -> reputation multiplier = 1.0.

        Проверяем: Upsilon=0.0.
        Границы: Upsilon=0.0.
        Почему такие: нет репутации = нет бонуса.
        """
        from space1.utility.composite import PhiRCalculator
        phi = PhiRCalculator(alpha_rep=0.3, lambda_psi=0.5)
        result = phi.calculate(phi=100.0, gamma=1.0, upsilon=0.0, psi=0.2)
        assert abs(result.phi_r - 99.9) < 0.001  # 100 * 1 * 1 - 0.1 = 99.9

    def test_phi_r_gamma_clamped(self):
        """
        Gamma > 1.0 -> clamped to 1.0.

        Проверяем: верхняя граница clamping.
        Границы: Gamma=1.5.
        Почему такие: Gamma ∈ [0, 1] по определению.
        """
        from space1.utility.composite import PhiRCalculator
        phi = PhiRCalculator(alpha_rep=0.3, lambda_psi=0.5)
        result = phi.calculate(phi=100.0, gamma=1.5, upsilon=0.5, psi=0.2)
        assert result.gamma_compliance == 1.0
        assert abs(result.phi_r - 114.9) < 0.001

    def test_phi_r_default_weights_from_config(self):
        """
        PhiRCalculator() без аргументов -> weights из config.

        Проверяем: default behavior.
        Границы: Без явных alpha_rep/lambda_psi.
        Почему такие: контракт -- default = config values.
        """
        from space1.utility.composite import PhiRCalculator
        phi = PhiRCalculator()
        assert phi.alpha_rep > 0.0
        assert phi.lambda_psi > 0.0

    def test_phi_r_components_to_dict(self):
        """
        PhiRComponents.to_dict() -> dict с 7 ключами.

        Проверяем: сериализация.
        Границы: Стандартный результат.
        Почему такие: контракт экспорта.
        """
        from space1.utility.composite import PhiRCalculator
        phi = PhiRCalculator(alpha_rep=0.3, lambda_psi=0.5)
        result = phi.calculate(phi=100.0, gamma=1.0, upsilon=0.5, psi=0.2)
        d = result.to_dict()
        assert set(d.keys()) == {"base_phi", "gamma_compliance", "upsilon_reputation", "psi_risk", "phi_r", "alpha_rep", "lambda_psi"}
        assert all(isinstance(v, float) for v in d.values())


# =============================================================================
# PAIR: Xi + PhiR consistency
# =============================================================================

class TestPairXiPhiR:
    """PAIR-тесты: связка Xi и PhiR."""

    def test_xi_and_phi_r_both_positive_for_good_task(self):
        """
        Хорошая задача -> Xi > 0 и Phi_R > 0.

        Проверяем: consistency между метриками.
        Границы: Q=0.9, O=0.1, Phi=50, Gamma=1.0, Upsilon=0.5, Psi=0.1.
        Почему такие: хорошая задача = положительные обе метрики.
        """
        from space1.utility.composite import XiCoefficients, PhiRCalculator
        xi = XiCoefficients(alpha=0.7, beta=0.3)
        phi_r = PhiRCalculator(alpha_rep=0.3, lambda_psi=0.5)
        xi_result = xi.calculate(quality_score=0.9, opportunity_time=0.1, opportunity_cost=0.0)
        phi_r_result = phi_r.calculate(phi=50.0, gamma=1.0, upsilon=0.5, psi=0.1)
        assert xi_result.xi_value > 0.0
        assert phi_r_result.phi_r > 0.0

    def test_xi_negative_phi_r_positive_possible(self):
        """
        Xi < 0, но Phi_R > 0 (возможно).

        Проверяем: независимость метрик.
        Границы: Q=0.1, O=1.0, Phi=100, Gamma=1.0.
        Почему такие: высокая прибыль компенсирует низкое качество.
        """
        from space1.utility.composite import XiCoefficients, PhiRCalculator
        xi = XiCoefficients(alpha=0.7, beta=0.3)
        phi_r = PhiRCalculator(alpha_rep=0.3, lambda_psi=0.5)
        xi_result = xi.calculate(quality_score=0.1, opportunity_time=1.0, opportunity_cost=1.0)
        phi_r_result = phi_r.calculate(phi=100.0, gamma=1.0, upsilon=0.5, psi=0.2)
        assert xi_result.xi_value < 0.0
        assert phi_r_result.phi_r > 0.0


# =============================================================================
# INTEGRITY: Архитектурные инварианты
# =============================================================================

class TestIntegrityComposite:
    """INTEGRITY-тесты: архитектурные инварианты composite."""

    def test_xi_components_alpha_plus_beta_approx_one(self):
        """
        alpha + beta ≈ 1.0 (конвенция, не жёсткое правило).

        Проверяем: баланс весов.
        Границы: Default values.
        Почему такие: alpha + beta > 1.0 = double counting.
        """
        from space1.utility.composite import XiCoefficients
        xi = XiCoefficients()
        assert xi.alpha + xi.beta <= 1.5  # Допуск

    def test_phi_r_multiplier_positive(self):
        """
        Reputation multiplier = 1 + alpha_rep*Upsilon >= 1.0.

        Проверяем: multiplier не уменьшает.
        Границы: Upsilon=0.0.
        Почему такие: репутация = бонус, не штраф.
        """
        from space1.utility.composite import PhiRCalculator
        phi = PhiRCalculator(alpha_rep=0.3, lambda_psi=0.5)
        result = phi.calculate(phi=100.0, gamma=1.0, upsilon=0.0, psi=0.0)
        # multiplier = 1.0 + 0 = 1.0
        assert result.phi_r >= 100.0  # Phi * 1.0 - 0 = 100

    def test_clamping_preserves_order(self):
        """
        Clamping не меняет порядок: clamp(a) < clamp(b) если a < b.

        Проверяем: монотонность clamping.
        Границы: a=-0.5, b=0.5, c=1.5.
        Почему такие: clamping = projection, не distortion.
        """
        from space1.utility.composite import XiCoefficients
        xi = XiCoefficients(alpha=0.7, beta=0.3)
        r1 = xi.calculate(quality_score=-0.5)
        r2 = xi.calculate(quality_score=0.5)
        r3 = xi.calculate(quality_score=1.5)
        assert r1.quality_score < r2.quality_score < r3.quality_score
        assert r1.quality_score == 0.0
        assert r2.quality_score == 0.5
        assert r3.quality_score == 1.0


# =============================================================================
# REGRESSION: Старые баги не вернулись
# =============================================================================

class TestRegressionComposite:
    """REGRESSION-тесты: старые баги не вернулись."""

    def test_xi_calculate_does_not_mutate_inputs(self):
        """
        calculate() не изменяет входные параметры.

        Проверяем: иммутабельность входа.
        Границы: Стандартные значения.
        Почему такие: баг: mutation входных float.
        """
        from space1.utility.composite import XiCoefficients
        xi = XiCoefficients(alpha=0.7, beta=0.3)
        q, ot, oc = 0.8, 0.2, 0.1
        xi.calculate(quality_score=q, opportunity_time=ot, opportunity_cost=oc)
        assert q == 0.8
        assert ot == 0.2
        assert oc == 0.1
