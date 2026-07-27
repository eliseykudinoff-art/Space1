"""
Tests for Phase 5 Multi-Agent, Environment, Knowledge Transfer, and 17 Factors
"""

import pytest

from space1.models import create_agent, create_task, TaskStatus
from space1.agents import ScoutAgent, WorkerAgent, FinanceAgent
from space1.environment import ClientProfile, MarketLead, MarketEnvironment
from space1.memory import StrategicMemory, StrategicExperience, TransferLearning
from space1.factors.registry import create_full_registry, FactorID


class TestPhase5MultiAgentAndEnvironment:
    """Test Suite for Space1 Phase 5 implementation."""

    def test_scout_agent_evaluates_leads(self):
        """Test ScoutAgent bidding and filtering rules."""
        agent_core = create_agent("Scout-1")
        scout = ScoutAgent(agent_core)
        
        # Scenario A: Good lead (high reward, low hours)
        task_good = create_task("Write fastAPI microservice")
        task_good.revenue = 300.0
        task_good.estimated_hours = 2.0
        
        eval_good = scout.evaluate_lead(task_good, ctx={})
        assert eval_good["decision"] == "BID"
        assert eval_good["phi"] > 10.0
        
        # Scenario B: Low profit lead - DECLINE (not REJECT per canonical spec)
        task_cheap = create_task("Answer simple email")
        task_cheap.revenue = 2.0
        task_cheap.estimated_hours = 1.0
        
        eval_cheap = scout.evaluate_lead(task_cheap, ctx={})
        assert eval_cheap["decision"] == "DECLINE"

    def test_worker_agent_executes_and_self_corrects(self):
        """Test WorkerAgent quality checkpoints and self-correction loop (x6)."""
        agent_core = create_agent("Worker-1")
        # Ensure LLM quality is high
        agent_core.capabilities.llm_quality = 0.90
        worker = WorkerAgent(agent_core)
        
        task = create_task("Train PyTorch model")
        task.metadata["quality_requirement"] = 0.85
        
        res = worker.execute_and_assess(task, complexity_modifier=1.2)
        
        # Worker should satisfy or self-correct to satisfy quality requirements
        assert res["status"] in ("completed", "failed")
        assert res["attempts"] >= 1
        assert 0.0 <= res["quality"] <= 1.0

    def test_finance_agent_bills_and_manages_budgets(self):
        """Test FinanceAgent bookkeeping and cost containment cuts."""
        agent_core = create_agent("Finance-1")
        agent_core.metrics.balance = 5.0
        agent_core.metrics.token_budget = 100.0
        
        finance = FinanceAgent(agent_core)
        
        task = create_task("Billing task")
        task.status = TaskStatus.COMPLETED
        task.revenue = 150.0
        
        # Test billing Completed project
        invoice_res = finance.process_invoice(task)
        assert invoice_res["success"] is True
        assert agent_core.metrics.balance == 155.0
        assert agent_core.metrics.total_earned == 150.0
        
        # Test budget cuts on low reserves
        agent_core.metrics.balance = 3.0  # critical low balance
        finance.enforce_budget_cuts(budget_limit=10.0)
        assert agent_core.metrics.token_budget == 50.0  # reduced by half

    def test_market_environment_lead_generation(self):
        """Test MarketEnvironment job streams, bidding competition, and feedback loops."""
        env = MarketEnvironment()
        
        # Stream 3 randomized leads
        tasks = env.stream_leads(count=3)
        assert len(tasks) == 3
        assert hasattr(tasks[0], "revenue")
        assert "client_rigor" in tasks[0].metadata
        
        # Test client reviews based on achieved quality vs requirements
        task = tasks[0]
        task.metadata["client_rigor"] = 0.5
        task.metadata["quality_requirement"] = 0.7
        task.metadata["client_reputation_multiplier"] = 1.5
        
        # Quality exceeds target (Delta >= 0.1) -> 5.0 score
        review = env.generate_review(task, achieved_quality=0.85)
        assert review["rating"] == 5.0
        assert review["reputation_multiplier"] == 1.5
        
        # Quality falls short -> rating penalty
        poor_review = env.generate_review(task, achieved_quality=0.5)
        assert poor_review["rating"] < 3.0

    def test_knowledge_transfer_learning(self):
        """Test G22 similarity metrics and delta_success knowledge transfer."""
        memory = StrategicMemory()
        transfer = TransferLearning(memory=memory, gamma_transfer=0.2)
        
        # Record completed similar task
        memory.add_experience(StrategicExperience(
            task_id="t-past",
            title="Deploy fastapi website",
            status="completed",
            strategy="Deploy via docker compose",
            revenue=100.0,
            cost=10.0,
            time_spent=2.0,
            quality=0.9,
            risk=0.1
        ))
        
        # Target task is highly similar
        target_task = create_task("Fastapi deployment task")
        
        sim = transfer.calculate_similarity(target_task, memory.get_experiences()[0])
        assert sim >= 0.2  # Overlapping word Jaccard similarity: fastapi/fastapi
        
        delta_s = transfer.calculate_transfer_delta(target_task)
        assert delta_s > 0.0
        assert delta_s <= 0.3  # Cap check

    def test_full_17_factors_registry(self):
        """Test that full 17 factors registry instantiates, registry computes total impacts successfully."""
        registry = create_full_registry()
        
        enabled_factors = registry.get_enabled()
        assert len(enabled_factors) == 17
        
        context = {
            "benchmarks": {"quality": 0.8, "reasoning": 0.8, "coding": 0.8, "agentic": 0.8},
            "budget": 50.0,
            "task_complexity": 0.6,
            "quality_requirement": 0.7,
            "active_guardrails": ["legal"],
            "risk_probabilities": {"legal": 0.1},
            "n_completed_tasks": 5,
            "current_knowledge": 0.4,
            "base_success": 0.3
        }
        
        total_deltas = registry.compute_total_deltas(context)
        assert "delta_success" in total_deltas
        assert "delta_time" in total_deltas
        assert total_deltas["delta_success"] > 0.0
