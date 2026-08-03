# План врезки гомеостаза (P0–P4)

> **Канон замысла:** `HOMEOSTASIS.md`, `MONITORING.md`.
> **Код пакета:** `srs/homeostasis/` (ещё не в orchestrator).

## Цель

pop→STALL заменить на: heartbeat/events → pulse → motor → revision/break_loop → внешняя или внутренняя работа.
Legacy HomeostaticRegulator сначала рядом (лог).

## Модули

srs/homeostasis/: events, pulse, backlog, motor, service + config.
Unit-тесты симов до полной врезки.

## Точки dispatch_full_cycle

| Место | Врезка |
|-------|--------|
| До Stage I | heartbeat, step; нет task → IDLE_TICK |
| Stage I | OWNER events |
| Stage II | h_i + snapshot в StatusBlock |
| Stage IV | COMPLIANCE_HIT |
| Stage VIII | tokens, rate, tools, STEP_OK, LOOP |
| Stage IX | VERIFIER_FAIL |
| Stage X–XI | NO_PROGRESS / TASK_DONE/FAILED |
| Stage XII | slow step |

Вне цикла: INTERNAL scheduler, SystemMonitor.subscribe→on_event, HealthChecker→Monitor, backlog API.

## Фазы

| Фаза | Суть |
|------|------|
| P0 | Модуль есть; IDLE_TICK вместо STALL |
| P1 | on_event по stages |
| P2 | revision + INTERNAL + backlog |
| P3 | break_loop рвёт Stage VIII |
| P4 | soft mode→𝒟, StatusBlock в prompt |

## Риски

Два homeo; раздувание INTERNAL; хронический S (тесты idle); e2e на STALL.

---
*План врезки · 2026-08-03*
