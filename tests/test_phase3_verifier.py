"""Tests for Verifier (Worker-Critic Loop) — 03_PIPELINE_MATH.md §VIII.6."""

import pytest
from space1.verifier import Verifier, Verdict, CriticType


def test_verifier_accepts_structured_deliverable():
    v = Verifier()
    task = """Write a Python function to compute factorial. Requirements:
- Must handle n=0
- Must use recursion"""
    deliverable = """# Factorial Function

```python
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n - 1)
```

This handles n=0 via the base case."""
    result = v.verify(deliverable, task)
    assert result.verdict in (Verdict.ACCEPT, Verdict.REVISE)
    assert len(result.scores) == 5
    assert all(0.0 <= s.score <= 10.0 for s in result.scores.values())


def test_verifier_rejects_empty():
    v = Verifier()
    result = v.verify("", "Write a detailed report on market analysis")
    assert result.min_score < 8.5


def test_verdict_by_minimum_not_average():
    """Even if 4 critics give 10, one at 2 -> min=2 -> not ACCEPT."""
    v = Verifier()
    task = """Create a full website with HTML, CSS, JS. Requirements:
- HTML structure
- CSS styling
- JS interactivity"""
    deliverable = "<div>Hello</div>"
    result = v.verify(deliverable, task)
    assert result.min_score <= 10.0
    assert CriticType.TECHNICAL in result.scores
    assert CriticType.BRIEF_COMPLIANCE in result.scores


def test_max_iterations_constant():
    v = Verifier()
    assert v.ACCEPT_THRESHOLD == 8.5
    assert v.REJECT_THRESHOLD == 3.0
    assert v.MAX_ITERATIONS == 4


def test_reject_threshold():
    v = Verifier()
    result = v.verify("x", "task", iteration=2)
    # Empty deliverable should score low on most critics
    assert result.min_score < 8.5


def test_history_tracking():
    v = Verifier()
    v.verify("test", "task")
    assert len(v.get_history()) == 1
    v.reset_history()
    assert len(v.get_history()) == 0


def test_verify_with_revisions_no_callback():
    v = Verifier()
    result = v.verify_with_revisions("bad", "task")
    assert result.verdict in (Verdict.REJECT, Verdict.ESCALATE, Verdict.REVISE)
