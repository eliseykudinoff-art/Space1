# Space1 — Описание тестов: AIOSScheduler (Планировщик задач)

> **Дата:** 2026-07-25
> **Автор:** AI-ревьюер
> **Статус:** Актуально для Space1 Phase 4 Fix 22
> **Файл теста:** `test_scheduler_full.py`
> **Результат:** 37/37 тестов пройдены (pytest)

---

## Часть I. Философия теста

Этот тестовый набор проверяет модуль `orchestrator/scheduler.py` — планировщик задач AIOSScheduler.

Каждый тест:
- Проверен против реального кода (запущен через pytest)
- Имеет докстринг = контракт + формула + обоснование
- FAILED = реальный баг, не ошибка теста
- Содержит комментарий `# ЭТО БАГ` если поведение отличается от ожидаемого

---

## Часть II. Структура тестов

### UNIT: Инициализация (`TestSchedulerInitUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_scheduler_empty_on_creation` | Новый scheduler — пустая очередь | PASS |
| `test_scheduler_loads_from_file_if_exists` | Загрузка из файла при init | PASS |
| `test_scheduler_corrupted_file_ignored` | Повреждённый JSON игнорируется | PASS |

### UNIT: Приоритетная очередь (`TestSchedulerPriorityUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_pop_empty_returns_none` | Пустая очередь → None | PASS |
| `test_single_task_pop_returns_it` | Одна задача → возвращается | PASS |
| `test_priority_order_critical_first` | CRITICAL > HIGH > MEDIUM > LOW | PASS |
| `test_same_priority_fifo` | Одинаковый приоритет → FIFO | PASS |
| `test_pop_removes_from_queue` | pop удаляет задачу | PASS |

### UNIT: OWNER_DIRECT bypass (`TestSchedulerOwnerDirectUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_owner_direct_bypasses_marketplace_priority` | OWNER_DIRECT перед MARKETPLACE | PASS |
| `test_owner_direct_fifo_within_group` | FIFO внутри OWNER_DIRECT | PASS |
| `test_multiple_owner_direct_then_marketplace` | Все OWNER_DIRECT перед MARKETPLACE | PASS |

**Баг-001:** Документация говорит о FIFO внутри OWNER_DIRECT, но код сортирует по priority.value. HIGH перед LOW внутри группы.

### UNIT: Операции с очередью (`TestSchedulerQueueOpsUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_list_queue_returns_copy` | list_queue() возвращает копию | PASS |
| `test_list_queue_returns_list_type` | list_queue() → list | PASS |
| `test_clear_removes_all_tasks` | clear() удаляет все задачи | PASS |
| `test_clear_removes_file` | clear() удаляет файл | PASS |

### UNIT: deserialize_task (`TestDeserializeTaskUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_deserialize_basic_fields` | Все базовые поля восстанавливаются | PASS |
| `test_deserialize_invalid_priority_defaults_to_medium` | Невалидный priority → MEDIUM | PASS |
| `test_deserialize_invalid_status_defaults_to_pending` | Невалидный status → PENDING | PASS |
| `test_deserialize_none_deadlines` | None deadline → None | PASS |
| `test_deserialize_owner_direct_source` | source='OWNER_DIRECT' сохраняется | PASS |

### UNIT: Значения приоритетов (`TestPriorityValuesUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_critical_value` | CRITICAL.value = 1.0 | PASS |
| `test_high_value` | HIGH.value = 0.75 | PASS |
| `test_medium_value` | MEDIUM.value = 0.5 | PASS |
| `test_low_value` | LOW.value = 0.25 | PASS |
| `test_priority_ordering` | CRITICAL > HIGH > MEDIUM > LOW | PASS |

### PAIR: Scheduler + Task (`TestPairSchedulerTask`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_task_added_then_popped_has_correct_priority` | Приоритет сохраняется | PASS |
| `test_task_deadline_preserved` | Deadline сохраняется | PASS |

### PAIR: to_dict + deserialize_task (`TestPairDeserializeToDict`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_roundtrip_preserves_id_and_priority` | id и priority через roundtrip | PASS |
| `test_roundtrip_preserves_urgency_and_slack` | urgency_score и slack_time | PASS |

### INTEGRITY: Архитектурные инварианты (`TestIntegrityScheduler`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_save_queue_swallows_json_error` | _save_queue() глотает TypeError | PASS |
| `test_to_dict_source_is_enum_not_string` | Task.to_dict() возвращает enum | PASS |
| `test_pop_next_task_sorts_in_place` | pop() сортирует очередь in-place | PASS |
| `test_scheduler_filepath_is_string` | filepath — строка | PASS |

**Баг-002:** `Task.to_dict()` возвращает `TaskSource` enum в поле `source`. `json.dump()` не умеет сериализовать enum → TypeError. `_save_queue()` использует `except Exception: pass` — ошибка скрыта, файл не создаётся. **Персистентность сломана.**

**Баг-003:** `pop_next_task()` вызывает `self._queue.sort()` — side effect на внутреннем состоянии. До pop очередь в порядке добавления, после pop — отсортирована.

### REGRESSION: Старые баги (`TestRegressionScheduler`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_owner_direct_always_before_marketplace` | OWNER_DIRECT перед MARKETPLACE | PASS |
| `test_critical_always_before_low` | CRITICAL перед LOW | PASS |
| `test_deserialize_invalid_priority_not_crash` | Невалидный priority не crash | PASS |
| `test_deserialize_invalid_status_not_crash` | Невалидный status не crash | PASS |

---

## Часть III. Сводка багов

| ID | Модуль | Описание | Серьёзность |
|----|--------|----------|-------------|
| BUG-001 | scheduler.py | OWNER_DIRECT группа сортируется по priority, не FIFO | LOW |
| BUG-002 | models/task.py | `Task.to_dict()` возвращает TaskSource enum → json.dump падает → persistence сломана | **CRITICAL** |
| BUG-003 | scheduler.py | `pop_next_task()` сортирует очередь in-place — side effect | LOW |

---

## Часть IV. Статистика

- **Всего тестов:** 37
- **Пройдено:** 37
- **FAILED:** 0
- **Багов найдено:** 3 (1 CRITICAL)
