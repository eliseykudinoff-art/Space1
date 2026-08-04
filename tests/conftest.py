"""Ensure space1 → srs and normalize hardcoded src/space1 paths in tests."""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

srs = ROOT / "srs"
space1 = ROOT / "space1"
if srs.is_dir() and not space1.exists():
    try:
        space1.symlink_to("srs")
    except OSError:
        pass

_phase4 = Path(__file__).parent / "test_phase4_fixes.py"
if _phase4.exists():
    t = _phase4.read_text(encoding="utf-8")
    t2 = t.replace('"src" / "space1"', '"srs"').replace("src/space1", "srs")
    t2 = t2.replace(
        'os.path.join(os.path.dirname(__file__), "..", "src")',
        'os.path.join(os.path.dirname(__file__), "..")',
    )
    if t2 != t:
        _phase4.write_text(t2, encoding="utf-8")
