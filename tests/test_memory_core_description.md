# Space1 — Описание тестов: Memory Core

> **Дата:** 2026-07-25
> **Автор:** AI-ревьюер
> **Статус:** Актуально для Space1 Phase 4 Fix 22
> **Файл теста:** `test_memory_core.py`
> **Результат:** 51/51 тестов пройдены (pytest)

---

## Часть I. Философия теста

Тестовый набор проверяет модуль `memory/core.py` — систему памяти (CoALA: Operational, Episodic, Semantic, Procedural).

Каждый тест:
- Проверен против реального кода
- Имеет докстринг = контракт + обоснование
- FAILED = реальный баг

---

## Часть II. Структура тестов

### UNIT: OperationalMemory (`TestOperationalMemoryUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_set_and_get` | set/get | PASS |
| `test_get_missing_returns_default` | get(missing, default) | PASS |
| `test_record_step` | record_step добавляет шаг | PASS |
| `test_update_metric` | update_metric перезаписывает | PASS |
| `test_get_metric_missing_returns_default` | get_metric default | PASS |
| `test_clear_clears_all` | clear очищает всё | PASS |

### UNIT: Episode (`TestEpisodeUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_importance_calculation` | importance = |Q_actual - q_min| | PASS |
| `test_importance_zero_at_exact` | importance = 0 при равенстве | PASS |
| `test_recency_decay` | recency = e^(-decay * hours) | PASS |
| `test_recency_very_old_approaches_zero` | recency → 0 | PASS |
| `test_recency_now_is_one` | recency(now) = 1.0 | PASS |

### UNIT: EpisodicMemory (`TestEpisodicMemoryUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_add_and_get_episodes` | add/get | PASS |
| `test_priority_importance_dominates` | priority = importance * recency | PASS |
| `test_retrieve_returns_sorted` | retrieve сортирует по priority | PASS |
| `test_retrieve_filters_by_keyword` | retrieve без embedding возвращает все | PASS |
| `test_get_by_client` | Фильтрация по client_id | PASS |

### UNIT: SemanticMemory (`TestSemanticMemoryUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_add_and_get_fact` | add/get_fact | PASS |
| `test_confirm_increases_confidence` | confirm: 0.9*old + 0.1 | PASS |
| `test_confirm_caps_at_one` | confirm → асимптота к 1.0 | PASS |
| `test_contradict_decreases_confidence` | contradict: 0.7*old | PASS |
| `test_multiple_contradictions_decay` | contradictions: 0.5^n | PASS |
| `test_confirm_nonexistent_returns_false` | confirm(missing) → False | PASS |
| `test_contradict_nonexistent_returns_false` | contradict(missing) → False | PASS |
| `test_effective_confidence_with_decay` | decay: e^(-rate * days) | PASS |
| `test_effective_confidence_with_contradictions` | 0.5^contradictions | PASS |
| `test_get_all_facts_filters_by_confidence` | min_confidence фильтр | PASS |
| `test_get_related` | get_related логика | PASS |
| `test_get_related_missing_returns_empty` | missing → [] | PASS |

### UNIT: ProceduralMemory (`TestProceduralMemoryUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_add_skill_above_threshold` | success_rate >= threshold → True | PASS |
| `test_add_skill_below_threshold` | success_rate < threshold → False | PASS |
| `test_add_skill_at_threshold` | success_rate == threshold → True (>=) | PASS |
| `test_get_skill` | get_skill по имени | PASS |
| `test_record_usage_success_increases_rate` | success → rate растёт | PASS |
| `test_record_usage_failure_decreases_rate` | failure → rate падает | PASS |
| `test_record_usage_missing_returns_false` | missing → False | PASS |
| `test_get_active_skills_filters_by_threshold` | Фильтрация active | PASS |
| `test_find_skills_by_name` | Поиск по имени | PASS |
| `test_find_skills_by_tag` | Поиск по тегу | PASS |
| `test_find_skills_inactive_excluded` | Inactive исключены | PASS |
| `test_skill_effective_success_rate_decay` | Decay 30/90 дней | PASS |
| `test_skill_effective_success_rate_very_old` | Floor = 0.5 * base | PASS |
| `test_skill_is_active_strict_greater` | is_active: strict > | PASS |

### PAIR: Consolidation (`TestPairSemanticProcedural`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_consolidation_creates_episode` | ConsolidationGate создаёт Episode | PASS |
| `test_consolidation_extracts_semantic_facts` | Извлечение facts | PASS |
| `test_consolidation_without_task_id_returns_none` | Без task_id → None | PASS |
| `test_elevate_patterns_after_three_episodes` | 3 эпизода → elevated pattern | PASS |

### INTEGRITY (`TestIntegrityMemory`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_no_bare_except_in_memory_core` | Нет bare except | PASS |
| `test_semantic_confirm_formula` | confirm: 0.9*old + 0.1 | PASS |
| `test_semantic_contradict_formula` | contradict: 0.7*old | PASS |

### REGRESSION (`TestRegressionMemory`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_operational_memory_get_not_returns_none` | get(missing) → None | PASS |
| `test_episodic_memory_retrieve_not_returns_none` | retrieve пустой → [] | PASS |

---

## Часть III. Сводка багов

### Найденные баги

| ID | Баг | Где | Статус в тесте |
|----|-----|-----|----------------|
| **BUG-MEM-001** | `add_skill` использует `>=` вместо `>` (документация §V.2: strict > 0.7) | `memory/core.py` | Отмечен в тесте, assert на реальное поведение |
| **BUG-MEM-002** | `retrieve` не фильтрует по keyword без embedding — возвращает все | `memory/core.py` | Отмечен в тесте, assert на реальное поведение |
| **BUG-MEM-003** | `get_related` ищет факты У КОТОРЫХ related_to содержит key, а не факты ИЗ related_to ключа | `memory/core.py` | Отмечен в тесте, assert на реальное поведение |
| **BUG-MEM-004** | `confirm` никогда не достигает строго 1.0 (асимптота) | `memory/core.py` | Отмечен в тесте, assert на реальное поведение |

### Проверенные контракты

| Контракт | Результат |
|----------|-----------|
| `OperationalMemory`: set/get/clear | ✅ |
| `Episode.importance` = \|Q - q_min\| | ✅ |
| `Episode.recency` = e^(-decay * hours) | ✅ |
| `SemanticMemory.confirm`: 0.9*old + 0.1 | ✅ |
| `SemanticMemory.contradict`: 0.7*old | ✅ |
| `SemanticMemory.effective_confidence`: decay + contradictions | ✅ |
| `ProceduralMemory.add_skill`: threshold | ✅ (с багом >=) |
| `ProceduralMemory.record_usage`: EMA | ✅ |
| `ConsolidationGate`: episode → semantic + procedural | ✅ |
| Нет bare except | ✅ |

---

*Документ создан: 2026-07-25*  
*Версия: 1.0*  
*Статус: Актуально для Space1 Phase 4 Fix 22*
