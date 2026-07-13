"""
Config Loader — Загрузка конфигурации из YAML файлов

Все параметры загружаются из config/*.yaml файлов.
"""

import os
try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - exercised when PyYAML is unavailable
    yaml = None
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


CONFIG_DIR = Path(__file__).parent.parent.parent.parent / "config"


@dataclass
class ConstantsConfig:
    success_rate_base: float = 0.3
    throughput_base: float = 1.0
    cost_base: float = 0.0
    time_base: float = 1.0
    price_per_task: float = 50.0
    learning_rate: float = 0.01
    knowledge_max: float = 1.0
    initial_knowledge: float = 0.0
    skill_max: float = 1.0
    initial_skill: float = 0.0
    ema_default_alpha: float = 0.2
    homeostasis_target: float = 1.0
    rating_min: float = 1.0
    rating_max: float = 5.0
    # Phase 2 additions
    phi_cap: float = 1000.0  # Cap for normalized phi
    psi_max: float = 1.0
    upsilon_cap: float = 1.0
    upsilon_decay: float = 0.95  # EMA decay factor for reputation
    pid_kp: float = 1.0
    pid_ki: float = 0.1
    pid_kd: float = 0.05
    xi_alpha: float = 0.7
    xi_beta: float = 0.3
    phi_r_lambda_psi: float = 0.5
    phi_r_alpha_rep: float = 0.3


@dataclass
class LLMWeights:
    quality_weight: float = 0.25
    reasoning_weight: float = 0.30
    coding_weight: float = 0.25
    agentic_weight: float = 0.20
    lambda_t: float = 5.0
    tau_t: float = 0.5


@dataclass
class CostTieringWeights:
    low_budget_threshold: float = 1.0
    medium_budget_threshold: float = 10.0


@dataclass
class GuardrailsWeights:
    base_beta: float = 0.05


@dataclass
class ContinualLearningWeights:
    learning_rate: float = 0.01
    knowledge_decay: float = 0.05
    gamma_cl: float = 0.12


@dataclass
class QualityWeights:
    completeness_weight: float = 0.25
    accuracy_weight: float = 0.25
    fullness_weight: float = 0.25
    timeliness_weight: float = 0.25


@dataclass
class ReputationWeights:
    rating_weight: float = 0.30
    retention_weight: float = 0.25
    positive_ratio_weight: float = 0.20
    delay_weight: float = 0.15
    momentum_weight: float = 0.10
    prior_strength: int = 7
    prior_mean: float = 4.2


@dataclass
class UtilityWeights:
    profit_weight: float = 0.30
    reputation_weight: float = 0.25
    evolution_weight: float = 0.20
    quality_weight: float = 0.25


@dataclass
class RiskWeights:
    uncertainty_coef: float = 0.3
    fatigue_coef: float = 0.2
    novelty_coef: float = 0.2
    deadline_coef: float = 0.3
    skill_coef: float = 0.1


@dataclass
class WeightsConfig:
    llm: LLMWeights = field(default_factory=LLMWeights)
    cost_tiering: CostTieringWeights = field(default_factory=CostTieringWeights)
    guardrails: GuardrailsWeights = field(default_factory=GuardrailsWeights)
    continual_learning: ContinualLearningWeights = field(default_factory=ContinualLearningWeights)
    quality: QualityWeights = field(default_factory=QualityWeights)
    reputation: ReputationWeights = field(default_factory=ReputationWeights)
    utility: UtilityWeights = field(default_factory=UtilityWeights)
    risk: RiskWeights = field(default_factory=RiskWeights)
    synergies: Dict[str, float] = field(default_factory=dict)


@dataclass
class FinancialRules:
    max_cost_per_task: float = 10.0
    max_total_cost: float = 1000.0
    min_balance: float = 0.0


@dataclass
class ActionRules:
    blocked_actions: list = field(default_factory=list)
    allowed_actions: list = field(default_factory=list)


@dataclass
class APIRules:
    rate_limit_per_minute: int = 60
    max_retries: int = 3
    timeout_seconds: int = 30


@dataclass
class SecurityRules:
    blocked_domains: list = field(default_factory=list)
    require_approval_for: list = field(default_factory=list)


@dataclass
class DataRules:
    max_file_size_mb: int = 100
    retention_days: int = 30
    allowed_extensions: list = field(default_factory=list)


@dataclass
class ParameterConstraints:
    budget_min: float = 0.0
    budget_max: float = 10000.0
    time_hours_min: float = 0.1
    time_hours_max: float = 168.0
    priority_min: float = 0.0
    priority_max: float = 1.0


@dataclass
class RulesConfig:
    financial: FinancialRules = field(default_factory=FinancialRules)
    actions: ActionRules = field(default_factory=ActionRules)
    api: APIRules = field(default_factory=APIRules)
    security: SecurityRules = field(default_factory=SecurityRules)
    data: DataRules = field(default_factory=DataRules)
    parameters: ParameterConstraints = field(default_factory=ParameterConstraints)


@dataclass
class ModelPrice:
    input: float
    output: float
    context_window: int = 8192
    description: str = ""


@dataclass
class ToolCosts:
    browser: float = 0.01
    file_read: float = 0.001
    file_write: float = 0.001
    web_search: float = 0.005
    code_execution: float = 0.02
    api_call: float = 0.001


