"""Deferred intentions backlog — ages into S_def."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
import uuid
from config import HomeostasisConfig

@dataclass
class DeferredItem:
    kind: str
    importance: float = 0.5
    soft_deadline: float = 20.0
    age: float = 0.0
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    note: str = ""

    def pressure(self) -> float:
        v = max(0.0, min(1.0, self.importance))
        return v * min(1.0, self.age / max(self.soft_deadline, 1e-6))

class DeferredBacklog:
    def __init__(self, config: Optional[HomeostasisConfig] = None):
        self.cfg = config or HomeostasisConfig()
        self.items: List[DeferredItem] = []

    def add(self, kind: str, importance: float = 0.5, soft_deadline: float = 20.0, note: str = "", age: float = 0.0) -> DeferredItem:
        item = DeferredItem(kind=kind, importance=importance, soft_deadline=soft_deadline, age=age, note=note)
        self.items.append(item)
        return item

    def age_all(self, dt: float = 1.0) -> None:
        for it in self.items:
            it.age += dt

    def complete(self, item_id: Optional[str] = None) -> Optional[DeferredItem]:
        if not self.items:
            return None
        if item_id:
            for i, it in enumerate(self.items):
                if it.id == item_id:
                    return self.items.pop(i)
            return None
        self.items.sort(key=lambda x: -x.pressure())
        return self.items.pop(0)

    def S_def(self) -> float:
        raw = sum(self.cfg.c_def * it.pressure() for it in self.items)
        return max(0.0, min(self.cfg.S_def_max, raw))

    def overdue_ids(self) -> List[str]:
        return [it.id for it in self.items if it.age >= it.soft_deadline]

    def snapshot(self) -> dict:
        return {
            "n": len(self.items),
            "S_def": round(self.S_def(), 6),
            "items": [{"id": it.id, "kind": it.kind, "importance": it.importance, "age": it.age, "T": it.soft_deadline, "pressure": round(it.pressure(), 4), "note": it.note} for it in self.items],
        }
