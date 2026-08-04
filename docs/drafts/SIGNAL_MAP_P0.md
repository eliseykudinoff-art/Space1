# Signal map P0 — что двигает действие (clean2)

Аудит `srs/orchestrator/core.py` + LifeAware-обёртка.

## Источники сигнала (до / после P0)

| Источник | Было | Сейчас (LifeAware) | Событие гомеостаза |
|----------|------|--------------------|--------------------|
| Пустая очередь scheduler | **STALL** (core L645) | **IDLE_TICK** (list_queue → life.on_idle) | IDLE.HEARTBEAT + boredom |
| SUCCESS (stage XII) | legacy `HomeostaticRegulator.update_all` | + `EXEC.TASK_DONE` + sync gauges | G↑ S↓ |
| REJECTED_BY_COMPLIANCE (×2) | только trace | `EXT.COMPLIANCE_HIT` | S↑ |
| DECLINED_BY_DECISION_RULE | только trace | `EXT.ORDER_REJECTED` | S↑ |
| CLARIFY_REQUIRED | только trace | `MEMORY.GAP` | S↑ |
| FAILED_QUALITY_GOAL | только trace | `EXEC.VERIFIER_FAIL` | S↑ |
| Stage XII stress>0.6 | mission_recalibrated flag | snapshot life + legacy pressures в result | (оси через gauges) |
| SignalToContextSynthesizer | legacy regulator pressures | **ещё legacy** | gap |
| WeightCalibrator | legacy pressures | **ещё legacy** | gap |
| Tool / MCP fail | нет единого status | **частично** via `Orchestrator.notify` | `TOOL.FAIL` |
| Tokens / rate limit | нет status return | gauges tokens_remaining_ratio | emit RES.* via notify |
| Payment / dispute | protocol escalate в trace | auto `EXT.PAYMENT_OVERDUE` if trace matches | S↑ |
| OWNER_EMERGENCY | не в dispatch | via `notify("OWNER.EMERGENCY")` | S↑ |
| Deferred backlog aging | нет | service.defer + idle age | S_def |

## Единственный публичный вход

`from space1.orchestrator import Orchestrator` → `life_orchestrator.Orchestrator`.

Прямой `core.Orchestrator` сохраняет STALL (legacy / тесты).

## API

- `dispatch_full_cycle()` — idle → IDLE_TICK; иначе pipeline + events
- `notify(event_id)` — внешние системы (router, protocols, owner)

## Следующие щели (P0.1)

1. SignalToContext + WeightCalibrator читать S/axes из life
2. Router/cost → notify RES.* / TOOL.FAIL
3. Deprecate STALL в core (one-line)
4. OWNER path в admission