@dataclass
class TierConfig:
    max_budget: float = 999999.0
    models: list = field(default_factory=list)


@dataclass
class PricesConfig:
    openai: Dict[str, ModelPrice] = field(default_factory=dict)
    anthropic: Dict[str, ModelPrice] = field(default_factory=dict)
    ollama: Dict[str, ModelPrice] = field(default_factory=dict)
    tools: ToolCosts = field(default_factory=ToolCosts)
    tiers: Dict[str, TierConfig] = field(default_factory=dict)


@dataclass
class Config:
    constants: ConstantsConfig
    weights: WeightsConfig
    rules: RulesConfig
    prices: PricesConfig


def _is_dataclass(obj):
    """Check if object is a dataclass."""
    return hasattr(obj, '__dataclass_fields__')


def _dict_to_dataclass(data: Dict, cls):
    if data is None:
        return cls()
    if isinstance(data, dict):
        if not _is_dataclass(cls):
            return data
        field_types = {f.name: f.type for f in cls.__dataclass_fields__.values()}
        kwargs = {}
        for key, value in data.items():
            if key in field_types:
                field_type = field_types[key]
                # Skip if field type is plain Dict/List/etc
                origin = getattr(field_type, '__origin__', None)
                if origin in (dict, list, Dict, List):
                    kwargs[key] = value
                elif isinstance(value, dict) and _is_dataclass(field_type):
                    kwargs[key] = _dict_to_dataclass(value, field_type)
                else:
                    kwargs[key] = value
        return cls(**kwargs)
    return data


def _parse_scalar(value: str):
    value = value.strip()
    if not value:
        return {}
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(part.strip()) for part in inner.split(",")]
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def _safe_load_config(path: Path) -> Dict[str, Any]:
    with open(path) as f:
        if yaml is not None:
            return yaml.safe_load(f) or {}
        return _simple_yaml_load(f.read())


def _simple_yaml_load(text: str) -> Dict[str, Any]:
    root: Dict[str, Any] = {}
    # entries are (indent, container, parent_container, key_in_parent)
    stack = [(-1, root, None, None)]
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        content = raw_line.split("#", 1)[0].rstrip()
        if not content.strip():
            continue
        indent = len(content) - len(content.lstrip(" "))
        stripped = content.strip()

        while stack and indent <= stack[-1][0]:
            stack.pop()

        if stripped.startswith("- "):
            value = _parse_scalar(stripped[2:].strip())
            current_indent, current, parent, parent_key = stack[-1]
            if not isinstance(current, list):
                replacement = []
                if isinstance(parent, dict) and parent_key is not None:
                    parent[parent_key] = replacement
                    stack[-1] = (current_indent, replacement, parent, parent_key)
                    current = replacement
                else:
                    continue
            current.append(value)
            continue

        key, sep, value = stripped.partition(":")
        if not sep:
            continue

        parent = stack[-1][1]
        if not isinstance(parent, dict):
            continue

        parsed = _parse_scalar(value)
        parent[key] = parsed
        if isinstance(parsed, dict):
            stack.append((indent, parsed, parent, key))
    return root

def load_constants(path: Optional[Path] = None) -> ConstantsConfig:
    if path is None:
        path = CONFIG_DIR / "constants.yaml"
    if not path.exists():
        return ConstantsConfig()
    data = _safe_load_config(path)
    return _dict_to_dataclass(data, ConstantsConfig)


def load_weights(path: Optional[Path] = None) -> WeightsConfig:
    if path is None:
        path = CONFIG_DIR / "weights.yaml"
    if not path.exists():
        return WeightsConfig()
    data = _safe_load_config(path)
    return _dict_to_dataclass(data, WeightsConfig)


def load_rules(path: Optional[Path] = None) -> RulesConfig:
    if path is None:
        path = CONFIG_DIR / "rules.yaml"
    if not path.exists():
        return RulesConfig()
    data = _safe_load_config(path)
    return _dict_to_dataclass(data, RulesConfig)


def load_prices(path: Optional[Path] = None) -> PricesConfig:
    if path is None:
        path = CONFIG_DIR / "prices.yaml"
    if not path.exists():
        return PricesConfig()
    data = _safe_load_config(path)
    for provider in ["openai", "anthropic", "ollama"]:
        if provider in data:
            data[provider] = {
                k: ModelPrice(**v) for k, v in data[provider].items()
            }
    if "tiers" in data:
        data["tiers"] = {
            k: TierConfig(**v) for k, v in data["tiers"].items()
        }
    if "tools" in data:
        data["tools"] = ToolCosts(**data["tools"])
    return PricesConfig(**data)


def load_config(config_dir: Optional[Path] = None) -> Config:
    if config_dir is None:
        config_dir = CONFIG_DIR
    return Config(
        constants=load_constants(config_dir / "constants.yaml"),
        weights=load_weights(config_dir / "weights.yaml"),
        rules=load_rules(config_dir / "rules.yaml"),
        prices=load_prices(config_dir / "prices.yaml"),
    )


_config: Optional[Config] = None


def get_config() -> Config:
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config() -> Config:
    global _config
    _config = load_config()
    return _config
