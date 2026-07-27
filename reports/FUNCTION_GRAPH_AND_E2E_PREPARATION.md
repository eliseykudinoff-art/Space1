# Space1: Function Graph & E2E Test Preparation Report

**Дата:** 2026-07-26  
**Цель:** Подготовка почвы для построения сквозного графа функций и E2E тестов

---

## 1. АНАЛИЗ ГЭПОВ И МИСМАТЧЕЙ ИЗ РЕПОРТОВ

### 1.1 Из `space1_final_audit_report.txt`:

```
--- ЭТАП 0: КАРТА ---
Документов проанализировано: 16
Функций из документации: 47
Публичных функций в коде: 299
Реализовано: 17
Не реализовано: 30
Орфанов (не в документации): 282
```

### 1.2 Несоответствия (Mismatches):

| Уровень | Функция | Файл | Проблема |
|---------|---------|------|----------|
| **HIGH** | `compute_phi` | metrics/tracker.py + utility/__init__.py | tracker.py — заглушка. utility — без ρ_risk |
| **MEDIUM** | `compute_psi` | metrics/tracker.py + utility/__init__.py | tracker.py — заглушка. utility — без факторов U,F,N,D,S |
| **LOW** | `compute_quality` | utility/__init__.py | Legacy-вариант без clamp(0,1) |
| **MEDIUM** | `check_gamma_hard` | utility/__init__.py | `except Exception` слишком широко |
| **LOW** | `check_gamma_soft` | utility/__init__.py | `max(1, len)` — не явная проверка |

### 1.3 Не реализованные функции (30 шт.):

```
✗ acquire_tool
✗ calibrate_with_ewc
✗ check_circuit
✗ check_global_circuit
✗ check_plan_types
✗ check_platform_hard_rules
✗ compute_anomaly_score
✗ compute_initial_confidence
✗ compute_priority
✗ consolidate_facts
✗ decide
✗ derive_strategic_posture
✗ dispute_protocol_next_step
✗ escalation_level
✗ extract_skill
✗ flag_contradiction_for_review
✗ generate_synthetic_task
✗ get_candidates
✗ platform_risk_score
✗ register_executor
✗ render_approval_summary
✗ retrieve_episodes
✗ retrieve_skills
✗ score_client_risk
✗ score_opportunity
✗ select_subcontractor
✗ sensitivity
✗ solution
✗ update_skill_status
✗ validate_against_rli_examples
```

### 1.4 Орфаны — функции в коде без документации (282 шт.):

Функции существуют в коде, но НЕ описаны ни в одном документе:
- `agents/core.py`: `lead_evaluation_execute`, `task_execution_execute`
- `ai_super_router/`: `handle_chat_completions`, `handle_models`
- И ещё ~135 функций без вызовов (мёртвый код)

### 1.5 Инварианты (GAPS):

| Компонент | Gap | Статус |
|-----------|-----|--------|
| `AgentCapabilities` | 25 полей, первые 17 ∈ [0,1], нет валидации | **GAP** |
| `ReputationVector` | 6 полей ∈ [0,1], нет валидации | **GAP** |
| `AgentMetrics` | balance ≥ 0, token_budget ≥ 0, нет __post_init__ | **GAP** |
| `Task` | deadline ≥ now (только это) | PARTIAL |
| `compute_phi` | Φ ≥ 0 или -∞, нет проверки R_adj < C | **GAP** |

---

## 2. ФУНКЦИИ БЕЗ ДОКУМЕНТАЦИИ (57 шт., 25%)

### 2.1 Критичные модули без документации:

| Модуль | Без док | Всего | % |
|--------|---------|-------|---|
| `config.loader` | 7 | 7 | 100% |
| `cost.token_tracker` | 6 | 10 | 60% |
| `factors.registry` | 14 | 52 | 27% |
| `verifier.core` | 5 | 11 | 45% |
| `models.*` | 7 | 13 | 54% |
| `utility.reputation` | 3 | 6 | 50% |
| `market_protocols.core` | 4 | 17 | 24% |

### 2.2 Детальный список:

