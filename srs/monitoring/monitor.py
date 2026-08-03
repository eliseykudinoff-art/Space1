"""SystemMonitor trial — gauges, thresholds, alerts, OperationalStatus."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class OperationalStatus(str, Enum):
    DORMANT = "dormant"
    ACTIVE = "active"
    RECOVERING = "recovering"
    SUSPENDED = "suspended"

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
    event_id: Optional[str] = None
    def to_dict(self) -> dict:
        return {"metric": self.metric_name, "level": self.level.value, "message": self.message,
                "value": self.value, "threshold": self.threshold, "event_id": self.event_id}

DEFAULT_THRESHOLDS = {
    "budget_health": {"warning": 0.30, "critical": 0.15, "direction": "lt"},
    "tokens_remaining_ratio": {"warning": 0.20, "critical": 0.05, "direction": "lt"},
    "rate_limit_usage": {"warning": 0.80, "critical": 0.95, "direction": "gt"},
    "compliance_violations": {"warning": 1.0, "critical": 1.0, "direction": "gt"},
    "no_progress_count": {"warning": 3.0, "critical": 5.0, "direction": "gt"},
    "provider_up": {"warning": 0.5, "critical": 0.5, "direction": "lt"},
    "platform_risk_score": {"warning": 0.55, "critical": 0.80, "direction": "gt"},
    "queue_depth": {"warning": 20.0, "critical": 50.0, "direction": "gt"},
    "tau_idle": {"warning": 30.0, "critical": 120.0, "direction": "gt"},
    "trust_executor": {"warning": 0.40, "critical": 0.20, "direction": "lt"},
    "tool_reliability": {"warning": 0.50, "critical": 0.30, "direction": "lt"},
    "open_disputes": {"warning": 1.0, "critical": 2.0, "direction": "gt"},
    "payment_overdue": {"warning": 1.0, "critical": 1.0, "direction": "gt"},
    "circuit_open": {"warning": 1.0, "critical": 1.0, "direction": "gt"},
    "global_circuit_trip": {"warning": 1.0, "critical": 1.0, "direction": "gt"},
    "hitl_pending_ticks": {"warning": 10.0, "critical": 30.0, "direction": "gt"},
    "anomaly_score": {"warning": 2.5, "critical": 4.0, "direction": "gt"},
}

def map_alert_to_event(alert: Alert) -> Optional[str]:
    name, level = alert.metric_name, alert.level
    if name == "anomaly_score":
        return None
    critical = {
        "budget_health": "RES.BUDGET_BLOCK", "tokens_remaining_ratio": "RES.TOKENS_EXHAUSTED",
        "rate_limit_usage": "RES.RATE_LIMIT", "compliance_violations": "EXT.COMPLIANCE_HIT",
        "no_progress_count": "EXEC.LOOP_DETECTED", "provider_up": "EXT.PROVIDER_WARNING",
        "platform_risk_score": "EXT.PLATFORM_WARNING", "trust_executor": "TOOL.FAIL",
        "tool_reliability": "TOOL.FAIL", "open_disputes": "EXT.DISPUTE_OPENED",
        "payment_overdue": "EXT.PAYMENT_OVERDUE", "circuit_open": "SYS.CB_OPEN",
        "global_circuit_trip": "SYS.CB_GLOBAL_TRIP", "hitl_pending_ticks": "SYS.HITL_TIMEOUT",
    }
    warning = {
        "tokens_remaining_ratio": "RES.TOKENS_LOW", "rate_limit_usage": "RES.RATE_LIMIT",
        "compliance_violations": "EXT.COMPLIANCE_HIT", "no_progress_count": "EXEC.NO_PROGRESS",
        "provider_up": "EXT.PROVIDER_WARNING", "platform_risk_score": "EXT.PLATFORM_WARNING",
        "open_disputes": "EXT.DISPUTE_OPENED", "payment_overdue": "EXT.PAYMENT_OVERDUE",
        "circuit_open": "SYS.CB_OPEN", "global_circuit_trip": "SYS.CB_GLOBAL_TRIP",
        "hitl_pending_ticks": "SYS.HITL_TIMEOUT", "budget_health": None, "tau_idle": None, "queue_depth": None,
    }
    if level == AlertLevel.CRITICAL:
        return critical.get(name)
    if level == AlertLevel.WARNING:
        return warning.get(name)
    return None

class SystemMonitor:
    def __init__(self, thresholds=None):
        self.thresholds = dict(DEFAULT_THRESHOLDS)
        if thresholds:
            self.thresholds.update(thresholds)
        self.metrics = {}
        self.alerts = []
        self.subscribers = []
        self.status = OperationalStatus.DORMANT
        self._last_alert_key = {}
        self.tick_count = 0

    def subscribe(self, callback):
        self.subscribers.append(callback)

    def set_status(self, status):
        self.status = status

    def record(self, name, value, unit="", tags=None, emit=True):
        from datetime import datetime
        val = MetricValue(name=name, value=float(value), unit=unit, tags=tags or {})
        self.metrics.setdefault(name, []).append(val)
        if not emit:
            return None
        return self._check_limits(name, val.value)

    def _check_limits(self, name, value):
        if name not in self.thresholds:
            return None
        lim = self.thresholds[name]
        direction = lim.get("direction", "gt")
        def breached(thr):
            return value <= thr if direction == "lt" else value >= thr
        alert = None
        if "critical" in lim and breached(float(lim["critical"])):
            alert = self._make_alert(name, AlertLevel.CRITICAL, value, float(lim["critical"]))
        elif "warning" in lim and breached(float(lim["warning"])):
            alert = self._make_alert(name, AlertLevel.WARNING, value, float(lim["warning"]))
        if alert is None:
            return None
        key = f"{name}:{alert.level.value}"
        if self._last_alert_key.get(name) == key:
            return None
        self._last_alert_key[name] = key
        alert.event_id = map_alert_to_event(alert)
        self.alerts.append(alert)
        for sub in self.subscribers:
            try:
                sub(alert)
            except Exception:
                pass
        return alert

    def clear_alert_latch(self, name):
        self._last_alert_key.pop(name, None)

    def _make_alert(self, name, level, value, threshold):
        return Alert(metric_name=name, level=level, message=f"{name}={value} {level.value} thr={threshold}",
                     value=value, threshold=threshold)

    def get_latest(self, name):
        ser = self.metrics.get(name)
        return ser[-1].value if ser else None

    def background_tick(self, gauges):
        self.tick_count += 1
        fired = []
        for name, value in gauges.items():
            if name in self.thresholds:
                lim = self.thresholds[name]
                direction = lim.get("direction", "gt")
                warn = lim.get("warning")
                if warn is not None:
                    ok = value > warn if direction == "lt" else value < warn
                    if ok:
                        self.clear_alert_latch(name)
            a = self.record(name, value)
            if a is not None:
                fired.append(a)
        return fired

    def snapshot(self):
        latest = {n: ser[-1].value for n, ser in self.metrics.items() if ser}
        return {"status": self.status.value, "tick": self.tick_count, "gauges": latest,
                "alerts_n": len(self.alerts), "recent_alerts": [a.to_dict() for a in self.alerts[-5:]]}
