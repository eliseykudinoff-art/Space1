# Space1 — Описание тестов: FactorRegistry (Реестр факторов x₁-x₁₇)

> **Дата:** 2026-07-25
> **Автор:** AI-ревьюер
> **Статус:** Актуально для Space1 Phase 4 Fix 22
> **Файл теста:** `test_factors_registry.py`
> **Результат:** 102/102 тестов пройдены (pytest)

---

## Часть I. Философия теста

Этот тестовый набор проверяет модуль `factors/registry.py` — реестр 17 факторов способностей агента (x₁-x₁₇).

Каждый тест:
- Проверен против реального кода (запущен через pytest)
- Имеет докстринг = контракт + формула + обоснование
- FAILED = реальный баг, не ошибка теста
- Содержит комментарий `# ЭТО БАГ` если поведение отличается от ожидаемого

---

## Часть II. Структура тестов

### UNIT: FactorResult dataclass (`TestFactorResultUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_factor_result_creation` | Создание с 4 обязательными полями | PASS |
| `test_factor_result_with_metadata` | metadata dict передаётся | PASS |
| `test_factor_result_default_metadata_is_empty_dict` | default metadata = {} | PASS |

### UNIT: FactorID Enum (`TestFactorIDUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_factor_id_count_is_17` | Ровно 17 значений | PASS |
| `test_factor_id_x1_value` | X1_LLM.value == 'x1' | PASS |
| `test_factor_id_x17_value` | X17_INFERENCE_OPT.value == 'x17' | PASS |
| `test_factor_id_all_unique` | Все значения уникальны | PASS |

### UNIT: BaseFactor abstract (`TestBaseFactorUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_base_factor_priority_default_medium` | priority по умолчанию = 'MEDIUM' | PASS |
| `test_base_factor_enabled_default_true` | enabled по умолчанию = True | PASS |
| `test_base_factor_can_be_disabled` | Можно создать с enabled=False | PASS |

### UNIT: LLMFactor (x₁) (`TestLLMFactorUnit`)

| Тест | Что проверяет | Реальное поведение | Статус |
|------|---------------|-------------------|--------|
| `test_llm_factor_name` | name == 'LLM Capability' | ✅ | PASS |
| `test_llm_factor_priority_high` | priority == 'HIGH' | ✅ | PASS |
| `test_llm_factor_id` | factor_id == X1_LLM | ✅ | PASS |
| `test_llm_default_benchmarks_value` | value = 0.7 | ✅ | PASS |
| `test_llm_default_delta_success` | delta_s ≈ 0.21174 | ✅ | PASS |
| `test_llm_default_delta_time_zero` | delta_t = 0.0 | ✅ | PASS |
| `test_llm_perfect_benchmarks_value` | benchmarks=1.0 → value=1.0 | ✅ | PASS |
| `test_llm_perfect_benchmarks_delta_success` | benchmarks=1.0 → delta_s≈0.62414 | ✅ | PASS |
| `test_llm_zero_benchmarks_value` | benchmarks=0 → value=0.0 | ✅ | PASS |
| `test_llm_zero_benchmarks_delta_success` | benchmarks=0 → delta_s=-0.3 | ✅ | PASS |
| `test_llm_partial_benchmarks_uses_defaults_for_missing` | Недостающие = 0.7 | ✅ | PASS |
| `test_llm_context_lambda_tau_ignored_causes_overflow` | lambda_t=999 → OverflowError | ✅ OverflowError | PASS |
| `test_llm_metadata_contains_s_m_and_benchmarks` | metadata содержит s_m, benchmarks | ✅ | PASS |

**Баг-001:** LLMFactor читает `lambda_t` и `tau_t` из context, но при больших значениях `2.71828 ** exp_term` вызывает OverflowError. Код не защищён от численного переполнения.

**Баг-002:** Код использует `2.71828` вместо `math.e` — погрешность ~2.5e-7. Накапливается в ContinualLearningFactor.

### UNIT: PromptFactor (x₂) (`TestPromptFactorUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_prompt_factor_name` | 'Prompt Engineering' | PASS |
| `test_prompt_factor_default_value` | value = 0.8 | PASS |
| `test_prompt_factor_default_delta_success` | delta_s = 0.04 | PASS |
| `test_prompt_factor_default_delta_time` | delta_t = -0.05 | PASS |
| `test_prompt_factor_id` | X2_PROMPT | PASS |

