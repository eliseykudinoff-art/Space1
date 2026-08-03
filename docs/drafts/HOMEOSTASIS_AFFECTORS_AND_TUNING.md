# Гомеостаз: аффекторы, отложенные дела, режимы, калибровка

> **Статус:** доработка «как часы» (2026-08-03).
> Дополняет CONCEPT_CLOSED, MATH_v0, EVENTS_v0.

## 1. Два полюса (не меню работ)

| Полюс | Когда | Поведение |
|-------|--------|-----------|
| **Urgent** | Высокий S / U_urge | Срочное: тупики, лимиты, варнинги, просроченный backlog |
| **Prospective** | Низкий–средний S, живой G | Развитие, правила, sandbox, информация — не «горип прямо щас» |

Удовлетворённость ≠ sleep. При S ≥ θ_urgent приоритет urgent.

## 2. Полный набор аффекторов

1. Compute/токены/квота/rate/budget, provider health
2. Rejects, compliance, platform/security warnings
3. Тупики, no-progress, verifier, fail / progress, done
4. RPE better/worse
5. Idle/boredom (калиброванный)
6. **Backlog отложенных дел** (см. ниже)
7. Энтропия информации (устаревшие правила биржи и т.д.)
8. Tool/MCP fail, memory gap
9. Репутация / клиентские долги
10. Owner task / emergency
11. Allostatic load (slow)

**Не аффекторы пульса:** Mission сама по себе; выбор LLM; голый Φ.

### Backlog (обязательный stress)

Отложил (не отвлекаться от заказа) ≠ отменил. Возраст × важность → S_def.

Типы: INFO_RULES, INFO_MARKET, SKILL_DRILL, SANDBOX_PIPELINE, REFLECT_ERRORS, SECURITY_REVIEW, RELATIONS, TOOL_HEALTH, COST_REVIEW, OWNER_PROMISE, GENERIC.

Пример: давно не гуглил правила биржи → неопределённость → stress; хочет прозрачной среды.

s_j = v_j · sat(τ_j / T_j); S_def = clip(Σ c_def s_j, 0, S_def_max≈0.5)

U_raw = α_S S + α_D D + α_def S_def

## 3. События-дополнения

TOOL.FAIL, MEMORY.GAP, DEF.ITEM_ADDED, DEF.ITEM_DONE, DEF.ITEM_OVERDUE

## 4. Калибровка (после симов)

Проблема v1: b=0.12, λ_S=0.08 → idle S→1 (хронический stress).

Цели: idle S_eq ∈ [0.15, 0.30]; работа → prospective; кризис → urgent → спад; backlog rules → mixed раньше чистого idle.

Рекомендуемые: b=0.03–0.035, λ_S=0.12, θ_rev≈0.28, α_def=0.25–0.3, S_def_max=0.5, w_idle повышен для «сидеть нельзя» без паники.

Симы v2: idle100 S_final≈0.25; work → prospective; crisis urgent→calm; deferred rules → mixed.

## 5. Инварианты

1. Удовлетворённость → развитие, не sleep
2. Stress → urgent, в т.ч. overdue deferred
3. Отложенное стареет в stress
4. Энтропия правил — через deferred, не Mission
5. Idle не хронический max S

---
*2026-08-03*
