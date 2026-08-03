"""Homeostasis package — hormone pulse + motor (Space1). Standalone branch."""
try:
    from .config import HomeostasisConfig, default_config
    from .events import EventID
    from .pulse import HormonePulse
    from .backlog import DeferredBacklog, DeferredItem
    from .motor import HomeostasisMotor, MotorSnapshot
    from .service import HomeostasisService
except ImportError:
    from config import HomeostasisConfig, default_config
    from events import EventID
    from pulse import HormonePulse
    from backlog import DeferredBacklog, DeferredItem
    from motor import HomeostasisMotor, MotorSnapshot
    from service import HomeostasisService

__all__ = [
    "HomeostasisConfig",
    "default_config",
    "EventID",
    "HormonePulse",
    "DeferredBacklog",
    "DeferredItem",
    "HomeostasisMotor",
    "MotorSnapshot",
    "HomeostasisService",
]
