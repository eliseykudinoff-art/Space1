# SYSTEM MONITORING — Мониторинг внутренней среды

## Полное руководство по мониторингу состояния агента

> **Проект:** Space1 — AI-Agent Freelancer Model
> **Дата:** 2026-07-08
> **Статус:** Документ для имплементации
> **Цель:** Формализация того, что система должна отслеживать постоянно

---

## СОДЕРЖАНИЕ

1. [Философия мониторинга](#1-философия-мониторинга)
2. [Режимы работы агента](#2-режимы-работы-агента)
3. [Фоновый мониторинг (Dormant/Idle)](#3-фоновый-мониторинг-dormantidle)
4. [Активный мониторинг (Active)](#4-активный-мониторинг-active)
5. [Гомеостатические метрики](#5-гомеостатические-метрики)
6. [Operational метрики](#6-operational-метрики)
7. [Метрики задач](#7-метрики-задач)
8. [Сводная таблица всех метрик](#8-сводная-таблица-всех-метрик)
9. [Код мониторинга](#9-код-мониторинга)

---

# 1. ФИЛОСОФИЯ МОНИТОРИНГА

## 1.1 Почему мониторинг критичен

Агент-фрилансер — это **автономная система**, которая:
- Работает **непрерывно** (между заказами)
- Принимает **стохастические решения**
- Должна **поддерживать себя** в рабочем состоянии
- Нуждается в **быстрой реакции** на проблемы

**Без мониторинга агент:**
- Не знает своего состояния
- Не может принять решение "что делать"
- Может потратить все ресурсы
- Может накопить критические проблемы

## 1.2 Архитектура мониторинга

```
┌─────────────────────────────────────────────────────────────────┐
│                     МОНИТОРИНГ АРХИТЕКТУРА                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    DATA COLLECTION                        │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │  │
│  │  │ Sensors │  │ Logs   │  │ Metrics │  │ Events  │    │  │
│  │  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘    │  │
│  └───────┼─────────────┼─────────────┼─────────────┼──────────┘  │
│          └──────────────┴─────┬──────┴─────────────┘           │
│                                ▼                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                 PROCESSING & AGGREGATION                  │  │
│  │  • Time-series aggregation                                 │  │
│  │  • Anomaly detection                                      │  │
│  │  • Threshold evaluation                                   │  │
│  └──────────────────────────────┬───────────────────────────┘  │
│                                 ▼                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    ALERTING & ACTIONS                     │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │  │
│  │  │   INFO     │  │   WARNING   │  │   CRITICAL  │    │  │
│  │  │  log only  │  │  adjust     │  │  intervene  │    │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 1.3 Типы метрик

| Тип | Описание | Пример | Частота |
|-----|---------|--------|---------|
| **Gauge** | Текущее значение | `memory_used_mb` | Каждый цикл |
| **Counter** | Cumulative count | `tasks_completed` | При событии |
| **Histogram** | Распределение | `task_duration_seconds` | При завершении |
| **Rate** | Изменение в единицу времени | `tasks_per_hour` | Каждые 5 минут |

## 1.4 Частота мониторинга

```
┌─────────────────────────────────────────────────────────────┐
│                 ЧАСТОТА МОНИТОРИНГА                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  IMMEDIATE (каждый цикл, ~1 сек):                          │
│  • Валидация health checks                                    │
│  • Очередь задач                                             │
│  • Budget consumption                                        │
│  • Текущая задача status                                     │
│                                                               │
│  MINUTE (каждую минуту):                                    │
│  • Profit rate                                                │
│  • Success rate (rolling window)                              │
│  • Resource utilization                                       │
│  • Reputation updates                                         │
│                                                               │
│  HOURLY (каждый час):                                       │
│  • Comprehensive health score                                  │
│  • Trend analysis                                             │
│  • Skill decay check                                          │
│  • Knowledge staleness                                        │
│                                                               │
│  DAILY (раз в день):                                        │
│  • Full system audit                                          │
│  • Strategy adjustment                                        │
│  • Model performance review                                   │
│  • Financial reconciliation                                   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

# 2. РЕЖИМЫ РАБОТЫ АГЕНТА

## 2.1 Диаграмма состояний

```
                    ┌─────────────────────────────────────────┐
                    │                                         │
                    │   ┌─────────────────────────────────┐   │
                    │   │                                 │   │
                    ▼   │         DORMANT (Idle)        │   │
                ┌───┐ │   │                                 │   │
                │   │ │   │  • Ожидание заказов            │   │
                │   │ │   │  • Фоновый мониторинг         │   │
    ┌───────────┤START├──▶│  • Поддержание готовности       │   │
    │           │   │ │   │  • Поиск новых заказов         │   │
    │           └───┘ │   │                                 │   │
    │               │   └──────────────┬──────────────────┘   │
    │               │                  │                      │
    │               │    Заказ          │ Нет заказов > X мин  │
    │               │    появился       │                      │
    │               │                  ▼                      │
    │               │   ┌─────────────────────────────────┐   │
    │               │   │                                 │   │
    │               │   │          ACTIVE                 │   │
    │               │   │                                 │   │
    │               │   │  • Выполнение задачи           │   │
    │               │   │  • Активный мониторинг         │   │
    │               │   │  • Budget tracking              │   │
    │               │   │                                 │   │
    │               │   └──────────────┬──────────────────┘   │
    │               │                  │                      │
    │               │     Задача       │ Задача завершена    │
    │               │     проблема     │                      │
    │               │                  ▼                      │
    │               │   ┌─────────────────────────────────┐   │
    │               │   │                                 │   │
    └───────────────│──▶│        RECOVERING              │   │
                    │   │                                 │   │
                    │   │  • Анализ проблемы             │   │
                    │   │  • Корректирующие действия     │   │
                    │   │  • Retry или graceful fail     │   │
                    │   │                                 │   │
                    │   └──────────────┬──────────────────┘   │
                    │                  │                      │
                    │                  │ Recovery complete     │
                    │                  ▼                      │
                    │   ┌─────────────────────────────────┐   │
                    │   │                                 │   │
                    │   │        SUSPENDED               │   │
                    │   │                                 │   │
                    │   │  • Критическая проблема        │   │
                    │   │  • Ожидание внешнего решения    │   │
                    │   │  • Нет автономных действий     │   │
                    │   │                                 │   │
                    │   └──────────────┬──────────────────┘   │
                    │                  │                      │
                    │                  │ Проблема решена      │
                    │                  │ или timeout          │
                    │                  ▼                      │
                    └─────────────────────────────────────────┘
```

## 2.2 Характеристики режимов

| Режим | Мониторинг | Действия | Ресурсы |
|-------|-------------|----------|---------|
| **DORMANT** | Фоновый | Поиск заказов | Минимальные |
| **ACTIVE** | Полный | Выполнение задач | Максимальные |
| **RECOVERING** | Фокусированный | Коррекция | Пониженные |
| **SUSPENDED** | Базовый | Нет автономных | Критические |

---

# 3. ФОНОВЫЙ МОНИТОРИНГ (Dormant/Idle)

> **Когда:** Агент не выполняет задачу, ожидает заказов

## 3.1 Health Check метрики

### M001: Agent Health Score

| Параметр | Значение |
|----------|----------|
| **Метрика** | `agent_health_score` |
| **Формула** | `H = w₁·H_1 + w₂·H_2 + w₃·H_3 + w₄·H_4` |
| **Компоненты** | Memory, Skills, Budget, Queue |
| **Единицы** | Score [0, 1] |
| **Частота** | Every 60 seconds |

```python
def compute_health_score(
    memory_health: float,
    skill_health: float,
    budget_health: float,
    queue_health: float
) -> float:
    """
    H = Σ wᵢ × Hᵢ
    """
    weights = {
        "memory": 0.25,
        "skills": 0.30,
        "budget": 0.25,
        "queue": 0.20
    }
    
    return (
        weights["memory"] * memory_health +
        weights["skills"] * skill_health +
        weights["budget"] * budget_health +
        weights["queue"] * queue_health
    )
```

### M002: Memory Health

| Параметр | Значение |
|----------|----------|
| **Метрика** | `memory_health` |
| **Формула** | `H_mem = 1 - (M_used / M_max) × Decay_factor` |
| **Единицы** | Score [0, 1] |
| **Alert threshold** | < 0.3 → WARNING |

### M003: Skill Health

| Параметр | Значение |
|----------|----------|
| **Метрика** | `skill_health` |
| **Формула** | `H_skill = min(1.0, L_s(t) / L_target × recency_factor)` |
| **Единицы** | Score [0, 1] |
| **Alert threshold** | < 0.4 → WARNING |

### M004: Budget Health

| Параметр | Значение |
|----------|----------|
| **Метрика** | `budget_health` |
| **Формула** | `H_budget = B_remaining / B_allocated` |
| **Единицы** | Ratio [0, 1] |
| **Alert threshold** | < 0.2 → CRITICAL |

### M005: Queue Health

| Параметр | Значение |
|----------|----------|
| **Метрика** | `queue_health` |
| **Формула** | `H_queue = 1 - min(1, Q_depth / Q_target)` |
| **Единицы** | Score [0, 1] |
| **Alert threshold** | > 0.8 (полная) → WARNING |

## 3.2 Resource метрики

### M006: API Budget Remaining

| Параметр | Значение |
|----------|----------|
| **Метрика** | `api_budget_remaining_usd` |
| **Формула** | `B_api(t) = B_api(t-1) - Σ Cost_api_calls` |
| **Единицы** | USD |
| **Alert threshold** | < $5.00 → WARNING, < $1.00 → CRITICAL |

### M007: Context Utilization

| Параметр | Значение |
|----------|----------|
| **Метрика** | `context_utilization_pct` |
| **Формула** | `U_ctx = Tokens_used / Context_window_max × 100` |
| **Единицы** | Percentage [0, 100] |
| **Alert threshold** | > 85% → WARNING, > 95% → CRITICAL |

### M008: Rate Limit Usage

| Параметр | Значение |
|----------|----------|
| **Метрика** | `rate_limit_usage_pct` |
| **Формула** | `U_rate = Calls_last_minute / Rate_limit_max × 100` |
| **Единицы** | Percentage [0, 100] |
| **Alert threshold** | > 80% → WARNING |

## 3.3 Capability метрики

### M009: Knowledge Staleness

| Параметр | Значение |
|----------|----------|
| **Метрика** | `knowledge_staleness` |
| **Формула** | `S_know = e^(-λ × t_since_last_update)` |
| **Единицы** | Score [0, 1] где 1 = свежий |
| **Alert threshold** | < 0.5 → Refresh recommended |

```python
def compute_knowledge_staleness(
    last_update_time: datetime,
    decay_rate: float = 0.01,
    current_time: datetime = None
) -> float:
    """
    S_know = e^{-λ × t}
    """
    if current_time is None:
        current_time = datetime.now()
    
    hours_elapsed = (current_time - last_update_time).total_seconds() / 3600
    
    return math.exp(-decay_rate * hours_elapsed)
```

### M010: Skill Decay

| Параметр | Значение |
|----------|----------|
| **Метрика** | `skill_decay_factor` |
| **Формула** | `D_skill = e^(-ρ × t)` |
| **Единицы** | Factor [0, 1] |
| **Alert threshold** | < 0.7 → Practice recommended |

### M011: Model Performance Drift

| Параметр | Значение |
|----------|----------|
| **Метрика** | `model_drift_score` |
| **Формула** | `D = |S_measured - S_expected| / S_expected` |
| **Единицы** | Relative error |
| **Alert threshold** | > 0.2 (20%) → Recalibration needed |

## 3.4 Market & Opportunity метрики

### M012: Order Flow Rate

| Параметр | Значение |
|----------|----------|
| **Метрика** | `order_flow_rate_per_hour` |
| **Формула** | `λ_observed = N_new_orders / time_period_hours` |
| **Единицы** | orders/hour |
| **Alert threshold** | < λ_target × 0.5 → Increase scouting |

### M013: Market Competitiveness Index

| Параметр | Значение |
|----------|----------|
| **Метрика** | `market_competitiveness` |
| **Формула** | `C_market = 1 - (R_agent / R_avg_competitors)` |
| **Единицы** | Score [0, 1] |
| **Range** | 0 = most competitive, 1 = top |

---

# 4. АКТИВНЫЙ МОНИТОРИНГ (Active)

> **Когда:** Агент выполняет задачу

## 4.1 Execution метрики

### M014: Task Progress

| Параметр | Значение |
|----------|----------|
| **Метрика** | `task_progress_pct` |
| **Формула** | `P = (T_elapsed / T_estimated) × 100` |
| **Единицы** | Percentage [0, 100+] |
| **Alert threshold** | > 100% → Overdue |

### M015: Budget Burn Rate

| Параметр | Значение |
|----------|----------|
| **Метрика** | `budget_burn_rate_usd_per_min` |
| **Формула** | `R_burn = ΔBudget_consumed / ΔTime_minutes` |
| **Единицы** | USD/minute |
| **Alert threshold** | > Estimated_rate × 1.5 → Reduce spending |

### M016: Subtask Success Rate (Rolling)

| Параметр | Значение |
|----------|----------|
| **Метрика** | `subtask_success_rolling_10` |
| **Формула** | `S_sub = N_successful_subtasks / N_total_subtasks_last_10` |
| **Единицы** | Ratio [0, 1] |
| **Alert threshold** | < 0.7 → Quality check |

### M017: Self-Correction Cycles

| Параметр | Значение |
|----------|----------|
| **Метрика** | `self_correction_cycles_current_task` |
| **Формула** | `C_sc = Count of retries in current task` |
| **Единицы** | Integer count |
| **Alert threshold** | > 3 → Pattern issue, > 5 → Abort task |

## 4.2 Quality метрики (Active)

### M018: Current Quality Score

| Параметр | Значение |
|----------|----------|
| **Метрика** | `current_quality_score` |
| **Формула** | `Q_current = α·Q_comp + β·Q_acc + γ·Q_full + δ·Q_time` |
| **Единицы** | Score [0, 1] |
| **Alert threshold** | < 0.7 → Improvement needed |

### M019: Quality Trend

| Параметр | Значение |
|----------|----------|
| **Метрика** | `quality_trend_5` |
| **Формула** | `T_q = Slope(Q_last_5_measurements)` |
| **Единицы** | Change per measurement |
| **Alert threshold** | Negative slope → Intervention |

## 4.3 Risk метрики (Active)

### M020: Current Risk Exposure

| Параметр | Значение |
|----------|----------|
| **Метрика** | `risk_exposure_usd` |
| **Формула** | `Ψ_current = P_fail × (C_direct + C_reputation)` |
| **Единицы** | USD expected loss |
| **Alert threshold** | > Task_price × 0.5 → Mitigation required |

### M021: Compliance Violation Count

| Параметр | Значение |
|----------|----------|
| **Метрика** | `compliance_violations_session` |
| **Формула** | `V = Count of Γ(action) = -∞ events` |
| **Единицы** | Integer count |
| **Alert threshold** | > 0 → Block task |

### M022: Deadlock Detection

| Параметр | Значение |
|----------|----------|
| **Метрика** | `consecutive_no_progress_count` |
| **Формула** | `D = Count of same state repeated` |
| **Единицы** | Integer count |
| **Alert threshold** | > 3 → Restart/Abort task |

---

# 5. ГОМЕОСТАТИЧЕСКИЕ МЕТРИКИ

> **Что это:** Критические переменные, которые должны оставаться в допустимых диапазонах

## 5.1 Core Homeostatic Variables

| ID | Метрика | Symbol | Target | Min | Max | Unit |
|----|---------|--------|--------|-----|-----|------|
| H1 | Profit Rate | Φ | > 0 | -∞ | +∞ | $/hour |
| H2 | Reputation | Υ | > 0.7 | 0 | 1 | score |
| H3 | Success Rate | S | > 0.8 | 0 | 1 | ratio |
| H4 | Quality | Q | > 0.7 | 0 | 1 | score |
| H5 | Risk Level | Ψ | < 0.3 | 0 | +∞ | score |
| H6 | Workload | W | 0.5-0.8 | 0 | 1 | ratio |
| H7 | API Budget | B_api | > 0 | 0 | ∞ | USD |
| H8 | Task Queue | Q_depth | 3-10 | 0 | ∞ | tasks |

## 5.2 Homeostasis Computation

### M023: Homeostatic Ratio

| Параметр | Значение |
|----------|----------|
| **Метрика** | `homeostatic_ratio` |
| **Формула** | `H = (F_reinforcing + ε) / (F_balancing + ε)` |
| **Единицы** | Ratio |
| **Range** | < 0.9 = SLOW, 0.9-1.1 = STABLE, > 1.1 = GROW |

```python
def compute_homeostatic_ratio(
    reinforcing_forces: dict,
    balancing_forces: dict
) -> HomeostasisResult:
    """
    H = F_rein / F_bal
    """
    eps = 1e-6
    
    F_rein = sum(reinforcing_forces.values())
    F_bal = sum(balancing_forces.values())
    
    H = (F_rein + eps) / (F_bal + eps)
    
    if H < 0.9:
        status = "SLOW"
    elif H > 1.1:
        status = "GROW"
    else:
        status = "STABLE"
    
    return HomeostasisResult(
        ratio=H,
        status=status,
        F_reinforcing=F_rein,
        F_balancing=F_bal
    )
```

### M024: Deviations from Target

| Параметр | Значение |
|----------|----------|
| **Метрика** | `deviation_score` |
| **Формула** | `D = Σ |hᵢ - h*ᵢ| / h*ᵢ for all Hᵢ` |
| **Единицы** | Aggregated deviation |
| **Alert threshold** | > 0.5 → Correction needed |

### M025: Time in Range

| Параметр | Значение |
|----------|----------|
| **Метрика** | `pct_time_in_range` |
| **Формула** | `T_range = (Time_with_all_vars_in_range / Total_time) × 100` |
| **Единицы** | Percentage |
| **Target** | > 95% |

## 5.3 Drive Metrics (Allostasis)

### M026: Total Drive Level

| Параметр | Значение |
|----------|----------|
| **Метрика** | `total_drive_level` |
| **Формула** | `D_total = Σ |hᵢ* - hᵢ|^p` |
| **Единицы** | Combined drive |
| **Alert threshold** | > 1.0 → Action priority |

### M027: Dominant Drive

| Параметр | Значение |
|----------|----------|
| **Метрика** | `dominant_drive` |
| **Формула** | `D_dom = argmax_i |hᵢ* - hᵢ|` |
| **Единицы** | Variable name |
| **Alert threshold** | Any drive > 0.5 → Address |

---

# 6. OPERATIONAL МЕТРИКИ

## 6.1 Throughput Metrics

### M028: Tasks Completed (Cumulative)

| Параметр | Значение |
|----------|----------|
| **Метрика** | `tasks_completed_total` |
| **Формула** | `N_comp = Σ I(task_completed)` |
| **Единицы** | Count |
| **Type** | Counter |

### M029: Tasks Per Hour (Rate)

| Параметр | Значение |
|----------|----------|
| **Метрика** | `throughput_tasks_per_hour` |
| **Формула** | `Q_actual = N_comp_last_hour / 1 hour` |
| **Единицы** | tasks/hour |
| **Target** | > Q_0 (baseline) |

### M030: Average Task Duration

| Параметр | Значение |
|----------|----------|
| **Метрика** | `avg_task_duration_minutes` |
| **Формула** | `T_avg = Mean(T_i for i in completed_tasks)` |
| **Единицы** | Minutes |
| **Alert threshold** | > T_target × 1.5 → Efficiency issue |

## 6.2 Financial Metrics

### M031: Total Revenue

| Параметр | Значение |
|----------|----------|
| **Метрика** | `revenue_total_usd` |
| **Формула** | `R_total = Σ P_task × S_task` |
| **Единицы** | USD |
| **Type** | Counter |

### M032: Total Costs

| Параметр | Значение |
|----------|----------|
| **Метрика** | `costs_total_usd` |
| **Формула** | `C_total = Σ (API_cost + Tool_cost + Overhead)` |
| **Единицы** | USD |
| **Type** | Counter |

### M033: Net Profit

| Параметр | Значение |
|----------|----------|
| **Метрика** | `net_profit_usd` |
| **Формула** | `Φ_net = R_total - C_total` |
| **Единицы** | USD |
| **Target** | > 0 |

### M034: Effective Hourly Rate

| Параметр | Значение |
|----------|----------|
| **Метрика** | `effective_hourly_rate_usd` |
| **Формула** | `R_hourly = Φ_net / T_total_hours` |
| **Единицы** | USD/hour |
| **Target** | > $25/hour |

## 6.3 Efficiency Metrics

### M035: API Cost Per Task

| Параметр | Значение |
|----------|----------|
| **Метрика** | `api_cost_per_task_usd` |
| **Формула** | `C_api_avg = C_api_total / N_comp` |
| **Единицы** | USD/task |
| **Alert threshold** | > $2.00/task → Optimize |

### M036: Token Efficiency

| Параметр | Значение |
|----------|----------|
| **Метрика** | `tokens_per_task` |
| **Формула** | `E_tokens = (In_tokens + Out_tokens) / N_comp` |
| **Единицы** | tokens/task |
| **Alert threshold** | > 2× baseline → Review prompts |

### M037: Cache Hit Rate

| Параметр | Значение |
|----------|----------|
| **Метрика** | `cache_hit_rate` |
| **Формула** | `H_cache = Cache_hits / (Cache_hits + Cache_misses)` |
| **Единицы** | Ratio [0, 1] |
| **Target** | > 0.3 |

---

# 7. МЕТРИКИ ЗАДАЧ

## 7.1 Task Metrics

### M038: Task Complexity Score

| Параметр | Значение |
|----------|----------|
| **Метрика** | `task_complexity` |
| **Формула** | `D = f(size, novelty, dependencies, tools_needed)` |
| **Единицы** | Score [0, 1] |
| **Alert threshold** | > H_max (ceiling) → Reject |

### M039: Estimated vs Actual Time

| Параметр | Значение |
|----------|----------|
| **Метрика** | `time_accuracy_ratio` |
| **Формула** | `A_time = T_actual / T_estimated` |
| **Единицы** | Ratio |
| **Alert threshold** | < 0.8 or > 1.5 → Recalibrate estimator |

### M040: Client Satisfaction (Post-Task)

| Параметр | Значение |
|----------|----------|
| **Метрика** | `client_satisfaction_score` |
| **Формула** | `S_client = Rating_given / 5.0` |
| **Единицы** | Score [0, 1] |
| **Target** | > 0.8 |

### M041: Rejection Rate

| Параметр | Значение |
|----------|----------|
| **Метрика** | `task_rejection_rate` |
| **Формула** | `R_rej = Tasks_rejected / Tasks_seen` |
| **Единицы** | Ratio [0, 1] |
| **Range** | < 0.5 = Good selector, > 0.8 = Too selective |

## 7.2 Quality Metrics

### M042: First Pass Quality

| Параметр | Значение |
|----------|----------|
| **Метрика** | `first_pass_quality` |
| **Формула** | `Q_fp = I(Q_final < threshold) / N_comp` |
| **Единицы** | Ratio [0, 1] |
| **Target** | > 0.8 (no revision needed) |

### M043: Revision Rate

| Параметр | Значение |
|----------|----------|
| **Метрика** | `revision_rate` |
| **Формула** | `R_rev = N_tasks_with_revisions / N_comp` |
| **Единицы** | Ratio [0, 1] |
| **Alert threshold** | > 0.3 → Quality issue |

### M044: Deadline Adherence

| Параметр | Значение |
|----------|----------|
| **Метрика** | `deadline_adherence_rate` |
| **Формула** | `A_deadline = Tasks_on_time / N_comp` |
| **Единицы** | Ratio [0, 1] |
| **Target** | > 0.9 |

## 7.3 Reputation Metrics

### M045: Current Reputation Score

| Параметр | Значение |
|----------|----------|
| **Метрика** | `reputation_score` |
| **Формула** | `Υ = f(R_avg, retention, reviews, response_time)` |
| **Единицы** | Score [0, 1] |
| **Alert threshold** | < 0.7 → Reputation recovery mode |

### M046: Review Count

| Параметр | Значение |
|----------|----------|
| **Метрика** | `reviews_count` |
| **Формула** | `N_reviews = Count of all reviews` |
| **Единицы** | Integer |
| **Alert threshold** | < 10 → Low credibility |

### M047: Response Time Average

| Параметр | Значение |
|----------|----------|
| **Метрика** | `avg_response_time_minutes` |
| **Формула** | `T_resp = Mean(time_to_first_response)` |
| **Единицы** | Minutes |
| **Target** | < 30 minutes |

---

# 8. СВОДНАЯ ТАБЛИЦА ВСЕХ МЕТРИК

## 8.1 Полный список метрик

| ID | Название | Режим | Частота | Единицы | Alert |
|----|---------|-------|---------|---------|-------|
| **HEALTH & CORE** |
| M001 | agent_health_score | All | 60s | [0,1] | < 0.5 |
| M002 | memory_health | Idle | 60s | [0,1] | < 0.3 |
| M003 | skill_health | Idle | 60s | [0,1] | < 0.4 |
| M004 | budget_health | All | 30s | [0,1] | < 0.2 |
| M005 | queue_health | Idle | 60s | [0,1] | > 0.8 |
| **RESOURCES** |
| M006 | api_budget_remaining | All | 30s | USD | < $5 |
| M007 | context_utilization | All | 60s | % | > 85% |
| M008 | rate_limit_usage | All | 60s | % | > 80% |
| **CAPABILITY** |
| M009 | knowledge_staleness | Idle | 5min | [0,1] | < 0.5 |
| M010 | skill_decay_factor | Idle | 1hr | [0,1] | < 0.7 |
| M011 | model_drift_score | All | 1hr | ratio | > 0.2 |
| **MARKET** |
| M012 | order_flow_rate | Idle | 5min | /hr | < target |
| M013 | market_competitiveness | Idle | 1hr | [0,1] | > 0.7 |
| **EXECUTION** |
| M014 | task_progress_pct | Active | 30s | % | > 100% |
| M015 | budget_burn_rate | Active | 30s | USD/min | > 1.5×est |
| M016 | subtask_success_rolling | Active | 60s | [0,1] | < 0.7 |
| M017 | self_correction_cycles | Active | per retry | count | > 5 |
| **QUALITY** |
| M018 | current_quality_score | Active | 60s | [0,1] | < 0.7 |
| M019 | quality_trend_5 | All | per task | slope | negative |
| M042 | first_pass_quality | All | per task | [0,1] | < 0.8 |
| M043 | revision_rate | All | daily | ratio | > 0.3 |
| **RISK** |
| M020 | risk_exposure_usd | Active | 60s | USD | > 50%price |
| M021 | compliance_violations | All | per event | count | > 0 |
| M022 | deadlock_count | Active | per cycle | count | > 3 |
| **HOMEOSTASIS** |
| M023 | homeostatic_ratio | All | 60s | ratio | < 0.9 |
| M024 | deviation_score | All | 60s | deviation | > 0.5 |
| M025 | pct_time_in_range | All | daily | % | < 95% |
| M026 | total_drive_level | All | 60s | drive | > 1.0 |
| M027 | dominant_drive | All | 60s | var_name | any > 0.5 |
| **THROUGHPUT** |
| M028 | tasks_completed | All | per task | count | — |
| M029 | throughput_per_hour | All | hourly | /hr | < baseline |
| M030 | avg_task_duration | All | daily | min | > 1.5×est |
| **FINANCIAL** |
| M031 | revenue_total | All | daily | USD | — |
| M032 | costs_total | All | daily | USD | — |
| M033 | net_profit | All | daily | USD | < 0 |
| M034 | effective_hourly_rate | All | daily | USD/hr | < $25 |
| M035 | api_cost_per_task | All | daily | USD | > $2 |
| M036 | token_efficiency | All | daily | tokens | > 2×base |
| M037 | cache_hit_rate | All | hourly | [0,1] | < 0.3 |
| **TASK** |
| M038 | task_complexity | Pre-task | once | [0,1] | > ceiling |
| M039 | time_accuracy_ratio | Post-task | once | ratio | < 0.8 |
| M040 | client_satisfaction | Post-task | once | [0,1] | < 0.8 |
| M041 | rejection_rate | All | daily | ratio | > 0.5 |
| **REPUTATION** |
| M045 | reputation_score | All | daily | [0,1] | < 0.7 |
| M046 | reviews_count | All | weekly | count | < 10 |
| M047 | avg_response_time | All | daily | min | > 30 |

## 8.2 Метрики по режимам

### Idle Mode (Dormant)

```
Мониторинг включает:
• M001-M005: Health checks
• M006-M008: Resource metrics
• M009-M011: Capability metrics
• M012-M013: Market metrics
• M023-M027: Homeostasis metrics

Частота: 1-5 минут
Priority: Low (фоновый)
```

### Active Mode

```
Мониторинг включает:
• M001, M004, M006-M008: Core health
• M014-M017: Execution metrics
• M018-M019, M042-M043: Quality
• M020-M022: Risk metrics
• M023-M027: Homeostasis

Частота: 30-60 секунд
Priority: HIGH
```

### Recovering Mode

```
Мониторинг включает:
• M017: Self-correction cycles
• M021-M022: Compliance/deadlock
• M020: Risk exposure
• M014-M015: Progress/budget

Частота: 10-30 секунд
Priority: CRITICAL
```

---

# 9. КОД МОНИТОРИНГА

## 9.1 Monitor Class

```python
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from enum import Enum
from datetime import datetime, timedelta
import threading
import time


class AgentMode(Enum):
    DORMANT = "dormant"
    ACTIVE = "active"
    RECOVERING = "recovering"
    SUSPENDED = "suspended"


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class MetricValue:
    name: str
    value: float
    timestamp: datetime
    unit: str
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class Alert:
    metric_name: str
    level: AlertLevel
    message: str
    value: float
    threshold: float
    timestamp: datetime


class SystemMonitor:
    def __init__(self):
        # Storage
        self.metrics: Dict[str, List[MetricValue]] = {}
        self.alerts: List[Alert] = []
        
        # Current state
        self.mode = AgentMode.DORMANT
        self.current_task_id: Optional[str] = None
        
        # Thresholds
        self.thresholds = self._init_thresholds()
        
        # Subscribers
        self.subscribers: List[Callable[[Alert], None]] = []
        
        # Monitoring loop
        self._running = False
        self._monitor_thread = None
    
    def _init_thresholds(self) -> Dict[str, Dict]:
        return {
            "agent_health_score": {"warning": 0.6, "critical": 0.4},
            "budget_health": {"warning": 0.3, "critical": 0.2},
            "api_budget_remaining": {"warning": 10.0, "critical": 5.0},
            "context_utilization": {"warning": 80.0, "critical": 90.0},
            "task_progress_pct": {"warning": 90.0, "critical": 100.0},
            "risk_exposure_usd": {"warning": 0.3, "critical": 0.5},  # ratio to price
            "self_correction_cycles": {"warning": 3, "critical": 5},
            "homeostatic_ratio": {"below_warning": 0.9, "above_warning": 1.1},
            # ... more thresholds
        }
    
    def record(self, name: str, value: float, unit: str = "", tags: Dict = None):
        """Record a metric value"""
        metric = MetricValue(
            name=name,
            value=value,
            timestamp=datetime.now(),
            unit=unit,
            tags=tags or {}
        )
        
        if name not in self.metrics:
            self.metrics[name] = []
        
        self.metrics[name].append(metric)
        
        # Check thresholds
        self._check_threshold(name, value)
    
    def _check_threshold(self, name: str, value: float):
        """Check if value exceeds thresholds"""
        if name not in self.thresholds:
            return
        
        thresh = self.thresholds[name]
        
        # Check for alerts
        if "critical" in thresh and value >= thresh["critical"]:
            self._emit_alert(name, AlertLevel.CRITICAL, value, thresh["critical"])
        elif "warning" in thresh and value >= thresh["warning"]:
            self._emit_alert(name, AlertLevel.WARNING, value, thresh["warning"])
    
    def _emit_alert(self, name: str, level: AlertLevel, value: float, threshold: float):
        """Emit an alert to subscribers"""
        alert = Alert(
            metric_name=name,
            level=level,
            message=f"{name}: {value} {'>' if value > threshold else '<'} {threshold}",
            value=value,
            threshold=threshold,
            timestamp=datetime.now()
        )
        
        self.alerts.append(alert)
        
        for subscriber in self.subscribers:
            subscriber(alert)
    
    def subscribe(self, callback: Callable[[Alert], None]):
        """Subscribe to alerts"""
        self.subscribers.append(callback)
    
    def get_metric(
        self,
        name: str,
        since: datetime = None,
        limit: int = None
    ) -> List[MetricValue]:
        """Get metric history"""
        if name not in self.metrics:
            return []
        
        values = self.metrics[name]
        
        if since:
            values = [v for v in values if v.timestamp >= since]
        
        if limit:
            values = values[-limit:]
        
        return values
    
    def get_latest(self, name: str) -> Optional[MetricValue]:
        """Get latest value for metric"""
        values = self.get_metric(name, limit=1)
        return values[0] if values else None
    
    def compute_rolling_average(
        self,
        name: str,
        window_minutes: int = 5
    ) -> Optional[float]:
        """Compute rolling average"""
        since = datetime.now() - timedelta(minutes=window_minutes)
        values = self.get_metric(name, since=since)
        
        if not values:
            return None
        
        return sum(v.value for v in values) / len(values)
    
    def get_all_alerts(
        self,
        since: datetime = None,
        level: AlertLevel = None
    ) -> List[Alert]:
        """Get alerts with optional filtering"""
        alerts = self.alerts
        
        if since:
            alerts = [a for a in alerts if a.timestamp >= since]
        
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        return alerts
    
    def start_monitoring(self, interval_seconds: int = 60):
        """Start background monitoring loop"""
        self._running = True
        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
    
    def _monitoring_loop(self, interval: int):
        """Background monitoring loop"""
        while self._running:
            try:
                self._run_health_checks()
                self._run_efficiency_checks()
                self._cleanup_old_metrics(days=7)
            except Exception as e:
                print(f"Monitoring error: {e}")
            
            time.sleep(interval)
    
    def _run_health_checks(self):
        """Run periodic health checks"""
        # This would be implemented based on actual system state
        pass
    
    def _run_efficiency_checks(self):
        """Run efficiency validations"""
        pass
    
    def _cleanup_old_metrics(self, days: int = 7):
        """Remove metrics older than N days"""
        cutoff = datetime.now() - timedelta(days=days)
        
        for name in self.metrics:
            self.metrics[name] = [
                v for v in self.metrics[name]
                if v.timestamp >= cutoff
            ]
```

## 9.2 Dashboard Data

```python
@dataclass
class DashboardSnapshot:
    """Snapshot for dashboard display"""
    timestamp: datetime
    mode: AgentMode
    
    # Health
    health_score: float
    memory_health: float
    skill_health: float
    budget_health: float
    
    # Current task
    current_task_id: Optional[str]
    task_progress: Optional[float]
    quality_score: Optional[float]
    
    # Financial
    net_profit_today: float
    effective_hourly_rate: float
    
    # Homeostasis
    homeostatic_ratio: float
    dominant_drive: Optional[str]
    
    # Recent alerts
    recent_alerts: List[Alert]
    
    # Trends
    tasks_completed_today: int
    success_rate_today: float


def get_dashboard_snapshot(monitor: SystemMonitor) -> DashboardSnapshot:
    """Generate dashboard snapshot"""
    
    return DashboardSnapshot(
        timestamp=datetime.now(),
        mode=monitor.mode,
        
        health_score=monitor.get_latest("agent_health_score").value,
        memory_health=monitor.get_latest("memory_health").value,
        skill_health=monitor.get_latest("skill_health").value,
        budget_health=monitor.get_latest("budget_health").value,
        
        current_task_id=monitor.current_task_id,
        task_progress=monitor.get_latest("task_progress_pct").value if monitor.current_task_id else None,
        quality_score=monitor.get_latest("current_quality_score").value if monitor.current_task_id else None,
        
        net_profit_today=monitor.get_latest("net_profit_today").value,
        effective_hourly_rate=monitor.get_latest("effective_hourly_rate_usd").value,
        
        homeostatic_ratio=monitor.get_latest("homeostatic_ratio").value,
        dominant_drive=monitor.get_latest("dominant_drive").value,
        
        recent_alerts=monitor.get_all_alerts(
            since=datetime.now() - timedelta(hours=1)
        ),
        
        tasks_completed_today=monitor.get_latest("tasks_completed_today").value,
        success_rate_today=monitor.get_latest("success_rate_today").value,
    )
```

## 9.3 Integration Example

```python
class FreelancerAgent:
    def __init__(self):
        self.monitor = SystemMonitor()
        self.monitor.subscribe(self._handle_alert)
    
    def _handle_alert(self, alert: Alert):
        """React to alerts"""
        if alert.level == AlertLevel.CRITICAL:
            if alert.metric_name == "budget_health":
                self._enter_suspended_mode("Budget critical")
            elif alert.metric_name == "compliance_violations":
                self._abort_current_task("Compliance violation")
        
        elif alert.level == AlertLevel.WARNING:
            if alert.metric_name == "task_progress_pct":
                self._notify_progress_delay()
    
    def execute_task(self, task: Task):
        """Execute task with monitoring"""
        self.monitor.mode = AgentMode.ACTIVE
        self.monitor.current_task_id = task.id
        
        try:
            # Execute with monitoring
            for step in task.steps:
                self._monitor_step(step)
                
                if self._should_abort():
                    raise TaskAbortError()
            
            self._complete_task(task)
            
        except Exception as e:
            self.monitor.mode = AgentMode.RECOVERING
            self._handle_failure(e)
        finally:
            self.monitor.current_task_id = None
    
    def _monitor_step(self, step):
        """Monitor individual step"""
        # Record progress
        self.monitor.record("task_progress_pct", step.progress)
        
        # Record quality
        if step.quality_score:
            self.monitor.record("current_quality_score", step.quality_score)
        
        # Record budget
        self.monitor.record("budget_health", self.budget_remaining)
    
    def wait_for_orders(self):
        """Idle mode - waiting for work"""
        self.monitor.mode = AgentMode.DORMANT
        
        while True:
            # Background monitoring
            self.monitor.record("memory_health", self.check_memory())
            self.monitor.record("skill_health", self.check_skills())
            self.monitor.record("queue_health", self.queue_depth / self.queue_target)
            
            # Check for new orders
            if order := self.poll_for_orders():
                return order
            
            time.sleep(60)  # Poll interval
```

---

# ПРИЛОЖЕНИЕ: МЕТРИКИ ПО ФОРМУЛАМ

## Метрики из MATHEMATICAL_FORMULAS

| Формула | Метрика | ID |
|---------|---------|-----|
| Φ = (R-C)/T | net_profit_usd | M033 |
| R = P×S×Q | revenue_total | M031 |
| Q = αQ_comp+... | current_quality_score | M018 |
| Ψ = P_fail×(C_direct+C_rep) | risk_exposure_usd | M020 |
| Υ = γ₁R̄+... | reputation_score | M045 |
| H = F_rein/F_bal | homeostatic_ratio | M023 |
| D(H) = Σ|h* - h|^p | total_drive_level | M026 |
| VoI = E[Φ] - E[Φ] | value_of_information_delta | — |
| U = Σλᵢ×compᵢ | utility_score | — |

---

*Документ создан: 2026-07-08*
*Версия: 1.0*
*Статус: Готов для имплементации*
