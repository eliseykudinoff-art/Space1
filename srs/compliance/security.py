"""
AIOS Access Manager & Security Kernel Module.

Reference: 04_ARCHITECTURE.md (Part VI / Part IV.6).
Manages human-in-the-loop approvals, rule enforcement, and security verification.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from ..compliance.core import Action, Rule, GammaVeto


class AIOSAccessManager:
    """
    AIOSAccessManager.
    Coordinates security compliance, human-in-the-loop approvals, and structured security auditing.
    """
    
    def __init__(
        self,
        veto_system: Optional[GammaVeto] = None,
        max_queue_size: int = 100,
        pending_ttl_hours: float = 24.0,
        persist_path: Optional[str] = None,
    ):
        self.veto_system = veto_system or GammaVeto()
        self._human_approvals: Dict[str, bool] = {}
        self._approval_queue: List[Dict[str, Any]] = []
        self._audit_log: List[Dict[str, Any]] = []
        self._max_queue_size = max_queue_size
        self._pending_ttl_seconds = pending_ttl_hours * 3600
        self._persist_path = persist_path

        # Load persisted state if available
        if persist_path:
            self._load_state()
        

    def _cleanup_expired(self) -> None:
        """Remove expired PENDING requests and old APPROVED/REJECTED entries."""
        now = datetime.now()
        cutoff = now.timestamp() - self._pending_ttl_seconds

        # Remove expired PENDING (TTL)
        self._approval_queue = [
            req for req in self._approval_queue
            if not (
                req["status"] == "PENDING"
                and datetime.fromisoformat(req["timestamp"]).timestamp() < cutoff
            )
        ]

        # Enforce max queue size (FIFO eviction of oldest — keep last N)
        if len(self._approval_queue) > self._max_queue_size:
            self._approval_queue = self._approval_queue[-self._max_queue_size:]

    def clear_approved(self) -> int:
        """Remove all APPROVED and REJECTED entries from queue. Returns count removed."""
        before = len(self._approval_queue)
        self._approval_queue = [
            req for req in self._approval_queue
            if req["status"] == "PENDING"
        ]
        removed = before - len(self._approval_queue)
        self._save_state()
        return removed

    def _save_state(self) -> None:
        """Persist queue and audit log to disk."""
        if not self._persist_path:
            return
        import json
        state = {
            "human_approvals": self._human_approvals,
            "approval_queue": self._approval_queue,
            "audit_log": self._audit_log[-1000:],  # Keep last 1000 entries
        }
        with open(self._persist_path, 'w') as f:
            json.dump(state, f, default=str)

    def _load_state(self) -> None:
        """Load persisted state from disk."""
        import json, os
        if not os.path.exists(self._persist_path):
            return
        try:
            with open(self._persist_path, 'r') as f:
                state = json.load(f)
            self._human_approvals = state.get("human_approvals", {})
            self._approval_queue = state.get("approval_queue", [])
            self._audit_log = state.get("audit_log", [])
        except (json.JSONDecodeError, IOError):
            pass  # Start fresh if corrupt
    def check_hard_veto(self, action: Action) -> bool:
        """Check if an action violates any registered hard security rules."""
        return self.veto_system.evaluate(action)
        
    def requires_human_approval(self, action: Action, budget_limit: float = 100.0) -> bool:
        """
        True if action resource cost exceeds limit or safety requires it.
        """
        requires = False
        if action.resource_cost > budget_limit:
            requires = True
        if action.params.get("sensitive", False):
            requires = True
            
        if requires:
            # Track in the active human approval queue
            req = {
                "action_id": action.name,
                "timestamp": datetime.now().isoformat(),
                "status": "PENDING",
                "action_details": {
                    "name": action.name,
                    "resource_cost": action.resource_cost,
                    "params": action.params
                }
            }
            self._approval_queue.append(req)
            self._cleanup_expired()
            self._save_state()
            
        return requires
        
    def request_human_approval(self, action_id: str, approved: bool, reason: str = "human_decision") -> None:
        """Record human approval decision in queue and audit log."""
        self._human_approvals[action_id] = approved
        
        # Update queue status if present
        for req in self._approval_queue:
            if req["action_id"] == action_id:
                req["status"] = "APPROVED" if approved else "REJECTED"
                
        # Append to the audit log
        log_entry = {
            "action_id": action_id,
            "timestamp": datetime.now().isoformat(),
            "approved": approved,
            "decision_maker": "human",
            "reason": reason
        }
        self._audit_log.append(log_entry)
        self._save_state()
        
    def is_approved_by_human(self, action_id: str) -> bool:
        """Check if human approval was obtained."""
        return self._human_approvals.get(action_id, False)

    def list_pending_approvals(self) -> List[Dict[str, Any]]:
        """Return list of currently pending approval requests."""
        return [r for r in self._approval_queue if r["status"] == "PENDING"]

    def list_security_audit_log(self) -> List[Dict[str, Any]]:
        """Return the security audit logs."""
        return list(self._audit_log)