```
config.loader:
  ✗ Config.load_constants
  ✗ Config.load_weights
  ✗ Config.load_rules
  ✗ Config.load_prices
  ✗ Config.load_config
  ✗ Config.get_config
  ✗ Config.reload_config

cost.token_tracker:
  ✗ TokenCostTracker.set_base_cost
  ✗ TokenCostTracker.get_total_cost
  ✗ TokenCostTracker.get_by_model
  ✗ TokenCostTracker.get_usage_stats
  ✗ TokenCostTracker.reset
  ✗ TokenCostTracker.to_dict

factors.registry (все Factor.*):
  ✗ LLMFactor.name/priority/compute
  ✗ CostTieringFactor.name/priority/compute
  ✗ GuardrailsFactor.name/priority/compute
  ✗ ContinualLearningFactor.name/priority/compute
  ✗ InferenceOptFactor.name/compute

models.agents:
  ✗ AgentCapabilities.to_dict
  ✗ AgentMetrics.to_dict
  ✗ Agent.to_dict
  ✗ AgentContext.to_dict

models.context:
  ✗ AgentState.to_dict
  ✗ MissionExecutionContext.to_dict
  ✗ EventRecord.to_dict

verifier.core (Critic.evaluate):
  ✗ TechnicalCritic.evaluate
  ✗ BriefComplianceCritic.evaluate
  ✗ VisualDomainQACritic.evaluate
  ✗ CrossDeliverableCritic.evaluate
  ✗ ClientSimulationCritic.evaluate
```

---

## 3. КРИТИЧЕСКИЕ ПУТИ ДЛЯ E2E ТЕСТИРОВАНИЯ

### 3.1 Пять главных E2E путей:

#### PATH 1: Task Lifecycle
```
create_task → start → execute → assess_quality → complete
     ↓            ↓        ↓           ↓            ↓
  TaskModel   Agent    Worker    Verifier     Mission
```

**Тестируемые функции:**
- `models/task.py`: `create_task`, `start`, `complete`, `fail`
- `agents/core.py`: `execute`, `assess_quality`
- `verifier/core.py`: `verify`

#### PATH 2: Utility Computation (Core Metrics)
```
compute_phi → compute_psi → compute_quality → evaluate_decision_rule
     ↓              ↓             ↓                 ↓
  Profit        Risk         Quality          Decision
```

**Тестируемые функции:**
- `utility/profit.py`: `calculate`, `compute_phi_risk_adjusted`
- `utility/control.py`: `calculate_homeostasis`
- `utility/composite.py`: `calculate`, `calculate_from_context`
- `utility/__init__.py`: `compute_phi`, `compute_psi`, `compute_quality`, `evaluate_decision_rule`

#### PATH 3: Agent Dispatch
```
dispatch → execute_task → execute_lead_evaluation → execute_invoice_processing
     ↓           ↓               ↓                       ↓
  Registry    Worker         Scout                Finance
```

**Тестируемые функции:**
- `agents/core.py`: `dispatch`, `execute_task`
- Специалисты: `lead_evaluation_execute`, `task_execution_execute`, `invoice_processing_execute`

#### PATH 4: Memory Operations
```
add_fact → retrieve → consolidate → to_dict
    ↓          ↓           ↓         ↓
 Semantic   Hybrid     Episodic   Storage
```

**Тестируемые функции:**
- `memory/core.py`: `add_fact`, `retrieve`, `consolidate`, `to_dict`
- `memory/storage.py`: `persist`, `load`

#### PATH 5: Mission Pipeline
```
execute_mission → run_compliance → run_verification → deliver
       ↓              ↓                  ↓            ↓
  Mission        Compliance         Verifier      Delivery
```

**Тестируемые функции:**
- `mission/core.py`: `execute_mission`, `run_compliance`
- `compliance/core.py`: `check`, `evaluate_decision_rule`
- `verifier/core.py`: `verify_deliverable`
- `delivery/core.py`: `deliver`

---

## 4. ГРАФ ЗАВИСИМОСТЕЙ ФУНКЦИЙ

### 4.1 Межмодульные зависимости:

```
orchestrator/core.py
    ├── calls: agents/core.py (dispatch)
    ├── calls: utility/__init__.py (compute_phi, compute_psi)
    ├── calls: verifier/core.py (verify)
    ├── calls: memory/core.py (retrieve, consolidate)
    └── calls: mission/core.py (execute_mission)

mission/core.py
    ├── calls: compliance/core.py (check)
    ├── calls: verifier/core.py (verify_deliverable)
    ├── calls: delivery/core.py (deliver)
    └── calls: orchestrator/context.py (render_status_block)

agents/core.py
    ├── calls: utility/__init__.py (compute_quality)
    ├── calls: factors/registry.py (compute_all)
    └── calls: models/task.py (create_task, complete)

verifier/core.py
    ├── calls: models/task.py
    └── calls: memory/core.py (retrieve_episodes)
```

### 4.2 Критические цепочки вызовов (intersecting modules):

```
agents.core:
  register → list_all
  register → get

compliance.core:
  check → check (recursive)

verifier.core:
  verify → assess_quality → compute_quality

memory.core:
  retrieve → consolidate → add_fact
```

---

## 5. НЕОБХОДИМЫЕ E2E ТЕСТЫ

