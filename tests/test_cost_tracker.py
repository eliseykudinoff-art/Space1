"""
Tests for TokenCostTracker

Reference: DEVELOPMENT_PLAN.md - G5
"""

import pytest
from space1.cost.token_tracker import (
    TokenCostTracker,
    TokenCostConfig,
    TokenUsage,
)


class TestTokenUsage:
    def test_total_tokens(self):
        usage = TokenUsage(input_tokens=1000, output_tokens=500)
        assert usage.total_tokens == 1500


class TestTokenCostTracker:
    def test_empty_tracker(self):
        tracker = TokenCostTracker()
        assert tracker.get_total_cost() == 0.0
    
    def test_record_tokens(self):
        tracker = TokenCostTracker()
        # gpt-4o-mini: $0.15/1M input, $0.60/1M output
        cost = tracker.record("gpt-4o-mini", input_tokens=1000, output_tokens=500)
        # 1000/1M * 0.15 + 500/1M * 0.60 = 0.00015 + 0.0003 = 0.00045
        assert abs(cost - 0.00045) < 0.00001
    
    def test_free_model(self):
        tracker = TokenCostTracker()
        cost = tracker.record("llama3", input_tokens=1000, output_tokens=500)
        assert cost == 0.0
    
    def test_tool_cost(self):
        tracker = TokenCostTracker()
        cost = tracker.record_tool("browser")
        assert cost == 0.01
    
    def test_total_with_all(self):
        tracker = TokenCostTracker()
        tracker.set_base_cost(0.5)
        tracker.record("gpt-4o-mini", 1000, 500)
        tracker.record_tool("browser")
        
        # 0.5 + 0.00045 + 0.01 = 0.51045
        assert abs(tracker.get_total_cost() - 0.51045) < 0.0001
    
    def test_cost_by_model(self):
        tracker = TokenCostTracker()
        tracker.record("gpt-4o-mini", 1000, 500)
        tracker.record("gpt-4o-mini", 2000, 1000)
        tracker.record("llama3", 1000, 500)
        
        by_model = tracker.get_by_model()
        assert "gpt-4o-mini" in by_model
        assert "llama3" in by_model
    
    def test_usage_stats(self):
        tracker = TokenCostTracker()
        tracker.record("gpt-4o-mini", 1000, 500)
        tracker.record("gpt-4o-mini", 2000, 1000)
        
        stats = tracker.get_usage_stats()
        assert stats["requests"] == 2
        assert stats["input_tokens"] == 3000
        assert stats["output_tokens"] == 1500
    
    def test_reset(self):
        tracker = TokenCostTracker()
        tracker.record("gpt-4o-mini", 1000, 500)
        tracker.reset()
        assert tracker.get_total_cost() == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
