"""
Utility functions for Space1.

Phase 2 connects the current MVP models into a decision utility layer:
    Φ = (R - C) / T
    Ψ = weighted risk pressure
    score = λΦ·norm(Φ) + λΥ·Υ + λΩ·Ω + λQ·Q - Ψ
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, TypedDict, Any
from enum import Enum

from space1.config.loader import get_config
from space1.cost.token_tracker import TokenCostTracker
from space1.factors.registry import FactorRegistry, FactorResult, create_mvp_registry
from space1.metrics.tracker import MetricRegistry
from space1.models.task import Task
from space1.models.agents import Agent
from space1.compliance.core import Action, Rule


class VetoType(Enum):
    """Enums representing specific safety veto categories."""
    NONE = 0
    SOFT = 1
    HARD = 2


class Decision(Enum):
    REJECT = "reject"
    DECLINE = "decline"
    CLARIFY = "clarify"
    EXECUTE = "execute"


# Capability Vector primitive type hint (02_MATHEMATICAL_CORE.md)
CapabilityVector = tuple[float, ...]  # length 17, each x_i in [0,1]


class ReputationVector(TypedDict):
    """Reputation Vector defining multidimensional platform trustworthiness (02_MATHEMATICAL_CORE.md)."""
    tech: float
    econ: float
    comm: float
    rel: float
    sec: float
    domain: float


@dataclass
class MultidimensionalReputation:
    """Multidimensional Reputation representing technical, economic, community, etc. trustworthiness."""
    tech: float = 0.8
    econ: float = 0.8
    comm: float = 0.8
    rel: float = 0.8
    sec: float = 0.8
    domain: float = 0.8

    def scalar_reputation(self) -> float:
        """Project multidimensional Reputation into a scalar [0, 1] using default weights."""
        return _clamp(
            0.2 * self.tech
            + 0.2 * self.econ
            + 0.15 * self.comm
            + 0.15 * self.rel
            + 0.15 * self.sec
            + 0.15 * self.domain
        )

    def update_with_incident(
        self,
        category: str,
        quality: float,
        incident: bool,
        eta: float = 0.1,
        gamma: float = 0.2,
    ) -> None:
        """Update reputation for a specific category based on quality and incident decays."""
        val = getattr(self, category, 0.8)
        new_val = val + eta * quality
        if incident:
            new_val -= gamma * val
        setattr(self, category, _clamp(new_val))


def _read_numeric(obj: object, name: str, default: float) -> float:
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


# --- IV.1 Compliance Veto ---

def check_gamma_hard(action: Action, hard_rules: list[Rule]) -> float:
    """Check hard rules against an action. Returns 0.0 or float('-inf'). Does not raise exceptions."""
    try:
        for rule in hard_rules:
            if not rule.check(action):
                return float('-inf')
        return 0.0
    except Exception:
        return float('-inf')


def check_gamma_soft(action: Action, soft_rules: list[Rule]) -> float:
    """Check soft rules against an action. Returns sum of penalties >= 0.0."""
    try:
        penalty = 0.0
        for rule in soft_rules:
            if not rule.check(action):
                # Accumulate penalty modulated by weight
                weight = getattr(rule, "weight", 1.0)
                penalty += float(weight)
        return penalty
    except Exception:
        return 0.0


# --- IV.2 Profit ---

def compute_phi(
    task_or_price: Task | float | None = None,
    agent_or_quality: Agent | float | None = None,
    cost_or_val: Optional[float] = None,
    time_hours_or_val: Optional[float] = None,
    epsilon_t: float = 1e-6,
    *,
    revenue: Optional[float] = None,
    cost: Optional[float] = None,
    time_hours: Optional[float] = None,
    token_tracker: Optional[TokenCostTracker] = None,
    delta_time: Optional[float] = None,
    Q_score: Optional[float] = None,
    Q_expected: float = 0.7,
    kappa_bonus: float = 0.1,
    kappa_penalty: float = 0.2,
    C_platform: float = 0.0,
    C_processing: float = 0.0,
) -> float:
    """
    Compute Profit (Φ) supporting both legacy signature (task, agent, ...)
    and new positional contract: compute_phi(price, quality, cost, time_hours, epsilon_t).
    """
    # Check if we are using the new positional signature
    if isinstance(task_or_price, (int, float)) and isinstance(agent_or_quality, (int, float)):
        price = float(task_or_price)
        quality = float(agent_or_quality)
        c_val = float(cost_or_val) if cost_or_val is not None else 0.0
        t_val = float(time_hours_or_val) if time_hours_or_val is not None else 1.0
        
        # apply quality-modulation directly on price
        b_Q = kappa_bonus * max(0.0, quality - Q_expected) - kappa_penalty * max(0.0, Q_expected - quality)
        modulated_price = price * (1.0 + b_Q)
        
        # Apply platform and payment processing fees
        modulated_price = modulated_price * (1.0 - C_platform - C_processing)
        
        duration = max(t_val, 0.1)
        return (modulated_price - c_val) / duration

    # Fallback to legacy signature
    # If not numeric, we can treat them as task and agent
    task = task_or_price if not isinstance(task_or_price, (int, float)) else None
    agent = agent_or_quality if not isinstance(agent_or_quality, (int, float)) else None

    # Auto-modulate task duration using 17 factors from aggregate_factors
    if delta_time is None and task is not None and agent is not None:
        try:
            ctx = build_factor_context(task, agent)
            agg = aggregate_factors(ctx)
            delta_time = agg.get("delta_time", 0.0)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Suppressed error: {e}")

    if revenue is None:
        if isinstance(task_or_price, (int, float)):
            revenue = float(task_or_price)
        else:
            default_price = get_config().constants.price_per_task
            revenue = _read_numeric(
                task,
                "revenue",
                _read_numeric(task, "reward", _read_numeric(task, "price", default_price)),
            )

    # b_Q(Q) modifier
    if Q_score is not None:
        b_Q = kappa_bonus * max(0.0, Q_score - Q_expected) - kappa_penalty * max(0.0, Q_expected - Q_score)
        revenue = float(revenue) * (1.0 + b_Q)
    elif isinstance(agent_or_quality, (int, float)):
        b_Q = kappa_bonus * max(0.0, float(agent_or_quality) - Q_expected) - kappa_penalty * max(0.0, Q_expected - float(agent_or_quality))
        revenue = float(revenue) * (1.0 + b_Q)

    # Apply platform and payment processing fees
    revenue = revenue * (1.0 - C_platform - C_processing)

    if cost is None:
        if cost_or_val is not None:
            cost = cost_or_val
        else:
            cost = _read_numeric(task, "cost", get_config().constants.cost_base)
            metrics = getattr(agent, "metrics", None) if agent is not None else None
            cost += _read_numeric(metrics, "total_spent", 0.0)

    if token_tracker is not None:
        cost += token_tracker.get_total_cost()

    if time_hours is None:
        if time_hours_or_val is not None:
            time_hours = time_hours_or_val
        else:
            time_hours = _read_numeric(task, "estimated_hours", get_config().constants.time_base)

    # Apply factor-modulated time scaling safely bounded (G17/Review Gaps: T >= 0.1 * T_base to avoid Φ -> ∞)
    multiplier = 1.0
    if delta_time is not None:
        multiplier = max(0.1, min(10.0, 1.0 + delta_time))
    elif task is not None and hasattr(task, "metadata") and isinstance(task.metadata, dict):
        dt = task.metadata.get("delta_time")
        if dt is not None:
            multiplier = max(0.1, min(10.0, 1.0 + float(dt)))

    T_base = float(time_hours)
    duration = max(T_base * multiplier, 0.1 * T_base, 0.1)
    return (float(revenue) - float(cost)) / duration


class KalmanFilter:
    """Full Kalman filter with automatic gain computation (02_MATHEMATICAL_CORE.md §IV.2).

    State: x (estimated value)
    Process noise: Q (uncertainty in model)
    Measurement noise: R (uncertainty in observations)
    Estimate covariance: P (uncertainty in estimate)
    """

    def __init__(self, initial_state: float = 0.0, Q: float = 0.01, R: float = 0.1, P: float = 1.0):
        self.x = initial_state
        self.Q = Q
        self.R = R
        self.P = P

    def predict(self) -> float:
        """Predict step (state transition is identity)."""
        self.P = self.P + self.Q
        return self.x

    def update(self, observed: float) -> float:
        """Update step with automatic Kalman gain."""
        # Kalman gain
        K = self.P / (self.P + self.R)
        # Update state
        self.x = self.x + K * (observed - self.x)
        # Update covariance
        self.P = (1 - K) * self.P
        return self.x

    def step(self, observed: float) -> float:
        """Full predict + update cycle."""
        self.predict()
        return self.update(observed)


def update_phi_historical(prev: float, observed: float, kalman_gain: float) -> float:
    """Backward-compatible wrapper. Direct formula (same as before)."""
    k = _clamp(kalman_gain)
    return prev + k * (observed - prev)


# --- IV.3 Quality ---

def compute_quality(
    comp_or_comp_score: float | None = None,
    acc_or_val: float | None = None,
    full_or_val: float | None = None,
    time_score_or_val: float | None = None,
    weights_tuple: tuple[float, float, float, float] = (0.25, 0.25, 0.25, 0.25),
    *,
    completeness: float = 0.7,
    accuracy: float = 0.7,
    fullness: float = 0.7,
    timeliness: Optional[float] = None,
    t_actual: Optional[float] = None,
    t_deadline: Optional[float] = None,
    metrics: Optional[MetricRegistry] = None,
) -> float:
    """
    Compute Quality (Q) supporting both legacy signature (completeness, accuracy, ...)
    and new positional contract: compute_quality(comp, acc, full, time_score, weights).
    """
    if isinstance(comp_or_comp_score, (int, float)) and isinstance(acc_or_val, (int, float)):
        # Assert weights sum to 1.0 on inputs (strict contract verification)
        assert abs(sum(weights_tuple) - 1.0) < 1e-5, "Quality weights must sum to 1.0"
        
        c = float(comp_or_comp_score)
        a = float(acc_or_val)
        f = float(full_or_val) if full_or_val is not None else 0.7
        t = float(time_score_or_val) if time_score_or_val is not None else 0.7
        
        value = _clamp(
            weights_tuple[0] * c
            + weights_tuple[1] * a
            + weights_tuple[2] * f
            + weights_tuple[3] * t
        )
        return value

    # Fallback to legacy behavior
    if comp_or_comp_score is not None:
        completeness = comp_or_comp_score
    if acc_or_val is not None:
        accuracy = acc_or_val
    if full_or_val is not None:
        fullness = full_or_val
    if time_score_or_val is not None:
        timeliness = time_score_or_val

    if t_actual is not None and t_deadline is not None:
        deadline = max(t_deadline, 1e-9)
        timeliness = 1.0 - min(1.0, max(0.0, t_actual - t_deadline) / deadline)
    elif timeliness is None:
        timeliness = 0.7

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


# --- IV.4 Risk ---

def compute_psi(
    task_or_p_fail: Task | float | None = None,
    agent_context_or_c_direct: Agent | float | None = None,
    canonical_or_c_reputation: bool | float = False,
    P_base: float = 0.1,
    C_direct: float = 10.0,
    C_reputation: float = 5.0,
    alpha_u: float = 0.2,
    alpha_f: float = 0.2,
    alpha_n: float = 0.2,
    alpha_d: float = 0.2,
    alpha_s: float = 0.5,
    *,
    task: Task | None = None,
    agent_context: Agent | None = None,
    canonical: bool = False,
) -> float:
    """
    Compute Risk (Ψ) supporting both legacy signature
    and new positional contract: compute_psi(p_fail, c_direct, c_reputation).
    """
    # Check if using the new positional signature
    if isinstance(task_or_p_fail, (int, float)) and isinstance(agent_context_or_c_direct, (int, float)):
        p_fail = float(task_or_p_fail)
        c_direct = float(agent_context_or_c_direct)
        c_reputation = float(canonical_or_c_reputation) if isinstance(canonical_or_c_reputation, (int, float)) else 5.0
        return max(0.0, p_fail * (c_direct + c_reputation))

    # Fallback to legacy signature
    arg_task = task if task is not None else (task_or_p_fail if not isinstance(task_or_p_fail, (int, float)) else None)
    arg_agent_context = agent_context if agent_context is not None else (agent_context_or_c_direct if not isinstance(agent_context_or_c_direct, (int, float)) else None)
    arg_canonical = canonical if canonical else (bool(canonical_or_c_reputation) if isinstance(canonical_or_c_reputation, bool) else False)

    weights = get_config().weights.risk
    agent = getattr(arg_agent_context, "agent", arg_agent_context)
    metrics = getattr(agent, "metrics", None)
    capabilities = getattr(agent, "capabilities", None)
    metadata = getattr(arg_agent_context, "metadata", {}) if arg_agent_context is not None else {}
    task_metadata = getattr(arg_task, "metadata", {}) if arg_task is not None else {}

    uncertainty = _clamp(task_metadata.get("uncertainty", metadata.get("uncertainty", 0.5)))
    fatigue = _clamp(_read_numeric(metrics, "n_active_tasks", 0.0) / 10.0)
    novelty = _clamp(task_metadata.get("novelty", metadata.get("novelty", 0.5)))
    deadline = _clamp(_read_numeric(arg_task, "urgency_score", 0.5))
    skill = _clamp(1.0 - _read_numeric(capabilities, "llm_quality", 0.7))

    if arg_canonical:
        p_fail = P_base * (
            1.0
            + alpha_u * uncertainty
            + alpha_f * fatigue
            + alpha_n * novelty
            + alpha_d * deadline
        ) * (1.0 / (1.0 + alpha_s * skill))
        return p_fail * (C_direct + C_reputation)

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


# --- IV.5 Reputation (MUltidimensional) ---

def compute_upsilon_scalar(rep: ReputationVector, weights: dict[str, float]) -> float:
    """Project multidimensional ReputationVector into a scalar [0, 1] using provided weights."""
    return _clamp(
        weights.get("tech", 0.2) * rep.get("tech", 0.8)
        + weights.get("econ", 0.2) * rep.get("econ", 0.8)
        + weights.get("comm", 0.15) * rep.get("comm", 0.8)
        + weights.get("rel", 0.15) * rep.get("rel", 0.8)
        + weights.get("sec", 0.15) * rep.get("sec", 0.8)
        + weights.get("domain", 0.15) * rep.get("domain", 0.8)
    )


def update_upsilon(
    rating: float | ReputationVector | None = None,
    n_reviews: float | int = 0,
    n_positive: dict[str, int] | int = 0,
    retention_rate: float = 0.5,
    delay_score: float = 1.0,
    momentum: float = 0.5,
    metrics: Optional[MetricRegistry] = None,
    reputation_vector: Optional[MultidimensionalReputation] = None,
    *,
    rating_or_rep: float | ReputationVector | None = None,
    n_reviews_or_task_quality: float | int | None = None,
    n_positive_or_incidents: dict[str, int] | int | None = None,
    task_quality: float | int | None = None,
) -> float | ReputationVector:
    """
    Compute soft-capped reputation (scalar float) OR update ReputationVector (Dict) depending on args
    to satisfy both legacy signatures and new Appendix A contracts.
    """
    # Resolve first parameter
    arg_rating = rating if rating is not None else rating_or_rep

    # Resolve second parameter
    if n_reviews_or_task_quality is not None:
        arg_n_reviews = n_reviews_or_task_quality
    elif task_quality is not None:
        arg_n_reviews = task_quality
    else:
        arg_n_reviews = n_reviews

    # Resolve third parameter
    arg_n_positive = n_positive_or_incidents if n_positive_or_incidents is not None else n_positive

    # Dynamic dispatch for ReputationVector contract
    if isinstance(arg_rating, dict):
        rep = dict(arg_rating)
        task_quality_val = float(arg_n_reviews)
        incidents = arg_n_positive if isinstance(arg_n_positive, dict) else {}
        
        eta = 0.1  # learning rate
        gamma = 0.2 # decay rate
        
        for cat in ["tech", "econ", "comm", "rel", "sec", "domain"]:
            val = rep.get(cat, 0.8)
            new_val = val + eta * task_quality_val
            # Apply decay if incidents occurred in this category
            if incidents.get(cat, 0) > 0:
                new_val -= gamma * incidents.get(cat, 0) * val
            rep[cat] = _clamp(new_val)
            
        return rep

    # Fallback to scalar update_upsilon
    rating_val = float(arg_rating) if arg_rating is not None else 0.0
    n_reviews_val = int(arg_n_reviews)
    n_positive_val = int(arg_n_positive) if isinstance(arg_n_positive, (int, float)) else 0

    if reputation_vector is not None:
        return reputation_vector.scalar_reputation()

    cfg = get_config()
    w = cfg.weights.reputation
    c = cfg.constants
    bayes_rating = (w.prior_strength * w.prior_mean + n_reviews_val * rating_val) / max(w.prior_strength + n_reviews_val, 1)
    rating_norm = _clamp((bayes_rating - c.rating_min) / max(c.rating_max - c.rating_min, 1e-9))
    positive_ratio = n_positive_val / n_reviews_val if n_reviews_val > 0 else rating_norm
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


# --- IV.6 Evolution ---

def compute_omega(skill_level: float, knowledge_level: float, weights: tuple[float, float] = (0.5, 0.5)) -> float:
    """Calculate Evolution Score Omega strictly within [0,1]."""
    return _clamp(weights[0] * skill_level + weights[1] * knowledge_level)


def compute_learning_rate(eta_0: float, homeostasis: float, floor: float = 0.2) -> float:
    """Calculate stress-scaled learning rate, bounded strictly by: floor * eta_0 <= outcome <= eta_0."""
    multiplier = max(floor, min(1.0, homeostasis))
    return round(float(eta_0 * multiplier), 9)


# --- IV.7 Homeostasis & Viability ---

def compute_h(balance_ratio: float, rating_ratio: float, workload_ratio: float, quality_ratio: float) -> float:
    """
    Compute homeostasis index H based on 02_MATHEMATICAL_CORE.md.
    Crucially, ratio parameters are NOT restricted to <= 1.0, enabling stress to drop to LOW/outstanding.
    """
    stress = (
        0.3 * (1.0 - balance_ratio)
        + 0.3 * (1.0 - rating_ratio)
        + 0.2 * workload_ratio
        + 0.2 * (1.0 - quality_ratio)
    )
    return 1.0 - stress


def compute_lambda(
    voi: float,
    upsilon_scalar: float,
    dn_tasks_dt: float,
    psi: float,
    error_rate: float,
    n_agents: int,
    nu: float = 0.1,
    gamma_reputation: float = 0.4,
    phi_ft: float = 0.3,
    lambda_psi: float = 0.5,
    rho: float = 0.2,
    delta_coord: float = 0.1,
    epsilon: float = 1e-6
) -> float:
    """
    Compute Lambda (Viability Ratio) from Part IV.8 of 02_MATHEMATICAL_CORE.md:
        Lambda = (F_reinforcing + epsilon) / (F_balancing + epsilon)
    """
    F_reinforcing = nu * voi + gamma_reputation * upsilon_scalar + phi_ft * dn_tasks_dt
    F_balancing = lambda_psi * psi + rho * error_rate + delta_coord * (n_agents ** 2)
    
    return (F_reinforcing + epsilon) / (F_balancing + epsilon)


# --- Legacy aggregations and decorators ---

def build_factor_context(
    task: Task | None = None,
    agent_context: Agent | None = None,
    action: Action | None = None
) -> Dict[str, float | int | List[str] | Dict[str, float]]:
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


def aggregate_factors(context: Dict[str, float | int | List[str] | Dict[str, float]], registry: Optional[FactorRegistry] = None) -> Dict[str, float | Dict[str, FactorResult]]:
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
    action: Action = field(compare=False)
    phi: float = field(compare=False)
    psi: float = field(compare=False)
    quality: float = field(compare=False)
    upsilon: float = field(compare=False)
    omega: float = field(compare=False)
    factors: Dict[str, FactorResult] = field(default_factory=dict, compare=False)


def score_action(
    action: Action,
    *,
    task: Task | None = None,
    agent_context: Agent | None = None,
    token_tracker: Optional[TokenCostTracker] = None,
    metrics: Optional[MetricRegistry] = None,
    factor_registry: Optional[FactorRegistry] = None,
    soft_rules: list[Rule] | None = None,
    gamma_soft: float | None = None,
) -> UtilityDecision:
    """
    Score one action by risk-adjusted utility per 02_MATHEMATICAL_CORE.md §IV.11.
    
    U_raw = λ_Φ·Φ_norm + λ_Υ·Υ + λ_Ω·Ω + λ_Q·Q
    U = U_raw * (1 - min(1, Γ_soft))
    
    Risk (Ψ) is NOT subtracted from U — it's filtered by the gate at the previous step.
    """
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
    
    # U_raw without risk subtraction per §IV.11
    u_raw = w.profit_weight * phi_norm + w.reputation_weight * upsilon + w.evolution_weight * aggregate["omega"] + w.quality_weight * quality
    
    # Apply gamma_soft multiplicatively (gate, not additive penalty)
    if gamma_soft is None and soft_rules is not None:
        gamma_soft = check_gamma_soft(action, soft_rules)
    if gamma_soft is None:
        gamma_soft = 0.0
    
    # U = U_raw * (1 - min(1, Γ_soft)) — §IV.11
    score = _clamp(u_raw * (1.0 - min(1.0, gamma_soft)), -1.0, 1.0)
    
    if metrics is not None:
        metrics.track("utility_score", score, category="operational")
        metrics.track("risk", psi, category="operational")
        metrics.track("profit_rate", phi, category="financial")
    return UtilityDecision(score, action, phi, psi, quality, upsilon, aggregate["omega"], aggregate["results"])


def rank_actions(actions: Iterable[Action], **kwargs: object) -> List[UtilityDecision]:
    """Return candidate actions sorted from highest to lowest utility."""
    return sorted((score_action(action, **kwargs) for action in actions), reverse=True)


def calculate_evolution_score(
    t: float,
    eta_0: float = 0.1,
    gamma: float = 0.5,
    L_0: float = 10.0,
    L_max: float = 100.0,
    K_0: float = 1.0,
    K_max: float = 50.0,
    w_L: float = 0.5,
    w_K: float = 0.5,
    H_val: float = 1.0,
    completed_task_knowledge: float = 5.0,
) -> Dict[str, float]:
    """
    Compute dynamic learning rate eta(t) and evolution score Omega according to 02_MATHEMATICAL_CORE.md.
    """
    import math
    eta = eta_0 * max(0.2, H_val)
    L_s = L_max * (1.0 - math.exp(-eta * (t ** gamma))) + L_0
    K = min(K_max, K_0 + eta * completed_task_knowledge)
    omega = w_L * ((L_s - L_0) / max(L_max - L_0, 1e-9)) + w_K * (K / max(K_max, 1e-9))
    return {
        "eta": eta,
        "L_s": L_s,
        "K": K,
        "omega": _clamp(omega),
    }


def calculate_portfolio_diversity(p_k: List[float]) -> float:
    """
    Compute task diversity / entropy portfolio:
        Delta_div = -sum(p_k * log2(p_k))
    """
    import math
    total = sum(p_k)
    if total <= 0:
        return 0.0
    probs = [p / total for p in p_k]
    return -sum(p * math.log2(p) for p in probs if p > 0.0)


def evaluate_decision_rule(
    gamma_hard: float,
    psi: float,
    psi_max: float,
    C_t: float,
    C_min: float,
    H_TZ: float,
    H_TZ_max: float,
    VoI: float,
    C_info: float,
    H_val: float,
    H_clarify: float,
    U_val: float,
    Q_predicted: float,
    q_min: float,
    *,
    veto_type: VetoType = VetoType.NONE,
    mission_profile: str = "BALANCED",
) -> str:
    """
    Evaluate the canonical decision rule D(T) 4-level cascade from 02_MATHEMATICAL_CORE.md.
    Integrates dynamic thresholds calibrated by Mission profiles (SURVIVAL, GROWTH, CHARITY).
    """
    # 1. Mission Profile Calibration Overrides (02_MATHEMATICAL_CORE.md Dynamic Thresholds)
    if mission_profile == "SURVIVAL":
        # Extreme risk aversion, minimal quality demands to preserve cash
        psi_max = psi_max * 0.5
        q_min = q_min * 0.8
        C_min = C_min * 0.5
    elif mission_profile == "GROWTH":
        # Higher risk tolerance, higher quality demand for reputation building
        psi_max = psi_max * 1.5
        q_min = q_min * 1.2
        C_min = C_min * 1.5
    elif mission_profile == "CHARITY":
        # Low risk limits, minimal quality requirements
        psi_max = psi_max * 2.0
        q_min = q_min * 0.5
        C_min = 0.1

    # Level 1: Hard compliance veto (checking Enum rather than magic numbers)
    if veto_type == VetoType.HARD or gamma_hard == float('-inf') or gamma_hard < -1e9:
        return "REJECT"
        
    # Level 2: Risk and compute budgets above threshold — DECLINE (not a violation, just unfavorable)
    if psi > psi_max or C_t < C_min:
        return "DECLINE"
        
    # Level 3: Information clarification trigger
    if H_TZ > H_TZ_max or VoI > C_info or H_val < H_clarify:
        return "CLARIFY"
        
    # Level 4: Execution utility evaluation
    if U_val > 0.0 and Q_predicted >= q_min:
        return "EXECUTE"
        
    # Level 5: Final failure by U <= 0 — DECLINE (not prohibited, just unprofitable)
    return "DECLINE"
