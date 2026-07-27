"""
Space1 — E2E Test Logger

Каждый тест генерирует ОДИН документ-лог.
Лог перезаписывается при каждом запуске (не плодит файлы).
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List


class E2ETestLogger:
    """
    Централизованный логгер для E2E тестов.
    Каждый тест = один файл лога.
    """
    _logs: List[str] = []
    _test_name: str = ""
    _output_dir: Path = None
    _current_file: Path = None

    @classmethod
    def start_test(cls, test_name: str, output_dir: str = None):
        """Начать новый тест, очистить логи."""
        cls._test_name = test_name
        cls._logs = []

        if output_dir:
            cls._output_dir = Path(output_dir)
        else:
            # Стандартная директория: project_root/e2e_test_logs/
            cls._output_dir = Path(__file__).parent.parent / "e2e_test_logs"

        cls._output_dir.mkdir(parents=True, exist_ok=True)

        # Фиксированное имя файла: перезаписываем каждый раз
        safe_name = test_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
        cls._current_file = cls._output_dir / f"{safe_name}.log"

        cls.log("="*80)
        cls.log(f"E2E TEST STARTED: {test_name}")
        cls.log(f"Timestamp: {datetime.now().isoformat()}")
        cls.log("="*80)

    @classmethod
    def log(cls, message: str, level: str = "INFO"):
        """Добавить сообщение в лог и напечатать."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        formatted = f"[{timestamp}] [{level:8}] {message}"
        cls._logs.append(formatted)
        print(formatted)

    @classmethod
    def log_value(cls, name: str, value: Any, description: str = "", unit: str = ""):
        """Логировать значение с описанием."""
        desc_part = f" — {description}" if description else ""
        unit_part = f" [{unit}]" if unit else ""
        cls.log(f"  {name}: {value}{unit_part}{desc_part}")

    @classmethod
    def log_dict(cls, data: Dict, title: str = "", indent: int = 2):
        """Логировать словарь в читаемом формате."""
        if title:
            cls.log(title)
        for key, value in data.items():
            if isinstance(value, dict):
                cls.log(f"{' ' * indent}{key}:")
                for k2, v2 in value.items():
                    cls.log(f"{' ' * (indent+2)}{k2}: {v2}")
            elif isinstance(value, list):
                cls.log(f"{' ' * indent}{key}: [{len(value)} items]")
                for i, item in enumerate(value[:5]):
                    cls.log(f"{' ' * (indent+2)}[{i}] {item}")
                if len(value) > 5:
                    cls.log(f"{' ' * (indent+2)}... and {len(value)-5} more")
            else:
                cls.log(f"{' ' * indent}{key}: {value}")

    @classmethod
    def log_stage(cls, stage_num: int, stage_name: str, status: str = "START"):
        """Логировать начало/конец Stage."""
        cls.log("\n" + "─"*80)
        cls.log(f"STAGE {stage_num}: {stage_name} [{status}]")
        cls.log("─"*80)

    @classmethod
    def log_decision(cls, decision: str, reason: str, factors: Dict = None):
        """Логировать решение с обоснованием."""
        cls.log("\n" + "▓"*80)
        cls.log(f"DECISION: {decision}")
        cls.log(f"REASON: {reason}")
        if factors:
            cls.log("FACTORS:")
            for k, v in factors.items():
                cls.log(f"  {k}: {v}")
        cls.log("▓"*80)

    @classmethod
    def log_table(cls, headers: List[str], rows: List[List[Any]], title: str = ""):
        """Логировать таблицу."""
        if title:
            cls.log(title)
        # Заголовок
        header_str = " | ".join(str(h)[:20] for h in headers)
        cls.log(f"  {header_str}")
        cls.log("  " + "-" * len(header_str))
        # Строки
        for row in rows:
            cls.log("  " + " | ".join(str(v)[:20] for v in row))

    @classmethod
    def log_input(cls, entity_type: str, entity_id: str, data: Dict):
        """Логировать входной сигнал."""
        cls.log("\n" + "▲"*40 + " INPUT " + "▲"*40)
        cls.log(f"{entity_type}: {entity_id}")
        cls.log_dict(data)
        cls.log("▲"*80)

    @classmethod
    def log_output(cls, entity_type: str, entity_id: str, data: Dict):
        """Логировать выходной сигнал."""
        cls.log("\n" + "▼"*40 + " OUTPUT " + "▼"*39)
        cls.log(f"{entity_type}: {entity_id}")
        cls.log_dict(data)
        cls.log("▼"*80)

    @classmethod
    def end_test(cls, passed: bool = True, error: str = None):
        """Завершить тест, сохранить лог в файл (перезаписать)."""
        cls.log("\n" + "="*80)
        if passed:
            cls.log(f"✅ E2E TEST PASSED: {cls._test_name}")
        else:
            cls.log(f"❌ E2E TEST FAILED: {cls._test_name}")
            if error:
                cls.log(f"   Error: {error}")
        cls.log("="*80)

        # Сохраняем в файл (перезаписываем)
        if cls._current_file:
            with open(cls._current_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(cls._logs))
            cls.log(f"📁 Log saved to: {cls._current_file}")

        return cls._current_file
