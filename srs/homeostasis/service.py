"""HomeostasisService facade."""
from __future__ import annotations
from typing import Optional
from .config import HomeostasisConfig, default_config
from .events import EventID, MAJOR_SLOW_EVENTS
from .pulse import HormonePulse
from .backlog import DeferredBacklog, DeferredItem
from .motor import HomeostasisMotor, MotorSnapshot

class HomeostasisService:
    def __init__(self, config: Optional[HomeostasisConfig] = None):
        self.cfg = config or default_config()
        self.pulse = HormonePulse(self.cfg)
        self.backlog = DeferredBacklog(self.cfg)
        self.motor = HomeostasisMotor(self.cfg)
        self.last_snapshot: Optional[MotorSnapshot] = None
        self.event_log: list = []

    def on_heartbeat(self, dt: float = 1.0) -> MotorSnapshot:
        self.pulse.on_heartbeat(dt)
        self.backlog.age_all(dt)
        if hasattr(self.motor, "note_success_decay_fail"):
            self.motor.note_success_decay_fail()
        for oid in self.backlog.overdue_ids():
            self.event_log.append(("DEF.ITEM_OVERDUE", oid))
        return self.step(force_slow=False, trap=False)

    def on_event(self, event_id: str | EventID, *, trap: bool = False) -> MotorSnapshot:
        eid = event_id.value if isinstance(event_id, EventID) else str(event_id)
        self.pulse.apply_event(eid)
        self.event_log.append(eid)
        if eid in ("EXEC.NO_PROGRESS", "EXEC.LOOP_DETECTED", "EXEC.DEAD_END", "EXEC.TASK_FAILED", "EXEC.VERIFIER_FAIL"):
            self.motor.note_failure(1.0 if "LOOP" in eid or "DEAD" in eid else 0.5)
            if eid in ("EXEC.NO_PROGRESS", "EXEC.LOOP_DETECTED", "EXEC.DEAD_END"):
                self.motor.axes.progress = min(1.0, self.motor.axes.progress + 0.2)
        if eid in ("RES.TOKENS_EXHAUSTED", "RES.TOKENS_LOW", "RES.BUDGET_BLOCK"):
            self.motor.axes.resource = min(1.0, self.motor.axes.resource + 0.25)
        if eid == "OUT.BLOCK_CLEARED":
            self.motor.axes.resource = max(0.0, self.motor.axes.resource - 0.3)
        if eid == "EXEC.TASK_DONE":
            self.motor.axes.progress = 0.0
        if eid == "DEF.ITEM_DONE":
            self.backlog.complete()
        force_slow = eid in MAJOR_SLOW_EVENTS
        is_trap = trap or eid in ("EXEC.LOOP_DETECTED", "EXEC.DEAD_END")
        return self.step(force_slow=force_slow, trap=is_trap)

    def update_axes(self, **kwargs: float) -> None:
        self.motor.update_axes(**kwargs)

    def defer(self, kind: str, importance: float = 0.5, soft_deadline: float = 20.0, note: str = "", age: float = 0.0) -> DeferredItem:
        item = self.backlog.add(kind, importance, soft_deadline, note, age)
        self.on_event(EventID.DEF_ITEM_ADDED)
        return item

    def complete_deferred(self, item_id: Optional[str] = None) -> MotorSnapshot:
        self.backlog.complete(item_id)
        return self.on_event(EventID.DEF_ITEM_DONE)

    def step(self, force_slow: bool = False, trap: bool = False) -> MotorSnapshot:
        if self.motor.should_run_slow(force=force_slow):
            D_preview = self.motor.drive(self.pulse.state.tau_idle)
            self.motor.update_slow(self.pulse.state.S, D_preview)
        snap = self.motor.compute(
            S=self.pulse.state.S, G=self.pulse.state.G, S_def=self.backlog.S_def(),
            tau_idle=self.pulse.state.tau_idle, trap=trap, n_deferred=len(self.backlog.items),
        )
        self.last_snapshot = snap
        return snap

    def snapshot(self) -> dict:
        s = self.last_snapshot.to_dict() if self.last_snapshot else self.step().to_dict()
        s["backlog"] = self.backlog.snapshot()
        s["pulse"] = self.pulse.snapshot()
        return s

    def idle_tick(self) -> dict:
        snap = self.on_heartbeat()
        return {
            "status": "IDLE_TICK",
            "reason": "No external task; homeostasis tick",
            "homeostasis": snap.to_dict(),
            "revision_needed": snap.revision_needed,
            "mode": snap.mode,
            "break_loop": snap.break_loop,
        }
