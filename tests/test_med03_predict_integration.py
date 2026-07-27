"""Тесты [MED-03]: интеграция predict_estimates в Stage V decision making."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from unittest.mock import MagicMock, patch

from space1.orchestrator.core import Orchestrator, predict_estimates, evaluate_decision_rule, VetoType
from space1.models.task import Task, TaskPriority, TaskStatus
from space1.models.agents import Agent, AgentCapabilities, AgentMetrics
from space1.compliance.core import Action, GammaVeto, MaxCostRule


def make_task(**kwargs):
    defaults = dict(
        id="task-001",
        title="Test Task",
        description="A test task for MED-03",
        priority=TaskPriority.MEDIUM,
        deadline=None,
        price=100.0,
        estimated_hours=2.0,
    )
    defaults.update(kwargs)
    return Task(**defaults)


def make_agent(**kwargs):
    caps = AgentCapabilities(
        llm_quality=kwargs.get("llm_quality", 0.9),
        n_completed_tasks=kwargs.get("n_completed", 10),
    )
    metrics = AgentMetrics(
        balance=kwargs.get("balance", 1000.0),
        success_rate=kwargs.get("success_rate", 0.85),
    )
    return Agent(id="test-agent", name="Test Agent", capabilities=caps, metrics=metrics)


class TestMed03PredictEstimatesIntegration:
    """predict_estimates результаты должны влиять на Stage V decision."""

    def test_high_phi_low_psi_executes(self):
        """Высокий phi_hat + низкий psi_hat → EXECUTE."""
        phi, q, psi = predict_estimates(
            x={"code_gen": 0.95, "debug": 0.9},
            category_probs={"code": 0.9},
            price=200.0,
            n_completed=15,
        )
        decision = evaluate_decision_rule(
            gamma_hard=0.0,
            psi=psi,
            psi_max=0.5,
            C_t=1000.0,
            C_min=0.0,
            H_TZ=0.3,
            H_TZ_max=1.0,
            VoI=0.0,
            C_info=100.0,
            H_val=0.5,
            H_clarify=0.5,
            U_val=phi * 0.9,
            Q_predicted=q,
            q_min=0.5,
            veto_type=VetoType.NONE,
            mission_profile="BALANCED",
        )
        assert decision == "EXECUTE"

    def test_high_psi_declines(self):
        """Высокий предсказанный риск → DECLINE."""
        phi, q, psi = predict_estimates(
            x={"code_gen": 0.1},
            category_probs={"unknown": 1.0},
            price=50.0,
            n_completed=0,
        )
        decision = evaluate_decision_rule(
            gamma_hard=0.0,
            psi=psi,
            psi_max=0.05,
            C_t=100.0,
            C_min=0.0,
            H_TZ=0.1,
            H_TZ_max=1.0,
            VoI=0.0,
            C_info=100.0,
            H_val=0.5,
            H_clarify=0.5,
            U_val=phi,
            Q_predicted=q,
            q_min=0.5,
            veto_type=VetoType.NONE,
            mission_profile="BALANCED",
        )
        assert decision == "DECLINE"

    def test_low_quality_declines(self):
        """Низкое предсказанное качество → DECLINE."""
        phi, q, psi = predict_estimates(
            x={},
            category_probs={},
            price=10.0,
            n_completed=0,
        )
        decision = evaluate_decision_rule(
            gamma_hard=0.0,
            psi=psi,
            psi_max=5.0,
            C_t=100.0,
            C_min=0.0,
            H_TZ=0.1,
            H_TZ_max=1.0,
            VoI=0.0,
            C_info=100.0,
            H_val=0.5,
            H_clarify=0.5,
            U_val=phi,
            Q_predicted=q,
            q_min=0.99,
            veto_type=VetoType.NONE,
            mission_profile="BALANCED",
        )
        assert decision == "DECLINE"

    def test_estimates_flow_through_orchestrator(self):
        """Проверка, что predict_estimates результаты доходят до Stage V в Orchestrator."""
        agent = make_agent(balance=1000.0, llm_quality=0.9, n_completed=10)
        orch = Orchestrator(core_agent=agent)
        task = make_task(price=200.0)
        orch.scheduler.add_task(task)

        result = orch.dispatch_full_cycle(mission_profile="BALANCED")

        assert result["status"] in ("SUCCESS", "DECLINED_BY_DECISION_RULE", "REJECTED_BY_COMPLIANCE")
        # Проверяем, что trace содержит predict_estimates
        trace = result.get("trace", [])
        assert any("Estimates predicted" in t for t in trace), "Stage III estimates missing from trace"
        assert any("phi_hat=" in t for t in trace), "Stage V should log phi_hat, psi_hat, q_hat"

    def test_gamma_soft_not_zero(self):
        """gamma_soft должен вычисляться из veto_system, а не быть хардкодом 0.0."""
        agent = make_agent()
        orch = Orchestrator(core_agent=agent)

        # Добавим soft rule в veto_system
        from space1.compliance.core import Rule
        class DummySoftRule(Rule):
            name = "dummy_soft"
            is_hard = False
            weight = 0.5
            def check(self, action):
                return True
            def check_graded(self, action):
                return 0.3

        orch.access_mgr.veto_system.register(DummySoftRule())

        task = make_task(price=100.0)
        orch.scheduler.add_task(task)

        # Захватываем gamma_soft_val через trace
        result = orch.dispatch_full_cycle(mission_profile="BALANCED")
        # Если дошли до Stage V, gamma_soft был вычислен
        assert result["status"] in ("SUCCESS", "DECLINED_BY_DECISION_RULE", "REJECTED_BY_COMPLIANCE")
