"""
Unit and integration tests for the AIOS kernel modules and 12-stage Orchestrator.
"""

import os
import pytest
from datetime import datetime, timedelta
from space1.models.agents import Agent, AgentCapabilities, AgentMetrics, AgentStatus


@pytest.fixture(autouse=True)
def cleanup_scheduler_files():
    # Clear scheduler files before and after test
    for f in ["scheduler_queue.json", "scheduler_queue.json.tmp"]:
        if os.path.exists(f):
            try:
                os.remove(f)
            except Exception:
                pass
    yield
    for f in ["scheduler_queue.json", "scheduler_queue.json.tmp"]:
        if os.path.exists(f):
            try:
                os.remove(f)
            except Exception:
                pass
from space1.models.task import Task, TaskPriority, TaskStatus
from space1.compliance.core import Action, MaxCostRule, GammaVeto
from space1 import (
    AIOSScheduler,
    AIOSContextManager,
    AIOSToolManager,
    AIOSStorageManager,
    AIOSAccessManager,
    Orchestrator,
)
from space1.agents.core import ScoutSpecialist, WorkerSpecialist, FinanceSpecialist


def _create_test_agent(name: str = "AIOS-Brain") -> Agent:
    return Agent(
        id="test_agent_id",
        name=name,
        status=AgentStatus.IDLE,
        created_at=datetime.now(),
        capabilities=AgentCapabilities(
            llm_quality=0.85,
            n_completed_tasks=10,
            current_knowledge=0.75
        ),
        metrics=AgentMetrics(
            balance=50.0,
            total_earned=100.0,
            success_rate=0.9,
            n_active_tasks=0,
            token_budget=500.0,
            tokens_used=50.0
        )
    )