### UNIT: CostTieringFactor (x₈) (`TestCostTieringFactorUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_cost_tiering_name` | 'Cost Tiering' | PASS |
| `test_cost_tiering_priority_high` | 'HIGH' | PASS |
| `test_cost_tiering_default_selects_paid_api` | Пустой → paid_api, 0.95 | PASS |
| `test_cost_tiering_budget_below_one_selects_ollama` | budget<1 → ollama, 0.6 | PASS |
| `test_cost_tiering_budget_between_one_and_ten_selects_free` | 1≤budget<10 → free_api, 0.75 | PASS |
| `test_cost_tiering_budget_ten_selects_paid` | budget≥10 → paid_api | PASS |
| `test_cost_tiering_high_quality_forces_paid` | quality≥0.8 → paid_api | PASS |
| `test_cost_tiering_negative_budget_selects_ollama` | budget<0 → ollama | PASS |
| `test_cost_tiering_delta_success_paid_positive` | paid: delta_s = 0.05 | PASS |
| `test_cost_tiering_delta_success_ollama_negative` | ollama: delta_s ≈ -0.02 | PASS |
| `test_cost_tiering_metadata_contains_budget` | metadata содержит budget | PASS |

### UNIT: GuardrailsFactor (x₁₂) (`TestGuardrailsFactorUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_guardrails_name` | 'Guardrails' | PASS |
| `test_guardrails_priority_high` | 'HIGH' | PASS |
| `test_guardrails_default_no_risks` | Пустой → g_eff=1.0, delta_s=0.05 | PASS |
| `test_guardrails_with_active_guardrail_reduces_risk` | guardrail активен → g_eff=1.0 | PASS |
| `test_guardrails_without_guardrail_exposes_risk` | guardrail отсутствует → g_eff=1-p | PASS |
| `test_guardrails_multiple_risks_multiplicative` | Несколько рисков перемножаются | PASS |
| `test_guardrails_partial_protection` | Частичная защита | PASS |
| `test_guardrails_p_risk_one_without_guardrail_g_eff_zero` | p=1.0 без guardrail → g_eff=0 | PASS |
| `test_guardrails_delta_time_scales_with_count` | delta_t = 0.02 * count | PASS |
| `test_guardrails_metadata_contains_count_and_g_eff` | metadata содержит count, g_eff | PASS |

### UNIT: ContinualLearningFactor (x₁₆) (`TestContinualLearningFactorUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_continual_learning_name` | 'Continual Learning' | PASS |
| `test_continual_learning_default_zero_tasks` | Пустой → value=0, delta_s=0 | PASS |
| `test_continual_learning_zero_tasks_explicit` | n=0 → value=0 | PASS |
| `test_continual_learning_100_tasks` | n=100 → value≈0.63212 | PASS |
| `test_continual_learning_1000_tasks_saturates` | n=1000 → value≈0.99995 | PASS |
| `test_continual_learning_negative_tasks` | n<0 → value<0 (без защиты) | PASS |
| `test_continual_learning_delta_time_scales_with_n` | delta_t = n * 1e-5 | PASS |
| `test_continual_learning_metadata_contains_n_tasks` | metadata содержит n_tasks | PASS |

**Баг-003:** `n_completed_tasks < 0` не защищён — value становится отрицательным.

### UNIT: FactorRegistry (`TestFactorRegistryUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_registry_empty_on_creation` | Новый registry пуст | PASS |
| `test_registry_register_adds_factor` | register добавляет | PASS |
| `test_registry_register_marks_enabled` | По умолчанию enabled | PASS |
| `test_registry_disable_removes_from_enabled` | disable исключает | PASS |
| `test_registry_enable_restores` | enable возвращает | PASS |
| `test_registry_unregister_removes_completely` | unregister удаляет | PASS |
| `test_registry_unregister_missing_returns_false` | unregister missing → False | PASS |
| `test_registry_get_existing` | get возвращает фактор | PASS |
| `test_registry_get_missing_returns_none` | get missing → None | PASS |
| `test_registry_compute_all_empty_returns_empty` | Пустой → {} | PASS |
| `test_registry_compute_all_returns_results` | compute_all вычисляет | PASS |
| `test_registry_compute_all_skips_disabled` | Пропускает disabled | PASS |
| `test_registry_compute_total_deltas_sums_correctly` | Суммирует дельты | PASS |
| `test_registry_compute_total_deltas_empty_zero` | Пустой → 0, 0 | PASS |

