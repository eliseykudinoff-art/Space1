# HOMEOSTASIS_EVENTS_v0 — Словарь событий → гормональный пульс

> **Статус:** черновик контракта (2026-08-03).
> **Назначение:** какие события **обязаны** обновлять гормональный фон.
> **Не содержит:** полных формул, выбора LLM, job-types.
> **Родитель:** `HOMEOSTASIS.md`.

---

## 1. Зачем

Гормоны — пульс реакции на события. Без словаря нечего обновлять в фоне.

v0 фиксирует: ID события, каналы stress/go, характер (spike/raise/lower/sustain), источник.
Коэффициенты — позже.

---

## 2. Каналы

| Канал | Смысл |
|-------|--------|
| **stress** | Жжёт: лимиты, отказы, тупики, **скука**. Тормоз бесконечных петель. |
| **go** | Тяга: прогресс, снятие блока, удачный исход. Не начисление $. |

---

## 3. Словарь

### 3.1 Ресурсы

| ID | Событие | stress | go |
|----|---------|--------|-----|
| `RES.TOKENS_EXHAUSTED` | Токены/квота исчерпаны | spike↑ | — |
| `RES.TOKENS_LOW` | Токены ниже порога | raise↑ | — |
| `RES.BUDGET_BLOCK` | Блок из‑за бюджета | spike↑ | — |
| `RES.RATE_LIMIT` | Rate limit | raise↑ | — |

### 3.2 Внешние отказы и регламент

| ID | Событие | stress | go |
|----|---------|--------|-----|
| `EXT.ORDER_REJECTED` | Отказ заказа | raise↑ | — |
| `EXT.PROPOSAL_REJECTED` | Отклонена заявка | raise↑ | — |
| `EXT.COMPLIANCE_HIT` | Γ / policy | spike↑ | — |
| `EXT.PLATFORM_WARNING` | Варнинг платформы | raise/spike↑ | — |
| `EXT.PROVIDER_WARNING` | Варнинг LLM-провайдера | raise/spike↑ | — |
| `EXT.SECURITY_WARNING` | Security warning | spike↑ | — |

### 3.3 Исполнение

| ID | Событие | stress | go |
|----|---------|--------|-----|
| `EXEC.NO_PROGRESS` | Нет прогресса | raise↑ | — |
| `EXEC.VERIFIER_FAIL` | Verifier fail | raise↑ | — |
| `EXEC.LOOP_DETECTED` | Цикл действий | spike↑ | — |
| `EXEC.DEAD_END` | Тупик плана | spike↑ | — |
| `EXEC.STEP_OK` | Прогресс шага | soft↓ | phasic↑ |
| `EXEC.TASK_DONE` | Успех задачи | lower↓ | phasic↑ |
| `EXEC.TASK_FAILED` | Провал задачи | raise↑ | — |

### 3.4 Простой и скука

| ID | Событие | stress | go |
|----|---------|--------|-----|
| `IDLE.QUEUE_EMPTY` | Нет внешней задачи | sustain↑ во времени | — |
| `IDLE.NO_SIGNIFICANT_WORK` | Долго нет значимой работы | raise↑ (скука) | — |
| `IDLE.HEARTBEAT` | Фоновый тик | sustain | — |

### 3.5 Исходы

| ID | Событие | stress | go |
|----|---------|--------|-----|
| `OUT.BETTER_THAN_EXPECTED` | Лучше ожидания | soft↓ | phasic↑ |
| `OUT.WORSE_THAN_EXPECTED` | Хуже ожидания | raise↑ | — |
| `OUT.BLOCK_CLEARED` | Снят блок | lower↓ | phasic↑ |

### 3.6 Владелец

| ID | Событие | stress | go |
|----|---------|--------|-----|
| `OWNER.TASK_RECEIVED` | OWNER_DIRECT | soft | soft↑ |
| `OWNER.EMERGENCY` | emergency_override | spike↑ | — |

---

## 4. Правила контракта

1. Событие из словаря → возможность `hormone_update(event)`.
2. Обновление пульса не требует задачи в scheduler.
3. События суммируются в фоне (затухание — позже).
4. Метрика = факт; пульс = реакция (оба могут обновиться).
5. Нет `IDLE.*` при пустой очереди = дыра контракта.
6. Выход update — только stress/go; не job-type.

---

## 5. Минимальный набор для первой реализации

1. `RES.TOKENS_EXHAUSTED` / `RES.TOKENS_LOW`
2. `EXEC.NO_PROGRESS` / `EXEC.LOOP_DETECTED` / `EXEC.VERIFIER_FAIL`
3. `IDLE.NO_SIGNIFICANT_WORK`
4. `EXEC.STEP_OK` / `EXEC.TASK_DONE`
5. `EXT.PLATFORM_WARNING` / `EXT.PROVIDER_WARNING`
6. `IDLE.HEARTBEAT`

---

## 6. Вне скоупа v0

Численные gain, half-life, RPE, soft-Γ, детекторы NO_PROGRESS, UI «кортизол».

---

*HOMEOSTASIS_EVENTS_v0 · 2026-08-03*
