# Space1 — Описание тестов: agents/core.py (Sub-Agent Manifests & UnifiedCognitiveAgent)

> **Дата:** 2026-07-25
> **Автор:** AI-ревьюер
> **Статус:** Актуально для Space1 Phase 4 Fix 22
> **Файл теста:** `test_agents_core.py`
> **Результат:** 69/69 тестов пройдены (pytest)

---

## Часть I. Философия теста

Этот тестовый набор проверяет модуль `agents/core.py` — sub-agent manifests, registry, execute-функции и UnifiedCognitiveAgent.

Каждый тест:
- Проверен против реального кода (запущен через pytest)
- Имеет докстринг = контракт + формула + обоснование
- FAILED = реальный баг, не ошибка теста
- Содержит комментарий `# ЭТО БАГ` если поведение отличается от ожидаемого

---

## Часть II. Структура тестов

### UNIT: SubAgentManifest (`TestSubAgentManifestUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_manifest_creation` | Создание с 5 полями | PASS |
| `test_manifest_can_handle_matching` | can_handle() True при совпадении | PASS |
| `test_manifest_can_handle_mismatch` | can_handle() False при несовпадении | PASS |
| `test_manifest_default_description_empty` | description по умолчанию = "" | PASS |

### UNIT: SubAgentRegistry (`TestSubAgentRegistryUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_registry_empty_on_creation` | Новый registry пуст | PASS |
| `test_registry_register_adds_manifest` | register() добавляет manifest | PASS |
| `test_registry_duplicate_action_type_overwrites` | Дублирующий action_type перезаписывает | PASS |
| `test_registry_list_all_returns_copies` | list_all() возвращает все | PASS |

**Баг-001:** `register()` silently перезаписывает `_by_action_type` при дублировании. `_manifests` содержит оба, но `find_for_action()` возвращает только последний.

### UNIT: create_sub_agent_registry (`TestCreateSubAgentRegistryUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_registry_has_four_manifests` | 4 manifest | PASS |
| `test_registry_contains_lead_evaluation` | LeadEvaluator | PASS |
| `test_registry_contains_task_execution` | TaskExecutor | PASS |
| `test_registry_contains_invoice_processing` | InvoiceProcessor | PASS |
| `test_registry_contains_budget_enforcement` | BudgetEnforcer | PASS |

### UNIT: lead_evaluation_execute (`TestLeadEvaluationExecuteUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_returns_phi_psi_decision_reason` | Возвращает 4 ключа | PASS |
| `test_high_quality_agent_bids` | Высокое качество → BID | PASS |
| `test_low_quality_agent_phi_still_above_threshold` | phi всегда > 5.0 | PASS |
| `test_psi_exceeds_limit_declines` | psi > 0.7 → DECLINE | PASS |
| `test_phi_numeric` | phi — число | PASS |
| `test_psi_between_zero_and_one` | psi ∈ [0, 1] | PASS |

**Баг-002:** `bid_threshold=5.0` бесполезен — `phi` никогда не опускается ниже ~50. Порог никогда не срабатывает.

### UNIT: task_execution_execute (`TestTaskExecutionExecuteUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_starts_task_then_completes_it` | start() → complete() | PASS |
| `test_high_quality_completes_task` | Высокое качество → completed | PASS |
| `test_quality_formula` | quality = clamp(llm_quality * (1.1 - 0.1*complexity)) | PASS |
| `test_complexity_five_reduces_quality_with_boost` | complexity=5 → quality=0.58, attempts=2 | PASS |
| `test_below_target_quality_attempts_boost` | < target → +0.1, attempts=2 | PASS |
| `test_still_below_target_fails` | После boost всё ещё ниже → failed | PASS |
| `test_returns_timestamp` | Результат содержит timestamp | PASS |

### UNIT: invoice_processing_execute (`TestInvoiceProcessingExecuteUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_not_completed_returns_false` | Не COMPLETED → success=False | PASS |
| `test_completed_adds_revenue_to_balance` | COMPLETED + revenue → balance += revenue | PASS |
| `test_no_revenue_defaults_to_zero` | Нет revenue → earned=0 | PASS |
| `test_returns_timestamp` | Результат содержит timestamp | PASS |

### UNIT: budget_enforcement_execute (`TestBudgetEnforcementExecuteUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_balance_below_limit_halves_budget` | balance < limit → token_budget *= 0.5 | PASS |
| `test_balance_below_limit_with_min_floor` | Минимум 10.0 | PASS |
| `test_balance_above_limit_unchanged` | balance >= limit → без изменений | PASS |
| `test_balance_exactly_at_limit_unchanged` | balance == limit → без изменений | PASS |
| `test_returns_balance_and_limit` | Результат содержит balance, limit | PASS |

