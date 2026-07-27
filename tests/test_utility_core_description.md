# Space1 — Описание тестов: Utility Core (Φ, Q, Ψ, 𝒟, Kalman, Γ)

> **Дата:** 2026-07-25
> **Автор:** AI-ревьюер
> **Статус:** Актуально для Space1 Phase 4 Fix 22
> **Файл теста:** `test_utility_core.py`
> **Результат:** 44/44 тестов пройдены (pytest)

---

## Часть I. Философия теста

Тестовый набор проверяет модуль `utility/__init__.py` — математическое ядро Space1.

Каждый тест:
- Проверен против реального кода (запущен через pytest)
- Имеет докстринг = контракт + обоснование
- FAILED = реальный баг, не ошибка теста
- Содержит комментарий `# ЭТО БАГ` если поведение отличается от ожидаемого

---

## Часть II. Структура тестов

### UNIT: compute_phi позиционная (`TestComputePhiPositional`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_phi_positional_basic` | compute_phi(100, 0.8, 20, 2) = 40.5 | PASS |
| `test_phi_positional_zero_time` | time=0 → max(t, 0.1) | PASS |
| `test_phi_positional_quality_below_expected` | quality < 0.7 → penalty | PASS |
| `test_phi_positional_platform_fees` | C_platform, C_processing | PASS |

### UNIT: compute_phi legacy (`TestComputePhiLegacy`) — БАГ

| Тест | Что проверяет | Реальное поведение | Статус |
|------|---------------|-------------------|--------|
| `test_phi_legacy_returns_291_not_40` | compute_phi(100, 20, 2) | 291.0 | PASS (баг) |
| `test_phi_legacy_with_task_and_agent` | task+agent → phi | float > 0 | PASS |

### UNIT: compute_quality позиционная (`TestComputeQualityPositional`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_quality_positional_equal_weights` | Равные веса → 0.85 | PASS |
| `test_quality_weights_must_sum_to_one` | Веса ≠ 1.0 → AssertionError | PASS |
| `test_quality_clamped` | Значения > 1 → clamped 1.0 | PASS |

### UNIT: compute_quality legacy (`TestComputeQualityLegacy`) — БАГ

| Тест | Что проверяет | Реальное поведение | Статус |
|------|---------------|-------------------|--------|
| `test_quality_legacy_default_weights` | Default weights → 0.775 | PASS |
| `test_quality_legacy_timeliness_from_deadline` | t_actual/t_deadline → timeliness | PASS |
| `test_quality_positional_ignores_t_actual_t_deadline` | Позиционные args игнорируют t_actual | PASS (баг) |

### UNIT: evaluate_decision_rule (`TestEvaluateDecisionRule`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_level1_reject_gamma_hard_neg_inf` | gamma_hard=-inf → REJECT | PASS |
| `test_level1_reject_veto_type_hard` | veto_type=HARD → REJECT | PASS |
| `test_level2_decline_psi_exceeds` | psi > psi_max → DECLINE | PASS |
| `test_level2_decline_cost_below_min` | C_t < C_min → DECLINE | PASS |
| `test_level3_clarify_entropy` | H_TZ > max → CLARIFY | PASS |
| `test_level3_clarify_voi_exceeds_cost` | VoI > C_info → CLARIFY | PASS |
| `test_level3_clarify_h_val_below_threshold` | H_val < H_clarify → CLARIFY | PASS |
| `test_level4_execute` | U>0, Q>=q_min → EXECUTE | PASS |
| `test_level5_decline_utility_non_positive` | U<=0 → DECLINE | PASS |
| `test_level5_decline_quality_below_min` | Q < q_min → DECLINE | PASS |

### UNIT: evaluate_decision_rule mission profiles (`TestEvaluateDecisionRuleMission`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_survival_reduces_psi_max` | psi_max *= 0.5 → DECLINE | PASS |
| `test_growth_increases_psi_max` | psi_max *= 1.5 → EXECUTE | PASS |
| `test_charity_lowers_thresholds` | C_min = 0.1 → EXECUTE | PASS |
| `test_balanced_default` | Без калибровки → EXECUTE | PASS |

### UNIT: KalmanFilter (`TestKalmanFilter`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_kalman_initial_state` | initial_state | PASS |
| `test_kalman_predict_increases_covariance` | P += Q | PASS |
| `test_kalman_update_converges` | Сходимость к observed | PASS |
| `test_kalman_step_returns_updated_state` | step → x | PASS |

