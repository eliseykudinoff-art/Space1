# Space1 — Описание тестов: Models Task

> **Дата:** 2026-07-25
> **Автор:** AI-ревьюер
> **Статус:** Актуально для Space1 Phase 4 Fix 22
> **Файл теста:** `test_models_task.py`
> **Результат:** 30/30 тестов пройдены (pytest)

---

## Часть I. Философия теста

Тестовый набор проверяет модуль `models/task.py` — модель задачи (Task).

Каждый тест:
- Проверен против реального кода
- Имеет докстринг = контракт + обоснование
- FAILED = реальный баг
- Содержит комментарий `# ЭТО БАГ`

---

## Часть II. Структура тестов

### UNIT: Task creation (`TestTaskCreationUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_task_creation_minimal` | Defaults при минимальном конструкторе | PASS |
| `test_task_creation_full` | Все поля сохраняются | PASS (auto-gen metadata) |
| `test_task_source_string_accepted` | source="OWNER_DIRECT" (str) | PASS |

### UNIT: Task properties (`TestTaskPropertiesUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_is_overdue_past_deadline_raises_value_error` | Прошлый deadline → ValueError | PASS |
| `test_is_overdue_future_deadline` | Будущий deadline → False | PASS |
| `test_is_overdue_none_deadline` | None → False | PASS |
| `test_is_critical_high_priority_is_false` | HIGH → False (только CRITICAL) | PASS (вопрос) |
| `test_is_critical_low_priority` | LOW → False | PASS |
| `test_remaining_time_attribute_missing` | remaining_time отсутствует | PASS (баг) |

### UNIT: to_dict (`TestTaskToDictUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_to_dict_basic` | Все поля в dict | PASS |
| `test_to_dict_none_deadline` | None deadline → None | PASS |

### UNIT: from_dict (`TestTaskFromDictUnit`) — БАГ

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_from_dict_missing` | from_dict отсутствует | PASS (баг) |

### UNIT: Enums (`TestTaskPriorityUnit`, `TestTaskStatusUnit`, `TestTaskSourceUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_priority_ordering` | CRITICAL > HIGH > MEDIUM > LOW | PASS |
| `test_priority_values` | Конкретные значения | PASS |
| `test_status_values` | 5 статусов | PASS |
| `test_source_values` | MARKETPLACE, OWNER_DIRECT | PASS |
| `test_source_enum_not_equal_string` | Enum != str | PASS (баг) |

### UNIT: Factory (`TestCreateTaskUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_create_task_basic` | Auto-generated id | PASS |
| `test_create_task_with_params` | Параметры передаются | PASS |

### UNIT: calculate_schedule (`TestCalculateScheduleUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_schedule_all_fit` | Все помещаются | PASS |
| `test_schedule_sorts_by_created_at_not_urgency` | Сортировка по created_at | PASS (баг) |
| `test_schedule_partial_fit` | Частичное расписание | PASS |
| `test_schedule_zero_available` | 0 часов → все dropped | PASS |

### PAIR: Task → Scheduler (`TestPairTaskScheduler`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_task_priority_in_scheduler` | HIGH перед LOW | PASS |

### INTEGRITY (`TestIntegrityTask`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_no_bare_except_in_task` | Нет bare except | PASS |
| `test_task_has_to_dict` | to_dict есть | PASS |
| `test_task_missing_from_dict` | from_dict отсутствует | PASS (баг) |

### REGRESSION (`TestRegressionTask`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_task_not_returns_none` | Не None | PASS |
| `test_priority_enum_not_string` | TaskPriority enum | PASS |

---

## Часть III. Сводка багов

| ID | Баг | Где | Статус |
|----|-----|-----|--------|
| **BUG-TASK-001** | `from_dict` отсутствует — нет десериализации | `models/task.py` | Assert |
| **BUG-TASK-002** | `to_dict['source']` — enum, не строка → JSON сломается | `models/task.py` | Assert |
| **BUG-TASK-003** | `TaskSource` enum != str — scheduler сравнение даст False | `models/task.py` | Assert |
| **BUG-TASK-004** | `urgency_score` и `slack_time` перезаписываются `__post_init__` | `models/task.py` | Assert |
| **BUG-TASK-005** | `remaining_time` не реализован | `models/task.py` | Assert |
| **BUG-TASK-006** | `calculate_schedule` сортирует по `created_at`, не по `urgency_score` | `models/task.py` | Assert |
| **BUG-TASK-007** | `is_critical` только для CRITICAL (HIGH не включается) | `models/task.py` | Assert |

---

## Часть IV. Параметры

### Запуск
```bash
pytest tests/test_models_task.py -v
```

### Зависимости
- `space1.models.task` (Task, TaskPriority, TaskStatus, TaskSource, create_task, calculate_schedule)
- `space1.orchestrator.scheduler` (AIOSScheduler)
- `pytest`

**Итого: 30 тестов, 30 пройдены, 0 skipped, 0 xfailed.**

---
*Документ создан: 2026-07-25*
