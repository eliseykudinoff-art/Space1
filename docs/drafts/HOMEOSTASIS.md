# Гомеостаз Space1 — канон черновика

> **Версия:** 1.0 · **2026-08-03** · `docs/drafts/`
> **Статус:** единственный канон темы гомеостаза в drafts.
> **Код:** `srs/homeostasis/` (не врезан).
> **Не канон:** homeostasis_v2 (отвергнут), legacy HomeostaticRegulator (пока в runtime).
> **Рядом:** `MONITORING.md`, `HOMEOSTASIS_INTEGRATION_PLAN.md`.
> Перенос в `02` — позже.

## 1. Роль

Гомеостаз — **единственный мотор жизни**. Гормоны — **пульс**. Метрики — зрение. Миссия — акценты метрик (не прямой stress). Γ — стоп-кран.

```text
События / алерты Monitor → [Гормоны S,G] → [Мотор D, U_urge, mode, break_loop]
    → ревизия → метрики + Γ + 𝒟 + LLM
```

Go / низкий S → **развитие**, не sleep. Высокий S / overdue backlog → **срочность**.

## 2. Инварианты

1. Жизнь не только от `pop_next_task`. STALL запрещён → IDLE_TICK.
2. Скука = stress (мягкий).
3. Mission ↛ S/G напрямую.
4. Нет job-types из пульса.
5. Γ_hard не заменяется.
6. Отложенные дела стареют в stress.

## 3. События → пульс

RES: TOKENS_*, BUDGET_BLOCK, RATE_LIMIT
EXT: REJECTED, COMPLIANCE_HIT, PLATFORM/PROVIDER/SECURITY_WARNING, PAYMENT_OVERDUE, DISPUTE_OPENED, REPUTATION_HIT
EXEC: NO_PROGRESS, VERIFIER_FAIL, LOOP, DEAD_END, STEP_OK, TASK_DONE/FAILED
IDLE: HEARTBEAT, QUEUE_EMPTY, NO_SIGNIFICANT_WORK
OUT: BETTER/WORSE, BLOCK_CLEARED
OWNER: TASK_RECEIVED, EMERGENCY
TOOL: FAIL, ACQ_FAIL · MEMORY: GAP · DEF: ADDED/DONE/OVERDUE
SYS: CB_OPEN, CB_GLOBAL_TRIP, HITL_TIMEOUT, A2A_VERIFY_FAIL

Не события: MISSION.CHANGED, LLM.SELECTED, PHI.RECOMPUTED.

Пересчёт: событие ∨ heartbeat ∨ существенный Δh_i.
Slow L,ρ: каждый K-й heartbeat ∨ major-аварии.

## 4. Формулы

D=Σ w_i max(0,ε_i)^p
Decay S,G; событие +a_S,a_G; boredom b(τ−τ_0)/(τ_0+τ)
S_def от backlog; U_urge=ρ(α_S S+α_D D+α_def S_def)
revision ⇔ U≥θ_rev; break_loop ⇔ trap ∨ S≥θ_break

Cold-start: b≈0.03–0.035, λ_S≈0.12, θ_rev≈0.28, S_eq idle ∈[0.15,0.30].

## 5. Аффекторы

Ресурсы · rejects/warnings · traps/progress · idle · backlog (rules, skill, sandbox, reflect, relations, tools, owner…) · entropy · tool/memory · reputation · owner · L.
Не: Mission сама; выбор LLM; голый Φ.

## 6. Выход

S, G, D, S_def, U_urge, L, ρ, revision_needed, break_loop, mode.
Не: job-type, model, bid.

## 7. Старое

H (4 ratio), Λ — log/диагностика. v2 EARN — мусор. Канон кода: `srs/homeostasis/`.

---
*Канон гомеостаза drafts · 1.0*
