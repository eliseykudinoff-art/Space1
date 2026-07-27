"""
Space1 — ПРОВЕРЕННЫЕ ТЕСТЫ: Config Loader

Каждый тест проверен против реального кода.
FAILED-тесты = реальные баги, не ошибки тестов.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from pathlib import Path
import warnings


# =============================================================================
# UNIT: _parse_scalar
# =============================================================================

class TestParseScalarUnit:
    """Unit-тесты на _parse_scalar — парсинг скалярных значений из YAML."""

    def test_parse_int(self):
        """_parse_scalar('42') → 42."""
        from space1.config.loader import _parse_scalar
        assert _parse_scalar("42") == 42

    def test_parse_float(self):
        """_parse_scalar('3.14') → 3.14."""
        from space1.config.loader import _parse_scalar
        assert _parse_scalar("3.14") == 3.14

    def test_parse_scientific_notation(self):
        """_parse_scalar('3.0e2') → 300.0."""
        from space1.config.loader import _parse_scalar
        assert _parse_scalar("3.0e2") == 300.0

    def test_parse_true(self):
        """_parse_scalar('true') → True."""
        from space1.config.loader import _parse_scalar
        assert _parse_scalar("true") is True
        assert _parse_scalar("TRUE") is True

    def test_parse_false(self):
        """_parse_scalar('false') → False."""
        from space1.config.loader import _parse_scalar
        assert _parse_scalar("false") is False
        assert _parse_scalar("False") is False

    def test_parse_quoted_string(self):
        """_parse_scalar('"hello"') → 'hello' (без кавычек)."""
        from space1.config.loader import _parse_scalar
        assert _parse_scalar('"hello"') == "hello"
        assert _parse_scalar("'world'") == "world"

    def test_parse_list(self):
        """_parse_scalar('[1, 2, 3]') → [1, 2, 3]."""
        from space1.config.loader import _parse_scalar
        assert _parse_scalar("[1, 2, 3]") == [1, 2, 3]

    def test_parse_empty_list(self):
        """_parse_scalar('[]') → []."""
        from space1.config.loader import _parse_scalar
        assert _parse_scalar("[]") == []

    def test_parse_list_with_strings(self):
        """_parse_scalar('["a", "b"]') → ['a', 'b']."""
        from space1.config.loader import _parse_scalar
        assert _parse_scalar('["a", "b"]') == ["a", "b"]

    def test_parse_empty_string(self):
        """_parse_scalar('') → {} (пустая строка → пустой dict)."""
        from space1.config.loader import _parse_scalar
        assert _parse_scalar("") == {}

    def test_parse_unquoted_string(self):
        """_parse_scalar('hello') → 'hello'."""
        from space1.config.loader import _parse_scalar
        assert _parse_scalar("hello") == "hello"

    def test_parse_strips_whitespace(self):
        """_parse_scalar('  42  ') → 42 (whitespace stripped)."""
        from space1.config.loader import _parse_scalar
        assert _parse_scalar("  42  ") == 42


# =============================================================================
# UNIT: _simple_yaml_load
# =============================================================================

class TestSimpleYamlLoadUnit:
    """Unit-тесты на _simple_yaml_load — собственный YAML-парсер."""

    def test_simple_key_value(self):
        """'key: value' → {'key': 'value'}."""
        from space1.config.loader import _simple_yaml_load
        result = _simple_yaml_load("key: value")
        assert result == {"key": "value"}

    def test_nested_dict(self):
        """Вложенные ключи → вложенный dict."""
        from space1.config.loader import _simple_yaml_load
        text = """
constants:
  success_rate_base: 0.5
  phi_cap: 500.0
"""
        result = _simple_yaml_load(text)
        assert result["constants"]["success_rate_base"] == 0.5
        assert result["constants"]["phi_cap"] == 500.0

    def test_list_values(self):
        """Список через '- ' → list."""
        from space1.config.loader import _simple_yaml_load
        text = """
blocked_actions:
  - hack
  - delete_all
