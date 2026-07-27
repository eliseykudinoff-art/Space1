# Space1 — Naming Convention

> **Статус:** ✅ Принято
> **Дата:** 2026-07-09
> **Reference:** DEVELOPMENT_PLAN.md - G15

---

## 1. Mathematical Functions

| Symbol | Name | Python | Example |
|--------|------|--------|---------|
| Φ | Profit Function | `compute_phi()` | `phi = compute_phi(task, agent)` |
| Γ | Compliance Veto | `check_gamma()` | `if check_gamma(action):` |
| Q | Quality Function | `compute_quality()` | `quality = compute_quality(result)` |
| Ψ | Risk Function | `compute_psi()` | `risk = compute_psi(task)` |
| Υ | Reputation | `update_upsilon()` | `rep = update_upsilon(rating)` |
| Ω | Evolution | `compute_omega()` | `growth = compute_omega(state)` |
| H | Homeostasis | `compute_h()` | `homeo = compute_h(state)` |
| VoI | Value of Information | `compute_voi()` | `value = compute_voi(info)` |

---

## 2. Classes

| Type | Convention | Example |
|------|------------|---------|
| Core Classes | PascalCase | `GammaVeto`, `MetricTracker` |
| Data Classes | PascalCase | `Action`, `Task`, `AgentState` |
| Rule Classes | PascalCase + Rule suffix | `MaxCostRule`, `BlockedActionsRule` |
| Agent Classes | PascalCase + Agent suffix | `ScoutAgent`, `WorkerAgent` |

---

## 3. Functions/Methods

| Type | Convention | Example |
|------|------------|---------|
| Compute functions | `compute_<name>()` | `compute_phi()` |
| Check functions | `check_<name>()` | `check_gamma()` |
| Update functions | `update_<name>()` | `update_upsilon()` |
| Get functions | `get_<name>()` | `get_state()` |
| Private methods | `_method_name()` | `_validate()` |

---

## 4. Variables

| Type | Convention | Example |
|------|------------|---------|
| Constants | UPPER_SNAKE | `MAX_COST`, `TOKEN_PRICE` |
| Class attributes | snake_case | `self.resource_cost` |
| Local variables | snake_case | `is_compliant` |
| Function params | snake_case | `def compute_phi(task, agent)` |
| Private variables | _underscore | `_internal_state` |

---

## 5. Files/Directories

| Type | Convention | Example |
|------|------------|---------|
| Python modules | snake_case | `compliance/core.py` |
| Test files | test_<name>.py | `test_gamma_veto.py` |
| Data files | snake_case | `config/rules.yaml` |
| Markdown docs | CAPITALIZE_WORDS.md | `NAMING_CONVENTION.md` |

---

## 6. Mathematical Notation (Code vs Math)

| Math | Python | Notes |
|------|--------|-------|
| Φ | `phi` | Greek letter as lowercase |
| Γ | `gamma` | Greek letter as lowercase |
| x₁, x₂ | `x1`, `x2` | Subscript as number |
| S(x) | `success_rate(x)` | Function name + arg |
| ∑ | `sum()` | Python built-in |
| ∈ | `in` | Python keyword |
| → | `->` | Type hint arrow |

---

## 7. Module Structure

```
src/space1/
├── __init__.py          # Public API exports
├── compliance/          # Γ (Gamma) - Compliance Veto
│   ├── __init__.py
│   └── core.py         # GammaVeto, Rule, etc.
├── metrics/            # Metrics tracking
│   ├── __init__.py
│   └── tracker.py
├── factors/            # x₁-x₁₇ factors
│   ├── __init__.py
│   └── registry.py
├── models/             # Data classes
│   ├── __init__.py
│   └── core.py        # Action, Task, AgentState
├── mission/            # Mission & Compliance hierarchy
│   ├── __init__.py
│   └── core.py
└── orchestrator/       # Main orchestration
    ├── __init__.py
    └── core.py
```

---

## 8. Export Convention

В `__init__.py` экспортируем только публичный API:

```python
# src/space1/__init__.py
from .compliance.core import GammaVeto, Rule, Action
from .metrics.tracker import MetricTracker
# Не экспортируем внутренние детали
```

---

*Принято: 2026-07-09*
