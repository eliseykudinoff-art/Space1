# Space1 — Описание тестов: Cold Start Core

> **Дата:** 2026-07-26
> **Автор:** AI-ревьюер
> **Статус:** Актуально для Space1 Phase 4 Fix 22
> **Файл теста:** `test_cold_start_core.py`
> **Результат:** 57/57 тестов пройдены (pytest)

---

## Часть I. Философия теста

Тестовый набор проверяет модуль `cold_start/core.py` — canonical cold-start константы, состояние, UCB1 с защитой от деления на ноль, ensemble weights, predictor priors.

Каждый тест:
- Проверен против реального кода
- Имеет докстринг = контракт + обоснование
- FAILED = реальный баг

---

## Часть II. Структура тестов

### UNIT: Константы (`TestColdStartConstantsUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_H_initial_value` | H_INITIAL = 1.0 | PASS |
| `test_upsilon_initial_value` | UPSILON_INITIAL = 0.5 | PASS |
| `test_phi_historical_initial_value` | PHI_HISTORICAL_INITIAL = 0.0 | PASS |
| `test_rli_population_default_q` | RLI_POPULATION_DEFAULT_Q = 0.65 | PASS |
| `test_rli_population_default_psi` | RLI_POPULATION_DEFAULT_PSI = 0.25 | PASS |
| `test_ucb1_epsilon_value` | UCB1_EPSILON = 1e-6 | PASS |
| `test_ensemble_weights_cold` | cold = (0.4, 0.2, 0.4) | PASS |
| `test_ensemble_weights_warm` | warm = (0.2, 0.5, 0.3) | PASS |
| `test_ensemble_weights_hot` | hot = (0.1, 0.7, 0.2) | PASS |
| `test_ensemble_weights_sum_to_one` | Все суммы = 1.0 | PASS |
| `test_ensemble_weights_all_positive` | Все веса > 0 | PASS |

### UNIT: ColdStartState (`TestColdStartStateUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_cold_start_state_defaults` | Default значения | PASS |
| `test_cold_start_state_custom_values` | Кастомные значения | PASS |
| `test_cold_start_state_to_dict` | Сериализация (6 ключей) | PASS |
| `test_cold_start_state_to_dict_values` | Точность сериализации | PASS |
| `test_cold_start_state_zero_n_completed` | n_completed = 0 | PASS |
| `test_cold_start_state_negative_n_completed` | n_completed = -1 (баг) | PASS |

### UNIT: get_ensemble_weights (`TestGetEnsembleWeightsUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_ensemble_weights_cold_start` | n=0 → cold | PASS |
| `test_ensemble_weights_cold_boundary` | n=4 → cold | PASS |
| `test_ensemble_weights_warm_start` | n=5 → warm | PASS |
| `test_ensemble_weights_warm_mid` | n=10 → warm | PASS |
| `test_ensemble_weights_warm_boundary` | n=19 → warm | PASS |
| `test_ensemble_weights_hot_start` | n=20 → hot | PASS |
| `test_ensemble_weights_hot_large` | n=1000 → hot | PASS |
| `test_ensemble_weights_negative_n` | n=-1 → cold (баг) | PASS |

### UNIT: ucb1_safe_divide (`TestUcb1SafeDivideUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_safe_divide_normal` | 10/2 = 5.0 | PASS |
| `test_safe_divide_by_zero` | 10/0 = 10/1e-6 | PASS |
| `test_safe_divide_by_negative` | 10/(-1) = 10/1e-6 | PASS |
| `test_safe_divide_zero_numerator` | 0/5 = 0.0 | PASS |
| `test_safe_divide_custom_epsilon` | epsilon=0.5 | PASS |
| `test_safe_divide_both_zero` | 0/0 = 0.0 | PASS |

