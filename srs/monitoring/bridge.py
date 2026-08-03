"""Bridge: SystemMonitor alerts → HomeostasisService."""
from __future__ import annotations
import sys
from pathlib import Path
from typing import TYPE_CHECKING

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "homeostasis"))
sys.path.insert(0, str(_ROOT / "monitoring"))

from monitor import Alert, AlertLevel, OperationalStatus, SystemMonitor

if TYPE_CHECKING:
    from service import HomeostasisService

class MonitorHomeostasisBridge:
    def __init__(self, monitor: SystemMonitor, homeo: "HomeostasisService"):
        self.monitor = monitor
        self.homeo = homeo
        self.events_forwarded = 0
        self.events_skipped = 0
        self.monitor.subscribe(self._on_alert)

    def _on_alert(self, alert: Alert) -> None:
        eid = alert.event_id
        if not eid:
            self.events_skipped += 1
            return
        self.homeo.on_event(eid)
        self.events_forwarded += 1
        if eid == "SYS.CB_GLOBAL_TRIP":
            self.monitor.set_status(OperationalStatus.SUSPENDED)
        elif eid in ("EXEC.LOOP_DETECTED", "EXEC.DEAD_END") and self.monitor.status == OperationalStatus.ACTIVE:
            self.monitor.set_status(OperationalStatus.RECOVERING)

    def sync_axes_from_gauges(self) -> None:
        g = self.monitor.snapshot()["gauges"]
        axes = {}
        bh, tr = g.get("budget_health"), g.get("tokens_remaining_ratio")
        if bh is not None or tr is not None:
            parts = [1.0 - x for x in (bh, tr) if x is not None]
            axes["resource"] = max(0.0, min(1.0, sum(parts) / len(parts)))
        np_ = g.get("no_progress_count")
        if np_ is not None:
            axes["progress"] = max(0.0, min(1.0, float(np_) / 5.0))
        cv = g.get("compliance_violations")
        if cv is not None:
            axes["compliance"] = max(0.0, min(1.0, float(cv) / 3.0))
        if axes:
            self.homeo.update_axes(**axes)

    def tick(self, gauges: dict, *, heartbeat: bool = True) -> dict:
        if self.monitor.status == OperationalStatus.SUSPENDED and heartbeat:
            fired = self.monitor.background_tick(gauges)
            self.sync_axes_from_gauges()
            snap = self.homeo.step()
            return self._pack(fired, snap, False)
        # heartbeat first; alerts last so trap/break_loop not wiped
        if heartbeat:
            self.homeo.on_heartbeat()
        fired = self.monitor.background_tick(gauges)
        self.sync_axes_from_gauges()
        snap = self.homeo.last_snapshot or self.homeo.step()
        return self._pack(fired, snap, heartbeat)

    def _pack(self, fired, snap, heartbeat):
        return {
            "monitor": self.monitor.snapshot(),
            "homeostasis": snap.to_dict() if hasattr(snap, "to_dict") else snap,
            "fired_alerts": [a.to_dict() for a in fired],
            "bridge": {"forwarded": self.events_forwarded, "skipped": self.events_skipped},
            "heartbeat": heartbeat,
        }

    def on_pipeline_event(self, event_id: str) -> dict:
        snap = self.homeo.on_event(event_id)
        if event_id in ("EXEC.STEP_OK", "EXEC.TASK_DONE"):
            if self.monitor.status == OperationalStatus.RECOVERING:
                self.monitor.set_status(OperationalStatus.ACTIVE)
            self.monitor.clear_alert_latch("no_progress_count")
            self.monitor.record("no_progress_count", 0.0, emit=False)
        return snap.to_dict()
