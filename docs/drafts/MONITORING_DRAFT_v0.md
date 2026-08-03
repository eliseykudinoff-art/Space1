# MONITORING_DRAFT_v0 — Мониторинг под гомеостаз (черновик)

> **Дата:** 2026-08-03 · обновление: перепроверка 06/09/10.
> Monitor = факты + alerts → гормоны → мотор. Не меню работ. STALL запрещён.

## Роль и режимы

OperationalStatus (DORMANT/ACTIVE/RECOVERING/SUSPENDED) ⊥ StrategicPosture ⊥ HormoneMode.
stress_level ≠ гормональный S.

## Реестр (сводка + дельта 06/09/10)

### Уже из SYSTEM_MONITORING / гомеостаза
memory/skill/budget/queue health; tokens; rate limit; staleness; decay; deadlock; compliance; τ_idle; deferred backlog; OWNER/EMERGENCY; provider health.

### Добавлено после 06
- payment overdue → EXT.PAYMENT_OVERDUE / спор
- DISPUTE_OPENED + open_disputes counter
- PlatformRiskScore + account suspend → SUSPENDED + Γ no new account
- off-platform channel / IP-geo consistency → PRS / compliance
- median_bid dump → market gauge
- REPUTATION_HIT

### Добавлено после 09
- Trust(e), ToolScore.reliability series
- Tool acquisition sandbox/test fail
- Typed DSL typecheck fail (counter / rework)
- MCP fail (TOOL.FAIL); A2A card verify fail; AP2 payment error

### Добавлено после 10
- Circuit breaker task OPEN (уже в коде — в Monitor!)
- **Global circuit** (H, platform_risk, session_open_ratio) → stop intake + status
- Anomaly score → StatusBlock + HITL, **не** авто S=1
- Audit log health; memory contradiction flag; HITL_TIMEOUT

### Одна шина
06 PlatformRiskScore и 10 anomaly/CB — один Monitor, разные подписчики (hormones / StatusBlock / stop-intake).

## Alert → Event (дополнение)

PAYMENT_OVERDUE, DISPUTE_OPENED, REPUTATION_HIT, TOOL.ACQ_FAIL, A2A_VERIFY_FAIL, CB_OPEN / CB_GLOBAL_TRIP, HITL_TIMEOUT, EXT.SECURITY_WARNING.

## MVP срез (расширенный)

1. OperationalStatus + IDLE_TICK
2. budget/tokens, queue, τ_idle, compliance, provider, no-progress
3. map alerts → events + subscribe → HomeostasisService
4. background heartbeat
5. PlatformRisk stub + global CB state
6. backlog age
7. dispute/payment overdue hooks when protocols live

## Не в пульс автоматически

anomaly (только StatusBlock/HITL); daily finance KPI без CRITICAL; Mission change.

---
*MONITORING_DRAFT_v0 · recheck 06/09/10 · 2026-08-03*
