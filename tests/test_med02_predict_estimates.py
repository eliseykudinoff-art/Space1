"""Тесты [MED-02]: predict_estimates."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from space1.orchestrator.core import predict_estimates

def test_predict_returns_three_values():
    phi, q, psi = predict_estimates(x={}, category_probs={"a": 1.0}, price=100.0)
    assert isinstance(phi, float)
    assert isinstance(q, float)
    assert isinstance(psi, float)
    assert 0.0 <= phi <= 1.0
    assert 0.0 <= q <= 1.0
    assert 0.0 <= psi <= 1.0

def test_predict_with_cold_start():
    phi, q, psi = predict_estimates(x={}, category_probs={}, price=0.0, n_completed=0)
    # Cold start: ensemble of priors, all in [0,1]
    assert 0.0 <= phi <= 1.0
    assert 0.0 <= q <= 1.0
    assert 0.0 <= psi <= 1.0

def test_predict_with_history():
    phi, q, psi = predict_estimates(
        x={"code_gen": 0.9},
        category_probs={"code": 0.8},
        price=200.0,
        n_completed=10,
        agent_history=[{"quality": 0.8, "risk": 0.1}, {"quality": 0.9, "risk": 0.2}]
    )
    assert phi != 0.5  # not cold start
    assert 0.0 <= phi <= 1.0
