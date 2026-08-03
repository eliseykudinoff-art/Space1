"""Smoke test without srs package __init__ (space1 alias)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYS_HOME = ROOT / "srs" / "homeostasis"
SYS_MON = ROOT / "srs" / "monitoring"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    # order: leaf modules first
    events = _load("h_events", SYS_HOME / "events.py")
    config = _load("h_config", SYS_HOME / "config.py")
    pulse = _load("h_pulse", SYS_HOME / "pulse.py")
    backlog = _load("h_backlog", SYS_HOME / "backlog.py")
    motor = _load("h_motor", SYS_HOME / "motor.py")
    # service imports relatives — inject package-like names
    sys.modules["srs"] = type(sys)("srs")
    sys.modules["srs.homeostasis"] = type(sys)("srs.homeostasis")
    sys.modules["srs.homeostasis.events"] = events
    sys.modules["srs.homeostasis.config"] = config
    sys.modules["srs.homeostasis.pulse"] = pulse
    sys.modules["srs.homeostasis.backlog"] = backlog
    sys.modules["srs.homeostasis.motor"] = motor

    # re-bind relative imports used inside service
    import types
    pkg = types.ModuleType("srs.homeostasis")
    pkg.events = events
    pkg.config = config
    pkg.pulse = pulse
    pkg.backlog = backlog
    pkg.motor = motor
    sys.modules["srs.homeostasis"] = pkg

    # service uses relative imports from .config etc — load as package member
    service_path = SYS_HOME / "service.py"
    spec = importlib.util.spec_from_file_location(
        "srs.homeostasis.service", service_path,
        submodule_search_locations=[str(SYS_HOME)],
    )
    service_mod = importlib.util.module_from_spec(spec)
    sys.modules["srs.homeostasis.service"] = service_mod
    # fake package for relative imports
    service_mod.__package__ = "srs.homeostasis"
    spec.loader.exec_module(service_mod)

    mon_mod = _load("srs.monitoring.monitor", SYS_MON / "monitor.py")
    mon_mod.__package__ = "srs.monitoring"
    sys.modules["srs.monitoring"] = types.ModuleType("srs.monitoring")
    sys.modules["srs.monitoring.monitor"] = mon_mod

    bridge_path = SYS_MON / "bridge.py"
    bspec = importlib.util.spec_from_file_location(
        "srs.monitoring.bridge", bridge_path,
        submodule_search_locations=[str(SYS_MON)],
    )
    bridge_mod = importlib.util.module_from_spec(bspec)
    bridge_mod.__package__ = "srs.monitoring"
    sys.modules["srs.monitoring.bridge"] = bridge_mod
    bspec.loader.exec_module(bridge_mod)

    HomeostasisService = service_mod.HomeostasisService
    HomeostasisConfig = config.HomeostasisConfig
    SystemMonitor = mon_mod.SystemMonitor
    OperationalStatus = mon_mod.OperationalStatus
    MonitorHomeostasisBridge = bridge_mod.MonitorHomeostasisBridge

    homeo = HomeostasisService(HomeostasisConfig())
    mon = SystemMonitor()
    bridge = MonitorHomeostasisBridge(mon, homeo)
    mon.set_status(OperationalStatus.DORMANT)
    out = bridge.tick(
        {"budget_health": 0.5, "tokens_remaining_ratio": 0.8, "provider_up": 1.0, "no_progress_count": 0.0},
        heartbeat=True,
    )
    snap = out["homeostasis"]
    assert 0.0 <= float(snap["S"]) <= 1.0
    bridge.on_pipeline_event("EXEC.TASK_DONE")
    print("SMOKE OK", "S=", snap["S"], "mode=", snap.get("mode"))


if __name__ == "__main__":
    main()
