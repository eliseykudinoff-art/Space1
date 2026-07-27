# Space1 — Описание тестов: Config Loader

> **Дата:** 2026-07-25
> **Автор:** AI-ревьюер
> **Статус:** Актуально для Space1 Phase 4 Fix 22
> **Файл теста:** `test_config_loader.py`
> **Результат:** 38/38 тестов пройдены (pytest)

---

## Часть I. Философия теста

Тестовый набор проверяет модуль `config/loader.py` — загрузчик конфигурации из YAML.

Каждый тест:
- Проверен против реального кода
- Имеет докстринг = контракт + обоснование
- FAILED = реальный баг

---

## Часть II. Структура тестов

### UNIT: _parse_scalar (`TestParseScalarUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_parse_int` | '42' → 42 | PASS |
| `test_parse_float` | '3.14' → 3.14 | PASS |
| `test_parse_scientific_notation` | '3.0e2' → 300.0 | PASS |
| `test_parse_true` | 'true'/'TRUE' → True | PASS |
| `test_parse_false` | 'false'/'False' → False | PASS |
| `test_parse_quoted_string` | '"hello"' → 'hello' | PASS |
| `test_parse_list` | '[1,2,3]' → [1,2,3] | PASS |
| `test_parse_empty_list` | '[]' → [] | PASS |
| `test_parse_list_with_strings` | '["a","b"]' → ['a','b'] | PASS |
| `test_parse_empty_string` | '' → {} | PASS |
| `test_parse_unquoted_string` | 'hello' → 'hello' | PASS |
| `test_parse_strips_whitespace` | '  42  ' → 42 | PASS |

### UNIT: _simple_yaml_load (`TestSimpleYamlLoadUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_simple_key_value` | 'key: value' → dict | PASS |
| `test_nested_dict` | Вложенность → nested dict | PASS |
| `test_list_values` | '- item' → list | PASS |
| `test_comments_ignored` | # комментарии игнорируются | PASS |
| `test_empty_lines_ignored` | Пустые строки игнорируются | PASS |
| `test_mixed_list_and_dict` | Список внутри dict | PASS |
| `test_deep_nesting` | Глубокая вложенность | PASS |
| `test_returns_dict_for_empty` | Пустой input → {} | PASS |

### UNIT: _dict_to_dataclass (`TestDictToDataclassUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_partial_data_uses_defaults` | Частичные данные + defaults | PASS |
| `test_none_returns_defaults` | None → полный default | PASS |
| `test_extra_keys_ignored` | Лишние ключи игнорируются | PASS |
| `test_nested_dataclass` | Вложенный dict → dataclass | PASS |
| `test_dict_fields_preserved` | Dict-поля сохраняются | PASS |

### UNIT: load_* functions (`TestLoadFunctionsUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_load_constants_from_real_file` | constants.yaml загружается | PASS |
| `test_load_weights_from_real_file` | weights.yaml загружается | PASS |
| `test_load_rules_from_real_file` | rules.yaml загружается | PASS |
| `test_load_prices_from_real_file` | prices.yaml загружается | PASS |
| `test_load_nonexistent_file_returns_defaults` | Несуществующий → default + warning | PASS |

### UNIT: Singleton (`TestConfigSingletonUnit`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_load_config_returns_config_object` | Config со всеми секциями | PASS |
| `test_get_config_singleton` | Один и тот же объект | PASS |
| `test_reload_config_creates_new_object` | reload → новый объект | PASS |

### INTEGRITY (`TestIntegrityConfigLoader`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_no_bare_except_in_loader` | Нет bare except | PASS |
| `test_config_dir_exists` | CONFIG_DIR существует | PASS |
| `test_constants_config_has_all_fields` | Все поля ConstantsConfig | PASS |

### REGRESSION (`TestRegressionConfigLoader`)

| Тест | Что проверяет | Статус |
|------|---------------|--------|
| `test_yaml_fallback_works` | _simple_yaml_load без PyYAML | PASS |
| `test_load_constants_not_returns_none` | Не возвращает None | PASS |

---

## Часть III. Сводка

**Итого: 38 тестов, 38 пройдены, 0 skipped, 0 xfailed.**

Багов не обнаружено. Все контракты подтверждены:
- `_parse_scalar` корректно парсит int, float, bool, string, list
- `_simple_yaml_load` корректно обрабатывает вложенность, списки, комментарии
- `_dict_to_dataclass` использует defaults для отсутствующих полей
- `load_*` функции загружают реальные YAML-файлы или возвращают defaults
- Singleton pattern работает: `get_config()` → кэш, `reload_config()` → новый объект

---

*Документ создан: 2026-07-25*  
*Версия: 1.0*  
*Статус: Актуально для Space1 Phase 4 Fix 22*
