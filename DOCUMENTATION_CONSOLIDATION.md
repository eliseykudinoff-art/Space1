# 📚 Предложение по консолидации документации

> **Дата:** 2026-07-06  
> **Статус:** 📋 ПРЕДЛОЖЕНИЕ для команды  
> **Цель:** Минимум файлов, максимум содержания

---

## 📊 Текущее состояние (12 файлов)

| Файл | Строк | Назначение |
|------|-------|------------|
| `PROJECT_NOTE.md` | 6937 | Заметки, журнал, идеи |
| `UNIFIED_VARIABLE_SYSTEM.md` | 1227 | Таксономия переменных |
| `UNIFIED_MODEL.md` | 536 | 17 факторов + синергии |
| `AGENT_CONTROL_ARCHITECTURE.md` | 827 | 7 управляющих функций |
| `atomic_decomposition_model.md` | 672 | Математика декомпозиции |
| `task_decomposition_model.md` | 373 | Дополнительно о декомпозиции |
| `complexity_classification_formula.md` | 228 | Классификация сложности |
| `MISSING_FACTORS_ANALYSIS.md` | 317 | Анализ пропущенных факторов |
| `MANUS_INTEGRATION_REPORT.md` | 221 | Отчёт об интеграции Manus |
| `IMPLEMENTATION_SUMMARY.md` | 143 | Резюме реализации |
| **docs/manuscripts/ (4 файла)** | ~1804 | Manus документы |
| **DOCUMENTATION_ISSUES.md** | NEW | Нестыковки |

**Итого:** ~14 файлов, ~12,985 строк

---

## 🎯 Целевая структура (6 файлов)

### Чистовики (Финальные версии)

| # | Файл | Строк | Содержание |
|---|------|-------|------------|
| 1 | `README.md` | ~200 | Обзор проекта, навигация |
| 2 | `MODEL_CORE.md` | ~1500 | Φ, Υ, Ω, Γ, Q, Ψ — ЯДРО модели |
| 3 | `MODEL_VARIABLES.md` | ~800 | Таксономия переменных, нотация |
| 4 | `ARCHITECTURE.md` | ~800 | Архитектура системы |
| 5 | `FORMULAS_REFERENCE.md` | ~600 | Все формулы, единый источник |
| 6 | `PROJECT_NOTE.md` | ~1000 | Рабочие заметки, TODO |

### Удалить/Архивировать

| Файл | Действие |
|------|----------|
| `UNIFIED_MODEL.md` | ❌ → `MODEL_CORE.md` |
| `UNIFIED_VARIABLE_SYSTEM.md` | ❌ → `MODEL_VARIABLES.md` |
| `AGENT_CONTROL_ARCHITECTURE.md` | ❌ → `ARCHITECTURE.md` |
| `atomic_decomposition_model.md` | ❌ → `MODEL_CORE.md` |
| `complexity_classification_formula.md` | ❌ → `FORMULAS_REFERENCE.md` |
| `task_decomposition_model.md` | ❌ → `MODEL_CORE.md` |
| `MISSING_FACTORS_ANALYSIS.md` | ❌ → `MODEL_CORE.md` |
| `MANUS_INTEGRATION_REPORT.md` | ❌ → `README.md` или `PROJECT_NOTE.md` |
| `IMPLEMENTATION_SUMMARY.md` | ❌ → `README.md` |

---

## 📝 Содержание чистовиков

### 1. README.md — Входная точка

```markdown
# AI-Agent Freelancer Model

## Быстрый старт
## Структура проекта
## Ключевые концепции (ссылки)
## Как читать документацию
## TODO / Roadmap
```

### 2. MODEL_CORE.md — Ядро математической модели

```markdown
# Φ, Υ, Ω, Γ, Q, Ψ — Управляющие функции

## 1. Φ(·) — Profit Function
   - Определение: (R - C) / T
   - Входы: P, S, Q, C, T
   - Выход: Φ_profit

## 2. Υ(·) — Reputation Function  
   - Определение: рейтинг, retention, feedback
   - Формула: γ₁·R̄ + γ₂·τ_ret + ...

## 3. Ω(·) — Evolution Function
   - ZPD learning, knowledge accumulation
   - Кривые: забывание, transfer

## 4. Γ(·) — Compliance Function
   - VETO: hard constraint
   - Γ = 0 (pass) или -∞ (fail)

## 5. Q(·) — Quality Function
   - Q_total = Σ w_i · q_i · φ_i (10 факторов из Manus)
   - Интеграция с Manus

## 6. Ψ(·) — Risk Function
   - Определение: P_fail · (C_direct + C_rep)
   - Risk budgeting

## 7. Целевая функция
   D*(T) = argmax [λ_φ·Φ + λ_υ·Υ + λ_ω·Ω - λ·C]
   s.t. Γ = 0, Q ≥ q_min, Ψ ≤ ψ_max

## 8. 17 Capability Factors (x₁-x₁₇)
   - Таблица с β, δ коэффициентами
   - Синергии Δγ
```

