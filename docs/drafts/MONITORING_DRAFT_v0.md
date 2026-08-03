# MONITORING_DRAFT_v0 — Мониторинг под гомеостаз (черновик)

> **Дата:** 2026-08-03 · **Статус:** черновик наблюдения; не код, не замена `02`.
> **Принцип:** ни одному источнику не верить слепо.

### Источники сверки

| Источник | Взяли | Не поверили вслепую |
|----------|-------|---------------------|
| ARCHIVE/SYSTEM_MONITORING.md | M001–M047, DORMANT…, частоты | алерты≠действия; ratio=Λ не наш пульс |
| 05 §VII | OperationalStatus ⊥ StrategicPosture | не полный sensor list |
| 06 | PlatformRiskScore | нет в архивном SYSTEM_MONITORING |
| 10_SECURITY | Anomaly → StatusBlock | не авто-стоп |
| HOMEOSTASIS_* | S/G, motor, EventID | канон мотора |
| monitoring.py | факт runtime | 3 порога, нет loop |
| 01 OWNER/emergency | приоритет | почти нет в SYSTEM_MONITORING |

## 1. Роль

Monitor = факты + thresholds + alerts → гормоны (пульс) → мотор (URGE).
Monitor **не** мотор и не меню работ. `stress_level` ≠ гормональный S.

## 2. Три ортогональных режима

- OperationalStatus: DORMANT/ACTIVE/RECOVERING/SUSPENDED
- StrategicPosture: derive(H|D, Mission)
- HormoneMode: calm/mixed/urgent/prospective

STALL запрещён; DORMANT + IDLE_TICK + heartbeat.

## 3. Шины

Gauge (период) → порог → Alert → EventID или только h_i.
Event (stage/router/Γ/owner) → сразу on_event; Monitor логирует counter.
subscribe → HomeostasisService.

## 4. Реестр сигналов (сверка)

**Arch есть, code почти нет:** memory/skill/budget/queue health, tokens, rate limit, staleness, decay, order_flow, deadlock, compliance as monitor series.

**Упущено архивом SYSTEM_MONITORING, требуется концепцией:**
PlatformRiskScore (06); τ_idle; deferred backlog; OWNER/EMERGENCY; INTERNAL queue; anomaly (10); circuit breaker; security warning; sandbox/reflect debt; token quota vs $; STALL metric.

**HealthChecker LLM** — есть, не в Monitor. **MetricRegistry** — EMA, не alerts.

## 5. Alert → EventID (норматив)

budget critical → RES.BUDGET_BLOCK; tokens → RES.TOKENS_*; rate/provider → RES.RATE_LIMIT / EXT.PROVIDER_WARNING; compliance → EXT.COMPLIANCE_HIT; PlatformRisk critical → EXT.PLATFORM_WARNING; deadlock → EXEC.LOOP/NO_PROGRESS; verifier → VERIFIER_FAIL; tool → TOOL.FAIL; memory → MEMORY.GAP; staleness/decay → DEF.*; security → EXT.SECURITY_WARNING; owner emergency → OWNER.EMERGENCY.

## 6. Каденция

DORMANT: 30–60s heartbeat + heavier 5–60min.
ACTIVE: 10–30s + on stage events.
RECOVERING: 10–30s focus.
SUSPENDED: basic + HITL only.

Background loop — обязанность Monitor (в архиве был, в коде нет).

## 7. MVP среза

1. OperationalStatus + IDLE_TICK
2. Gauges: budget/tokens, queue, τ_idle, compliance, provider, no-progress
3. map §5 minimal
4. subscribe → homeostasis
5. background ≥ heartbeat
6. PlatformRisk stub
7. backlog age tick

## 8. Не входит

job-type, Φ/U/VoI, замена Γ, Mission→stress, UI.

## 9. Открытые

Пороги PRS; anomaly в MVP?; Monitor vs Registry store; owner background process.

---
*MONITORING_DRAFT_v0 · 2026-08-03*
