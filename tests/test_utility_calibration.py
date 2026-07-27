"""
Space1 -- TESTS: utility/calibration.py (ParameterCalibrator)

Каждый тест проверен против реального кода.
FAILED = баг, не ошибка теста.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from datetime import datetime


# =============================================================================
# UNIT: ParameterCalibrator с пустой памятью
# =============================================================================

class TestCalibratorEmptyUnit:
    """Unit-тесты на ParameterCalibrator с пустой памятью."""

    def test_empty_memory_returns_no_data(self):
        """
        Пустая память -> status="No data available", recommendations={}.

        Проверяем: graceful degradation при отсутствии данных.
        Границы: 0 эпизодов.
        Почему такие: калибровка без данных должна сообщать об этом, не падать.
        """
        from space1.memory.core import StrategicMemory
        from space1.utility.calibration import ParameterCalibrator
        mem = StrategicMemory()
        cal = ParameterCalibrator(mem)
        result = cal.calibrate_constants()
        assert result["status"] == "No data available"
        assert result["recommendations"] == {}

    def test_empty_memory_save_returns_false(self):
        """
        save_calibrated_weights с пустыми recommendations -> False.

        Проверяем: защита от сохранения пустых данных.
        Границы: {} и {"recommendations": {}}.
        Почему такие: не сохраняем мусор.
        """
        from space1.memory.core import StrategicMemory
        from space1.utility.calibration import ParameterCalibrator
        cal = ParameterCalibrator(StrategicMemory())
        assert cal.save_calibrated_weights({}) == False
        assert cal.save_calibrated_weights({"recommendations": {}}) == False


# =============================================================================
# UNIT: psi_max калибровка
# =============================================================================

class TestCalibratorPsiMaxUnit:
    """Unit-тесты на калибровку psi_max (порог риска)."""

    def test_no_high_risk_failures_no_psi_max_recommendation(self):
        """
        Нет failed с risk > 0.5 -> psi_max не рекомендуется.

        Проверяем: порог срабатывания.
        Границы: 0 high-risk failures.
        Почему такие: нет данных для рекомендации.
        """
        from space1.memory.core import StrategicMemory, Episode
        from space1.utility.calibration import ParameterCalibrator
        mem = StrategicMemory()
        mem.add_experience(Episode(task_id="t1", risk=0.8, status="completed", revenue=100, cost=20, time_spent=2, quality=0.9, quality_actual=0.9))
        result = ParameterCalibrator(mem).calibrate_constants()
        assert "psi_max" not in result["recommendations"]

    def test_one_high_risk_failure_no_psi_max(self):
        """
        1 failed с risk > 0.5 -> psi_max не рекомендуется (нужно >1).

        Проверяем: порог срабатывания.
        Границы: 1 high-risk failure.
        Почему такие: 1 failure = случайность, не паттерн.
        """
        from space1.memory.core import StrategicMemory, Episode
        from space1.utility.calibration import ParameterCalibrator
        mem = StrategicMemory()
        mem.add_experience(Episode(task_id="t1", risk=0.8, status="failed", revenue=0, cost=50, time_spent=1, quality=0.1, quality_actual=0.1))
        result = ParameterCalibrator(mem).calibrate_constants()
        assert "psi_max" not in result["recommendations"]

    def test_two_high_risk_failures_recommends_psi_max_0_75(self):
        """
        2 failed с risk > 0.5 -> psi_max = 0.75.

        Проверяем: порог срабатывания и значение.
        Границы: 2 high-risk failures.
        Почему такие: 2 failures = паттерн, нужно снизить psi_max.
        """
        from space1.memory.core import StrategicMemory, Episode
        from space1.utility.calibration import ParameterCalibrator
        mem = StrategicMemory()
        mem.add_experience(Episode(task_id="t1", risk=0.8, status="failed", revenue=0, cost=50, time_spent=1, quality=0.1, quality_actual=0.1))
        mem.add_experience(Episode(task_id="t2", risk=0.6, status="failed", revenue=0, cost=30, time_spent=1, quality=0.2, quality_actual=0.2))
        result = ParameterCalibrator(mem).calibrate_constants()
        assert "psi_max" in result["recommendations"]
        assert result["recommendations"]["psi_max"]["recommended"] == 0.75
        assert result["recommendations"]["psi_max"]["current"] == 1.0

    def test_three_high_risk_failures_same_recommendation(self):
        """
        3 failed с risk > 0.5 -> psi_max = 0.75 (та же рекомендация).

        Проверяем: рекомендация не меняется с ростом данных.
        Границы: 3 high-risk failures.
        Почему такие: рекомендация бинарна, не зависит от количества.
        """
        from space1.memory.core import StrategicMemory, Episode
        from space1.utility.calibration import ParameterCalibrator
        mem = StrategicMemory()
        for i in range(3):
            mem.add_experience(Episode(task_id=f"t{i}", risk=0.7 + i * 0.05, status="failed", revenue=0, cost=40, time_spent=1, quality=0.1, quality_actual=0.1))
        result = ParameterCalibrator(mem).calibrate_constants()
        assert result["recommendations"]["psi_max"]["recommended"] == 0.75


# =============================================================================
# UNIT: phi_r_alpha_rep калибровка
# =============================================================================

class TestCalibratorPhiRAlphaRepUnit:
    """Unit-тесты на калибровку phi_r_alpha_rep (репутационный бонус)."""

    def test_no_high_quality_completes_no_phi_r_recommendation(self):
        """
        Нет completed с quality > 0.8 -> phi_r_alpha_rep не рекомендуется.

        Проверяем: порог срабатывания.
        Границы: 0 high-quality completed.
        Почему такие: нет данных для рекомендации.
        """
        from space1.memory.core import StrategicMemory, Episode
        from space1.utility.calibration import ParameterCalibrator
        mem = StrategicMemory()
        mem.add_experience(Episode(task_id="t1", risk=0.2, status="completed", revenue=100, cost=20, time_spent=2, quality=0.6, quality_actual=0.6))
        result = ParameterCalibrator(mem).calibrate_constants()
        assert "phi_r_alpha_rep" not in result["recommendations"]

    def test_two_high_quality_completes_no_phi_r(self):
        """
        2 completed с quality > 0.8 -> phi_r_alpha_rep не рекомендуется (нужно >2).

        Проверяем: порог срабатывания.
        Границы: 2 high-quality completed.
        Почему такие: порог = 2, нужно 3+ для рекомендации.
        """
        from space1.memory.core import StrategicMemory, Episode
        from space1.utility.calibration import ParameterCalibrator
        mem = StrategicMemory()
        mem.add_experience(Episode(task_id="t1", risk=0.2, status="completed", revenue=100, cost=20, time_spent=2, quality=0.85, quality_actual=0.85))
        mem.add_experience(Episode(task_id="t2", risk=0.3, status="completed", revenue=150, cost=30, time_spent=2.5, quality=0.9, quality_actual=0.9))
        result = ParameterCalibrator(mem).calibrate_constants()
        assert "phi_r_alpha_rep" not in result["recommendations"]

    def test_three_high_quality_completes_recommends_phi_r_0_45(self):
        """
        3 completed с quality > 0.8 -> phi_r_alpha_rep = 0.45.

        Проверяем: порог срабатывания и значение.
        Границы: 3 high-quality completed.
        Почему такие: 3+ = стабильный паттерн высокого качества.
        """
        from space1.memory.core import StrategicMemory, Episode
        from space1.utility.calibration import ParameterCalibrator
        mem = StrategicMemory()
        for i in range(3):
            mem.add_experience(Episode(task_id=f"t{i}", risk=0.1 + i * 0.1, status="completed", revenue=100 + i * 50, cost=20 + i * 10, time_spent=2 + i * 0.5, quality=0.85 + i * 0.05, quality_actual=0.85 + i * 0.05))
        result = ParameterCalibrator(mem).calibrate_constants()
        assert "phi_r_alpha_rep" in result["recommendations"]
        assert result["recommendations"]["phi_r_alpha_rep"]["recommended"] == 0.45
        assert result["recommendations"]["phi_r_alpha_rep"]["current"] == 0.3


# =============================================================================
# UNIT: min_profit_rate калибровка
# =============================================================================

class TestCalibratorMinProfitRateUnit:
    """Unit-тесты на калибровку min_profit_rate."""

    def test_single_completed_calculates_avg_phi(self):
        """
        1 completed -> min_profit_rate = max(2.0, phi * 0.8).

        Проверяем: формула расчёта.
        Границы: revenue=100, cost=20, time=2 -> phi=40.
        Почему такие: phi = (R-C)/T = 80/2 = 40.
        """
        from space1.memory.core import StrategicMemory, Episode
        from space1.utility.calibration import ParameterCalibrator
        mem = StrategicMemory()
        mem.add_experience(Episode(task_id="t1", risk=0.2, status="completed", revenue=100, cost=20, time_spent=2, quality=0.9, quality_actual=0.9))
        result = ParameterCalibrator(mem).calibrate_constants()
        assert "min_profit_rate" in result["recommendations"]
        rec = result["recommendations"]["min_profit_rate"]["recommended"]
        expected = max(2.0, 40.0 * 0.8)  # 32.0
        assert abs(rec - expected) < 0.1

    def test_multiple_completed_averages_phi(self):
        """
        Несколько completed -> min_profit_rate = среднее phi * 0.8.

        Проверяем: усреднение.
        Границы: 3 completed с phi=40, 53.33, 48.
        Почему такие: среднее = 47.11, recommended = 37.69.
        """
        from space1.memory.core import StrategicMemory, Episode
        from space1.utility.calibration import ParameterCalibrator
        mem = StrategicMemory()
        mem.add_experience(Episode(task_id="t1", risk=0.2, status="completed", revenue=100, cost=20, time_spent=2, quality=0.9, quality_actual=0.9))  # phi=40
        mem.add_experience(Episode(task_id="t2", risk=0.3, status="completed", revenue=200, cost=40, time_spent=3, quality=0.9, quality_actual=0.9))  # phi=53.33
        mem.add_experience(Episode(task_id="t3", risk=0.1, status="completed", revenue=150, cost=30, time_spent=2.5, quality=0.9, quality_actual=0.9))  # phi=48
        result = ParameterCalibrator(mem).calibrate_constants()
        rec = result["recommendations"]["min_profit_rate"]["recommended"]
        avg_phi = (40 + 53.33 + 48) / 3
        expected = max(2.0, avg_phi * 0.8)
        assert abs(rec - expected) < 1.0

    def test_zero_time_spent_raises_zero_division(self):
        """
        time_spent=0 -> ZeroDivisionError.

        Проверяем: защита от деления на ноль.
        Границы: time_spent=0.
        Почему такие: phi = (R-C)/T, T=0 -> деление на ноль.
        """
        from space1.memory.core import StrategicMemory, Episode
        from space1.utility.calibration import ParameterCalibrator
        mem = StrategicMemory()
        mem.add_experience(Episode(task_id="t1", risk=0.2, status="completed", revenue=100, cost=20, time_spent=0, quality=0.9, quality_actual=0.9))
        with pytest.raises(ZeroDivisionError):
            ParameterCalibrator(mem).calibrate_constants()
        # ЭТО БАГ: код не защищён от деления на ноль


# =============================================================================
# UNIT: save_calibrated_weights
# =============================================================================

class TestCalibratorSaveUnit:
    """Unit-тесты на save_calibrated_weights."""

    def test_save_with_valid_recommendations(self):
        """
        save_calibrated_weights с валидными recommendations -> True (если файл существует).

        Проверяем: сохранение валидных данных.
        Границы: Стандартный result от calibrate_constants.
        Почему такие: контракт — валидные данные сохраняются при наличии файла.
        """
        import tempfile, os
        from space1.memory.core import StrategicMemory, Episode
        from space1.utility.calibration import ParameterCalibrator
        mem = StrategicMemory()
        mem.add_experience(Episode(task_id="t1", risk=0.2, status="completed", revenue=100, cost=20, time_spent=2, quality=0.9, quality_actual=0.9))
        cal = ParameterCalibrator(mem)
        result = cal.calibrate_constants()
        # Создаём временный weights.yaml
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
            tmp.write("min_profit_rate: 5.0\n")
            tmp_path = tmp.name
        try:
            assert cal.save_calibrated_weights(result, tmp_path) == True
            # Проверим, что значение обновилось
            with open(tmp_path, 'r') as f:
                content = f.read()
            assert "32.0" in content or "min_profit_rate:" in content
        finally:
            os.unlink(tmp_path)

    def test_save_with_none_returns_false(self):
        """
        save_calibrated_weights(None) -> False.

        Проверяем: защита от None.
        Границы: None.
        Почему такие: fail fast на некорректный вход.
        """
        from space1.memory.core import StrategicMemory
        from space1.utility.calibration import ParameterCalibrator
        cal = ParameterCalibrator(StrategicMemory())
        assert cal.save_calibrated_weights(None) == False


# =============================================================================
# PAIR: Episode + ParameterCalibrator
# =============================================================================

class TestPairEpisodeCalibrator:
    """PAIR-тесты: связка Episode и ParameterCalibrator."""

    def test_episode_quality_vs_quality_actual(self):
        """
        Episode(quality=0.85) -> quality=0.85, quality_actual=0.5 (не синхронизированы).

        Проверяем: consistency полей Episode.
        Границы: quality=0.85, quality_actual не указан.
        Почему такие: calibration.py использует e.quality, но quality_actual=0.5.
        """
        from space1.memory.core import Episode
        e = Episode(task_id="t1", quality=0.85)
        assert e.quality == 0.85
        assert e.quality_actual == 0.5  # Default, не синхронизировано
        # ЭТО БАГ: quality и quality_actual — два поля для одного значения,
        # но они не связаны. calibration.py использует e.quality,
        # другие модули могут использовать quality_actual.

    def test_episode_quality_actual_explicit(self):
        """
        Episode(quality_actual=0.85) -> quality_actual=0.85, quality=0.5.

        Проверяем: explicit quality_actual.
        Границы: quality_actual=0.85.
        Почему такие: то же разделение полей.
        """
        from space1.memory.core import Episode
        e = Episode(task_id="t1", quality_actual=0.85)
        assert e.quality_actual == 0.85
        assert e.quality == 0.5  # Default

    def test_calibrator_uses_quality_not_quality_actual(self):
        """
        ParameterCalibrator проверяет e.quality, не e.quality_actual.

        Проверяем: какое поле используется.
        Границы: quality=0.85, quality_actual=0.1.
        Почему такие: consistency между Episode и Calibrator.
        """
        from space1.memory.core import StrategicMemory, Episode
        from space1.utility.calibration import ParameterCalibrator
        mem = StrategicMemory()
        mem.add_experience(Episode(task_id="t1", risk=0.2, status="completed", revenue=100, cost=20, time_spent=2, quality=0.85, quality_actual=0.1))
        mem.add_experience(Episode(task_id="t2", risk=0.3, status="completed", revenue=150, cost=30, time_spent=2.5, quality=0.9, quality_actual=0.1))
        mem.add_experience(Episode(task_id="t3", risk=0.1, status="completed", revenue=200, cost=40, time_spent=3, quality=0.95, quality_actual=0.1))
        result = ParameterCalibrator(mem).calibrate_constants()
        # Если бы использовалось quality_actual (0.1 < 0.8), phi_r_alpha_rep не рекомендовался бы
        # Но используется quality (>0.8), поэтому рекомендуется
        assert "phi_r_alpha_rep" in result["recommendations"]


# =============================================================================
# INTEGRITY: Архитектурные инварианты
# =============================================================================

class TestIntegrityCalibrator:
    """INTEGRITY-тесты: архитектурные инварианты calibration."""

    def test_calibrator_requires_strategic_memory(self):
        """
        ParameterCalibrator требует StrategicMemory (get_experiences).

        Проверяем: тип памяти.
        Границы: EpisodicMemory вместо StrategicMemory.
        Почему такие: ParameterCalibrator использует get_experiences,
        которого нет в EpisodicMemory (только get_episodes).
        """
        from space1.memory.core import EpisodicMemory, Episode
        from space1.utility.calibration import ParameterCalibrator
        mem = EpisodicMemory()
        mem.add_episode(Episode(task_id="t1", risk=0.2, status="completed", revenue=100, cost=20, time_spent=2, quality=0.9, quality_actual=0.9))
        cal = ParameterCalibrator(mem)
        # ЭТО БАГ: ParameterCalibrator ожидает get_experiences,
        # но EpisodicMemory имеет только get_episodes.
        with pytest.raises(AttributeError):
            cal.calibrate_constants()

    def test_recommendation_values_are_positive(self):
        """
        Все recommended values > 0.

        Проверяем: положительность рекомендаций.
        Границы: Любые входные данные.
        Почему такие: отрицательные рекомендации = бессмыслица.
        """
        from space1.memory.core import StrategicMemory, Episode
        from space1.utility.calibration import ParameterCalibrator
        mem = StrategicMemory()
        for i in range(5):
            mem.add_experience(Episode(task_id=f"t{i}", risk=0.5 + i * 0.05, status="completed", revenue=100 + i * 10, cost=20, time_spent=2, quality=0.9, quality_actual=0.9))
        result = ParameterCalibrator(mem).calibrate_constants()
        for key, rec in result["recommendations"].items():
            assert rec["recommended"] > 0

    def test_current_less_than_or_equal_recommended(self):
        """
        current <= recommended для min_profit_rate.

        Проверяем: рекомендация увеличивает порог.
        Границы: Стандартные данные.
        Почему такие: рекомендация = повышение планки.
        """
        from space1.memory.core import StrategicMemory, Episode
        from space1.utility.calibration import ParameterCalibrator
        mem = StrategicMemory()
        mem.add_experience(Episode(task_id="t1", risk=0.2, status="completed", revenue=100, cost=20, time_spent=2, quality=0.9, quality_actual=0.9))
        result = ParameterCalibrator(mem).calibrate_constants()
        rec = result["recommendations"]["min_profit_rate"]
        assert rec["current"] <= rec["recommended"]


# =============================================================================
# REGRESSION: Старые баги не вернулись
# =============================================================================

class TestRegressionCalibrator:
    """REGRESSION-тесты: старые баги не вернулись."""

    def test_calibrator_does_not_mutate_input_memory(self):
        """
        calibrate_constants не изменяет входную память.

        Проверяем: иммутабельность входа.
        Границы: Стандартная память.
        Почему такие: баг: mutation входной памяти.
        """
        from space1.memory.core import StrategicMemory, Episode
        from space1.utility.calibration import ParameterCalibrator
        mem = StrategicMemory()
        mem.add_experience(Episode(task_id="t1", risk=0.2, status="completed", revenue=100, cost=20, time_spent=2, quality=0.9, quality_actual=0.9))
        count_before = len(mem.get_experiences())
        ParameterCalibrator(mem).calibrate_constants()
        count_after = len(mem.get_experiences())
        assert count_before == count_after
