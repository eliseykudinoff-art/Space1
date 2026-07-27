"""
TokenCostTracker — Отслеживание стоимости токенов

Formula: C(x) = C_0 + tokens × price_per_token + tool_cost

Reference: DEVELOPMENT_PLAN.md - G5 (Token cost в Cost)
MATHEMATICAL_FORMULAS.md - section 6.5 Cost Model
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
from datetime import datetime


@dataclass
class TokenUsage:
    """Использование токенов для одного запроса."""
    input_tokens: int = 0
    output_tokens: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    model: str = "unknown"
    
    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class TokenCostConfig:
    """Конфигурация цен на токены для разных моделей."""
    prices_per_million: Dict[str, tuple] = field(default_factory=lambda: {
        # OpenAI
        "gpt-4o": (5.0, 15.0),
        "gpt-4o-mini": (0.15, 0.60),
        "gpt-4-turbo": (10.0, 30.0),
        "gpt-3.5-turbo": (0.5, 1.5),
        # Anthropic
        "claude-3-5-sonnet": (3.0, 15.0),
        "claude-3-opus": (15.0, 75.0),
        "claude-3-haiku": (0.25, 1.25),
        # Ollama / Local (free)
        "llama3": (0.0, 0.0),
        "mistral": (0.0, 0.0),
        "codellama": (0.0, 0.0),
        # Fallback
        "unknown": (1.0, 3.0),
    })
    
    tool_costs: Dict[str, float] = field(default_factory=lambda: {
        "browser": 0.01,
        "file_read": 0.001,
        "file_write": 0.001,
        "web_search": 0.005,
        "code_execution": 0.02,
    })
    
    def get_price(self, model: str) -> tuple:
        """Get (input_price, output_price) per 1M tokens."""
        return self.prices_per_million.get(model, self.prices_per_million["unknown"])


class TokenCostTracker:
    """
    Tracker для подсчёта стоимости токенов.
    
    Formula: C(x) = C_0 + tokens × price_per_token + tool_cost
    
    Usage:
        tracker = TokenCostTracker()
        tracker.record("gpt-4o-mini", input_tokens=1000, output_tokens=500)
        tracker.record_tool("browser")
        
        total = tracker.get_total_cost()
    """
    
    def __init__(self, config: Optional[TokenCostConfig] = None):
        self._config = config or TokenCostConfig()
        self._usage: list = []
        self._tool_costs: list = []
        self._base_cost: float = 0.0
    
    def record(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Записать использование токенов. Returns cost in $."""
        usage = TokenUsage(input_tokens, output_tokens, model=model)
        self._usage.append(usage)
        return self._calc_cost(usage)
    
    def record_tool(self, tool_name: str, count: int = 1) -> float:
        """Записать стоимость инструмента. Returns cost in $."""
        cost = self._config.tool_costs.get(tool_name, 0.0) * count
        self._tool_costs.append((tool_name, cost))
        return cost
    
    def set_base_cost(self, cost: float) -> None:
        self._base_cost = cost
    
    def _calc_cost(self, usage: TokenUsage) -> float:
        in_price, out_price = self._config.get_price(usage.model)
        return (usage.input_tokens / 1_000_000) * in_price + \
               (usage.output_tokens / 1_000_000) * out_price
    
    def get_total_cost(self) -> float:
        base = self._base_cost
        tokens = sum(self._calc_cost(u) for u in self._usage)
        tools = sum(c for _, c in self._tool_costs)
        return base + tokens + tools
    
    def get_by_model(self) -> Dict[str, float]:
        result: Dict[str, float] = {}
        for u in self._usage:
            result[u.model] = result.get(u.model, 0.0) + self._calc_cost(u)
        return result
    
    def get_usage_stats(self) -> Dict[str, int]:
        return {
            "requests": len(self._usage),
            "input_tokens": sum(u.input_tokens for u in self._usage),
            "output_tokens": sum(u.output_tokens for u in self._usage),
        }
    
    def reset(self) -> None:
        self._usage.clear()
        self._tool_costs.clear()
        self._base_cost = 0.0
    
    def to_dict(self) -> dict:
        return {
            "total_cost": self.get_total_cost(),
            "by_model": self.get_by_model(),
            "usage": self.get_usage_stats(),
        }
