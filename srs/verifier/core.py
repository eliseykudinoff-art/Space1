"""
Verifier — Worker-Critic Loop (03_PIPELINE_MATH.md §VIII.6).

Five critic types, min-based verdict, thresholds:
  ACCEPT:   min_k score_k >= 8.5
  REVISE:   min_k score_k in [3, 8.5) and iteration < 4
  REJECT:   min_k score_k < 3 and iteration >= 2

Cross-model QA requirement: Critic must not use the same model as Worker
without calibration (03 §VIII.6, methodological caveat).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime


class Verdict(Enum):
    ACCEPT = "accept"
    REVISE = "revise"
    REJECT = "reject"
    ESCALATE = "escalate"


class CriticType(Enum):
    TECHNICAL = "technical"              # File integrity, format, completeness
    BRIEF_COMPLIANCE = "brief_compliance"  # Extract requirements from T_raw, check each
    VISUAL_DOMAIN_QA = "visual_domain_qa"  # Aesthetics, style, professional level
    CROSS_DELIVERABLE = "cross_deliverable"  # Consistency between multiple files
    CLIENT_SIMULATION = "client_simulation"  # "Would the client pay for this?"


@dataclass
class CriticScore:
    critic_type: CriticType
    score: float          # [0, 10]
    issues: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class VerificationResult:
    verdict: Verdict
    scores: Dict[CriticType, CriticScore]
    min_score: float
    iteration: int
    issues: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict.value,
            "scores": {k.value: {"score": v.score, "issues": v.issues} for k, v in self.scores.items()},
            "min_score": self.min_score,
            "iteration": self.iteration,
            "issues": self.issues,
            "timestamp": self.timestamp.isoformat(),
        }


class Critic:
    """Base critic interface."""

    def __init__(self, critic_type: CriticType):
        self.critic_type = critic_type

    def evaluate(self, deliverable: Any, task_raw: str, context: Optional[Dict[str, Any]] = None) -> CriticScore:
        raise NotImplementedError


class TechnicalCritic(Critic):
    """Check file integrity, format, completeness — all deliverables from brief present."""

    def __init__(self):
        super().__init__(CriticType.TECHNICAL)

    def evaluate(self, deliverable: Any, task_raw: str, context: Optional[Dict[str, Any]] = None) -> CriticScore:
        issues: List[str] = []
        score = 10.0

        # Extract expected deliverables from task_raw (heuristic: count file mentions)
        expected_files = self._extract_expected_files(task_raw)
        actual_files = self._extract_actual_files(deliverable)

        if expected_files and not actual_files:
            issues.append("No deliverable files found")
            score -= 5.0
        elif expected_files:
            missing = set(expected_files) - set(actual_files)
            if missing:
                issues.append(f"Missing files: {missing}")
                score -= 3.0 * (len(missing) / len(expected_files))

        # Format check
        if isinstance(deliverable, str):
            if len(deliverable.strip()) < 50:
                issues.append("Deliverable too short")
                score -= 3.0

        score = max(0.0, min(10.0, score))
        return CriticScore(critic_type=self.critic_type, score=score, issues=issues)

    def _extract_expected_files(self, task_raw: str) -> List[str]:
        import re
        # Heuristic: look for file extensions mentioned
        patterns = re.findall(r"[\w\-]+\.(py|js|ts|html|css|md|txt|json|yaml|pdf|docx|png|jpg)", task_raw, re.IGNORECASE)
        return list(set(p.lower() for p in patterns))

    def _extract_actual_files(self, deliverable: Any) -> List[str]:
        if isinstance(deliverable, dict):
            return list(deliverable.keys())
        if isinstance(deliverable, str):
            import re
            patterns = re.findall(r"[\w\-]+\.(py|js|ts|html|css|md|txt|json|yaml|pdf|docx|png|jpg)", deliverable, re.IGNORECASE)
            return list(set(p.lower() for p in patterns))
        return []


class BriefComplianceCritic(Critic):
    """Extract requirements from T_raw and check each against result."""

    def __init__(self):
        super().__init__(CriticType.BRIEF_COMPLIANCE)

    def evaluate(self, deliverable: Any, task_raw: str, context: Optional[Dict[str, Any]] = None) -> CriticScore:
        issues: List[str] = []
        score = 10.0

        # Extract requirement keywords from task_raw
        requirements = self._extract_requirements(task_raw)
        deliverable_text = self._to_text(deliverable)

        if not requirements:
            # No explicit requirements found — neutral
            return CriticScore(critic_type=self.critic_type, score=8.0, issues=["No explicit requirements extracted"])

        for req in requirements:
            if req.lower() not in deliverable_text.lower():
                issues.append(f"Requirement not addressed: '{req}'")
                score -= 10.0 / len(requirements)

        score = max(0.0, min(10.0, score))
        return CriticScore(critic_type=self.critic_type, score=score, issues=issues)

    def _extract_requirements(self, task_raw: str) -> List[str]:
        import re
        # Heuristic: bullet points, numbered lists, "must", "should", "required"
        lines = task_raw.split("\n")
        reqs = []
        for line in lines:
            line = line.strip()
            if re.match(r"^[-*••]\s+", line):
                reqs.append(re.sub(r"^[-*••]\s+", "", line))
            elif re.search(r"\b(must|should|required|need to|has to)\b", line, re.IGNORECASE):
                reqs.append(line)
        return reqs[:10]  # Cap at 10

    def _to_text(self, deliverable: Any) -> str:
        if isinstance(deliverable, str):
            return deliverable
        if isinstance(deliverable, dict):
            return " ".join(str(v) for v in deliverable.values())
        return str(deliverable)


class VisualDomainQACritic(Critic):
    """Aesthetics, style, professional level — applicable when domain allows."""

    def __init__(self):
        super().__init__(CriticType.VISUAL_DOMAIN_QA)

    def evaluate(self, deliverable: Any, task_raw: str, context: Optional[Dict[str, Any]] = None) -> CriticScore:
        issues: List[str] = []
        score = 8.0  # Default slightly lower — visual QA is harder to auto-check

        deliverable_text = self._to_text(deliverable)

        # Heuristic quality checks
        if len(deliverable_text) < 100:
            issues.append("Deliverable seems too short for visual/domain standards")
            score -= 2.0

        # Check for professional structure (headers, sections)
        if "#" not in deliverable_text and "==" not in deliverable_text:
            issues.append("No clear structure/headers found")
            score -= 1.5

        # Domain-specific: code quality heuristics
        if "```" in deliverable_text:
            code_blocks = deliverable_text.count("```")
            if code_blocks < 2 and "function" in task_raw.lower():
                issues.append("Code deliverable may be incomplete")
                score -= 1.0

        score = max(0.0, min(10.0, score))
        return CriticScore(critic_type=self.critic_type, score=score, issues=issues)

    def _to_text(self, deliverable: Any) -> str:
        if isinstance(deliverable, str):
            return deliverable
        if isinstance(deliverable, dict):
            return " ".join(str(v) for v in deliverable.values())
        return str(deliverable)


class CrossDeliverableCritic(Critic):
    """Consistency between multiple files in a single task."""

    def __init__(self):
        super().__init__(CriticType.CROSS_DELIVERABLE)

    def evaluate(self, deliverable: Any, task_raw: str, context: Optional[Dict[str, Any]] = None) -> CriticScore:
        issues: List[str] = []
        score = 10.0

        if not isinstance(deliverable, dict) or len(deliverable) < 2:
            # Single file — consistency not applicable, neutral score
            return CriticScore(critic_type=self.critic_type, score=10.0, issues=["Single deliverable — consistency N/A"])

        files = list(deliverable.values())
        texts = [self._to_text(f) for f in files]

        # Check for contradictions (simple keyword overlap)
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                overlap = self._keyword_overlap(texts[i], texts[j])
                if overlap < 0.1:
                    issues.append(f"Low keyword overlap between deliverable {i} and {j}")
                    score -= 2.0

        score = max(0.0, min(10.0, score))
        return CriticScore(critic_type=self.critic_type, score=score, issues=issues)

    def _to_text(self, deliverable: Any) -> str:
        if isinstance(deliverable, str):
            return deliverable
        return str(deliverable)

    def _keyword_overlap(self, text1: str, text2: str) -> float:
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0.0
        intersection = words1 & words2
        return len(intersection) / max(len(words1), len(words2))


class ClientSimulationCritic(Critic):
    """Final gate: 'Would the client pay for this?' — holistic evaluation."""

    def __init__(self):
        super().__init__(CriticType.CLIENT_SIMULATION)

    def evaluate(self, deliverable: Any, task_raw: str, context: Optional[Dict[str, Any]] = None) -> CriticScore:
        issues: List[str] = []
        score = 8.0  # Start conservative — client simulation is demanding

        deliverable_text = self._to_text(deliverable)

        # Length heuristic: very short = unlikely to satisfy
        if len(deliverable_text) < 200:
            issues.append("Deliverable too short for paid work")
            score -= 4.0
        elif len(deliverable_text) < 500:
            issues.append("Deliverable shorter than typical paid deliverable")
            score -= 1.5

        # Check if task mentions specific deliverables and they are present
        if "report" in task_raw.lower() and "report" not in deliverable_text.lower():
            issues.append("Task mentions report but none found")
            score -= 3.0

        if "code" in task_raw.lower() and "```" not in deliverable_text:
            issues.append("Task mentions code but no code block found")
            score -= 3.0

        score = max(0.0, min(10.0, score))
        return CriticScore(critic_type=self.critic_type, score=score, issues=issues)

    def _to_text(self, deliverable: Any) -> str:
        if isinstance(deliverable, str):
            return deliverable
        if isinstance(deliverable, dict):
            return " ".join(str(v) for v in deliverable.values())
        return str(deliverable)


class Verifier:
    """
    Worker-Critic Verifier per 03_PIPELINE_MATH.md §VIII.6.

    Orchestrates 5 critics, computes min-score verdict, manages up to 4 REVISE iterations.
    """

    ACCEPT_THRESHOLD: float = 8.5
    REJECT_THRESHOLD: float = 3.0
    MAX_ITERATIONS: int = 4

    def __init__(self, critics: Optional[List[Critic]] = None, worker_model: Optional[str] = None):
        self.critics = critics or [
            TechnicalCritic(),
            BriefComplianceCritic(),
            VisualDomainQACritic(),
            CrossDeliverableCritic(),
            ClientSimulationCritic(),
        ]
        self.worker_model = worker_model  # For cross-model QA tracking
        self._history: List[VerificationResult] = []

    def verify(self, deliverable: Any, task_raw: str, iteration: int = 0,
               context: Optional[Dict[str, Any]] = None) -> VerificationResult:
        """
        Run the Worker-Critic verification loop.

        Args:
            deliverable: The deliverable to verify (str, dict, etc.)
            task_raw: Original task description/requirements
            iteration: Current iteration number (0-based)
            context: Optional additional context

        Returns:
            VerificationResult with verdict and detailed scores
        """
        scores: Dict[CriticType, CriticScore] = {}
        all_issues: List[str] = []

        for critic in self.critics:
            score = critic.evaluate(deliverable, task_raw, context)
            scores[critic.critic_type] = score
            all_issues.extend(score.issues)

        min_score = min(s.score for s in scores.values())

        # Verdict by minimum, not average
        if min_score >= self.ACCEPT_THRESHOLD:
            verdict = Verdict.ACCEPT
        elif min_score < self.REJECT_THRESHOLD and iteration >= 2:
            verdict = Verdict.REJECT
        elif iteration >= self.MAX_ITERATIONS:
            # Max iterations reached — escalate if not accepted
            verdict = Verdict.ESCALATE if min_score < self.ACCEPT_THRESHOLD else Verdict.ACCEPT
        else:
            verdict = Verdict.REVISE

        result = VerificationResult(
            verdict=verdict,
            scores=scores,
            min_score=min_score,
            iteration=iteration,
            issues=all_issues,
        )
        self._history.append(result)
        return result

    def verify_with_revisions(self, deliverable: Any, task_raw: str,
                              revise_callback: Optional[Callable[[VerificationResult, int], Any]] = None,
                              context: Optional[Dict[str, Any]] = None) -> VerificationResult:
        """
        Full loop: verify, revise, verify again, up to MAX_ITERATIONS.

        Args:
            deliverable: Initial deliverable
            task_raw: Task description
            revise_callback: Callable(result, iteration) -> revised_deliverable
            context: Optional context

        Returns:
            Final VerificationResult
        """
        current = deliverable
        for i in range(self.MAX_ITERATIONS + 1):
            result = self.verify(current, task_raw, iteration=i, context=context)
            if result.verdict in (Verdict.ACCEPT, Verdict.REJECT, Verdict.ESCALATE):
                return result
            # REVISE — call callback if provided
            if revise_callback:
                current = revise_callback(result, i)
            else:
                # No callback — cannot revise, escalate
                return VerificationResult(
                    verdict=Verdict.ESCALATE,
                    scores=result.scores,
                    min_score=result.min_score,
                    iteration=i,
                    issues=result.issues + ["No revise callback provided"],
                )
        # Should not reach here, but safety fallback
        return result

    def get_history(self) -> List[VerificationResult]:
        """Return verification history."""
        return self._history.copy()

    def reset_history(self) -> None:
        """Clear verification history."""
        self._history.clear()
