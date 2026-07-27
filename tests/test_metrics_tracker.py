"""
Space1 — ПРОВЕРЕННЫЕ ТЕСТЫ: Metrics Tracker

Каждый тест проверен против реального кода.
FAILED-тесты = реальные баги, не ошибки тестов.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest


# =============================================================================
# UNIT: MetricRecord
# =============================================================================

class TestMetricRecordUnit:
    """Unit-тесты на MetricRecord dataclass."""

    def test_metric_record_creation(self):
        """
        MetricRecord(timestamp=1.0, value=0.5, raw_value=0.6, alpha=0.2) → поля установлены.

        Проверяем: создание записи.
        Границы: Стандартный кейс.
        Почему такие: базовая функциональность dataclass.
        """
        from space1.metrics.tracker import MetricRecord
        rec = MetricRecord(timestamp=1.0, value=0.5, raw_value=0.6, alpha=0.2)
        assert rec.timestamp == 1.0
        assert rec.value == 0.5
        assert rec.raw_value == 0.6
        assert rec.alpha == 0.2


# =============================================================================
# UNIT: MetricTracker
# =============================================================================

class TestMetricTrackerUnit:
    """Unit-тесты на MetricTracker."""

    def test_tracker_init_default_alpha(self):
        """
        MetricTracker() → default_alpha = 0.2.

        Проверяем: default alpha.
        Границы: Без аргументов.
        Почему такие: контракт default_alpha = 0.2.
        """
        from space1.metrics.tracker import MetricTracker
        tracker = MetricTracker()
        assert tracker._default_alpha == 0.2

    def test_tracker_init_custom_alpha(self):
        """
        MetricTracker(0.5) → default_alpha = 0.5.

        Проверяем: кастомный alpha.
        Границы: alpha = 0.5.
        Почему такие: проверка кастомного alpha.
        """
        from space1.metrics.tracker import MetricTracker
        tracker = MetricTracker(0.5)
        assert tracker._default_alpha == 0.5

    def test_tracker_init_alpha_zero_raises(self):
        """
        MetricTracker(0) → ValueError.

        Проверяем: alpha=0 отклоняется.
        Границы: alpha = 0.
        Почему такие: граничный случай — alpha=0 недопустим.
        """
        from space1.metrics.tracker import MetricTracker
        try:
            MetricTracker(0)
            assert False, "Должен был упасть с ValueError"
        except ValueError as e:
            assert "alpha must be in (0, 1]" in str(e)

    def test_tracker_init_alpha_negative_raises(self):
        """
        MetricTracker(-0.1) → ValueError.

        Проверяем: отрицательный alpha отклоняется.
        Границы: alpha < 0.
        Почему такие: граничный случай — отрицательный alpha.
        """
        from space1.metrics.tracker import MetricTracker
        try:
            MetricTracker(-0.1)
            assert False, "Должен был упасть с ValueError"
        except ValueError:
            pass

    def test_tracker_init_alpha_above_one_raises(self):
        """
        MetricTracker(1.1) → ValueError.

        Проверяем: alpha > 1 отклоняется.
        Границы: alpha = 1.1.
        Почему такие: граничный случай — alpha > 1.
        """
        from space1.metrics.tracker import MetricTracker
        try:
            MetricTracker(1.1)
            assert False, "Должен был упасть с ValueError"
        except ValueError:
            pass

    def test_tracker_init_alpha_one_ok(self):
        """
        MetricTracker(1.0) → OK.

        Проверяем: alpha=1 допустим (граница включена).
        Границы: alpha = 1.0.
        Почему такие: граничный случай — верхняя граница включена.
        """
        from space1.metrics.tracker import MetricTracker
        tracker = MetricTracker(1.0)
        assert tracker._default_alpha == 1.0

    def test_tracker_update_first_value(self):
        """
        update("m", 0.5) → 0.5 (первое значение, EMA не применяется).

        Проверяем: первое значение устанавливается как есть.
        Границы: Первое обновление.
        Почему такие: контракт — первое значение = raw value.
        """
        from space1.metrics.tracker import MetricTracker
        tracker = MetricTracker()
        result = tracker.update("m", 0.5)
        assert result == 0.5

    def test_tracker_update_ema_formula(self):
        """
        update("m", 0.5) → 0.5, update("m", 0.7, alpha=0.5) → 0.5 + 0.5*(0.7-0.5) = 0.6.

        Проверяем: EMA формула S_{t+1} = S_t + α·(R_t - S_t).
        Границы: Второе обновление с alpha=0.5.
        Почему такие: проверка математической формулы.
        """
        from space1.metrics.tracker import MetricTracker
        tracker = MetricTracker()
        tracker.update("m", 0.5)
        result = tracker.update("m", 0.7, alpha=0.5)
        expected = 0.5 + 0.5 * (0.7 - 0.5)
        assert abs(result - expected) < 1e-9

    def test_tracker_update_ema_converges(self):
        """
        Многократное обновление к 1.0 с alpha=0.2 → значение стремится к 1.0.

        Проверяем: EMA сходится к стационарному значению.
        Границы: 10 обновлений.
        Почему такие: проверка сходимости EMA.
        """
        from space1.metrics.tracker import MetricTracker
        tracker = MetricTracker()
        tracker.update("m", 0.0)
        for _ in range(20):
            tracker.update("m", 1.0)
        # EMA сходится к 1.0, но не достигает его полностью
        assert tracker.get("m") > 0.9
        assert tracker.get("m") <= 1.0

    def test_tracker_update_uses_default_alpha(self):
        """
        update без alpha → использует default_alpha.

        Проверяем: fallback на default.
        Границы: alpha = None.
        Почему такие: проверка default behavior.
        """
        from space1.metrics.tracker import MetricTracker
        tracker = MetricTracker(0.5)
        tracker.update("m", 0.0)
        result = tracker.update("m", 1.0)
        expected = 0.0 + 0.5 * (1.0 - 0.0)
        assert abs(result - expected) < 1e-9

    def test_tracker_get_existing(self):
        """
        get("m") после update → текущее EMA значение.

        Проверяем: получение значения.
        Границы: Существующая метрика.
        Почему такие: базовая функциональность get.
        """
        from space1.metrics.tracker import MetricTracker
        tracker = MetricTracker()
        tracker.update("m", 0.5)
        assert tracker.get("m") == 0.5

    def test_tracker_get_missing(self):
        """
        get("missing") → None.

        Проверяем: отсутствующая метрика.
        Границы: Несуществующая метрика.
        Почему такие: граничный случай — нет метрики.
        """
        from space1.metrics.tracker import MetricTracker
        tracker = MetricTracker()
        assert tracker.get("missing") is None

    def test_tracker_get_missing_with_default(self):
        """
        get("missing", default=0.0) → 0.0.

        Проверяем: default для отсутствующей метрики.
        Границы: Несуществующая метрика + default.
        Почему такие: проверка default parameter.
        """
        from space1.metrics.tracker import MetricTracker
        tracker = MetricTracker()
        assert tracker.get("missing", 0.0) == 0.0

    def test_tracker_get_raw_single(self):
        """
        get_raw("m", n=1) → последнее raw значение.

        Проверяем: получение одного raw значения.
        Границы: n = 1.
        Почему такие: проверка get_raw.
        """
        from space1.metrics.tracker import MetricTracker
        tracker = MetricTracker()
        tracker.update("m", 0.5)
        tracker.update("m", 0.7)
        assert tracker.get_raw("m", 1) == 0.7

    def test_tracker_get_raw_multiple(self):
        """
        get_raw("m", n=2) → список из 2 последних raw значений.

        Проверяем: получение нескольких raw значений.
        Границы: n = 2.
        Почему такие: проверка get_raw с n > 1.
        """
        from space1.metrics.tracker import MetricTracker
        tracker = MetricTracker()
        tracker.update("m", 0.1)
        tracker.update("m", 0.2)
        tracker.update("m", 0.3)
        raw = tracker.get_raw("m", 2)
        assert raw == [0.2, 0.3]

    def test_tracker_get_raw_missing(self):
        """
        get_raw("missing") → None.

        Проверяем: отсутствующая метрика.
        Границы: Несуществующая метрика.
        Почему такие: граничный случай.
        """
        from space1.metrics.tracker import MetricTracker
        tracker = MetricTracker()
        assert tracker.get_raw("missing") is None

    def test_tracker_get_history(self):
        """
        get_history("m") → список MetricRecord.

        Проверяем: получение истории.
        Границы: 2 обновления.
        Почему такие: проверка get_history.
        """
        from space1.metrics.tracker import MetricTracker
        tracker = MetricTracker()
        tracker.update("m", 0.5)
        tracker.update("m", 0.7)
        history = tracker.get_history("m")
        assert len(history) == 2
        assert history[0].raw_value == 0.5
        assert history[1].raw_value == 0.7

    def test_tracker_get_history_n(self):
        """
        get_history("m", n=1) → последняя запись.

        Проверяем: ограничение истории.
        Границы: n = 1.
        Почему такие: проверка параметра n.
        """
        from space1.metrics.tracker import MetricTracker
        tracker = MetricTracker()
        tracker.update("m", 0.5)
        tracker.update("m", 0.7)
        history = tracker.get_history("m", 1)
        assert len(history) == 1
        assert history[0].raw_value == 0.7

    def test_tracker_get_history_missing(self):
        """
        get_history("missing") → [].

        Проверяем: отсутствующая метрика.
        Границы: Несуществующая метрика.
        Почему такие: граничный случай.
        """
        from space1.metrics.tracker import MetricTracker
        tracker = MetricTracker()
        assert tracker.get_history("missing") == []

    def test_tracker_get_all(self):
        """
        get_all() → dict всех метрик.

        Проверяем: получение всех значений.
        Границы: 2 метрики.
        Почему такие: проверка get_all.
        """
        from space1.metrics.tracker import MetricTracker
        tracker = MetricTracker()
        tracker.update("m1", 0.5)
        tracker.update("m2", 0.7)
        all_metrics = tracker.get_all()
        assert all_metrics["m1"] == 0.5
        assert all_metrics["m2"] == 0.7
        assert len(all_metrics) == 2

    def test_tracker_get_all_returns_copy(self):
        """
        get_all() возвращает копию, не оригинал.

        Проверяем: иммутабельность возвращаемого dict.
        Границы: Стандартный кейс.
        Почему такие: проверка .copy().
        """
        from space1.metrics.tracker import MetricTracker
        tracker = MetricTracker()
        tracker.update("m", 0.5)
        all_metrics = tracker.get_all()
        all_metrics["m"] = 999
        assert tracker.get("m") == 0.5

    def test_tracker_reset_single(self):
        """
        reset("m") → метрика удалена.

        Проверяем: удаление одной метрики.
        Границы: Одна метрика.
        Почему такие: проверка reset.
        """
        from space1.metrics.tracker import MetricTracker
        tracker = MetricTracker()
        tracker.update("m1", 0.5)
        tracker.update("m2", 0.7)
        tracker.reset("m1")
        assert tracker.get("m1") is None
        assert tracker.get("m2") == 0.7

    def test_tracker_reset_all(self):
        """
        reset() → все метрики удалены.

        Проверяем: удаление всех метрик.
        Границы: Все метрики.
        Почему такие: проверка reset без аргументов.
        """
        from space1.metrics.tracker import MetricTracker
        tracker = MetricTracker()
        tracker.update("m1", 0.5)
        tracker.update("m2", 0.7)
        tracker.reset()
        assert tracker.get("m1") is None
        assert tracker.get("m2") is None
        assert tracker.get_all() == {}

    def test_tracker_get_stats(self):
        """
        get_stats("m") → current, mean, min, max, count.

        Проверяем: статистика метрики.
        Границы: 3 обновления.
        Почему такие: проверка get_stats.
        """
        from space1.metrics.tracker import MetricTracker
        tracker = MetricTracker()
        tracker.update("m", 0.1)
        tracker.update("m", 0.2)
        tracker.update("m", 0.3)
        stats = tracker.get_stats("m")
        assert "current" in stats
        assert "mean" in stats
        assert "min" in stats
        assert "max" in stats
        assert "count" in stats
        assert abs(stats["mean"] - 0.2) < 1e-9
        assert stats["min"] == 0.1
        assert stats["max"] == 0.3
        assert stats["count"] == 3

    def test_tracker_get_stats_missing(self):
        """
        get_stats("missing") → {}.

        Проверяем: отсутствующая метрика.
        Границы: Несуществующая метрика.
        Почему такие: граничный случай.
        """
        from space1.metrics.tracker import MetricTracker
        tracker = MetricTracker()
        assert tracker.get_stats("missing") == {}

    def test_tracker_history_limit_1000(self):
        """
        1001 обновление → история содержит последние 1000.

        Проверяем: ограничение истории 1000 записями.
        Границы: 1001 обновление.
        Почему такие: проверка лимита истории.
        """
        from space1.metrics.tracker import MetricTracker
        tracker = MetricTracker()
        for i in range(1001):
            tracker.update("m", float(i))
        history = tracker.get_history("m")
        assert len(history) == 1000
        assert history[0].raw_value == 1.0  # Первое (0) вытеснено
        assert history[-1].raw_value == 1000.0


# =============================================================================
# UNIT: MetricsEngine
# =============================================================================

class TestMetricsEngineUnit:
    """Unit-тесты на MetricsEngine."""

    def test_engine_init(self):
        """
        MetricsEngine() → tracker с default_alpha=0.2.

        Проверяем: инициализация engine.
        Границы: Без аргументов.
        Почему такие: базовая функциональность.
        """
        from space1.metrics.tracker import MetricsEngine
        engine = MetricsEngine()
        assert engine.tracker._default_alpha == 0.2

    def test_engine_track(self):
        """
        engine.track("m", 0.5) → 0.5.

        Проверяем: shortcut для tracker.update.
        Границы: Стандартный кейс.
        Почему такие: проверка proxy track.
        """
        from space1.metrics.tracker import MetricsEngine
        engine = MetricsEngine()
        result = engine.track("m", 0.5)
        assert result == 0.5

    def test_engine_get(self):
        """
        engine.get("m") после track → значение.

        Проверяем: shortcut для tracker.get.
        Границы: Существующая метрика.
        Почему такие: проверка proxy get.
        """
        from space1.metrics.tracker import MetricsEngine
        engine = MetricsEngine()
        engine.track("m", 0.5)
        assert engine.get("m") == 0.5

    def test_engine_compute_phi_stub(self):
        """
        compute_phi(task, agent) → 0.0 (stub).

        Проверяем: заглушка compute_phi.
        Границы: Любые аргументы.
        Почему такие: проверка stub.
        """
        from space1.metrics.tracker import MetricsEngine
        engine = MetricsEngine()
        assert engine.compute_phi(None, None) == 0.0

    def test_engine_compute_psi_stub(self):
        """
        compute_psi(task) → 0.0 (stub).

        Проверяем: заглушка compute_psi.
        Границы: Любые аргументы.
        Почему такие: проверка stub.
        """
        from space1.metrics.tracker import MetricsEngine
        engine = MetricsEngine()
        assert engine.compute_psi(None) == 0.0


# =============================================================================
# UNIT: MetricRegistry
# =============================================================================

class TestMetricRegistryUnit:
    """Unit-тесты на MetricRegistry."""

    def test_registry_categories(self):
        """
        MetricRegistry.CATEGORIES содержит 5 категорий.

        Проверяем: наличие категорий.
        Границы: Стандартный кейс.
        Почему такие: контракт G14.
        """
        from space1.metrics.tracker import MetricRegistry
        assert len(MetricRegistry.CATEGORIES) == 5
        assert "financial" in MetricRegistry.CATEGORIES
        assert "reputation" in MetricRegistry.CATEGORIES
        assert "operational" in MetricRegistry.CATEGORIES
        assert "cost" in MetricRegistry.CATEGORIES
        assert "homeostatic" in MetricRegistry.CATEGORIES

    def test_registry_track(self):
        """
        registry.track("m", 0.5) → 0.5.

        Проверяем: базовое отслеживание.
        Границы: Стандартный кейс.
        Почему такие: базовая функциональность.
        """
        from space1.metrics.tracker import MetricRegistry
        registry = MetricRegistry()
        result = registry.track("m", 0.5)
        assert result == 0.5

    def test_registry_get_existing(self):
        """
        registry.get("m") после track → значение.

        Проверяем: получение значения.
        Границы: Существующая метрика.
        Почему такие: проверка get.
        """
        from space1.metrics.tracker import MetricRegistry
        registry = MetricRegistry()
        registry.track("m", 0.5)
        assert registry.get("m") == 0.5

    def test_registry_get_missing_returns_zero(self):
        """
        registry.get("missing") → 0.0 (default=0.0).

        Проверяем: default для отсутствующей метрики.
        Границы: Несуществующая метрика.
        Почему такие: граничный случай — default=0.0.
        """
        from space1.metrics.tracker import MetricRegistry
        registry = MetricRegistry()
        assert registry.get("missing") == 0.0

    def test_registry_get_creates_metric(self):
        """
        registry.get("new") → 0.0, метрика появляется в get_all().

        Проверяем: get создаёт метрику.
        Границы: Несуществующая метрика.
        Почему такие: проверка side-effect get — auto-creation.
        """
        from space1.metrics.tracker import MetricRegistry
        registry = MetricRegistry()
        registry.get("new")
        assert "new" in registry.get_all()

    def test_registry_update_alias(self):
        """
        registry.update("m", 0.5) → 0.5 (alias для track).

        Проверяем: update — alias track.
        Границы: Стандартный кейс.
        Почему такие: проверка alias.
        """
        from space1.metrics.tracker import MetricRegistry
        registry = MetricRegistry()
        result = registry.update("m", 0.5)
        assert result == 0.5
        assert registry.get("m") == 0.5

    def test_registry_track_with_category(self):
        """
        registry.track("m", 0.5, category="custom") → метрика в категории.

        Проверяем: создание категории.
        Границы: Новая категория.
        Почему такие: проверка category parameter.
        """
        from space1.metrics.tracker import MetricRegistry
        registry = MetricRegistry()
        registry.track("m", 0.5, category="custom")
        assert "m" in registry._categories["custom"]

    def test_registry_get_by_category(self):
        """
        get_by_category("financial") → dict с метриками категории.

        Проверяем: получение по категории.
        Границы: Стандартная категория.
        Почему такие: проверка get_by_category.
        """
        from space1.metrics.tracker import MetricRegistry
        registry = MetricRegistry()
        registry.track("balance", 100.0)
        financial = registry.get_by_category("financial")
        assert "balance" in financial
        assert financial["balance"] == 100.0

    def test_registry_get_by_category_missing_metric(self):
        """
        get_by_category("financial") для missing metric → 0.0.

        Проверяем: fallback для отсутствующей метрики в категории.
        Границы: Категория определена, метрика не tracked.
        Почему такие: проверка fallback.
        """
        from space1.metrics.tracker import MetricRegistry
        registry = MetricRegistry()
        financial = registry.get_by_category("financial")
        assert financial["total_earned"] == 0.0

    def test_registry_get_categories(self):
        """
        get_categories() → список категорий.

        Проверяем: получение списка категорий.
        Границы: Стандартный кейс.
        Почему такие: проверка get_categories.
        """
        from space1.metrics.tracker import MetricRegistry
        registry = MetricRegistry()
        cats = registry.get_categories()
        assert "financial" in cats
        assert "reputation" in cats
        assert len(cats) == 5

    def test_registry_get_history(self):
        """
        get_history("m") → история из tracker.

        Проверяем: proxy get_history.
        Границы: 2 обновления.
        Почему такие: проверка proxy.
        """
        from space1.metrics.tracker import MetricRegistry
        registry = MetricRegistry()
        registry.track("m", 0.5)
        registry.track("m", 0.7)
        history = registry.get_history("m")
        assert len(history) == 2

    def test_registry_get_stats(self):
        """
        get_stats("m") → статистика из tracker.

        Проверяем: proxy get_stats.
        Границы: 2 обновления.
        Почему такие: проверка proxy.
        """
        from space1.metrics.tracker import MetricRegistry
        registry = MetricRegistry()
        registry.track("m", 0.5)
        registry.track("m", 0.7)
        stats = registry.get_stats("m")
        assert stats["count"] == 2

    def test_registry_reset(self):
        """
        reset("m") → метрика удалена.

        Проверяем: proxy reset.
        Границы: Одна метрика.
        Почему такие: проверка proxy reset.
        """
        from space1.metrics.tracker import MetricRegistry
        registry = MetricRegistry()
        registry.track("m", 0.5)
        registry.reset("m")
        assert registry.get("m") == 0.0  # get создаёт заново

    def test_registry_to_dict(self):
        """
        to_dict() → {"metrics": {...}, "categories": {...}}.

        Проверяем: сериализация.
        Границы: Стандартный кейс.
        Почему такие: проверка to_dict.
        """
        from space1.metrics.tracker import MetricRegistry
        registry = MetricRegistry()
        registry.track("m", 0.5)
        d = registry.to_dict()
        assert "metrics" in d
        assert "categories" in d
        assert d["metrics"]["m"] == 0.5


# =============================================================================
# PAIR: MetricTracker + MetricRecord
# =============================================================================

class TestPairTrackerRecord:
    """PAIR: MetricTracker + MetricRecord — интеграция в миниатюре."""

    def test_tracker_history_contains_records(self):
        """
        update → get_history возвращает MetricRecord.

        Проверяем: история содержит правильный тип.
        Границы: Одно обновление.
        Почему такие: интеграция tracker → record.
        """
        from space1.metrics.tracker import MetricTracker, MetricRecord
        tracker = MetricTracker()
        tracker.update("m", 0.5)
        history = tracker.get_history("m")
        assert len(history) == 1
        assert isinstance(history[0], MetricRecord)
        assert history[0].raw_value == 0.5

    def test_tracker_record_has_timestamp(self):
        """
        MetricRecord в истории имеет timestamp.

        Проверяем: timestamp записывается.
        Границы: Одно обновление.
        Почему такие: интеграция — проверка полноты записи.
        """
        from space1.metrics.tracker import MetricTracker
        tracker = MetricTracker()
        tracker.update("m", 0.5)
        history = tracker.get_history("m")
        assert history[0].timestamp > 0

    def test_tracker_record_has_alpha(self):
        """
        MetricRecord в истории имеет alpha.

        Проверяем: alpha записывается.
        Границы: Одно обновление.
        Почему такие: интеграция — проверка полноты записи.
        """
        from space1.metrics.tracker import MetricTracker
        tracker = MetricTracker(0.3)
        tracker.update("m", 0.5)
        history = tracker.get_history("m")
        assert history[0].alpha == 0.3


# =============================================================================
# PAIR: MetricsEngine + MetricTracker
# =============================================================================

class TestPairEngineTracker:
    """PAIR: MetricsEngine + MetricTracker — интеграция в миниатюре."""

    def test_engine_uses_tracker(self):
        """
        engine.track → tracker.update.

        Проверяем: engine делегирует tracker.
        Границы: Стандартный кейс.
        Почему такие: интеграция engine → tracker.
        """
        from space1.metrics.tracker import MetricsEngine
        engine = MetricsEngine()
        engine.track("m", 0.5)
        assert engine.tracker.get("m") == 0.5

    def test_engine_alpha_passed_to_tracker(self):
        """
        MetricsEngine(0.5) → tracker с alpha=0.5.

        Проверяем: проксирование alpha.
        Границы: alpha = 0.5.
        Почему такие: интеграция — конфигурация.
        """
        from space1.metrics.tracker import MetricsEngine
        engine = MetricsEngine(0.5)
        assert engine.tracker._default_alpha == 0.5


# =============================================================================
# PAIR: MetricRegistry + MetricTracker
# =============================================================================

class TestPairRegistryTracker:
    """PAIR: MetricRegistry + MetricTracker — интеграция в миниатюре."""

    def test_registry_delegates_to_tracker(self):
        """
        registry.track → tracker.update.

        Проверяем: registry делегирует tracker.
        Границы: Стандартный кейс.
        Почему такие: интеграция registry → tracker.
        """
        from space1.metrics.tracker import MetricRegistry
        registry = MetricRegistry()
        registry.track("m", 0.5)
        assert registry._tracker.get("m") == 0.5

    def test_registry_get_all_delegates(self):
        """
        registry.get_all → tracker.get_all.

        Проверяем: proxy get_all.
        Границы: Стандартный кейс.
        Почему такие: интеграция — проксирование.
        """
        from space1.metrics.tracker import MetricRegistry
        registry = MetricRegistry()
        registry.track("m", 0.5)
        assert registry.get_all() == registry._tracker.get_all()


# =============================================================================
# INTEGRITY: Архитектурные инварианты
# =============================================================================

class TestIntegrityMetrics:
    """INTEGRITY: Архитектурные инварианты metrics/tracker.py."""

    def test_no_bare_except_in_metrics(self):
        """
        metrics/tracker.py не содержит bare except Exception: pass.

        Проверяем: отсутствие bare except (10_SECURITY.md §III — fail fast).
        Границы: Проверка всего файла.
        Почему такие: bare except маскирует ошибки.
        """
        import inspect
        from space1.metrics import tracker
        src_file = inspect.getfile(tracker)
        with open(src_file, 'r') as f:
            lines = f.readlines()
        bare_excepts = [i + 1 for i, line in enumerate(lines) if "except Exception" in line]
        assert len(bare_excepts) == 0, f"Bare except найден на строках: {bare_excepts}"

    def test_ema_formula_invariant(self):
        """
        EMA: S_{t+1} = S_t + α·(R_t - S_t) — формула соблюдается.

        Проверяем: математический инвариант.
        Границы: alpha=0.5, S_t=0.4, R_t=0.8.
        Почему такие: архитектурный инвариант — формула EMA.
        """
        from space1.metrics.tracker import MetricTracker
        tracker = MetricTracker()
        tracker.update("m", 0.4)
        result = tracker.update("m", 0.8, alpha=0.5)
        expected = 0.4 + 0.5 * (0.8 - 0.4)
        assert abs(result - expected) < 1e-9

    def test_alpha_range_invariant(self):
        """
        alpha ∈ (0, 1] — диапазон соблюдается при валидации.

        Проверяем: границы alpha.
        Границы: 0, 1, 1.1, -0.1.
        Почему такие: архитектурный инвариант — alpha в (0, 1].
        """
        from space1.metrics.tracker import MetricTracker
        # Граничные случаи
        MetricTracker(1.0)  # OK
        try:
            MetricTracker(0.0)
            assert False
        except ValueError:
            pass
        try:
            MetricTracker(1.1)
            assert False
        except ValueError:
            pass
        try:
            MetricTracker(-0.1)
            assert False
        except ValueError:
            pass

    def test_history_limit_invariant(self):
        """
        История ограничена 1000 записями.

        Проверяем: лимит истории.
        Границы: 1001 запись.
        Почему такие: архитектурный инвариант — memory bound.
        """
        from space1.metrics.tracker import MetricTracker
        tracker = MetricTracker()
        for i in range(1001):
            tracker.update("m", float(i))
        assert len(tracker.get_history("m")) == 1000

    def test_metric_registry_categories_complete(self):
        """
        MetricRegistry.CATEGORIES содержит все 5 категорий.

        Проверяем: полнота категорий.
        Границы: Стандартный кейс.
        Почему такие: архитектурный инвариант — G14.
        """
        from space1.metrics.tracker import MetricRegistry
        expected = {"financial", "reputation", "operational", "cost", "homeostatic"}
        assert set(MetricRegistry.CATEGORIES.keys()) == expected


# =============================================================================
# REGRESSION: Старые баги не вернулись
# =============================================================================

class TestRegressionMetrics:
    """REGRESSION: Проверки, что исправленные баги не вернулись."""

    def test_reset_does_not_leave_ghost_metrics(self):
        """
        reset("m") → get("m") возвращает None (в MetricTracker).

        Проверяем: полное удаление.
        Границы: Одна метрика.
        Почему такие: регрессия — ранее мог остаться ghost metric.
        """
        from space1.metrics.tracker import MetricTracker
        tracker = MetricTracker()
        tracker.update("m", 0.5)
        tracker.reset("m")
        assert tracker.get("m") is None

    def test_get_all_returns_copy_not_reference(self):
        """
        get_all() → изменение возвращаемого dict не влияет на tracker.

        Проверяем: иммутабельность.
        Границы: Стандартный кейс.
        Почему такие: регрессия — ранее мог вернуть reference.
        """
        from space1.metrics.tracker import MetricTracker
        tracker = MetricTracker()
        tracker.update("m", 0.5)
        all_m = tracker.get_all()
        all_m["m"] = 999.0
        assert tracker.get("m") == 0.5

    def test_registry_get_creates_metric_with_default(self):
        """
        registry.get("new") для missing → создаёт с default=0.0, не падает.

        Проверяем: graceful handling missing.
        Границы: Несуществующая метрика.
        Почему такие: регрессия — ранее мог упасть.
        """
        from space1.metrics.tracker import MetricRegistry
        registry = MetricRegistry()
        result = registry.get("totally_new_metric")
        assert result == 0.0
        assert "totally_new_metric" in registry.get_all()