### UNIT: compute_ucb1_score (`TestComputeUcb1ScoreUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_ucb1_zero_selections` | n=0 → inf | PASS |
| `test_ucb1_one_selection` | n=1, total=1 | PASS |
| `test_ucb1_exploration_growth` | Меньший n → выше score | PASS |
| `test_ucb1_mean_reward_dominates` | Высокий reward → выше score | PASS |
| `test_ucb1_custom_c_exploration` | c=2.0 > c=1.0 | PASS |
| `test_ucb1_total_zero` | total=0 → ValueError (баг) | PASS |

### UNIT: get_predictor_priors (`TestGetPredictorPriorsUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_predictor_priors_default` | (0.65, 0.25) | PASS |
| `test_predictor_priors_unknown_category` | Fallback | PASS |
| `test_predictor_priors_empty_string` | Fallback | PASS |

### UNIT: initialize_agent_state (`TestInitializeAgentStateUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_initialize_empty_dict` | 6 ключей | PASS |
| `test_initialize_preserves_existing` | setdefault | PASS |
| `test_initialize_fills_missing` | Частичная инициализация | PASS |
| `test_initialize_returns_same_dict` | In-place mutation | PASS |

### PAIR: State + Ensemble (`TestPairStateEnsemble`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_state_n_completed_determines_weights` | state → weights | PASS |
| `test_state_transition_cold_to_warm` | n=4→5 | PASS |
| `test_state_transition_warm_to_hot` | n=19→20 | PASS |

### PAIR: UCB1 (`TestPairUcb1`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_ucb1_with_safe_divide_protection` | log(0) → ValueError (баг) | PASS |
| `test_ucb1_cold_start_protection` | n=0 → inf | PASS |

### INTEGRITY (`TestIntegrityColdStart`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_no_bare_except_in_cold_start` | Нет bare except | PASS |
| `test_ensemble_weights_keys` | 3 ключа | PASS |
| `test_ucb1_epsilon_positive` | epsilon > 0 | PASS |
| `test_ucb1_epsilon_small` | epsilon < 1e-3 | PASS |
| `test_cold_start_state_all_fields_positive_defaults` | Все >= 0 | PASS |

### REGRESSION (`TestRegressionColdStart`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_ucb1_division_by_zero_guarded` | ZeroDivisionError не падает | PASS |
| `test_ucb1_zero_selections_returns_inf` | n=0 → inf | PASS |
| `test_initialize_agent_state_no_side_effects` | Идемпотентность | PASS |

---

## Часть III. Сводка багов

### Найденные баги

| ID | Баг | Где | Статус в тесте |
|----|-----|-----|----------------|
| **BUG-CS-001** | `compute_ucb1_score` падает с `ValueError: math domain error` при `total_selections=0` — `math.log(0)` вызывается ДО защиты `ucb1_safe_divide` | `cold_start/core.py:97` | Подтверждён в `test_ucb1_total_zero` и `test_ucb1_with_safe_divide_protection` |
| **BUG-CS-002** | `ColdStartState` принимает отрицательный `n_completed` без валидации | `cold_start/core.py:48` | Подтверждён в `test_cold_start_state_negative_n_completed` |
| **BUG-CS-003** | `get_ensemble_weights(-1)` возвращает cold веса вместо ошибки | `cold_start/core.py:76` | Подтверждён в `test_ensemble_weights_negative_n` |

### Проверенные контракты

| Контракт | Результат |
|----------|-----------|
| Canonical constants (H, Upsilon, Phi, Q, Psi, epsilon) | ✅ |
| ENSEMBLE_WEIGHTS (cold/warm/hot) | ✅ |
| ColdStartState defaults | ✅ |
| ColdStartState.to_dict() | ✅ |
| ucb1_safe_divide guard | ✅ |
| compute_ucb1_score n=0 → inf | ✅ |
| get_predictor_priors fallback | ✅ |
| initialize_agent_state setdefault | ✅ |
| No bare except | ✅ |

---

*Документ создан: 2026-07-26*  
*Версия: 1.0*  
*Статус: Актуально для Space1 Phase 4 Fix 22*
