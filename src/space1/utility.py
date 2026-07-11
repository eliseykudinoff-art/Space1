"""
Utility functions for Space1.

Phase 2 connects the current MVP models into a decision utility layer:
    Φ = (R - C) / T
    Ψ = weighted risk pressure
    score = λΦ·norm(Φ) + λΥ·Υ + λΩ·Ω + λQ·Q - Ψ
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

from .config.loader import get_config
from .cost.token_tracker import TokenCostTracker
from .factors.registry import FactorRegistry, FactorResult, create_mvp_registry
from .metrics.tracker import MetricRegistry


def _read_numeric(obj: Any, name: str, default: float) -> float:
    """Read a numeric attribute or mapping key from an object."""
    if obj is None:
        return default
    value = obj.get(name, default) if isinstance(obj, dict) else getattr(obj, name, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def compute_phi(
    task: Any = None,
    agent: Any = None,
    *,
    revenue: Optional[float] = None,
    cost: Optional[float] = None,
    time_hours: Optional[float] = None,
    token_tracker: Optional[TokenCostTracker] = None,
) -> float:
    """Compute Profit (Φ) with direct, agent and token/tool cost included."""
    if revenue is None:
        default_price = get_config().constants.price_per_task
        revenue = _read_numeric(
            task,
            "revenue",
            _read_numeric(task, "reward", _read_numeric(task, "price", default_price)),
        )

    if cost is None:
        cost = _read_numeric(task, "cost", get_config().constants.cost_base)
        metrics = getattr(agent, "metrics", None) if agent is not None else None
        cost += _read_numeric(metrics, "total_spent", 0.0)

    if token_tracker is not None:
        cost += token_tracker.get_total_cost()

    if time_hours is None:
        time_hours = _read_numeric(task, "estimated_hours", get_config().constants.time_base)

    duration = max(float(time_hours), 1e-9)
    return (float(revenue) - float(cost)) / duration


def compute_psi(task: Any = None, agent_context: Any = None) -> float:
    """Compute bounded risk pressure Ψ from uncertainty, fatigue, novelty, deadline and skill gap."""
    weights = get_config().weights.risk
    agent = getattr(agent_context, "agent", agent_context)
    metrics = getattr(agent, "metrics", None)
    capabilities = getattr(agent, "capabilities", None)
    metadata = getattr(agent_context, "metadata", {}) if agent_context is not None else {}
    task_metadata = getattr(task, "metadata", {}) if task is not None else {}

    uncertainty = _clamp(task_metadata.get("uncertainty", metadata.get("uncertainty", 0.5)))
    fatigue = _clamp(_read_numeric(metrics, "n_active_tasks", 0.0) / 10.0)
    novelty = _clamp(task_metadata.get("novelty", metadata.get("novelty", 0.5)))
    deadline = _clamp(_read_numeric(task, "urgency_score", 0.5))
    skill = _clamp(1.0 - _read_numeric(capabilities, "llm_quality", 0.7))

    raw = (
        weights.uncertainty_coef * uncertainty
        + weights.fatigue_coef * fatigue
        + weights.novelty_coef * novelty
        + weights.deadline_coef * deadline
        + weights.skill_coef * skill
    )
    normalizer = max(
        weights.uncertainty_coef + weights.fatigue_coef + weights.novelty_coef + weights.deadline_coef + weights.skill_coef,
        1e-9,
    )
    return _clamp(raw / normalizer)


def compute_quality(
    *, completeness: float = 0.7, accuracy: float = 0.7, fullness: float = 0.7, timeliness: float = 0.7,
    metrics: Optional[MetricRegistry] = None,
) -> float:
    """Compute Q and optionally write it through MetricRegistry EMA."""
    w = get_config().weights.quality
    value = _clamp(
        w.completeness_weight * completeness
        + w.accuracy_weight * accuracy
        + w.fullness_weight * fullness
        + w.timeliness_weight * timeliness
    )
    if metrics is not None:
        metrics.track("quality", value, category="operational")
    return value


def update_upsilon(
    rating: float, *, n_reviews: int = 0, n_positive: int = 0, retention_rate: float = 0.5,
    delay_score: float = 1.0, momentum: float = 0.5, metrics: Optional[MetricRegistry] = None,
) -> float:
    """Compute soft-capped reputation Υ with a Bayesian rating prior and optional EMA tracking."""
    cfg = get_config()
    w = cfg.weights.reputation
    c = cfg.constants
    bayes_rating = (w.prior_strength * w.prior_mean + n_reviews * rating) / max(w.prior_strength + n_reviews, 1)
    rating_norm = _clamp((bayes_rating - c.rating_min) / max(c.rating_max - c.rating_min, 1e-9))
    positive_ratio = n_positive / n_reviews if n_reviews > 0 else rating_norm
    value = _clamp(
        w.rating_weight * rating_norm
        + w.retention_weight * _clamp(retention_rate)
        + w.positive_ratio_weight * _clamp(positive_ratio)
        + w.delay_weight * _clamp(delay_score)
        + w.momentum_weight * _clamp(momentum)
    )
    if metrics is not None:
        metrics.track("upsilon", value, category="reputation")
    return value


def build_factor_context(task: Any = None, agent_context: Any = None, action: Any = None) -> Dict[str, Any]:
    """Build the shared context consumed by MVP factor implementations."""
    agent = getattr(agent_context, "agent", agent_context)
    capabilities = getattr(agent, "capabilities", None)
    metrics = getattr(agent, "metrics", None)
    mission_params = getattr(agent_context, "mission_params", {}) if agent_context is not None else {}
    return {
        "benchmarks": getattr(capabilities, "to_dict", lambda: {})().get("benchmarks", {}),
        "budget": mission_params.get("budget", getattr(agent_context, "available_budget", 100.0)),
        "task_complexity": getattr(task, "metadata", {}).get("complexity", 0.5) if task is not None else 0.5,
        "quality_requirement": getattr(task, "metadata", {}).get("quality_requirement", 0.7) if task is not None else 0.7,
        "active_guardrails": getattr(action, "params", {}).get("guardrails", []),
        "risk_probabilities": getattr(action, "params", {}).get("risk_probabilities", {}),
        "n_completed_tasks": _read_numeric(capabilities, "n_completed_tasks", 0),
        "current_knowledge": _read_numeric(capabilities, "current_knowledge", 0.0),
        "base_success": _read_numeric(metrics, "success_rate", get_config().constants.success_rate_base),
    }


def aggregate_factors(context: Dict[str, Any], registry: Optional[FactorRegistry] = None) -> Dict[str, Any]:
    """Aggregate MVP factors without duplicating factor weights in callers."""
    registry = registry or create_mvp_registry()
    results = registry.compute_all(context)
    return {
        "results": results,
        "delta_success": sum(r.delta_success for r in results.values()),
        "delta_time": sum(r.delta_time for r in results.values()),
        "omega": _clamp(sum(r.value for r in results.values()) / max(len(results), 1)),
    }


@dataclass(order=True)
class UtilityDecision:
    """Ranked utility result for a candidate action."""
    score: float
    action: Any = field(compare=False)
    phi: float = field(compare=False)
    psi: float = field(compare=False)
    quality: float = field(compare=False)
    upsilon: float = field(compare=False)
    omega: float = field(compare=False)
    factors: Dict[str, FactorResult] = field(default_factory=dict, compare=False)


def score_action(
    action: Any, *, task: Any = None, agent_context: Any = None, token_tracker: Optional[TokenCostTracker] = None,
    metrics: Optional[MetricRegistry] = None, factor_registry: Optional[FactorRegistry] = None,
) -> UtilityDecision:
    """Score one action by risk-adjusted utility."""
    agent = getattr(agent_context, "agent", agent_context)
    phi = compute_phi(task, agent, cost=getattr(action, "resource_cost", None), token_tracker=token_tracker)
    psi = compute_psi(task, agent_context)
    quality = compute_quality(metrics=metrics)
    agent_metrics = getattr(agent, "metrics", None)
    upsilon = update_upsilon(
        _read_numeric(agent_metrics, "rating", get_config().weights.reputation.prior_mean),
        n_reviews=int(_read_numeric(agent_metrics, "n_reviews", 0)),
        n_positive=int(_read_numeric(agent_metrics, "n_positive", 0)),
        metrics=metrics,
    )
    aggregate = aggregate_factors(build_factor_context(task, agent_context, action), factor_registry)
    w = get_config().weights.utility
    phi_norm = _clamp(phi / max(get_config().constants.price_per_task, 1e-9))
    score = _clamp(w.profit_weight * phi_norm + w.reputation_weight * upsilon + w.evolution_weight * aggregate["omega"] + w.quality_weight * quality - psi, -1.0, 1.0)
    if metrics is not None:
        metrics.track("utility_score", score, category="operational")
        metrics.track("risk", psi, category="operational")
        metrics.track("profit_rate", phi, category="financial")
    return UtilityDecision(score, action, phi, psi, quality, upsilon, aggregate["omega"], aggregate["results"])


def rank_actions(actions: Iterable[Any], **kwargs: Any) -> List[UtilityDecision]:
    """Return candidate actions sorted from highest to lowest utility."""
    return sorted((score_action(action, **kwargs) for action in actions), reverse=True)
