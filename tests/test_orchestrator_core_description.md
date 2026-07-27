# Space1 — Описание тестов: orchestrator/core.py (Orchestrator, CircuitBreaker, Pipeline Contracts)

> **Дата:** 2026-07-25
> **Автор:** AI-ревьюер
> **Статус:** Актуально для Space1 Phase 4 Fix 22
> **Файл теста:** `test_orchestrator_core.py`
> **Результат:** 64/64 тестов пройдены (pytest)

---

## Часть I. Философия теста

Этот тестовый набор проверяет модуль `orchestrator/core.py` — ядро оркестратора: SignalToContextSynthesizer, HomeostaticUtilityModulator, WeightCalibrator, CircuitBreaker, pipeline-контракты.

Каждый тест:
- Проверен против реального кода (запущен через pytest)
- Имеет докстринг = контракт + формула + обоснование
- FAILED = реальный баг, не ошибка теста
- Содержит комментарий `# ЭТО БАГ` если поведение отличается от ожидаемого

---

## Часть II. Структура тестов

### UNIT: SignalToContextSynthesizer (`TestSignalToContextSynthesizerUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_synthesize_returns_orchestrator_context` | Возвращает OrchestratorContext | PASS |
| `test_synthesize_survival_mode` | Низкие метрики → SURVIVAL | PASS |
| `test_synthesize_growth_mode` | Средние метрики → GROWTH | PASS |
| `test_synthesize_includes_task_title` | task.title в prompt | PASS |
| `test_synthesize_no_urgent_defaults_to_optimal` | Все pressures < 0.3 → optimal_equilibrium | PASS |
| `test_synthesize_memories_empty_when_optimal` | optimal → memories=[] | PASS |

### UNIT: HomeostaticUtilityModulator (`TestHomeostaticUtilityModulatorUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_low_pressure_fifty_percent` | pressure<0.5 → f=0.5+pressure | PASS |
| `test_optimal_pressure_one_hundred_percent` | 0.5≤pressure<1.0 → f=1.0 | PASS |
| `test_stress_pressure_reduces_utility` | 1.0≤pressure<2.0 → f<1.0 | PASS |
| `test_critical_pressure_ten_percent` | pressure≥2.0 → f=0.1 | PASS |
| `test_negative_pressures_ignored` | max(0, v) | PASS |
| `test_modulation_preserves_zero_base` | base=0 → U=0 | PASS |

### UNIT: WeightCalibrator (`TestWeightCalibratorUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_default_weights_sum_to_one` | Сумма = 1.0 | PASS |
| `test_default_weights_values` | profit=0.30, rep=0.25, evo=0.20, qual=0.25 | PASS |
| `test_high_balance_boosts_profit` | balance>0.3 → profit↑ | PASS |
| `test_high_stress_boosts_quality` | stress>0.3 → quality↑ | PASS |
| `test_high_knowledge_boosts_evolution` | knowledge>0.3 → evolution↑ | PASS |
| `test_all_weights_positive` | Все > 0 | PASS |

**Баг-001:** При экстремальных pressures `min_floor=0.01` не гарантируется после нормализации — веса могут быть < 0.01 (но > 0).

### UNIT: CircuitBreaker (`TestCircuitBreakerUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_initial_state_closed` | state=CLOSED | PASS |
| `test_before_call_closed_no_raise` | CLOSED → no raise | PASS |
| `test_record_success_stays_closed` | success → CLOSED | PASS |
| `test_failures_to_open` | threshold failures → OPEN | PASS |
| `test_open_raises_on_before_call` | OPEN → raises | PASS |
| `test_open_to_half_open_after_cooldown` | OPEN + cooldown → HALF_OPEN | PASS |
| `test_half_open_to_closed_after_successes` | HALF_OPEN + successes → CLOSED | PASS |
| `test_half_open_to_open_on_failure` | HALF_OPEN + failure → OPEN | PASS |
| `test_record_success_resets_failure_count` | failure_count=0 после success | PASS |
| `test_budget_overrun_triggers_open` | 2 overruns → OPEN | PASS |
| `test_global_trip_h_critical` | H<0.2 → OPEN | PASS |
| `test_global_trip_platform_risk` | platform_risk>0.8 → OPEN | PASS |