"""
        result = _simple_yaml_load(text)
        assert result["blocked_actions"] == ["hack", "delete_all"]

    def test_comments_ignored(self):
        """Комментарии (#) игнорируются."""
        from space1.config.loader import _simple_yaml_load
        text = """
# Это комментарий
key: value  # inline comment
"""
        result = _simple_yaml_load(text)
        assert result == {"key": "value"}

    def test_empty_lines_ignored(self):
        """Пустые строки игнорируются."""
        from space1.config.loader import _simple_yaml_load
        text = """

key1: value1

key2: value2

"""
        result = _simple_yaml_load(text)
        assert result == {"key1": "value1", "key2": "value2"}

    def test_mixed_list_and_dict(self):
        """Список внутри dict → корректная структура."""
        from space1.config.loader import _simple_yaml_load
        text = """
rules:
  actions:
    blocked_actions:
      - hack
      - exploit
    allowed_actions:
      - deploy
  financial:
    max_cost_per_task: 10.0
"""
        result = _simple_yaml_load(text)
        assert result["rules"]["actions"]["blocked_actions"] == ["hack", "exploit"]
        assert result["rules"]["actions"]["allowed_actions"] == ["deploy"]
        assert result["rules"]["financial"]["max_cost_per_task"] == 10.0

    def test_deep_nesting(self):
        """Глубокая вложенность → корректный dict."""
        from space1.config.loader import _simple_yaml_load
        text = """
a:
  b:
    c:
      d: 42
"""
        result = _simple_yaml_load(text)
        assert result["a"]["b"]["c"]["d"] == 42

    def test_returns_dict_for_empty(self):
        """Пустой input → пустой dict."""
        from space1.config.loader import _simple_yaml_load
        assert _simple_yaml_load("") == {}


# =============================================================================
# UNIT: _dict_to_dataclass
# =============================================================================

class TestDictToDataclassUnit:
    """Unit-тесты на _dict_to_dataclass — конвертация dict в dataclass."""

    def test_partial_data_uses_defaults(self):
        """Частичные данные → остальное из defaults."""
        from space1.config.loader import _dict_to_dataclass, ConstantsConfig
        cfg = _dict_to_dataclass({"success_rate_base": 0.99}, ConstantsConfig)
        assert cfg.success_rate_base == 0.99
        assert cfg.phi_cap == 1000.0  # default
        assert cfg.psi_max == 1.0      # default

    def test_none_returns_defaults(self):
        """None → полностью default dataclass."""
        from space1.config.loader import _dict_to_dataclass, ConstantsConfig
        cfg = _dict_to_dataclass(None, ConstantsConfig)
        assert cfg.success_rate_base == 0.3
        assert cfg.phi_cap == 1000.0

    def test_extra_keys_ignored(self):
        """Лишние ключи в dict игнорируются."""
        from space1.config.loader import _dict_to_dataclass, ConstantsConfig
        cfg = _dict_to_dataclass({"success_rate_base": 0.5, "nonexistent": 999}, ConstantsConfig)
        assert cfg.success_rate_base == 0.5

    def test_nested_dataclass(self):
        """Вложенный dict → вложенный dataclass."""
        from space1.config.loader import _dict_to_dataclass, WeightsConfig, QualityWeights
        cfg = _dict_to_dataclass({"quality": {"completeness_weight": 0.5}}, WeightsConfig)
        assert cfg.quality.completeness_weight == 0.5
        assert cfg.quality.accuracy_weight == 0.25  # default

    def test_dict_fields_preserved(self):
        """Dict-поля (synergies) сохраняются как dict."""
        from space1.config.loader import _dict_to_dataclass, WeightsConfig
        cfg = _dict_to_dataclass({"synergies": {"a": 0.5, "b": 0.3}}, WeightsConfig)
        assert cfg.synergies == {"a": 0.5, "b": 0.3}


# =============================================================================
# UNIT: load_* functions
# =============================================================================

class TestLoadFunctionsUnit:
    """Unit-тесты на load_constants, load_weights, load_rules, load_prices."""

    def test_load_constants_from_real_file(self):
        """load_constants() загружает из реального constants.yaml."""
        from space1.config.loader import load_constants
        cfg = load_constants()
        assert cfg.success_rate_base == 0.3
        assert cfg.phi_cap == 1000.0
        assert cfg.psi_max == 1.0

    def test_load_weights_from_real_file(self):
        """load_weights() загружает из реального weights.yaml."""
        from space1.config.loader import load_weights
        cfg = load_weights()
        assert cfg.quality.completeness_weight == 0.25
        assert cfg.risk.uncertainty_coef == 0.3

    def test_load_rules_from_real_file(self):
        """load_rules() загружает из реального rules.yaml."""
        from space1.config.loader import load_rules
        cfg = load_rules()
        assert cfg.financial.max_cost_per_task == 10.0
        assert cfg.api.rate_limit_per_minute == 60

    def test_load_prices_from_real_file(self):
        """load_prices() загружает из реального prices.yaml."""
        from space1.config.loader import load_prices
        cfg = load_prices()
        assert cfg.tools.browser == 0.01
        assert "gpt-4o" in cfg.openai

    def test_load_nonexistent_file_returns_defaults(self):
        """Несуществующий файл → default + warning."""
        from space1.config.loader import load_constants
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            cfg = load_constants(Path("/nonexistent.yaml"))
            assert len(w) == 1
            assert "Config file not found" in str(w[0].message)
        assert cfg.success_rate_base == 0.3  # default


# =============================================================================
# UNIT: load_config / get_config / reload_config
# =============================================================================

class TestConfigSingletonUnit:
    """Unit-тесты на singleton-конфигурацию."""

    def test_load_config_returns_config_object(self):
        """load_config() возвращает Config со всеми секциями."""
        from space1.config.loader import load_config
        cfg = load_config()
        assert hasattr(cfg, "constants")
        assert hasattr(cfg, "weights")
        assert hasattr(cfg, "rules")
        assert hasattr(cfg, "prices")

    def test_get_config_singleton(self):
        """get_config() возвращает тот же объект при повторном вызове."""
        from space1.config.loader import get_config
        cfg1 = get_config()
        cfg2 = get_config()
        assert cfg1 is cfg2

    def test_reload_config_creates_new_object(self):
        """reload_config() создаёт новый объект."""
        from space1.config.loader import get_config, reload_config
        cfg1 = get_config()
        cfg2 = reload_config()
        assert cfg1 is not cfg2


# =============================================================================
# INTEGRITY: Архитектурные инварианты Config Loader
# =============================================================================

class TestIntegrityConfigLoader:
    """INTEGRITY: Проверки кода loader на антипаттерны."""

    def test_no_bare_except_in_loader(self):
        """config/loader.py не содержит bare except."""
        import space1.config.loader as loader_mod
        loader_path = loader_mod.__file__
        with open(loader_path, "r") as f:
            content = f.read()
        lines = content.split("\n")
        bare_excepts = [i + 1 for i, line in enumerate(lines) if "except Exception" in line]
        assert len(bare_excepts) == 0,             f"loader.py содержит bare except на строках: {bare_excepts}"

    def test_config_dir_exists(self):
        """CONFIG_DIR существует и содержит YAML-файлы."""
        from space1.config.loader import CONFIG_DIR
        assert CONFIG_DIR.exists(), f"CONFIG_DIR {CONFIG_DIR} не существует"
        yaml_files = list(CONFIG_DIR.glob("*.yaml"))
        assert len(yaml_files) >= 4, f"Найдено только {len(yaml_files)} YAML-файлов"

    def test_constants_config_has_all_fields(self):
        """ConstantsConfig содержит все ожидаемые поля."""
        from space1.config.loader import ConstantsConfig
        cfg = ConstantsConfig()
        expected = [
            "success_rate_base", "throughput_base", "cost_base", "time_base",
            "price_per_task", "learning_rate", "knowledge_max", "initial_knowledge",
            "skill_max", "initial_skill", "ema_default_alpha", "homeostasis_target",
            "rating_min", "rating_max", "phi_cap", "psi_max", "upsilon_cap",
            "upsilon_decay", "pid_kp", "pid_ki", "pid_kd", "xi_alpha", "xi_beta",
            "phi_r_lambda_psi", "phi_r_alpha_rep"
        ]
        for field in expected:
            assert hasattr(cfg, field), f"ConstantsConfig не имеет поля {field}"


# =============================================================================
# REGRESSION: Старые баги Config Loader
# =============================================================================

class TestRegressionConfigLoader:
    """REGRESSION: Проверки, что исправленные баги не вернулись."""

    def test_yaml_fallback_works(self):
        """_simple_yaml_load работает при отсутствии PyYAML."""
        from space1.config.loader import _simple_yaml_load
        result = _simple_yaml_load("key: 42")
        assert result == {"key": 42}

    def test_load_constants_not_returns_none(self):
        """load_constants не возвращает None."""
        from space1.config.loader import load_constants
        cfg = load_constants()
        assert cfg is not None
        assert hasattr(cfg, "success_rate_base")
