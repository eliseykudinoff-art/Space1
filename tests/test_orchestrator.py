"""
Tests for Phase 4 Orchestrator (G2 Impulse to Chain, G10 Signal-to-Context Synthesizer, G19 Weight Calibration)
"""

import pytest
from datetime import timedelta

from space1.memory import StrategicMemory, StrategicExperience
from space1.orchestrator import (
    SignalToContextSynthesizer,
    HomeostaticUtilityModulator,
    WeightCalibrator,
)
from space1.utility.control import HomeostaticRegulator
from space1.models import create_task


class TestOrchestratorPhase4:
    """Test Suite for Space1 Orchestrator Subsystem (Phase 4)."""

    def test_signal_to_context_synthesizer_survival(self):
        """Test structured prompt guide generation under survival pressure."""
        # Setup memory and record a lesson for balance
        memory = StrategicMemory()
        memory.add_experience(StrategicExperience(
            task_id="t-prev",
            title="balance task",
            status="completed",
            strategy="Drastically reduce api budget and execute offline tasks",
            revenue=10.0,
            cost=1.0,
            time_spent=1.0,
            quality=0.8,
            risk=0.1
        ))
        
        synthesizer = SignalToContextSynthesizer(memory=memory)
        
        # Balance is at critical low 2.0 (threshold is 10.0) -> triggers survival mode
        metrics = {
            "balance": 2.0,
            "success_rate": 0.8,
            "stress_level": 0.4,  # stress at target (0.4) to avoid artificial survival stress error
            "utilization": 0.1,
            "quality": 0.9,
            "knowledge": 0.8,
            "reputation": 0.8,
        }
        
        task = create_task(title="High-cost deployment task")
        context = synthesizer.synthesize(metrics, task=task)
        
        assert "Mode: SURVIVAL" in context.situation
        assert context.recommended_tone == "CONSERVATIVE / SURVIVAL ONLY"
        assert "balance" in context.priority_variables
        
        # Verify that relevant memory lesson was successfully recalled
        assert "Relevant Strategic Memories" in context.prompt
        assert "Drastically reduce api budget" in context.prompt

    def test_signal_to_context_synthesizer_growth(self):
        """Test prompt synthesis guidelines in growth mode."""
        memory = StrategicMemory()
        synthesizer = SignalToContextSynthesizer(memory=memory)
        
        # Balance is high (100.0), success is high (0.9), stress is optimal (0.4), and knowledge is high (0.9) -> triggers growth mode
        metrics = {
            "balance": 100.0,
            "success_rate": 0.9,
            "stress_level": 0.4,
            "utilization": 0.1,
            "quality": 0.9,
            "knowledge": 0.9,
            "reputation": 0.9,
        }
        
        context = synthesizer.synthesize(metrics)
        assert "Mode: GROWTH" in context.situation
        assert context.recommended_tone == "EXPLORATIVE / LEARNING OR REPUTATION"
        assert "Minimize tool cost" not in context.prompt  # Not in survival guidelines

    def test_homeostatic_utility_modulation(self):
        """Test decision modulation curve across various homeostatic zones."""
        modulator = HomeostaticUtilityModulator()
        
        # Zone 1: Complacency / Too low pressure (total sum of positive pressures = 0.1)
        # f = 0.5 + 1.0 * total = 0.6
        p_low = {"balance": 0.05, "success_rate": 0.05}
        val_low = modulator.modulate(base_utility=10.0, pressures=p_low)
        assert abs(val_low - 6.0) < 1e-3
        
        # Zone 2: Optimal pressure (total = 0.6)
        # f = 1.0
        p_optimal = {"balance": 0.6, "success_rate": 0.0}
        val_opt = modulator.modulate(base_utility=10.0, pressures=p_optimal)
        assert val_opt == 10.0
        
        # Zone 3: Stress zone (total = 1.5)
        # f = 1.0 - 0.3 * (1.5 - 1.0) = 0.85
        p_stress = {"balance": 1.5}
        val_stress = modulator.modulate(base_utility=10.0, pressures=p_stress)
        assert abs(val_stress - 8.5) < 1e-3
        
        # Zone 4: Critical zone (total = 2.5)
        # f = 0.1
        p_critical = {"balance": 2.5}
        val_critical = modulator.modulate(base_utility=10.0, pressures=p_critical)
        assert abs(val_critical - 1.0) < 1e-3

    def test_weight_calibrator_survival_adaptation(self):
        """Test dynamic calibration shifts priority towards profit weight under financial distress."""
        calibrator = WeightCalibrator()
        
        # Severe balance pressure (balance_p = 0.8)
        pressures = {
            "balance": 0.8,
            "success_rate": 0.0,
            "stress_level": 0.0,
        }
        
        calibrated = calibrator.calibrate(pressures)
        
        # Profit weight should have increased significantly compared to default base 0.30
        assert calibrated["profit_weight"] > 0.40
        # Evolution weight should have been compressed to prioritize near-term gains
        assert calibrated["evolution_weight"] < 0.15

    def test_weight_calibrator_quality_adaptation(self):
        """Test dynamic calibration shifts priority towards quality under high failure rates."""
        calibrator = WeightCalibrator()
        
        # Severe success_rate and stress pressure (e.g. success_p = 0.7)
        pressures = {
            "balance": 0.0,
            "success_rate": 0.7,
            "stress_level": 0.0,
        }
        
        calibrated = calibrator.calibrate(pressures)
        
        # Quality weight should have increased compared to default base 0.25
        assert calibrated["quality_weight"] > 0.35
        # Total sum of normalized weights must always remain 1.0
        assert abs(sum(calibrated.values()) - 1.0) < 1e-9

    def test_circuit_breaker_state_transitions(self):
        """Test CircuitBreaker state transitions: CLOSED -> OPEN -> HALF-OPEN -> CLOSED."""
        from space1.orchestrator.core import CircuitBreaker, CircuitBreakerOpenException
        import time

        # Cooldown of 0.1s for fast test, theta_fail=0.99 to avoid early trip
        cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=0.1, theta_fail=0.99)
        assert cb.state == "CLOSED"

        # 1st failure - stays CLOSED
        cb.record_failure()
        assert cb.state == "CLOSED"

        # 2nd failure - trips to OPEN
        cb.record_failure()
        assert cb.state == "OPEN"

        # Call in OPEN state should fail
        with pytest.raises(CircuitBreakerOpenException):
            cb.before_call()

        # Wait for cooldown
        time.sleep(0.12)
        
        # Next call transitions state to HALF_OPEN
        cb.before_call()
        assert cb.state == "HALF_OPEN"

        # Need 3 consecutive successes in HALF_OPEN to close (stabilization)
        cb.record_success()
        assert cb.state == "HALF_OPEN"
        cb.record_success()
        assert cb.state == "HALF_OPEN"
        cb.record_success()
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0

    def test_dynamic_decomposer_contextual_rules(self):
        """Test contextual custom Action plans generated by TaskDecomposer."""
        from space1.mission.core import TaskDecomposer
        decomposer = TaskDecomposer()

        # Overlapping keywords: "Deploy" + "JWT" → security + deploy categories combined
        t_auth = create_task(title="Deploy JWT User Login Module")
        auth_plan, _ = decomposer.decompose(t_auth)
        assert len(auth_plan) == 6  # 3 security + 3 deploy actions
        assert any("security" in action.name for action in auth_plan)
        assert any("auth" in action.name for action in auth_plan)
        assert any("infra" in action.name or "deploy" in action.name for action in auth_plan)

        # Cloud/AWS keywords
        t_cloud = create_task(title="Provision Kubernetes cluster on AWS Cloud")
        cloud_plan, _ = decomposer.decompose(t_cloud)
        assert len(cloud_plan) == 3
        assert any("configure_infra" in action.name or "write_dockerfile" in action.name for action in cloud_plan)
        assert any("provision_cloud" in action.name or "deploy_cloud" in action.name for action in cloud_plan)

        # Fallback standard keyword task
        t_normal = create_task(title="Write some general text documentation")
        normal_plan, _ = decomposer.decompose(t_normal)
        assert len(normal_plan) == 3
        assert any("setup" in action.name or "analyze" in action.name for action in normal_plan)
