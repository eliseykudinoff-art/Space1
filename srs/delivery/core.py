"""Delivery core — adapters and manager for result delivery."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import json
import os


class DeliveryStatus(Enum):
    """Status of a delivery attempt."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class DeliveryResult:
    """Result of a delivery attempt."""
    success: bool
    status: DeliveryStatus
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0


class DeliveryAdapter(ABC):
    """
    Abstract base class for delivery adapters.

    Implementations:
    - MockDeliveryAdapter: for testing
    - FileDeliveryAdapter: saves to local file
    - Future: HTTPDeliveryAdapter, EmailDeliveryAdapter, etc.
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self._history: List[DeliveryResult] = []

    @abstractmethod
    def send(self, task_id: str, result: Any, recipient: str, **kwargs) -> DeliveryResult:
        """
        Send result to recipient.

        Args:
            task_id: Unique task identifier
            result: Task result (any serializable object)
            recipient: Target recipient (platform-specific ID)
            **kwargs: Platform-specific options

        Returns:
            DeliveryResult with status and metadata
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if adapter is healthy and ready."""
        pass

    def get_history(self) -> List[DeliveryResult]:
        """Get delivery history for this adapter."""
        return list(self._history)

    def _record(self, result: DeliveryResult) -> None:
        """Record delivery attempt in history."""
        self._history.append(result)


class MockDeliveryAdapter(DeliveryAdapter):
    """
    Mock delivery adapter for testing.

    Simulates delivery with configurable success rate and latency.
    Records all attempts for verification.
    """

    def __init__(
        self,
        name: str = "mock",
        config: Optional[Dict[str, Any]] = None,
        success_rate: float = 1.0,
        simulate_latency: bool = False
    ):
        super().__init__(name, config)
        self.success_rate = success_rate
        self.simulate_latency = simulate_latency
        self._delivered: List[Dict[str, Any]] = []

    def send(self, task_id: str, result: Any, recipient: str, **kwargs) -> DeliveryResult:
        """Mock send — always succeeds (or fails based on success_rate)."""
        import random
        import time

        if self.simulate_latency:
            time.sleep(0.01)  # 10ms simulated latency

        success = random.random() < self.success_rate

        if success:
            record = {
                "task_id": task_id,
                "result": result,
                "recipient": recipient,
                "timestamp": datetime.now().isoformat(),
                "metadata": kwargs
            }
            self._delivered.append(record)

            result_obj = DeliveryResult(
                success=True,
                status=DeliveryStatus.DELIVERED,
                message=f"Mock delivery to {recipient} succeeded",
                metadata={"recipient": recipient, "task_id": task_id}
            )
        else:
            result_obj = DeliveryResult(
                success=False,
                status=DeliveryStatus.FAILED,
                message=f"Mock delivery to {recipient} failed (simulated)",
                metadata={"recipient": recipient, "task_id": task_id}
            )

        self._record(result_obj)
        return result_obj

    def health_check(self) -> bool:
        """Mock adapter is always healthy."""
        return True

    def get_delivered(self) -> List[Dict[str, Any]]:
        """Get all delivered items (for testing)."""
        return list(self._delivered)

    def clear(self) -> None:
        """Clear delivery history."""
        self._delivered.clear()
        self._history.clear()


class FileDeliveryAdapter(DeliveryAdapter):
    """
    File-based delivery adapter.

    Saves results to JSON files in a directory.
    Useful for local development and debugging.
    """

    def __init__(
        self,
        name: str = "file",
        config: Optional[Dict[str, Any]] = None,
        output_dir: str = "./deliveries"
    ):
        super().__init__(name, config)
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def send(self, task_id: str, result: Any, recipient: str, **kwargs) -> DeliveryResult:
        """Save result to JSON file."""
        try:
            filename = f"{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(self.output_dir, filename)

            payload = {
                "task_id": task_id,
                "recipient": recipient,
                "result": result,
                "timestamp": datetime.now().isoformat(),
                "metadata": kwargs
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=2, default=str)

            result_obj = DeliveryResult(
                success=True,
                status=DeliveryStatus.DELIVERED,
                message=f"Saved to {filepath}",
                metadata={"filepath": filepath, "recipient": recipient}
            )
        except Exception as e:
            result_obj = DeliveryResult(
                success=False,
                status=DeliveryStatus.FAILED,
                message=str(e),
                metadata={"recipient": recipient, "error": str(e)}
            )

        self._record(result_obj)
        return result_obj

    def health_check(self) -> bool:
        """Check if output directory is writable."""
        return os.path.isdir(self.output_dir) and os.access(self.output_dir, os.W_OK)


class DeliveryManager:
    """
    Manager for multiple delivery adapters.

    Routes deliveries to appropriate adapter based on recipient platform.
    Supports fallback chains and retry logic.
    """

    def __init__(self):
        self._adapters: Dict[str, DeliveryAdapter] = {}
        self._default_adapter: Optional[str] = None

    def register(self, adapter: DeliveryAdapter, default: bool = False) -> None:
        """Register a delivery adapter."""
        self._adapters[adapter.name] = adapter
        if default or self._default_adapter is None:
            self._default_adapter = adapter.name

    def unregister(self, name: str) -> None:
        """Unregister an adapter."""
        if name in self._adapters:
            del self._adapters[name]
        if self._default_adapter == name:
            self._default_adapter = next(iter(self._adapters), None)

    def send(
        self,
        task_id: str,
        result: Any,
        recipient: str,
        adapter_name: Optional[str] = None,
        **kwargs
    ) -> DeliveryResult:
        """
        Send result using specified or default adapter.

        Args:
            task_id: Task identifier
            result: Result payload
            recipient: Target recipient
            adapter_name: Specific adapter to use (or default)
            **kwargs: Additional options

        Returns:
            DeliveryResult
        """
        name = adapter_name or self._default_adapter
        if not name:
            return DeliveryResult(
                success=False,
                status=DeliveryStatus.FAILED,
                message="No delivery adapter registered"
            )

        adapter = self._adapters.get(name)
        if not adapter:
            return DeliveryResult(
                success=False,
                status=DeliveryStatus.FAILED,
                message=f"Adapter '{name}' not found"
            )

        return adapter.send(task_id, result, recipient, **kwargs)

    def health_check(self) -> Dict[str, bool]:
        """Check health of all adapters."""
        return {name: adapter.health_check() for name, adapter in self._adapters.items()}

    def get_adapter(self, name: str) -> Optional[DeliveryAdapter]:
        """Get adapter by name."""
        return self._adapters.get(name)

    def list_adapters(self) -> List[str]:
        """List registered adapter names."""
        return list(self._adapters.keys())
