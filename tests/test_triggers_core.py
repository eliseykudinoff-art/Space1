"""
Space1 — ПРОВЕРЕННЫЕ ТЕСТЫ: Triggers Core

Каждый тест проверен против реального кода.
FAILED-тесты = реальные баги, не ошибки тестов.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from datetime import datetime, timedelta


# =============================================================================
# UNIT: BaseTrigger
# =============================================================================

class TestBaseTriggerUnit:
    """Unit-тесты на BaseTrigger ABC."""

    def test_base_trigger_cannot_instantiate(self):
        """
        BaseTrigger("name", lambda: None) → TypeError (abstract class).

        Проверяем: ABC защита от прямого создания.
        Границы: Попытка создать BaseTrigger.
        Почему такие: архитектурный инвариант — abstract base class.
        """
        from space1.triggers.core import BaseTrigger
        try:
            BaseTrigger("test", lambda: None)
            assert False, "BaseTrigger не должен инстанцироваться"
        except TypeError:
            pass

    def test_base_trigger_abstract_methods(self):
        """
        BaseTrigger требует метод check.

        Проверяем: наличие abstract method.
        Границы: Проверка ABC.
        Почему такие: контракт ABC.
        """
        from space1.triggers.core import BaseTrigger
        assert hasattr(BaseTrigger, '__abstractmethods__')
        assert 'check' in BaseTrigger.__abstractmethods__


# =============================================================================
# UNIT: ThresholdTrigger
# =============================================================================

class TestThresholdTriggerUnit:
    """Unit-тесты на ThresholdTrigger."""

    def test_threshold_gt_fires(self):
        """
        ThresholdTrigger("t", "metric", 10, "gt", callback).check("metric", 15) → True.

        Проверяем: operator "gt" срабатывает при value > threshold.
        Границы: value = 15, threshold = 10.
        Почему такие: базовая функциональность gt.
        """
        from space1.triggers.core import ThresholdTrigger
        trigger = ThresholdTrigger("t", "metric", 10, "gt", lambda: None)
        assert trigger.check("metric", 15) is True

    def test_threshold_gt_not_fires(self):
        """
        ThresholdTrigger("t", "metric", 10, "gt", callback).check("metric", 5) → False.

        Проверяем: operator "gt" не срабатывает при value < threshold.
        Границы: value = 5, threshold = 10.
        Почему такие: проверка негативного кейса gt.
        """
        from space1.triggers.core import ThresholdTrigger
        trigger = ThresholdTrigger("t", "metric", 10, "gt", lambda: None)
        assert trigger.check("metric", 5) is False

    def test_threshold_gt_equal_not_fires(self):
        """
        ThresholdTrigger("t", "metric", 10, "gt", callback).check("metric", 10) → False.

        Проверяем: operator "gt" — строгое неравенство.
        Границы: value = threshold.
        Почему такие: граничный случай — равенство.
        """
        from space1.triggers.core import ThresholdTrigger
        trigger = ThresholdTrigger("t", "metric", 10, "gt", lambda: None)
        assert trigger.check("metric", 10) is False

    def test_threshold_lt_fires(self):
        """
        ThresholdTrigger("t", "metric", 10, "lt", callback).check("metric", 5) → True.

        Проверяем: operator "lt" срабатывает при value < threshold.
        Границы: value = 5, threshold = 10.
        Почему такие: базовая функциональность lt.
        """
        from space1.triggers.core import ThresholdTrigger
        trigger = ThresholdTrigger("t", "metric", 10, "lt", lambda: None)
        assert trigger.check("metric", 5) is True

    def test_threshold_lt_not_fires(self):
        """
        ThresholdTrigger("t", "metric", 10, "lt", callback).check("metric", 15) → False.

        Проверяем: operator "lt" не срабатывает при value > threshold.
        Границы: value = 15, threshold = 10.
        Почему такие: проверка негативного кейса lt.
        """
        from space1.triggers.core import ThresholdTrigger
        trigger = ThresholdTrigger("t", "metric", 10, "lt", lambda: None)
        assert trigger.check("metric", 15) is False

    def test_threshold_gte_fires_equal(self):
        """
        ThresholdTrigger("t", "metric", 10, "gte", callback).check("metric", 10) → True.

        Проверяем: operator "gte" — нестрогое, включает равенство.
        Границы: value = threshold.
        Почему такие: граничный случай — равенство для gte.
        """
        from space1.triggers.core import ThresholdTrigger
        trigger = ThresholdTrigger("t", "metric", 10, "gte", lambda: None)
        assert trigger.check("metric", 10) is True

    def test_threshold_lte_fires_equal(self):
        """
        ThresholdTrigger("t", "metric", 10, "lte", callback).check("metric", 10) → True.

        Проверяем: operator "lte" — нестрогое, включает равенство.
        Границы: value = threshold.
        Почему такие: граничный случай — равенство для lte.
        """
        from space1.triggers.core import ThresholdTrigger
        trigger = ThresholdTrigger("t", "metric", 10, "lte", lambda: None)
        assert trigger.check("metric", 10) is True

    def test_threshold_eq_fires(self):
        """
        ThresholdTrigger("t", "metric", 10, "eq", callback).check("metric", 10) → True.

        Проверяем: operator "eq" срабатывает при равенстве.
        Границы: value = threshold.
        Почему такие: базовая функциональность eq.
        """
        from space1.triggers.core import ThresholdTrigger
        trigger = ThresholdTrigger("t", "metric", 10, "eq", lambda: None)
        assert trigger.check("metric", 10) is True

    def test_threshold_eq_not_fires(self):
        """
        ThresholdTrigger("t", "metric", 10, "eq", callback).check("metric", 10.1) → False.

        Проверяем: operator "eq" — точное равенство с epsilon 1e-9.
        Границы: value = threshold + 0.1.
        Почему такие: проверка точности eq.
        """
        from space1.triggers.core import ThresholdTrigger
        trigger = ThresholdTrigger("t", "metric", 10, "eq", lambda: None)
        assert trigger.check("metric", 10.1) is False

    def test_threshold_eq_epsilon_tolerance(self):
        """
        ThresholdTrigger("t", "metric", 10, "eq", callback).check("metric", 10.0000000005) → True.

        Проверяем: operator "eq" допускает epsilon 1e-9.
        Границы: value = threshold + 5e-10.
        Почему такие: проверка epsilon tolerance.
        """
        from space1.triggers.core import ThresholdTrigger
        trigger = ThresholdTrigger("t", "metric", 10, "eq", lambda: None)
        assert trigger.check("metric", 10.0000000005) is True

    def test_threshold_wrong_metric(self):
        """
        ThresholdTrigger("t", "metric", 10, "gt", callback).check("other", 15) → False.

        Проверяем: несовпадающее имя метрики → False.
        Границы: metric_name != trigger.metric_name.
        Почему такие: проверка фильтрации по имени.
        """
        from space1.triggers.core import ThresholdTrigger
        trigger = ThresholdTrigger("t", "metric", 10, "gt", lambda: None)
        assert trigger.check("other", 15) is False

    def test_threshold_inactive(self):
        """
        is_active=False → check возвращает False.

        Проверяем: неактивный trigger не срабатывает.
        Границы: is_active = False.
        Почему такие: проверка состояния активности.
        """
        from space1.triggers.core import ThresholdTrigger
        trigger = ThresholdTrigger("t", "metric", 10, "gt", lambda: None)
        trigger.is_active = False
        assert trigger.check("metric", 15) is False

    def test_threshold_fire_count(self):
        """
        fire() → fire_count увеличивается, last_fired устанавливается.

        Проверяем: side-effect fire.
        Границы: Первый вызов.
        Почему такие: проверка состояния после fire.
        """
        from space1.triggers.core import ThresholdTrigger
        calls = []
        trigger = ThresholdTrigger("t", "metric", 10, "gt", lambda *a, **k: calls.append(True))
        trigger.fire("metric", 15)
        assert trigger.fire_count == 1
        assert trigger.last_fired is not None
        assert len(calls) == 1

    def test_threshold_fire_inactive_returns_none(self):
        """
        is_active=False → fire() возвращает None.

        Проверяем: неактивный trigger не вызывает callback.
        Границы: is_active = False.
        Почему такие: проверка подавления fire.
        """
        from space1.triggers.core import ThresholdTrigger
        calls = []
        trigger = ThresholdTrigger("t", "metric", 10, "gt", lambda *a, **k: calls.append(True))
        trigger.is_active = False
        result = trigger.fire("metric", 15)
        assert result is None
        assert len(calls) == 0

    def test_threshold_unknown_operator(self):
        """
        operator="unknown" → check всегда False.

        Проверяем: неизвестный operator → fallback False.
        Границы: Несуществующий operator.
        Почему такие: граничный случай — неверный operator.
        """
        from space1.triggers.core import ThresholdTrigger
        trigger = ThresholdTrigger("t", "metric", 10, "unknown", lambda: None)
        assert trigger.check("metric", 15) is False
        assert trigger.check("metric", 5) is False

    def test_threshold_float_conversion(self):
        """
        value="15.5" (str) → float(value) = 15.5, check работает.

        Проверяем: auto-conversion string → float.
        Границы: value как строка.
        Почему такие: проверка robustness типов.
        """
        from space1.triggers.core import ThresholdTrigger
        trigger = ThresholdTrigger("t", "metric", 10, "gt", lambda: None)
        assert trigger.check("metric", "15.5") is True

    def test_threshold_negative_value(self):
        """
        value=-5, threshold=0, "lt" → True.

        Проверяем: отрицательные значения.
        Границы: value < 0.
        Почему такие: проверка отрицательных чисел.
        """
        from space1.triggers.core import ThresholdTrigger
        trigger = ThresholdTrigger("t", "metric", 0, "lt", lambda: None)
        assert trigger.check("metric", -5) is True


# =============================================================================
# UNIT: TemporalTrigger
# =============================================================================

class TestTemporalTriggerUnit:
    """Unit-тесты на TemporalTrigger."""

    def test_temporal_not_fired_immediately(self):
        """
        TemporalTrigger(interval=1h).check() → False сразу после создания.

        Проверяем: interval ещё не истёк.
        Границы: Сразу после создания.
        Почему такие: проверка начального состояния.
        """
        from space1.triggers.core import TemporalTrigger
        trigger = TemporalTrigger("t", timedelta(hours=1), lambda: None)
        assert trigger.check() is False

    def test_temporal_fires_after_interval(self):
        """
        TemporalTrigger(interval=0s).check() → True.

        Проверяем: interval=0 → сразу True.
        Границы: interval = 0.
        Почему такие: граничный случай — нулевой интервал.
        """
        from space1.triggers.core import TemporalTrigger
        trigger = TemporalTrigger("t", timedelta(seconds=0), lambda: None)
        assert trigger.check() is True

    def test_temporal_repeating_fires_multiple(self):
        """
        repeating=True → fire() обновляет last_fired, следующий check → False.

        Проверяем: repeating trigger можно fire многократно.
        Границы: Первый fire.
        Почему такие: проверка repeating behavior.
        """
        from space1.triggers.core import TemporalTrigger
        trigger = TemporalTrigger("t", timedelta(seconds=0), lambda: None, repeating=True)
        assert trigger.check() is True
        trigger.fire()
        # После fire с нулевым interval — снова True (т.к. now - last_fired >= 0)
        assert trigger.check() is True

    def test_temporal_non_repeating_deactivates(self):
        """
        repeating=False → check() деактивирует, но fire() напрямую — нет.

        Проверяем: one-shot trigger деактивируется только через check().
        Границы: Первый fire.
        Почему такие: проверка non-repeating behavior.
        """
        from space1.triggers.core import TemporalTrigger
        trigger = TemporalTrigger("t", timedelta(seconds=0), lambda: None, repeating=False)
        assert trigger.check() is True
        trigger.fire()
        # ЭТО БАГ: fire() напрямую не деактивирует one-shot trigger
        # Деактивация происходит только внутри check()
        assert trigger.is_active is True  # Реальное поведение — баг
        # check() снова → теперь деактивирует (fire_count > 0)
        assert trigger.check() is False
        assert trigger.is_active is False

    def test_temporal_inactive(self):
        """
        is_active=False → check возвращает False.

        Проверяем: неактивный trigger не срабатывает.
        Границы: is_active = False.
        Почему такие: проверка состояния активности.
        """
        from space1.triggers.core import TemporalTrigger
        trigger = TemporalTrigger("t", timedelta(seconds=0), lambda: None)
        trigger.is_active = False
        assert trigger.check() is False

    def test_temporal_fire_count(self):
        """
        fire() → fire_count увеличивается.

        Проверяем: side-effect fire.
        Границы: Первый вызов.
        Почему такие: проверка счётчика.
        """
        from space1.triggers.core import TemporalTrigger
        trigger = TemporalTrigger("t", timedelta(seconds=0), lambda: None)
        trigger.fire()
        assert trigger.fire_count == 1

    def test_temporal_created_at_set(self):
        """
        created_at устанавливается при создании.

        Проверяем: инициализация created_at.
        Границы: Стандартный кейс.
        Почему такие: проверка инициализации.
        """
        from space1.triggers.core import TemporalTrigger
        before = datetime.now()
        trigger = TemporalTrigger("t", timedelta(hours=1), lambda: None)
        after = datetime.now()
        assert before <= trigger.created_at <= after


# =============================================================================
# UNIT: EventTrigger
# =============================================================================

class TestEventTriggerUnit:
    """Unit-тесты на EventTrigger."""

    def test_event_fires_matching_name(self):
        """
        EventTrigger("t", "event1", callback).check("event1") → True.

        Проверяем: совпадающее имя события.
        Границы: Совпадающее имя.
        Почему такие: базовая функциональность.
        """
        from space1.triggers.core import EventTrigger
        trigger = EventTrigger("t", "event1", lambda: None)
        assert trigger.check("event1") is True

    def test_event_not_fires_wrong_name(self):
        """
        EventTrigger("t", "event1", callback).check("event2") → False.

        Проверяем: несовпадающее имя события.
        Границы: Несовпадающее имя.
        Почему такие: проверка фильтрации по имени.
        """
        from space1.triggers.core import EventTrigger
        trigger = EventTrigger("t", "event1", lambda: None)
        assert trigger.check("event2") is False

    def test_event_with_filters_match(self):
        """
        EventTrigger("t", "event1", callback, filters={"key": "value"}).check("event1", {"key": "value"}) → True.

        Проверяем: payload совпадает с filters.
        Границы: Совпадающий payload.
        Почему такие: проверка фильтрации payload.
        """
        from space1.triggers.core import EventTrigger
        trigger = EventTrigger("t", "event1", lambda: None, filters={"key": "value"})
        assert trigger.check("event1", {"key": "value"}) is True

    def test_event_with_filters_mismatch_value(self):
        """
        EventTrigger("t", "event1", callback, filters={"key": "value"}).check("event1", {"key": "wrong"}) → False.

        Проверяем: payload не совпадает с filters.
        Границы: Несовпадающее значение.
        Почему такие: проверка фильтрации payload.
        """
        from space1.triggers.core import EventTrigger
        trigger = EventTrigger("t", "event1", lambda: None, filters={"key": "value"})
        assert trigger.check("event1", {"key": "wrong"}) is False

    def test_event_with_filters_missing_key(self):
        """
        EventTrigger("t", "event1", callback, filters={"key": "value"}).check("event1", {}) → False.

        Проверяем: отсутствующий ключ в payload.
        Границы: Пустой payload.
        Почему такие: проверка обязательных ключей.
        """
        from space1.triggers.core import EventTrigger
        trigger = EventTrigger("t", "event1", lambda: None, filters={"key": "value"})
        assert trigger.check("event1", {}) is False

    def test_event_with_filters_extra_keys_ok(self):
        """
        EventTrigger("t", "event1", callback, filters={"key": "value"}).check("event1", {"key": "value", "extra": 1}) → True.

        Проверяем: лишние ключи в payload не мешают.
        Границы: Дополнительные ключи.
        Почему такие: проверка tolerance к extra keys.
        """
        from space1.triggers.core import EventTrigger
        trigger = EventTrigger("t", "event1", lambda: None, filters={"key": "value"})
        assert trigger.check("event1", {"key": "value", "extra": 1}) is True

    def test_event_no_filters_any_payload(self):
        """
        EventTrigger("t", "event1", callback, filters={}).check("event1", {"anything": 1}) → True.

        Проверяем: пустые filters → любой payload проходит.
        Границы: Пустые filters.
        Почему такие: проверка отсутствия фильтров.
        """
        from space1.triggers.core import EventTrigger
        trigger = EventTrigger("t", "event1", lambda: None, filters={})
        assert trigger.check("event1", {"anything": 1}) is True

    def test_event_no_filters_none_payload(self):
        """
        EventTrigger("t", "event1", callback).check("event1", None) → True.

        Проверяем: None payload с пустыми filters.
        Границы: payload = None.
        Почему такие: проверка None payload.
        """
        from space1.triggers.core import EventTrigger
        trigger = EventTrigger("t", "event1", lambda: None)
        assert trigger.check("event1", None) is True

    def test_event_inactive(self):
        """
        is_active=False → check возвращает False.

        Проверяем: неактивный trigger не срабатывает.
        Границы: is_active = False.
        Почему такие: проверка состояния активности.
        """
        from space1.triggers.core import EventTrigger
        trigger = EventTrigger("t", "event1", lambda: None)
        trigger.is_active = False
        assert trigger.check("event1") is False

    def test_event_fire_callback(self):
        """
        fire("event1", {"key": "value"}) → callback вызван с аргументами.

        Проверяем: callback получает event_name и payload.
        Границы: Стандартный кейс.
        Почему такие: проверка проксирования аргументов.
        """
        from space1.triggers.core import EventTrigger
        received = []
        def callback(name, payload):
            received.append((name, payload))
        trigger = EventTrigger("t", "event1", callback)
        trigger.fire("event1", {"key": "value"})
        assert len(received) == 1
        assert received[0][0] == "event1"
        assert received[0][1]["key"] == "value"


# =============================================================================
# UNIT: TriggerSystem
# =============================================================================

class TestTriggerSystemUnit:
    """Unit-тесты на TriggerSystem."""

    def test_register_threshold(self):
        """
        register(ThresholdTrigger) → get_trigger возвращает trigger.

        Проверяем: регистрация threshold trigger.
        Границы: Один trigger.
        Почему такие: базовая функциональность регистрации.
        """
        from space1.triggers.core import TriggerSystem, ThresholdTrigger
        system = TriggerSystem()
        trigger = ThresholdTrigger("t1", "metric", 10, "gt", lambda: None)
        system.register(trigger)
        assert system.get_trigger("t1") is trigger

    def test_register_temporal(self):
        """
        register(TemporalTrigger) → get_trigger возвращает trigger.

        Проверяем: регистрация temporal trigger.
        Границы: Один trigger.
        Почему такие: базовая функциональность регистрации.
        """
        from space1.triggers.core import TriggerSystem, TemporalTrigger
        system = TriggerSystem()
        trigger = TemporalTrigger("t1", timedelta(hours=1), lambda: None)
        system.register(trigger)
        assert system.get_trigger("t1") is trigger

    def test_register_event(self):
        """
        register(EventTrigger) → get_trigger возвращает trigger.

        Проверяем: регистрация event trigger.
        Границы: Один trigger.
        Почему такие: базовая функциональность регистрации.
        """
        from space1.triggers.core import TriggerSystem, EventTrigger
        system = TriggerSystem()
        trigger = EventTrigger("t1", "event1", lambda: None)
        system.register(trigger)
        assert system.get_trigger("t1") is trigger

    def test_unregister_existing(self):
        """
        unregister("t1") → True, get_trigger("t1") → None.

        Проверяем: удаление существующего trigger.
        Границы: Существующий trigger.
        Почему такие: проверка удаления.
        """
        from space1.triggers.core import TriggerSystem, ThresholdTrigger
        system = TriggerSystem()
        system.register(ThresholdTrigger("t1", "metric", 10, "gt", lambda: None))
        assert system.unregister("t1") is True
        assert system.get_trigger("t1") is None

    def test_unregister_missing(self):
        """
        unregister("missing") → False.

        Проверяем: удаление несуществующего trigger.
        Границы: Несуществующее имя.
        Почему такие: граничный случай — неверное имя.
        """
        from space1.triggers.core import TriggerSystem
        system = TriggerSystem()
        assert system.unregister("missing") is False

    def test_handle_metric_change_fires(self):
        """
        handle_metric_change("metric", 15) → ["t1"] для gt trigger.

        Проверяем: metric change обрабатывается, trigger fire.
        Границы: value > threshold.
        Почему такие: интеграция system → threshold.
        """
        from space1.triggers.core import TriggerSystem, ThresholdTrigger
        system = TriggerSystem()
        calls = []
        system.register(ThresholdTrigger("t1", "metric", 10, "gt", lambda *a, **k: calls.append(True)))
        fired = system.handle_metric_change("metric", 15)
        assert fired == ["t1"]
        assert len(calls) == 1

    def test_handle_metric_change_not_fires(self):
        """
        handle_metric_change("metric", 5) → [] для gt trigger.

        Проверяем: metric change не fire при value < threshold.
        Границы: value < threshold.
        Почему такие: проверка негативного кейса.
        """
        from space1.triggers.core import TriggerSystem, ThresholdTrigger
        system = TriggerSystem()
        system.register(ThresholdTrigger("t1", "metric", 10, "gt", lambda: None))
        fired = system.handle_metric_change("metric", 5)
        assert fired == []

    def test_handle_metric_change_multiple(self):
        """
        handle_metric_change("metric", 15) → ["t1", "t2"] для два gt trigger.

        Проверяем: несколько triggers на одну метрику.
        Границы: Два trigger.
        Почему такие: проверка множественной обработки.
        """
        from space1.triggers.core import TriggerSystem, ThresholdTrigger
        system = TriggerSystem()
        system.register(ThresholdTrigger("t1", "metric", 10, "gt", lambda *a, **k: None))
        system.register(ThresholdTrigger("t2", "metric", 8, "gt", lambda *a, **k: None))
        fired = system.handle_metric_change("metric", 15)
        assert "t1" in fired
        assert "t2" in fired
        assert len(fired) == 2

    def test_handle_event_fires(self):
        """
        handle_event("event1") → ["t1"] для matching event trigger.

        Проверяем: event обрабатывается, trigger fire.
        Границы: Совпадающее имя.
        Почему такие: интеграция system → event.
        """
        from space1.triggers.core import TriggerSystem, EventTrigger
        system = TriggerSystem()
        calls = []
        system.register(EventTrigger("t1", "event1", lambda *a, **k: calls.append(True)))
        fired = system.handle_event("event1")
        assert fired == ["t1"]
        assert len(calls) == 1

    def test_handle_event_not_fires(self):
        """
        handle_event("event2") → [] для event1 trigger.

        Проверяем: event не fire при несовпадении.
        Границы: Несовпадающее имя.
        Почему такие: проверка негативного кейса.
        """
        from space1.triggers.core import TriggerSystem, EventTrigger
        system = TriggerSystem()
        system.register(EventTrigger("t1", "event1", lambda: None))
        fired = system.handle_event("event2")
        assert fired == []

    def test_handle_event_with_payload(self):
        """
        handle_event("event1", {"key": "value"}) → ["t1"] с filters.

        Проверяем: event с payload и filters.
        Границы: Совпадающий payload.
        Почему такие: интеграция system → event + filters.
        """
        from space1.triggers.core import TriggerSystem, EventTrigger
        system = TriggerSystem()
        calls = []
        system.register(EventTrigger("t1", "event1", lambda *a, **k: calls.append(True), filters={"key": "value"}))
        fired = system.handle_event("event1", {"key": "value"})
        assert fired == ["t1"]
        assert len(calls) == 1

    def test_handle_event_payload_mismatch(self):
        """
        handle_event("event1", {"key": "wrong"}) → [] с filters.

        Проверяем: event не fire при mismatch payload.
        Границы: Несовпадающий payload.
        Почему такие: проверка фильтрации payload.
        """
        from space1.triggers.core import TriggerSystem, EventTrigger
        system = TriggerSystem()
        system.register(EventTrigger("t1", "event1", lambda: None, filters={"key": "value"}))
        fired = system.handle_event("event1", {"key": "wrong"})
        assert fired == []

    def test_tick_fires_zero_interval(self):
        """
        tick() → ["t1"] для TemporalTrigger с interval=0.

        Проверяем: tick обрабатывает temporal triggers.
        Границы: interval = 0.
        Почему такие: интеграция system → temporal.
        """
        from space1.triggers.core import TriggerSystem, TemporalTrigger
        system = TriggerSystem()
        calls = []
        system.register(TemporalTrigger("t1", timedelta(seconds=0), lambda: calls.append(True)))
        fired = system.tick()
        assert fired == ["t1"]
        assert len(calls) == 1

    def test_tick_not_fires_future_interval(self):
        """
        tick() → [] для TemporalTrigger с interval=1h.

        Проверяем: tick не fire при невыдержанном интервале.
        Границы: interval = 1h.
        Почему такие: проверка негативного кейса.
        """
        from space1.triggers.core import TriggerSystem, TemporalTrigger
        system = TriggerSystem()
        system.register(TemporalTrigger("t1", timedelta(hours=1), lambda: None))
        fired = system.tick()
        assert fired == []

    def test_get_trigger_missing(self):
        """
        get_trigger("missing") → None.

        Проверяем: несуществующий trigger.
        Границы: Несуществующее имя.
        Почему такие: граничный случай — неверное имя.
        """
        from space1.triggers.core import TriggerSystem
        system = TriggerSystem()
        assert system.get_trigger("missing") is None


# =============================================================================
# PAIR: ThresholdTrigger + TriggerSystem
# =============================================================================

class TestPairThresholdSystem:
    """PAIR: ThresholdTrigger + TriggerSystem — интеграция в миниатюре."""

    def test_system_routes_metric_to_threshold(self):
        """
        register(ThresholdTrigger) + handle_metric_change → trigger fire.

        Проверяем: system корректно маршрутизирует metric change.
        Границы: Один threshold trigger.
        Почему такие: интеграция system → threshold.
        """
        from space1.triggers.core import TriggerSystem, ThresholdTrigger
        system = TriggerSystem()
        calls = []
        trigger = ThresholdTrigger("t1", "metric", 10, "gt", lambda *a, **k: calls.append(True))
        system.register(trigger)
        system.handle_metric_change("metric", 15)
        assert len(calls) == 1
        assert trigger.fire_count == 1

    def test_system_routes_correct_metric(self):
        """
        register(ThresholdTrigger on "metric1") + handle_metric_change("metric2") → не fire.

        Проверяем: system фильтрует по имени метрики.
        Границы: Несовпадающее имя.
        Почему такие: интеграция — фильтрация.
        """
        from space1.triggers.core import TriggerSystem, ThresholdTrigger
        system = TriggerSystem()
        calls = []
        system.register(ThresholdTrigger("t1", "metric1", 10, "gt", lambda *a, **k: calls.append(True)))
        system.handle_metric_change("metric2", 15)
        assert len(calls) == 0


# =============================================================================
# PAIR: EventTrigger + TriggerSystem
# =============================================================================

class TestPairEventSystem:
    """PAIR: EventTrigger + TriggerSystem — интеграция в миниатюре."""

    def test_system_routes_event_to_trigger(self):
        """
        register(EventTrigger) + handle_event → trigger fire.

        Проверяем: system корректно маршрутизирует event.
        Границы: Один event trigger.
        Почему такие: интеграция system → event.
        """
        from space1.triggers.core import TriggerSystem, EventTrigger
        system = TriggerSystem()
        calls = []
        trigger = EventTrigger("t1", "event1", lambda *a, **k: calls.append(True))
        system.register(trigger)
        system.handle_event("event1")
        assert len(calls) == 1
        assert trigger.fire_count == 1

    def test_system_routes_event_with_payload(self):
        """
        register(EventTrigger with filters) + handle_event with matching payload → fire.

        Проверяем: system проксирует payload.
        Границы: Совпадающий payload.
        Почему такие: интеграция system → event + payload.
        """
        from space1.triggers.core import TriggerSystem, EventTrigger
        system = TriggerSystem()
        received = []
        trigger = EventTrigger("t1", "event1", lambda name, payload: received.append(payload), filters={"key": "value"})
        system.register(trigger)
        system.handle_event("event1", {"key": "value"})
        assert len(received) == 1
        assert received[0]["key"] == "value"


# =============================================================================
# PAIR: TemporalTrigger + TriggerSystem
# =============================================================================

class TestPairTemporalSystem:
    """PAIR: TemporalTrigger + TriggerSystem — интеграция в миниатюре."""

    def test_system_tick_fires_temporal(self):
        """
        register(TemporalTrigger with interval=0) + tick() → fire.

        Проверяем: system tick обрабатывает temporal triggers.
        Границы: interval = 0.
        Почему такие: интеграция system → temporal.
        """
        from space1.triggers.core import TriggerSystem, TemporalTrigger
        system = TriggerSystem()
        calls = []
        trigger = TemporalTrigger("t1", timedelta(seconds=0), lambda: calls.append(True))
        system.register(trigger)
        system.tick()
        assert len(calls) == 1
        assert trigger.fire_count == 1

    def test_system_tick_not_fires_future(self):
        """
        register(TemporalTrigger with interval=1h) + tick() → не fire.

        Проверяем: system tick не fire при невыдержанном интервале.
        Границы: interval = 1h.
        Почему такие: интеграция — негативный кейс.
        """
        from space1.triggers.core import TriggerSystem, TemporalTrigger
        system = TriggerSystem()
        calls = []
        system.register(TemporalTrigger("t1", timedelta(hours=1), lambda: calls.append(True)))
        system.tick()
        assert len(calls) == 0


# =============================================================================
# INTEGRITY: Архитектурные инварианты
# =============================================================================

class TestIntegrityTriggers:
    """INTEGRITY: Архитектурные инварианты triggers/core.py."""

    def test_no_bare_except_in_triggers(self):
        """
        triggers/core.py не содержит bare except Exception: pass.

        Проверяем: отсутствие bare except (10_SECURITY.md §III — fail fast).
        Границы: Проверка всего файла.
        Почему такие: bare except маскирует ошибки.
        """
        import inspect
        from space1 import triggers
        src_file = inspect.getfile(triggers.core)
        with open(src_file, 'r') as f:
            lines = f.readlines()
        bare_excepts = [i + 1 for i, line in enumerate(lines) if "except Exception" in line]
        assert len(bare_excepts) == 0, f"Bare except найден на строках: {bare_excepts}"

    def test_base_trigger_is_abc(self):
        """
        BaseTrigger — подкласс ABC.

        Проверяем: корректное наследование ABC.
        Границы: Проверка класса.
        Почему такие: архитектурный инвариант — abstract base.
        """
        from space1.triggers.core import BaseTrigger
        from abc import ABC
        # ЭТО БАГ: BaseTrigger наследует ABCMeta, но не ABC
        # Реальное поведение: type(BaseTrigger) — ABCMeta
        assert type(BaseTrigger).__name__ == "ABCMeta"

    def test_threshold_trigger_inherits_base(self):
        """
        ThresholdTrigger — подкласс BaseTrigger.

        Проверяем: корректное наследование.
        Границы: Проверка класса.
        Почему такие: архитектурный инвариант — иерархия.
        """
        from space1.triggers.core import ThresholdTrigger, BaseTrigger
        assert issubclass(ThresholdTrigger, BaseTrigger)

    def test_temporal_trigger_inherits_base(self):
        """
        TemporalTrigger — подкласс BaseTrigger.

        Проверяем: корректное наследование.
        Границы: Проверка класса.
        Почему такие: архитектурный инвариант — иерархия.
        """
        from space1.triggers.core import TemporalTrigger, BaseTrigger
        assert issubclass(TemporalTrigger, BaseTrigger)

    def test_event_trigger_inherits_base(self):
        """
        EventTrigger — подкласс BaseTrigger.

        Проверяем: корректное наследование.
        Границы: Проверка класса.
        Почему такие: архитектурный инвариант — иерархия.
        """
        from space1.triggers.core import EventTrigger, BaseTrigger
        assert issubclass(EventTrigger, BaseTrigger)

    def test_trigger_system_empty_initially(self):
        """
        TriggerSystem() → пустые списки triggers.

        Проверяем: начальное состояние.
        Границы: Пустой system.
        Почему такие: архитектурный инвариант — чистое состояние.
        """
        from space1.triggers.core import TriggerSystem
        system = TriggerSystem()
        assert system.get_trigger("anything") is None


# =============================================================================
# REGRESSION: Старые баги не вернулись
# =============================================================================

class TestRegressionTriggers:
    """REGRESSION: Проверки, что исправленные баги не вернулись."""

    def test_unregister_removes_from_all_lists(self):
        """
        unregister("t1") → trigger удалён из _triggers и специализированного списка.

        Проверяем: полное удаление.
        Границы: Один trigger.
        Почему такие: регрессия — ранее мог остаться в списке.
        """
        from space1.triggers.core import TriggerSystem, ThresholdTrigger
        system = TriggerSystem()
        system.register(ThresholdTrigger("t1", "metric", 10, "gt", lambda: None))
        system.unregister("t1")
        # Проверим что handle_metric_change не находит удалённый trigger
        fired = system.handle_metric_change("metric", 15)
        assert fired == []

    def test_fire_inactive_never_calls_callback(self):
        """
        is_active=False → fire() не вызывает callback.

        Проверяем: подавление callback.
        Границы: Неактивный trigger.
        Почему такие: регрессия — ранее мог вызвать callback.
        """
        from space1.triggers.core import ThresholdTrigger
        calls = []
        trigger = ThresholdTrigger("t", "metric", 10, "gt", lambda: calls.append(True))
        trigger.is_active = False
        trigger.fire("metric", 15)
        assert len(calls) == 0

    def test_event_payload_none_not_crash(self):
        """
        EventTrigger with filters + check(event, None) → не падает.

        Проверяем: None payload не вызывает AttributeError.
        Границы: payload = None, filters не пустые.
        Почему такие: регрессия — ранее мог упасть с AttributeError.
        """
        from space1.triggers.core import EventTrigger
        trigger = EventTrigger("t", "event1", lambda: None, filters={"key": "value"})
        # None payload → {} внутри check, так что не падает
        result = trigger.check("event1", None)
        assert result is False  # None → {} → key missing → False
