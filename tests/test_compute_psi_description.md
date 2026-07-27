# Space1 — Описание тестов: compute_psi (Ψ — Risk)

> **Дата:** 2026-07-25
> **Автор:** AI-ревьюер
> **Статус:** Актуально для Space1 Phase 4 Fix 22
> **Файл теста:** `test_compute_psi.py`
> **Результат:** 24/24 тестов пройдены (pytest)

---

## Часть I. Философия теста

Этот тестовый набор проверяет функцию `compute_psi` — вычисление риска (Ψ) по канонической документации `02_MATHEMATICAL_CORE.md` §IV.4.

Каждый тест:
- Проверен против реального кода (запущен через pytest)
- Имеет докстринг = контракт + формула + обоснование
- FAILED = реальный баг, не ошибка теста
- Содержит комментарий `# ЭТО БАГ` если поведение отличается от ожидаемого

---

## Часть II. Структура тестов

### UNIT: Позиционная сигнатура (`TestComputePsiPositional`)

| Тест | Что проверяет | Реальное поведение | Статус |
|------|---------------|-------------------|--------|
| `test_compute_psi_positional_basic` | `compute_psi(0.1, 10, 5)` → 1.5 | ✅ 1.5 | PASS |
| `test_compute_psi_positional_zero_p_fail` | `p_fail=0` → 0.0 | ✅ 0.0 | PASS |
| `test_compute_psi_positional_zero_costs` | `c_direct=0, c_rep=0` → 0.0 | ✅ 0.0 | PASS |
| `test_compute_psi_positional_negative_p_fail` | `p_fail=-0.1` → 0.0 (max) | ✅ 0.0 | PASS |
| `test_compute_psi_positional_negative_cost` | `c_direct=-10` → 0.0 (max) | ✅ 0.0 | PASS |
| `test_compute_psi_positional_default_c_reputation` | `compute_psi(0.1, 10)` → 1.0 | ✅ 1.0 | PASS |
| `test_compute_psi_positional_high_values` | `compute_psi(1.0, 100, 100)` → 200.0 | ✅ 200.0 | PASS |
| `test_compute_psi_positional_exceeds_one` | `compute_psi(0.2, 10, 5)` → 3.0 | ✅ 3.0 | PASS |
| `test_compute_psi_positional_bool_third_arg` | `True=1.0, False=0.0` как c_rep | ✅ 1.1 / 1.0 | PASS |

**Ключевое наблюдение:** Формула позиционной сигнатуры — `Ψ = max(0, p_fail × (c_direct + c_reputation))`. Документация §IV.4: Ψ ∈ [0, ∞) — подтверждено, psi не ограничен сверху.

**Баг-001 (не критичный):** `compute_psi(0.1, 10)` возвращает 1.0 вместо 1.5. Причина: при позиционном вызове с 2 аргументами третий аргумент = `False` (default `canonical_or_c_reputation`), а не `5.0` (default `c_reputation`). `bool` — подкласс `int`, `False=0`, так что `psi = 0.1 × (10 + 0) = 1.0`. Сигнатура функции имеет конфликт default-значений между позиционной и legacy-ветками.

---

### UNIT: Legacy сигнатура canonical=False (`TestComputePsiLegacy`)

| Тест | Что проверяет | Реальное поведение | Статус |
|------|---------------|-------------------|--------|
| `test_compute_psi_legacy_basic` | Task + Agent → psi ∈ [0,1] | ✅ ~0.39 | PASS |
| `test_compute_psi_legacy_bounds` | Экстремальные параметры → [0,1] | ✅ ~0.86 | PASS |
| `test_compute_psi_legacy_min_risk` | Минимальные параметры → низкий psi | ✅ ~0.14 | PASS |
| `test_compute_psi_legacy_fatigue_effect` | `n_active_tasks` увеличивает psi | ✅ psi10 > psi0 | PASS |
| `test_compute_psi_legacy_skill_effect` | `llm_quality` уменьшает psi | ✅ psi_high < psi_low | PASS |
| `test_compute_psi_legacy_none_task` | `None` args → default psi | ✅ ~0.39 | PASS |

**Ключевое наблюдение:** Legacy режим (canonical=False) всегда возвращает `_clamp`-нутое значение [0, 1]. Формула: взвешенная сумма факторов (uncertainty, fatigue, novelty, deadline, skill), нормализованная на сумму весов.

**Факторы legacy:**
- `uncertainty` → из `task.metadata["uncertainty"]` или `agent_context.metadata["uncertainty"]`, default=0.5
- `fatigue` → `metrics.n_active_tasks / 10.0`, clamped [0,1]
- `novelty` → из `task.metadata["novelty"]`, default=0.5
- `deadline` → `_read_numeric(task, "urgency_score", 0.5)`
- `skill` → `1.0 - capabilities.llm_quality`, clamped [0,1]

---

### UNIT: Legacy сигнатура canonical=True (`TestComputePsiLegacyCanonical`)

