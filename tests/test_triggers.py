"""
Tests for Phase 3 Trigger System (G12 Triggers)
"""

import pytest
from datetime import timedelta
import time

from space1.triggers import (
    ThresholdTrigger,
    TemporalTrigger,
    EventTrigger,
    TriggerSystem,
)


class TestTriggerSystem:
    """Test Suite for Space1 Trigger System."""

    def test_threshold_trigger(self):
        """Test threshold breaching triggers."""
        fired_flag = False
        fired_val = 0.0

        def callback(metric_name, value):
            nonlocal fired_flag, fired_val
            fired_flag = True
            fired_val = value

        # Fires when utility_score < 0.3
        trigger = ThresholdTrigger(
            name="low_utility_warning",
            metric_name="utility_score",
            threshold=0.3,
            operator="lt",
            callback=callback,
        )

        # Value above threshold
        assert trigger.check("utility_score", 0.5) is False
        assert not fired_flag

        # Value below threshold (breach)
        assert trigger.check("utility_score", 0.25) is True
        trigger.fire("utility_score", 0.25)
        assert fired_flag
        assert fired_val == 0.25
        assert trigger.fire_count == 1
        assert trigger.last_fired is not None

    def test_temporal_trigger(self):
        """Test temporal delay triggers."""
        fired_count = 0

        def callback():
            nonlocal fired_count
            fired_count += 1

        # Periodic trigger with 5ms interval (using tiny interval for unit testing)
        trigger = TemporalTrigger(
            name="periodic_tick",
            interval=timedelta(milliseconds=5),
            callback=callback,
            repeating=True
        )

        # Check immediately (not enough time elapsed yet)
        assert trigger.check() is False
        
        # Sleep and check again
        time.sleep(0.01)
        assert trigger.check() is True
        trigger.fire()
        assert fired_count == 1

    def test_event_trigger_filtering(self):
        """Test event named events and payload filter matches."""
        fired_flag = False
        payload_received = None

        def callback(event_name, payload):
            nonlocal fired_flag, payload_received
            fired_flag = True
            payload_received = payload

        # Listen to compliance_veto event on action 'rm_rf'
        trigger = EventTrigger(
            name="critical_veto",
            event_name="compliance_veto",
            callback=callback,
            filters={"action": "rm_rf"}
        )

        # Different event name
        assert trigger.check("execution_success", {"action": "rm_rf"}) is False
        
        # Matching event name, mismatching payload filter
        assert trigger.check("compliance_veto", {"action": "write_file"}) is False

        # Match
        assert trigger.check("compliance_veto", {"action": "rm_rf"}) is True
        trigger.fire("compliance_veto", {"action": "rm_rf"})
        assert fired_flag
        assert payload_received == {"action": "rm_rf"}

    def test_trigger_system_orchestration(self):
        """Test TriggerSystem central coordination and subscription updates."""
        system = TriggerSystem()
        
        metric_fired = False
        event_fired = False
        
        system.register(ThresholdTrigger(
            "t1", "risk", 0.7, "gt", lambda m, v: setattr(pytest, "metric_fired", True)
        ))
        
        system.register(EventTrigger(
            "e1", "execution_failure", lambda e, p: setattr(pytest, "event_fired", True)
        ))
        
        pytest.metric_fired = False
        pytest.event_fired = False
        
        # Test metric change routing
        fired_triggers = system.handle_metric_change("risk", 0.8)
        assert "t1" in fired_triggers
        assert pytest.metric_fired is True
        
        # Test event routing
        fired_events = system.handle_event("execution_failure", {"action": "compute_phi"})
        assert "e1" in fired_events
        assert pytest.event_fired is True
        
        # Test unregister
        assert system.unregister("t1") is True
        assert system.get_trigger("t1") is None
