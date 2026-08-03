# srs/homeostasis (clean2)

Pulse (S/G) + motor (D/U/L) + backlog. Wired via:

- `srs/orchestrator/life_support.py`
- `srs/orchestrator/life_orchestrator.py` (public Orchestrator)
- `srs/monitoring/` (gauges → alerts → events)

Empty scheduler queue → **IDLE_TICK**, not STALL.

```bash
python -m srs.orchestrator.test_life_smoke
```
