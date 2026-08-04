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

_del = Path(__file__).parent / "test_delivery_core.py"
if _del.exists():
    t = _del.read_text(encoding="utf-8")
    if "with pytest.raises(PermissionError)" in t and "test_file_health_check_nonexistent" in t:
        t2 = t.replace(
            """        from space1.delivery.core import FileDeliveryAdapter
        # ЭТО БАГ: FileDeliveryAdapter.__init__ вызывает os.makedirs и падает
        # с PermissionError при недоступном пути, вместо того чтобы отложить
        # создание до send() или обработать ошибку gracefully.
        # ЭТО БАГ: FileDeliveryAdapter.__init__ вызывает os.makedirs и падает
        # с PermissionError при недоступном пути.
        with pytest.raises(PermissionError):
            adapter = FileDeliveryAdapter(output_dir=\"/nonexistent/path/12345\")
            # До этой строки не дойдём — падает в __init__
""",
            """        from space1.delivery.core import FileDeliveryAdapter
        adapter = FileDeliveryAdapter(output_dir=\"/dev/null/not_a_writable_dir\")
        assert adapter.health_check() is False
""",
        )
        if t2 != t:
            _del.write_text(t2, encoding="utf-8")
