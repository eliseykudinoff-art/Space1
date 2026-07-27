"""
Cold-start initial values (02_MATHEMATICAL_CORE.md Часть X).

Provides explicit starting values for:
  - H(0) = 1.0 (homeostasis baseline)
  - Upsilon_k(0) = 0.5 (neutral reputation)
  - Phi_historical(0) — prior from RLI/population default
  - UCB1 n_e=0 protection (division by zero guard)
  - Predictor ensemble priors for n=0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import math


# =============================================================================
# Canonical cold-start constants (02_MATHEMATICAL_CORE.md Часть X)
# =============================================================================

H_INITIAL: float = 1.0           # Homeostasis baseline at t=0
UPSILON_INITIAL: float = 0.5     # Neutral reputation at t=0
PHI_HISTORICAL_INITIAL: float = 0.0  # No historical profit data

# RLI/population default for cold-start prediction
RLI_POPULATION_DEFAULT_Q: float = 0.65   # Prior quality estimate
RLI_POPULATION_DEFAULT_PSI: float = 0.25  # Prior risk estimate

# UCB1 epsilon guard for n_e=0
UCB1_EPSILON: float = 1e-6

# Predictor ensemble weights by n (completed tasks)
# n < 5:  ref=0.4, bayes=0.2, llm=0.4
# 5 <= n < 20: ref=0.2, bayes=0.5, llm=0.3
# n >= 20: ref=0.1, bayes=0.7, llm=0.2
ENSEMBLE_WEIGHTS: Dict[str, Tuple[float, float, float]] = {
    "cold": (0.4, 0.2, 0.4),      # n < 5
    "warm": (0.2, 0.5, 0.3),      # 5 <= n < 20
    "hot": (0.1, 0.7, 0.2),       # n >= 20
}


@dataclass
class ColdStartState:
    """Complete cold-start state bundle for a new agent or new task category."""
    H: float = H_INITIAL
    upsilon_k: float = UPSILON_INITIAL
    phi_historical: float = PHI_HISTORICAL_INITIAL
    q_prior: float = RLI_POPULATION_DEFAULT_Q
    psi_prior: float = RLI_POPULATION_DEFAULT_PSI
    n_completed: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "H": self.H,
            "upsilon_k": self.upsilon_k,
            "phi_historical": self.phi_historical,
            "q_prior": self.q_prior,
            "psi_prior": self.psi_prior,
            "n_completed": self.n_completed,
        }


def get_ensemble_weights(n_completed: int) -> Tuple[float, float, float]:
    """
    Return (w_ref, w_bayes, w_llm) for predictor ensemble based on experience.
    Per 03_PIPELINE_MATH.md §III.1.
    """
    if n_completed < 5:
        return ENSEMBLE_WEIGHTS["cold"]
    elif n_completed < 20:
        return ENSEMBLE_WEIGHTS["warm"]
    else:
        return ENSEMBLE_WEIGHTS["hot"]


def ucb1_safe_divide(numerator: float, denominator: float, epsilon: float = UCB1_EPSILON) -> float:
    """Guarded division for UCB1 — prevents division by zero at cold start."""
    return numerator / max(denominator, epsilon)


def compute_ucb1_score(
    mean_reward: float,
    n_selections: int,
    total_selections: int,
    c_exploration: float = math.sqrt(2),
) -> float:
    """
    UCB1 score with cold-start protection.
    When n_selections=0, returns +inf (guaranteed first chance).
    """
    if n_selections == 0:
        return float("inf")
    exploration = c_exploration * math.sqrt(
        ucb1_safe_divide(math.log(total_selections), n_selections)
    )
    return mean_reward + exploration


def get_predictor_priors(category: Optional[str] = None) -> Tuple[float, float]:
    """
    Return (q_predicted_hat, psi_hat) priors for cold start.
    Uses population default or category-specific prior if available.
    """
    # Category-specific priors could be loaded from config
    category_priors: Dict[str, Tuple[float, float]] = {
        # Add category-specific priors here as they become available
    }
    if category and category in category_priors:
        return category_priors[category]
    return (RLI_POPULATION_DEFAULT_Q, RLI_POPULATION_DEFAULT_PSI)


def initialize_agent_state(agent_dict: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Initialize an agent's state with canonical cold-start values.
    Mutates and returns the dict.
    """
    state = agent_dict or {}
    state.setdefault("H", H_INITIAL)
    state.setdefault("upsilon_k", UPSILON_INITIAL)
    state.setdefault("phi_historical", PHI_HISTORICAL_INITIAL)
    state.setdefault("n_completed", 0)
    state.setdefault("q_prior", RLI_POPULATION_DEFAULT_Q)
    state.setdefault("psi_prior", RLI_POPULATION_DEFAULT_PSI)
    return state
