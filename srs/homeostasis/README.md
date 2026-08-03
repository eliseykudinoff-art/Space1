# srs/homeostasis — potential branch (not wired)

Hormone **pulse** (S/G) + homeostasis **motor** (D, U_urge, mode, backlog).

Canonical docs: `docs/drafts/HOMEOSTASIS_*.md`, integration: `HOMEOSTASIS_INTEGRATION_PLAN.md`.

**Not** the same as:
- `srs.utility.control.HomeostaticRegulator` (legacy H)
- `srs.homeostasis_v2` (EARN menu experiment)

## Quick demo

```bash
cd srs/homeostasis && python demo_sim.py
```

## Facade

```python
from srs.homeostasis import HomeostasisService, EventID  # after package install path
# or from service import HomeostasisService when cwd is this folder

svc = HomeostasisService()
svc.on_heartbeat()
svc.on_event("EXEC.LOOP_DETECTED")
snap = svc.last_snapshot
svc.idle_tick()  # future STALL replacement
svc.defer("INFO_RULES", importance=0.8, soft_deadline=12.0)
```

## Integration

Orchestrator still uses STALL. Wire-up is P0+ in INTEGRATION_PLAN.
