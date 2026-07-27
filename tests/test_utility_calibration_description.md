# Space1 -- Описание тестов: Utility Calibration (ParameterCalibrator)

> **Дата:** 2026-07-26
> **Автор:** AI-ревьюер
> **Статус:** Актуально для Space1 Phase 4 Fix 22
> **Файл теста:** `test_utility_calibration.py`
> **Результат:** 21/21 тестов пройдены (pytest)

---

## Часть I. Философия теста

Тестовый набор проверяет модуль `utility/calibration.py` -- калибровку параметров на основе исторических эпизодов.

Каждый тест:
- Проверен против реального кода (запущен через pytest)
- Имеет докстринг = контракт + формула + обоснование
- FAILED = реальный баг, не ошибка теста
- Содержит комментарий `# ЭТО БАГ` при расхождении с документацией

---

## Часть II. Структура тестов

### UNIT: Empty memory (`TestCalibratorEmptyUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_empty_memory_returns_no_data` | Пустая память -> status="No data available" | PASS |
| `test_empty_memory_save_returns_false` | save_calibrated_weights({}) -> False | PASS |

### UNIT: psi_max (`TestCalibratorPsiMaxUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_no_high_risk_failures_no_psi_max_recommendation` | 0 failed с risk>0.5 -> нет рекомендации | PASS |
| `test_one_high_risk_failure_no_psi_max` | 1 failed -> нет рекомендации | PASS |
| `test_two_high_risk_failures_recommends_psi_max_0_75` | 2 failed -> psi_max=0.75 | PASS |
| `test_three_high_risk_failures_same_recommendation` | 3 failed -> та же рекомендация | PASS |

### UNIT: phi_r_alpha_rep (`TestCalibratorPhiRAlphaRepUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_no_high_quality_completes_no_phi_r_recommendation` | 0 completed с quality>0.8 -> нет | PASS |
| `test_two_high_quality_completes_no_phi_r` | 2 completed -> нет (нужно >2) | PASS |
| `test_three_high_quality_completes_recommends_phi_r_0_45` | 3 completed -> phi_r=0.45 | PASS |

### UNIT: min_profit_rate (`TestCalibratorMinProfitRateUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_single_completed_calculates_avg_phi` | 1 completed -> phi=(R-C)/T | PASS |
| `test_multiple_completed_averages_phi` | 3 completed -> среднее phi * 0.8 | PASS |
| `test_zero_time_spent_raises_zero_division` | time_spent=0 -> ZeroDivisionError | PASS (баг) |

### UNIT: Save (`TestCalibratorSaveUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_save_with_valid_recommendations` | Валидные recommendations -> True | PASS |
| `test_save_with_none_returns_false` | None -> False | PASS |

### PAIR: Episode + Calibrator (`TestPairEpisodeCalibrator`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_episode_quality_vs_quality_actual` | quality=0.85, quality_actual=0.5 | PASS (баг) |
| `test_episode_quality_actual_explicit` | quality_actual=0.85, quality=0.5 | PASS (баг) |
| `test_calibrator_uses_quality_not_quality_actual` | Calibrator читает quality | PASS |

### INTEGRITY (`TestIntegrityCalibrator`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_calibrator_requires_strategic_memory` | Требуется StrategicMemory | PASS (баг) |
| `test_recommendation_values_are_positive` | Все recommended > 0 | PASS |
| `test_current_less_than_or_equal_recommended` | current <= recommended | PASS |

### REGRESSION (`TestRegressionCalibrator`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_calibrator_does_not_mutate_input_memory` | Иммутабельность памяти | PASS |

---

## Часть III. Сводка багов

| ID | Баг | Где | Статус в тесте |
|----|-----|-----|----------------|
| **BUG-CAL-001** | `ParameterCalibrator` ожидает `get_experiences`, которого нет в `EpisodicMemory` | `utility/calibration.py` | `# ЭТО БАГ` в `test_calibrator_requires_strategic_memory` |
| **BUG-CAL-002** | `Episode` имеет `quality` и `quality_actual` -- два поля, не синхронизированы | `memory/core.py` | `# ЭТО БАГ` в `test_episode_quality_vs_quality_actual` |
| **BUG-CAL-003** | Деление на ноль при `time_spent=0` | `utility/calibration.py` | `# ЭТО БАГ` в `test_zero_time_spent_raises_zero_division` |

---

## Часть IV. Параметры теста

### Запуск

```bash
export PYTHONPATH=/path/to/space1/src
pytest tests/test_utility_calibration.py -v
```

### Зависимости

- `space1.utility.calibration` (ParameterCalibrator)
- `space1.memory.core` (Episode, StrategicMemory, EpisodicMemory)
- `pytest`

### Покрытие

- **Empty memory:** 2 теста
- **psi_max:** 4 теста
- **phi_r_alpha_rep:** 3 теста
- **min_profit_rate:** 3 теста
- **Save:** 2 теста
- **PAIR:** 3 теста
- **INTEGRITY:** 3 теста
- **REGRESSION:** 1 тест

**Итого: 21 тест, 21 пройден, 0 skipped, 0 xfailed.**

---

*Документ создан: 2026-07-26*
*Версия: 1.0*
*Статус: Актуально для Space1 Phase 4 Fix 22*
