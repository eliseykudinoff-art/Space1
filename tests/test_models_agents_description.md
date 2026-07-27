# Space1 — Описание тестов: Models Agents

> **Дата:** 2026-07-25
> **Автор:** AI-ревьюер
> **Статус:** Актуально для Space1 Phase 4 Fix 22
> **Файл теста:** `test_models_agents.py`
> **Результат:** 28/28 тестов пройдены (pytest)

---

## Часть I. Философия

Тестовый набор проверяет модуль `models/agents.py` — модели агента (Agent, AgentCapabilities, AgentMetrics, AgentContext).

---

## Часть II. Структура

### UNIT: AgentCapabilities (`TestAgentCapabilitiesUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_capabilities_defaults` | 17 факторов + backward-compatible | PASS |
| `test_capabilities_to_dict_structure` | nested dict с 4 секциями | PASS |
| `test_capabilities_custom_values` | Кастомные значения | PASS |
| `test_capabilities_17_factors` | Ровно 17 факторов (§IV.10) | PASS |

### UNIT: AgentMetrics (`TestAgentMetricsUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_metrics_defaults` | Default values | PASS |
| `test_rating_default` | rating = 0.5 | PASS |
| `test_rating_custom_reputation` | Weighted average | PASS |
| `test_rating_empty_vector` | {} → 0.0 | PASS |
| `test_rating_missing_dimensions` | get(k, 0.5) | PASS |
| `test_metrics_to_dict` | Структура сериализации | PASS |
| `test_reputation_vector_is_dict_not_list` | dict, не list (§IV.5) | PASS (баг) |

### UNIT: Agent (`TestAgentUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_agent_creation` | Defaults | PASS |
| `test_agent_to_dict` | Сериализация | PASS |
| `test_agent_status_enum_value` | Enum values | PASS |

### UNIT: AgentContext (`TestAgentContextUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_context_creation` | Defaults | PASS |
| `test_context_to_dict` | agent_id, не вложенный agent | PASS |

### UNIT: create_agent (`TestCreateAgentUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_create_agent_generates_id` | Auto-generated id (8 chars) | PASS |
| `test_create_agent_defaults` | status=IDLE | PASS |

### UNIT: from_dict (`TestFromDictUnit`) — БАГ

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_agent_no_from_dict` | Отсутствует | PASS (баг) |
| `test_capabilities_no_from_dict` | Отсутствует | PASS (баг) |
| `test_metrics_no_from_dict` | Отсутствует | PASS (баг) |
| `test_context_no_from_dict` | Отсутствует | PASS (баг) |

### PAIR (`TestPairAgentTask`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_agent_can_have_task` | n_active_tasks | PASS |

### INTEGRITY (`TestIntegrityAgents`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_no_bare_except_in_agents` | Нет bare except | PASS |
| `test_reputation_vector_6_dimensions` | 6 измерений | PASS |
| `test_rating_weights_sum_to_one` | Веса = 1.0 | PASS |

### REGRESSION (`TestRegressionAgents`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_agent_not_returns_none` | Не None | PASS |
| `test_reputation_vector_not_none` | Не None | PASS |

---

## Часть III. Сводка багов

| ID | Баг | Где | Статус |
|----|-----|-----|--------|
| **BUG-AGENT-001** | `from_dict` отсутствует везде | `models/agents.py` | Assert (×4) |
| **BUG-AGENT-002** | `reputation_vector` = dict, не 6-мерный вектор | `models/agents.py` | Assert |

---

## Часть IV. Параметры

### Запуск
```bash
pytest tests/test_models_agents.py -v
```

### Зависимости
- `space1.models.agents` (Agent, AgentCapabilities, AgentMetrics, AgentContext, AgentStatus, create_agent)
- `pytest`

**Итого: 28 тестов, 28 пройдены, 0 skipped, 0 xfailed.**

---
*Документ создан: 2026-07-25*
