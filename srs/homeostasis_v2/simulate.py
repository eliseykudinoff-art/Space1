"""Simulation: Homeostasis V2 must never sleep. Run from repo root or this dir."""
from __future__ import annotations

import json
from pathlib import Path
import sys

# allow running as script from this directory
sys.path.insert(0, str(Path(__file__).resolve().parent))

from model import (
    HomeostasisV2,
    HomeostasisV2Config,
    default_state,
    apply_impulse_dynamics,
    ActionImpulse,
    ImpulseKind,
)


def snapshot_state(state) -> dict:
    return {k: round(v.current, 3) for k, v in state.items()}


def run_scenario(name: str, state, steps: int = 1, rotate: bool = False) -> dict:
    cfg = HomeostasisV2Config()
    homeo = HomeostasisV2(cfg)
    history = []
    for t in range(steps):
        if rotate:
            cfg.baseline_rotation = t
        out = homeo.step(state)
        history.append(
            {
                "t": t,
                "state": snapshot_state(state),
                "H_v2": out["H_v2"],
                "primary": out["primary"],
                "n_impulses": out["n_impulses"],
                "top3": out["impulses"][:3],
            }
        )
        if steps > 1 and out["primary"]:
            prim = ActionImpulse(
                kind=ImpulseKind(out["primary"]["kind"]),
                urgency=out["primary"]["urgency"],
                reason=out["primary"]["reason"],
                source_variable=out["primary"]["source_variable"],
            )
            apply_impulse_dynamics(state, prim, dt=1.0)
    return {"scenario": name, "history": history}


def main():
    results = {}
    s = default_state(cash=400.0, runway_months=0.4, pipeline=1.0, workload=1.0)
    results["A_crisis"] = run_scenario("A_crisis_low_cash", s, steps=1)

    s = default_state(
        cash=5000.0, runway_months=6.0, reputation=4.9, workload=3.0,
        pipeline=8.0, quality=0.95, skill=0.9,
    )
    results["B_equilibrium"] = run_scenario("B_all_targets_met", s, steps=1)

    s = default_state(
        cash=5000.0, runway_months=6.0, reputation=4.9, workload=3.0,
        pipeline=8.0, quality=0.95, skill=0.9,
    )
    results["B2_equilibrium_traj"] = run_scenario("B2_eq_trajectory", s, steps=8, rotate=True)

    s = default_state(workload=7.0, pipeline=2.0, cash=2500.0)
    results["C_overload"] = run_scenario("C_workload_overload", s, steps=1)

    s = default_state(cash=500.0, runway_months=0.5, pipeline=0.5, workload=1.0, skill=0.5)
    results["D_recovery"] = run_scenario("D_recovery_traj", s, steps=12)

    metrics = {
        "A_primary": results["A_crisis"]["history"][0]["primary"]["kind"],
        "A_has_earn": results["A_crisis"]["history"][0]["primary"]["kind"]
        in ("EARN", "BID_SAFE", "CUT_SPEND"),
        "B_n_impulses": results["B_equilibrium"]["history"][0]["n_impulses"],
        "B_primary": results["B_equilibrium"]["history"][0]["primary"]["kind"],
        "B_never_idle": results["B_equilibrium"]["history"][0]["n_impulses"] >= 1,
        "B2_all_steps_nonzero": all(
            h["n_impulses"] >= 1 for h in results["B2_equilibrium_traj"]["history"]
        ),
        "B2_kinds_seen": sorted(
            {h["primary"]["kind"] for h in results["B2_equilibrium_traj"]["history"]}
        ),
        "C_primary": results["C_overload"]["history"][0]["primary"]["kind"],
        "C_throttle": results["C_overload"]["history"][0]["primary"]["kind"]
        in ("THROTTLE_INTAKE", "FINISH_CURRENT"),
        "D_cash_start": results["D_recovery"]["history"][0]["state"]["cash"],
        "D_cash_end": results["D_recovery"]["history"][-1]["state"]["cash"],
    }
    gates = {
        "gate_crisis_financial": metrics["A_has_earn"],
        "gate_eq_not_idle": metrics["B_never_idle"],
        "gate_eq_traj_not_idle": metrics["B2_all_steps_nonzero"],
        "gate_eq_has_baseline_kinds": any(
            k in metrics["B2_kinds_seen"]
            for k in ("SCOUT_LIGHT", "LEARN", "AUDIT_RISK", "RELATE", "MAINTAIN")
        ),
        "gate_overload_throttle": metrics["C_throttle"],
        "gate_recovery_cash_up": metrics["D_cash_end"] > metrics["D_cash_start"],
    }
    metrics["gates"] = gates
    metrics["all_pass"] = all(gates.values())
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    print("ALL PASS" if metrics["all_pass"] else "SOME GATES FAILED")
    return metrics["all_pass"]


if __name__ == "__main__":
    raise SystemExit(0 if main() else 1)
