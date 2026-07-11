"""Tests for Space1 utility functions."""

from datetime import datetime, timedelta

import space1
from space1.compliance.core import Action
from space1.cost import TokenCostTracker
from space1.metrics.tracker import MetricRegistry
from space1.models.agents import AgentContext, create_agent
from space1.models.task import Task
from space1.utility import (
    compute_phi,
    compute_psi,
    compute_quality,
    rank_actions,
    update_upsilon,
)


class TaskLike:
    revenue = 100.0
    estimated_hours = 2.0
    cost = 10.0


def test_compute_phi_public_api():
    assert space1.compute_phi(revenue=50.0, cost=10.0, time_hours=2.0) == 20.0


def test_compute_phi_from_task_like_object():
    assert compute_phi(TaskLike()) == 45.0


def test_compute_phi_includes_token_tracker_cost():
    tracker = TokenCostTracker()
    tracker.record("gpt-4o-mini", 1000, 500)

    result = compute_phi(revenue=1.0, cost=0.0, time_hours=1.0, token_tracker=tracker)

    assert abs(result - 0.99955) < 0.00001


def test_compute_psi_reflects_deadline_and_context_pressure():
    agent = create_agent("risk-agent")
    agent.metrics.n_active_tasks = 8
    task = Task(
        id="risk-task",
        title="Urgent risky task",
        deadline=datetime.now() + timedelta(minutes=5),
        metadata={"uncertainty": 0.9, "novelty": 0.8},
    )

    risk = compute_psi(task, AgentContext(agent=agent))

    assert 0.5 < risk <= 1.0


def test_update_upsilon_tracks_reputation_with_ema_registry():
    agent = create_agent("rep-agent")
    agent.metrics.rating = 5.0
    agent.metrics.n_reviews = 10
    agent.metrics.n_positive = 9
    registry = MetricRegistry()

    value = update_upsilon(agent, registry)

    assert registry.get("upsilon") == value
    assert 0.0 <= value <= 1.0


def test_rank_actions_prefers_higher_risk_adjusted_utility():
    agent = create_agent("decision-agent")
    task = Task(id="decision-task", title="Choose action", estimated_hours=2.0)
    context = AgentContext(agent=agent, available_budget=100.0)
    low_value = Action(
        name="low",
        params={"revenue": 10.0, "cost": 5.0, "quality_signals": {"accuracy": 0.4}},
    )
    high_value = Action(
        name="high",
        params={"revenue": 100.0, "cost": 5.0, "quality_signals": {"accuracy": 0.9}},
    )

    ranked = rank_actions(task, context, [low_value, high_value])

    assert ranked[0].action.name == "high"
    assert ranked[0].score > ranked[1].score
    assert compute_quality({"accuracy": 1.0}) <= 1.0
