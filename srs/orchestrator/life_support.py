"""LifeSupport — homeostasis + monitoring (P0 single motor face)."""
from __future__ import annotations
from typing import Any, Dict, Optional

from ..homeostasis.service import HomeostasisService
from ..homeostasis.config import HomeostasisConfig
from ..monitoring.monitor import SystemMonitor, OperationalStatus
from ..monitoring.bridge import MonitorHomeostasisBridge

STATUS_EVENT_MAP: Dict[str, str] = {
    "SUCCESS": "EXEC.TASK_DONE",
    "REJECTED_BY_COMPLIANCE": "EXT.COMPLIANCE_HIT",
    "FAILED_QUALITY_GOAL": "EXEC.VERIFIER_FAIL",
    "DECLINED_BY_DECISION_RULE": "EXT.ORDER_REJECTED",
    "CLARIFY_REQUIRED": "MEMORY.GAP",
    "STALL": "IDLE.QUEUE_EMPTY",
}


class LifeSupport:
    def __init__(self, config: Optional[HomeostasisConfig] = None):
        overrides = {
            "EXT.PAYMENT_OVERDUE": (0.35, 0.0),
            "EXT.DISPUTE_OPENED": (0.40, 0.0),
            "EXT.REPUTATION_HIT": (0.35, 0.0),
            "SYS.CB_OPEN": (0.45, 0.0),
            "SYS.CB_GLOBAL_TRIP": (0.70, 0.0),
            "SYS.HITL_TIMEOUT": (0.30, 0.0),
            "TOOL.FAIL": (0.30, 0.0),
            "RES.TOKENS_LOW": (0.22, 0.0),
            "RES.TOKENS_EXHAUSTED": (0.55, 0.0),
        }
        cfg = config or HomeostasisConfig(amplitude_overrides=overrides)
        self.homeostasis = HomeostasisService(cfg)
        self.monitor = SystemMonitor()
        self.bridge = MonitorHomeostasisBridge(self.monitor, self.homeostasis)
        self._no_progress = 0.0
        self._compliance_hits = 0.0

    def gauges_from_agent(self, agent: Any) -> Dict[str, float]:
        m = getattr(agent, "metrics", None)
        bal = float(getattr(m, "balance", 50.0) or 50.0)
        budget_health = max(0.0, min(1.0, bal / 100.0 if bal <= 200 else 1.0))

        token_budget = float(getattr(m, "token_budget", 100.0) or 100.0)
        tokens_used = float(getattr(m, "tokens_used", 0.0) or 0.0)
        tokens_ratio = 1.0
        if token_budget > 0:
            tokens_ratio = max(0.0, min(1.0, 1.0 - tokens_used / token_budget))

        active = float(getattr(m, "n_active_tasks", 0) or 0)
        success_rate = float(getattr(m, "success_rate", 0.5) or 0.5)

        return {
            "budget_health": budget_health,
            "tokens_remaining_ratio": tokens_ratio,
            "provider_up": 1.0,
            "no_progress_count": self._no_progress,
            "compliance_violations": self._compliance_hits,
            "queue_depth": active,
            "anomaly_score": max(0.0, 1.0 - success_rate),
        }

    def on_idle(self, agent: Any) -> Dict[str, Any]:
        self.monitor.set_status(OperationalStatus.DORMANT)
        gauges = self.gauges_from_agent(agent)
        out = self.bridge.tick(gauges, heartbeat=True)
        snap = out.get("homeostasis") or self.homeostasis.snapshot()
        return {
            "status": "IDLE_TICK",
            "reason": "No active tasks — homeostasis heartbeat (not STALL)",
            "homeostasis": snap,
            "monitor": out.get("monitor"),
            "mode": snap.get("mode") if isinstance(snap, dict) else None,
            "revision_needed": bool(snap.get("revision_needed")) if isinstance(snap, dict) else False,
            "break_loop": bool(snap.get("break_loop")) if isinstance(snap, dict) else False,
        }

    def on_status(self, status: str, agent: Any = None) -> Dict[str, Any]:
        if status == "FAILED_QUALITY_GOAL":
            self._no_progress = min(5.0, self._no_progress + 1.0)
        elif status == "SUCCESS":
            self._no_progress = 0.0
        elif status == "REJECTED_BY_COMPLIANCE":
            self._compliance_hits = min(5.0, self._compliance_hits + 1.0)

        eid = STATUS_EVENT_MAP.get(status)
        snap: Dict[str, Any] = {}
        if eid:
            snap = self.emit(eid)
        if agent is not None:
            self.sync_from_agent(agent)
        return snap or self.snapshot()

    def emit(self, event_id: str) -> Dict[str, Any]:
        return self.bridge.on_pipeline_event(event_id)

    def emit_external(self, event_id: str, agent: Any = None) -> Dict[str, Any]:
        snap = self.emit(event_id)
        if agent is not None:
            self.sync_from_agent(agent)
        return snap

    def sync_from_agent(self, agent: Any) -> None:
        g = self.gauges_from_agent(agent)
        self.monitor.background_tick(g)
        self.bridge.sync_axes_from_gauges()

    def snapshot(self) -> dict:
        return self.homeostasis.snapshot()
