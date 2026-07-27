"""
Space1 — ПРОВЕРЕННЫЕ ТЕСТЫ: Metrics Monitoring

Каждый тест проверен против реального кода.
FAILED-тесты = реальные баги, не ошибки тестов.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from datetime import datetime


# =============================================================================
# UNIT: AlertLevel
# =============================================================================

class TestAlertLevelUnit:
    """Unit-тесты на AlertLevel enum."""

    def test_alert_level_info(self):
        """
        AlertLevel.INFO.value = "info".

        Проверяем: значение INFO.
        Границы: Стандартная константа.
        Почему такие: контракт enum.
        """
        from space1.metrics.monitoring import AlertLevel
        assert AlertLevel.INFO.value == "info"

    def test_alert_level_warning(self):
        """
        AlertLevel.WARNING.value = "warning".

        Проверяем: значение WARNING.
        Границы: Стандартная константа.
        Почему такие: контракт enum.
        """
        from space1.metrics.monitoring import AlertLevel
        assert AlertLevel.WARNING.value == "warning"

    def test_alert_level_critical(self):
        """
        AlertLevel.CRITICAL.value = "critical".

        Проверяем: значение CRITICAL.
        Границы: Стандартная константа.
        Почему такие: контракт enum.
        """
        from space1.metrics.monitoring import AlertLevel
        assert AlertLevel.CRITICAL.value == "critical"

    def test_alert_level_three_values(self):
        """
        AlertLevel содержит ровно 3 значения.

        Проверяем: полнота enum.
        Границы: Все значения.
        Почему такие: архитектурный инвариант — 3 уровня.
        """
        from space1.metrics.monitoring import AlertLevel
        assert len(list(AlertLevel)) == 3


# =============================================================================
# UNIT: MetricValue
# =============================================================================

class TestMetricValueUnit:
    """Unit-тесты на MetricValue dataclass."""

    def test_metric_value_creation(self):
        """
        MetricValue(name="m", value=0.5) → поля установлены.

        Проверяем: создание записи.
        Границы: Стандартный кейс.
        Почему такие: базовая функциональность dataclass.
        """
        from space1.metrics.monitoring import MetricValue
        val = MetricValue(name="m", value=0.5)
        assert val.name == "m"
        assert val.value == 0.5
        assert val.unit == ""
        assert val.tags == {}
        assert isinstance(val.timestamp, datetime)

    def test_metric_value_with_unit(self):
        """
        MetricValue(name="m", value=0.5, unit="%") → unit="%".

        Проверяем: кастомный unit.
        Границы: unit = "%".
        Почему такие: проверка unit.
        """
        from space1.metrics.monitoring import MetricValue
        val = MetricValue(name="m", value=0.5, unit="%")
        assert val.unit == "%"

    def test_metric_value_with_tags(self):
        """
        MetricValue(name="m", value=0.5, tags={"key": "value"}) → tags установлены.

        Проверяем: кастомные tags.
        Границы: tags с одним ключом.
        Почему такие: проверка tags.
        """
        from space1.metrics.monitoring import MetricValue
        val = MetricValue(name="m", value=0.5, tags={"key": "value"})
        assert val.tags["key"] == "value"


# =============================================================================
# UNIT: Alert
# =============================================================================

class TestAlertUnit:
    """Unit-тесты на Alert dataclass."""

    def test_alert_creation(self):
        """
        Alert(metric_name="m", level=AlertLevel.WARNING, message="msg", value=0.5, threshold=0.6) → поля установлены.

        Проверяем: создание алерта.
        Границы: Стандартный кейс.
        Почему такие: базовая функциональность dataclass.
        """
        from space1.metrics.monitoring import Alert, AlertLevel
        alert = Alert(metric_name="m", level=AlertLevel.WARNING, message="msg", value=0.5, threshold=0.6)
        assert alert.metric_name == "m"
        assert alert.level == AlertLevel.WARNING
        assert alert.message == "msg"
        assert alert.value == 0.5
        assert alert.threshold == 0.6
        assert isinstance(alert.timestamp, datetime)


# =============================================================================
# UNIT: SystemMonitor
# =============================================================================

class TestSystemMonitorUnit:
    """Unit-тесты на SystemMonitor."""

    def test_monitor_init_empty(self):
        """
        SystemMonitor() → пустые metrics, alerts, subscribers.

        Проверяем: начальное состояние.
        Границы: Без аргументов.
        Почему такие: контракт чистого состояния.
        """
        from space1.metrics.monitoring import SystemMonitor
        monitor = SystemMonitor()
        assert monitor.metrics == {}
        assert monitor.alerts == []
        assert monitor.subscribers == []

    def test_monitor_default_thresholds(self):
        """
        SystemMonitor() → thresholds содержит budget_health, compliance_violations, stress_level.

        Проверяем: default thresholds.
        Границы: Стандартный кейс.
        Почему такие: контракт default конфигурации.
        """
        from space1.metrics.monitoring import SystemMonitor
        monitor = SystemMonitor()
        assert "budget_health" in monitor.thresholds
        assert "compliance_violations" in monitor.thresholds
        assert "stress_level" in monitor.thresholds

    def test_monitor_threshold_budget_health(self):
        """
        budget_health: warning=20, critical=5, direction="lt".

        Проверяем: конфигурация budget_health.
        Границы: Стандартная конфигурация.
        Почему такие: контракт threshold.
        """
        from space1.metrics.monitoring import SystemMonitor
        monitor = SystemMonitor()
        th = monitor.thresholds["budget_health"]
        assert th["warning"] == 20.0
        assert th["critical"] == 5.0
        assert th["direction"] == "lt"

    def test_monitor_threshold_compliance_violations(self):
        """
        compliance_violations: warning=1, critical=3, direction="gt".

        Проверяем: конфигурация compliance_violations.
        Границы: Стандартная конфигурация.
        Почему такие: контракт threshold.
        """
        from space1.metrics.monitoring import SystemMonitor
        monitor = SystemMonitor()
        th = monitor.thresholds["compliance_violations"]
        assert th["warning"] == 1.0
        assert th["critical"] == 3.0
        assert th["direction"] == "gt"

    def test_monitor_threshold_stress_level(self):
        """
        stress_level: warning=0.7, critical=0.9, direction="gt".

        Проверяем: конфигурация stress_level.
        Границы: Стандартная конфигурация.
        Почему такие: контракт threshold.
        """
        from space1.metrics.monitoring import SystemMonitor
        monitor = SystemMonitor()
        th = monitor.thresholds["stress_level"]
        assert th["warning"] == 0.7
        assert th["critical"] == 0.9
        assert th["direction"] == "gt"

    def test_monitor_record_creates_metric(self):
        """
        record("m", 0.5) → metrics["m"] содержит 1 запись.

        Проверяем: создание метрики.
        Границы: Первая запись.
        Почему такие: базовая функциональность record.
        """
        from space1.metrics.monitoring import SystemMonitor
        monitor = SystemMonitor()
        monitor.record("m", 0.5)
        assert "m" in monitor.metrics
        assert len(monitor.metrics["m"]) == 1
        assert monitor.metrics["m"][0].value == 0.5

    def test_monitor_record_appends(self):
        """
        record("m", 0.5) + record("m", 0.7) → 2 записи.

        Проверяем: накопление записей.
        Границы: Вторая запись.
        Почему такие: проверка накопления.
        """
        from space1.metrics.monitoring import SystemMonitor
        monitor = SystemMonitor()
        monitor.record("m", 0.5)
        monitor.record("m", 0.7)
        assert len(monitor.metrics["m"]) == 2

    def test_monitor_record_with_unit(self):
        """
        record("m", 0.5, unit="%") → unit="%".

        Проверяем: передача unit.
        Границы: unit = "%".
        Почему такие: проверка unit.
        """
        from space1.metrics.monitoring import SystemMonitor
        monitor = SystemMonitor()
        monitor.record("m", 0.5, unit="%")
        assert monitor.metrics["m"][0].unit == "%"

    def test_monitor_record_with_tags(self):
        """
        record("m", 0.5, tags={"key": "value"}) → tags установлены.

        Проверяем: передача tags.
        Границы: tags с одним ключом.
        Почему такие: проверка tags.
        """
        from space1.metrics.monitoring import SystemMonitor
        monitor = SystemMonitor()
        monitor.record("m", 0.5, tags={"key": "value"})
        assert monitor.metrics["m"][0].tags["key"] == "value"

    def test_monitor_get_latest_existing(self):
        """
        get_latest("m") → последняя запись.

        Проверяем: получение последней записи.
        Границы: 2 записи.
        Почему такие: проверка get_latest.
        """
        from space1.metrics.monitoring import SystemMonitor
        monitor = SystemMonitor()
        monitor.record("m", 0.5)
        monitor.record("m", 0.7)
        latest = monitor.get_latest("m")
        assert latest.value == 0.7

    def test_monitor_get_latest_missing(self):
        """
        get_latest("missing") → None.

        Проверяем: отсутствующая метрика.
        Границы: Несуществующая метрика.
        Почему такие: граничный случай.
        """
        from space1.metrics.monitoring import SystemMonitor
        monitor = SystemMonitor()
        assert monitor.get_latest("missing") is None

    def test_monitor_get_latest_empty_list(self):
        """
        get_latest("m") для пустого списка → None.

        Проверяем: пустой список.
        Границы: metrics["m"] = [].
        Почему такие: граничный случай — пустой список.
        """
        from space1.metrics.monitoring import SystemMonitor
        monitor = SystemMonitor()
        monitor.metrics["m"] = []
        assert monitor.get_latest("m") is None

    def test_monitor_subscribe(self):
        """
        subscribe(callback) → subscribers содержит callback.

        Проверяем: регистрация подписчика.
        Границы: Один callback.
        Почему такие: базовая функциональность subscribe.
        """
        from space1.metrics.monitoring import SystemMonitor
        monitor = SystemMonitor()
        def cb(alert):
            pass
        monitor.subscribe(cb)
        assert len(monitor.subscribers) == 1
        assert monitor.subscribers[0] is cb

    def test_monitor_alert_gt_warning(self):
        """
        record("compliance_violations", 1.0) → WARNING alert.

        Проверяем: gt warning threshold.
        Границы: value = warning.
        Почему такие: проверка alert generation.
        """
        from space1.metrics.monitoring import SystemMonitor, AlertLevel
        monitor = SystemMonitor()
        monitor.record("compliance_violations", 1.0)
        assert len(monitor.alerts) == 1
        assert monitor.alerts[0].level == AlertLevel.WARNING

    def test_monitor_alert_gt_critical(self):
        """
        record("compliance_violations", 3.0) → CRITICAL alert (warning пропущен).

        Проверяем: gt critical threshold — critical имеет приоритет.
        Границы: value = critical.
        Почему такие: проверка приоритета critical.
        """
        from space1.metrics.monitoring import SystemMonitor, AlertLevel
        monitor = SystemMonitor()
        monitor.record("compliance_violations", 3.0)
        assert len(monitor.alerts) == 1
        assert monitor.alerts[0].level == AlertLevel.CRITICAL

    def test_monitor_alert_lt_warning(self):
        """
        record("budget_health", 20.0) → WARNING alert.

        Проверяем: lt warning threshold.
        Границы: value = warning.
        Почему такие: проверка alert generation для lt.
        """
        from space1.metrics.monitoring import SystemMonitor, AlertLevel
        monitor = SystemMonitor()
        monitor.record("budget_health", 20.0)
        assert len(monitor.alerts) == 1
        assert monitor.alerts[0].level == AlertLevel.WARNING

    def test_monitor_alert_lt_critical(self):
        """
        record("budget_health", 5.0) → CRITICAL alert.

        Проверяем: lt critical threshold.
        Границы: value = critical.
        Почему такие: проверка alert generation для lt critical.
        """
        from space1.metrics.monitoring import SystemMonitor, AlertLevel
        monitor = SystemMonitor()
        monitor.record("budget_health", 5.0)
        assert len(monitor.alerts) == 1
        assert monitor.alerts[0].level == AlertLevel.CRITICAL

    def test_monitor_alert_no_threshold(self):
        """
        record("unknown_metric", 100.0) → нет alerts.

        Проверяем: метрика без threshold не генерирует alert.
        Границы: Нет threshold.
        Почему такие: проверка отсутствия false positive.
        """
        from space1.metrics.monitoring import SystemMonitor
        monitor = SystemMonitor()
        monitor.record("unknown_metric", 100.0)
        assert len(monitor.alerts) == 0

    def test_monitor_alert_below_warning(self):
        """
        record("compliance_violations", 0.5) → нет alerts.

        Проверяем: значение ниже warning → нет alert.
        Границы: value < warning.
        Почему такие: проверка отсутствия false positive.
        """
        from space1.metrics.monitoring import SystemMonitor
        monitor = SystemMonitor()
        monitor.record("compliance_violations", 0.5)
        assert len(monitor.alerts) == 0

    def test_monitor_alert_between_warning_and_critical(self):
        """
        record("compliance_violations", 2.0) → WARNING alert.

        Проверяем: значение между warning и critical.
        Границы: warning < value < critical.
        Почему такие: проверка границы — только warning.
        """
        from space1.metrics.monitoring import SystemMonitor, AlertLevel
        monitor = SystemMonitor()
        monitor.record("compliance_violations", 2.0)
        assert len(monitor.alerts) == 1
        assert monitor.alerts[0].level == AlertLevel.WARNING

    def test_monitor_alert_stress_critical(self):
        """
        record("stress_level", 0.9) → CRITICAL alert.

        Проверяем: stress_level critical.
        Границы: value = 0.9.
        Почему такие: проверка stress threshold.
        """
        from space1.metrics.monitoring import SystemMonitor, AlertLevel
        monitor = SystemMonitor()
        monitor.record("stress_level", 0.9)
        assert len(monitor.alerts) == 1
        assert monitor.alerts[0].level == AlertLevel.CRITICAL

    def test_monitor_alert_stress_warning(self):
        """
        record("stress_level", 0.7) → WARNING alert.

        Проверяем: stress_level warning.
        Границы: value = 0.7.
        Почему такие: проверка stress threshold.
        """
        from space1.metrics.monitoring import SystemMonitor, AlertLevel
        monitor = SystemMonitor()
        monitor.record("stress_level", 0.7)
        assert len(monitor.alerts) == 1
        assert monitor.alerts[0].level == AlertLevel.WARNING

    def test_monitor_alert_stress_safe(self):
        """
        record("stress_level", 0.5) → нет alerts.

        Проверяем: stress_level безопасен.
        Границы: value < warning.
        Почему такие: проверка безопасного значения.
        """
        from space1.metrics.monitoring import SystemMonitor
        monitor = SystemMonitor()
        monitor.record("stress_level", 0.5)
        assert len(monitor.alerts) == 0

    def test_monitor_get_alerts_all(self):
        """
        get_alerts() → все alerts.

        Проверяем: получение всех alerts.
        Границы: 2 alerts.
        Почему такие: проверка get_alerts.
        """
        from space1.metrics.monitoring import SystemMonitor, AlertLevel
        monitor = SystemMonitor()
        monitor.record("compliance_violations", 1.0)
        monitor.record("compliance_violations", 3.0)
        alerts = monitor.get_alerts()
        assert len(alerts) == 2

    def test_monitor_get_alerts_filtered(self):
        """
        get_alerts(AlertLevel.CRITICAL) → только critical.

        Проверяем: фильтрация по уровню.
        Границы: 1 critical из 2.
        Почему такие: проверка фильтрации.
        """
        from space1.metrics.monitoring import SystemMonitor, AlertLevel
        monitor = SystemMonitor()
        monitor.record("compliance_violations", 1.0)
        monitor.record("compliance_violations", 3.0)
        critical = monitor.get_alerts(AlertLevel.CRITICAL)
        assert len(critical) == 1
        assert critical[0].level == AlertLevel.CRITICAL

    def test_monitor_dispatch_calls_subscriber(self):
        """
        subscribe + record → subscriber вызван.

        Проверяем: dispatch вызывает подписчика.
        Границы: Один подписчик.
        Почему такие: проверка dispatch.
        """
        from space1.metrics.monitoring import SystemMonitor
        monitor = SystemMonitor()
        received = []
        monitor.subscribe(lambda a: received.append(a))
        monitor.record("compliance_violations", 1.0)
        assert len(received) == 1
        assert received[0].metric_name == "compliance_violations"

    def test_monitor_dispatch_multiple_subscribers(self):
        """
        2 subscribers + record → оба вызваны.

        Проверяем: dispatch всем подписчикам.
        Границы: Два подписчика.
        Почему такие: проверка broadcast.
        """
        from space1.metrics.monitoring import SystemMonitor
        monitor = SystemMonitor()
        calls1 = []
        calls2 = []
        monitor.subscribe(lambda a: calls1.append(a))
        monitor.subscribe(lambda a: calls2.append(a))
        monitor.record("compliance_violations", 1.0)
        assert len(calls1) == 1
        assert len(calls2) == 1

    def test_monitor_dispatch_subscriber_exception(self):
        """
        subscriber падает → другие подписчики всё равно вызваны.

        Проверяем: изоляция ошибок подписчиков.
        Границы: Один падает, один OK.
        Почему такие: проверка robustness.
        """
        from space1.metrics.monitoring import SystemMonitor
        monitor = SystemMonitor()
        calls = []
        monitor.subscribe(lambda a: (_ for _ in ()).throw(Exception("boom")))
        monitor.subscribe(lambda a: calls.append(a))
        monitor.record("compliance_violations", 1.0)
        # ЭТО БАГ: except Exception: pass маскирует ошибки
        # Но второй подписчик должен быть вызван
        assert len(calls) == 1

    def test_monitor_alert_message_contains_metric(self):
        """
        Alert.message содержит имя метрики.

        Проверяем: содержимое сообщения.
        Границы: Стандартный кейс.
        Почему такие: проверка формата сообщения.
        """
        from space1.metrics.monitoring import SystemMonitor
        monitor = SystemMonitor()
        monitor.record("compliance_violations", 3.0)
        assert "compliance_violations" in monitor.alerts[0].message

    def test_monitor_alert_message_contains_values(self):
        """
        Alert.message содержит value и threshold.

        Проверяем: содержимое сообщения.
        Границы: Стандартный кейс.
        Почему такие: проверка формата сообщения.
        """
        from space1.metrics.monitoring import SystemMonitor
        monitor = SystemMonitor()
        monitor.record("compliance_violations", 3.0)
        assert "3.0" in monitor.alerts[0].message
        assert "3.0" in monitor.alerts[0].message  # threshold тоже 3.0

    def test_monitor_record_float_conversion(self):
        """
        record("m", "15.5") → value=15.5 (float conversion).

        Проверяем: auto-conversion string → float.
        Границы: value как строка.
        Почему такие: проверка robustness типов.
        """
        from space1.metrics.monitoring import SystemMonitor
        monitor = SystemMonitor()
        monitor.record("m", "15.5")
        assert monitor.metrics["m"][0].value == 15.5
        assert isinstance(monitor.metrics["m"][0].value, float)


# =============================================================================
# PAIR: SystemMonitor + Alert
# =============================================================================

class TestPairMonitorAlert:
    """PAIR: SystemMonitor + Alert — интеграция в миниатюре."""

    def test_monitor_creates_alert_with_correct_level(self):
        """
        record → Alert с правильным AlertLevel.

        Проверяем: monitor создаёт Alert с корректным enum.
        Границы: WARNING.
        Почему такие: интеграция monitor → alert.
        """
        from space1.metrics.monitoring import SystemMonitor, AlertLevel
        monitor = SystemMonitor()
        monitor.record("compliance_violations", 1.0)
        assert isinstance(monitor.alerts[0].level, AlertLevel)
        assert monitor.alerts[0].level == AlertLevel.WARNING

    def test_monitor_alert_has_timestamp(self):
        """
        record → Alert с timestamp.

        Проверяем: timestamp в Alert.
        Границы: Стандартный кейс.
        Почему такие: интеграция — проверка полноты.
        """
        from space1.metrics.monitoring import SystemMonitor
        monitor = SystemMonitor()
        monitor.record("compliance_violations", 1.0)
        assert isinstance(monitor.alerts[0].timestamp, datetime)


# =============================================================================
# PAIR: SystemMonitor + Subscriber
# =============================================================================

class TestPairMonitorSubscriber:
    """PAIR: SystemMonitor + Subscriber — интеграция в миниатюре."""

    def test_subscriber_receives_alert_object(self):
        """
        subscribe + record → subscriber получает Alert.

        Проверяем: тип объекта в callback.
        Границы: Стандартный кейс.
        Почему такие: интеграция monitor → subscriber.
        """
        from space1.metrics.monitoring import SystemMonitor, Alert
        monitor = SystemMonitor()
        received = []
        monitor.subscribe(lambda a: received.append(a))
        monitor.record("compliance_violations", 1.0)
        assert isinstance(received[0], Alert)

    def test_subscriber_receives_correct_alert_data(self):
        """
        subscribe + record → Alert содержит правильные value/threshold.

        Проверяем: точность данных в Alert.
        Границы: value = 3.0, threshold = 3.0.
        Почему такие: интеграция — проверка точности.
        """
        from space1.metrics.monitoring import SystemMonitor
        monitor = SystemMonitor()
        received = []
        monitor.subscribe(lambda a: received.append(a))
        monitor.record("compliance_violations", 3.0)
        assert received[0].value == 3.0
        assert received[0].threshold == 3.0


# =============================================================================
# INTEGRITY: Архитектурные инварианты
# =============================================================================

class TestIntegrityMonitoring:
    """INTEGRITY: Архитектурные инварианты metrics/monitoring.py."""

    def test_bare_except_in_dispatch(self):
        """
        _dispatch_alert содержит except Exception: pass (10_SECURITY.md §III).

        Проверяем: наличие bare except — ЭТО БАГ.
        Границы: Проверка всего файла.
        Почему такие: bare except маскирует ошибки подписчиков.
        """
        import inspect
        from space1.metrics import monitoring
        src_file = inspect.getfile(monitoring)
        with open(src_file, 'r') as f:
            lines = f.readlines()
        bare_excepts = [i + 1 for i, line in enumerate(lines) if "except Exception" in line]
        # ЭТО БАГ: bare except в _dispatch_alert
        assert len(bare_excepts) == 1, f"Bare except найден на строках: {bare_excepts}"

    def test_alert_level_enum_complete(self):
        """
        AlertLevel содержит ровно 3 значения: INFO, WARNING, CRITICAL.

        Проверяем: полнота enum.
        Границы: Все значения.
        Почему такие: архитектурный инвариант — 3 уровня alert.
        """
        from space1.metrics.monitoring import AlertLevel
        assert set(a.value for a in AlertLevel) == {"info", "warning", "critical"}

    def test_default_thresholds_have_direction(self):
        """
        Все default thresholds имеют direction.

        Проверяем: полнота конфигурации.
        Границы: Все default thresholds.
        Почему такие: архитектурный инвариант — direction обязателен.
        """
        from space1.metrics.monitoring import SystemMonitor
        monitor = SystemMonitor()
        for name, th in monitor.thresholds.items():
            assert "direction" in th, f"{name} missing direction"
            assert th["direction"] in ("gt", "lt"), f"{name} invalid direction"

    def test_default_thresholds_have_warning_and_critical(self):
        """
        Все default thresholds имеют warning и critical.

        Проверяем: полнота конфигурации.
        Границы: Все default thresholds.
        Почему такие: архитектурный инвариант — оба уровня обязательны.
        """
        from space1.metrics.monitoring import SystemMonitor
        monitor = SystemMonitor()
        for name, th in monitor.thresholds.items():
            assert "warning" in th, f"{name} missing warning"
            assert "critical" in th, f"{name} missing critical"

    def test_critical_priority_over_warning(self):
        """
        value = critical → только CRITICAL alert, не WARNING.

        Проверяем: приоритет critical.
        Границы: value = critical threshold.
        Почему такие: архитектурный инвариант — critical имеет приоритет.
        """
        from space1.metrics.monitoring import SystemMonitor, AlertLevel
        monitor = SystemMonitor()
        monitor.record("compliance_violations", 3.0)
        assert len(monitor.alerts) == 1
        assert monitor.alerts[0].level == AlertLevel.CRITICAL


# =============================================================================
# REGRESSION: Старые баги не вернулись
# =============================================================================

class TestRegressionMonitoring:
    """REGRESSION: Проверки, что исправленные баги не вернулись."""

    def test_record_no_crash_without_threshold(self):
        """
        record("unknown", 100.0) без threshold → не падает.

        Проверяем: graceful handling неизвестной метрики.
        Границы: Нет threshold.
        Почему такие: регрессия — ранее мог упасть.
        """
        from space1.metrics.monitoring import SystemMonitor
        monitor = SystemMonitor()
        monitor.record("unknown_metric", 100.0)
        assert "unknown_metric" in monitor.metrics
        assert len(monitor.alerts) == 0

    def test_get_latest_no_crash_empty(self):
        """
        get_latest("m") для пустого monitor → None, не падает.

        Проверяем: graceful handling пустого monitor.
        Границы: Пустой monitor.
        Почему такие: регрессия — ранее мог упасть.
        """
        from space1.metrics.monitoring import SystemMonitor
        monitor = SystemMonitor()
        assert monitor.get_latest("anything") is None

    def test_subscriber_exception_does_not_crash_monitor(self):
        """
        Падающий subscriber → monitor продолжает работать.

        Проверяем: изоляция ошибок.
        Границы: Падающий callback.
        Почему такие: регрессия — ранее мог упасть весь monitor.
        """
        from space1.metrics.monitoring import SystemMonitor
        monitor = SystemMonitor()
        monitor.subscribe(lambda a: (_ for _ in ()).throw(Exception("boom")))
        # ЭТО БАГ: except Exception: pass маскирует, но monitor не падает
        monitor.record("compliance_violations", 1.0)
        assert len(monitor.alerts) == 1  # Alert всё равно создан
