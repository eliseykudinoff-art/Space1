"""Delivery module — отправка результатов клиенту.

Per 09_ECOSYSTEM_AND_INTEROP.md §V.2:
- AP2-like protocol for result delivery
- Abstract adapter pattern for multiple platforms
- Mock adapter for testing
"""

from .core import (
    DeliveryAdapter,
    MockDeliveryAdapter,
    FileDeliveryAdapter,
    DeliveryManager,
    DeliveryResult,
    DeliveryStatus,
)

__all__ = [
    "DeliveryAdapter",
    "MockDeliveryAdapter", 
    "FileDeliveryAdapter",
    "DeliveryManager",
    "DeliveryResult",
    "DeliveryStatus",
]
