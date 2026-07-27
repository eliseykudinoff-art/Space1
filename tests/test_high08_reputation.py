"""Тесты [HIGH-08]: ReputationVector."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from space1.models.agents import AgentMetrics

def test_reputation_vector_default():
    m = AgentMetrics()
    assert len(m.reputation_vector) == 6
    assert m.reputation_vector["tech"] == 0.5

def test_rating_is_scalar_from_vector():
    m = AgentMetrics()
    m.reputation_vector = {"tech": 1.0, "econ": 1.0, "comm": 1.0, "rel": 1.0, "sec": 1.0, "domain": 1.0}
    assert m.rating == 1.0

    m.reputation_vector = {"tech": 0.0, "econ": 0.0, "comm": 0.0, "rel": 0.0, "sec": 0.0, "domain": 0.0}
    assert m.rating == 0.0

def test_rating_partial():
    m = AgentMetrics()
    m.reputation_vector = {"tech": 1.0, "econ": 0.0, "comm": 0.0, "rel": 0.0, "sec": 0.0, "domain": 0.0}
    assert m.rating == 0.20  # tech weight = 0.20

def test_backward_compatible():
    m = AgentMetrics()
    assert isinstance(m.rating, float)
    assert 0.0 <= m.rating <= 1.0
