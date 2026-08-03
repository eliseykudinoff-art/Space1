# Гомеостаз и гормоны — закрытие концепции

> **Статус:** концепция **закрыта** (2026-08-03).
> **Принцип:** полнота без избыточности.
> **Связка:** HOMEOSTASIS.md, EVENTS_v0, MATH_v0.

---

## 1. Суть

**Гормоны** — пульс на **события** (S/G).
**Гомеостаз** — мотор: пульс + ошибки **текущих** метрик → D, U_urge, ревизия/обрыв петли; slow — L, ρ.
**Миссия не действует на гормоны.** Миссия меняет **акценты метрик** (веса, пороги, setpoint). Если из‑за этого изменилась картина состояния → D/URGE — мотор отрабатывает как обычно.

```text
Mission → акценты метрик → h_i / w_i → D / U_urge → гомеостаз
```

Смена миссии без сдвига h_i/весов и без событий → S/G и URGE **не обязаны** меняться.

---

## 2. Два входа мотора (только они)

| Вход | Что обновляет |
|------|----------------|
| События (словарь §4) | S, G, затем шаг мотора |
| Снимок h_i | D, затем U_urge |

Нет входа «MissionChanged → stress».

---

## 3. Когда пересчитывать (закрыто)

**Шаг** = decay → event amplitudes → boredom (heartbeat) → h_i → D → (slow) L,ρ → U_urge → flags → (исход) δ.

| Триггер | S,G | D | U_urge | L,ρ | δ |
|---------|-----|---|--------|-----|---|
| Событие из §4 | да | да | да | по §3.3 | если исход |
| Heartbeat | decay+boredom | да | да | по §3.3 | нет |
| Существенный Δh_i или смена весов/setpoint (в т.ч. от миссии) | нет | да | да | по §3.3 | нет |

**Существенный Δh_i:** |Δh_i| > ε_i или смена w_i/setpoint. Иначе микро-тики метрик шаг не обязаны.

**Slow:** каждый K-й heartbeat **или** сразу после major: LOOP, DEAD_END, TASK_FAILED, COMPLIANCE_HIT, SECURITY_WARNING, TOKENS_EXHAUSTED, BUDGET_BLOCK, OWNER.EMERGENCY.

**Не триггеры:** смена Mission сама по себе; выбор LLM; каждая строка лога; soft Γ без hit; пересчёт Φ/U/VoI; OWNER без emergency (кроме TASK_RECEIVED как event).

---

## 4. Словарь событий (закрыт для v0)

**RES:** TOKENS_EXHAUSTED, TOKENS_LOW, BUDGET_BLOCK, RATE_LIMIT

**EXT:** ORDER_REJECTED, PROPOSAL_REJECTED, COMPLIANCE_HIT, PLATFORM_WARNING, PROVIDER_WARNING, SECURITY_WARNING

**EXEC:** NO_PROGRESS, VERIFIER_FAIL, LOOP_DETECTED, DEAD_END, STEP_OK, TASK_DONE, TASK_FAILED

**IDLE:** HEARTBEAT (обязателен), QUEUE_EMPTY, NO_SIGNIFICANT_WORK (скука в основном через τ_idle на heartbeat)

**OUT:** BETTER_THAN_EXPECTED, WORSE_THAN_EXPECTED, BLOCK_CLEARED

**OWNER:** TASK_RECEIVED, EMERGENCY

**Не события:** MISSION.CHANGED, LLM.SELECTED, PHI.RECOMPUTED.

---

## 5. Оси h_i (минимум v0)

resource, runway, compliance_exposure, competence, reputation, workload (band), progress_debt, idle_time.

Веса/setpoint могут зависеть от Mission. Гормоны видят результат через D и события.

---

## 6. Выходы

S, G, D, U_urge, L, ρ, revision_needed, break_loop, (δ).
Не: job-type, specialist, model, bid, Φ.

---

## 7. Инварианты

1. Нет события и нет существенного Δh → нет обязанности менять S/G.
2. Mission ↛ S/G напрямую.
3. Скука: heartbeat + τ_idle.
4. Γ_hard не заменяется пульсом.
5. Формулы — MATH_v0; здесь — без дыр по «когда/от чего».

---

## 8. Не дыры, а следующие этапы

Калибровка амплитуд, код, привязка к Stage I–XII, перенос в 02, байес по w_i.

---

## 9. Чеклист закрытия

Роли; Mission через метрики; словарь событий; таблица триггеров; не-триггеры; оси h_i; slow-правило; выходы; MATH; скука.

---

*Концепция закрыта · 2026-08-03*
