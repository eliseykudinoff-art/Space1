# Space1 — Описание тестов: Environment Core

> **Дата:** 2026-07-26
> **Автор:** AI-ревьюер
> **Статус:** Актуально для Space1 Phase 4 Fix 22
> **Файл теста:** `test_environment_core.py`
> **Результат:** 42/42 теста пройдены (pytest)

---

## Часть I. Философия теста

Тестовый набор проверяет модуль `environment/core.py` — MarketEnvironment, MarketLead, ClientProfile, stream_leads, simulate_competition, generate_review.

Каждый тест:
- Проверен против реального кода
- Имеет докстринг = контракт + обоснование
- FAILED = реальный баг

---

## Часть II. Структура тестов

### UNIT: ClientProfile (`TestClientProfileUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_client_profile_defaults` | rigor=0.5, max_budget=500, multiplier=1.0, demanding=False | PASS |
| `test_client_profile_custom` | Кастомные значения | PASS |
| `test_client_profile_negative_rigor` | rigor=-0.1 принимается (баг) | PASS |
| `test_client_profile_rigor_above_one` | rigor=1.5 принимается (баг) | PASS |

### UNIT: MarketLead (`TestMarketLeadUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_market_lead_defaults` | required_quality=0.7, hours=2.0, urgency=0.5 | PASS |
| `test_market_lead_custom` | Кастомные значения | PASS |

### UNIT: MarketEnvironment (`TestMarketEnvironmentUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_env_init_empty` | Пустое состояние, pressure=0.3 | PASS |
| `test_env_add_lead` | Добавление lead | PASS |
| `test_env_stream_leads_count` | Количество | PASS |
| `test_env_stream_leads_returns_tasks` | Тип Task | PASS |
| `test_env_stream_leads_uses_available` | Pre-existing priority | PASS |
| `test_env_stream_leads_generates_when_empty` | Auto-generation | PASS |
| `test_env_stream_leads_task_has_revenue` | Revenue | PASS |
| `test_env_stream_leads_task_has_client_metadata` | Metadata | PASS |
| `test_env_stream_leads_priority_high` | urgency>0.7 → HIGH | PASS |
| `test_env_stream_leads_priority_medium` | urgency≤0.7 → MEDIUM | PASS |
| `test_env_stream_leads_count_zero` | count=0 → [] | PASS |
| `test_env_simulate_competition_returns_bool` | Тип bool | PASS |
| `test_env_simulate_competition_high_margin` | margin>100 → pressure+0.3 | PASS |
| `test_env_simulate_competition_low_margin` | margin<100 → pressure=0.3 | PASS |
| `test_env_simulate_competition_no_revenue` | Graceful no revenue | PASS |
| `test_env_generate_review_excellent` | delta≥0.1 → rating=5.0 | PASS |
| `test_env_generate_review_satisfactory` | delta=0 → rating=4.0 | PASS |
| `test_env_generate_review_poor` | delta<0 → rating<3.0 | PASS |
| `test_env_generate_review_rigor_affects_poor` | rigor влияет на penalty | PASS |
| `test_env_generate_review_rating_floor` | rating ≥ 1.0 | PASS |
| `test_env_generate_review_rating_ceiling` | rating ≤ 5.0 | PASS |
| `test_env_generate_review_returns_multiplier` | multiplier проксирован | PASS |
| `test_env_generate_review_missing_metadata` | Default metadata | PASS |

### PAIR: Env + Lead (`TestPairEnvLead`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_env_uses_lead_budget_as_revenue` | budget → revenue | PASS |
| `test_env_uses_lead_client_in_metadata` | client → metadata | PASS |

### PAIR: Env + Task (`TestPairEnvTask`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_stream_creates_task_with_title` | Title проксирован | PASS |
| `test_stream_creates_task_with_estimated_hours` | Hours проксирован | PASS |

### PAIR: Env + Review (`TestPairEnvReview`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_review_uses_task_metadata` | End-to-end metadata flow | PASS |

### INTEGRITY (`TestIntegrityEnvironment`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_no_bare_except_in_environment` | Нет bare except | PASS |
| `test_competitor_pressure_range` | pressure ∈ [0, 1] | PASS |
| `test_rating_range` | rating ∈ [1.0, 5.0] | PASS |
| `test_client_profile_rigor_is_probability` | rigor контракт | PASS |
| `test_revenue_non_negative` | revenue ≥ 0 | PASS |

### REGRESSION (`TestRegressionEnvironment`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_stream_leads_does_not_modify_original_lead` | Иммутабельность | PASS |
| `test_generate_review_no_crash_missing_metadata` | Graceful missing | PASS |
| `test_simulate_competition_no_crash_no_revenue` | Graceful no revenue | PASS |

---

## Часть III. Сводка багов

### Найденные баги

| ID | Баг | Где | Статус в тесте |
|----|-----|-----|----------------|
| **BUG-ENV-001** | `ClientProfile` принимает отрицательный `rigor` без валидации | `environment/core.py:24` | Подтверждён в `test_client_profile_negative_rigor` |
| **BUG-ENV-002** | `ClientProfile` принимает `rigor > 1` без валидации | `environment/core.py:24` | Подтверждён в `test_client_profile_rigor_above_one` |

### Проверенные контракты

| Контракт | Результат |
|----------|-----------|
| ClientProfile defaults | ✅ |
| MarketLead defaults | ✅ |
| MarketEnvironment stream_leads | ✅ |
| MarketEnvironment priority mapping | ✅ |
| MarketEnvironment simulate_competition | ✅ |
| MarketEnvironment generate_review branches | ✅ |
| MarketEnvironment rating floor/ceiling | ✅ |
| MarketEnvironment rigor affects penalty | ✅ |
| No bare except | ✅ |
| Competitor pressure range | ✅ |
| Revenue non-negative | ✅ |

---

*Документ создан: 2026-07-26*  
*Версия: 1.0*  
*Статус: Актуально для Space1 Phase 4 Fix 22*
