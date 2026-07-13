"""Tests for Space1 utility functions."""

import space1
from space1.cost import TokenCostTracker
from space1.utility import compute_phi


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

from datetime import datetime, timedelta

from space1.compliance.core import Action
from space1.metrics.tracker import MetricRegistry
from space1.models.agents import Agent, AgentContext
from space1.models.task import Task
from space1.utility import compute_psi, rank_actions, update_upsilon


def test_compute_psi_uses_deadline_and_context_bounds():
    task = Task(id="t1", title="urgent", deadline=datetime.now() + timedelta(hours=1), metadata={"uncertainty": 0.8, "novelty": 0.7})
    context = AgentContext(agent=Agent(id="a1", name="agent"))

    risk = compute_psi(task, context)

    assert 0.0 <= risk <= 1.0
    assert risk > 0.4


def test_update_upsilon_tracks_metric_registry():
    metrics = MetricRegistry()

    value = update_upsilon(4.8, n_reviews=10, n_positive=9, metrics=metrics)

    assert 0.0 <= value <= 1.0
    assert metrics.get("upsilon") == value


def test_rank_actions_prefers_lower_cost_when_other_inputs_match():
    task = Task(id="t2", title="rank", estimated_hours=2.0)
    context = AgentContext(agent=Agent(id="a2", name="agent"))
    cheap = Action(name="cheap", resource_cost=1.0)
    expensive = Action(name="expensive", resource_cost=20.0)

    ranked = rank_actions([expensive, cheap], task=task, agent_context=context)

    assert ranked[0].action == cheap
    assert ranked[0].score >= ranked[1].score
