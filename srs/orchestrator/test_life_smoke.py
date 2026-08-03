"""Smoke: LifeSupport idle path. python srs/orchestrator/test_life_smoke.py"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# import submodules directly — avoid srs/__init__.py (space1 alias deps)
from srs.homeostasis.service import HomeostasisService  # noqa: E402
from srs.homeostasis.config import HomeostasisConfig  # noqa: E402
from srs.monitoring.monitor import SystemMonitor, OperationalStatus  # noqa: E402
from srs.monitoring.bridge import MonitorHomeostasisBridge  # noqa: E402


def main() -> None:
    cfg = HomeostasisConfig()
    homeo = HomeostasisService(cfg)
    mon = SystemMonitor()
    bridge = MonitorHomeostasisBridge(mon, homeo)

    mon.set_status(OperationalStatus.DORMANT)
    out = bridge.tick(
        {
            "budget_health": 0.5,
            "tokens_remaining_ratio": 0.8,
            "provider_up": 1.0,
            "no_progress_count": 0.0,
        },
        heartbeat=True,
    )
    snap = out["homeostasis"]
    assert isinstance(snap, dict), snap
    assert 0.0 <= float(snap["S"]) <= 1.0
    assert snap.get("break_loop") is False

    bridge.on_pipeline_event("EXEC.TASK_DONE")
    snap2 = homeo.snapshot()
    assert "S" in snap2 or "pulse" in snap2

    # idle payload shape (as life_support.on_idle)
    payload = {
        "status": "IDLE_TICK",
        "homeostasis": snap,
        "mode": snap.get("mode"),
    }
    assert payload["status"] == "IDLE_TICK"
    print("SMOKE OK", "S=", snap["S"], "mode=", snap.get("mode"))


if __name__ == "__main__":
    main()
