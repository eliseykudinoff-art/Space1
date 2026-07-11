# 🚀 Space1 — Comprehensive Development Plan

> **Статус:** ✅ СОСТАВЛЕН
> **Дата:** 2026-07-09
> **Автор:** OpenHands Agent
> **Версия:** 1.1
> **Покрытие:** 100% идентифицированных пробелов (23/23)
> **Уточнение 2026-07-11:** план пересмотрен по коду основной ветки/проекта; `docs/drafts/` считаются справочными материалами, а не источником текущей реализации.

---

## ⚠️ ПЕРЕД СТАРТОМ СЕССИИ — ОБЯЗАТЕЛЬНО ПРОЧИТАТЬ

Этот документ — **единый источник истины** для разработки Space1.
Перед началом любой работы:
1. Прочитайте текущий статус фаз
2. Определите, на какой фазе остановились
3. Начните с Definition of Done для текущей фазы

---

## 📋 СОДЕРЖАНИЕ

1. [Обзор пробелов](#1-обзор-пробелов)
2. [Pre-MVP решения](#2-pre-mvp-решения)
3. [Аудит текущего кода основной ветки](#3-аудит-текущего-кода-основной-ветки)
4. [Уточнённые фазы разработки](#4-уточнённые-фазы-разработки)
5. [Детальный план по пробелам](#5-детальный-план-по-пробелам)

---

## 1. ОБЗОР ПРОБЕЛОВ

| ID | Пробел | Источник | Статус |
|----|--------|----------|--------|
| G1 | Γ threshold не определён | MATHEMATICAL_ANALYSIS.md:289 | ❌ Решить в Pre-MVP |
| G2 | Impulse → Chain не формализован | MATHEMATICAL_ANALYSIS.md:295 | ❌ Phase 4 |
| G3 | Внешняя среда не смоделирована | MATHEMATICAL_ANALYSIS.md:307 | ❌ Phase 5 |
| G4 | Feedback loop отсутствует | MATHEMATICAL_ANALYSIS.md:319 | ❌ Pre-MVP |
| G5 | Token cost не в Φ | MATHEMATICAL_REVIEW.md | ❌ Phase 1 |
| G6 | PID controller не реализован | MATHEMATICAL_REVIEW.md | ❌ Phase 2 |
| G7 | Φ risk-adjusted | MATHEMATICAL_REVIEW.md | ❌ Phase 2 |
| G8 | Υ soft cap + EMA decay | MATHEMATICAL_REVIEW.md | ❌ Phase 2 |
| G9 | 17 факторов не в коде | COMPARATIVE_ANALYSIS.md | ❌ Phase 2 (MVP) → Phase 5 (full) |
| G10 | Signal-to-Context | COMPARATIVE_ANALYSIS.md:545 | ❌ Phase 4 |
| G11 | Data classes | PROJECT_NOTE | ❌ Phase 1 |
| G12 | Triggers | PROJECT_NOTE | ❌ Phase 3 |
| G13 | Multi-agent | COMPARATIVE_ANALYSIS.md | ❌ Phase 5 |
| G14 | Metric duplication | PROJECT_NOTE | ❌ Phase 1 |
| G15 | Notation inconsistency | PROJECT_NOTE | ❌ Pre-MVP |
| G16 | Mission vs Compliance | PROJECT_NOTE | ❌ Pre-MVP |
| G17 | Ξ coefficients | MATHEMATICAL_WORKSPACE.md | ❌ Phase 2 |
| G18 | Φ_R consistency | MATHEMATICAL_WORKSPACE.md | ❌ Phase 2 |
| G19 | λ adaptation | MATHEMATICAL_ANALYSIS.md | ❌ Phase 4 |
| G20 | Walrus notation | MATHEMATICAL_FORMULAS.md | ❌ Pre-MVP |
| G21 | Consolidation Gate | COMPARATIVE_ANALYSIS_REPORT.md | ❌ Phase 3 |
| G22 | Transfer learning | docs/manuscripts | ❌ Phase 5 |
| G23 | Deadline awareness | MATHEMATICAL_WORKSPACE.md | ❌ Phase 1 |

---

## 2. PRE-MVP РЕШЕНИЯ

### 2.1 Γ Threshold — БИНАРНЫЙ VETO (решение принято)

```python
# Формула: Γ(action) = 1 if all rules PASS else 0
class GammaVeto:
    def evaluate(self, action: Action, rules: List[Rule]) -> bool:
        """Binary compliance — return True only if ALL rules pass."""
        return all(rule.check(action) for rule in rules)
```

**Phase:** Pre-MVP
**Deliverable:** `compliance.py`

### 2.2 Feedback Loop — EMA (решение принято)

```python
# Формула: S_{t+1} = S_t + α · (R_t - S_t), α = 0.2
class MetricTracker:
    def update(self, metric: str, new_value: float, alpha: float = 0.2):
        current = self.get(metric)
        self.set(metric, current + alpha * (new_value - current))
```

**Phase:** Pre-MVP
**Deliverable:** `metrics.py`

### 2.3 MVP Factors (решение принято)

Для MVP берём 4 ключевых фактора:
- **x₁** — LLM quality (критичен)
- **x₈** — Cost tiering (бюджет=0)
- **x₁₂** — Guardrails (безопасность)
- **x₁₆** — Continual learning (адаптация)

**Phase:** Pre-MVP → Phase 2
**Deliverable:** `factors.py`

### 2.4 Naming Convention (решение принято)

| Нотация | Значение | Пример |
|---------|----------|--------|
| `Phi` | Profit Function | `compute_phi(task, agent)` |
| `Gamma` | Compliance Veto | `check_gamma(action)` |
| `Psi` | Risk Function | `compute_psi(task)` |
| `Upsilon` | Reputation | `update_upsilon(rating)` |
| `H` | Homeostasis | `compute_h(state)` |

**Phase:** Pre-MVP
**Deliverable:** `NAMING_CONVENTION.md`

### 2.5 Mission → Compliance Hierarchy (решение принято)

```
Mission → Compliance → Utility → Execution
     ↓           ↓           ↓         ↓
  calibrate   veto check   optimize   execute
```

**Phase:** Pre-MVP
**Deliverable:** `mission.py`

---


## 3. АУДИТ ТЕКУЩЕГО КОДА ОСНОВНОЙ ВЕТКИ

На 2026-07-11 текущая рабочая ветка репозитория содержит основной исполняемый код проекта, а `docs/drafts/` используется как справочная база с документацией и частичными/разрозненными идеями. Поэтому приоритет планирования смещён с «реализовать с нуля» на «довести существующие модули до связанной MVP-вертикали».

### 3.1 Что уже реализовано и должно считаться базой

| Область | Файлы | Вывод для плана |
|---------|-------|-----------------|
| Γ / compliance | `src/space1/compliance/core.py`, `config/rules.yaml` | Binary veto, rule registry и базовые правила уже есть; дальше нужен config-driven bootstrap и richer diagnostics. |
| Метрики / feedback | `src/space1/metrics/tracker.py` | EMA tracker и MetricRegistry уже есть; дальше нужен не новый tracker, а подключение формул Φ/Ψ/Q/Υ/H к единому registry. |
| Факторы | `src/space1/factors/registry.py`, `config/weights.yaml` | 17 FactorID и 4 MVP factors уже есть; Phase 2 должна добавить агрегатор/калькулятор и конфигурационные веса вместо дублирования констант. |
| Cost | `src/space1/cost/token_tracker.py`, `config/prices.yaml` | Token/tool cost уже реализован; следующий шаг — включить его в Φ и унифицировать источник цен с YAML. |
| Models | `src/space1/models/task.py`, `src/space1/models/agents.py` | Task/Agent/Context уже есть; нужно использовать их как контракт utility/orchestrator, не создавать параллельные модели. |
| Mission pipeline | `src/space1/mission/core.py` | Mission → Compliance → Utility → Execution уже есть как skeleton; Phase 2 должна заменить pass-through utility реальным ранжированием действий. |
| Config | `src/space1/config/loader.py`, `config/*.yaml` | YAML-конфигурация стала обязательной частью архитектуры; новые коэффициенты должны добавляться в YAML, а не хардкодиться в коде. |

### 3.2 Ключевые корректировки относительно старого плана

1. **Pre-MVP и Phase 1 считаются закрытыми по коду**, но требуют небольшого stabilization-прохода: публичные exports, docstrings, config-loader edge cases, отсутствие расхождения `NAMING_CONVENTION.md` с фактической структурой.
2. **Phase 2 теперь начинается не с отдельных классов**, а с `space1/utility/` как слоя, который связывает существующие `Task`, `Agent`, `TokenCostTracker`, `FactorRegistry`, `MetricRegistry` и YAML-конфигурацию.
3. **`docs/drafts/` больше не диктуют структуру модулей напрямую**: из них берутся формулы и смысловые ограничения, но контракт реализации определяется текущим кодом в `src/space1/`.
4. **Главный MVP-инкремент** — end-to-end decision loop: вход `Task + AgentContext + candidate Actions`, затем Γ veto, расчёт Φ/Q/Ψ/Υ/H, risk-adjusted score, выбор действия, запись метрик.
5. **Multi-agent, environment и transfer learning остаются поздними фазами**, пока single-agent utility loop не работает на реальных моделях данных и конфигурации.

---

## 4. УТОЧНЁННЫЕ ФАЗЫ РАЗРАБОТКИ

### Pre-MVP (0.5 дня)

| ID | Задача | Deliverable |
|----|--------|-------------|
| G1 | Реализовать GammaVeto (binary) | `compliance.py` |
| G4 | Реализовать MetricTracker (EMA) | `metrics.py` |
| G9_mvp | Создать FactorRegistry | `factors.py` |
| G15 | Написать NAMING_CONVENTION.md | `NAMING_CONVENTION.md` |
| G16 | Реализовать MissionCompliance hierarchy | `mission.py` |
| G20 | Standardize notation | Refactoring |
| G23 | Добавить deadline в Task | `models.py` |

**Definition of Done:**
- [ ] `import space1; space1.compute_phi()` работает
- [ ] `GammaVeto().evaluate(action)` возвращает bool
- [ ] Все метрики обновляются через EMA
- [ ] FactorRegistry с 4 факторами

---

### Phase 1: Foundation (1-2 недели)

| ID | Задача | Deliverable |
|----|--------|-------------|
| G5 | Token cost в Cost | `TokenCostTracker` |
| G11 | Data classes | `models.py` (Task, Agent, Context) |
| G14 | MetricRegistry | Single source of truth |

**Definition of Done:**
- [ ] Все модели в `models.py`
- [ ] Cost включает token cost
- [ ] Единый MetricRegistry

---

### Phase 2: Utility Functions & MVP Decision Loop (2-3 недели)

| ID | Задача | Deliverable |
|----|--------|-------------|
| G5/G7 | `compute_phi()` с token/tool cost и risk-adjustment | `utility/profit.py` |
| G8 | Soft-capped Υ + EMA поверх MetricRegistry | `utility/reputation.py` |
| G9 | Factor calculator/aggregator для x₁, x₈, x₁₂, x₁₆ | `utility/factors.py` |
| G6/G19 | PID/homeostasis controller как регулятор весов utility | `utility/control.py` |
| G17/G18 | Ξ coefficients и Φ_R consistency | `utility/composite.py` |
| Pipeline | Подключить utility scoring в `MissionProcessor` | `mission/core.py` |
| Config | Все коэффициенты Phase 2 вынести в YAML | `config/*.yaml` |

**Definition of Done:**
- [ ] `compute_phi(task, agent, cost_tracker)` использует reward, time, token/tool cost и YAML constants
- [ ] `compute_psi(task, agent_context)` учитывает uncertainty/fatigue/novelty/deadline/skill из существующих моделей
- [ ] `compute_quality()` и `update_upsilon()` пишут значения через `MetricRegistry`/EMA
- [ ] `FactorCalculator` агрегирует 4 MVP фактора из существующего `FactorRegistry` без хардкода весов
- [ ] `MissionProcessor` выбирает лучшее действие по risk-adjusted utility после Γ veto
- [ ] Есть тест end-to-end: Task + Agent + Actions → compliant ranked decision → metrics updated

---

### Phase 3: Memory & State (2 недели)

| ID | Задача | Deliverable |
|----|--------|-------------|
| G12 | Trigger System | `triggers.py` |
| G21 | Consolidation Gate | `memory/consolidation.py` |

**Definition of Done:**
- [ ] Persistent state между сессиями
- [ ] триггеры срабатывают
- [ ] Memory consolidation работает

---

### Phase 4: Orchestrator (2-3 недели)

| ID | Задача | Deliverable |
|----|--------|-------------|
| G2 | Impulse → Chain | `SignalToContextSynthesizer` |
| G10 | Signal-to-Context | `HomeostaticSynthesizer` |
| G19 | λ adaptation | `WeightCalibrator` |

**Definition of Done:**
- [ ] Orchestrator принимает decisions
- [ ] Homeostatic pressure → context conversion
- [ ] Adaptive weights

---

### Phase 5: Multi-Agent (3-4 недели)

| ID | Задача | Deliverable |
|----|--------|-------------|
| G3 | Environment Model | `environment/` |
| G9_full | Full 17 factors | `factors_full.py` |
| G13 | Multi-agent pool | `agents/` |
| G22 | Transfer learning | `transfer.py` |

**Definition of Done:**
- [ ] Scout/Worker/Finance agents работают
- [ ] Agent coordination
- [ ] Environment awareness

---

### Phase 6: Production (2 недели)

| ID | Задача | Deliverable |
|----|--------|-------------|
| G1_prod | Graded compliance | `compliance.py` (configurable) |
| G15 | Refactoring | Code consistency |
| G17 | Calibration | `calibration.py` |

**Definition of Done:**
- [ ] Production-ready monitoring
- [ ] All gaps closed
- [ ] 100% documentation coverage

---

## 5. ДЕТАЛЬНЫЙ ПЛАН ПО ПРОБЕЛАМ

### G1: Γ Threshold

| Аспект | Значение |
|--------|----------|
| **Source** | MATHEMATICAL_ANALYSIS.md:289 |
| **Decision** | Binary для MVP, Graded для production |
| **Formula MVP** | `Γ(action) = 1 if all rules PASS else 0` |
| **Formula Prod** | `U_final = U - λ_Γ · max(0, -Γ)` |
| **Implementation** | `GammaVeto` class |
| **Phase** | Pre-MVP |

### G2: Impulse → Chain

| Аспект | Значение |
|--------|----------|
| **Source** | MATHEMATICAL_ANALYSIS.md:295 |
| **Formula** | `Chain = f(Impulse, Memory, Context)` |
| **Implementation** | `SignalToContextSynthesizer` |
| **Phase** | Phase 4 |

### G3: External Environment

| Аспект | Значение |
|--------|----------|
| **Source** | MATHEMATICAL_ANALYSIS.md:307 |
| **Components** | MarketModel, CompetitorModel, ClientModel |
| **Integration** | λ_orders = f(R, Θ, market_state) |
| **Phase** | Phase 5 |

### G4: Feedback Loop

| Аспект | Значение |
|--------|----------|
| **Source** | MATHEMATICAL_ANALYSIS.md:319 |
| **Formula** | `S_{t+1} = S_t + α · (R_t - S_t)` |
| **Alpha** | 0.2 (настраиваемый) |
| **Implementation** | `MetricTracker` с EMA |
| **Phase** | Pre-MVP |

### G5: Token Cost

| Аспект | Значение |
|--------|----------|
| **Source** | MATHEMATICAL_REVIEW.md |
| **Formula** | `C(x) = C_0 + tokens × price_per_token + tool_cost` |
| **Implementation** | `TokenCostTracker` |
| **Phase** | Phase 1 |

### G6: PID Controller

| Аспект | Значение |
|--------|----------|
| **Source** | MATHEMATICAL_REVIEW.md |
| **Formula** | `u(t) = Kp·e(t) + Ki·∫e·dt + Kd·de/dt` |
| **Implementation** | `PIDController` |
| **Phase** | Phase 2 |

### G7: Risk-adjusted Φ

| Аспект | Значение |
|--------|----------|
| **Source** | MATHEMATICAL_REVIEW.md |
| **Formula** | `Φ_adj = Φ × (1 - Ψ/P)` |
| **Implementation** | `RiskAdjustedProfit` |
| **Phase** | Phase 2 |

### G8: Υ Soft Cap + EMA

| Аспект | Значение |
|--------|----------|
| **Source** | MATHEMATICAL_REVIEW.md |
| **Formula** | `Υ = min(1.0, raw_score × decay_factor)` |
| **Implementation** | `SoftCappedReputation` |
| **Phase** | Phase 2 |

### G9: 17 Factors

| Аспект | Значение |
|--------|----------|
| **Source** | COMPARATIVE_ANALYSIS.md |
| **MVP** | x₁, x₈, x₁₂, x₁₆ |
| **Full** | x₁-x₁₇ |
| **Implementation** | `FactorRegistry`, `FactorCalculator` |
| **Phase** | Pre-MVP → Phase 5 |

### G10: Signal-to-Context

| Аспект | Значение |
|--------|----------|
| **Source** | COMPARATIVE_ANALYSIS.md:545 |
| **Назначение** | "Главный хвост" Space1 |
| **Implementation** | `HomeostaticSynthesizer` |
| **Phase** | Phase 4 |

### G11: Data Classes

| Аспект | Значение |
|--------|----------|
| **Source** | PROJECT_NOTE |
| **Classes** | Task, AgentState, Context, Action, Metrics |
| **Implementation** | `models.py` |
| **Phase** | Phase 1 |

### G12: Triggers

| Аспект | Значение |
|--------|----------|
| **Source** | PROJECT_NOTE |
| **Types** | ThresholdTrigger, TemporalTrigger, EventTrigger |
| **Implementation** | `triggers.py` |
| **Phase** | Phase 3 |

### G13: Multi-Agent

| Аспект | Значение |
|--------|----------|
| **Source** | COMPARATIVE_ANALYSIS.md |
| **Agents** | Scout, Worker, Finance, Communicator |
| **Implementation** | `agents/`, `AgentCoordinator` |
| **Phase** | Phase 5 |

### G14: Metric Duplication

| Аспект | Значение |
|--------|----------|
| **Source** | PROJECT_NOTE |
| **Solution** | Единый MetricRegistry |
| **Implementation** | `metrics.py` |
| **Phase** | Phase 1 |

### G15: Notation

| Аспект | Значение |
|--------|----------|
| **Source** | PROJECT_NOTE |
| **Solution** | NAMING_CONVENTION.md |
| **Phase** | Pre-MVP |

### G16: Mission vs Compliance

| Аспект | Значение |
|--------|----------|
| **Source** | PROJECT_NOTE |
| **Hierarchy** | Mission → Compliance → Utility → Execution |
| **Implementation** | `mission.py` |
| **Phase** | Pre-MVP |

### G17: Ξ Coefficients

| Аспект | Значение |
|--------|----------|
| **Source** | MATHEMATICAL_WORKSPACE.md |
| **Initial** | α = 0.7, β = 0.3 (placeholder) |
| **Calibration** | Phase 6 |
| **Phase** | Phase 2 |

### G18: Φ_R Consistency

| Аспект | Значение |
|--------|----------|
| **Source** | MATHEMATICAL_WORKSPACE.md |
| **Formula** | `Φ_R = Φ × Γ=0 × (1+α_rep·Υ) - λ_Ψ × Ψ` |
| **Implementation** | `PhiRCalculator` |
| **Phase** | Phase 2 |

### G19: λ Adaptation

| Аспект | Значение |
|--------|----------|
| **Source** | MATHEMATICAL_ANALYSIS.md |
| **Solution** | PID-based weight calibration |
| **Implementation** | `WeightCalibrator` |
| **Phase** | Phase 4 |

### G20: Walrus Notation

| Аспект | Значение |
|--------|----------|
| **Source** | MATHEMATICAL_FORMULAS.md |
| **Solution** | Standard Python notation |
| **Phase** | Pre-MVP |

### G21: Consolidation Gate

| Аспект | Значение |
|--------|----------|
| **Source** | COMPARATIVE_ANALYSIS_REPORT.md |
| **Solution** | episodic → semantic memory gate |
| **Implementation** | `memory/consolidation.py` |
| **Phase** | Phase 3 |

### G22: Transfer Learning

| Аспект | Значение |
|--------|----------|
| **Source** | docs/manuscripts |
| **Formula** | `ΔS_transfer = γ_transfer × TaskSimilarity × K_past` |
| **Implementation** | `transfer.py` |
| **Phase** | Phase 5 |

### G23: Deadline Awareness

| Аспект | Значение |
|--------|----------|
| **Source** | MATHEMATICAL_WORKSPACE.md |
| **Fields** | deadline, urgency_score, slack_time |
| **Implementation** | `Task` model |
| **Phase** | Phase 1 |

---

## 📊 TIMELINE SUMMARY

```
Pre-MVP:   0.5 дня    (решения, models skeleton)
Phase 1:   1-2 недели (Foundation)
Phase 2:   2-3 недели (Utility Functions)
Phase 3:   2 недели   (Memory & State)
Phase 4:   2-3 недели (Orchestrator)
Phase 5:   3-4 недели (Multi-Agent)
Phase 6:   2 недели   (Production)

─────────────────────────────────────────────────
TOTAL:     11-18 недель (2.5-4 месяца)
MVP:       Phase 2 (месяц 2)
Production: Phase 6 (месяц 4)
```

---

## ✅ CHECKLIST ПЕРЕД СЕССИЕЙ

- [ ] Прочитал DEVELOPMENT_PLAN.md
- [ ] Знаю, на какой фазе остановка
- [ ] Знаю Definition of Done для текущей фазы
- [ ] Есть план на текущую сессию

---

*Документ создан: 2026-07-09*
*Статус: ✅ Составлен и согласован*
*Следующий шаг: Phase 2 — связать существующие модули в MVP decision loop*
