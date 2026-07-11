# 📋 PROJECT CONTEXT

**Обновлено:** 2026-07-11
**Проект:** Space1 (ранее Manus) — Автономный AI-агент Фрилансер
**Статус:** ✅ Pre-MVP ЗАВЕРШЁН

---

## 🚨 ОБЯЗАТЕЛЬНО К ПРОЧТЕНИЮ ПЕРЕД СТАРТОМ СЕССИИ

1. Прочитать `DEVELOPMENT_PLAN.md`
2. Проверить текущую фазу и статус
3. Начать с Definition of Done для текущей фазы

---

## 📚 СТРУКТУРА ДОКУМЕНТАЦИИ (drafts branch)

### ⚠️ ВАЖНО: Порядок изучения

```
ОСНОВНОЙ ИСТОЧНИК (читать первым):
├── MATHEMATICAL_ANALYSIS.md     ← Описание Manus/Space1
└── AGENT_CONTROL_ARCHITECTURE.md ← Архитектура функций управления

МАТЕМАТИКА (для Phase 2+):
├── MATHEMATICAL_FORMULAS.md     ← Все формулы (Φ, Q, Ψ, Υ, Γ, Ω)
└── CYBERNETICS_HOMEOSTASIS_FORMULAS.md ← Кибернетика, PID, гомеостаз

ПОБОЧНЫЕ (НЕ первоисточники, искажают восприятие):
├── FREELANCER_AGENT_ARCHITECTURE.md  ← Альтернативная версия
└── COMPARATIVE_ANALYSIS_REPORT.md   ← Сравнение 2 систем с синтезом
```

### Что такое Space1 ( Manus)

**Manus → Space1** — AI-агент для фриланс-платформы:
- Максимизирует Φ = (R-C)/T при соблюдении Γ (compliance)
- Гомеостатическая регуляция: баланс денег, репутации, загрузки
- Orchestrator: Φ, Γ, Υ, Ψ, Q, Ω, H

---

## 📍 ТЕКУЩИЙ СТАТУС РАЗРАБОТКИ

| Фаза | Статус |
|------|--------|
| Pre-MVP | ✅ Завершён (7/7) |
| Phase 1 | ✅ Завершён (3/3) |
| Phase 2 | ⚪ Ожидает |

### Pre-MVP Выполнено
- G1: GammaVeto, G4: MetricTracker, G9: FactorRegistry
- G15: NAMING_CONVENTION, G16: Mission hierarchy
- G20: Notation, G23: Task model

### Phase 1 Выполнено
- G5: TokenCostTracker
- G11: Data classes (Task, Agent, AgentContext)
- G14: MetricRegistry

### Тесты: 68 passed ✅

---

## 📌 СЛЕДУЮЩИЙ ШАГ

**Phase 2: Utility Functions & MVP Decision Loop** — использовать текущий код `src/space1/` как основу, а `docs/drafts/` только как справочник формул. Приоритет: связать `Task`, `AgentContext`, `GammaVeto`, `FactorRegistry`, `TokenCostTracker`, `MetricRegistry` и YAML-конфигурацию в end-to-end выбор действия.

---

*Обновлено: 2026-07-11*