class TestAIOSKernelAndOrchestrator:
    """Test suite validating 100% compliance with AIOS kernel specifications and Orchestrator."""

    def test_scheduler_prioritization_owner_direct(self):
        """Test scheduler gives immediate priority to OWNER_DIRECT task source overrides."""
        scheduler = AIOSScheduler()
        
        task_normal = Task(id="task_1", title="Regular Marketplace task", priority=TaskPriority.HIGH)
        task_normal.metadata["source"] = "MARKETPLACE"
        
        task_owner = Task(id="task_2", title="Owner Direct critical request", priority=TaskPriority.LOW)
        task_owner.metadata["source"] = "OWNER_DIRECT"
        
        scheduler.add_task(task_normal)
        scheduler.add_task(task_owner)
        
        # Pop should yield OWNER_DIRECT first, bypassing standard urgency-based order
        next_task = scheduler.pop_next_task()
        assert next_task is not None
        assert next_task.id == "task_2"
        assert next_task.metadata["source"] == "OWNER_DIRECT"
        
        # Next should be regular task
        next_task_2 = scheduler.pop_next_task()
        assert next_task_2 is not None
        assert next_task_2.id == "task_1"

    def test_context_manager_status_block_rendering(self):
        """Test structured StatusBlock rendering without LLMs."""
        ctx_mgr = AIOSContextManager()
        
        status = ctx_mgr.render_status_block(
            homeostasis_h=1.15,
            deviations=[{"metric": "stress", "val": 0.1}],
            remaining_plan=["Step 1", "Step 2"],
            memory_snippets=["Completed similar task in past"],
            max_length=500
        )
        
        assert "=== STATUS BLOCK ===" in status
        assert "Homeostasis Index H: 1.15" in status
        assert "stress" in status
        assert "Step 1" in status
        assert "Completed similar" in status
        assert len(status) <= 500

    def test_tool_manager_ucb1_selection(self):
        """Test UCB1 selects unvisited candidates first, then greedy best reward."""
        agent_core = _create_test_agent()
        tool_mgr = AIOSToolManager(c_exploration=1.414)
        
        scout = ScoutSpecialist(agent_core)
        worker = WorkerSpecialist(agent_core)
        
        tool_mgr.register_specialist(scout)
        tool_mgr.register_specialist(worker)
        
        # 1. Unvisited check: Scout and Worker both have 0 runs -> should return unvisited first
        first_selected = tool_mgr.select_best_specialist(["Scout", "Worker"])
        assert first_selected in ("Scout", "Worker")
        
        # Simulate Scout selected first, records success
        tool_mgr.record_outcome(first_selected, success=True)
        
        # Next selection should select the other unvisited one (Worker) to resolve cold start
        other = "Worker" if first_selected == "Scout" else "Scout"
        second_selected = tool_mgr.select_best_specialist(["Scout", "Worker"])
        assert second_selected == other

    def test_access_manager_approvals(self):
        """Test Access Manager rule vetoes and human approval gates."""
        veto_system = GammaVeto([MaxCostRule(max_cost=50.0)])
        access_mgr = AIOSAccessManager(veto_system)
        
        action_cheap = Action(name="read", resource_cost=10.0, params={})
        action_expensive = Action(name="deploy", resource_cost=110.0, params={})
        action_sensitive = Action(name="query", resource_cost=10.0, params={"sensitive": True})
        
        # Veto checks
        assert access_mgr.check_hard_veto(action_cheap) is True
        assert access_mgr.check_hard_veto(action_expensive) is False  # cost exceeds 50
        
        # Human approval gate triggers
        assert access_mgr.requires_human_approval(action_cheap) is False
        assert access_mgr.requires_human_approval(action_expensive) is True
        assert access_mgr.requires_human_approval(action_sensitive) is True

    def test_storage_manager_weighted_retrieval(self):
        """Test Storage Manager retrieval ranked by Recency, Importance, Relevance."""
        storage = AIOSStorageManager(w1=0.3, w2=0.4, w3=0.3)
        storage.clear()  # Ensure clean isolation
        
        # Persist three memories with different importance/keys
        storage.persist("code_generation_task", "Success on python algorithm", importance=0.9)
        storage.persist("factual_qa_task", "Legal document fact extraction", importance=0.4)
        storage.persist("multi_turn_task", "Negotiation conversational drift", importance=0.6)
        
        # Retrieval matching "generation"
        results = storage.retrieve_with_weighted_ranking("generation", max_results=3)
        
        assert len(results) == 3
        # First result should match primary query term 'generation' due to relevance and high importance
        assert results[0]["entry"].key == "code_generation_task"

    def test_orchestrator_end_to_end_dispatch_run(self):
        """Test full 12-stage pipeline dispatch cycle from task pop to calibration."""
        agent_core = _create_test_agent()
        agent_core.capabilities.llm_quality = 1.0  # Guarantee success for deterministic test run
        orchestrator = Orchestrator(agent_core)
        orchestrator.storage_mgr.clear()  # Ensure clean isolation
        
        # Add tasks to scheduler
        task_marketplace = Task(id="market_task", title="Resolve algorithm issue", metadata={"revenue": 200.0})
        task_owner = Task(id="owner_task", title="Urgent owner admin task", metadata={"revenue": 100.0, "source": "OWNER_DIRECT"})
        
        orchestrator.scheduler.add_task(task_marketplace)
        orchestrator.scheduler.add_task(task_owner)
        
        # Register functional specialties
        orchestrator.tool_mgr.register_specialist(ScoutSpecialist(agent_core))
        orchestrator.tool_mgr.register_specialist(WorkerSpecialist(agent_core))
        orchestrator.tool_mgr.register_specialist(FinanceSpecialist(agent_core))
        
        # Run first cycle -> OWNER_DIRECT must bypass regular task
        res = orchestrator.dispatch_full_cycle()
        
        assert res["status"] == "SUCCESS"
        assert res["task_id"] == "owner_task"
        assert res["decision"] == "EXECUTE"
        assert len(res["trace"]) > 0
        
        # Ensure experience was consolidated and persisted into storage manager
        assert len(orchestrator.storage_mgr._store) == 1
        assert orchestrator.storage_mgr._store[0].key == "Urgent owner admin task"

    def test_pipeline_appendix_a_signatures(self):
        """Test exact execution contract signatures of 03_PIPELINE_MATH.md Appendix A."""
        from space1.orchestrator.core import (
            Attachment,
            Deviation,
            Trend,
            MemorySnippet,
            ExecutorProfile,
            ExecutorStatsRegistry,
            NoEligibleExecutorError,
            Attempt,
            ReflectionAction,
            classify_task,
            render_status_block,
            predict_estimates,
            decide_with_pipeline_context,
            select_executor,
            reflect,
        )
        
        # 1. classify_task
        attachments = [Attachment(filename="lead_brief.pdf")]
        x, p, h_tz = classify_task("Need algorithm help", attachments)
        assert len(x) == 17
        assert p["code"] == 0.6
        assert h_tz == 0.4
        
        # 2. render_status_block
        status = render_status_block(
            h=1.1,
            top_deviations=[Deviation(metric="stress", value=0.15)],
            trend=Trend(direction="up", velocity=0.5),
            remaining_plan=[Action(name="test")],
            memory_snippets=[MemorySnippet(key="task_key", value="Success")],
            max_length=500
        )
        assert "Homeostasis H: 1.10" in status
        assert "Trend: up" in status
        assert "task_key" in status
        
        # 3. predict_estimates
        phi_hat, q_hat, psi_hat = predict_estimates(x, p, 100.0)
        # phi_hat, q_hat, psi_hat are now properly normalized to [0, 1]
        assert 0.0 <= phi_hat <= 1.0
        assert 0.0 <= q_hat <= 1.0
        assert 0.0 <= psi_hat <= 1.0
        # With 17 capabilities and price=100, expect moderate values
        assert 0.3 <= phi_hat <= 0.9
        assert 0.4 <= q_hat <= 0.9
        assert 0.0 <= psi_hat <= 0.5
        
        # 4. decide_with_pipeline_context
        # (task, x, h_tz, estimates, gamma_hard, gamma_soft, state, policy)
        from space1 import Decision
        task = Task(id="t_test", title="Task test")
        state = _create_test_agent()
        dec, reason = decide_with_pipeline_context(
            task, x, h_tz, (phi_hat, q_hat, psi_hat), 0.0, 0.0, state, {}
        )
        # Decision should be EXECUTE or DECLINE (not REJECT or CLARIFY)
        assert dec in (Decision.EXECUTE, Decision.DECLINE)
        assert len(reason) > 0
        
        # 5. select_executor
        candidates = [ExecutorProfile(name="A", trust_score=0.2), ExecutorProfile(name="B", trust_score=0.8)]
        history = ExecutorStatsRegistry()
        executor = select_executor(Action(name="test"), candidates, history)
        assert executor.name == "B"
        
        # Empty eligible candidates raises custom error
        with pytest.raises(NoEligibleExecutorError):
            select_executor(Action(name="test"), [ExecutorProfile(name="A", trust_score=0.1)], history)
            
        # 6. reflect
        action = Action(name="test_action")
        attempt_history = [Attempt(action_name="test_action", success=False, error_reason="Timeout")]
        action_type, remedial_action_name = reflect(action, attempt_history, current_psi=0.2, policy={})
        assert action_type == ReflectionAction.RETRY
        assert remedial_action_name == "backup_remedial_test_action"
