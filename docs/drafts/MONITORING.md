# Мониторинг Space1 — канон черновика (под гомеостаз)

> **Версия:** 1.0 · **2026-08-03**
> **Сверка:** ARCHIVE/SYSTEM_MONITORING, 05, 06, 09, 10, HOMEOSTASIS, runtime monitoring.py
> **Рядом:** `HOMEOSTASIS.md`, `HOMEOSTASIS_INTEGRATION_PLAN.md`

## 1. Роль

```text
Сенсоры / stages / external → Monitor (record, thresholds, alerts, OperationalStatus)
    → subscribe → Homeostasis.on_event + h_i
    → (StatusBlock / HITL / stop-intake)
```

Monitor **не** мотор. stress_level ≠ гормональный S.

## 2. Режимы

OperationalStatus: DORMANT / ACTIVE / RECOVERING / SUSPENDED
StrategicPosture: derive(H|D, Mission)
HormoneMode: calm / mixed / urgent / prospective

STALL запрещён → DORMANT + IDLE_TICK + heartbeat.

## 3. Сигналы (минимум)

**Внутренние:** budget/tokens, queue, τ_idle, memory/skill health, staleness, skill_decay, progress/no-progress, deadlock, compliance, backlog age, CB task/global, HITL timeout, audit log health.

**06:** PlatformRiskScore, account suspend, payment overdue, dispute opened, off-channel, IP-geo consistency, median_bid dump, reputation hit, provider health.

**09:** Trust(e), ToolScore.reliability, tool acquisition fail, MCP fail, A2A verify fail, AP2 error, DSL typecheck counter.

**10:** anomaly → StatusBlock+HITL (не авто-S); global CB → stop intake; memory contradiction.

## 4. Alert → Event

budget/tokens → RES.*
rate/provider → RATE_LIMIT / PROVIDER_WARNING
compliance → COMPLIANCE_HIT
PRS/suspend → PLATFORM_WARNING + SUSPENDED
deadlock → LOOP / NO_PROGRESS
verifier/tool → VERIFIER_FAIL / TOOL.FAIL
payment/dispute/reputation → PAYMENT_OVERDUE / DISPUTE_OPENED / REPUTATION_HIT
CB → CB_OPEN / CB_GLOBAL_TRIP
HITL timeout → HITL_TIMEOUT
security → SECURITY_WARNING

INFO → log only.

## 5. Каденция

DORMANT 30–60s + heavier 5–60min · ACTIVE 10–30s + events · RECOVERING 10–30s · SUSPENDED basic+HITL.
Background loop обязателен (в runtime нет).

## 6. MVP

1. OperationalStatus + IDLE_TICK
2. Gauges: budget/tokens, queue, τ_idle, compliance, provider, no-progress
3. map §4 + subscribe → homeostasis
4. background heartbeat
5. PRS stub + global CB state
6. backlog age
7. dispute/payment hooks when live

## 7. Код сейчас

3 порога, нет loop/subscribe, STALL, HealthChecker и Registry изолированы.

---
*Канон мониторинга drafts · 1.0*
