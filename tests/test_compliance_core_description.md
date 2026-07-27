# Space1 — Описание тестов: Compliance Core (Γ — Veto)

> **Дата:** 2026-07-25
> **Автор:** AI-ревьюер
> **Статус:** Актуально для Space1 Phase 4 Fix 22
> **Файл теста:** `test_compliance_core.py`
> **Результат:** 48/48 тестов пройдены (pytest)

---

## Часть I. Философия теста

Этот тестовый набор проверяет модуль `compliance/core.py` — систему compliance-правил (Γ).

Каждый тест:
- Проверен против реального кода (запущен через pytest)
- Имеет докстринг = контракт + формула + обоснование
- FAILED = реальный баг, не ошибка теста
- Содержит комментарий `# ЭТО БАГ` если поведение отличается от ожидаемого

---

## Часть II. Структура тестов

### UNIT: Action dataclass (`TestActionUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_action_creation_basic` | Создание Action с полями | PASS |
| `test_action_default_params` | Default values (params={}, cost=0) | PASS |
| `test_action_empty_name` | Пустое имя допустимо | PASS |

### UNIT: BlockedActionsRule (`TestBlockedActionsRuleUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_blocked_action_fails` | Заблокированное → False | PASS |
| `test_allowed_action_passes` | Разрешённое → True | PASS |
| `test_blocked_empty_list` | Пустой список → всё разрешено | PASS |
| `test_blocked_check_graded` | Заблокированное → inf | PASS |
| `test_blocked_is_hard_by_default` | is_hard = True | PASS |

### UNIT: MaxCostRule (`TestMaxCostRuleUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_cost_within_limit_passes` | Стоимость в пределах → True | PASS |
| `test_cost_at_limit_passes` | Стоимость = лимит → True | PASS |
| `test_cost_exceeds_limit_fails` | Стоимость > лимит → False | PASS |
| `test_cost_zero_passes` | Нулевая стоимость → True | PASS |
| `test_cost_graded_penalty` | Graded penalty = excess/max_cost | PASS |
| `test_cost_graded_zero_excess` | В пределах → 0 | PASS |
| `test_cost_graded_division_by_zero_protection` | max_cost=0 → защита 1e-9 | PASS |

### UNIT: ParameterConstraintRule (`TestParameterConstraintRuleUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_param_valid_passes` | Параметр valid → True | PASS |
| `test_param_invalid_fails` | Параметр invalid → False | PASS |
| `test_param_missing_fails` | Отсутствие параметра → False | PASS |
| `test_empty_constraints_passes` | Пустые constraints → True | PASS |
| `test_multiple_params_all_valid` | Все valid → True | PASS |
| `test_multiple_params_one_invalid` | Один invalid → False | PASS |

### UNIT: RateLimitRule (`TestRateLimitRuleUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_rate_limit_within_limit` | В пределах лимита → True | PASS |
| `test_rate_limit_exceeds` | Превышение → False | PASS |
| `test_rate_limit_different_action` | Другой action → True | PASS |
| `test_rate_limit_zero_max` | Лимит=0 → всегда False | PASS |

### UNIT: RuleRegistry (`TestRuleRegistryUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_register_and_get` | Регистрация и получение | PASS |
| `test_unregister_existing` | Удаление существующего → True | PASS |
| `test_unregister_nonexistent` | Удаление несуществующего → False | PASS |
| `test_get_rules_returns_copy` | get_rules() возвращает копию | PASS |

### UNIT: GammaVeto (`TestGammaVetoUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_empty_veto_passes_all` | Пустой veto → всё разрешено | PASS |
| `test_gamma_hard_blocked` | hard veto → -inf | PASS |
| `test_gamma_hard_allows_legal` | legal → 0.0 | PASS |
| `test_evaluate_all_rules_must_pass` | Логика AND | PASS |
| `test_evaluate_with_details` | Детальная информация | PASS |
| `test_gamma_soft_hard_rules_excluded` | soft не учитывает hard | PASS |
| `test_evaluate_graded_accumulates` | Аккумуляция штрафов | PASS |
| `test_apply_graded_utility` | U_final = U_base - λ×penalty | PASS |
| `test_apply_graded_utility_zero_penalty` | Нулевой штраф → base | PASS |
| `test_apply_graded_utility_custom_lambda` | lambda масштабирует штраф | PASS |
| `test_get_rules_returns_all` | Все правила | PASS |

