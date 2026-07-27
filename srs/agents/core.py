"""
Specialist Subroutines and Single-Brain Agent Coordinator per 04_ARCHITECTURE.md §V.

Per 03_PIPELINE_MATH.md §VII.1 and 04_ARCHITECTURE.md §V:
- Role-based multi-agent (Scout/Worker/Finance) is REJECTED
- Sub-agent = declaration (name, tool allowlist, call condition on atomic action)
- Single-level hierarchy (sub-agent does not spawn sub-agents)
- Manifest pattern replaces persistent role classes

Reference: 04_ARCHITECTURE.md §V, 03_PIPELINE_MATH.md §VII.1
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

from ..models.agents import Agent, AgentCapabilities, AgentMetrics, AgentStatus
from ..models.task import Task, TaskStatus
from ..utility import compute_phi, compute_psi, score_action


# =============================================================================
# Functional Sub-Agent Manifest (04_ARCHITECTURE.md §V)
# =============================================================================

@dataclass
class SubAgentManifest:
    """
    Manifest for a functional sub-agent per 04_ARCHITECTURE.md §V.
    
    A sub-agent is a declaration (not a persistent object):
    - name: identifier for the sub-agent
    - tool_allowlist: set of tools this sub-agent can use
    - action_type: type of atomic action this sub-agent handles
    - execute: the actual execution function
    """
    name: str
    tool_allowlist: Set[str]
    action_type: str  # e.g., "lead_evaluation", "task_execution", "invoice_processing"
    execute: Callable[..., Dict[str, Any]]
    description: str = ""
    
    def can_handle(self, action_type: str) -> bool:
        """Check if this sub-agent can handle the given action type."""
        return self.action_type == action_type


@dataclass
class SubAgentRegistry:
    """
    Registry of functional sub-agents.
    
    Single-level hierarchy: sub-agents do not spawn other sub-agents.
    All sub-agents are registered with manifests.
    """
    def __init__(self):
        self._manifests: Dict[str, SubAgentManifest] = {}
        self._by_action_type: Dict[str, SubAgentManifest] = {}
    
    def register(self, manifest: SubAgentManifest) -> None:
        """Register a sub-agent manifest."""
        self._manifests[manifest.name] = manifest
        self._by_action_type[manifest.action_type] = manifest
    
    def get(self, name: str) -> Optional[SubAgentManifest]:
        """Get manifest by name."""
        return self._manifests.get(name)
    
    def find_for_action(self, action_type: str) -> Optional[SubAgentManifest]:
        """Find the sub-agent that handles this action type."""
        return self._by_action_type.get(action_type)
    
    def list_all(self) -> List[SubAgentManifest]:
        """List all registered sub-agent manifests."""
        return list(self._manifests.values())


# =============================================================================
# Sub-Agent Implementations
# =============================================================================

def lead_evaluation_execute(task: Task, agent: Agent, **kwargs) -> Dict[str, Any]:
    """Execute lead evaluation (scout function)."""
    phi = compute_phi(task, agent)
    psi = compute_psi(task, agent)
    
    bid_threshold = 5.0
    risk_veto_limit = 0.7
    
    decision = "BID"
    reason = "Profitable and low risk"
    
    if psi > risk_veto_limit:
        decision = "DECLINE"
        reason = f"Risk {psi:.2f} exceeds threshold {risk_veto_limit}"
    elif phi < bid_threshold:
        decision = "DECLINE"
        reason = f"Expected profit {phi:.2f} below minimum {bid_threshold}"
    
    return {
        "phi": phi,
        "psi": psi,
        "decision": decision,
        "reason": reason,
    }


def task_execution_execute(task: Task, agent: Agent, **kwargs) -> Dict[str, Any]:
    """Execute task (worker function)."""
    if task.status != TaskStatus.IN_PROGRESS:
        task.start()
    
    llm_quality = agent.capabilities.llm_quality
    complexity_modifier = kwargs.get("complexity_modifier", 1.0)
    expected_quality = max(0.0, min(1.0, llm_quality * (1.1 - 0.1 * complexity_modifier)))
    
    target_quality = task.metadata.get("quality_requirement", 0.7)
    attempts = 1
    
    if expected_quality < target_quality:
        expected_quality = min(1.0, expected_quality + 0.1)
        attempts += 1
    
    if expected_quality >= target_quality:
        task.complete()
        status = "completed"
    else:
        task.fail(reason="Failed to satisfy quality threshold")
        status = "failed"
    
    return {
        "status": status,
        "quality": expected_quality,
        "attempts": attempts,
        "timestamp": datetime.now().isoformat()
    }


def invoice_processing_execute(task: Task, agent: Agent, **kwargs) -> Dict[str, Any]:
    """Execute invoice processing (finance function)."""
    if task.status != TaskStatus.COMPLETED:
        return {"success": False, "error": "Task is not completed"}
    
    reward = getattr(task, "revenue", None) or 0.0
    agent.metrics.balance += reward
    agent.metrics.total_earned += reward
    
    return {
        "success": True,
        "earned": reward,
        "new_balance": agent.metrics.balance,
        "timestamp": datetime.now().isoformat()
    }


def budget_enforcement_execute(agent: Agent, budget_limit: float, **kwargs) -> Dict[str, Any]:
    """Execute budget enforcement (finance function)."""
    current_balance = agent.metrics.balance
    if current_balance < budget_limit:
        agent.metrics.token_budget = max(10.0, agent.metrics.token_budget * 0.5)
    
    return {
        "new_token_budget": agent.metrics.token_budget,
        "balance": current_balance,
        "budget_limit": budget_limit,
    }


# =============================================================================
# Sub-Agent Registry (pre-populated with canonical actions)
# =============================================================================

def create_sub_agent_registry() -> SubAgentRegistry:
    """Create a registry with all canonical sub-agent manifests."""
    registry = SubAgentRegistry()
    
    # Lead Evaluation (Scout)
    registry.register(SubAgentManifest(
        name="LeadEvaluator",
        tool_allowlist={"web_search", "api_call", "data_analysis"},
        action_type="lead_evaluation",
        execute=lead_evaluation_execute,
        description="Evaluates leads based on risk-to-profit expectations"
    ))
    
    # Task Execution (Worker)
    registry.register(SubAgentManifest(
        name="TaskExecutor",
        tool_allowlist={"code_editor", "llm_call", "verification", "correction_loop"},
        action_type="task_execution",
        execute=task_execution_execute,
        description="Executes tasks and runs correction loops for quality"
    ))
    
    # Invoice Processing (Finance)
    registry.register(SubAgentManifest(
        name="InvoiceProcessor",
        tool_allowlist={"payment_api", "balance_update", "ledger"},
        action_type="invoice_processing",
        execute=invoice_processing_execute,
        description="Processes invoices and updates balance"
    ))
    
    # Budget Enforcement (Finance)
    registry.register(SubAgentManifest(
        name="BudgetEnforcer",
        tool_allowlist={"token_budget_update", "alert_system"},
        action_type="budget_enforcement",
        execute=budget_enforcement_execute,
        description="Dynamically adjusts token budgets based on balance"
    ))
    
    return registry


# =============================================================================
# Single-Brain Coordinator (UnifiedCognitiveAgent)
# =============================================================================

class UnifiedCognitiveAgent:
    """
    Single-Brain Agent Coordinator per 04_ARCHITECTURE.md §V.
    
    The true single-brain coordinator for Space1.
    All decision-making happens here; sub-agents are functional declarations
    for atomic actions, not independent cognitive entities.
    """
    
    def __init__(self, core_agent: Agent):
        self.core_agent = core_agent
        self.sub_agents = create_sub_agent_registry()

    def __getattr__(self, name: str):
        """Delegate attribute access to core_agent."""
        return getattr(self.core_agent, name)
    
    def dispatch(self, action_type: str, **kwargs) -> Dict[str, Any]:
        """
        Dispatch an action to the appropriate sub-agent manifest.
        
        Single-level hierarchy: we go directly to the manifest, no cascading.
        """
        manifest = self.sub_agents.find_for_action(action_type)
        if manifest is None:
            return {"error": f"No sub-agent for action type: {action_type}"}
        
        return manifest.execute(agent=self.core_agent, **kwargs)
    
    def list_capabilities(self) -> List[str]:
        """List all available action types."""
        return [m.action_type for m in self.sub_agents.list_all()]


# =============================================================================
# Legacy Backward Compatibility (kept for tests)
# =============================================================================

class BaseSpecialistAgent:
    """Legacy base agent class. Obsolete but kept for tests compatibility."""
    def __init__(self, name: str, core_agent: Agent):
        self.name = name
        self.core_agent = core_agent


class SpecialistSubroutine:
    """Legacy specialist subroutine. Redirects to manifest-based execution."""
    def __init__(self, core_agent: Agent, action_type: str):
        self.core_agent = core_agent
        self.action_type = action_type
        self._brain = UnifiedCognitiveAgent(core_agent)
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        return self._brain.dispatch(self.action_type, **kwargs)
    
    # Legacy method aliases for backward compatibility with tests
    def evaluate_lead(self, lead, ctx=None, **kwargs) -> Dict[str, Any]:
        """Legacy compatibility: evaluate a lead (maps to task execution)."""
        return self._brain.dispatch("lead_evaluation", task=lead, context=ctx or {}, **kwargs)
    
    def execute_and_assess(self, task, **kwargs) -> Dict[str, Any]:
        """Legacy compatibility: execute task and self-assess."""
        return self._brain.dispatch("task_execution", task=task, **kwargs)
    
    def process_invoice(self, task) -> Dict[str, Any]:
        """Legacy compatibility: process an invoice."""
        return self._brain.dispatch("invoice_processing", task=task)
    
    async def run_role_async(self, task) -> Dict[str, Any]:
        """Legacy compatibility: async execution."""
        return self.execute(task=task)


class ScoutSpecialist(SpecialistSubroutine):
    """Legacy ScoutSpecialist. Redirects to LeadEvaluator."""
    def __init__(self, core_agent: Agent):
        super().__init__(core_agent, "lead_evaluation")
        self.name = "Scout"


class WorkerSpecialist(SpecialistSubroutine):
    """Legacy WorkerSpecialist. Redirects to TaskExecutor."""
    def __init__(self, core_agent: Agent):
        super().__init__(core_agent, "task_execution")
        self.name = "Worker"


class FinanceSpecialist(SpecialistSubroutine):
    """Legacy FinanceSpecialist. Redirects to InvoiceProcessor/BudgetEnforcer."""
    def __init__(self, core_agent: Agent):
        super().__init__(core_agent, "invoice_processing")
        self.name = "Finance"
    
    def enforce_budget_cuts(self, budget_limit: float) -> Dict[str, Any]:
        """Legacy compatibility: enforce budget cuts."""
        return self._brain.dispatch("budget_enforcement", budget_limit=budget_limit)


# Legacy wrapper classes (deprecated)
ScoutAgent = ScoutSpecialist
WorkerAgent = WorkerSpecialist
FinanceAgent = FinanceSpecialist
