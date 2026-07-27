"""
Tests for Phase 6 Production and G15/G17/G3/G10/G13/G19/G21 Integration
"""

import pytest
import asyncio
from datetime import timedelta
import os

from space1 import (
    GammaVeto,
    Action,
    MaxCostRule,
    BlockedActionsRule,
    StrategicMemory,
    StrategicExperience,
    ParameterCalibrator,
    HomeostaticRegulator,
    ScoutAgent,
    WorkerAgent,
    FinanceAgent,
)
from space1.models import create_agent
from space1.models.task import create_task
from space1.mission import create_mission, MissionProcessor
from space1.mission.core import TaskDecomposer
from space1.metrics.monitoring import SystemMonitor, AlertLevel


class TestPhase6Production:
    """Test Suite for Space1 Phase 6 Production-ready features."""

    def test_graded_compliance_penalties(self):
        """Test that evaluate_graded properly accumulates rule severity penalties."""
        veto = GammaVeto(lambda_gamma=2.0)
        
        veto.register(MaxCostRule(max_cost=10.0))
        veto.register(BlockedActionsRule(blocked_names=["sudo"]))
        
        action_ok = Action(name="read_file", resource_cost=5.0)
        assert veto.evaluate_graded(action_ok) == 0.0
        assert veto.apply_graded_utility(100.0, action_ok) == 100.0
        
        action_over_budget = Action(name="read_file", resource_cost=15.0)
        assert veto.evaluate_graded(action_over_budget) == 0.5
        assert veto.apply_graded_utility(100.0, action_over_budget) == 99.0
        
        action_sudo = Action(name="sudo", resource_cost=5.0)
        assert veto.evaluate_graded(action_sudo) == float('inf')
        assert veto.apply_graded_utility(100.0, action_sudo) == float('-inf')

    def test_parameter_calibrator_recommends_corrections(self):
        """Test ParameterCalibrator analyzes strategic logs to output tuning recommendations."""
        memory = StrategicMemory()
        calibrator = ParameterCalibrator(memory)
        
        res_empty = calibrator.calibrate_constants()
        assert res_empty["status"] == "No data available"
        
        memory.add_experience(StrategicExperience(
            task_id="t-1", title="Web dev", status="completed", strategy="Docker",
            revenue=100.0, cost=10.0, time_spent=2.0, quality=0.9, risk=0.1
        ))
        memory.add_experience(StrategicExperience(
            task_id="t-2", title="Web API", status="completed", strategy="Docker",
            revenue=120.0, cost=10.0, time_spent=2.0, quality=0.85, risk=0.1
        ))
        memory.add_experience(StrategicExperience(
            task_id="t-3", title="Web Mobile", status="completed", strategy="Docker",
            revenue=80.0, cost=5.0, time_spent=2.0, quality=0.95, risk=0.1
        ))
        
        memory.add_experience(StrategicExperience(
            task_id="t-4", title="Risky crypto", status="failed", strategy="Trading",
            revenue=0.0, cost=20.0, time_spent=1.0, quality=0.1, risk=0.8
        ))
        memory.add_experience(StrategicExperience(
            task_id="t-5", title="Risky launch", status="failed", strategy="Trading",
            revenue=0.0, cost=10.0, time_spent=1.0, quality=0.1, risk=0.7
        ))
        
        res = calibrator.calibrate_constants()
        assert res["status"] == "Success"
        
        recs = res["recommendations"]
        assert "psi_max" in recs
        assert "phi_r_alpha_rep" in recs
        
        # Test saving calibrated weights back to config file
        temp_config = "tests/temp_weights.yaml"
        with open(temp_config, 'w') as f:
            f.write("llm:\n  quality_weight: 0.25\nphi_r_alpha_rep: 0.3\npsi_max: 1.0\n")
            
        try:
            assert calibrator.save_calibrated_weights(res, temp_config) is True
            # Read and verify updated properties
            with open(temp_config, 'r') as f:
                saved_content = f.read()
            assert "phi_r_alpha_rep: 0.45" in saved_content
            assert "psi_max: 0.75" in saved_content
        finally:
            if os.path.exists(temp_config):
                os.remove(temp_config)

    def test_task_complexity_auto_classification(self):
        """Test that tasks are auto-classified upon instantiation based on title and description."""
        task_normal = create_task(title="implement user profile api")
        assert "complexity" in task_normal.metadata
        assert task_normal.metadata["complexity"] == 0.5  # default
        assert task_normal.metadata["routing_decision"] == "AUTO_ASSIGN"
        
        # Typos are trivial
        task_low = create_task(title="fix typo in readme docs")
        assert task_low.metadata["complexity"] < 0.4
        assert task_low.metadata["routing_decision"] == "AUTO_ASSIGN"
        
        # Refactors or leaks are complex
        task_high = create_task(title="refactor slow memory leak error in core server")
        assert task_high.metadata["complexity"] > 0.6
        assert task_high.metadata["routing_decision"] in ("HUMAN_REVIEW", "ESCALATE")

    def test_task_decomposer_atomic_subtasks(self):
        """Test task decomposer splits complex tasks into directed Action chains with quality score."""
        decomposer = TaskDecomposer()
        
        # Test authentications task
        actions, quality = decomposer.decompose("Build JWT user login and registration auth endpoints")
        assert len(actions) == 3
        assert actions[0].name in ("setup_database", "security_audit")
        assert actions[1].name in ("implement_register", "implement_auth")
        assert actions[2].name in ("implement_login", "verify_encryption")
        assert 0.0 <= quality <= 1.0
        
        # Test deployment task
        actions_d, _ = decomposer.decompose("Deploy the core web server to AWS cloud")
        assert len(actions_d) == 3
        assert actions_d[0].name in ("write_dockerfile", "configure_infra")
        assert actions_d[1].name in ("setup_ci_cd", "provision_cloud")

    def test_system_monitoring_limit_alerts(self):
        """Test SystemMonitor threshold checks and alert subscriptions."""
        monitor = SystemMonitor()
        alerts_fired = []
        
        def listener(alert):
            alerts_fired.append(alert)
            
        monitor.subscribe(listener)
        
        # Record normal budget
        monitor.record("budget_health", 50.0)
        assert len(alerts_fired) == 0
        
        # Record critical low budget (warning threshold is 20.0, critical is 5.0)
        monitor.record("budget_health", 3.0)
        assert len(alerts_fired) == 1
        assert alerts_fired[0].level == AlertLevel.CRITICAL
        assert "budget_health" in alerts_fired[0].message
        
        # Record high stress level
        monitor.record("stress_level", 0.95)
        assert len(alerts_fired) == 2
        assert alerts_fired[1].level == AlertLevel.CRITICAL

    def test_pid_hysteresis_oscillations_prevention(self):
        """Test that HomeostaticRegulator implements hysteresis buffering."""
        regulator = HomeostaticRegulator()
        # Set kd and ki to 0 to prevent derivative kick / integral windup under rapid successive updates
        for metric in ["balance", "success_rate", "stress_level", "utilization", "quality", "knowledge", "reputation"]:
            pid = regulator._get_pid(metric)
            pid.kd = 0.0
            pid.ki = 0.0
        
        # Set normal metrics to begin
        metrics_ok = {
            "balance": 20.0,
            "success_rate": 0.8,
            "stress_level": 0.4,
            "utilization": 0.5,
            "quality": 0.8,
            "knowledge": 0.8,
            "reputation": 0.8,
        }
        regulator.update_all(metrics_ok)
        assert regulator.get_mode() == "normal"
        
        # 1. Enter survival mode with critical balance = 2.0 (pressure breaches 0.3)
        metrics_bad = dict(metrics_ok, balance=2.0)
        regulator.update_all(metrics_bad)
        assert regulator.get_mode() == "survival"
        
        # 2. Hysteresis check: If balance improves slightly to 5.0 (still pressure > 0.15), we stay in survival
        metrics_slightly_better = dict(metrics_ok, balance=5.0)
        regulator.update_all(metrics_slightly_better)
        assert regulator.get_mode() == "survival"  # hysteresis prevents immediate transition to normal!
        
        # 3. Only transition back to normal if pressure fully clears (balance = 20.0)
        regulator.update_all(metrics_ok)
        assert regulator.get_mode() == "normal"

    def test_async_specialist_agents_and_processor(self):
        """Test asynchronous execution pathways in agents and pipeline processor using asyncio.run."""
        async def run_test():
            core_agent = create_agent("AsyncAgent")
            worker = WorkerAgent(core_agent)
            
            task = create_task("Async PyTorch Training")
            task.status = "in_progress"
            
            # Run async role
            result = await worker.run_role_async(task)
            assert result["status"] == "completed"
            
            # Run async processor pipeline
            mission = create_mission(name="Async Mission")
            processor = MissionProcessor()
            processor.setup_mission(mission)
            
            action = Action(name="setup_server")
            ctx = await processor.execute_async(action, context={"task": task})
            assert len(ctx.errors) == 0
            assert ctx.execution_result["status"] == "executed"

        asyncio.run(run_test())
