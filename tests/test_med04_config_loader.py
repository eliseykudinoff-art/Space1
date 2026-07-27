"""Тесты [MED-04]: Config loader warning."""
import sys, os, warnings
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from space1.config.loader import load_constants, CONFIG_DIR

def test_config_dir_exists():
    assert CONFIG_DIR is not None

def test_missing_config_warns():
    from pathlib import Path
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = load_constants(Path("/nonexistent/config.yaml"))
        assert len(w) == 1
        assert "Config file not found" in str(w[0].message)
        assert result.success_rate_base == 0.3  # default
