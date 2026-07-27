"""
AIOS Tool Manager Kernel Module.

Reference: 04_ARCHITECTURE.md (Part V / Part IV.5).
Manages functional specialists, execution tools, retries, and UCB1 specialist routing.
"""

import math
from typing import List, Dict, Any, Optional
from ..agents.core import SpecialistSubroutine


class AIOSToolManager:
    """
    AIOSToolManager.
    Manages functional subroutines and dispatches actions using UCB1 selection.
    """
    
    def __init__(self, c_exploration: float = 1.414):
        self.c = c_exploration
        self._specialists: Dict[str, SpecialistSubroutine] = {}
        # UCB1 stats: specialist_name -> {"selections": int, "rewards_sum": float}
        self._stats: Dict[str, Dict[str, Any]] = {}
        self._total_selections = 0
        
    def register_specialist(self, specialist: SpecialistSubroutine) -> None:
        """Register an execution specialist subroutine."""
        name = specialist.name
        self._specialists[name] = specialist
        if name not in self._stats:
            self._stats[name] = {"selections": 0, "rewards_sum": 0.0}
            
    def record_outcome(self, name: str, success: bool) -> None:
        """Record the outcome (reward 1.0 or 0.0) of a specialist's task run."""
        if name in self._stats:
            self._stats[name]["selections"] += 1
            self._stats[name]["rewards_sum"] += 1.0 if success else 0.0
            self._total_selections += 1
            
    def select_best_specialist(self, candidates: List[str]) -> str:
        """
        Select the best specialist subroutine among candidates using the UCB1 algorithm.
        If a candidate has never been selected, it gets selected immediately to ensure cold start.
        """
        if not candidates:
            raise ValueError("No specialist candidates provided")
            
        # 1. Cold start check
        for name in candidates:
            if name in self._stats and self._stats[name]["selections"] == 0:
                return name
                
        # 2. Compute UCB1 scores
        best_score = -1.0
        best_name = candidates[0]
        
        for name in candidates:
            stats = self._stats.get(name, {"selections": 0, "rewards_sum": 0.0})
            n_i = stats["selections"]
            if n_i == 0:
                continue
                
            mean_reward = stats["rewards_sum"] / n_i
            # UCB1 = mean_reward + c * sqrt(ln(N) / n_i)
            ucb_score = mean_reward + self.c * math.sqrt(math.log(max(1, self._total_selections)) / n_i)
            
            if ucb_score > best_score:
                best_score = ucb_score
                best_name = name
                
        return best_name
        
    def get_specialist(self, name: str) -> Optional[SpecialistSubroutine]:
        """Retrieve specialist by name."""
        return self._specialists.get(name)
