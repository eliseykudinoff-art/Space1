"""
Tests for Mission → Compliance → Utility → Execution Pipeline

Reference: DEVELOPMENT_PLAN.md - G16
"""

import pytest
from datetime import timedelta

from space1.mission import (
    ExecutionContext,
    MissionProcessor,
    PipelineStage,
    create_mission,
)
from space1.compliance.core import Action, BlockedActionsRule
from space1.models.agents import AgentContext, create_agent
from space1.models.task import Task


class TestMission:
    """Test Mission model."""
    
    def test_create_mission(self):
        """Test creating a mission."""
        mission = create_mission(
            name="Test Mission",
            goals=["Goal 1", "Goal 2"],
            max_budget=50.0,
            max_hours=8.0,
        )
        
        assert mission.name == "Test Mission"
        assert len(mission.goals) == 2
        assert mission.max_budget == 50.0
        assert mission.max_time == timedelta(hours=8.0)
    
    def test_mission_calibrate(self):
        """Test mission calibration."""
        mission = create_mission(name="Test", max_budget=100.0, max_hours=24.0)
        
        context = {"available_budget": 50.0, "urgency_multiplier": 2.0}
        calibrated = mission.calibrate(context)
        
        assert calibrated["budget"] == 50.0  # limited by available
        assert calibrated["priority"] == 2.0  # doubled by urgency
        assert "time_budget" in calibrated


class TestMissionProcessor:
    """Test MissionProcessor pipeline."""
    
    def test_pipeline_setup(self):
        """Test setting up mission processor."""
        mission = create_mission(name="Test Mission")
        processor = MissionProcessor()
        processor.setup_mission(mission)
        
        assert processor._mission is not None
        assert len(processor._stages) == 4
    
    def test_pipeline_stages_order(self):
        """Test pipeline executes in correct order."""
        processor = MissionProcessor()
        statuses = processor.get_pipeline_status()
        
        assert statuses[0]["stage"] == "mission"
        assert statuses[1]["stage"] == "compliance"
        assert statuses[2]["stage"] == "utility"
        assert statuses[3]["stage"] == "execution"
    
    def test_execute_action_success(self):
        """Test executing action through pipeline."""
        mission = create_mission(name="Test Mission")
        processor = MissionProcessor()
        processor.setup_mission(mission)
        
        action = Action(name="test_action", params={"value": 42})
        
        ctx = processor.execute(action)
        
        assert ctx.mission.name == "Test Mission"
        assert ctx.selected_action == action
        assert PipelineStage.MISSION in ctx.stage_results
        assert PipelineStage.COMPLIANCE in ctx.stage_results
        assert PipelineStage.EXECUTION in ctx.stage_results
        assert len(ctx.errors) == 0
    
    def test_execute_action_with_compliance_failure(self):
        """Test pipeline handles compliance failure."""
        mission = create_mission(name="Test Mission")
        processor = MissionProcessor()
        processor.setup_mission(mission)
        
        # Add rule that blocks "blocked_action"
        processor.add_compliance_rule(
            BlockedActionsRule(blocked_names=["blocked_action"])
        )
        
        action = Action(name="blocked_action")
        ctx = processor.execute(action)
        
        assert len(ctx.errors) > 0
        assert "failed compliance" in ctx.errors[0].lower()


class TestExecutionContext:
    """Test ExecutionContext."""
    
    def test_context_creation(self):
        """Test creating execution context."""
        mission = create_mission(name="Test Mission")
        ctx = ExecutionContext(mission=mission)
        
        assert ctx.mission == mission
        assert ctx.selected_action is None
        assert len(ctx.errors) == 0
        assert len(ctx.stage_results) == 0
    
    def test_context_adds_error(self):
        """Test context tracks errors."""
        mission = create_mission(name="Test Mission")
        ctx = ExecutionContext(mission=mission)
        
        ctx.errors.append("Test error")
        
        assert len(ctx.errors) == 1
        assert ctx.errors[0] == "Test error"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


def test_execute_decision_selects_best_compliant_candidate():
    mission = create_mission(name="Decision Mission", max_budget=100.0)
    processor = MissionProcessor()
    processor.setup_mission(mission)
    processor.add_compliance_rule(BlockedActionsRule(blocked_names=["blocked"]))

    agent_context = AgentContext(agent=create_agent("mission-agent"), available_budget=100.0)
    task = Task(id="mission-task", title="Mission decision", estimated_hours=2.0)
    actions = [
        Action(name="low", params={"revenue": 10.0, "cost": 1.0}),
        Action(name="blocked", params={"revenue": 1000.0, "cost": 1.0}),
        Action(name="high", params={"revenue": 100.0, "cost": 1.0}),
    ]

    ctx = processor.execute_decision(task, agent_context, actions)

    assert ctx.selected_action.name == "high"
    assert ctx.stage_results[PipelineStage.COMPLIANCE]["compliant_actions"] == ["low", "high"]
    assert ctx.stage_results[PipelineStage.UTILITY]["optimization"] == "risk_adjusted_utility"
    assert ctx.execution_result["status"] == "executed"