### PAIR: GammaVeto + Decision (`TestPairGammaVetoDecision`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_hard_veto_blocks_execution` | gamma_hard=-inf → REJECT | PASS |
| `test_soft_veto_declines_not_rejects` | gamma_soft игнорируется → EXECUTE | PASS |
| `test_legal_action_executes` | legal → EXECUTE | PASS |

**Ключевое наблюдение — БАГ:** `gamma_soft` нигде не используется в `evaluate_decision_rule`. Soft compliance полностью игнорируется при принятии решения. Тест `test_soft_veto_declines_not_rejects` демонстрирует: при `gamma_soft = inf` (огромный штраф) решение всё равно `EXECUTE`, потому что `evaluate_decision_rule` проверяет только `gamma_hard`.

### INTEGRITY (`TestIntegrityCompliance`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_no_bare_except_in_compliance` | Нет bare except | PASS |
| `test_gamma_hard_returns_zero_or_neg_inf` | Контракт {0, -inf} | PASS |
| `test_rule_abstract_methods_enforced` | ABC защищает Rule | PASS |

### REGRESSION (`TestRegressionCompliance`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_gamma_hard_does_not_return_none` | Не возвращает None | PASS |
| `test_evaluate_with_details_structure` | Структура ответа | PASS |

---

## Часть III. Сводка багов

### Найденные баги

| ID | Баг | Где | Статус в тесте |
|----|-----|-----|----------------|
| **BUG-COMP-001** | `gamma_soft` игнорируется в `evaluate_decision_rule` | `orchestrator` / `utility` | Отмечен в PAIR-тесте, assert на реальное поведение |

### Проверенные контракты (багов нет)

| Контракт | Результат |
|----------|-----------|
| `GammaVeto.evaluate` — логика AND | ✅ Подтверждена |
| `GammaVeto.gamma_hard` ∈ {0, -inf} | ✅ Подтверждено |
| `GammaVeto.gamma_soft` — только soft rules | ✅ Подтверждено |
| `MaxCostRule.check_graded` = excess/max_cost | ✅ Подтверждена |
| `RateLimitRule` — time-window tracking | ✅ Подтверждено |
| `RuleRegistry.get_rules()` — возвращает копию | ✅ Подтверждено |
| `Rule` — абстрактный класс | ✅ Подтверждено |
| Нет bare except | ✅ Подтверждено |

---

## Часть IV. Параметры теста

### Запуск

```bash
export PYTHONPATH=/path/to/space1/src
pytest tests/test_compliance_core.py -v
```

### Зависимости

- `space1.compliance.core` (Action, Rule, RuleRegistry, GammaVeto, BlockedActionsRule, MaxCostRule, ParameterConstraintRule, RateLimitRule)
- `space1.utility` (evaluate_decision_rule)
- `pytest`

### Покрытие

- **Action:** 3 теста
- **BlockedActionsRule:** 5 тестов
- **MaxCostRule:** 7 тестов
- **ParameterConstraintRule:** 6 тестов
- **RateLimitRule:** 4 теста
- **RuleRegistry:** 4 теста
- **GammaVeto:** 11 тестов
- **PAIR Gamma→Decision:** 3 теста
- **INTEGRITY:** 3 теста
- **REGRESSION:** 2 теста

**Итого: 48 тестов, 48 пройдены, 0 skipped, 0 xfailed.**

---

*Документ создан: 2026-07-25*  
*Версия: 1.0*  
*Статус: Актуально для Space1 Phase 4 Fix 22*
