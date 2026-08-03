"""Integration tests Monitor ↔ Homeostasis. python test_integration.py"""
from __future__ import annotations
import math, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "homeostasis"))
sys.path.insert(0, str(ROOT / "monitoring"))
from config import HomeostasisConfig
from service import HomeostasisService
from monitor import OperationalStatus, SystemMonitor, map_alert_to_event
from bridge import MonitorHomeostasisBridge

def make_pair():
    overrides = {
        "EXT.PAYMENT_OVERDUE": (0.35, 0.0), "EXT.DISPUTE_OPENED": (0.40, 0.0),
        "EXT.REPUTATION_HIT": (0.35, 0.0), "SYS.CB_OPEN": (0.45, 0.0),
        "SYS.CB_GLOBAL_TRIP": (0.70, 0.0), "SYS.HITL_TIMEOUT": (0.30, 0.0),
    }
    homeo = HomeostasisService(HomeostasisConfig(amplitude_overrides=overrides))
    mon = SystemMonitor()
    return MonitorHomeostasisBridge(mon, homeo), mon, homeo

def assert_true(c, m):
    if not c: raise AssertionError(m)

def test_anomaly_does_not_spike_hormones():
    b, mon, h = make_pair()
    s0 = h.pulse.state.S
    mon.record("anomaly_score", 5.0)
    assert_true(h.pulse.state.S == s0, "anomaly must not change S")
    print("OK anomaly")

def test_budget_critical():
    b, mon, h = make_pair()
    b.tick({"budget_health": 0.10, "tokens_remaining_ratio": 0.5})
    assert_true(h.pulse.state.S > 0.4, f"S={h.pulse.state.S}")
    print("OK budget")

def test_dedupe():
    b, mon, h = make_pair()
    b.tick({"budget_health": 0.10})
    n1 = b.events_forwarded
    b.tick({"budget_health": 0.10})
    assert_true(b.events_forwarded == n1, "dedupe")
    print("OK dedupe")

def test_recovery():
    b, mon, h = make_pair()
    b.tick({"budget_health": 0.10})
    b.tick({"budget_health": 0.9, "tokens_remaining_ratio": 0.9})
    b.on_pipeline_event("OUT.BLOCK_CLEARED")
    b.on_pipeline_event("EXEC.TASK_DONE")
    for _ in range(5):
        b.tick({"budget_health": 0.9, "tokens_remaining_ratio": 0.9})
    assert_true(h.pulse.state.S < 0.35, f"S={h.pulse.state.S}")
    print("OK recovery")

def test_idle():
    b, mon, h = make_pair()
    mon.set_status(OperationalStatus.DORMANT)
    for _ in range(80):
        b.tick({"budget_health": 0.8, "tokens_remaining_ratio": 0.8, "no_progress_count": 0})
    assert_true(h.pulse.state.S < 0.55, f"chronic S={h.pulse.state.S}")
    print("OK idle", h.pulse.state.S)

def test_loop():
    b, mon, h = make_pair()
    mon.set_status(OperationalStatus.ACTIVE)
    b.tick({"no_progress_count": 6, "budget_health": 0.7})
    assert_true(h.last_snapshot.break_loop, "break_loop")
    assert_true(mon.status == OperationalStatus.RECOVERING, str(mon.status))
    b.on_pipeline_event("EXEC.TASK_DONE")
    assert_true(mon.status == OperationalStatus.ACTIVE, "back ACTIVE")
    print("OK loop")

def test_global_cb():
    b, mon, h = make_pair()
    mon.set_status(OperationalStatus.ACTIVE)
    b.tick({"global_circuit_trip": 1.0, "budget_health": 0.8})
    assert_true(mon.status == OperationalStatus.SUSPENDED, str(mon.status))
    print("OK global_cb")

def test_work():
    b, mon, h = make_pair()
    mon.set_status(OperationalStatus.ACTIVE)
    for t in range(20):
        if (t+1) % 5 == 0: b.on_pipeline_event("EXEC.STEP_OK")
        if (t+1) % 10 == 0: b.on_pipeline_event("EXEC.TASK_DONE")
        b.tick({"budget_health": 0.85, "tokens_remaining_ratio": 0.8, "no_progress_count": 0})
    assert_true(h.last_snapshot.S < 0.25, str(h.last_snapshot.S))
    assert_true(h.last_snapshot.mode in ("prospective", "calm"), h.last_snapshot.mode)
    print("OK work", h.last_snapshot.mode)

def test_crisis():
    b, mon, h = make_pair()
    mon.set_status(OperationalStatus.ACTIVE)
    b.tick({"tokens_remaining_ratio": 0.02, "no_progress_count": 6, "provider_up": 0.0, "budget_health": 0.5})
    peak = h.pulse.state.S
    assert_true(peak > 0.7, str(peak))
    b.on_pipeline_event("OUT.BLOCK_CLEARED")
    for _ in range(3): b.on_pipeline_event("EXEC.STEP_OK")
    b.on_pipeline_event("EXEC.TASK_DONE")
    for _ in range(15):
        b.tick({"tokens_remaining_ratio": 0.8, "no_progress_count": 0, "provider_up": 1.0, "budget_health": 0.85})
    assert_true(h.pulse.state.S < 0.4, str(h.pulse.state.S))
    print("OK crisis", peak, "->", h.pulse.state.S)

def main():
    tests = [test_anomaly_does_not_spike_hormones, test_budget_critical, test_dedupe, test_recovery,
             test_idle, test_loop, test_global_cb, test_work, test_crisis]
    failed = []
    for t in tests:
        try: t()
        except Exception as e:
            failed.append((t.__name__, e)); print("FAIL", t.__name__, e)
    print(f"\npassed {len(tests)-len(failed)}/{len(tests)}")
    if failed: sys.exit(1)
    print("All OK")

if __name__ == "__main__":
    main()
