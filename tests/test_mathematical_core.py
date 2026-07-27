"""
Unit and integration tests for canonical mathematical core formulas (02_MATHEMATICAL_CORE.md)
"""

import pytest
import math
from space1.utility import (
    compute_phi,
    compute_psi,
    compute_quality,
    evaluate_decision_rule,
    calculate_evolution_score,
    calculate_portfolio_diversity,
    MultidimensionalReputation,
)
from space1.compliance.core import Action, Rule, GammaVeto, MaxCostRule
from space1.utility.control import HomeostaticRegulator


class DummySoftRule(Rule):
    """A soft rule with weight."""
    is_hard = False
    weight = 0.5
    
    @property
    def name(self) -> str:
        return "dummy_soft"
        
    def check(self, action: Action) -> bool:
        return action.resource_cost <= 5.0


class TestCanonicalMathematicalCore:
    """Test suite for verified canonical formulas."""

    def test_canonical_stress_and_unbounded_homeostasis(self):
        """Test H calculation with and without unachievable LOW stress (H > 1.2) bounds."""
        regulator = HomeostaticRegulator()
        
        # 1. Normal state metrics
        metrics_normal = {
            "balance": 20.0,
            "rating": 4.5,
            "quality": 0.8,
            "active_tasks": 1.0,
            "budget_target": 100.0,
            "rating_target": 4.5,
            "quality_target": 0.8,
            "max_capacity": 5.0,
        }
        H, stress = regulator.calculate_homeostasis(metrics_normal)
        # stress = 0.3*(1 - 0.2) + 0.3*(1 - 1.0) + 0.2*(0.2) + 0.2*(1 - 1.0) = 0.24 + 0 + 0.04 + 0 = 0.28
        # H = 1 - 0.28 = 0.72
        assert abs(stress - 0.28) < 0.01
        assert abs(H - 0.72) < 0.01
        
        # 2. LOW stress (H > 1.2) achievable with rating/quality ratio exceeding target (no upper cap!)
        metrics_outstanding = {
            "balance": 100.0,  # balance_ratio = 1.0
            "rating": 5.4,      # rating_ratio = 1.2
            "quality": 0.96,    # quality_ratio = 1.2
            "active_tasks": 0.0,  # workload_ratio = 0.0
            "budget_target": 100.0,
            "rating_target": 4.5,
            "quality_target": 0.8,
            "max_capacity": 5.0,
        }
        H_low, stress_low = regulator.calculate_homeostasis(metrics_outstanding)
        # stress = 0.3*(1 - 1.0) + 0.3*(1 - 1.2) + 0.2*(0.0) + 0.2*(1 - 1.2)
        #        = 0.0 - 0.06 + 0.0 - 0.04 = -0.10
        # H = 1 - (-0.10) = 1.10
        # Since rating can grow unbounded (e.g. rating=6.0 on 4.5 target), H can easily exceed 1.2!
        metrics_exceptional = dict(metrics_outstanding, rating=6.0, quality=1.2)
        H_exceptional, _ = regulator.calculate_homeostasis(metrics_exceptional)
        assert H_exceptional >= 1.2  # LOW stress H > 1.2 is now fully achievable!

    def test_quality_modulated_profit_with_b_Q_modifier(self):
        """Test compute_phi using quality-modulated revenue and safe duration bounds."""
        # 1. Base run
        phi_base = compute_phi(revenue=100.0, cost=10.0, time_hours=2.0)
        assert phi_base == 45.0
        
        # 2. Quality exceeds expected (Q_score = 0.9 vs Q_expected = 0.7, kappa_bonus = 0.1)
        # b_Q = 0.1 * (0.9 - 0.7) = 0.02. Modulated revenue = 100 * 1.02 = 102.0
        # (102.0 - 10.0) / 2.0 = 46.0
        phi_bonus = compute_phi(revenue=100.0, cost=10.0, time_hours=2.0, Q_score=0.9, Q_expected=0.7, kappa_bonus=0.1)
        assert phi_bonus == 46.0
        
        # 3. Quality below expected (Q_score = 0.5 vs Q_expected = 0.7, kappa_penalty = 0.2)
        # b_Q = -0.2 * (0.7 - 0.5) = -0.04. Modulated revenue = 100 * 0.96 = 96.0
        # (96.0 - 10.0) / 2.0 = 43.0
        phi_penalty = compute_phi(revenue=100.0, cost=10.0, time_hours=2.0, Q_score=0.5, Q_expected=0.7, kappa_penalty=0.2)
        assert phi_penalty == 43.0

    def test_canonical_failure_probability_based_risk_psi(self):
        """Test compute_psi using canonical P_fail * Costs."""
        class DummyTask:
            metadata = {"uncertainty": 0.8, "novelty": 0.6}
            urgency_score = 0.7
            
        class DummyAgent:
            class DummyMetrics:
                n_active_tasks = 4.0
            metrics = DummyMetrics()
            class DummyCapabilities:
                llm_quality = 0.8
            capabilities = DummyCapabilities()

        # psi = P_fail * (C_direct + C_reputation)
        # P_fail = P_base * (1 + alpha_u*U + alpha_f*F + alpha_n*N + alpha_d*D) * (1 / (1 + alpha_s*skill))
        psi_val = compute_psi(
            task=DummyTask(),
            agent_context=DummyAgent(),
            canonical=True,
            P_base=0.1,
            C_direct=20.0,
            C_reputation=10.0,
            alpha_u=0.5,
            alpha_f=0.5,
            alpha_n=0.5,
            alpha_d=0.5,
            alpha_s=0.5,
        )
        # U = 0.8, F = 0.4, N = 0.6, D = 0.7, skill = 0.2
        # P_fail = 0.1 * (1 + 0.4 + 0.2 + 0.3 + 0.35) * (1 / (1 + 0.1)) = 0.1 * 2.25 * 0.909 = 0.2045
        # psi_val = 0.2045 * 30.0 = 6.136
        assert 5.0 <= psi_val <= 7.0

    def test_bounded_Q_time_completeness(self):
        """Test compute_quality bounded time computation."""
        # Task delivered with delay: t_actual = 5.0, t_deadline = 4.0
        # timeliness = 1 - min(1, max(0, t_actual - t_deadline)/t_deadline) = 1 - min(1, 1.0/4.0) = 0.75
        Q_delayed = compute_quality(
            completeness=1.0, accuracy=1.0, fullness=1.0,
            t_actual=5.0, t_deadline=4.0
        )
        assert Q_delayed < 1.0
        
        # Task delivered extremely late: t_actual = 20.0, t_deadline = 4.0
        # timeliness = 1 - min(1, 16.0/4.0) = 0.0
        Q_very_late = compute_quality(
            completeness=1.0, accuracy=1.0, fullness=1.0,
            t_actual=20.0, t_deadline=4.0
        )
        # weighted: 0.25 * (1 + 1 + 1 + 0.0) = 0.75
        assert Q_very_late == 0.75

    def test_multidimensional_reputation_decays(self):
        """Test MultidimensionalReputation scalar projection and incident updating."""
        rep = MultidimensionalReputation(tech=0.9, econ=0.8, comm=0.7, rel=0.6, sec=0.5, domain=0.4)
        
        # Scalar projection
        val = rep.scalar_reputation()
        expected = 0.2*0.9 + 0.2*0.8 + 0.15*0.7 + 0.15*0.6 + 0.15*0.5 + 0.15*0.4
        # expected = 0.18 + 0.16 + 0.105 + 0.09 + 0.075 + 0.06 = 0.67
        assert abs(val - 0.67) < 0.01
        
        # Update with positive quality
        rep.update_with_incident("tech", quality=1.0, incident=False, eta=0.1)
        assert rep.tech == 1.0  # capped at 1.0
        
        # Update with incident (heavy decay penalty)
        rep.update_with_incident("sec", quality=0.0, incident=True, eta=0.1, gamma=0.3)
        # sec = 0.5 - 0.3*0.5 = 0.35
        assert abs(rep.sec - 0.35) < 0.01

    def test_evolution_dynamic_learning_rate(self):
        """Test evolution Omega score and dynamic learning rate eta(H)."""
        # Under normal conditions (H=1.0)
        res_normal = calculate_evolution_score(t=4.0, H_val=1.0, eta_0=0.1)
        assert abs(res_normal["eta"] - 0.1) < 1e-9
        
        # Under high stress (H=0.1) -> learning rate eta is capped to 0.2 * eta_0 = 0.02
        res_stress = calculate_evolution_score(t=4.0, H_val=0.1, eta_0=0.1)
        assert abs(res_stress["eta"] - 0.02) < 1e-9
        assert res_stress["omega"] < res_normal["omega"]

    def test_portfolio_diversity_entropy(self):
        """Test calculate_portfolio_diversity Shannon entropy calculations."""
        # 1. Zero/Empty distribution
        assert calculate_portfolio_diversity([]) == 0.0
        
        # 2. Flat distribution: two types, equal count
        entropy = calculate_portfolio_diversity([10.0, 10.0])
        # H = -(0.5*log2(0.5) + 0.5*log2(0.5)) = 1.0
        assert entropy == 1.0

    def test_compliance_veto_hard_vs_soft(self):
        """Test GammaVeto gamma_hard and gamma_soft separation."""
        veto = GammaVeto()
        veto.register(MaxCostRule(max_cost=10.0))  # hard by default
        
        soft_rule = DummySoftRule()
        veto.register(soft_rule)
        
        # Cost exceeds both hard (10) and soft (5) rules
        action = Action(name="sudo", resource_cost=15.0)
        
        # hard veto triggers negative infinity
        assert veto.gamma_hard(action) == float('-inf')
        # soft rule violation returns weighted penalty
        assert veto.gamma_soft(action) == 0.5

    def test_canonical_decision_rule_cascade(self):
        """Test evaluate_decision_rule across all levels of the decision cascade."""
        # Level 1: Reject on Hard Veto
        assert evaluate_decision_rule(
            gamma_hard=float('-inf'), psi=1.0, psi_max=5.0, C_t=0.9, C_min=0.1,
            H_TZ=0.2, H_TZ_max=1.0, VoI=1.0, C_info=5.0, H_val=1.0, H_clarify=0.5,
            U_val=10.0, Q_predicted=0.8, q_min=0.5
        ) == "REJECT"

        # Level 2: Decline on high Risk or Low Compute Window (not a violation, just unfavorable)
        assert evaluate_decision_rule(
            gamma_hard=0.0, psi=10.0, psi_max=5.0, C_t=0.9, C_min=0.1,
            H_TZ=0.2, H_TZ_max=1.0, VoI=1.0, C_info=5.0, H_val=1.0, H_clarify=0.5,
            U_val=10.0, Q_predicted=0.8, q_min=0.5
        ) == "DECLINE"
        
        assert evaluate_decision_rule(
            gamma_hard=0.0, psi=1.0, psi_max=5.0, C_t=0.05, C_min=0.1,  # C_t < C_min
            H_TZ=0.2, H_TZ_max=1.0, VoI=1.0, C_info=5.0, H_val=1.0, H_clarify=0.5,
            U_val=10.0, Q_predicted=0.8, q_min=0.5
        ) == "DECLINE"

        # Level 3: Clarify on high uncertainty or high value of information or stress
        assert evaluate_decision_rule(
            gamma_hard=0.0, psi=1.0, psi_max=5.0, C_t=0.9, C_min=0.1,
            H_TZ=1.5, H_TZ_max=1.0, VoI=1.0, C_info=5.0, H_val=1.0, H_clarify=0.5,  # H_TZ > H_TZ_max
            U_val=10.0, Q_predicted=0.8, q_min=0.5
        ) == "CLARIFY"

        assert evaluate_decision_rule(
            gamma_hard=0.0, psi=1.0, psi_max=5.0, C_t=0.9, C_min=0.1,
            H_TZ=0.2, H_TZ_max=1.0, VoI=6.0, C_info=5.0, H_val=1.0, H_clarify=0.5,  # VoI > C_info
            U_val=10.0, Q_predicted=0.8, q_min=0.5
        ) == "CLARIFY"

        # Level 4: Execute on high quality and positive utility
        assert evaluate_decision_rule(
            gamma_hard=0.0, psi=1.0, psi_max=5.0, C_t=0.9, C_min=0.1,
            H_TZ=0.2, H_TZ_max=1.0, VoI=1.0, C_info=5.0, H_val=1.0, H_clarify=0.5,
            U_val=5.0, Q_predicted=0.8, q_min=0.5
        ) == "EXECUTE"
        
        # Level 5: Decline if not positive utility or not meeting minimum quality (not prohibited, just unprofitable)
        assert evaluate_decision_rule(
            gamma_hard=0.0, psi=1.0, psi_max=5.0, C_t=0.9, C_min=0.1,
            H_TZ=0.2, H_TZ_max=1.0, VoI=1.0, C_info=5.0, H_val=1.0, H_clarify=0.5,
            U_val=-2.0, Q_predicted=0.8, q_min=0.5  # U_val <= 0.0
        ) == "DECLINE"

    def test_new_appendix_a_math_contracts(self):
        """Test all newly introduced math core contracts from 02_MATHEMATICAL_CORE.md Appendix A."""
        from space1.utility import (
            check_gamma_hard,
            check_gamma_soft,
            update_phi_historical,
            compute_upsilon_scalar,
            update_upsilon,
            compute_omega,
            compute_learning_rate,
            compute_h,
            compute_lambda,
            VetoType,
            ReputationVector,
        )
        
        # 1. check_gamma_hard and check_gamma_soft
        hard_rules = [MaxCostRule(max_cost=10.0)]
        action_ok = Action(name="read", resource_cost=5.0)
        action_bad = Action(name="sudo", resource_cost=25.0)
        
        assert check_gamma_hard(action_ok, hard_rules) == 0.0
        assert check_gamma_hard(action_bad, hard_rules) == float('-inf')
        
        assert check_gamma_soft(action_ok, hard_rules) == 0.0
        assert check_gamma_soft(action_bad, hard_rules) == 1.0  # weight 1.0
        
        # 2. compute_phi new direct/positional contract
        phi_pos = compute_phi(100.0, 0.9, 10.0, 2.0)
        # Quality 0.9 vs expected 0.7, kappa_bonus=0.1 -> b_Q = 0.1 * 0.2 = 0.02.
        # price = 100 * 1.02 = 102.0. (102.0 - 10.0)/2.0 = 46.0
        assert phi_pos == 46.0
        
        # 3. update_phi_historical (Kalman filter)
        phi_hist = update_phi_historical(prev=40.0, observed=50.0, kalman_gain=0.1)
        # 40.0 + 0.1 * 10 = 41.0
        assert abs(phi_hist - 41.0) < 1e-5
        
        # 4. compute_quality direct contract with weights assertion
        q_pos = compute_quality(0.8, 0.9, 0.7, 0.8, (0.3, 0.3, 0.2, 0.2))
        assert abs(q_pos - 0.81) < 1e-5
        
        # weights sum assertion validation
        with pytest.raises(AssertionError):
            compute_quality(0.8, 0.9, 0.7, 0.8, (0.5, 0.5, 0.5, 0.5))
            
        # 5. compute_psi direct contract
        psi_pos = compute_psi(0.2, 20.0, 10.0)  # p_fail, c_direct, c_reputation
        # 0.2 * (20 + 10) = 6.0
        assert abs(psi_pos - 6.0) < 1e-5
        
        # 6. ReputationVector multidimensional scalar projection and updates
        rep: ReputationVector = {"tech": 0.9, "econ": 0.8, "comm": 0.7, "rel": 0.6, "sec": 0.5, "domain": 0.4}
        weights = {"tech": 0.2, "econ": 0.2, "comm": 0.15, "rel": 0.15, "sec": 0.15, "domain": 0.15}
        
        upsilon_scalar = compute_upsilon_scalar(rep, weights)
        assert abs(upsilon_scalar - 0.67) < 1e-5
        
        # update_upsilon vector update contract
        incidents = {"tech": 0, "sec": 1}
        rep_new = update_upsilon(rep, task_quality=1.0, n_positive_or_incidents=incidents)
        # tech: 0.9 + 0.1 * 1.0 = 1.0 (capped)
        # sec: 0.5 + 0.1 * 1.0 - 0.2 * 0.5 = 0.5
        assert rep_new["tech"] == 1.0
        assert abs(rep_new["sec"] - 0.50) < 1e-5
        
        # 7. compute_omega and learning rate
        assert compute_omega(0.8, 0.6, (0.7, 0.3)) == 0.74
        assert compute_learning_rate(0.1, 0.5, 0.2) == 0.05
        assert compute_learning_rate(0.1, 0.1, 0.2) == 0.02  # floor-bounded
        
        # 8. compute_h (unbounded ratio stress)
        assert compute_h(1.0, 1.2, 0.0, 1.2) == 1.10
        
        # 9. compute_lambda (Viability Ratio)
        # nu*voi + gamma*upsilon + phi_ft*dn_tasks_dt / (lambda_psi*psi + rho*error + delta*n_agents^2)
        lam = compute_lambda(voi=1.0, upsilon_scalar=0.8, dn_tasks_dt=5.0, psi=0.2, error_rate=0.1, n_agents=2)
        # reinforcing: 0.1*1 + 0.4*0.8 + 0.3*5 = 0.1 + 0.32 + 1.5 = 1.92
        # balancing: 0.5*0.2 + 0.2*0.1 + 0.1*4 = 0.1 + 0.02 + 0.4 = 0.52
        # lam = 1.92 / 0.52 = 3.6923
        assert abs(lam - 3.6923) < 0.01
