"""Тесты [MED-01]: SignalToContextSynthesizer."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from space1.orchestrator.core import SignalToContextSynthesizer

def test_synthesize_returns_context():
    s = SignalToContextSynthesizer()
    result = s.synthesize(metrics={"balance": 100.0})
    assert result is not None

def test_synthesize_with_task():
    s = SignalToContextSynthesizer()
    result = s.synthesize(
        metrics={"balance": 50.0, "stress_level": 0.8},
        task={"title": "Urgent", "priority": "CRITICAL"}
    )
    assert result is not None
