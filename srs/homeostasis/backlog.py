"""Deferred intentions backlog — ages into S_def."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
import uuid
from .config import HomeostasisConfig


@dataclass
class DeferredItem:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    kind: str = "generic"
    importance: float = 0.5
    soft_deadline: float = 20.0
    age: float = 0.0
    note: str = ""


class DeferredBacklog:
    def __init__(self, cfg: Optional[HomeostasisConfig] = None):
        self.cfg = cfg or HomeostasisConfig()
        self.items: List[DeferredItem] = []

    def add(self, kind: str, importance: float = 0.5, soft_deadline: float = 20.0, note: str = "", age: float = 0.0) -> DeferredItem:
        item = DeferredItem(kind=kind, importance=importance, soft_deadline=soft_deadline, note=note, age=age)
        self.items.append(item)
        return item

    def complete(self, item_id: Optional[str] = None) -> None:
        if not self.items:
            return
        if item_id is None:
            self.items.pop(0)
            return
        self.items = [i for i in self.items if i.id != item_id]

    def age_all(self, dt: float = 1.0) -> None:
        for i in self.items:
            i.age += dt

    def overdue_ids(self) -> List[str]:
        return [i.id for i in self.items if i.age >= i.soft_deadline]

    def S_def(self) -> float:
        if not self.items:
            return 0.0
        total = 0.0
        for i in self.items:
            overdue = max(0.0, i.age - i.soft_deadline) / max(1.0, i.soft_deadline)
            total += i.importance * (0.3 + 0.7 * min(1.0, i.age / max(1.0, i.soft_deadline)) + 0.2 * min(1.0, overdue))
        return max(0.0, min(1.0, total / max(1, len(self.items))))

    def snapshot(self) -> dict:
        return {"n": len(self.items), "S_def": self.S_def(), "items": [{"id": i.id, "kind": i.kind, "age": i.age} for i in self.items]}
