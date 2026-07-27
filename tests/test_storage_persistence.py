"""
Тесты на повреждение persistence — BUG-042 FIX

Tests for corrupted file, partial write, empty storage, etc.
"""

import pytest
import json
import os
import tempfile
from datetime import datetime

from space1.memory.storage import AIOSStorageManager, MemoryEntry


class TestStorageCorruption:
    """BUG-042: Тесты на повреждение persistence."""
    
    def test_corrupted_json_file(self):
        """Тест: JSON файл повреждён."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{ "broken": json }')
            filepath = f.name
        
        try:
            storage = AIOSStorageManager(filepath)
            assert storage._store == []
        finally:
            os.unlink(filepath)
    
    def test_empty_json_file(self):
        """Тест: Пустой JSON файл."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('')
            filepath = f.name
        
        try:
            storage = AIOSStorageManager(filepath)
            assert storage._store == []
        finally:
            os.unlink(filepath)
    
    def test_valid_json_no_entries(self):
        """Тест: Валидный JSON без entries."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"_storage_version": "1.0", "entries": []}, f)
            filepath = f.name
        
        try:
            storage = AIOSStorageManager(filepath)
            assert len(storage._store) == 0
        finally:
            os.unlink(filepath)
    
    def test_valid_json_with_entries(self):
        """Тест: Валидный JSON с entries."""
        entries = [
            {"key": "test1", "value": "value1", "importance": 0.5, "timestamp": datetime.now().isoformat(), "_schema_version": "1.0"},
            {"key": "test2", "value": "value2", "importance": 0.8, "timestamp": datetime.now().isoformat(), "_schema_version": "1.0"},
        ]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"_storage_version": "1.0", "entries": entries}, f)
            filepath = f.name
        
        try:
            storage = AIOSStorageManager(filepath)
            assert len(storage._store) == 2
            assert storage._store[0].key == "test1"
            assert storage._store[1].key == "test2"
        finally:
            os.unlink(filepath)
    
    def test_partial_json_write(self):
        """Тест: Частичная запись (неполный JSON)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"_storage_version": "1.0", "entries": [{"key": "test", "value": "val')
            filepath = f.name
        
        try:
            storage = AIOSStorageManager(filepath)
            assert storage._store == []
        finally:
            os.unlink(filepath)
    
    def test_invalid_entry_data(self):
        """Тест: Entry с невалидными данными (BUG-039 validation)."""
        entries = [
            {"key": "valid", "value": "ok", "importance": 0.5, "timestamp": datetime.now().isoformat(), "_schema_version": "1.0"},
            {"key": "", "value": "empty_key", "importance": 0.5, "timestamp": datetime.now().isoformat(), "_schema_version": "1.0"},  # Invalid: empty key
            {"key": "invalid_importance", "value": "val", "importance": 1.5, "timestamp": datetime.now().isoformat(), "_schema_version": "1.0"},  # Invalid: > 1.0
            {"key": "future_time", "value": "val", "importance": 0.5, "timestamp": "2099-01-01T00:00:00", "_schema_version": "1.0"},  # Invalid: future timestamp
        ]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"_storage_version": "1.0", "entries": entries}, f)
            filepath = f.name
        
        try:
            storage = AIOSStorageManager(filepath)
            # Должен остаться только валидный entry
            assert len(storage._store) == 1
            assert storage._store[0].key == "valid"
        finally:
            os.unlink(filepath)
    
    def test_legacy_format_compatibility(self):
        """Тест: Совместимость с legacy форматом (без _storage_version)."""
        entries = [
            {"key": "old1", "value": "val1", "importance": 0.5, "timestamp": datetime.now().isoformat()},
            {"key": "old2", "value": "val2", "importance": 0.7, "timestamp": datetime.now().isoformat()},
        ]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(entries, f)  # Legacy format: просто список
            filepath = f.name
        
        try:
            storage = AIOSStorageManager(filepath)
            assert len(storage._store) == 2
        finally:
            os.unlink(filepath)
    
    def test_schema_version_mismatch_warning(self):
        """Тест: Предупреждение при несовпадении версии схемы."""
        entries = [
            {"key": "test", "value": "val", "importance": 0.5, "timestamp": datetime.now().isoformat(), "_schema_version": "0.5"},
        ]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"_storage_version": "0.9", "entries": entries}, f)
            filepath = f.name
        
        try:
            storage = AIOSStorageManager(filepath)
            # Загружается, но с предупреждением
            assert len(storage._store) == 1
        finally:
            os.unlink(filepath)


class TestStorageWrite:
    """Тесты записи."""
    
    def test_persist_adds_entry(self):
        """Тест: persist() добавляет entry."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            filepath = f.name
        
        try:
            storage = AIOSStorageManager(filepath)
            storage.persist("key1", "value1", 0.7)
            
            assert len(storage._store) == 1
            assert storage._store[0].key == "key1"
            assert storage._store[0].value == "value1"
        finally:
            os.unlink(filepath)
    
    def test_persist_saves_to_disk(self):
        """Тест: persist() сохраняет на диск."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            filepath = f.name
        
        try:
            storage = AIOSStorageManager(filepath)
            storage.persist("key1", "value1", 0.7)
            
            # Загружаем заново
            storage2 = AIOSStorageManager(filepath)
            assert len(storage2._store) == 1
            assert storage2._store[0].key == "key1"
        finally:
            os.unlink(filepath)
    
    def test_clear_removes_all(self):
        """Тест: clear() удаляет все entries."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            filepath = f.name
        
        try:
            storage = AIOSStorageManager(filepath)
            storage.persist("key1", "value1", 0.7)
            storage.persist("key2", "value2", 0.5)
            
            storage.clear()
            
            assert len(storage._store) == 0
            assert not os.path.exists(filepath)
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
