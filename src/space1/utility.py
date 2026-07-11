"""
Utility functions for Space1.

Implements Phase 2 MVP decision-loop formulas:
- Φ: profit with token/tool cost
- Ψ: risk from task/context pressure
- Q: quality estimate
- Υ: soft-capped reputation with EMA support
- risk-adjusted action scoring for MissionProcessor
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Optional

from .config.loader import Config, get_config
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
    """Compute Profit (Φ) = (R - C) / T with token/tool cost included."""
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
    return (float(revenue) - float(cost)) / max(float(time_hours), 1e-9)


def compute_psi(task: Any = None, agent_context: Any = None, config: Optional[Config] = None) -> float:
    """Compute normalized Risk (Ψ) from uncertainty, fatigue, novelty, deadline and skill gap."""
    weights = (config or get_config()).weights.risk
    metadata = getattr(task, "metadata", {}) or {}
    agent = getattr(agent_context, "agent", None)
    metrics = getattr(agent, "metrics", None)
    capabilities = getattr(agent, "capabilities", None)

    uncertainty = _clamp(metadata.get("uncertainty", metadata.get("risk", 0.3)))
    fatigue = _clamp(_read_numeric(metrics, "n_active_tasks", 0.0) / 10.0)
    novelty = _clamp(metadata.get("novelty", 0.5))
    deadline = _clamp(_read_numeric(task, "urgency_score", 0.5))
    skill = _clamp(1.0 - _read_numeric(capabilities, "llm_quality", 0.7))

    weighted = (
        weights.uncertainty_coef * uncertainty
        + weights.fatigue_coef * fatigue
        + weights.novelty_coef * novelty
        + weights.deadline_coef * deadline
        + weights.skill_coef * skill
    )
    normalizer = max(
        weights.uncertainty_coef
        + weights.fatigue_coef
        + weights.novelty_coef
        + weights.deadline_coef
        + weights.skill_coef,
        1e-9,
    )
    return _clamp(weighted / normalizer)


def compute_quality(signals: Optional[Dict[str, float]] = None, config: Optional[Config] = None) -> float:
    """Compute Q from completeness, accuracy, fullness and timeliness signals."""
    signals = signals or {}
    weights = (config or get_config()).weights.quality
    return _clamp(
        weights.completeness_weight * _clamp(signals.get("completeness", 0.7))
        + weights.accuracy_weight * _clamp(signals.get("accuracy", 0.7))
        + weights.fullness_weight * _clamp(signals.get("fullness", 0.7))
        + weights.timeliness_weight * _clamp(signals.get("timeliness", 0.7))
    )


def compute_upsilon(agent: Any = None, config: Optional[Config] = None) -> float:
    """Compute soft-capped reputation Υ in [0, 1] with Bayesian review prior."""
    cfg = config or get_config()
    weights = cfg.weights.reputation
    constants = cfg.constants
    metrics = getattr(agent, "metrics", agent)
    rating = _read_numeric(metrics, "rating", weights.prior_mean)
    reviews = max(_read_numeric(metrics, "n_reviews", 0.0), 0.0)
    positives = max(_read_numeric(metrics, "n_positive", 0.0), 0.0)
    success = _clamp(_read_numeric(metrics, "success_rate", 0.3))
    avg_time = max(_read_numeric(metrics, "avg_task_time", 1.0), 1e-9)

    bayes_rating = (weights.prior_strength * weights.prior_mean + reviews * rating) / (
        weights.prior_strength + reviews
    )
    rating_norm = _clamp((bayes_rating - constants.rating_min) / (constants.rating_max - constants.rating_min))
    positive_ratio = _clamp(positives / reviews) if reviews else _clamp((weights.prior_mean - 1.0) / 4.0)
    delay_score = _clamp(1.0 / avg_time)

    return _clamp(
        weights.rating_weight * rating_norm
        + weights.retention_weight * success
        + weights.positive_ratio_weight * positive_ratio
        + weights.delay_weight * delay_score
        + weights.momentum_weight * success
    )


def update_upsilon(agent: Any, registry: MetricRegistry, alpha: Optional[float] = None) -> float:
    """Update reputation Υ through MetricRegistry EMA."""
    return registry.track("upsilon", compute_upsilon(agent), category="reputation", alpha=alpha)


@dataclass
class ActionScore:
    """Detailed utility score for one candidate action."""

    action: Any
    score: float
    phi: float
    psi: float
    quality: float
    upsilon: float
    factors: Dict[str, FactorResult] = field(default_factory=dict)


class FactorCalculator:
    """Aggregates enabled MVP factors without hardcoding factor weights in callers."""

    def __init__(self, registry: Optional[FactorRegistry] = None):
        self.registry = registry or create_mvp_registry()

    def build_context(self, task: Any, agent_context: Any, action: Any) -> Dict[str, Any]:
        agent = getattr(agent_context, "agent", None)
        capabilities = getattr(agent, "capabilities", None)
        mission_params = getattr(agent_context, "mission_params", {}) or {}
        params = getattr(action, "params", {}) or {}
        return {
            "benchmarks": getattr(capabilities, "to_dict", lambda: {})().get("benchmarks", {}),
            "budget": mission_params.get("budget", _read_numeric(agent_context, "available_budget", 100.0)),
            "task_complexity": params.get("task_complexity", getattr(task, "metadata", {}).get("complexity", 0.5)),
            "quality_requirement": params.get("quality_requirement", 0.7),
            "active_guardrails": params.get("active_guardrails", []),
            "risk_probabilities": params.get("risk_probabilities", {}),
            "n_completed_tasks": _read_numeric(capabilities, "n_completed_tasks", 0.0),
            "current_knowledge": _read_numeric(capabilities, "current_knowledge", 0.0),
            "base_success": _read_numeric(getattr(agent, "metrics", None), "success_rate", 0.3),
        }

    def compute(self, task: Any, agent_context: Any, action: Any) -> Dict[str, FactorResult]:
        return self.registry.compute_all(self.build_context(task, agent_context, action))


def score_action(
    task: Any,
    agent_context: Any,
    action: Any,
    *,
    token_tracker: Optional[TokenCostTracker] = None,
    metric_registry: Optional[MetricRegistry] = None,
    factor_calculator: Optional[FactorCalculator] = None,
    config: Optional[Config] = None,
) -> ActionScore:
    """Compute risk-adjusted composite utility for one compliant action."""
    cfg = config or get_config()
    agent = getattr(agent_context, "agent", None)
    params = getattr(action, "params", {}) or {}
    revenue = params.get("revenue", _read_numeric(task, "revenue", _read_numeric(task, "price", cfg.constants.price_per_task)))
    cost = params.get("cost", _read_numeric(task, "cost", 0.0) + _read_numeric(action, "resource_cost", 0.0))
    time_hours = params.get("estimated_hours", _read_numeric(task, "estimated_hours", cfg.constants.time_base))

    phi = compute_phi(task, agent, revenue=revenue, cost=cost, time_hours=time_hours, token_tracker=token_tracker)
    psi = compute_psi(task, agent_context, cfg)
    quality = compute_quality(params.get("quality_signals"), cfg)
    upsilon = compute_upsilon(agent, cfg)
    factors = (factor_calculator or FactorCalculator()).compute(task, agent_context, action)
    factor_delta = sum(result.delta_success - result.delta_time for result in factors.values())

    weights = cfg.weights.utility
    normalized_phi = phi / max(abs(revenue), 1.0)
    score = (
        weights.profit_weight * normalized_phi
        + weights.reputation_weight * upsilon
        + weights.quality_weight * quality
        + weights.evolution_weight * factor_delta
    ) * (1.0 - psi)

    if metric_registry is not None:
        metric_registry.track("phi", phi, category="financial")
        metric_registry.track("psi", psi, category="homeostatic")
        metric_registry.track("quality", quality, category="operational")
        metric_registry.track("utility_score", score, category="operational")
        update_upsilon(agent, metric_registry)

    return ActionScore(action=action, score=score, phi=phi, psi=psi, quality=quality, upsilon=upsilon, factors=factors)


def rank_actions(task: Any, agent_context: Any, actions: Iterable[Any], **kwargs: Any) -> list[ActionScore]:
    """Return candidate action scores ordered best-first."""
    return sorted((score_action(task, agent_context, action, **kwargs) for action in actions), key=lambda s: s.score, reverse=True)