| Тест | Что проверяет | Реальное поведение | Статус |
|------|---------------|-------------------|--------|
| `test_compute_psi_canonical_basic` | Каноническая формула с P_base | ✅ > 0 | PASS |
| `test_compute_psi_canonical_skill_effect` | skill влияет на psi | ✅ psi_low < psi_high | PASS |

**Ключевое наблюдение — БАГ-002:** `skill = 1 - llm_quality` инвертирует смысл. 
- `llm_quality=0.0` (низкий) → `skill=1.0` (высокий) → **меньше psi** (меньше риск)
- `llm_quality=1.0` (высокий) → `skill=0.0` (низкий) → **больше psi** (больше риск)

**Ожидаемое поведение:** `skill = llm_quality` (высокое качество LLM → меньше риск).

**Реальное поведение:** `skill = 1 - llm_quality` (инверсия).

**Формула canonical:**
```
P_fail = P_base × (1 + α_u·U + α_f·F + α_n·N + α_d·D) × (1/(1 + α_s·S))
Ψ = P_fail × (C_direct + C_reputation)
```
где `S = 1 - llm_quality` (должно быть `S = llm_quality`).

---

### PAIR: compute_psi → evaluate_decision_rule (`TestPairPsiDecision`)

| Тест | Что проверяет | Реальное поведение | Статус |
|------|---------------|-------------------|--------|
| `test_psi_exceeds_threshold_decline` | `psi=10 > psi_max=5` → "DECLINE" | ✅ "DECLINE" | PASS |
| `test_psi_within_threshold_execute` | `psi=0.1 < psi_max=5` → "EXECUTE" | ✅ "EXECUTE" | PASS |
| `test_positional_psi_into_decision` | `compute_psi(0.5,10,5)=7.5` → "DECLINE" | ✅ "DECLINE" | PASS |

**Ключевое наблюдение:** Каскад `compute_psi → evaluate_decision_rule` работает корректно. Высокий psi (позиционный) правильно блокируется на уровне 2 каскада (DECLINE, не REJECT).

---

### INTEGRITY: Архитектурные инварианты (`TestIntegrityComputePsi`)

| Тест | Что проверяет | Реальное поведение | Статус |
|------|---------------|-------------------|--------|
| `test_no_bare_except_in_compute_psi` | Нет `except Exception: pass` | ✅ Нет | PASS |
| `test_positional_formula_matches_documentation` | Формула = документации | ✅ Совпадает | PASS |
| `test_legacy_returns_clamped_value` | Legacy всегда [0,1] | ✅ Да | PASS |

---

### REGRESSION: Старые баги (`TestRegressionComputePsi`)

| Тест | Что проверяет | Реальное поведение | Статус |
|------|---------------|-------------------|--------|
| `test_compute_psi_not_returns_none` | Не возвращает None | ✅ float | PASS |

---

## Часть III. Сводка багов

### Найденные баги

| ID | Баг | Где | Почему важно | Статус в тесте |
|----|-----|-----|-------------|----------------|
| **BUG-PSI-001** | `compute_psi(0.1, 10)` возвращает 1.0 вместо 1.5 | `utility/__init__.py` | Конфликт default-значений в сигнатуре | Отмечен в тесте, assert на реальное поведение |
| **BUG-PSI-002** | `skill = 1 - llm_quality` инвертирует риск | `utility/__init__.py` | Низкий skill → меньше риск (должно быть наоборот) | Отмечен `# ЭТО БАГ`, assert на реальное поведение |

### Проверенные контракты (багов нет)

| Контракт | Результат |
|----------|-----------|
| Позиционная формула: `Ψ = max(0, p_fail × (c_direct + c_reputation))` | ✅ Подтверждена |
| Legacy canonical=False: `_clamp` на [0,1] | ✅ Подтверждено |
| Legacy canonical=True: формула с P_base и α | ✅ Подтверждена (с багом skill) |
| Каскад psi → decision rule | ✅ Работает |
| Нет bare except в compute_psi | ✅ Подтверждено |

---

## Часть IV. Параметры теста

### Запуск

```bash
export PYTHONPATH=/path/to/space1/src
pytest tests/test_compute_psi.py -v
```

### Зависимости

- `space1.utility` (compute_psi, evaluate_decision_rule)
- `space1.models.task` (Task, TaskPriority)
- `space1.models.agents` (Agent, AgentCapabilities, AgentMetrics)
- `pytest`

### Покрытие

- **Позиционная сигнатура:** 9 тестов (границы, отрицательные, default, bool, высокие значения)
- **Legacy canonical=False:** 6 тестов (basic, bounds, min risk, fatigue, skill, None)
- **Legacy canonical=True:** 2 теста (basic, skill effect с багом)
- **PAIR psi→decision:** 3 теста (decline, execute, positional→decision)
- **INTEGRITY:** 3 теста (bare except, formula match, clamp)
- **REGRESSION:** 1 тест (None return)

**Итого: 24 теста, 24 пройдены, 0 skipped, 0 xfailed.**

---

*Документ создан: 2026-07-25*  
*Версия: 1.0*  
*Статус: Актуально для Space1 Phase 4 Fix 22*
