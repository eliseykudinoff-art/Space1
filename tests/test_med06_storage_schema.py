"""Тесты [MED-06]: StorageManager schema_version."""
import sys, os, json, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from space1.memory.storage import AIOSStorageManager, MemoryEntry

def test_memory_entry_has_schema():
    e = MemoryEntry("k", "v")
    d = e.to_dict()
    assert "_schema_version" in d
    assert d["_schema_version"] == "1.0"

def test_storage_schema_version_check():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode='w') as f:
        json.dump({"_storage_version": "0.5", "entries": []}, f)
        path = f.name
    try:
        import logging
        logging.basicConfig(level=logging.WARNING)
        mgr = AIOSStorageManager(filepath=path)
        assert mgr._store == []
    finally:
        os.unlink(path)

def test_storage_save_load_roundtrip():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    try:
        mgr1 = AIOSStorageManager(filepath=path)
        mgr1._store = [MemoryEntry("test", {"data": 42})]
        mgr1._save_to_disk()

        mgr2 = AIOSStorageManager(filepath=path)
        assert len(mgr2._store) == 1
        assert mgr2._store[0].key == "test"
        assert mgr2._store[0].value["data"] == 42
    finally:
        os.unlink(path)
