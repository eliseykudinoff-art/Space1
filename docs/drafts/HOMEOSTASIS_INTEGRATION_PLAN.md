# План врезки гомеостаза и гормонального пульса

> **Дата:** 2026-08-03 · **Статус:** план (не код).
> Опора: FINAL_INDEX, MATH_v0, EVENTS, AFFECTORS; код: `orchestrator/core.py` `dispatch_full_cycle`.

## 0. Цель

Сейчас: `pop_next_task` → 12 stages / иначе **STALL**.

Нужно: heartbeat/events → pulse → motor → revision/break_loop → внешняя или **внутренняя** работа. STALL при пустой очереди не норма.

Legacy `HomeostaticRegulator` оставить рядом (лог H_legacy vs S,G,U_urge).

## 1. Новые модули

`srs/homeostasis/`: events, pulse, backlog, motor, service + YAML cold-start.
Unit-тесты симов **до** полной врезки в 12 stages.

## 2. Точки в `dispatch_full_cycle`

| Место | Врезка |
|-------|--------|
| **До Stage I** | heartbeat → step; revision_needed; pop; если нет task → **IDLE_TICK** (не STALL) |
| Stage I | OWNER.TASK_RECEIVED / EMERGENCY |
| Stage II | оси h_i; snapshot в StatusBlock (S,G,U_urge,mode,S_def) |
| Stage IV | COMPLIANCE_HIT при veto |
| Stage VIII | TOKENS_*, RATE_LIMIT, PROVIDER_WARNING, TOOL.FAIL, STEP_OK, LOOP_DETECTED |
| Stage IX | VERIFIER_FAIL |
| Stage X | NO_PROGRESS / DEAD_END / recovery STEP_OK |
| Stage XI | TASK_DONE / TASK_FAILED / PLATFORM_WARNING |
| Stage XII | step(do_slow=True); mode/L рядом с weights |

Stage III–V: 𝒟 пока не ломать; soft от mode — P2+.

## 3. Вне цикла

- Scheduler: задачи INTERNAL (revision, deferred, sandbox)
- Главный loop: tick без внешней очереди
- SystemMonitor / router health → events
- Backlog API: DEF.ITEM_ADDED/DONE

## 4. Дыры

StatusBlock не в prompt; нет loop detector; нет τ_idle; backlog persist; e2e ждут STALL; два «homeo».

## 5. Фазы

| Фаза | Суть | Критерий |
|------|------|----------|
| **P0** | Модуль + IDLE_TICK вместо STALL | snapshot в idle; e2e живы |
| **P1** | on_event/on_heartbeat по stages | цепочка событий в логе |
| **P2** | revision + INTERNAL + backlog | пустая биржа + stale rules → работа |
| **P3** | break_loop рвёт Stage VIII | искусственный loop обрывается |
| **P4** | soft mode→𝒟, StatusBlock→prompt, deprecate legacy H | подготовка к `02` |

## 6. Риски

Двойной stress PID+S; взрыв INTERNAL задач; хронический S (тесты idle); OWNER_DIRECT; слишком большие PR → только по фазам.

## 7. Не входит

Байес w_i; перепись 03; замена Γ; UI эмоций.

---
*План врезки · 2026-08-03*
