"""
Market Protocols — 10 protocols for external environment interaction (06_EXTERNAL_ENVIRONMENT.md Часть II).

Protocols:
  II.1  Dispute Resolution
  II.2  Payment Risk
  II.3  Platform Compliance & Account Risk
  II.4  Account Suspension Response
  II.5  Competitor Dumping Response
  II.6  Opportunity Arbitration
  II.7  Client Boundary Escalation
  II.8  Reputation Damage Response
  II.9  Client Exit
  II.10 Platform Diversification (Post-MVP)

Each protocol: trigger -> steps -> decision points -> outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta


class ProtocolOutcome(Enum):
    CONTINUE = "continue"      # Proceed to next step
    RESOLVED = "resolved"      # Protocol completed successfully
    ESCALATE = "escalate"      # Escalate to higher level
    EXIT = "exit"              # Terminate relationship/process
    DEFER = "defer"            # Postpone decision


class ProtocolStep(Enum):
    DIRECT_RESOLUTION = "direct_resolution"
    PLATFORM_MEDIATION = "platform_mediation"
    ACCEPT_RECOMMENDATION = "accept_recommendation"
    ARBITRATION = "arbitration"
    NOTIFY_CLIENTS = "notify_clients"
    APPEAL = "appeal"
    DOCUMENT = "document"
    REVIEW_TERMS = "review_terms"
    WALK_AWAY = "walk_away"
    SET_BOUNDARY = "set_boundary"
    FORMAL_REVIEW = "formal_review"
    PRIVATE_CONTACT = "private_contact"
    PUBLIC_RESPONSE = "public_response"
    FORMAL_NOTICE = "formal_notice"
    HANDOVER = "handover"


@dataclass
class ProtocolState:
    """Current state of a running protocol."""
    protocol_name: str = ""
    step: ProtocolStep = ProtocolStep.DIRECT_RESOLUTION
    history: List[Dict[str, Any]] = field(default_factory=list)
    outcome: Optional[ProtocolOutcome] = None
    started_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    iteration: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "protocol_name": self.protocol_name,
            "step": self.step.value,
            "iteration": self.iteration,
            "history": self.history,
            "outcome": self.outcome.value if self.outcome else None,
            "started_at": self.started_at.isoformat(),
            "metadata": self.metadata,
        }


# =============================================================================
# II.1 Dispute Resolution Protocol
# =============================================================================

class DisputeProtocol:
    """
    §II.1 — Two-stage mediation -> arbitration.
    Trigger: client initiated dispute OR agent cannot reach agreement after recovery tactics.
    """

    TAU_DIRECT_DEFAULT: timedelta = timedelta(days=7)  # tau_direct — configurable

    def __init__(self, tau_direct: Optional[timedelta] = None):
        self.tau_direct = tau_direct or self.TAU_DIRECT_DEFAULT

    def run(self, state: ProtocolState, context: Dict[str, Any]) -> ProtocolState:
        """Execute dispute resolution steps."""
        step = state.step

        if step == ProtocolStep.DIRECT_RESOLUTION:
            # Step 1: Direct resolution (recovery tactics)
            # Hard-rule: respond within fixed window, accountable tone
            state.history.append({"step": "direct_resolution", "action": "recovery_tactics", "timestamp": datetime.now().isoformat()})
            # If resolved by recovery tactics -> RESOLVED
            if context.get("resolved_by_recovery", False):
                state.outcome = ProtocolOutcome.RESOLVED
                return state
            # If timeout exceeded -> move to mediation
            dispute_started = context.get("dispute_started_at", datetime.now())
            if datetime.now() - dispute_started > self.tau_direct:
                state.step = ProtocolStep.PLATFORM_MEDIATION
            else:
                state.outcome = ProtocolOutcome.DEFER
            return state

        elif step == ProtocolStep.PLATFORM_MEDIATION:
            # Step 2: Platform mediation
            # Form structured summary: chronology, expected vs actual, scope changes
            state.history.append({"step": "platform_mediation", "action": "structured_summary", "timestamp": datetime.now().isoformat()})
            # Mediator recommendation received?
            if context.get("mediator_recommendation") is not None:
                state.step = ProtocolStep.ACCEPT_RECOMMENDATION
            else:
                state.outcome = ProtocolOutcome.DEFER
            return state

        elif step == ProtocolStep.ACCEPT_RECOMMENDATION:
            # Step 3: Accept/reject recommendation
            # Decision: U(accept) vs U(arbitrage) * P(win) - C_arbitration
            recommendation = context.get("mediator_recommendation")
            u_accept = context.get("u_accept", 0.0)
            u_arbitrage = context.get("u_arbitrage", 0.0)
            p_win = context.get("p_win_arbitrage", 0.5)
            c_arbitration = context.get("c_arbitration", 0.0)

            u_arbitrage_expected = u_arbitrage * p_win - c_arbitration

            if u_accept >= u_arbitrage_expected:
                state.outcome = ProtocolOutcome.RESOLVED
                state.history.append({"step": "accept_recommendation", "decision": "accept", "timestamp": datetime.now().isoformat()})
            else:
                state.step = ProtocolStep.ARBITRATION
            return state

        elif step == ProtocolStep.ARBITRATION:
            # Step 4: Arbitration (formal, binding)
            # Hard-rule: comply with arbitration decision (Gamma_hard)
            state.history.append({"step": "arbitration", "action": "formal_arbitration", "timestamp": datetime.now().isoformat()})
            state.outcome = ProtocolOutcome.RESOLVED
            return state

        return state


# =============================================================================
# II.2 Payment Risk Protocol
# =============================================================================

class PaymentRiskProtocol:
    """
    §II.2 — Payment risk profiling and escalation.
    Not a standalone protocol from scratch — specialization of II.1 Step 1 for non-payment.
    """

    TAU_PAYMENT_DEFAULT: timedelta = timedelta(days=14)

    def __init__(self, tau_payment: Optional[timedelta] = None):
        self.tau_payment = tau_payment or self.TAU_PAYMENT_DEFAULT

    def check_payment_terms(self, ccrs: float) -> Dict[str, Any]:
        """Return payment structure recommendation based on CCRS zone."""
        from ..client_psychometrics import payment_terms_from_ccrs
        return payment_terms_from_ccrs(ccrs)

    def run(self, state: ProtocolState, context: Dict[str, Any]) -> ProtocolState:
        """Check for overdue milestone and escalate to dispute protocol if needed."""
        milestone_due = context.get("milestone_due_date")
        last_payment_response = context.get("last_payment_response")

        if milestone_due and last_payment_response:
            overdue = datetime.now() - last_payment_response
            if overdue > self.tau_payment:
                # Auto-escalate to dispute protocol Step 1
                state.step = ProtocolStep.DIRECT_RESOLUTION
                state.metadata["escalation_reason"] = "payment_overdue"
                state.metadata["overdue_days"] = overdue.days
                return state

        state.outcome = ProtocolOutcome.DEFER
        return state


# =============================================================================
# II.3 Platform Compliance Protocol
# =============================================================================

class PlatformComplianceProtocol:
    """
    §II.3 — Platform compliance and account risk.
    Hard-rules:
      - Use ONLY built-in platform communication channel
      - NEVER open a new account when current is flagged
    """

    def check_hard_rules(self, context: Dict[str, Any]) -> List[str]:
        """Check hard compliance rules. Returns list of violations."""
        violations = []
        if context.get("used_external_channel", False):
            violations.append("External communication channel used — violates platform policy")
        if context.get("opened_new_account_while_flagged", False):
            violations.append("New account opened while current account flagged — automatic suspension risk")
        return violations

    def compute_platform_risk_score(
        self,
        consistency_score: float,      # Location/IP consistency
        behavioral_score: float,       # Behavioral biometrics
        complaint_rate: float,         # Complaint frequency
        account_age_days: int,
    ) -> float:
        """
        Compute PlatformRiskScore per §II.3.
        w1*consistency + w2*behavioral + w3*complaint_rate + w4*age_factor
        """
        # Age factor: newer accounts are riskier
        age_factor = max(0.0, 1.0 - account_age_days / 365.0)
        # Weights (not calibrated — [O] parameters)
        w1, w2, w3, w4 = 0.3, 0.3, 0.25, 0.15
        score = w1 * (1.0 - consistency_score) + w2 * (1.0 - behavioral_score) + w3 * complaint_rate + w4 * age_factor
        return min(1.0, score)

    def run(self, state: ProtocolState, context: Dict[str, Any]) -> ProtocolState:
        """Run compliance check."""
        violations = self.check_hard_rules(context)
        if violations:
            state.outcome = ProtocolOutcome.ESCALATE
            state.metadata["violations"] = violations
            state.history.append({"step": "compliance_check", "violations": violations})
            return state

        # Compute risk score
        prs = self.compute_platform_risk_score(
            context.get("consistency_score", 1.0),
            context.get("behavioral_score", 1.0),
            context.get("complaint_rate", 0.0),
            context.get("account_age_days", 365),
        )
        state.metadata["platform_risk_score"] = prs

        if prs > 0.7:
            state.outcome = ProtocolOutcome.ESCALATE
        else:
            state.outcome = ProtocolOutcome.RESOLVED
        return state


# =============================================================================
# II.4 Account Suspension Response Protocol
# =============================================================================

class AccountSuspensionProtocol:
    """
    §II.4 — Response to account suspension.
    Immediate: H -> CRITICAL, OperationalStatus -> SUSPENDED.
    """

    def run(self, state: ProtocolState, context: Dict[str, Any]) -> ProtocolState:
        """Execute suspension response."""
        # Immediate state change
        state.metadata["H"] = "CRITICAL"
        state.metadata["operational_status"] = "SUSPENDED"

        # Step 1: Document everything
        state.step = ProtocolStep.DOCUMENT
        state.history.append({"step": "document", "action": "gather_evidence", "timestamp": datetime.now().isoformat()})

        # Step 2: Appeal with facts (calm, factual)
        if context.get("appeal_submitted", False):
            state.step = ProtocolStep.APPEAL
            state.history.append({"step": "appeal", "action": "submitted", "timestamp": datetime.now().isoformat()})

        # Hard-rule: do NOT open new account
        if context.get("opened_new_account", False):
            state.metadata["hard_rule_violation"] = "Opened new account during suspension"
            state.outcome = ProtocolOutcome.ESCALATE
            return state

        # Notify current clients with early warning template (not detailed explanation)
        if context.get("clients_notified", False):
            state.history.append({"step": "notify_clients", "action": "early_warning", "timestamp": datetime.now().isoformat()})

        state.outcome = ProtocolOutcome.DEFER
        return state


# =============================================================================
# II.5 Competitor Dumping Response Protocol
# =============================================================================

class CompetitorDumpingProtocol:
    """
    §II.5 — Response to competitor underpricing.
    Do NOT race to bottom. Focus on differentiation (quality, speed, communication).
    """

    def run(self, state: ProtocolState, context: Dict[str, Any]) -> ProtocolState:
        """Evaluate whether to compete on price or differentiate."""
        competitor_price = context.get("competitor_price", 0.0)
        my_price = context.get("my_price", 0.0)
        my_quality_score = context.get("my_quality_score", 0.5)

        if competitor_price < my_price * 0.5:
            # Severe dumping — do NOT match
            state.metadata["recommendation"] = "differentiate"
            state.metadata["action"] = "emphasize_quality_and_speed"
            state.outcome = ProtocolOutcome.RESOLVED
        else:
            state.metadata["recommendation"] = "monitor"
            state.outcome = ProtocolOutcome.DEFER

        return state


# =============================================================================
# II.6 Opportunity Arbitration Protocol
# =============================================================================

class OpportunityArbitrationProtocol:
    """
    §II.6 — Arbitration between multiple simultaneous opportunities.
    Use U (utility) comparison, not just price.
    """

    def run(self, state: ProtocolState, context: Dict[str, Any]) -> ProtocolState:
        """Compare opportunities and select best by U."""
        opportunities = context.get("opportunities", [])
        if not opportunities:
            state.outcome = ProtocolOutcome.DEFER
            return state

        best = max(opportunities, key=lambda o: o.get("U", 0.0))
        state.metadata["selected_opportunity"] = best
        state.outcome = ProtocolOutcome.RESOLVED
        return state


# =============================================================================
# II.7 Client Boundary Escalation Protocol
# =============================================================================

class ClientBoundaryProtocol:
    """
    §II.7 — Escalation when client repeatedly probes boundaries.
    Level 0->1: Walk Away tactic on specific point
    Level 1->2: Explicit written boundary
    Level 2->3: Formal contract review or Exit (II.9)
    """

    def run(self, state: ProtocolState, context: Dict[str, Any]) -> ProtocolState:
        """Escalate boundary level."""
        current_level = context.get("escalation_level", 0)
        gamma_soft_count = context.get("gamma_soft_count", 0)
        window_days = context.get("window_days", 30)

        if gamma_soft_count < 2:
            state.outcome = ProtocolOutcome.DEFER
            return state

        # Escalate level
        new_level = min(current_level + 1, 3)
        state.metadata["escalation_level"] = new_level

        if new_level == 1:
            state.step = ProtocolStep.WALK_AWAY
            state.metadata["action"] = "walk_away_tactic"
        elif new_level == 2:
            state.step = ProtocolStep.SET_BOUNDARY
            state.metadata["action"] = "explicit_written_boundary"
        else:
            state.step = ProtocolStep.FORMAL_REVIEW
            state.metadata["action"] = "contract_review_or_exit"
            state.outcome = ProtocolOutcome.EXIT
            return state

        state.outcome = ProtocolOutcome.ESCALATE
        return state


# =============================================================================
# II.8 Reputation Damage Response Protocol
# =============================================================================

class ReputationDamageProtocol:
    """
    §II.8 — Response to public negative review.
    1. Private contact first (Own It Fast)
    2. Public response if not retracted (factual, short, no blame)
    3. Do NOT artificially drown with new orders
    """

    def run(self, state: ProtocolState, context: Dict[str, Any]) -> ProtocolState:
        """Execute reputation damage response."""
        review_retracted = context.get("review_retracted", False)
        private_contact_made = context.get("private_contact_made", False)

        if not private_contact_made:
            state.step = ProtocolStep.PRIVATE_CONTACT
            state.metadata["action"] = "own_it_fast_private"
            state.outcome = ProtocolOutcome.DEFER
            return state

        if review_retracted:
            state.outcome = ProtocolOutcome.RESOLVED
            return state

        # Public response
        state.step = ProtocolStep.PUBLIC_RESPONSE
        state.metadata["action"] = "factual_public_response_no_blame"
        state.metadata["warning"] = "Do NOT artificially boost orders to drown review"
        state.outcome = ProtocolOutcome.RESOLVED
        return state


# =============================================================================
# II.9 Client Exit Protocol
# =============================================================================

class ClientExitProtocol:
    """
    §II.9 — Exit from client relationship.
    Hard-rule: do NOT disappear without notice.
    Minimum: formal notice, handover documentation, access transfer.
    """

    def run(self, state: ProtocolState, context: Dict[str, Any]) -> ProtocolState:
        """Execute client exit."""
        # Hard-rule check
        if context.get("disappeared_without_notice", False):
            state.metadata["hard_rule_violation"] = "Disappeared without notice"
            state.outcome = ProtocolOutcome.ESCALATE
            return state

        state.step = ProtocolStep.FORMAL_NOTICE
        state.history.append({"step": "formal_notice", "timestamp": datetime.now().isoformat()})

        state.step = ProtocolStep.HANDOVER
        state.metadata["handover_complete"] = context.get("handover_complete", False)
        state.metadata["documentation_transferred"] = context.get("documentation_transferred", False)
        state.metadata["access_transferred"] = context.get("access_transferred", False)

        state.outcome = ProtocolOutcome.RESOLVED
        return state


# =============================================================================
# II.10 Platform Diversification Protocol (Post-MVP)
# =============================================================================

class PlatformDiversificationProtocol:
    """
    §II.10 — Multi-platform strategy.
    Second independent justification: risk management (single point of failure), not just revenue optimization.
    """

    def run(self, state: ProtocolState, context: Dict[str, Any]) -> ProtocolState:
        """Evaluate diversification need."""
        platforms = context.get("platforms", [])
        if len(platforms) < 2:
            state.metadata["recommendation"] = "register_on_additional_platform"
            state.metadata["justification"] = "single_point_of_failure_risk"
            state.outcome = ProtocolOutcome.RESOLVED
            return state

        # Thompson Sampling weight could include PlatformRiskScore
        state.metadata["recommendation"] = "maintain_multi_platform"
        state.outcome = ProtocolOutcome.DEFER
        return state


# =============================================================================
# Protocol Registry
# =============================================================================

class ProtocolRegistry:
    """Registry for all market protocols."""

    def __init__(self):
        self._protocols: Dict[str, Any] = {
            "dispute": DisputeProtocol(),
            "payment_risk": PaymentRiskProtocol(),
            "platform_compliance": PlatformComplianceProtocol(),
            "account_suspension": AccountSuspensionProtocol(),
            "competitor_dumping": CompetitorDumpingProtocol(),
            "opportunity_arbitration": OpportunityArbitrationProtocol(),
            "client_boundary": ClientBoundaryProtocol(),
            "reputation_damage": ReputationDamageProtocol(),
            "client_exit": ClientExitProtocol(),
            "platform_diversification": PlatformDiversificationProtocol(),
        }

    def get(self, name: str) -> Optional[Any]:
        return self._protocols.get(name)

    def run(self, name: str, state: ProtocolState, context: Dict[str, Any]) -> ProtocolState:
        protocol = self.get(name)
        if protocol is None:
            raise ValueError(f"Unknown protocol: {name}")
        return protocol.run(state, context)

    def list_protocols(self) -> List[str]:
        return list(self._protocols.keys())
