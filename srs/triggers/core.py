"""
Triggers Module — Threshold, Temporal, and Event Triggers

G12: Trigger System

Provides:
- BaseTrigger: Abstract base class for triggers
- ThresholdTrigger: Fires when metrics breach a threshold
- TemporalTrigger: Fires after a specific time interval
- EventTrigger: Fires on specified events
- TriggerSystem: Manages and coordinates triggers and event subscriptions
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Callable, Optional


class BaseTrigger(ABC):
    """Base class for all triggers."""
    
    def __init__(self, name: str, callback: Callable[..., Any]):
        self.name = name
        self.callback = callback
        self.is_active = True
        self.last_fired: Optional[datetime] = None
        self.fire_count = 0
        
    @abstractmethod
    def check(self, *args: Any, **kwargs: Any) -> bool:
        """Check if trigger conditions are met."""
        pass
        
    def fire(self, *args: Any, **kwargs: Any) -> Any:
        """Fire the trigger callback."""
        if not self.is_active:
            return None
        self.last_fired = datetime.now()
        self.fire_count += 1
        return self.callback(*args, **kwargs)


class ThresholdTrigger(BaseTrigger):
    """
    ThresholdTrigger.
    
    Fires when a monitored metric breaches a threshold (greater than, less than, etc.).
    """
    
    def __init__(
        self,
        name: str,
        metric_name: str,
        threshold: float,
        operator: str,  # "gt", "lt", "gte", "lte", "eq"
        callback: Callable[..., Any],
    ):
        super().__init__(name, callback)
        self.metric_name = metric_name
        self.threshold = float(threshold)
        self.operator = operator.lower()
        
    def check(self, metric_name: str, value: float) -> bool:
        """Check if the provided metric value satisfies the threshold constraint."""
        if not self.is_active or metric_name != self.metric_name:
            return False
            
        val = float(value)
        if self.operator == "gt":
            return val > self.threshold
        elif self.operator == "lt":
            return val < self.threshold
        elif self.operator == "gte":
            return val >= self.threshold
        elif self.operator == "lte":
            return val <= self.threshold
        elif self.operator == "eq":
            return abs(val - self.threshold) < 1e-9
            
        return False


class TemporalTrigger(BaseTrigger):
    """
    TemporalTrigger.
    
    Fires after a specific period or in repeating intervals.
    """
    
    def __init__(self, name: str, interval: timedelta, callback: Callable[..., Any], repeating: bool = True):
        super().__init__(name, callback)
        self.interval = interval
        self.repeating = repeating
        self.created_at = datetime.now()
        self.last_checked = datetime.now()
        
    def check(self) -> bool:
        """Check if interval duration has elapsed."""
        if not self.is_active:
            return False
            
        now = datetime.now()
        reference_time = self.last_fired if self.last_fired else self.created_at
        
        if now - reference_time >= self.interval:
            # If not repeating, deactivate after firing once
            if not self.repeating and self.fire_count > 0:
                self.is_active = False
                return False
            return True
            
        return False


class EventTrigger(BaseTrigger):
    """
    EventTrigger.
    
    Fires when a specific named event is received with matching optional filters.
    """
    
    def __init__(self, name: str, event_name: str, callback: Callable[..., Any], filters: Optional[Dict[str, Any]] = None):
        super().__init__(name, callback)
        self.event_name = event_name
        self.filters = filters or {}
        
    def check(self, event_name: str, payload: Optional[Dict[str, Any]] = None) -> bool:
        """Check if incoming event and payload match trigger requirements."""
        if not self.is_active or event_name != self.event_name:
            return False
            
        if not self.filters:
            return True
            
        payload = payload or {}
        for k, v in self.filters.items():
            if k not in payload or payload[k] != v:
                return False
                
        return True


class TriggerSystem:
    """
    Central trigger manager coordinating Threshold, Temporal, and Event Triggers.
    """
    
    def __init__(self):
        self._triggers: Dict[str, BaseTrigger] = {}
        self._threshold_triggers: List[ThresholdTrigger] = []
        self._temporal_triggers: List[TemporalTrigger] = []
        self._event_triggers: List[EventTrigger] = []
        
    def register(self, trigger: BaseTrigger) -> None:
        """Register a new trigger."""
        self._triggers[trigger.name] = trigger
        if isinstance(trigger, ThresholdTrigger):
            self._threshold_triggers.append(trigger)
        elif isinstance(trigger, TemporalTrigger):
            self._temporal_triggers.append(trigger)
        elif isinstance(trigger, EventTrigger):
            self._event_triggers.append(trigger)
            
    def unregister(self, name: str) -> bool:
        """Unregister trigger by name."""
        if name not in self._triggers:
            return False
            
        trigger = self._triggers.pop(name)
        if isinstance(trigger, ThresholdTrigger):
            self._threshold_triggers.remove(trigger)
        elif isinstance(trigger, TemporalTrigger):
            self._temporal_triggers.remove(trigger)
        elif isinstance(trigger, EventTrigger):
            self._event_triggers.remove(trigger)
        return True
        
    def get_trigger(self, name: str) -> Optional[BaseTrigger]:
        """Retrieve registered trigger."""
        return self._triggers.get(name)
        
    def handle_metric_change(self, metric_name: str, value: float) -> List[str]:
        """
        Process a metric update and fire any triggered ThresholdTriggers.
        
        Returns:
            List of names of triggers that fired.
        """
        fired = []
        for trigger in self._threshold_triggers:
            if trigger.check(metric_name, value):
                trigger.fire(metric_name, value)
                fired.append(trigger.name)
        return fired
        
    def handle_event(self, event_name: str, payload: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Process a custom event and fire any matching EventTriggers.
        
        Returns:
            List of names of triggers that fired.
        """
        fired = []
        for trigger in self._event_triggers:
            if trigger.check(event_name, payload):
                trigger.fire(event_name, payload)
                fired.append(trigger.name)
        return fired
        
    def tick(self) -> List[str]:
        """
        Periodic tick processing TemporalTriggers.
        
        Returns:
            List of names of triggers that fired.
        """
        fired = []
        for trigger in self._temporal_triggers:
            if trigger.check():
                trigger.fire()
                fired.append(trigger.name)
        return fired
