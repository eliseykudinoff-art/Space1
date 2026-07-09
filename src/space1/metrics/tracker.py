"""
MetricTracker — Metrics Tracking with EMA (Exponential Moving Average)

Reference: DEVELOPMENT_PLAN.md - G4 (Feedback Loop)
Formula: S_{t+1} = S_t + α · (R_t - S_t), α = 0.2 (default)
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import time


@dataclass
class MetricRecord:
    """Record of a single metric update."""
    timestamp: float
    value: float
    raw_value: float
    alpha: float


class MetricTracker:
    """
    MetricTracker with EMA (Exponential Moving Average) updates.
    
    Formula:
        S_{t+1} = S_t + α · (R_t - S_t)
    
    Usage:
        tracker = MetricTracker()
        tracker.update('success_rate', 0.8)
        tracker.update('success_rate', 0.85)
        value = tracker.get('success_rate')  # ~0.84
    """
    
    def __init__(self, default_alpha: float = 0.2):
        """
        Args:
            default_alpha: Default EMA smoothing factor (0 < alpha <= 1)
        """
        if not 0 < default_alpha <= 1:
            raise ValueError("alpha must be in (0, 1]")
        
        self._default_alpha = default_alpha
        self._metrics: Dict[str, float] = {}
        self._history: Dict[str, list] = {}
        self._timestamps: Dict[str, float] = {}
    
    def update(self, metric: str, new_value: float, alpha: Optional[float] = None) -> float:
        """
        Update a metric using EMA formula.
        
        Args:
            metric: Metric name
            new_value: New raw observation
            alpha: EMA smoothing factor (uses default if None)
        
        Returns:
            New EMA value
        """
        alpha = alpha if alpha is not None else self._default_alpha
        
        if metric not in self._metrics:
            # First value - no EMA, just set
            self._metrics[metric] = new_value
            self._history[metric] = []
            self._timestamps[metric] = time.time()
        else:
            # EMA update: S_{t+1} = S_t + α · (R_t - S_t)
            current = self._metrics[metric]
            self._metrics[metric] = current + alpha * (new_value - current)
        
        # Record history
        self._history[metric].append(MetricRecord(
            timestamp=time.time(),
            value=self._metrics[metric],
            raw_value=new_value,
            alpha=alpha
        ))
        
        # Keep last 1000 records
        if len(self._history[metric]) > 1000:
            self._history[metric] = self._history[metric][-1000:]
        
        return self._metrics[metric]
    
    def get(self, metric: str, default: Optional[float] = None) -> Optional[float]:
        """
        Get current EMA value for a metric.
        
        Args:
            metric: Metric name
            default: Default value if metric not found
        
        Returns:
            Current EMA value or default
        """
        return self._metrics.get(metric, default)
    
    def get_raw(self, metric: str, n: int = 1) -> Optional[float]:
        """
        Get last n raw values for a metric.
        
        Args:
            metric: Metric name
            n: Number of last values to return
        
        Returns:
            List of last n raw values
        """
        if metric not in self._history:
            return None
        
        history = self._history[metric]
        if n == 1:
            return history[-1].raw_value if history else None
        
        return [r.raw_value for r in history[-n:]]
    
    def get_history(self, metric: str, n: Optional[int] = None) -> list:
        """
        Get metric history.
        
        Args:
            metric: Metric name
            n: Number of last records (None = all)
        
        Returns:
            List of MetricRecord
        """
        if metric not in self._history:
            return []
        
        history = self._history[metric]
        if n is None:
            return history
        
        return history[-n:]
    
    def get_all(self) -> Dict[str, float]:
        """Get all current metric values."""
        return self._metrics.copy()
    
    def reset(self, metric: Optional[str] = None) -> None:
        """
        Reset metrics.
        
        Args:
            metric: Specific metric to reset, or None for all
        """
        if metric is None:
            self._metrics.clear()
            self._history.clear()
            self._timestamps.clear()
        else:
            self._metrics.pop(metric, None)
            self._history.pop(metric, None)
            self._timestamps.pop(metric, None)
    
    def get_stats(self, metric: str) -> Dict[str, float]:
        """
        Get statistics for a metric.
        
        Returns:
            Dict with: current, mean, min, max, count
        """
        if metric not in self._history:
            return {}
        
        history = self._history[metric]
        values = [r.raw_value for r in history]
        
        return {
            "current": self._metrics.get(metric, 0),
            "mean": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "count": len(values)
        }


class MetricsEngine:
    """
    Engine for computing system metrics.
    
    Centralizes all metric computations for Space1.
    """
    
    def __init__(self, default_alpha: float = 0.2):
        self.tracker = MetricTracker(default_alpha=default_alpha)
        self._formulas: Dict[str, callable] = {}
    
    def compute_phi(self, task: Any, agent: Any) -> float:
        """
        Compute Profit (Φ) = (R - C) / T
        
        Note: Full implementation in Phase 2
        """
        return 0.0
    
    def compute_psi(self, task: Any) -> float:
        """
        Compute Risk (Ψ) = P_fail × (C_direct + C_reputation)
        
        Note: Full implementation in Phase 2
        """
        return 0.0
    
    def track(self, metric: str, value: float, alpha: Optional[float] = None) -> float:
        """Shortcut for tracker.update()."""
        return self.tracker.update(metric, value, alpha)
    
    def get(self, metric: str, default: Optional[float] = None) -> Optional[float]:
        """Shortcut for tracker.get()."""
        return self.tracker.get(metric, default)


class MetricRegistry:
    """
    Единый источник истины для всех метрик агента.
    
    G14: MetricRegistry — Single source of truth
    
    Все метрики системы собираются здесь:
    - Гомеостатические переменные
    - Финансовые метрики
    - Репутационные метрики
    - Операционные метрики
    
    Usage:
        registry = MetricRegistry()
        registry.track("balance", 100.0)
        registry.track("rating", 4.5)
        
        # Получить все метрики
        all_metrics = registry.get_all()
        
        # Получить историю
        history = registry.get_history("balance")
    """
    
    # Категории метрик
    CATEGORIES = {
        "financial": ["balance", "total_earned", "total_spent", "revenue_rate"],
        "reputation": ["rating", "n_reviews", "n_positive", "retention_rate"],
        "operational": ["success_rate", "avg_task_time", "n_active_tasks", "utilization"],
        "cost": ["token_cost", "api_cost", "tool_cost"],
        "homeostatic": ["stress_level", "capacity_utilization", "reputation_health"],
    }
    
    def __init__(self):
        self._tracker = MetricTracker(default_alpha=0.2)
        self._categories: Dict[str, list] = self.CATEGORIES.copy()
    
    def track(self, metric: str, value: float, 
              category: Optional[str] = None,
              alpha: Optional[float] = None) -> float:
        """
        Track a metric with EMA smoothing.
        
        Args:
            metric: Metric name
            value: New value
            category: Optional category for organization
            alpha: EMA smoothing factor
        """
        result = self._tracker.update(metric, value, alpha)
        
        if category and metric not in self._categories.get(category, []):
            if category not in self._categories:
                self._categories[category] = []
            self._categories[category].append(metric)
        
        return result
    
    def get(self, metric: str, default: Optional[float] = None) -> Optional[float]:
        """Get current EMA value for a metric."""
        return self._tracker.get(metric, default)
    
    def get_all(self) -> Dict[str, float]:
        """Get all current metric values."""
        return self._tracker.get_all()
    
    def get_by_category(self, category: str) -> Dict[str, float]:
        """Get all metrics in a category."""
        metrics = self._categories.get(category, [])
        return {m: self._tracker.get(m, 0.0) for m in metrics}
    
    def get_categories(self) -> list:
        """Get list of all categories."""
        return list(self._categories.keys())
    
    def get_history(self, metric: str, n: Optional[int] = None) -> list:
        """Get metric history."""
        return self._tracker.get_history(metric, n)
    
    def get_stats(self, metric: str) -> Dict[str, float]:
        """Get statistics for a metric."""
        return self._tracker.get_stats(metric)
    
    def reset(self, metric: Optional[str] = None) -> None:
        """Reset metrics."""
        self._tracker.reset(metric)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize registry state."""
        return {
            "metrics": self.get_all(),
            "categories": self._categories,
        }
