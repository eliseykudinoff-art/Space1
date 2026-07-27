"""
System Monitoring Module

Provides:
- SystemMonitor: Background logging of agent health metrics, threshold checking, and alerts dispatch.

Reference: SYSTEM_MONITORING.md
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from enum import Enum


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class MetricValue:
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    unit: str = ""
    tags: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    metric_name: str
    level: AlertLevel
    message: str
    value: float
    threshold: float
    timestamp: datetime = field(default_factory=datetime.now)


class SystemMonitor:
    """
    SystemMonitor (SYSTEM_MONITORING.md).
    
    Tracks system-wide indicators like:
    - budget_health
    - memory_health
    - skill_health
    - compliance_violations
    
    Dispatches alerts to subscribers when thresholds are breached.
    """
    
    def __init__(self):
        self.metrics: Dict[str, List[MetricValue]] = {}
        self.alerts: List[Alert] = []
        self.subscribers: List[Callable[[Alert], None]] = []
        
        # Configure default warning and critical thresholds
        self.thresholds = {
            "budget_health": {"warning": 20.0, "critical": 5.0, "direction": "lt"},
            "compliance_violations": {"warning": 1.0, "critical": 3.0, "direction": "gt"},
            "stress_level": {"warning": 0.7, "critical": 0.9, "direction": "gt"},
        }
        
    def record(self, name: str, value: float, unit: str = "", tags: Optional[Dict[str, Any]] = None) -> None:
        """Record a monitored metric value and evaluate limits."""
        val = MetricValue(
            name=name,
            value=float(value),
            timestamp=datetime.now(),
            unit=unit,
            tags=tags or {}
        )
        
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(val)
        
        self._check_limits(name, val.value)
        
    def _check_limits(self, name: str, value: float) -> None:
        """Evaluate if metric breaches warning or critical thresholds."""
        if name not in self.thresholds:
            return
            
        limits = self.thresholds[name]
        direction = limits.get("direction", "gt")
        
        # Critical checks
        if "critical" in limits:
            crit = limits["critical"]
            if (direction == "gt" and value >= crit) or (direction == "lt" and value <= crit):
                self._dispatch_alert(name, AlertLevel.CRITICAL, value, crit)
                return
                
        # Warning checks
        if "warning" in limits:
            warn = limits["warning"]
            if (direction == "gt" and value >= warn) or (direction == "lt" and value <= warn):
                self._dispatch_alert(name, AlertLevel.WARNING, value, warn)
                
    def _dispatch_alert(self, name: str, level: AlertLevel, value: float, threshold: float) -> None:
        """Create and dispatch an alert to all registered subscribers."""
        alert = Alert(
            metric_name=name,
            level=level,
            message=f"Metric '{name}' breached threshold: current {value} (limit {threshold})",
            value=value,
            threshold=threshold,
            timestamp=datetime.now()
        )
        
        self.alerts.append(alert)
        for sub in self.subscribers:
            try:
                sub(alert)
            except Exception:
                pass
                
    def subscribe(self, callback: Callable[[Alert], None]) -> None:
        """Register alert listener callback."""
        self.subscribers.append(callback)
        
    def get_latest(self, name: str) -> Optional[MetricValue]:
        """Retrieve latest recorded metric."""
        if name not in self.metrics or not self.metrics[name]:
            return None
        return self.metrics[name][-1]
        
    def get_alerts(self, level: Optional[AlertLevel] = None) -> List[Alert]:
        """Retrieve active alerts with optional level filter."""
        if level is None:
            return list(self.alerts)
        return [a for a in self.alerts if a.level == level]
