"""
Storage Migrator — BUG-026 FIX
================================
Механизм миграции состояния между версиями схемы.

Reference: баги.txt BUG-026
"""

import json
import logging
from typing import Dict, Any, List, Callable, Tuple
from datetime import datetime

logger = logging.getLogger("storage_migrator")


class SchemaMigration:
    """
    Миграция одной версии схемы в другую.
    """
    def __init__(self, from_version: str, to_version: str, migrate_fn: Callable[[Dict], Dict]):
        self.from_version = from_version
        self.to_version = to_version
        self.migrate_fn = migrate_fn
    
    def migrate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнить миграцию."""
        return self.migrate_fn(data)


class StorageMigrator:
    """
    BUG-026 FIX: Мигратор схем хранилища.
    
    Поддерживает цепочки миграций между версиями.
    """
    
    def __init__(self, current_version: str = "1.0"):
        self.current_version = current_version
        self._migrations: List[SchemaMigration] = []
        
        # Регистрируем известные миграции
        self._register_builtin_migrations()
    
    def _register_builtin_migrations(self):
        """Регистрируем встроенные миграции."""
        # Миграция с 0.0 -> 1.0 (добавление schema version)
        self.register_migration("0.0", "1.0", self._migrate_v0_to_v1)
    
    @staticmethod
    def _migrate_v0_to_v1(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Миграция с v0.0 на v1.0.
        
        Changes:
        - Добавлен _storage_version
        - entries обёрнуты в объект
        """
        logger.info("Migrating storage from v0.0 to v1.0")
        
        # Если это уже новый формат
        if "_storage_version" in data:
            return data
        
        # Если это список (legacy формат)
        if isinstance(data, list):
            return {
                "_storage_version": "1.0",
                "entries": data
            }
        
        # Если это dict без версии
        return {
            "_storage_version": "1.0",
            "entries": data.get("entries", data.get("memories", []))
        }
    
    def register_migration(self, from_version: str, to_version: str, migrate_fn: Callable[[Dict], Dict]):
        """Зарегистрировать миграцию."""
        migration = SchemaMigration(from_version, to_version, migrate_fn)
        self._migrations.append(migration)
        logger.info(f"Registered migration: {from_version} -> {to_version}")
    
    def get_migration_path(self, from_version: str) -> List[SchemaMigration]:
        """
        Найти путь миграции от from_version до current_version.
        
        Returns:
            Список миграций для применения
        """
        if from_version == self.current_version:
            return []
        
        # Простой линейный поиск
        path = []
        current = from_version
        
        while current != self.current_version:
            found = False
            for migration in self._migrations:
                if migration.from_version == current:
                    path.append(migration)
                    current = migration.to_version
                    found = True
                    break
            
            if not found:
                raise ValueError(f"No migration path from {from_version} to {self.current_version}")
        
        return path
    
    def migrate(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """
        Выполнить миграцию данных до текущей версии.
        
        Args:
            data: Данные для миграции
            
        Returns:
            Tuple[data, applied_migrations]
        """
        # Определяем текущую версию данных
        # Поддержка legacy формата (список)
        if isinstance(data, list):
            version = "0.0"
        else:
            version = data.get("_storage_version", "0.0")
        
        if version == self.current_version:
            return data, []
        
        # Находим путь миграции
        path = self.get_migration_path(version)
        
        if not path:
            return data, []
        
        # Применяем миграции
        applied = []
        for migration in path:
            logger.info(f"Applying migration: {migration.from_version} -> {migration.to_version}")
            data = migration.migrate(data)
            applied.append(f"{migration.from_version} -> {migration.to_version}")
        
        return data, applied
    
    def needs_migration(self, data: Dict[str, Any]) -> bool:
        """Проверить, нужна ли миграция."""
        version = data.get("_storage_version", "0.0")
        return version != self.current_version


def migrate_storage_file(filepath: str, backup: bool = True) -> Tuple[bool, List[str]]:
    """
    Мигрировать файл хранилища.
    
    Args:
        filepath: Путь к файлу
        backup: Создать ли backup перед миграцией
        
    Returns:
        Tuple[migrated, applied_migrations]
    """
    import os
    
    if not os.path.exists(filepath):
        logger.warning(f"Storage file not found: {filepath}")
        return False, []
    
    # Читаем данные
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Мигрируем
    migrator = StorageMigrator()
    
    if not migrator.needs_migration(data):
        logger.info("Storage already at current version")
        return False, []
    
    migrated_data, applied = migrator.migrate(data)
    
    if not applied:
        return False, []
    
    # Backup
    if backup:
        backup_path = f"{filepath}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Created backup: {backup_path}")
    
    # Записываем мигрированные данные
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(migrated_data, f, indent=2)
    
    logger.info(f"Migration complete: {applied}")
    return True, applied


if __name__ == "__main__":
    # Тест миграции
    migrator = StorageMigrator()
    
    # Legacy формат
    legacy_data = [
        {"key": "test", "value": "val", "importance": 0.5, "timestamp": datetime.now().isoformat()}
    ]
    
    migrated, applied = migrator.migrate(legacy_data)
    print(f"Applied: {applied}")
    print(f"Migrated data: {migrated}")
