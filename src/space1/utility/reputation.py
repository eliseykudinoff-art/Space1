"""
Reputation Module — Soft-Capped Reputation (Υ)

G8: Soft cap + EMA decay
    Υ = min(1.0, raw_score × decay_factor)
    decay_factor = γ^t where γ = 0.95 (configurable)
    
EMA update:
    Υ_{t+1} = Υ_t + α · (new_Υ - Υ_t)

Reference: DEVELOPMENT_PLAN.md - G8
           MATHEMATICAL_FORMULAS.md - Reputation soft cap
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime

from space1.config.loader import get_config
from space1.metrics.tracker import MetricRegistry
from space1.utility import update_upsilon, _clamp


@dataclass
class ReputationState:
    """Internal state for reputation tracking."""
    last_update: datetime = field(default_factory=datetime.now)
    cumulative_score: float = 0.0
    update_count: int = 0
    
    def to_dict(self) -> dict:
        return {
            "last_update": self.last_update.isoformat(),
            "cumulative_score": self.cumulative_score,
            "update_count": self.update_count,
        }


class SoftCappedReputation:
    """
    Soft-Capped Reputation calculator with EMA decay.
    
    Formula:
        raw_Υ = computed reputation score [0, ∞)
        Υ = min(cap, raw_Υ × decay^Δt)
        
    Where:
        cap = maximum reputation (default: 1.0)
        decay = decay factor per time unit (default: 0.95)
        Δt = time since last update
        
    The soft cap ensures reputation doesn't grow unbounded,
    while the decay factor ensures inactive reputation slowly fades.
    """
    
    def __init__(
        self,
        cap: Optional[float] = None,
        decay_factor: Optional[float] = None,
        ema_alpha: float = 0.2,
    ):
        cfg = get_config().constants
        self.cap = cap if cap is not None else cfg.upsilon_cap
        self.decay_factor = decay_factor if decay_factor is not None else cfg.upsilon_decay
        self.ema_alpha = ema_alpha
        self._state = ReputationState()
        self._current_ema: float = 0.0
    
    def compute(
        self,
        rating: float,
        *,
        n_reviews: int = 0,
        n_positive: int = 0,
        retention_rate: float = 0.5,
        delay_score: float = 1.0,
        momentum: float = 0.5,
        metrics: Optional[MetricRegistry] = None,
    ) -> float:
        """
        Compute soft-capped reputation.
        
        Args:
            rating: Raw rating value
            n_reviews: Total number of reviews
            n_positive: Number of positive reviews
            retention_rate: Client retention rate [0, 1]
            delay_score: Delay score [0, 1]
            momentum: Momentum factor [0, 1]
            metrics: Optional MetricRegistry for EMA tracking
            
        Returns:
            Soft-capped reputation value [0, cap]
        """
        # Compute time decay
        now = datetime.now()
        time_delta = (now - self._state.last_update).total_seconds() / 3600.0  # hours
        decay = self.decay_factor ** time_delta
        
        # Compute base reputation using existing function
        raw_upsilon = update_upsilon(
            rating=rating,
            n_reviews=n_reviews,
            n_positive=n_positive,
            retention_rate=retention_rate,
            delay_score=delay_score,
            momentum=momentum,
        )
        
        # Apply decay
        decayed = raw_upsilon * decay
        
        # Apply soft cap
        capped = min(self.cap, decayed)
        
        # EMA update
        if self._state.update_count == 0:
            self._current_ema = capped
        else:
            self._current_ema = self._current_ema + self.ema_alpha * (capped - self._current_ema)
        
        # Update state
        self._state.last_update = now
        self._state.cumulative_score += raw_upsilon
        self._state.update_count += 1
        
        # Track through MetricRegistry if provided
        if metrics is not None:
            metrics.track("upsilon_soft_capped", self._current_ema, category="reputation")
            metrics.track("upsilon_raw", raw_upsilon, category="reputation")
        
        return self._current_ema
    
    def get_current(self) -> float:
        """Get current EMA reputation value."""
        return self._current_ema
    
    def apply_decay_only(self) -> float:
        """
        Apply decay without new input (for periodic updates).
        
        Returns:
            Decayed reputation value
        """
        now = datetime.now()
        time_delta = (now - self._state.last_update).total_seconds() / 3600.0
        decay = self.decay_factor ** time_delta
        
        self._current_ema *= decay
        self._current_ema = min(self.cap, self._current_ema)
        self._state.last_update = now
        
        return self._current_ema
    
    def reset(self) -> None:
        """Reset reputation state."""
        self._state = ReputationState()
        self._current_ema = 0.0
    
    def to_dict(self) -> dict:
        return {
            "state": self._state.to_dict(),
            "current_ema": self._current_ema,
            "cap": self.cap,
            "decay_factor": self.decay_factor,
        }
