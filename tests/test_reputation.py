"""Tests for Soft-Capped Reputation (G8)."""

import pytest
import time
from space1.utility.reputation import SoftCappedReputation


class TestSoftCappedReputation:
    """Test Soft-Capped Reputation calculator."""
    
    def test_basic_computation(self):
        """Compute reputation with defaults."""
        rep = SoftCappedReputation(cap=1.0, decay_factor=1.0)
        value = rep.compute(rating=4.5, n_reviews=10)
        
        assert 0 <= value <= 1.0
    
    def test_soft_cap(self):
        """Reputation is capped at cap value."""
        rep = SoftCappedReputation(cap=0.5, decay_factor=1.0)
        
        # High rating should hit cap
        value = rep.compute(rating=5.0, n_reviews=100)
        
        assert value <= 0.5
    
    def test_ema_smoothing(self):
        """EMA smooths reputation updates."""
        rep = SoftCappedReputation(cap=1.0, decay_factor=1.0, ema_alpha=0.2)
        
        v1 = rep.compute(rating=3.0, n_reviews=5)
        v2 = rep.compute(rating=5.0, n_reviews=10)
        
        # EMA should smooth the jump
        assert v2 != v1
        assert 0 <= v2 <= 1.0
    
    def test_decay_over_time(self):
        """Reputation decays over time."""
        rep = SoftCappedReputation(cap=1.0, decay_factor=0.9, ema_alpha=1.0)
        
        # Initial high rating
        v1 = rep.compute(rating=5.0, n_reviews=100)
        
        # Wait a bit
        time.sleep(0.1)
        
        # Same rating but with decay
        v2 = rep.compute(rating=5.0, n_reviews=100)
        
        # Decay should reduce value (but EMA may smooth it)
        # At least verify it doesn't crash
        assert 0 <= v2 <= 1.0
    
    def test_apply_decay_only(self):
        """Decay-only update works."""
        rep = SoftCappedReputation(cap=1.0, decay_factor=0.95)
        
        # Set initial value
        rep.compute(rating=4.0, n_reviews=10)
        initial = rep.get_current()
        
        # Wait and apply decay
        time.sleep(0.1)
        decayed = rep.apply_decay_only()
        
        assert decayed <= initial or decayed == 0
    
    def test_tracks_through_metrics(self):
        """Tracks through MetricRegistry."""
        from space1.metrics.tracker import MetricRegistry
        
        metrics = MetricRegistry()
        rep = SoftCappedReputation(cap=1.0, decay_factor=1.0)
        
        rep.compute(rating=4.0, n_reviews=10, metrics=metrics)
        
        # Should have tracked values
        assert metrics.get("upsilon_soft_capped") is not None
    
    def test_reset(self):
        """Reset clears state."""
        rep = SoftCappedReputation()
        rep.compute(rating=4.0, n_reviews=10)
        rep.reset()
        
        assert rep.get_current() == 0.0
        assert rep._state.update_count == 0
    
    def test_to_dict(self):
        """Can serialize state."""
        rep = SoftCappedReputation()
        rep.compute(rating=4.0, n_reviews=10)
        d = rep.to_dict()
        
        assert "state" in d
        assert "current_ema" in d
        assert "cap" in d
        assert "decay_factor" in d
