# Space1 — Описание тестов: Mission Core (Mission, MissionPolicy, TaskDecomposer, MissionProcessor)

> **Дата:** 2026-07-26
> **Автор:** AI-ревьюер
> **Статус:** Актуально для Space1 Phase 4 Fix 22
> **Файл теста:** `test_mission_core.py`
> **Результат:** 65/65 тестов пройдены (pytest)

---

## Часть I. Философия теста

Тестовый набор проверяет модуль `mission/core.py` — калибровку миссий, декомпозицию задач, pipeline execution.

Каждый тест:
- Проверен против реального кода (запущен через pytest)
- Имеет докстринг = контракт + формула + обоснование
- FAILED = реальный баг, не ошибка теста
- Содержит комментарий `# ЭТО БАГ` если поведение отличается от ожидаемого

---

## Часть II. Структура тестов

### UNIT: MISSION_CALIBRATION table (`TestMissionCalibrationUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_mission_calibration_has_all_six_types` | 6 типов в таблице | PASS |
| `test_mission_calibration_weights_sum_to_one` | Веса суммируются в 1.0 | PASS |
| `test_mission_calibration_survival_has_high_phi` | SURVIVAL phi=0.50, MAXIMIZE phi=0.55 | PASS |
| `test_mission_calibration_premium_has_highest_quality` | PREMIUM quality=0.40 — максимум | PASS |
| `test_mission_calibration_charity_has_lowest_phi` | CHARITY phi=0.10 — минимум | PASS |

### UNIT: Mission.calibrate() (`TestMissionCalibrateUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_calibrate_returns_policy_params` | Тип возвращаемого значения | PASS |
| `test_calibrate_weights_sum_to_one` | Нормировка для всех 6 типов | PASS |
| `test_calibrate_survival_with_low_balance_boosts_phi` | Низкий баланс → phi↑ | PASS |
| `test_calibrate_phi_historical_negative_increases_psi_max` | phi_historical<0 → psi_max*=1.2 | PASS |
| `test_calibrate_q_min_between_zero_and_one` | q_min ∈ [0.1, 1.0] | PASS |
| `test_calibrate_c_max_positive_with_floor` | c_max > 0, floor=0.1 | PASS (баг отмечен) |
| `test_calibrate_mission_type_preserved_in_params` | Тип миссии сохраняется | PASS |
| `test_calibrate_default_mission_context` | Default voi=0.5, c_info=2.0 | PASS |
| `test_calibrate_custom_mission_context` | Custom context propagation | PASS |

### UNIT: StateModifier (`TestStateModifierUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_default_modifiers_are_all_one` | Нейтральное состояние | PASS |
| `test_low_balance_boosts_phi_and_reduces_upsilon` | balance<0.3 → phi*=1.5, ups*=0.7 | PASS |
| `test_high_balance_boosts_phi` | balance>0.9 → phi*=1.2 | PASS |
| `test_high_stress_reduces_omega` | stress>1.3 → omega*=0.5 | PASS |
| `test_low_reputation_boosts_upsilon` | reputation<0.5 → ups*=1.3 | PASS |
| `test_high_workload_boosts_quality_reduces_phi` | workload>3.0 → qual*=1.1, phi*=0.9 | PASS |
| `test_low_workload_boosts_omega` | workload<0.5 → omega*=1.2 | PASS |
| `test_combined_extreme_state` | Комбинированные модификаторы | PASS |

### UNIT: MissionPolicy (`TestMissionPolicyUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_mission_policy_presets_sum_to_one` | Все пресеты нормированы | PASS |
| `test_mission_policy_survival_preset` | profit=0.40, risk=0.10... | PASS |
| `test_mission_policy_charity_preset` | profit=0.05, quality=0.70 | PASS |
| `test_mission_policy_calibrate_low_balance_increases_profit` | balance<100 → profit↑ | PASS |
| `test_mission_policy_calibrate_high_stress_reduces_risk` | stress>0.7 → risk↓ | PASS |
| `test_mission_policy_calibrate_normalizes_to_one` | Нормировка после pressures | PASS |
| `test_mission_policy_to_dict` | 4 ключа, все float | PASS |

### UNIT: TaskDecomposer (`TestTaskDecomposerUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_decompose_returns_actions_and_quality` | Контракт возвращаемого | PASS |
| `test_decompose_security_keywords` | "auth", "jwt" → security actions | PASS |
| `test_decompose_deploy_keywords` | "deploy", "aws" → deploy actions | PASS |
| `test_decompose_finance_keywords` | "payment", "stripe" → finance actions | PASS |
| `test_decompose_combined_categories` | Комбинирование категорий | PASS |
| `test_decompose_fallback_no_match` | Нет keywords → fallback | PASS |
| `test_decompose_budget_allocation` | Сумма cost ≈ budget | PASS |
| `test_decompose_quality_score_positive` | quality > 0 | PASS |
| `test_decompose_action_params_have_input_output` | DAG-структура params | PASS |
| `test_decompose_with_task_object` | Полиморфизм str/Task | PASS |

