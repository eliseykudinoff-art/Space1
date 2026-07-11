"""
Utility functions for Space1.

Implements the MVP profit function Φ from the development plan:
    Φ = (R - C) / T
where token/tool costs are included in C when a TokenCostTracker is provided.
"""

from typing import Any, Optional

from .cost.token_tracker import TokenCostTracker


def _read_numeric(obj: Any, name: str, default: float) -> float:
    """Read a numeric attribute or mapping key from an object."""
    if obj is None:
        return default

    if isinstance(obj, dict):
        value = obj.get(name, default)
    else:
        value = getattr(obj, name, default)

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def compute_phi(
    task: Any = None,
    agent: Any = None,
    *,
    revenue: Optional[float] = None,
    cost: Optional[float] = None,
    time_hours: Optional[float] = None,
    token_tracker: Optional[TokenCostTracker] = None,
) -> float:
    """
    Compute MVP Profit (Φ) with token/tool cost included in total cost.

    Args:
        task: Optional task-like object. Uses ``price``/``reward``/``revenue``,
            ``estimated_hours``, and ``cost`` attributes/keys when explicit values
            are not supplied.
        agent: Optional agent-like object. If it exposes ``metrics.total_spent``,
            that amount is included in cost when explicit ``cost`` is not supplied.
        revenue: Explicit revenue/reward R.
        cost: Explicit direct cost C before token/tool costs.
        time_hours: Explicit duration T in hours.
        token_tracker: Optional TokenCostTracker whose total is added to C.

    Returns:
        (R - C) / T. T is clamped to a small positive value to avoid division by zero.
    """
    if revenue is None:
        revenue = _read_numeric(
            task,
            "revenue",
            _read_numeric(task, "reward", _read_numeric(task, "price", 0.0)),
        )

    if cost is None:
        cost = _read_numeric(task, "cost", 0.0)
        metrics = getattr(agent, "metrics", None) if agent is not None else None
        cost += _read_numeric(metrics, "total_spent", 0.0)

    if token_tracker is not None:
        cost += token_tracker.get_total_cost()

    if time_hours is None:
        time_hours = _read_numeric(task, "estimated_hours", 1.0)

    duration = max(float(time_hours), 1e-9)
    return (float(revenue) - float(cost)) / duration
