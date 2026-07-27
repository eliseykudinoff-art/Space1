# Space1 -- Описание тестов: Utility Composite (XiCoefficients, PhiRCalculator)

> **Дата:** 2026-07-26
> **Автор:** AI-ревьюер
> **Статус:** Актуально для Space1 Phase 4 Fix 22
> **Файл теста:** `test_utility_composite.py`
> **Результат:** 26/26 тестов пройдены (pytest)

---

## Часть I. Философия теста

Тестовый набор проверяет модуль `utility/composite.py` -- составные формулы Xi (G17) и Phi_R (G18).

Каждый тест:
- Проверен против реального кода (запущен через pytest)
- Имеет докстринг = контракт + формула + обоснование
- FAILED = реальный баг, не ошибка теста

---

## Часть II. Структура тестов

### UNIT: XiCoefficients (`TestXiCoefficientsUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_xi_basic_calculation` | Xi = alpha*Q - beta*(O_time + O_cost) | PASS |
| `test_xi_quality_clamped_to_one` | Q > 1.0 -> clamped to 1.0 | PASS |
| `test_xi_quality_clamped_to_zero` | Q < 0.0 -> clamped to 0.0 | PASS |
| `test_xi_opportunity_clamped_to_zero` | O < 0.0 -> clamped to 0.0 | PASS |
| `test_xi_maximum_quality_zero_opportunity` | Q=1.0, O=0.0 -> Xi = alpha | PASS |
| `test_xi_zero_quality_maximum_opportunity` | Q=0.0, O=2.0 -> Xi = -2*beta | PASS |
| `test_xi_alpha_zero_returns_negative_opportunity` | alpha=0.0 -> только штраф | PASS |
| `test_xi_beta_zero_returns_quality_bonus` | beta=0.0 -> только бонус | PASS |
| `test_xi_default_weights_from_config` | Default weights из config | PASS |
| `test_xi_components_to_dict` | Сериализация XiComponents | PASS |

### UNIT: PhiRCalculator (`TestPhiRCalculatorUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_phi_r_basic_calculation` | Phi_R = Phi*Gamma*(1+alpha_rep*Upsilon) - lambda_psi*Psi | PASS |
| `test_phi_r_gamma_zero_compliance_failed` | Gamma=0.0 -> Phi_R = -lambda_psi*Psi | PASS |
| `test_phi_r_high_psi_clamped` | Psi > 1.0 -> clamped to 1.0 | PASS |
| `test_phi_r_negative_phi` | Phi < 0 -> Phi_R отрицательный | PASS |
| `test_phi_r_alpha_rep_zero_no_reputation_bonus` | alpha_rep=0.0 -> multiplier=1.0 | PASS |
| `test_phi_r_lambda_psi_zero_no_risk_penalty` | lambda_psi=0.0 -> penalty=0.0 | PASS |
| `test_phi_r_upsilon_zero_no_reputation` | Upsilon=0.0 -> multiplier=1.0 | PASS |
| `test_phi_r_gamma_clamped` | Gamma > 1.0 -> clamped to 1.0 | PASS |
| `test_phi_r_default_weights_from_config` | Default weights из config | PASS |
| `test_phi_r_components_to_dict` | Сериализация PhiRComponents | PASS |

### PAIR: Xi + PhiR (`TestPairXiPhiR`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_xi_and_phi_r_both_positive_for_good_task` | Хорошая задача -> обе метрики > 0 | PASS |
| `test_xi_negative_phi_r_positive_possible` | Xi < 0, Phi_R > 0 (возможно) | PASS |

### INTEGRITY (`TestIntegrityComposite`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_xi_components_alpha_plus_beta_approx_one` | alpha + beta <= 1.5 | PASS |
| `test_phi_r_multiplier_positive` | Reputation multiplier >= 1.0 | PASS |
| `test_clamping_preserves_order` | Clamping сохраняет порядок | PASS |

### REGRESSION (`TestRegressionComposite`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_xi_calculate_does_not_mutate_inputs` | Иммутабельность входа | PASS |

---

## Часть III. Сводка багов

Багов не найдено. Все 26 тестов пройдены.

---

## Часть IV. Параметры теста

### Запуск

```bash
export PYTHONPATH=/path/to/space1/src
pytest tests/test_utility_composite.py -v
```

### Зависимости

- `space1.utility.composite` (XiCoefficients, PhiRCalculator)
- `pytest`

### Покрытие

- **XiCoefficients:** 10 тестов
- **PhiRCalculator:** 10 тестов
- **PAIR:** 2 теста
- **INTEGRITY:** 3 теста
- **REGRESSION:** 1 тест

**Итого: 26 тестов, 26 пройдены, 0 skipped, 0 xfailed.**

---

*Документ создан: 2026-07-26*
*Версия: 1.0*
*Статус: Актуально для Space1 Phase 4 Fix 22*
