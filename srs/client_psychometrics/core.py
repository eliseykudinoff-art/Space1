"""
Client Psychometrics — CCRS and risk_premium(T) (06_EXTERNAL_ENVIRONMENT.md §I.2, 02_MATHEMATICAL_CORE.md §IV.4).

Provides:
  - risk_premium(T): 6 binary flags with weights -> [0, 0.5]
  - CCRS: continuous client risk score -> [0, 1] with zone classification
  - ClientRiskProfile: structured 5-component profile
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import math


class RiskZone(Enum):
    GREEN = "green"      # < 0.3  — standard terms
    YELLOW = "yellow"    # 0.3–0.6 — +15% overhead, detailed SOW
    ORANGE = "orange"    # 0.6–0.8 — +30% risk premium, strict milestones
    RED = "red"          # >= 0.8 — +50% or DECLINE, escrow mandatory


@dataclass
class ClientRiskProfile:
    """5-component client psychometric profile (06 §I.2)."""
    scope_creep: float = 0.0
    micromanage: float = 0.0
    payment_risk: float = 0.0
    unrealistic: float = 0.0
    comm_friction: float = 0.0

    # Aggregated score
    ccrs: float = 0.0
    zone: RiskZone = RiskZone.GREEN

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scope_creep": self.scope_creep,
            "micromanage": self.micromanage,
            "payment_risk": self.payment_risk,
            "unrealistic": self.unrealistic,
            "comm_friction": self.comm_friction,
            "ccrs": self.ccrs,
            "zone": self.zone.value,
        }


# =============================================================================
# risk_premium(T) — 6 binary flags (02_MATHEMATICAL_CORE.md §IV.4)
# =============================================================================

# Default weights per canonical table
DEFAULT_RISK_WEIGHTS: Dict[str, float] = {
    "new_client": 0.10,           # No history with this client
    "vague_brief": 0.15,          # Description < 50% of typical for category
    "compressed_deadline": 0.10,  # Deadline < median for category / 8h/day
    "new_tech": 0.15,             # New technology/domain for agent
    "no_milestones": 0.10,        # Not split into payable milestones
    "fixed_price": 0.05,          # Fixed price (not hourly)
}


def risk_premium(
    task_description: str,
    category_median_hours: float = 8.0,
    agent_has_history_with_client: bool = False,
    agent_has_skill_in_domain: bool = True,
    has_milestones: bool = False,
    is_fixed_price: bool = False,
    deadline_hours: Optional[float] = None,
    custom_weights: Optional[Dict[str, float]] = None,
) -> float:
    """
    Compute risk_premium(T) per 02_MATHEMATICAL_CORE.md §IV.4.

    Returns value in [0, 0.5] — additive risk premium to be used in Ψ calculation.
    """
    weights = custom_weights or DEFAULT_RISK_WEIGHTS.copy()
    total = 0.0

    # Flag 1: New client
    if not agent_has_history_with_client:
        total += weights.get("new_client", 0.10)

    # Flag 2: Vague brief (description shorter than 50% of typical)
    typical_desc_len = category_median_hours * 20  # heuristic: ~20 chars per hour
    if len(task_description.strip()) < typical_desc_len * 0.5:
        total += weights.get("vague_brief", 0.15)

    # Flag 3: Compressed deadline
    if deadline_hours is not None and category_median_hours > 0:
        if deadline_hours < category_median_hours:
            total += weights.get("compressed_deadline", 0.10)

    # Flag 4: New technology/domain
    if not agent_has_skill_in_domain:
        total += weights.get("new_tech", 0.15)

    # Flag 5: No milestones
    if not has_milestones:
        total += weights.get("no_milestones", 0.10)

    # Flag 6: Fixed price
    if is_fixed_price:
        total += weights.get("fixed_price", 0.05)

    return min(0.5, total)


# =============================================================================
# CCRS — Continuous Client Risk Score (06_EXTERNAL_ENVIRONMENT.md §I.2)
# =============================================================================

# Default alpha weights for CCRS components (sum to 1)
DEFAULT_CCRS_ALPHAS: Dict[str, float] = {
    "scope_creep": 0.25,
    "micromanage": 0.20,
    "payment_risk": 0.25,
    "unrealistic": 0.15,
    "comm_friction": 0.15,
}

# Market and category modifiers (default 1.0)
DEFAULT_BETA_MARKET: float = 1.0
DEFAULT_GAMMA_CATEGORY: float = 1.0


def compute_ccrs(
    text: str,
    alphas: Optional[Dict[str, float]] = None,
    beta_market: float = 1.0,
    gamma_category: float = 1.0,
) -> ClientRiskProfile:
    """
    Compute CCRS from task text per 06_EXTERNAL_ENVIRONMENT.md §I.2.

    s_k = sigmoid(w_k^T * phi(text) + b_k) for each component.
    CCRS = sum_k alpha_k * s_k * beta_market * gamma_category

    This is a rule-based/heuristic MVP implementation.
    Post-MVP: replace with trained classifier when data is available.
    """
    alphas = alphas or DEFAULT_CCRS_ALPHAS.copy()
    text_lower = text.lower()

    # Heuristic feature extraction (phi(text) proxy)
    def _sigmoid(x: float) -> float:
        return 1.0 / (1.0 + math.exp(-x))

    # Scope creep signals
    scope_signals = [
        "scope" in text_lower,
        "additional" in text_lower,
        "extra" in text_lower,
        "and more" in text_lower,
        "etc" in text_lower,
        "unlimited revisions" in text_lower,
    ]
    scope_score = _sigmoid(sum(scope_signals) * 1.5 - 2.0)

    # Micromanage signals
    micro_signals = [
        "daily call" in text_lower,
        "hourly update" in text_lower,
        "must be online" in text_lower,
        "screen sharing" in text_lower,
        "constant communication" in text_lower,
    ]
    micro_score = _sigmoid(sum(micro_signals) * 2.0 - 2.0)

    # Payment risk signals
    payment_signals = [
        "pay after" in text_lower,
        "no upfront" in text_lower,
        "test task" in text_lower and "free" in text_lower,
        "exposure" in text_lower,
        "portfolio piece" in text_lower,
    ]
    payment_score = _sigmoid(sum(payment_signals) * 2.0 - 1.5)

    # Unrealistic expectations
    unreal_signals = [
        "urgent" in text_lower and "cheap" in text_lower,
        "asap" in text_lower and "budget" in text_lower,
        "world-class" in text_lower and "$" not in text,
        "expert" in text_lower and "student" in text_lower,
    ]
    unreal_score = _sigmoid(sum(unreal_signals) * 2.0 - 1.5)

    # Communication friction
    comm_signals = [
        "only phone" in text_lower,
        "no email" in text_lower,
        "telegram only" in text_lower,
        "whatsapp only" in text_lower,
        "no written agreement" in text_lower,
    ]
    comm_score = _sigmoid(sum(comm_signals) * 2.0 - 1.5)

    # Aggregate
    ccrs = (
        alphas.get("scope_creep", 0.25) * scope_score +
        alphas.get("micromanage", 0.20) * micro_score +
        alphas.get("payment_risk", 0.25) * payment_score +
        alphas.get("unrealistic", 0.15) * unreal_score +
        alphas.get("comm_friction", 0.15) * comm_score
    ) * beta_market * gamma_category

    ccrs = max(0.0, min(1.0, ccrs))

    # Zone classification
    if ccrs < 0.3:
        zone = RiskZone.GREEN
    elif ccrs < 0.6:
        zone = RiskZone.YELLOW
    elif ccrs < 0.8:
        zone = RiskZone.ORANGE
    else:
        zone = RiskZone.RED

    return ClientRiskProfile(
        scope_creep=scope_score,
        micromanage=micro_score,
        payment_risk=payment_score,
        unrealistic=unreal_score,
        comm_friction=comm_score,
        ccrs=ccrs,
        zone=zone,
    )


def payment_terms_from_ccrs(ccrs: float) -> Dict[str, Any]:
    """
    Map CCRS to payment terms per 06 §II.2.
    Returns structured payment recommendation.
    """
    if ccrs < 0.3:
        return {"structure": "standard", "milestone_required": False, "escrow_required": False, "premium_pct": 0}
    elif ccrs < 0.6:
        return {"structure": "milestone", "milestone_required": True, "escrow_required": False, "premium_pct": 15}
    elif ccrs < 0.8:
        return {"structure": "strict_milestone", "milestone_required": True, "escrow_required": False, "premium_pct": 30}
    else:
        return {"structure": "escrow_or_decline", "milestone_required": True, "escrow_required": True, "premium_pct": 50}
