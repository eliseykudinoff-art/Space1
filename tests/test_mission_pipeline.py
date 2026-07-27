"""
Tests for Mission → Compliance → Utility → Execution Pipeline

Reference: DEVELOPMENT_PLAN.md - G16
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
from space1.compliance.core import GammaVeto, Action, Rule, MaxCostRule, BlockedActionsRule, ComplianceError


class TestMission:
    """Test Mission model per canonical spec (02_MATHEMATICAL_CORE.md §IV.12)."""
    
    def test_create_mission(self):
        """Test creating a mission."""
        mission = create_mission(
            name="Test Mission",
            max_budget=50.0,
            max_hours=8.0,
        )
        
        assert mission.name == "Test Mission"
        assert mission.max_budget == 50.0
        assert mission.max_time == timedelta(hours=8.0)
        assert mission.mission_type.value == "maintenance"
    
    def test_mission_calibrate(self):
        """Test mission calibration per §IV.12."""
        mission = create_mission(name="Test", max_budget=100.0, max_hours=24.0)
        
        agent_state = {"balance": 500.0, "stress_level": 0.3, "phi_historical": 0.7}
        calibrated = mission.calibrate(agent_state)
        
        assert hasattr(calibrated, 'lambda_phi')
        assert hasattr(calibrated, 'lambda_upsilon')
        assert hasattr(calibrated, 'lambda_omega')
        assert hasattr(calibrated, 'lambda_quality')
        assert hasattr(calibrated, 'psi_max')


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
        
        # BUG-004 FIX: ComplianceError now raised instead of swallowing
        with pytest.raises(ComplianceError, match="vetoed"):
            ctx = processor.execute(action)


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


def test_execute_best_ranks_compliant_actions():
    """Test candidate actions are vetoed before utility ranking."""
    mission = create_mission(name="Test Mission")
    processor = MissionProcessor()
    processor.setup_mission(mission)
    processor.add_compliance_rule(BlockedActionsRule(blocked_names=["blocked"]))

    ctx = processor.execute_best([
        Action(name="expensive", resource_cost=30.0),
        Action(name="cheap", resource_cost=1.0),
        Action(name="blocked", resource_cost=0.0),
    ])

    assert ctx.selected_action.name == "cheap"
    assert ctx.stage_results[PipelineStage.UTILITY]["optimization"] == "risk_adjusted"
    ranked_names = [item["action"] for item in ctx.stage_results[PipelineStage.UTILITY]["ranked_actions"]]
    assert "blocked" not in ranked_names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