### UNIT: check_gamma_hard/soft (`TestCheckGamma`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_gamma_hard_all_pass` | Пустой список → 0.0 | PASS |
| `test_gamma_hard_one_fails` | Blocked → -inf | PASS |
| `test_gamma_hard_exception_returns_neg_inf` | Exception → -inf (bare except) | PASS (баг) |
| `test_gamma_soft_no_penalty` | Пустой список → 0.0 | PASS |
| `test_gamma_soft_accumulates_penalty` | Два rule → сумма весов | PASS |

### PAIR: compute_phi → evaluate_decision_rule (`TestPairPhiDecision`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_positive_phi_positive_utility_execute` | Φ>0, U>0 → EXECUTE | PASS |
| `test_negative_phi_decline` | Φ<0 → DECLINE | PASS |

### PAIR: compute_quality → evaluate_decision_rule (`TestPairQualityDecision`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_high_quality_execute` | Q=0.9 >= 0.5 → EXECUTE | PASS |
| `test_low_quality_decline` | Q=0.3 < 0.5 → DECLINE | PASS |

### INTEGRITY (`TestIntegrityUtility`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_bare_except_in_check_gamma` | except Exception ×2 | PASS (баг) |
| `test_evaluate_decision_rule_no_gamma_soft` | gamma_soft отсутствует | PASS (баг) |
| `test_compute_phi_legacy_confuses_cost_and_quality` | Конфликт сигнатур | PASS (баг) |

### REGRESSION (`TestRegressionUtility`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_compute_phi_not_returns_none` | Не None | PASS |
| `test_evaluate_decision_rule_not_returns_none` | Не None | PASS |

---

## Часть III. Сводка багов

### Найденные баги

| ID | Баг | Где | Почему важно | Статус в тесте |
|----|-----|-----|-------------|----------------|
| **BUG-UTIL-001** | `compute_phi(100, 20, 2)` → 291 вместо 40 | `utility/__init__.py` | Конфликт позиционной и legacy сигнатур | Assert на реальное поведение |
| **BUG-UTIL-002** | `compute_quality` позиционные args игнорируют `t_actual`/`t_deadline` | `utility/__init__.py` | Keyword-only params не работают с позиционными float | Assert на реальное поведение |
| **BUG-UTIL-003** | `gamma_soft` нигде не используется в `evaluate_decision_rule` | `utility/__init__.py` | Soft compliance игнорируется | Assert на отсутствие в коде |
| **BUG-UTIL-004** | `except Exception: pass` в `check_gamma_hard` и `check_gamma_soft` | `utility/__init__.py` | Ошибки маскируются | Assert на присутствие |

### Проверенные контракты (багов нет)

| Контракт | Результат |
|----------|-----------|
| `compute_phi` позиционная: Φ = (price*(1+b_Q) - cost) / max(time, 0.1) | ✅ |
| `compute_quality` позиционная: Q = Σ w_i * q_i, clamped [0,1] | ✅ |
| `compute_quality` веса суммируются в 1.0 (assert) | ✅ |
| `evaluate_decision_rule` 5 уровней каскада | ✅ |
| `evaluate_decision_rule` mission profiles (SURVIVAL/GROWTH/CHARITY) | ✅ |
| `KalmanFilter` predict/update/step | ✅ |
| `check_gamma_hard` логика AND | ✅ |
| `check_gamma_soft` аккумуляция penalty | ✅ |

---

## Часть IV. Параметры теста

### Запуск

```bash
export PYTHONPATH=/path/to/space1/src
pytest tests/test_utility_core.py -v
```

### Зависимости

- `space1.utility` (compute_phi, compute_quality, compute_psi, evaluate_decision_rule, KalmanFilter, check_gamma_hard, check_gamma_soft)
- `space1.models.task` (Task, TaskPriority)
- `space1.models.agents` (Agent, AgentCapabilities, AgentMetrics)
- `space1.compliance.core` (Action, Rule)
- `pytest`

### Покрытие

- **compute_phi позиционная:** 4 теста
- **compute_phi legacy:** 2 теста (1 баг)
- **compute_quality позиционная:** 3 теста
- **compute_quality legacy:** 3 теста (1 баг)
- **evaluate_decision_rule:** 10 тестов
- **evaluate_decision_rule mission:** 4 теста
- **KalmanFilter:** 4 теста
- **check_gamma:** 5 тестов (1 баг)
- **PAIR phi→decision:** 2 теста
- **PAIR quality→decision:** 2 теста
- **INTEGRITY:** 3 теста (3 бага)
- **REGRESSION:** 2 теста

**Итого: 44 теста, 44 пройдены, 0 skipped, 0 xfailed.**

---

*Документ создан: 2026-07-25*  
*Версия: 1.0*  
*Статус: Актуально для Space1 Phase 4 Fix 22*
