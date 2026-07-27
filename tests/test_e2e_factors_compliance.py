"""
Space1 — SUPER VERBOSE E2E TESTS: Factors, Compliance, Verifier

Финальная часть E2E тестов с максимальным логированием.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from enum import Enum

# Import logger
sys.path.insert(0, os.path.dirname(__file__))
try:
    from test_e2e_super_verbose import E2ETestLogger, ValueDescribers
except ImportError:
    from test_e2e_memory_verbose import E2ETestLogger, ValueDescribers


# =============================================================================
# E2E PATH 9: FACTOR AGGREGATION
# =============================================================================

class TestE2EFactorAggregationVerbose:
    """
    E2E-09: Агрегация всех факторов.
    
    Тестирует систему факторов с полным логированием.
    """
    
    def test_factor_aggregation_verbose(self):
        """Подробный тест агрегации факторов."""
        E2ETestLogger.start_test("factor_aggregation_verbose")
        log = E2ETestLogger.log
        lval = E2ETestLogger.log_value
        
        from space1.factors.registry import create_mvp_registry, FactorRegistry
        from space1.models.task import Task, TaskPriority
        from space1.models.agents import Agent, AgentCapabilities, AgentMetrics
        
        log("="*60)
        log("FACTOR AGGREGATION — ALL FACTORS")
        log("="*60)
        
        # Create registry
        registry = create_mvp_registry()
        
        lval("Registry Created", "Yes")
        lval("Registered Factors", len(registry._factors))
        
        # List all factors
        log("\n--- Registered Factors ---")
        for factor_id, factor in registry._factors.items():
            lval(f"Factor: {factor_id}", f"priority={factor.priority if hasattr(factor, 'priority') else 'N/A'}")
        
        # Create test context
        log("\n--- Test Context ---")
        
        task = Task(
            id="factor-test-task",
            title="Complex API Integration",
            description="Integration with third-party API requiring security",
            priority=TaskPriority.HIGH,
            deadline=datetime.now() + timedelta(hours=48)
        )
        
        agent = Agent(
            id="factor-test-agent",
            name="Expert Agent",
            capabilities=AgentCapabilities(
                n_completed_tasks=50,
                current_knowledge=0.8,
                llm_quality=0.9,
                code_gen=0.85
            ),
            metrics=AgentMetrics(
                balance=200.0,
                success_rate=0.85,
            )
        )
        
        lval("Task", task.title)
        lval("Task Priority", task.priority.name)
        lval("Agent", agent.name)
        lval("Agent Success Rate", f"{agent.metrics.success_rate:.2%}")
        lval("Agent Completed Tasks", agent.capabilities.n_completed_tasks)
        
        # Build factor context
        log("\n--- Building Factor Context ---")
        
        from space1.utility import build_factor_context
        
        context = build_factor_context(task, agent)
        
        lval("Context Keys", list(context.keys()))
        lval("Benchmarks", context.get("benchmarks", {}))
        lval("Budget", context.get("budget", 0))
        lval("Task Complexity", context.get("task_complexity", 0))
        lval("Quality Requirement", context.get("quality_requirement", 0))
        lval("N Completed Tasks", context.get("n_completed_tasks", 0))
        lval("Current Knowledge", context.get("current_knowledge", 0))
        lval("Base Success Rate", context.get("base_success", 0))
        
        # Aggregate factors
        log("\n--- Factor Computation ---")
        
        from space1.utility import aggregate_factors
        
        result = aggregate_factors(context, registry)
        
        lval("Result Keys", list(result.keys()))
        lval("Delta Success", f"{result['delta_success']:.4f}")
        lval("Delta Time", f"{result['delta_time']:.4f}")
        lval("Omega (Evolution)", f"{result['omega']:.4f}")
        
        # Show individual factor results
        log("\n--- Individual Factor Results ---")
        
        factor_results = result.get("results", {})
        for factor_name, factor_result in factor_results.items():
            lval(f"Factor: {factor_name}", "")
            lval("  Value", f"{factor_result.value:.4f}" if hasattr(factor_result, "value") else "N/A")
            lval("  Delta Success", f"{factor_result.delta_success:.4f}" if hasattr(factor_result, "delta_success") else "N/A")
            lval("  Delta Time", f"{factor_result.delta_time:.4f}" if hasattr(factor_result, "delta_time") else "N/A")
        
        E2ETestLogger.end_test(passed=True)


# =============================================================================
# E2E PATH 10: COMPLIANCE RULES
# =============================================================================

class TestE2EComplianceRulesVerbose:
    """
    E2E-10: Тестирование правил compliance.
    """
    
    def test_compliance_rules_verbose(self):
        """Подробный тест compliance checker."""
        E2ETestLogger.start_test("compliance_rules_verbose")
        log = E2ETestLogger.log
        lval = E2ETestLogger.log_value
        
        from space1.compliance.core import Action, Rule
        from space1.utility import check_gamma_hard, check_gamma_soft
        
        log("="*60)
        log("COMPLIANCE RULES — DETAILED")
        log("="*60)
        
        # Define test rules
        log("\n--- Rule Definitions ---")
        
        # Hard Rule 1: Minimum security level
        class MinSecurityRule(Rule):
            def name(self) -> str:
                return "MinSecurity"
            def check(self, action: Action) -> bool:
                level = action.params.get("security_level", 0)
                result = level >= 3
                log(f"  MinSecurity: level={level} >= 3 = {result}")
                return result
        
        # Hard Rule 2: Budget limit
        class BudgetLimitRule(Rule):
            def name(self) -> str:
                return "BudgetLimit"
            def check(self, action: Action) -> bool:
                cost = action.params.get("cost", 0)
                result = cost <= 500
                log(f"  BudgetLimit: cost={cost} <= 500 = {result}")
                return result
        
        # Soft Rule 1: Preferred completion time
        class PreferredTimeRule(Rule):
            def name(self) -> str:
                return "PreferredTime"
            def check(self, action: Action) -> bool:
                hours = action.params.get("estimated_hours", 24)
                result = hours <= 8
                log(f"  PreferredTime: hours={hours} <= 8 = {result}")
                return result
        
        # Soft Rule 2: Quality requirement
        class QualityRequirementRule(Rule):
            def name(self) -> str:
                return "QualityReq"
            def check(self, action: Action) -> bool:
                quality = action.params.get("min_quality", 1.0)
                result = quality <= 0.9
                log(f"  QualityReq: min_quality={quality} <= 0.9 = {result}")
                return result
        
        hard_rules = [MinSecurityRule(), BudgetLimitRule()]
        soft_rules = [PreferredTimeRule(), QualityRequirementRule()]
        
        lval("Hard Rules", len(hard_rules))
        lval("Soft Rules", len(soft_rules))
        
        # Test cases
        log("\n--- Test Cases ---")
        
        test_cases = [
            {
                "name": "PASS_ALL",
                "params": {"security_level": 4, "cost": 200, "estimated_hours": 6, "min_quality": 0.8},
                "desc": "Все правила пройдены"
            },
            {
                "name": "FAIL_SECURITY",
                "params": {"security_level": 2, "cost": 200, "estimated_hours": 6, "min_quality": 0.8},
                "desc": "Недостаточный уровень безопасности"
            },
            {
                "name": "FAIL_BUDGET",
                "params": {"security_level": 4, "cost": 600, "estimated_hours": 6, "min_quality": 0.8},
                "desc": "Превышен бюджет"
            },
            {
                "name": "SOFT_VIOLATION_TIME",
                "params": {"security_level": 4, "cost": 200, "estimated_hours": 12, "min_quality": 0.8},
                "desc": "Мягкое нарушение: долгое время"
            },
            {
                "name": "SOFT_VIOLATION_QUALITY",
                "params": {"security_level": 4, "cost": 200, "estimated_hours": 6, "min_quality": 0.95},
                "desc": "Мягкое нарушение: высокие требования к качеству"
            }
        ]
        
        results = []
        
        for tc in test_cases:
            log(f"\n{'─'*50}")
            log(f"Test Case: {tc['name']}")
            log(f"Description: {tc['desc']}")
            
            action = Action(name=tc["name"], params=tc["params"])
            
            gamma_hard = check_gamma_hard(action, hard_rules)
            gamma_soft = check_gamma_soft(action, soft_rules)
            
            lval("γ_hard", gamma_hard, "PASS" if gamma_hard == 0.0 else "FAIL (-inf)")
            lval("γ_soft", gamma_soft, f"{gamma_soft:.2f}" if gamma_soft > 0 else "No penalty")
            
            passed = gamma_hard == 0.0
            decision = "APPROVED" if passed else "REJECTED"
            
            if gamma_hard == 0.0 and gamma_soft > 0:
                decision = f"APPROVED_WITH_PENALTY ({gamma_soft:.2f})"
            
            lval("Decision", decision)
            
            results.append({
                "name": tc["name"],
                "gamma_hard": gamma_hard,
                "gamma_soft": gamma_soft,
                "decision": decision
            })
        
        # Summary
        log("\n" + "="*60)
        log("COMPLIANCE SUMMARY")
        log("="*60)
        
        E2ETestLogger.log_table(
            headers=["Case", "γ_hard", "γ_soft", "Decision"],
            rows=[
                [r["name"], 
                 "PASS" if r["gamma_hard"] == 0 else "FAIL",
                 f"{r['gamma_soft']:.2f}" if r["gamma_soft"] > 0 else "0",
                 r["decision"]]
                for r in results
            ]
        )
        
        E2ETestLogger.end_test(passed=True)


# =============================================================================
# E2E PATH 11: VERIFIER
# =============================================================================

class TestE2EVerifierVerbose:
    """
    E2E-11: Тестирование верификатора.
    """
    
    def test_verifier_assessment_verbose(self):
        """Подробный тест оценки качества верификатором."""
        E2ETestLogger.start_test("verifier_assessment_verbose")
        log = E2ETestLogger.log
        lval = E2ETestLogger.log_value
        
        from space1.verifier.core import Verifier, TechnicalCritic, BriefComplianceCritic
        from space1.models.task import Task, TaskStatus, TaskPriority
        from space1.utility import compute_quality
        
        log("="*60)
        log("VERIFIER — QUALITY ASSESSMENT")
        log("="*60)
        
        # Create verifier
        verifier = Verifier()
        lval("Verifier Created", "Yes")
        lval("Critics", len(verifier.critics))
        
        for critic in verifier.critics:
            lval("Critic", critic.__class__.__name__)
        
        # Create task
        log("\n--- Task Creation ---")
        
        task = Task(
            id="verify-test-task",
            title="API Integration Deliverable",
            description="Completed API integration",
            priority=TaskPriority.HIGH
        )
        
        lval("Task ID", task.id)
        lval("Task Title", task.title)
        
        # Simulate deliverable
        log("\n--- Deliverable Assessment ---")
        
        deliverable = {
            "code_quality": 0.85,
            "test_coverage": 0.75,
            "documentation": 0.90,
            "api_response_time": 150,  # ms
            "error_rate": 0.02,  # 2%
            "security_scan": "passed",
            "performance_score": 0.88
        }
        
        for key, value in deliverable.items():
            unit = "ms" if "time" in key else "%" if "rate" in key else "" if isinstance(value, str) else ""
            lval(key, f"{value}{unit}")
        
        # Calculate overall quality
        log("\n--- Quality Calculation ---")
        
        completeness = (deliverable["code_quality"] + deliverable["test_coverage"] + deliverable["documentation"]) / 3
        accuracy = 1 - deliverable["error_rate"]
        fulfillment = deliverable["performance_score"]
        consistency = deliverable["code_quality"]
        
        lval("Completeness (avg)", f"{completeness:.3f}")
        lval("Accuracy (1 - error_rate)", f"{accuracy:.3f}")
        lval("Fulfillment (performance)", f"{fulfillment:.3f}")
        lval("Consistency (code_quality)", f"{consistency:.3f}")
        
        q_score = compute_quality(completeness, accuracy, fulfillment, consistency)
        lval("Q (Overall Quality)", f"{q_score:.4f}", ValueDescribers.describe_quality(q_score))
        
        # Verdict
        log("\n--- Verdict ---")
        
        q_threshold = 0.5
        passed = q_score >= q_threshold
        
        lval("Quality Threshold", q_threshold)
        lval("Passed", passed)
        lval("Verdict", "APPROVED" if passed else "REJECTED")
        
        E2ETestLogger.end_test(passed=passed)


# =============================================================================
# E2E PATH 12: COLD START & EXPLORATION
# =============================================================================

class TestE2EColdStartVerbose:
    """
    E2E-12: Холодный старт и исследование.
    """
    
    def test_cold_start_verbose(self):
        """Подробный тест холодного старта агента."""
        E2ETestLogger.start_test("cold_start_verbose")
        log = E2ETestLogger.log
        lval = E2ETestLogger.log_value
        
        from space1.cold_start.core import ColdStartState
        from space1.models.task import Task, TaskPriority
        from space1.models.agents import Agent, AgentCapabilities, AgentMetrics
        
        log("="*60)
        log("COLD START — EXPLORATION VS EXPLOITATION")
        log("="*60)
        
        # Create cold start state
        state = ColdStartState()
        lval("ColdStartState Created", "Yes")
        
        # Initial state: new agent with no history
        log("\n--- Agent Initial State ---")
        
        agent = Agent(
            id="cold-start-agent",
            name="New Agent",
            capabilities=AgentCapabilities(
                n_completed_tasks=0,
                current_knowledge=0.0
            ),
            metrics=AgentMetrics(
                balance=100.0,
                success_rate=0.0,
            )
        )
        
        lval("Agent ID", agent.id)
        lval("N Completed Tasks", agent.capabilities.n_completed_tasks)
        lval("Success Rate", f"{agent.metrics.success_rate:.2%}")
        lval("Current Knowledge", f"{agent.capabilities.current_knowledge:.2f}")
        
        # Task options for exploration
        log("\n--- Task Options (Exploration) ---")
        
        tasks = [
            Task(id="easy", title="Simple Fix", priority=TaskPriority.LOW, estimated_hours=1),
            Task(id="medium", title="Feature Implementation", priority=TaskPriority.MEDIUM, estimated_hours=4),
            Task(id="hard", title="System Refactoring", priority=TaskPriority.HIGH, estimated_hours=12),
        ]
        
        E2ETestLogger.log_table(
            headers=["ID", "Title", "Priority", "Est. Hours"],
            rows=[[t.id, t.title, t.priority.name, t.estimated_hours] for t in tasks]
        )
        
        # UCB1 formula for exploration
        log("\n--- UCB1 Selection (Exploration Phase) ---")
        
        # With no history, UCB1 should favor exploration
        c = 1.41  # Exploration constant
        n = agent.capabilities.n_completed_tasks
        avg_reward = 0.5  # Prior estimate
        
        for task in tasks:
            n_i = 0  # No history for any task
            
            ucb = avg_reward + c * ((2 * (n + 1) / max(n_i, 1)) ** 0.5) if n_i > 0 else float('inf')
            
            lval(f"UCB1({task.id})", f"={ucb:.2f}" if ucb != float('inf') else "=∞ (first visit)")
        
        # Simulate task completion
        log("\n--- Simulate Task Completion ---")
        
        task_quality = 0.7
        task_reward = 50.0
        
        agent.capabilities.n_completed_tasks += 1
        agent.metrics.success_rate = task_quality
        agent.metrics.balance += task_reward
        agent.capabilities.current_knowledge += 0.1
        
        lval("N Completed Tasks", agent.capabilities.n_completed_tasks)
        lval("Success Rate", f"{agent.metrics.success_rate:.2%}")
        lval("Balance", f"{agent.metrics.balance:.2f} USD")
        lval("Knowledge", f"{agent.capabilities.current_knowledge:.2f}")
        
        # === ASSERTIONS ===
        assert agent.capabilities.n_completed_tasks == 1, f"n_completed={agent.capabilities.n_completed_tasks}, expected 1 (only 1 task simulated)"
        assert agent.metrics.balance > 100.0, f"balance={agent.metrics.balance}, expected >100"
        assert agent.metrics.success_rate == 0.7, f"success_rate={agent.metrics.success_rate}, expected 0.7"
        assert agent.capabilities.current_knowledge > 0.0, f"knowledge={agent.capabilities.current_knowledge}, expected >0"

        E2ETestLogger.end_test(passed=True)


# =============================================================================
# E2E PATH 13: COST TRACKING
# =============================================================================

class TestE2ECostTrackingVerbose:
    """
    E2E-13: Отслеживание стоимости.
    """
    
    def test_cost_tracking_verbose(self):
        """Подробный тест трекера стоимости."""
        E2ETestLogger.start_test("cost_tracking_verbose")
        log = E2ETestLogger.log
        lval = E2ETestLogger.log_value
        
        from space1.cost.token_tracker import TokenCostTracker
        
        log("="*60)
        log("COST TRACKING — TOKEN CONSUMPTION")
        log("="*60)
        
        tracker = TokenCostTracker()
        lval("TokenCostTracker Created", "Yes")
        
        # Simulate token usage
        log("\n--- Token Usage Simulation ---")
        
        operations = [
            {"model": "gpt-4", "prompt_tokens": 500, "completion_tokens": 200, "cost_per_1k": 0.03},
            {"model": "gpt-4", "prompt_tokens": 800, "completion_tokens": 400, "cost_per_1k": 0.03},
            {"model": "gpt-3.5", "prompt_tokens": 1000, "completion_tokens": 500, "cost_per_1k": 0.002},
        ]
        
        for i, op in enumerate(operations):
            total_tokens = op["prompt_tokens"] + op["completion_tokens"]
            cost = (total_tokens / 1000) * op["cost_per_1k"]
            
            lval(f"Operation {i+1}", "")
            lval("  Model", op["model"])
            lval("  Prompt Tokens", op["prompt_tokens"])
            lval("  Completion Tokens", op["completion_tokens"])
            lval("  Total Tokens", total_tokens)
            lval("  Cost", f"${cost:.4f}")
            
            tracker.record(
                model=op["model"],
                input_tokens=op["prompt_tokens"],
                output_tokens=op["completion_tokens"]
            )
        
        # Summary
        log("\n--- Cost Summary ---")
        
        total_cost = tracker.get_total_cost()
        by_model = tracker.get_by_model()
        
        lval("Total Cost", f"${total_cost:.4f}")
        lval("By Model", by_model)
        
        # === ASSERTIONS ===
        assert total_cost > 0, f"total_cost={total_cost}, expected >0"
        assert isinstance(by_model, dict), f"by_model type={type(by_model)}, expected dict"
        assert len(by_model) > 0, "by_model is empty"

        E2ETestLogger.end_test(passed=True)


# =============================================================================
# RUN ALL TESTS
# =============================================================================

if __name__ == "__main__":
    print("="*80)
    print("SPACE1 E2E TESTS: FACTORS, COMPLIANCE, VERIFIER")
    print("="*80)
    
    tests = [
        TestE2EFactorAggregationVerbose(),
        TestE2EComplianceRulesVerbose(),
        TestE2EVerifierVerbose(),
        TestE2EColdStartVerbose(),
        TestE2ECostTrackingVerbose(),
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
