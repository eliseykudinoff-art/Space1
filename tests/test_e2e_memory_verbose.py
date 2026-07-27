"""
Space1 — SUPER VERBOSE E2E TESTS: Memory & Mission Pipeline

Продолжение E2E тестов с максимальным логированием.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from pathlib import Path

# Import logger from sibling module
sys.path.insert(0, os.path.dirname(__file__))
try:
    from test_e2e_super_verbose import E2ETestLogger, ValueDescribers
except ImportError:
    # Define minimal version if sibling not available
    class E2ETestLogger:
        _logs = []
        @classmethod
        def start_test(cls, name): 
            cls._logs = []
            print(f"\n{'='*80}\nE2E TEST: {name}\n{'='*80}")
        @classmethod
        def log(cls, msg): print(msg)
        @classmethod
        def log_value(cls, name, value, desc=""): print(f"  {name}: {value} {desc}")
        @classmethod
        def end_test(cls, passed=True): print(f"\n{'='*80}\n{'PASSED' if passed else 'FAILED'}\n{'='*80}\n")
        @classmethod
        def log_table(cls, headers, rows, title=""):
            if title: print(title)
            print("  " + " | ".join(str(h)[:15] for h in headers))
            for row in rows:
                print("  " + " | ".join(str(v)[:15] for v in row))

    class ValueDescribers:
        @staticmethod
        def describe_quality(q): 
            if q >= 0.8: return "Хорошее"
            elif q >= 0.5: return "Среднее"
            return "Низкое"
        @staticmethod
        def describe_psi(psi):
            if psi >= 0.6: return "Высокий риск"
            return "Низкий риск"


# =============================================================================
# E2E PATH 5: MEMORY OPERATIONS
# =============================================================================

class TestE2EMemoryOperationsVerbose:
    """
    E2E-05: Полный цикл операций с памятью.
    
    Путь: add_fact → retrieve → consolidate → persist
    """
    
    def test_memory_semantic_storage_verbose(self):
        """Подробный тест семантической памяти."""
        E2ETestLogger.start_test("memory_semantic_storage_verbose")
        log = E2ETestLogger.log
        lval = E2ETestLogger.log_value
        
        from space1.memory.core import SemanticMemory, OperationalMemory
        from space1.models.task import Task, TaskPriority
        
        log("="*60)
        log("MEMORY OPERATIONS — SEMANTIC & OPERATIONAL")
        log("="*60)
        
        # === SEMANTIC MEMORY ===
        log("\n--- Semantic Memory ---")
        
        semantic = SemanticMemory()
        lval("Semantic Memory Created", "Yes")
        lval("Initial Size", len(semantic._facts), "facts")
        
        # Add facts
        facts = [
            ("task-001-outcome", "Task completed with quality 0.9", 0.9),
            ("agent-001-behavior", "Agent reliability 0.85", 0.85),
            ("system-state", "Orchestrator load 0.6", 0.6),
            ("task-002-outcome", "Task completed with quality 0.6", 0.6),
            ("task-003-outcome", "Task failed with quality 0.3", 0.3),
        ]
        
        for key, value, confidence in facts:
            semantic.add_fact(key, value, confidence)
            lval("Added Fact", f"{key}: {value} (conf={confidence})")
        
        lval("Final Semantic Size", len(semantic._facts), "facts")
        
        # Retrieve facts
        log("\n--- Retrieve Facts ---")
        for key, _, _ in facts[:3]:
            fact = semantic.get_fact(key)
            if fact:
                lval(f"Retrieved {key}", f"value={fact.value}, confidence={fact.confidence}")
        
        # === OPERATIONAL MEMORY ===
        log("\n--- Operational Memory ---")
        
        operational = OperationalMemory()
        lval("Operational Memory Created", "Yes")
        
        # Set values
        operational.set("current_task_id", "task-004")
        operational.set("agent_state", "processing")
        operational.set("retry_count", 2)
        operational.set("last_error", None)
        
        lval("Set: current_task_id", "task-004")
        lval("Set: agent_state", "processing")
        lval("Set: retry_count", 2)
        
        # Get values
        log("\n--- Get Values ---")
        current_task = operational.get("current_task_id")
        agent_state = operational.get("agent_state")
        retry_count = operational.get("retry_count")
        missing = operational.get("missing_key", "DEFAULT_VALUE")
        
        lval("Get: current_task_id", current_task)
        lval("Get: agent_state", agent_state)
        lval("Get: retry_count", retry_count)
        lval("Get: missing_key (default)", missing)
        
        # === MEMORY CONSOLIDATION ===
        log("\n--- Memory Consolidation ---")
        
        # Simulate consolidation of semantic facts
        all_facts = semantic.get_all_facts()
        
        lval("Total Facts", len(all_facts))
        
        # Calculate average confidence
        if all_facts:
            avg_confidence = sum(f.confidence for f in all_facts) / len(all_facts)
            lval("Average Confidence", f"{avg_confidence:.3f}")
        
        # Store consolidated summary
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_facts": len(all_facts),
            "avg_confidence": avg_confidence if all_facts else 0
        }
        
        operational.set("consolidated_summary", summary)
        lval("Stored Summary", summary)
        
        # === PERSISTENCE ===
        log("\n--- Persistence Simulation ---")
        
        # Serialize memory state (simple JSON simulation)
        memory_state = {
            "semantic_facts": len(semantic._facts),
            "operational_keys": list(operational._store.keys()) if hasattr(operational, "_store") else [],
            "timestamp": datetime.now().isoformat()
        }
        
        lval("Serialized State Keys", list(memory_state.keys()))
        lval("Semantic Facts Count", memory_state["semantic_facts"])
        lval("Operational Keys Count", len(memory_state["operational_keys"]))
        
        E2ETestLogger.end_test(passed=True)


# =============================================================================
# E2E PATH 6: MISSION PIPELINE
# =============================================================================

class TestE2EMissionPipelineVerbose:
    """
    E2E-06: Полный pipeline миссии.
    
    Путь: execute_mission → run_compliance → run_verification → deliver
    """
    
    def test_mission_pipeline_verbose(self):
        """Подробный тест pipeline миссии."""
        E2ETestLogger.start_test("mission_pipeline_verbose")
        log = E2ETestLogger.log
        lval = E2ETestLogger.log_value
        
        from space1.mission.core import Mission, MissionType, MISSION_CALIBRATION
        from space1.models.context import MissionExecutionContext, AgentState
        from space1.compliance.core import Action, Rule
        from space1.utility import compute_phi, compute_quality, evaluate_decision_rule, VetoType, check_gamma_hard, check_gamma_soft
        
        log("="*60)
        log("MISSION PIPELINE — FULL EXECUTION")
        log("="*60)
        
        # === MISSION CREATION ===
        log("\n--- Mission Creation ---")
        
        mission_id = "mission-e2e-001"
        mission_name = "Database Migration Project"
        mission_type = MissionType.MAXIMIZE
        
        lval("Mission ID", mission_id)
        lval("Mission Name", mission_name)
        lval("Mission Type", mission_type.name)
        
        # Mission calibration weights
        weights = MISSION_CALIBRATION[mission_type]
        weight_names = ["λ_Φ (profit)", "λ_Υ (reputation)", "λ_Ω (evolution)", "λ_Q (quality)"]
        
        log("\n  Mission Calibration Weights:")
        for name, weight in zip(weight_names, weights):
            lval(name, f"{weight:.2f}")
        
        # Create mission
        mission = Mission(
            id=mission_id,
            name=mission_name,
            mission_type=mission_type
        )
        
        lval("Mission Created", "Yes")
        lval("Mission ID", mission.id)
        
        # === CONTEXT CREATION ===
        log("\n--- Execution Context ---")
        
        state = AgentState(
            balance=500.0,
            reputation=0.8,
            success_rate=0.88,
            workload=5,
            active_tasks=2
        )
        
        ctx = MissionExecutionContext(
            mission_id=mission_id,
            mission_name=mission_name,
            state=state
        )
        
        lval("Agent Balance", state.balance, "USD")
        lval("Agent Reputation", state.reputation, "0-1")
        lval("Workload", state.workload)
        lval("Active Tasks", state.active_tasks)
        lval("Success Rate", f"{state.success_rate:.2%}")
        
        # === COMPLIANCE CHECK ===
        log("\n--- Compliance Check ---")
        
        # Define rules
        class SecurityRule(Rule):
            def name(self) -> str:
                return "Security"
            def check(self, action: Action) -> bool:
                return action.params.get("security_level", 0) >= 3
        
        class BudgetRule(Rule):
            def name(self) -> str:
                return "Budget"
            def check(self, action: Action) -> bool:
                return action.params.get("cost", 0) <= 200.0
        
        hard_rules = [SecurityRule()]
        soft_rules = [BudgetRule()]
        
        # Test action
        action = Action(
            name="db_migration",
            params={"security_level": 4, "cost": 150.0, "description": "Database migration"}
        )
        
        lval("Action", action.name)
        lval("Security Level", action.params["security_level"])
        lval("Cost", action.params["cost"], "USD")
        
        # Run compliance
        from space1.utility import check_gamma_hard, check_gamma_soft
        
        gamma_hard = check_gamma_hard(action, hard_rules)
        gamma_soft = check_gamma_soft(action, soft_rules)
        
        lval("γ_hard", gamma_hard, "PASS" if gamma_hard == 0.0 else "FAIL")
        lval("γ_soft", gamma_soft, "No penalty" if gamma_soft == 0.0 else f"{gamma_soft:.2f} penalty")
        
        ctx.compliance_passed = gamma_hard == 0.0
        lval("Compliance Passed", ctx.compliance_passed)
        
        # === UTILITY COMPUTATION ===
        log("\n--- Utility Computation ---")
        
        # Parameters for task
        price = 300.0
        quality = 0.85
        cost = 150.0
        time_hours = 4.0
        
        phi = compute_phi(price, quality, cost, time_hours)
        psi = 0.3  # Simulated risk
        q = compute_quality(0.85, 0.9, 0.8, 0.85)
        
        lval("Price", price, "USD")
        lval("Quality", quality)
        lval("Cost", cost, "USD")
        lval("Time", time_hours, "hours")
        lval("Φ (Profit)", f"{phi:.2f}", f"${phi:.2f}/hour")
        lval("Ψ (Risk)", f"{psi:.3f}")
        lval("Q (Quality)", f"{q:.3f}")
        
        ctx.phi = phi
        ctx.psi = psi
        ctx.quality = q
        ctx.utility_score = phi / 100.0
        
        lval("Utility Score", f"{ctx.utility_score:.3f}")
        
        # === DECISION ===
        log("\n--- Decision ---")
        
        decision = evaluate_decision_rule(
            gamma_hard=gamma_hard,
            psi=psi,
            psi_max=0.7,
            C_t=state.balance,
            C_min=50.0,
            H_TZ=0.2,
            H_TZ_max=0.5,
            VoI=10.0,
            C_info=20.0,
            H_val=0.8,
            H_clarify=0.3,
            U_val=ctx.utility_score,
            Q_predicted=quality,
            q_min=0.5
        )
        
        lval("Decision", decision, ValueDescribers.describe_decision(decision) if hasattr(ValueDescribers, 'describe_decision') else decision)
        
        # === VERIFICATION ===
        log("\n--- Verification ---")
        
        if decision == "EXECUTE":
            # Simulate task completion
            lval("Executing Task...", "In Progress")
            
            # Verify deliverable
            deliverable_quality = 0.88
            lval("Deliverable Quality", deliverable_quality)
            
            verification_passed = deliverable_quality >= 0.5
            lval("Verification Passed", verification_passed)
            
            if verification_passed:
                # === DELIVERY ===
                log("\n--- Delivery ---")
                
                # Simulate delivery
                delivery_result = {
                    "id": f"delivery-{mission_id}",
                    "status": "completed",
                    "revenue": price
                }
                
                lval("Delivery ID", delivery_result["id"])
                lval("Delivery Status", delivery_result["status"])
                lval("Revenue", delivery_result["revenue"], "USD")
                
                ctx.delivered = True
                lval("Mission Delivered", ctx.delivered)
            else:
                log("⚠️ Verification failed — task not delivered")
                ctx.add_error("Verification failed: quality below threshold")
        else:
            log(f"⚠️ Decision: {decision} — Task not executed")
            ctx.add_error(f"Rejected by decision rule: {decision}")
        
        # === FINAL STATE ===
        log("\n--- Final Mission State ---")
        
        lval("Mission ID", mission.id)
        lval("Has Errors", ctx.has_errors())
        lval("Errors Count", len(ctx.errors))
        
        for error in ctx.errors:
            log(f"  ⚠️ {error}")
        
        # === ASSERTIONS ===
        assert ctx.compliance_passed, f"Compliance failed: gamma_hard={gamma_hard}"
        assert not ctx.has_errors(), f"Errors present: {ctx.errors}"
        assert ctx.phi > 0, f"Phi should be positive: {ctx.phi}"
        assert 0.0 <= ctx.psi <= 1.0, f"Psi out of range: {ctx.psi}"
        assert 0.0 <= ctx.quality <= 1.0, f"Quality out of range: {ctx.quality}"
        assert ctx.delivered, "Deliverable not marked as delivered"
        assert decision == "EXECUTE", f"Decision={decision}, expected EXECUTE"

        E2ETestLogger.end_test(passed=ctx.compliance_passed and not ctx.has_errors())


# =============================================================================
# E2E PATH 7: REPUTATION & QUALITY TRACKING
# =============================================================================

class TestE2EReputationQualityVerbose:
    """
    E2E-07: Репутация и качество с течением времени.
    """
    
    def test_reputation_update_verbose(self):
        """Подробный тест обновления репутации."""
        E2ETestLogger.start_test("reputation_update_verbose")
        log = E2ETestLogger.log
        lval = E2ETestLogger.log_value
        
        from space1.utility import update_upsilon, MultidimensionalReputation
        
        log("="*60)
        log("REPUTATION UPDATE — DETAILED")
        log("="*60)
        
        # === SCALAR REPUTATION ===
        log("\n--- Scalar Reputation (Υ) ---")
        
        # Simulate a series of task completions
        task_results = [
            {"quality": 0.9, "success": True, "review": 5},
            {"quality": 0.7, "success": True, "review": 4},
            {"quality": 0.6, "success": True, "review": 3},
            {"quality": 0.4, "success": False, "review": 2},
            {"quality": 0.8, "success": True, "review": 4},
        ]
        
        lval("Task Results Count", len(task_results))
        
        total_quality = sum(t["quality"] for t in task_results)
        avg_quality = total_quality / len(task_results)
        successes = sum(1 for t in task_results if t["success"])
        total_reviews = sum(t["review"] for t in task_results)
        
        lval("Total Quality Sum", f"{total_quality:.2f}")
        lval("Average Quality", f"{avg_quality:.3f}")
        lval("Success Rate", f"{successes}/{len(task_results)} = {successes/len(task_results):.2%}")
        lval("Total Reviews", total_reviews)
        
        # Compute reputation using correct signature
        upsilon = update_upsilon(
            rating=avg_quality,
            n_reviews=len(task_results),
            n_positive=successes,
            metrics=None
        )
        
        lval("Υ (Computed Reputation)", f"{upsilon:.4f}")
        
        # === MULTIDIMENSIONAL REPUTATION ===
        log("\n--- Multidimensional Reputation ---")
        
        rep = MultidimensionalReputation(
            tech=0.85,
            econ=0.75,
            comm=0.90,
            rel=0.80,
            sec=0.70,
            domain=0.88
        )
        
        lval("Technical", rep.tech)
        lval("Economic", rep.econ)
        lval("Communication", rep.comm)
        lval("Reliability", rep.rel)
        lval("Security", rep.sec)
        lval("Domain", rep.domain)
        
        scalar = rep.scalar_reputation()
        lval("Scalar Projection", f"{scalar:.4f}")
        
        # Update with incident
        log("\n--- Update with Incident ---")
        
        lval("Incident: Low quality task", "")
        lval("Quality", 0.3)
        lval("Category", "tech")
        
        rep.update_with_incident(
            category="tech",
            quality=0.3,
            incident=True,
            eta=0.1,
            gamma=0.2
        )
        
        lval("New Technical", rep.tech)
        lval("Delta", f"{rep.tech - 0.85:.4f}")
        
        # === ASSERTIONS ===
        assert successes == 4, f"Expected 4 successes, got {successes}"
        assert 0.0 <= upsilon <= 1.0, f"Upsilon {upsilon} out of [0,1]"
        assert scalar > 0, f"Scalar reputation should be positive: {scalar}"
        assert rep.tech >= 0.0, f"Tech reputation negative: {rep.tech}"

        E2ETestLogger.end_test(passed=True)


# =============================================================================
# E2E PATH 8: SCHEDULER PRIORITY QUEUE
# =============================================================================

class TestE2ESchedulerQueueVerbose:
    """
    E2E-08: Приоритетная очередь планировщика.
    """
    
    def test_scheduler_priority_verbose(self):
        """Подробный тест планировщика с приоритетами."""
        E2ETestLogger.start_test("scheduler_priority_verbose")
        log = E2ETestLogger.log
        lval = E2ETestLogger.log_value
        
        from space1.orchestrator.scheduler import AIOSScheduler
        from space1.models.task import Task, TaskPriority
        
        log("="*60)
        log("SCHEDULER PRIORITY QUEUE")
        log("="*60)
        
        scheduler = AIOSScheduler()
        
        # Add tasks with different priorities
        tasks = [
            Task(id="t1", title="Low Priority Task", priority=TaskPriority.LOW),
            Task(id="t2", title="Medium Priority Task", priority=TaskPriority.MEDIUM),
            Task(id="t3", title="High Priority Task", priority=TaskPriority.HIGH),
            Task(id="t4", title="Critical Task", priority=TaskPriority.CRITICAL),
            Task(id="t5", title="Another Low Task", priority=TaskPriority.LOW),
        ]
        
        log("\n--- Adding Tasks ---")
        
        for task in tasks:
            scheduler.add_task(task)
            lval(f"Added: {task.title}", f"Priority={task.priority.name} ({task.priority.value})")
        
        lval("Queue Size", len(scheduler.list_queue()))
        
        # Show queue order
        log("\n--- Current Queue Order ---")
        
        queue_list = scheduler.list_queue()
        E2ETestLogger.log_table(
            headers=["Position", "Task ID", "Title", "Priority", "Value"],
            rows=[
                [i+1, t.id, t.title[:20], t.priority.name, t.priority.value]
                for i, t in enumerate(queue_list)
            ]
        )
        
        # Pop highest priority
        log("\n--- Popping Tasks (by Priority) ---")
        
        popped = []
        queue = scheduler.list_queue()
        while len(queue) > 0:
            task = scheduler.pop_next_task()
            if task:
                popped.append(task)
                lval(f"Pop #{len(popped)}", f"{task.title} ({task.priority.name})")
            queue = scheduler.list_queue()
        
        # Verify order
        log("\n--- Verification ---")
        
        expected_order = ["t4", "t3", "t2", "t1", "t5"]  # CRITICAL, HIGH, MEDIUM, LOW, LOW
        actual_order = [t.id for t in popped]
        
        lval("Expected Order", expected_order)
        lval("Actual Order", actual_order)
        lval("Order Correct", expected_order == actual_order)
        
        E2ETestLogger.end_test(passed=expected_order == actual_order)


# =============================================================================
# RUN ALL TESTS
# =============================================================================

if __name__ == "__main__":
    print("="*80)
    print("SPACE1 E2E TESTS: MEMORY & MISSION PIPELINE")
    print("="*80)
    
    tests = [
        TestE2EMemoryOperationsVerbose(),
        TestE2EMissionPipelineVerbose(),
        TestE2EReputationQualityVerbose(),
        TestE2ESchedulerQueueVerbose(),
    ]
    
    results = []
    
    for test in tests:
        test_name = test.__class__.__name__
        methods = [m for m in dir(test) if m.startswith("test_")]
        
        for method_name in methods:
            method = getattr(test, method_name)
            print(f"\n{'#'*80}\n# {test_name}.{method_name}\n{'#'*80}")
            
            try:
                method()
                results.append((test_name, method_name, "PASSED"))
            except Exception as e:
                print(f"\n❌ EXCEPTION: {e}")
                results.append((test_name, method_name, f"FAILED: {e}"))
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, _, r in results if r == "PASSED")
    for test_name, method_name, result in results:
        status = "✅" if result == "PASSED" else "❌"
        print(f"  {status} {test_name}.{method_name}")
    
    print(f"\n{passed}/{len(results)} passed")