### UNIT: Factory functions (`TestFactoryFunctionsUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_create_mvp_registry_has_4_factors` | MVP = 4 фактора | PASS |
| `test_create_mvp_registry_factors_enabled` | Все 4 enabled | PASS |
| `test_create_mvp_registry_contains_expected_ids` | x1, x8, x12, x16 | PASS |
| `test_create_full_registry_has_17_factors` | Full = 17 факторов | PASS |
| `test_create_full_registry_all_enabled` | Все 17 enabled | PASS |
| `test_create_full_registry_contains_all_ids` | Все FactorID присутствуют | PASS |

### UNIT: Remaining factors (`TestRemainingFactorsUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_memory_retrieval_factor` | x₃: value=0.75, delta_s=0.05 | PASS |
| `test_memory_system_factor` | x₄: value=0.7, delta_s=0.03 | PASS |
| `test_multi_agent_factor` | x₅: value=0.85, delta_s=0.08 | PASS |
| `test_self_correction_factor` | x₆: value=0.9, delta_s=0.12 | PASS |
| `test_tool_calling_factor` | x₇: value=0.8, delta_s=0.06 | PASS |
| `test_grounding_factor` | x₉: value=0.75, delta_s=0.05 | PASS |
| `test_fine_tuning_factor` | x₁₀: value=0.82, delta_s=0.07 | PASS |
| `test_context_management_factor` | x₁₁: value=0.78, delta_s=0.04 | PASS |
| `test_test_time_compute_factor` | x₁₃: value=0.85, delta_s=0.10 | PASS |
| `test_design_patterns_factor` | x₁₄: value=0.8, delta_s=0.06 | PASS |
| `test_evaluation_factor` | x₁₅: value=0.74, delta_s=0.04 | PASS |
| `test_inference_opt_factor` | x₁₇: value=0.7, delta_s=0.01 | PASS |

### PAIR: FactorRegistry + LLMFactor (`TestPairRegistryLLM`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_registry_compute_all_propagates_context_to_llm` | context передаётся в LLMFactor | PASS |
| `test_registry_compute_total_deltas_with_multiple_factors` | Сумма 2+ факторов | PASS |

### PAIR: CostTieringFactor + GuardrailsFactor (`TestPairCostGuardrails`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_high_priority_factors_both_positive_delta` | Оба HIGH дают положительный delta_s | PASS |
| `test_cost_guardrails_combined_delta_time` | Суммарное delta_time = -0.095 | PASS |

### INTEGRITY: Архитектурные инварианты (`TestIntegrityFactors`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_llm_factor_uses_hardcoded_e_not_math_exp` | 2.71828 вместо math.e | PASS |
| `test_all_factors_return_factor_result` | Все 17 возвращают FactorResult | PASS |
| `test_factor_result_values_are_numeric` | value/delta_s/delta_t — числа | PASS |
| `test_registry_unregister_does_not_affect_other_factors` | unregister изолирован | PASS |
| `test_compute_all_with_disabled_registry_returns_empty` | Все disabled → {} | PASS |

### REGRESSION: Старые баги (`TestRegressionFactors`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_mvp_registry_always_has_four_factors` | MVP = 4 | PASS |
| `test_full_registry_always_has_seventeen_factors` | Full = 17 | PASS |
| `test_factor_id_enum_not_mutated` | Enum неизменен | PASS |
| `test_guardrails_g_eff_formula_unchanged` | Формула g_eff стабильна | PASS |

---

## Часть III. Сводка багов

| ID | Модуль | Описание | Серьёзность |
|----|--------|----------|-------------|
| BUG-001 | LLMFactor | `lambda_t`/`tau_t` из context не защищены от overflow | MEDIUM |
| BUG-002 | LLMFactor, ContinualLearningFactor | `2.71828` вместо `math.e` — погрешность ~2.5e-7 | LOW |
| BUG-003 | ContinualLearningFactor | `n_completed_tasks < 0` не защищён — value < 0 | LOW |

---

## Часть IV. Статистика

- **Всего тестов:** 102
- **Пройдено:** 102
- **FAILED:** 0
- **Предупреждения:** 1 (pytest не может собрать TestTimeComputeFactor как тест-класс из-за `__init__` — это false positive, класс определён в production-коде)
