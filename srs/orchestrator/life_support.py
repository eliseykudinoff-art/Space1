"""LifeSupport — homeostasis + monitoring integration (P0)."""
from __future__ import annotations
from typing import Any, Dict, Optional
from ..homeostasis.service import HomeostasisService
from ..homeostasis.config import HomeostasisConfig
from ..monitoring.monitor import SystemMonitor, OperationalStatus
from ..monitoring.bridge import MonitorHomeostasisBridge

class LifeSupport:
    def __init__(self, config: Optional[HomeostasisConfig] = None):
        overrides = {
            "EXT.PAYMENT_OVERDUE": (0.35, 0.0),
            "EXT.DISPUTE_OPENED": (0.40, 0.0),
            "EXT.REPUTATION_HIT": (0.35, 0.0),
            "SYS.CB_OPEN": (0.45, 0.0),
            "SYS.CB_GLOBAL_TRIP": (0.70, 0.0),
            "SYS.HITL_TIMEOUT": (0.30, 0.0),
        }
        cfg = config or HomeostasisConfig(amplitude_overrides=overrides)
        self.homeostasis = HomeostasisService(cfg)
        self.monitor = SystemMonitor()
        self.bridge = MonitorHomeostasisBridge(self.monitor, self.homeostasis)

    def gauges_from_agent(self, agent: Any) -> Dict[str, float]:
        m = getattr(agent, "metrics", None)
        bal = float(getattr(m, "balance", 50.0) or 50.0)
        budget_health = max(0.0, min(1.0, bal / 100.0))
        active = float(getattr(m, "n_active_tasks", 0) or 0)
        return {
            "budget_health": budget_health,
            "tokens_remaining_ratio": 0.8,
            "provider_up": 1.0,
            "no_progress_count": 0.0,
            "compliance_violations": 0.0,
            "queue_depth": active,
            "anomaly_score": 0.0,
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
            "revision_needed": snap.get("revision_needed") if isinstance(snap, dict) else False,
            "break_loop": snap.get("break_loop") if isinstance(snap, dict) else False,
        }

    def emit(self, event_id: str) -> Dict[str, Any]:
        return self.bridge.on_pipeline_event(event_id)

    def sync_from_agent(self, agent: Any) -> None:
        g = self.gauges_from_agent(agent)
        self.monitor.background_tick(g)
        self.bridge.sync_axes_from_gauges()

    def snapshot(self) -> dict:
        return self.homeostasis.snapshot()
