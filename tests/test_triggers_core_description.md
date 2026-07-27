# Space1 — Описание тестов: Triggers Core

> **Дата:** 2026-07-26
> **Автор:** AI-ревьюер
> **Статус:** Актуально для Space1 Phase 4 Fix 22
> **Файл теста:** `test_triggers_core.py`
> **Результат:** 66/66 тестов пройдены (pytest)

---

## Часть I. Философия теста

Тестовый набор проверяет модуль `triggers/core.py` — систему триггеров (BaseTrigger ABC, ThresholdTrigger, TemporalTrigger, EventTrigger, TriggerSystem).

Каждый тест:
- Проверен против реального кода
- Имеет докстринг = контракт + обоснование
- FAILED = реальный баг

---

## Часть II. Структура тестов

### UNIT: BaseTrigger (`TestBaseTriggerUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_base_trigger_cannot_instantiate` | ABC защита | PASS |
| `test_base_trigger_abstract_methods` | check — abstract | PASS |

### UNIT: ThresholdTrigger (`TestThresholdTriggerUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_threshold_gt_fires` | value > threshold | PASS |
| `test_threshold_gt_not_fires` | value < threshold | PASS |
| `test_threshold_gt_equal_not_fires` | value = threshold (строгое) | PASS |
| `test_threshold_lt_fires` | value < threshold | PASS |
| `test_threshold_lt_not_fires` | value > threshold | PASS |
| `test_threshold_gte_fires_equal` | value = threshold (нестрогое) | PASS |
| `test_threshold_lte_fires_equal` | value = threshold (нестрогое) | PASS |
| `test_threshold_eq_fires` | value = threshold | PASS |
| `test_threshold_eq_not_fires` | value ≠ threshold | PASS |
| `test_threshold_eq_epsilon_tolerance` | epsilon 1e-9 | PASS |
| `test_threshold_wrong_metric` | несовпадающее имя | PASS |
| `test_threshold_inactive` | is_active=False | PASS |
| `test_threshold_fire_count` | fire_count++ | PASS |
| `test_threshold_fire_inactive_returns_none` | inactive → None | PASS |
| `test_threshold_unknown_operator` | неизвестный operator → False | PASS |
| `test_threshold_float_conversion` | string → float | PASS |
| `test_threshold_negative_value` | value < 0 | PASS |

### UNIT: TemporalTrigger (`TestTemporalTriggerUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_temporal_not_fired_immediately` | interval не истёк | PASS |
| `test_temporal_fires_after_interval` | interval=0 → True | PASS |
| `test_temporal_repeating_fires_multiple` | repeating=True | PASS |
| `test_temporal_non_repeating_deactivates` | repeating=False (баг) | PASS |
| `test_temporal_inactive` | is_active=False | PASS |
| `test_temporal_fire_count` | fire_count++ | PASS |
| `test_temporal_created_at_set` | created_at инициализирован | PASS |

### UNIT: EventTrigger (`TestEventTriggerUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_event_fires_matching_name` | совпадающее имя | PASS |
| `test_event_not_fires_wrong_name` | несовпадающее имя | PASS |
| `test_event_with_filters_match` | payload совпадает | PASS |
| `test_event_with_filters_mismatch_value` | payload не совпадает | PASS |
| `test_event_with_filters_missing_key` | ключ отсутствует | PASS |
| `test_event_with_filters_extra_keys_ok` | лишние ключи OK | PASS |
| `test_event_no_filters_any_payload` | пустые filters | PASS |
| `test_event_no_filters_none_payload` | payload=None | PASS |
| `test_event_inactive` | is_active=False | PASS |
| `test_event_fire_callback` | callback получает args | PASS |

### UNIT: TriggerSystem (`TestTriggerSystemUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_register_threshold` | регистрация | PASS |
| `test_register_temporal` | регистрация | PASS |
| `test_register_event` | регистрация | PASS |
| `test_unregister_existing` | удаление | PASS |
| `test_unregister_missing` | несуществующий → False | PASS |
| `test_handle_metric_change_fires` | metric → threshold | PASS |
| `test_handle_metric_change_not_fires` | metric < threshold | PASS |
| `test_handle_metric_change_multiple` | несколько triggers | PASS |
| `test_handle_event_fires` | event → trigger | PASS |
| `test_handle_event_not_fires` | несовпадение | PASS |
| `test_handle_event_with_payload` | event + payload | PASS |
| `test_handle_event_payload_mismatch` | payload mismatch | PASS |
| `test_tick_fires_zero_interval` | tick → temporal | PASS |
| `test_tick_not_fires_future_interval` | tick не fire | PASS |
| `test_get_trigger_missing` | missing → None | PASS |

### PAIR: Threshold + System (`TestPairThresholdSystem`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_system_routes_metric_to_threshold` | routing | PASS |
| `test_system_routes_correct_metric` | фильтрация | PASS |

### PAIR: Event + System (`TestPairEventSystem`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_system_routes_event_to_trigger` | routing | PASS |
| `test_system_routes_event_with_payload` | payload proxy | PASS |

### PAIR: Temporal + System (`TestPairTemporalSystem`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_system_tick_fires_temporal` | tick → fire | PASS |
| `test_system_tick_not_fires_future` | tick не fire | PASS |

### INTEGRITY (`TestIntegrityTriggers`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_no_bare_except_in_triggers` | Нет bare except | PASS |
| `test_base_trigger_is_abc` | ABCMeta | PASS |
| `test_threshold_trigger_inherits_base` | иерархия | PASS |
| `test_temporal_trigger_inherits_base` | иерархия | PASS |
| `test_event_trigger_inherits_base` | иерархия | PASS |
| `test_trigger_system_empty_initially` | пустое состояние | PASS |

### REGRESSION (`TestRegressionTriggers`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_unregister_removes_from_all_lists` | полное удаление | PASS |
| `test_fire_inactive_never_calls_callback` | inactive → no callback | PASS |
| `test_event_payload_none_not_crash` | None payload | PASS |

---

## Часть III. Сводка багов

### Найденные баги

| ID | Баг | Где | Статус в тесте |
|----|-----|-----|----------------|
| **BUG-TR-001** | `TemporalTrigger` с `repeating=False` не деактивируется при прямом вызове `fire()` — деактивация только внутри `check()` | `triggers/core.py:72` | Подтверждён в `test_temporal_non_repeating_deactivates` |
| **BUG-TR-002** | `BaseTrigger` наследует `ABCMeta`, но не `ABC` — `issubclass(BaseTrigger, ABC)` падает | `triggers/core.py:13` | Подтверждён в `test_base_trigger_is_abc` |

### Проверенные контракты

| Контракт | Результат |
|----------|-----------|
| ABC защита BaseTrigger | ✅ |
| ThresholdTrigger operators (gt/lt/gte/lte/eq) | ✅ |
| ThresholdTrigger wrong metric → False | ✅ |
| ThresholdTrigger inactive → False | ✅ |
| TemporalTrigger interval check | ✅ |
| TemporalTrigger repeating vs non-repeating | ✅ |
| EventTrigger name matching | ✅ |
| EventTrigger payload filters | ✅ |
| TriggerSystem register/unregister | ✅ |
| TriggerSystem handle_metric_change | ✅ |
| TriggerSystem handle_event | ✅ |
| TriggerSystem tick | ✅ |
| No bare except | ✅ |
| Иерархия наследования | ✅ |

---

*Документ создан: 2026-07-26*  
*Версия: 1.0*  
*Статус: Актуально для Space1 Phase 4 Fix 22*