### 3. MODEL_VARIABLES.md — Таксономия переменных

```markdown
# Единая система переменных

## 1.1 Primitives (P_, B_, T_, L_, Q_, C_, N_, R_, S_, K_, A_)
## 1.2 State (C_spent, T_elapsed, N_tasks_*, Φ_historical, Υ_rating, K_knowledge, A_autonomy, L_health)
## 1.3 Derived (C_remaining, T_remaining, S_success_rate, R_expected, Λ_load, Ω_diversity)
## 1.4 Outputs (Φ_profit, Υ_reputation, Ω_evolution, Q_quality, Ψ_risk, VoI_info, H_entropy, Γ_status)
## 1.5 Policy (λ_*, q_min, ψ_max, c_max, Γ_rules)

## Правила именования
## Глоссарий
## Примеры использования
```

### 4. ARCHITECTURE.md — Системная архитектура

```markdown
# Архитектура AI-Agent Freelancer

## 1. Иерархия уровней
   - Meta (Mission)
   - Strategic (Orchestrator)
   - Tactical (Agent)
   - Operational (API)

## 2. 4-ная система внутренней среды
   - Sensors: метрики
   - Triggers: события
   - Homeostat: PID-регуляция
   - Hormones: медленные модуляторы

## 3. Внешняя среда
   - Sensors для рынка, задач, клиентов
   - Адаптация внутренней среды

## 4. Синтезатор сигнала → Промт
   - Бинарный → структурированный контекст
   - Алгоритмика конвертации
   - Связь с памятью

## 5. Manus интеграция
   - ai_super_router
   - digital_garden
   - Knowledge graph
```

### 5. FORMULAS_REFERENCE.md — Все формулы

```markdown
# Справочник формул

## 1. Profit Function
   Φ(x) = (R - C) / T

## 2. Reputation Function  
   Υ = γ₁·R̄ + γ₂·τ_ret + ...

## 3. Evolution Function
   L_s(t) = L_max·(1 - e^(-η·t^γ)) + L_0
   Φ(t,n) = e^(-t/(S·(1+κ·n)^ψ))
   ZPD = ZPD_base · (1 + α_M·M - α_CL·CL + α_η·η)

## 4. Risk Function
   Ψ = P_fail · (C_direct + C_rep)

## 5. Quality Function (Manus)
   Q_total = Σ w_i · q_i · φ_i

## 6. Atomic Decomposition
   D*(T) = argmax [U - λ·C]
   δ(T) = σ(w_δ·f(T) + b_δ)
   ...

## 7. Синергии
   γ_syn = Σ Δγ_ij · x_i · x_j

## 8. Complexity Classification
   ĉ = argmax P(c|x, θ)
   ...

## 9. Test-Time Compute
   S_reason = S + β_reason · log(1 + T_think/T_base)
   ...

## 10. Inference Optimization
    T_opt = T(x) · Π (1 - δ_o)
    ...
```

### 6. PROJECT_NOTE.md — Рабочие заметки

```markdown
# PROJECT_NOTE — Рабочие заметки

## Критические заметки пользователя
## Текущие задачи
## Журнал изменений
## Следующая сессия
## Контекст для загрузки
```

---

## 📋 План выполнения

| Этап | Действие | Файлы | Приоритет |
|------|----------|-------|-----------|
| 1 | Создать `MODEL_CORE.md` | Объединить 5 файлов | 🔴 |
| 2 | Создать `MODEL_VARIABLES.md` | UNIFIED_VARIABLE_SYSTEM | 🔴 |
| 3 | Создать `ARCHITECTURE.md` | AGENT_CONTROL_ARCHITECTURE | 🟡 |
| 4 | Создать `FORMULAS_REFERENCE.md` | Вынести все формулы | 🟡 |
| 5 | Сократить `PROJECT_NOTE.md` | До ~1000 строк | 🟡 |
| 6 | Создать `README.md` | Обзор | 🟡 |
| 7 | Удалить старые файлы | 8 файлов | 🟢 |
| 8 | Очистить Manus дубли | _contents папки | 🟢 |

---

## ✅ Чеклист унификации формул

После консолидации исправить:

| # | Проблема | Действие |
|---|----------|----------|
| 1 | Φ(·) — двойное определение | Φ = Profit только |
| 2 | φ — несколько значений | φ = confidence только |
| 3 | Ψ(·) — не определена | Формализовать |
| 4 | γ_syn — непонятна | Φ_R или константа |
| 5 | Q_total из Manus | Интегрировать с Q(·) |
| 6 | ZPD — из Manus | Интегрировать с Ω(·) |
| 7 | 4-ная система | Описать в ARCHITECTURE |
| 8 | Бинарный → промт | Описать в ARCHITECTURE |

---

*Создано: 2026-07-06*
*Рекомендация для команды*