### UNIT: UnifiedCognitiveAgent (`TestUnifiedCognitiveAgentUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_creation_stores_core_agent` | core_agent сохранён | PASS |
| `test_list_capabilities_returns_four` | 4 capability | PASS |
| `test_dispatch_lead_evaluation` | dispatch lead_evaluation | PASS |
| `test_dispatch_task_execution` | dispatch task_execution | PASS |
| `test_dispatch_invoice_processing` | dispatch invoice_processing | PASS |
| `test_dispatch_budget_enforcement` | dispatch budget_enforcement | PASS |
| `test_dispatch_unknown_returns_error` | Неизвестный action → error | PASS |
| `test_dispatch_with_agent_in_kwargs_raises_typeerror` | agent в kwargs → TypeError | PASS |

**Баг-003:** `dispatch()` передаёт `agent=self.core_agent` + `**kwargs`. Если kwargs содержит `agent` → `TypeError: multiple values for keyword argument 'agent'`.

### UNIT: Legacy classes (`TestLegacyClassesUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_base_specialist_agent_stores_name` | BaseSpecialistAgent хранит name | PASS |
| `test_scout_specialist_name` | ScoutSpecialist.name = "Scout" | PASS |
| `test_scout_evaluate_lead` | evaluate_lead() → lead_evaluation | PASS |
| `test_worker_specialist_name` | WorkerSpecialist.name = "Worker" | PASS |
| `test_worker_execute_and_assess` | execute_and_assess() → task_execution | PASS |
| `test_finance_specialist_name` | FinanceSpecialist.name = "Finance" | PASS |
| `test_finance_process_invoice` | process_invoice() → invoice_processing | PASS |
| `test_finance_enforce_budget_cuts` | enforce_budget_cuts() → budget_enforcement | PASS |
| `test_specialist_subroutine_wrong_action` | Неверный action_type → error | PASS |
| `test_scout_agent_alias` | ScoutAgent is ScoutSpecialist | PASS |
| `test_worker_agent_alias` | WorkerAgent is WorkerSpecialist | PASS |
| `test_finance_agent_alias` | FinanceAgent is FinanceSpecialist | PASS |

### PAIR: UCA + Registry (`TestPairUCARegistry`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_dispatch_uses_registry_find` | dispatch() через registry.find_for_action() | PASS |

### PAIR: task_execution + Task (`TestPairTaskExecutionTask`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_execution_changes_task_status_to_completed` | Высокое качество → COMPLETED | PASS |
| `test_execution_changes_task_status_to_failed` | Низкое качество → FAILED | PASS |

### INTEGRITY: Архитектурные инварианты (`TestIntegrityAgents`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_registry_duplicate_action_type_silent_overwrite` | Silent overwrite | PASS |
| `test_dispatch_duplicate_agent_kwarg` | TypeError при agent в kwargs | PASS |
| `test_invoice_processing_mutates_agent_metrics` | Side effect на balance | PASS |
| `test_budget_enforcement_mutates_agent_metrics` | Side effect на token_budget | PASS |
| `test_all_execute_functions_return_dict` | Все возвращают dict | PASS |
| `test_task_execution_quality_clamped_to_one` | quality <= 1.0 | PASS |
| `test_task_execution_quality_floor_at_zero` | quality >= 0.0 | PASS |

### REGRESSION: Старые баги (`TestRegressionAgents`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_create_sub_agent_registry_always_four` | Всегда 4 manifest | PASS |
| `test_uca_list_capabilities_always_four` | Всегда 4 capability | PASS |
| `test_legacy_aliases_stable` | Алиасы неизменны | PASS |
| `test_lead_evaluation_thresholds_stable` | Пороги стабильны | PASS |

---

## Часть III. Сводка багов

| ID | Модуль | Описание | Серьёзность |
|----|--------|----------|-------------|
| BUG-001 | agents/core.py | `register()` silently перезаписывает duplicate action_type | LOW |
| BUG-002 | agents/core.py | `bid_threshold=5.0` бесполезен — phi всегда > 50 | LOW |
| BUG-003 | agents/core.py | `dispatch()` падает при `agent` в kwargs — duplicate keyword | **CRITICAL** |

---

## Часть IV. Статистика

- **Всего тестов:** 69
- **Пройдено:** 69
- **FAILED:** 0
- **Багов найдено:** 3 (1 CRITICAL)