**Баг-002:** `record_success()` сбрасывает `failure_count`, но НЕ сбрасывает `_cascade_depth` и `_budget_violations` в состоянии OPEN — несогласованный сброс.

### UNIT: SimulatedResponse & MCPToolClient (`TestSimulatedResponseUnit`, `TestMCPToolClientUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_creation` | 5 полей dataclass | PASS |
| `test_execute_tool_returns_dict` | success=True | PASS |

### UNIT: calculate_token_cost & parse_response_content (`TestCalculateTokenCostUnit`, `TestParseResponseContentUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_known_model` | tokens * rate / 1000 | PASS |
| `test_unknown_model_fallback` | fallback 0.002 | PASS |
| `test_extracts_code_block` | python code block | PASS |
| `test_extracts_json_block` | json code block | PASS |
| `test_no_code_returns_none` | None при отсутствии | PASS |
| `test_curly_brace_fallback` | fallback на curly braces | PASS |

### UNIT: Pipeline contract functions (`TestClassifyTaskUnit`, `TestRenderStatusBlockUnit`, `TestPredictEstimatesUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_returns_tuple_three` | classify_task → 3 значения | PASS |
| `test_h_tz_between_zero_and_one` | h_tz ∈ [0,1] | PASS |
| `test_returns_string` | render_status_block → str | PASS |
| `test_contains_homeostasis` | "Homeostasis H" в выводе | PASS |
| `test_respects_max_length` | len ≤ max_length | PASS |
| `test_returns_tuple_three` | predict_estimates → 3 значения | PASS |
| `test_all_clamped_zero_to_one` | phi,q,psi ∈ [0,1] | PASS |
| `test_n_completed_affects_weights` | n_completed < 5 vs ≥ 20 | PASS |
| `test_with_history_uses_bayesian` | Bayesian update | PASS |
| `test_empty_x_defaults` | x_avg=0.5 при пустом x | PASS |

### UNIT: select_executor, reflect, decide_with_pipeline_context (`TestSelectExecutorUnit`, `TestReflectUnit`, `TestDecideWithPipelineContextUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_no_eligible_raises` | trust<0.3 → NoEligibleExecutorError | PASS |
| `test_single_eligible_returns_it` | Один eligible → возвращается | PASS |
| `test_cold_start_selects_unselected` | n_i=0 → немедленный выбор | PASS |
| `test_zero_attempts_retry` | 0 attempts → RETRY | PASS |
| `test_three_attempts_escalate` | 3 attempts → ESCALATE | PASS |
| `test_high_psi_abandon` | psi>0.8 → ABANDON | PASS |
| `test_returns_decision_and_reason` | (Decision, str) | PASS |

### PAIR: CircuitBreaker + execution flow (`TestPairCircuitBreakerFlow`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_open_blocks_execution` | OPEN → before_call raises | PASS |
| `test_closed_allows_execution` | CLOSED → before_call ok | PASS |

### INTEGRITY: Архитектурные инварианты (`TestIntegrityOrchestrator`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_circuit_breaker_failure_count_not_reset_on_open` | failure_count сохраняется | PASS |
| `test_predict_estimates_clamps_negative_x` | Отрицательные x → clamp 0 | PASS |
| `test_weight_calibrator_all_weights_positive_after_extreme` | Все > 0 | PASS |
| `test_render_status_block_with_none_plan` | None plan → no error | PASS |

### REGRESSION: Старые баги (`TestRegressionOrchestrator`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_circuit_breaker_states_three_only` | Только 3 состояния | PASS |
| `test_predict_estimates_always_returns_three` | Всегда 3 значения | PASS |
| `test_classify_task_always_returns_three` | Всегда 3 значения | PASS |

---

## Часть III. Сводка багов

| ID | Модуль | Описание | Серьёзность |
|----|--------|----------|-------------|
| BUG-001 | orchestrator/core.py | WeightCalibrator: min_floor=0.01 не гарантируется после нормализации | LOW |
| BUG-002 | orchestrator/core.py | CircuitBreaker: record_success() сбрасывает failure_count, но не cascade_depth/budget_violations в OPEN | LOW |

---

## Часть IV. Статистика

- **Всего тестов:** 64
- **Пройдено:** 64
- **FAILED:** 0
- **Багов найдено:** 2
