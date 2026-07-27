"""
Tests for Pipeline, Memory & Trigger Integration (Phase 3 Integration)
"""

import pytest
from datetime import datetime, timedelta

from space1.mission import (
    Mission,
    ExecutionContext,
    MissionProcessor,
    PipelineStage,
    create_mission,
)
from space1.compliance.core import Action, BlockedActionsRule
from space1.models import Task, create_task, TaskPriority, TaskStatus


def test_mission_processor_phase3_integration():
    """Test that MissionProcessor properly integrates Operational Memory, Strategic Memory, and Triggers."""
    mission = create_mission(name="Integration Mission", max_budget=200.0, max_hours=12.0)
    processor = MissionProcessor()
    processor.setup_mission(mission)
    
    # Track triggered events
    fired_events = []
    
    from space1.triggers import EventTrigger, ThresholdTrigger
    
    processor.triggers.register(EventTrigger(
        name="on_success",
        event_name="execution_success",
        callback=lambda e, p: fired_events.append(e)
    ))
    
    processor.triggers.register(ThresholdTrigger(
        name="on_high_risk",
        metric_name="risk",
        threshold=0.5,
        operator="gt",
        callback=lambda m, v: fired_events.append("high_risk")
    ))
    
    # Create task with high uncertainty (results in higher risk PSI)
    task = Task(
        id="t-integration",
        title="High Uncertainty Website Design",
        priority=TaskPriority.HIGH,
        estimated_hours=4.0,
        metadata={"uncertainty": 0.9, "novelty": 0.8}
    )
    
    action = Action(name="deploy_server", resource_cost=20.0)
    
    # Execute through pipeline
    ctx = processor.execute(action, context={"task": task})
    
    # Check that execution succeeded and errors are empty
    assert len(ctx.errors) == 0
    assert ctx.execution_result["status"] == "executed"
    
    # 1. Operational memory check: should have been consolidated and wiped
    assert processor.op_mem.get("task_id") is None
    
    # 2. Strategic memory check: ConsolidationGate should have saved the completed run
    experiences = processor.strategic_mem.get_experiences()
    assert len(experiences) == 1
    exp = experiences[0]
    assert exp.task_id == "t-integration"
    assert exp.status == "completed"
    assert exp.revenue > 0.0  # phi profit
    assert exp.risk > 0.4     # psi should be elevated due to uncertainty
    
    # 3. Triggers check: EventTrigger and ThresholdTrigger should have fired based on risk and completion
    assert "execution_success" in fired_events
    if exp.risk > 0.5:
        assert "high_risk" in fired_events


def test_mission_processor_veto_trigger():
    """Test that EventTrigger is fired when a compliance check failure occurs."""
    mission = create_mission(name="Veto Mission")
    processor = MissionProcessor()
    processor.setup_mission(mission)
    
    processor.add_compliance_rule(BlockedActionsRule(blocked_names=["blocked_action"]))
    
    from space1.triggers import EventTrigger
    from space1.compliance.core import ComplianceError
    
    veto_triggered = []
    processor.triggers.register(EventTrigger(
        name="on_veto",
        event_name="compliance_veto",
        callback=lambda e, p: veto_triggered.append(True)
    ))
    
    action = Action(name="blocked_action")
    
    # BUG-004 FIX: ComplianceError now raised, but trigger should still fire
    with pytest.raises(ComplianceError, match="vetoed"):
        processor.execute(action)
    
    assert len(veto_triggered) == 1, "Trigger should fire before exception"
