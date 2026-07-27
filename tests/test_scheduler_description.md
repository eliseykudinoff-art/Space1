# Space1 — Описание тестов: Scheduler (AIOSScheduler)

> **Дата:** 2026-07-25
> **Автор:** AI-ревьюер
> **Статус:** Актуально для Space1 Phase 4 Fix 22
> **Файл теста:** `test_scheduler.py`
> **Результат:** 22/22 тестов пройдены (pytest)

---

## Часть I. Философия теста

Тестовый набор проверяет модуль `orchestrator/scheduler.py` — планировщик задач (AIOSScheduler).

Каждый тест:
- Проверен против реального кода (запущен через pytest)
- Имеет докстринг = контракт + обоснование
- FAILED = реальный баг, не ошибка теста
- Содержит комментарий `# ЭТО БАГ` если поведение отличается от ожидаемого

---

## Часть II. Структура тестов

### UNIT: deserialize_task (`TestDeserializeTaskUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_deserialize_basic` | Корректная десериализация всех полей | PASS |
| `test_deserialize_invalid_priority_defaults_to_medium` | INVALID → MEDIUM | PASS |
| `test_deserialize_none_deadline` | None deadline → None | PASS |
| `test_deserialize_source_stored_in_attribute_not_metadata` | source в attr, не metadata | PASS |

### UNIT: add/pop (`TestSchedulerAddPopUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_add_task_increases_queue` | add → размер +1 | PASS |
| `test_pop_next_task_returns_highest_priority` | CRITICAL > HIGH > LOW | PASS |
| `test_pop_empty_queue_returns_none` | Пустая → None | PASS |
| `test_pop_removes_from_queue` | pop удаляет | PASS |

### UNIT: OWNER_DIRECT приоритет (`TestSchedulerOwnerDirectUnit`) — БАГ

| Тест | Что проверяет | Реальное поведение | Статус |
|------|---------------|-------------------|--------|
| `test_owner_direct_does_not_override_marketplace` | OWNER > MARKET | MARKET первым | PASS (баг) |
| `test_all_tasks_treated_as_marketplace` | Смешанные source | Только priority | PASS (баг) |
| `test_source_attribute_vs_metadata` | source attr vs metadata | metadata None | PASS (root cause) |

### UNIT: Persistence (`TestSchedulerPersistenceUnit`) — БАГ

| Тест | Что проверяет | Реальное поведение | Статус |
|------|---------------|-------------------|--------|
| `test_save_queue_does_not_create_file` | Файл создаётся | Файл НЕ создан | PASS (баг) |
| `test_load_queue_returns_empty` | Задачи восстанавливаются | Пусто | PASS (баг) |
| `test_load_queue_bad_json_returns_empty` | Битый JSON → пусто | Пусто | PASS |
| `test_clear_removes_file` | clear удаляет файл | Удаляет | PASS |

### UNIT: list_queue (`TestSchedulerListQueueUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_list_queue_returns_copy` | Копия, не оригинал | PASS |
| `test_list_queue_order_before_pop` | FIFO до pop | PASS |

### INTEGRITY (`TestIntegrityScheduler`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_bare_except_in_scheduler` | except Exception ×4 | PASS (баг) |
| `test_save_queue_atomic_write` | os.replace присутствует | PASS |
| `test_scheduler_checks_metadata_not_source_attr` | metadata.get('source') | PASS (баг) |

### REGRESSION (`TestRegressionScheduler`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_pop_does_not_crash_on_empty` | None, не Exception | PASS |
| `test_task_source_is_enum_not_string` | TaskSource enum | PASS |

---

## Часть III. Сводка багов

### Найденные баги

| ID | Баг | Где | Почему важно | Статус в тесте |
|----|-----|-----|-------------|----------------|
| **BUG-SCHED-001** | `source` в `task.source`, scheduler ищет в `metadata.get('source')` | `scheduler.py:pop_next_task` | OWNER_DIRECT приоритет не работает — нарушение §I.3 | Assert на реальное поведение |
| **BUG-SCHED-002** | `_save_queue` падает на `TaskSource` enum JSON serialization | `scheduler.py:_save_queue` | Persistence полностью сломан — очередь не сохраняется | Assert на реальное поведение |
| **BUG-SCHED-003** | `except Exception: pass` ×4 | `scheduler.py:62,72,76,115` | Ошибки маскируются — невозможно диагностировать | Assert на реальное поведение |

### Проверенные контракты (багов нет)

| Контракт | Результат |
|----------|-----------|
| `deserialize_task` — корректная десериализация | ✅ |
| `add_task` → размер очереди +1 | ✅ |
| `pop_next_task` — сортировка по priority (CRITICAL>HIGH>LOW) | ✅ |
| `pop_next_task` — пустая очередь → None | ✅ |
| `list_queue` — возвращает копию | ✅ |
| `_save_queue` — использует atomic write (os.replace) | ✅ |
| `clear` — удаляет файл | ✅ |

---

## Часть IV. Параметры теста

### Запуск

```bash
export PYTHONPATH=/path/to/space1/src
pytest tests/test_scheduler.py -v
```

### Зависимости

- `space1.orchestrator.scheduler` (AIOSScheduler, deserialize_task)
- `space1.models.task` (Task, TaskPriority, TaskStatus, TaskSource)
- `pytest`

### Покрытие

- **deserialize_task:** 4 теста
- **add/pop:** 4 теста
- **OWNER_DIRECT:** 3 теста (2 бага)
- **Persistence:** 4 теста (1 баг)
- **list_queue:** 2 теста
- **INTEGRITY:** 3 теста (2 бага)
- **REGRESSION:** 2 теста

**Итого: 22 теста, 22 пройдены, 0 skipped, 0 xfailed.**

---

*Документ создан: 2026-07-25*  
*Версия: 1.0*  
*Статус: Актуально для Space1 Phase 4 Fix 22*
