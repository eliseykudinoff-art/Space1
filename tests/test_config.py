"""
Tests for Config Loader

Reference: Config should be loaded from YAML files
"""

import pytest
from pathlib import Path


class TestConfigLoader:
    """Test configuration loading."""
    
    def test_load_constants(self):
        """Test loading constants from YAML."""
        from space1.config.loader import load_constants, ConstantsConfig
        
        config = load_constants(Path("config/constants.yaml"))
        
        assert isinstance(config, ConstantsConfig)
        assert config.success_rate_base == 0.3
        assert config.price_per_task == 50.0
        assert config.ema_default_alpha == 0.2
    
    def test_load_weights(self):
        """Test loading weights from YAML."""
        from space1.config.loader import load_weights, WeightsConfig
        
        config = load_weights(Path("config/weights.yaml"))
        
        assert isinstance(config, WeightsConfig)
        assert config.llm.quality_weight == 0.25
        assert config.llm.reasoning_weight == 0.30
        assert config.reputation.rating_weight == 0.30
    
    def test_load_rules(self):
        """Test loading rules from YAML."""
        from space1.config.loader import load_rules, RulesConfig
        
        config = load_rules(Path("config/rules.yaml"))
        
        assert isinstance(config, RulesConfig)
        assert config.financial.max_cost_per_task == 10.0
        assert "delete_all" in config.actions.blocked_actions
        assert config.api.rate_limit_per_minute == 60
    
    def test_load_prices(self):
        """Test loading prices from YAML."""
        from space1.config.loader import load_prices, PricesConfig
        
        config = load_prices(Path("config/prices.yaml"))
        
        assert isinstance(config, PricesConfig)
        assert "gpt-4o-mini" in config.openai
        assert config.openai["gpt-4o-mini"].input == 0.15
        assert config.openai["gpt-4o-mini"].output == 0.60
        
        # Ollama is free
        assert "llama3" in config.ollama
        assert config.ollama["llama3"].input == 0.0
        
        # Tool costs
        assert config.tools.browser == 0.01
    
    def test_load_full_config(self):
        """Test loading all config at once."""
        from space1.config.loader import load_config
        
        config = load_config()
        
        # Constants
        assert config.constants.success_rate_base == 0.3
        
        # Weights
        assert config.weights.llm.lambda_t == 5.0
        
        # Rules
        assert config.rules.financial.max_cost_per_task == 10.0
        
        # Prices
        assert config.prices.openai["gpt-4o"].input == 5.0
    
    def test_singleton_config(self):
        """Test singleton get_config."""
        from space1.config.loader import get_config, reload_config
        
        config1 = get_config()
        config2 = get_config()
        
        assert config1 is config2  # Same instance
        
        # Reload
        config3 = reload_config()
        assert config3 is not config1  # New instance created


class TestConfigValues:
    """Test that config values match expectations."""
    
    def test_llm_weights_sum(self):
        """LLM weights should sum to 1.0."""
        from space1.config.loader import load_weights
        
        w = load_weights().llm
        total = w.quality_weight + w.reasoning_weight + w.coding_weight + w.agentic_weight
        
        assert abs(total - 1.0) < 0.001
    
    def test_quality_weights_sum(self):
        """Quality weights should sum to 1.0."""
        from space1.config.loader import load_weights
        
        w = load_weights().quality
        total = w.completeness_weight + w.accuracy_weight + w.fullness_weight + w.timeliness_weight
        
        assert abs(total - 1.0) < 0.001
    
    def test_utility_weights_sum(self):
        """Utility weights should sum to 1.0."""
        from space1.config.loader import load_weights
        
        w = load_weights().utility
        total = w.profit_weight + w.reputation_weight + w.evolution_weight + w.quality_weight
        
        assert abs(total - 1.0) < 0.001
    
    def test_reputation_weights_sum(self):
        """Reputation weights should sum to 1.0."""
        from space1.config.loader import load_weights
        
        w = load_weights().reputation
        total = w.rating_weight + w.retention_weight + w.positive_ratio_weight + w.delay_weight + w.momentum_weight
        
        assert abs(total - 1.0) < 0.001


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
