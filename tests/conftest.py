"""Ensure space1 package resolves to srs/."""
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
