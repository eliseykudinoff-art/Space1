"""
Tests for Agent and Context models

Reference: DEVELOPMENT_PLAN.md - G11
"""

import pytest
from datetime import datetime, timedelta

from space1.models import (
    Agent,
    AgentStatus,
    AgentCapabilities,
    AgentMetrics,
    AgentContext,
    create_agent,
    Task,
    TaskPriority,
)


class TestAgent:
    def test_create_agent(self):
        agent = create_agent("Test Agent")
        assert agent.name == "Test Agent"
        assert agent.id is not None
        assert agent.status == AgentStatus.IDLE
    
    def test_agent_default_capabilities(self):
        agent = create_agent("Test Agent")
        caps = agent.capabilities
        assert caps.llm_name == "unknown"
        assert caps.llm_quality == 0.7
        assert caps.n_completed_tasks == 0
    
    def test_agent_default_metrics(self):
        agent = create_agent("Test Agent")
        metrics = agent.metrics
        assert metrics.balance == 0.0
        assert metrics.rating == 0.5
        assert metrics.success_rate == 0.3
    
    def test_agent_to_dict(self):
        agent = create_agent("Test Agent")
        d = agent.to_dict()
        assert d["name"] == "Test Agent"
        assert d["status"] == "idle"
        assert "capabilities" in d
        assert "metrics" in d


class TestAgentCapabilities:
    def test_to_dict(self):
        caps = AgentCapabilities(
            llm_name="gpt-4o-mini",
            llm_quality=0.9,
            has_browser=True,
        )
        d = caps.to_dict()
        assert d["llm_name"] == "gpt-4o-mini"
        assert d["capabilities"]["llm_quality"] == 0.9
        assert d["tools"]["has_browser"] == True


class TestAgentMetrics:
    def test_to_dict(self):
        metrics = AgentMetrics(
            balance=100.0,
            reputation_vector={"tech": 0.9, "econ": 0.9, "comm": 0.9, "rel": 0.9, "sec": 0.9, "domain": 0.9},
            success_rate=0.85,
        )
        d = metrics.to_dict()
        assert d["balance"] == 100.0
        assert d["rating"] == 0.9  # scalar from reputation_vector


class TestAgentContext:
    def test_create_context(self):
        agent = create_agent("Test Agent")
        ctx = AgentContext(agent=agent, available_budget=50.0)
        
        assert ctx.agent == agent
        assert ctx.available_budget == 50.0
        assert ctx.available_time == 24.0
    
    def test_context_with_mission(self):
        agent = create_agent("Test Agent")
        ctx = AgentContext(
            agent=agent,
            mission_id="mission-123",
            mission_params={"priority": "high"},
        )
        
        assert ctx.mission_id == "mission-123"
        assert ctx.mission_params["priority"] == "high"
    
    def test_context_to_dict(self):
        agent = create_agent("Test Agent")
        ctx = AgentContext(agent=agent)
        d = ctx.to_dict()
        
        assert d["agent_id"] == agent.id
        assert "created_at" in d


class TestIntegration:
    def test_agent_with_task(self):
        """Test that agent can work with tasks."""
        agent = create_agent("Worker")
        
        # Simulate task assignment
        task = Task(
            id="task-1",
            title="Test Task",
            priority=TaskPriority.HIGH,
        )
        
        # Agent picks up task
        agent.status = AgentStatus.WORKING
        agent.metrics.n_active_tasks += 1
        
        assert agent.status == AgentStatus.WORKING
        assert agent.metrics.n_active_tasks == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
