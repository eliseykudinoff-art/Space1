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
