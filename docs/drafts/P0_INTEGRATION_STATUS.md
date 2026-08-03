# P0 Integration status (2026-08-03)

## On `last` now
- `srs/orchestrator/life_support.py` — LifeSupport (monitor+homeostasis)
- `srs/monitoring/bridge.py` — package imports fixed
- `srs/homeostasis_v2/*` removed (rejected EARN menu)

## core.py (STALL → IDLE_TICK)
Patched locally; apply by replacing `srs/orchestrator/core.py` with workspace `orchestrator_core_p0.py` or edit:

1. `from .life_support import LifeSupport`
2. `self.life = LifeSupport()` beside legacy `self.homeo`
3. empty queue: `return self.life.on_idle(self.core_agent)` → status **IDLE_TICK**
4. compliance fail: `self.life.emit("EXT.COMPLIANCE_HIT")`
5. quality fail: `self.life.emit("EXEC.VERIFIER_FAIL")`
6. success: `self.life.emit("EXEC.TASK_DONE")` + `homeostasis` in return

## Branches (run locally — API cannot delete refs)
```bash
git push origin --delete codespace-probable-waffle-vppppr7gwgp6cpvr7
git push origin --delete 'codex/-main' codex-2q1b5l codex-15fv29 codex-m2phfa phase2-utility-functions
git fetch origin last && git push origin origin/last:clean --force
```
Keep: **main**, **drafts**, **last**, **clean**.
