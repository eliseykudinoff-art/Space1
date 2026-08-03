"""Smoke: LifeSupport + idle path. Run: python -m srs.orchestrator.test_life_smoke"""
from __future__ import annotations

import sys
from pathlib import Path

# allow running from repo root
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    from srs.orchestrator.life_support import LifeSupport

    class _M:
        balance = 50.0
        n_active_tasks = 0

    class _A:
        metrics = _M()

    life = LifeSupport()
    out = life.on_idle(_A())
    assert out["status"] == "IDLE_TICK", out
    assert "homeostasis" in out, out
    snap = out["homeostasis"]
    assert isinstance(snap, dict), type(snap)
    assert 0.0 <= float(snap.get("S", 0)) <= 1.0
    assert out.get("break_loop") is False or out.get("break_loop") is None

    life.emit("EXEC.TASK_DONE")
    s2 = life.snapshot()
    assert "S" in s2 or "pulse" in s2

    print("SMOKE OK", "status=", out["status"], "S=", snap.get("S"), "mode=", snap.get("mode"))


if __name__ == "__main__":
    main()
