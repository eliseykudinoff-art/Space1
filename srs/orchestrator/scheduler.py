"""
AIOS Scheduler Kernel Module.

Reference: 04_ARCHITECTURE.md (Part I / Part IV.1).
Handles prioritized task queues, dispatch scheduling, and resource allocation.
"""

import json
import os
from typing import List, Dict, Any, Optional
from ..models.task import Task, TaskStatus, TaskPriority
from datetime import datetime


def deserialize_task(d: dict) -> Task:
    deadline = datetime.fromisoformat(d["deadline"]) if d["deadline"] else None
    created_at = datetime.fromisoformat(d["created_at"]) if d["created_at"] else datetime.now()
    started_at = datetime.fromisoformat(d["started_at"]) if d["started_at"] else None
    completed_at = datetime.fromisoformat(d["completed_at"]) if d["completed_at"] else None
    
    priority = TaskPriority[d["priority"]] if d["priority"] in TaskPriority.__members__ else TaskPriority.MEDIUM
    status = TaskStatus(d["status"]) if d["status"] in [e.value for e in TaskStatus] else TaskStatus.PENDING
    
    task = Task(
        id=d["id"],
        title=d["title"],
        description=d["description"],
        deadline=deadline,
        priority=priority,
        status=status,
        source=d.get("source", "MARKETPLACE"),
        estimated_hours=d.get("estimated_hours", 1.0),
        tags=d.get("tags", []),
    )
    task.created_at = created_at
    task.started_at = started_at
    task.completed_at = completed_at
    task.urgency_score = d.get("urgency_score", 0.5)
    task.slack_time = d.get("slack_time", 24.0)
    return task


class AIOSScheduler:
    """
    AIOSScheduler.
    Manages a prioritised queue of tasks. Tasks with source='OWNER_DIRECT' 
    bypass the queue order and are processed with highest priority.
    """
    
    def __init__(self, filepath: str = "scheduler_queue.json"):
        self.filepath = filepath
        self._queue: List[Task] = []
        self._load_queue()
        
    def _load_queue(self) -> None:
        """Load the persisted task queue from JSON file if it exists."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._queue = [deserialize_task(item) for item in data]
            except Exception:
                self._queue = []
                
    def _save_queue(self) -> None:
        """Serialize and persist the task queue atomically to disk."""
        temp_filepath = self.filepath + ".tmp"
        try:
            with open(temp_filepath, "w", encoding="utf-8") as f:
                json.dump([item.to_dict() for item in self._queue], f, indent=2)
            os.replace(temp_filepath, self.filepath)
        except Exception:
            if os.path.exists(temp_filepath):
                try:
                    os.remove(temp_filepath)
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"Suppressed error: {e}")

    def add_task(self, task: Task) -> None:
        """Add a task to the queue and save to disk."""
        self._queue.append(task)
        self._save_queue()
        
    def pop_next_task(self) -> Optional[Task]:
        """
        Pop the next high-priority task and update the disk file.
        OWNER_DIRECT tasks always override regular marketplace queue order.
        Within each source group, tasks are sorted by priority (descending).
        """
        if not self._queue:
            return None
        
        # Two-level sort:
        # 1. OWNER_DIRECT comes before MARKETPLACE (bool sort: False < True)
        # 2. Within each group, higher priority.value comes first
        self._queue.sort(key=lambda t: (
            t.metadata.get("source", "MARKETPLACE") != "OWNER_DIRECT",
            -(t.priority.value if hasattr(t.priority, "value") else float(t.priority))
        ))
        
        res_task = self._queue.pop(0)
        self._save_queue()
        return res_task
    def list_queue(self) -> List[Task]:
        """Return the current task queue."""
        return list(self._queue)
        
    def clear(self) -> None:
        """Clear all tasks from scheduler queue."""
        self._queue.clear()
        if os.path.exists(self.filepath):
            try:
                os.remove(self.filepath)
            except Exception:
                pass