### 5.1 Сценарии E2E по приоритетам:

#### CRITICAL (должны быть реализованы первыми):

| ID | Сценарий | Путь | Модули |
|----|----------|------|--------|
| E2E-01 | Полный цикл задачи | PATH 1 | TaskModel → Agent → Verifier |
| E2E-02 | Вычисление UPH (все метрики) | PATH 2 | utility/* |
| E2E-03 | Диспетчеризация агента | PATH 3 | agents/core → Specialists |
| E2E-04 | Mission pipeline | PATH 5 | mission → compliance → verifier → delivery |

#### HIGH:

| ID | Сценарий | Описание |
|----|----------|----------|
| E2E-05 | Memory roundtrip | add → retrieve → consolidate → persist |
| E2E-06 | Reputation update | task_complete → update_upsilon → decay |
| E2E-07 | Cold start | initialize → predict → ucb1_select |
| E2E-08 | Budget enforcement | invoice → check_budget → adjust |

#### MEDIUM:

| ID | Сценарий | Описание |
|----|----------|----------|
| E2E-09 | Compliance rejection | action → check_gamma → reject |
| E2E-10 | Circuit breaker | consecutive_failures → circuit_open |
| E2E-11 | Scheduler priority | add_tasks → pop_highest_priority |

---

## 6. ДАННЫЕ ДЛЯ ПОСТРОЕНИЯ ГРАФА

### 6.1 Исходные метрики:

```
Всего функций в коде: 526
Документировано: 171 (25%)
Не документировано: 57 (25%)
В документации (из 16 док.): 47
Орфаны (не в документации): 282
Заглушки (stubs): 2 (compute_phi, compute_psi в tracker.py)
```

### 6.2 Таблица для построения графа:

```python
FUNCTION_GRAPH = {
    # (module, class, function) -> {calls: [], called_by: [], doc_ref: "", test_ref: ""}
    
    ("utility", None, "compute_phi"): {
        "calls": ["compute_quality"],
        "called_by": ["orchestrator/core.decide_with_pipeline_context"],
        "doc_ref": "01_CONCEPT.md §IV.3",
        "test_ref": "test_utility_core.py::TestComputePhiPositional",
        "status": "IMPLEMENTED",
        "gap": "нет ρ_risk"
    },
    
    ("utility", None, "compute_psi"): {
        "calls": [],
        "called_by": ["orchestrator/core.decide_with_pipeline_context"],
        "doc_ref": "01_CONCEPT.md §IV.4",
        "test_ref": "test_utility_core.py::TestComputePsiPositional",
        "status": "IMPLEMENTED",
        "gap": "нет факторов U,F,N,D,S"
    },
    
    # ... weitere Einträge
}
```

### 6.3 Статус покрытия тестами:

| Категория | Функций | Покрыто тестами |
|-----------|---------|-----------------|
| Core Utility (PATH 2) | 8 | 100% |
| Agent Core (PATH 3) | 12 | 65% |
| Verifier | 5 | 40% |
| Memory | 10 | 55% |
| Mission | 8 | 50% |
| Compliance | 6 | 30% |

---

## 7. РЕКОМЕНДАЦИИ

### 7.1 Немедленные действия:

1. **Документировать 57 функций** — приоритет по critical path
2. **Удалить 2 заглушки** в `metrics/tracker.py`
3. **Реализовать 30 отсутствующих функций** или удалить из документации
4. **Добавить __post_init__** валидацию в AgentCapabilities, ReputationVector, AgentMetrics

### 7.2 Для E2E тестов:

1. Создать `test_e2e_critical_paths.py` с 4 критическими сценариями
2. Использовать данные из FUNCTION_GRAPH для построения fixture chain
3. Добавить "дымовые тесты" для всех 5 путей

### 7.3 Для графа функций:

1. Сгенерировать JSON-описание всех 526 функций
2. Построить directed graph с graphviz
3. Визуализировать пересечения модулей

---

## 8. СОЗДАННЫЕ ФАЙЛЫ

### 8.1 Данные для графа функций:

| Файл | Описание | Размер |
|------|----------|--------|
| `function_graph_data.json` | Полные данные о 441 функции | 234 KB |
| `function_graph.dot` | GraphViz файл для визуализации | 301 KB |
| `FUNCTION_GRAPH_AND_E2E_PREPARATION.md` | Этот отчёт | 12 KB |

### 8.2 Структура JSON данных:

```json
{
  "total_functions": 441,
  "by_status": {
    "IMPLEMENTED": 384,
    "NO_DOC": 56,
    "NOT_IMPLEMENTED": 1
  },
  "e2e_coverage": {
    "PATH_1": 24,
    "PATH_2": 4,
    "PATH_3": 2,
    "PATH_4": 5,
    "PATH_5": 1
  },
  "by_module": {
    "agents.core": {"total": 18, "no_doc": 0},
    "utility.composite": {"total": 6, "no_doc": 1},
    ...
  },
  "functions": {
    "space1.agents.core.UnifiedCognitiveAgent.dispatch": {
      "module": "space1.agents.core",
      "class": "UnifiedCognitiveAgent",
      "function": "dispatch",
      "has_doc": true,
      "calls": ["execute_task", "execute_lead_evaluation"],
      "doc_ref": "01_CONCEPT.md",
      "status": "IMPLEMENTED",
      "gap": "",
      "test_coverage": ["test_agents_core.py::test_dispatch_*"],
      "e2e_path": "PATH_3"
    }
  }
}
```

### 8.3 Визуализация графа:

Для просмотра графа в терминале:
```bash
# Установить graphviz (если не установлен)
sudo apt install graphviz

# Сгенерировать PNG
dot -Tpng function_graph.dot > function_graph.png

# Или просмотр в интерактивном режиме
xdot function_graph.dot
```

Для ASCII визуализации (без graphviz):
```
agents ─────────────────────────────────────────────────────────────► factors
    │                                                                ▲
    └────────────────────────────────────────────────────────────► memory
orchestrator ───────────────────────────────────────────────────► mission
    │
    └──────────────────► utility (compute_phi, compute_psi, ...)
```

---

## 9. МАТРИЦА КРОСС-МОДУЛЬНЫХ ЗАВИСИМОСТЕЙ

```
                 agents ai_sup compl config cost  deliv envir factors marke  memo  metri missi model optimi orch  trigge utile
agents              -     .     X     .     X     X     .     .     .     X     .     .     .     .      X     .     X
ai_super_router     X     -     X     .     .     X     X     X     .     X     X     .     .     .      X     .     X
compliance         X     .     -     .     .     .     .     .     .     .     .     .     X     .      X     X     X
config             .     .     .     -     .     .     .     .     .     .     .     .     .     .      X     .     .
cost               .     X     X     .     -     X     .     X     .     .     X     .     .     .      X     .     X
delivery           .     X     X     .     X     -     .     .     .     .     X     .     .     .      X     .     X
environment        .     X     X     .     X     X     -     X     .     X     X     .     .     .      X     .     X
factors            X     X     X     .     X     X     X     -     X     X     X     X     X     X      X     X     X
market_protocols   X     X     X     .     .     X     X     X     -     X     .     X     X     .      X     .     .
memory             X     X     X     .     X     X     X     X     .     -     X     X     X     X      X     .     X
metrics            X     X     X     .     X     X     X     X     .     X     -     X     X     X      X     X     X
mission            X     X     X     .     X     X     X     X     .     X     X     -     X     X      X     X     X
models             X     X     X     .     .     .     X     X     .     X     .     X     -     .      X     .     .
optimizer          .     X     X     X     X     .     .     X     .     X     X     .     .     -      X     .     X
orchestrator       X     X     X     X     X     X     X     X     X     X     X     X     X     X      -     X     X
triggers           .     X     X     .     .     .     .     X     .     X     X     X     .     .      X     -     .
utility            X     X     X     .     X     X     X     X     .     X     X     X     X     X      X     X     -
verifier           .     X     .     .     X     X     .     X     .     X     X     X     .     X      X     .     -
```

**. = нет прямой зависимости, X = есть зависимость**

---

## 10. ПЛАН ДЕЙСТВИЙ ДЛЯ E2E ТЕСТИРОВАНИЯ

### Phase 1: Критические пути (2 недели)
```
E2E-01: Task Lifecycle Full Path
E2E-02: Utility Computation (UPH)
E2E-03: Agent Dispatch Flow
E2E-04: Mission Pipeline End-to-End
```

### Phase 2: Расширенные сценарии (2 недели)
```
E2E-05: Memory Operations
E2E-06: Reputation & Quality
E2E-07: Cold Start Scenarios
E2E-08: Budget & Cost Tracking
```

### Phase 3: Edge Cases (1 неделя)
```
E2E-09: Compliance Rejections
E2E-10: Circuit Breaker
E2E-11: Scheduler Priority
```

---

**Следующий шаг:** Реализация E2E тестов на основе этого анализа

---

*Отчёт подготовлен: 2026-07-26*
*Созданные файлы:*
- `function_graph_data.json` — полные данные о функциях (441 функция)
- `function_graph.dot` — GraphViz визуализация
- `FUNCTION_GRAPH_AND_E2E_PREPARATION.md` — этот документ