### UNIT: MissionProcessor (`TestMissionProcessorUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_processor_setup_mission` | Инициализация | PASS |
| `test_processor_execute_without_setup_raises` | ValueError без setup | PASS |
| `test_processor_execute_runs_all_stages` | 4 stage_results | PASS |
| `test_processor_execute_no_errors_for_legal_action` | Legal action проходит | PASS |
| `test_processor_execute_compliance_veto_raises` | ComplianceError на veto | PASS |
| `test_processor_execute_best_selects_one_action` | Ranking + execution | PASS |
| `test_processor_execute_best_with_all_vetoed` | Graceful degradation | PASS |
| `test_processor_get_pipeline_status` | 4 stages в статусе | PASS |
| `test_processor_decompose_task` | Delegation к decomposer | PASS |

### UNIT: create_mission (`TestCreateMissionUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_create_mission_returns_mission` | Тип | PASS |
| `test_create_mission_sets_name` | name propagation | PASS |
| `test_create_mission_default_type_is_maintenance` | Default MAINTENANCE | PASS |
| `test_create_mission_sets_max_budget` | budget propagation | PASS |
| `test_create_mission_sets_max_hours` | time propagation | PASS |
| `test_create_mission_generates_unique_id` | Уникальность id | PASS |

### PAIR: Mission thresholds (`TestPairMissionThresholds`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_survival_mission_has_lower_psi_max_than_growth` | psi_max зависит от state | PASS |
| `test_mission_type_affects_quality_weight` | PREMIUM quality > MAXIMIZE quality | PASS |

### PAIR: Processor + Decomposer (`TestPairProcessorDecomposer`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_processor_decompose_then_execute` | End-to-end декомпозиция→выполнение | PASS |

### INTEGRITY (`TestIntegrityMission`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_mission_calibration_table_matches_enum` | Полнота таблицы | PASS |
| `test_policy_params_weights_are_positive` | Все weights > 0 | PASS |
| `test_mission_policy_presets_match_mission_calibration` | Консистентность источников | PASS |
| `test_no_asyncio_sleep_in_synchronous_execute` | execute — синхронный | PASS |
| `test_task_decomposer_budget_non_negative` | budget=0 не падает | PASS |

### REGRESSION (`TestRegressionMission`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_mission_calibrate_does_not_mutate_input_state` | Иммутабельность state | PASS |
| `test_mission_processor_stages_order` | Порядок: MISSION→COMPLIANCE→UTILITY→EXECUTION | PASS |
| `test_execution_context_initially_no_errors` | Чистый контекст | PASS |

---

## Часть III. Сводка багов

| ID | Баг | Где | Статус в тесте |
|----|-----|-----|----------------|
| **BUG-MISS-001** | `c_max` использует `max(cost_penalty, 0.1)` вместо `cost_penalty` | `mission/core.py` | `# ЭТО БАГ` в `test_calibrate_c_max_positive_with_floor` |

**Обоснование BUG-MISS-001:** Документация §IV.12: `c_max = C_remaining * (2.0 / cost_penalty)`. Код: `max(cost_penalty, 0.1)` — floor 0.1 меняет результат при `cost_penalty < 0.1`. Это защита от деления на ноль, но она не документирована и меняет математику.

---

## Часть IV. Параметры теста

### Запуск

```bash
export PYTHONPATH=/path/to/space1/src
pytest tests/test_mission_core.py -v
```

### Зависимости

- `space1.mission.core` (Mission, MissionType, PolicyParams, StateModifier, MISSION_CALIBRATION, MissionPolicy, MissionProfile, TaskDecomposer, MissionProcessor, ExecutionContext, PipelineStage, create_mission)
- `space1.compliance.core` (Action, BlockedActionsRule, ComplianceError)
- `space1.models.task` (Task, TaskPriority)
- `pytest`

### Покрытие

- **MISSION_CALIBRATION:** 5 тестов
- **Mission.calibrate:** 9 тестов
- **StateModifier:** 8 тестов
- **MissionPolicy:** 7 тестов
- **TaskDecomposer:** 10 тестов
- **MissionProcessor:** 9 тестов
- **create_mission:** 6 тестов
- **PAIR:** 3 теста
- **INTEGRITY:** 5 тестов
- **REGRESSION:** 3 теста

**Итого: 65 тестов, 65 пройдены, 0 skipped, 0 xfailed.**

---

*Документ создан: 2026-07-26*
*Версия: 1.0*
*Статус: Актуально для Space1 Phase 4 Fix 22*
