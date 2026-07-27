"""Тесты [HIGH-09]: CapabilityVector 17 факторов."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from space1.models.agents import AgentCapabilities

def test_seventeen_factors():
    c = AgentCapabilities()
    factors = [
        "llm_quality", "code_gen", "data_analysis", "llm_reasoning",
        "browser", "code_exec", "multimodal", "negotiation", "legal",
        "design", "research", "testing", "devops", "i18n",
        "accessibility", "performance", "security_audit",
    ]
    for f in factors:
        assert hasattr(c, f), f"Missing factor: {f}"

def test_backward_compatible():
    c = AgentCapabilities()
    assert hasattr(c, "llm_name")
    assert hasattr(c, "has_browser")
    assert c.llm_coding == c.code_gen  # alias

def test_to_dict_has_all():
    c = AgentCapabilities()
    d = c.to_dict()
    assert "capabilities" in d
    assert len(d["capabilities"]) == 17
