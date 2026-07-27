"""
Space1 -- Universal audit of tests against Space1 rules.

Usage:
    python test_audit.py /path/to/tests

Output: text report to stdout + test_audit_report.txt
"""
import sys, os, re, argparse
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict
from collections import defaultdict


@dataclass
class Violation:
    file: str
    line: int
    severity: str
    category: str
    detail: str
    context: str
    recommendation: str = ""


class TestAuditor:
    FORBIDDEN = [
        ("assert is not None", r"assert\s+\S+\s+is\s+not\s+None", "CRITICAL",
         "Заменить на проверку конкретного значения"),
        ("assert key in dict", r"assert\s+['\"]?\w+['\"]?\s+in\s+\w+", "CRITICAL",
         "Заменить на assert d[key] == expected"),
        ("@patch", r"@patch", "CRITICAL",
         "Удалить @patch, тестировать реальное поведение"),
        ("assert True", r"assert\s+True\b", "CRITICAL",
         "Удалить или заменить на реальную проверку"),
        ("except Exception: pass", r"except\s+Exception\s*:\s*\n?\s*pass", "CRITICAL",
         "Заменить на конкретное исключение"),
    ]

    WEAK_VERBS = {
        "creation", "matching", "mismatch", "default", "empty", "basic", "full",
        "minimal", "structure", "values", "factors", "count", "value", "attribute",
        "missing", "returns", "accepts", "stored", "behavior", "mode", "title",
        "optimal", "increases", "decreases", "exists", "ignored", "none",
        "corrupted", "loads", "on", "and", "or", "not", "if", "when"
    }

    def __init__(self, tests_dir: str):
        self.tests_dir = Path(tests_dir)
        self.violations: List[Violation] = []
        self.stats = {
            "files": 0, "tests": 0, "critical": 0, "high": 0, "medium": 0, "low": 0,
            "forbidden": 0, "weak_names": 0, "no_docstring": 0, "no_hierarchy": 0,
            "isinstance_asserts": 0, "no_none_input": 0, "no_empty_input": 0,
            "bug_comments": 0, "concept_mismatch": 0,
        }
        self.quality_scores: Dict[str, float] = defaultdict(float)

    def audit(self) -> str:
        test_files = [p for p in sorted(self.tests_dir.glob("test_*.py")) if p.name != "test_audit.py"]
        self.stats["files"] = len(test_files)
        for path in test_files:
            self._audit_file(path)
        return self._build_report()

    def _audit_file(self, path):
        code = path.read_text(encoding="utf-8")
        fname = path.name
        file_score = 1.0

        # 1. Forbidden patterns
        for label, pattern, severity, recommendation in self.FORBIDDEN:
            for m in re.finditer(pattern, code):
                line_num = code[:m.start()].count("\n") + 1
                self.violations.append(Violation(
                    fname, line_num, severity, "FORBIDDEN", label,
                    m.group(0).strip()[:60], recommendation
                ))
                self.stats["forbidden"] += 1
                self.stats[severity.lower()] += 1
                file_score -= 0.1

        # 2. Test functions
        test_funcs = list(re.finditer(r"def (test_[^\(]+)\([^)]*\):", code))
        self.stats["tests"] += len(test_funcs)

        for m in test_funcs:
            func_name = m.group(1)
            start = m.end()
            after = code[start:start + 500]
            dq = chr(34) * 3
            sq = chr(39) * 3
            has_docstring = dq in after[:400] or sq in after[:400]

            if not has_docstring:
                self.violations.append(Violation(
                    fname, 0, "CRITICAL", "NO_DOCSTRING", func_name,
                    "Нет докстринга", "Добавить докстринг: контракт + формула + обоснование"
                ))
                self.stats["no_docstring"] += 1
                self.stats["critical"] += 1
                file_score -= 0.1

            parts = func_name.split("_")
            if len(parts) >= 2 and parts[1] in self.WEAK_VERBS:
                self.violations.append(Violation(
                    fname, 0, "HIGH", "WEAK_NAME", func_name,
                    f"weak verb: {parts[1]}",
                    "Переименовать: test_<глагол>_<что>_<условие>"
                ))
                self.stats["weak_names"] += 1
                self.stats["high"] += 1
                file_score -= 0.03

            # Concept match
            if has_docstring:
                first_dq = after.find(dq)
                first_sq = after.find(sq)
                doc_end = -1
                if first_dq >= 0:
                    doc_end = after.find(dq, first_dq + 3)
                if first_sq >= 0:
                    sq_end = after.find(sq, first_sq + 3)
                    if sq_end > doc_end:
                        doc_end = sq_end
                if doc_end > 0:
                    doc = after[:doc_end].lower()
                    has_checks = "проверяем" in doc or "checks" in doc
                    has_bounds = "границы" in doc or "boundaries" in doc or "гранич" in doc
                    has_why = "почему" in doc or "why" in doc or "обоснован" in doc
                    if not (has_checks and has_bounds and has_why):
                        self.violations.append(Violation(
                            fname, 0, "MEDIUM", "CONCEPT_MISMATCH", func_name,
                            "Докстринг неполный",
                            "Добавить: Проверяем / Границы / Почему такие"
                        ))
                        self.stats["concept_mismatch"] += 1
                        self.stats["medium"] += 1
                        file_score -= 0.01

        # 3. Class hierarchy
        classes = re.findall(r"class (Test[^\(]+)", code)
        for cn in classes:
            if not any(x in cn for x in ["Unit", "Pair", "Integrity", "Regression"]):
                self.violations.append(Violation(
                    fname, 0, "HIGH", "NO_HIERARCHY", cn,
                    "Нет метки UNIT/PAIR/INTEGRITY/REGRESSION",
                    "Переименовать: Test<Function><Unit|Pair|Integrity|Regression>"
                ))
                self.stats["no_hierarchy"] += 1
                self.stats["high"] += 1
                file_score -= 0.05

        # 4. assert isinstance
        isinstance_count = len(re.findall(r"assert isinstance\(", code))
        self.stats["isinstance_asserts"] += isinstance_count
        if isinstance_count > 0:
            file_score -= 0.01 * isinstance_count

        # 5. Boundary values
        has_none_input = bool(re.search(r"\(\s*None\s*[,\)]", code))
        has_empty_input = bool(re.search(r"\(\s*\[\]\s*[,\)]", code)) or bool(re.search(r"\(\s*\{\}\s*[,\)]", code))
        if not has_none_input:
            self.stats["no_none_input"] += 1
            file_score -= 0.02
        if not has_empty_input:
            self.stats["no_empty_input"] += 1
            file_score -= 0.02

        # 6. Bug comments
        self.stats["bug_comments"] += len(re.findall(r"# ЭТО БАГ", code))

        self.quality_scores[fname] = max(0.0, min(1.0, file_score))

    def _build_report(self) -> str:
        lines = []
        lines.append("=" * 70)
        lines.append("Space1 -- AUDIT REPORT")
        lines.append("=" * 70)
        lines.append("")
        lines.append("--- STATISTICS ---")
        lines.append("  Test files:         " + str(self.stats["files"]))
        lines.append("  Test functions:     " + str(self.stats["tests"]))
        lines.append("  CRITICAL:           " + str(self.stats["critical"]))
        lines.append("  HIGH:               " + str(self.stats["high"]))
        lines.append("  MEDIUM:             " + str(self.stats["medium"]))
        lines.append("  LOW:                " + str(self.stats["low"]))
        lines.append("  Forbidden patterns: " + str(self.stats["forbidden"]))
        lines.append("  Weak names:         " + str(self.stats["weak_names"]))
        lines.append("  No docstring:       " + str(self.stats["no_docstring"]))
        lines.append("  No hierarchy:       " + str(self.stats["no_hierarchy"]))
        lines.append("  Concept mismatch:   " + str(self.stats["concept_mismatch"]))
        lines.append("  assert isinstance:  " + str(self.stats["isinstance_asserts"]))
        lines.append("  Files without None: " + str(self.stats["no_none_input"]))
        lines.append("  Files without empty:" + str(self.stats["no_empty_input"]))
        lines.append("  # BUG comments:     " + str(self.stats["bug_comments"]))
        lines.append("")
        lines.append("--- QUALITY SCORES ---")
        for fname, score in sorted(self.quality_scores.items(), key=lambda x: x[1], reverse=True):
            bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
            lines.append(f"  [{bar}] {score:.2f}  {fname}")
        lines.append("")

        if self.violations:
            lines.append("--- VIOLATIONS ---")
            current_file = None
            for v in sorted(self.violations, key=lambda x: (x.file, x.line, x.detail)):
                if v.file != current_file:
                    lines.append("")
                    lines.append(v.file + ":")
                    current_file = v.file
                loc = "L" + str(v.line) if v.line > 0 else ""
                sev = {"CRITICAL": "C", "HIGH": "H", "MEDIUM": "M", "LOW": "L"}.get(v.severity, "?")
                lines.append(f"  [{sev}] [{v.severity:8s}] [{v.category:12s}] {loc:6s} {v.detail}")
                if v.recommendation:
                    lines.append(f"     -> {v.recommendation}")
        else:
            lines.append("--- NO VIOLATIONS ---")

        lines.append("")
        lines.append("=" * 70)
        lines.append("END OF REPORT")
        lines.append("=" * 70)
        sep = chr(10)
        return sep.join(lines)


def main():
    parser = argparse.ArgumentParser(description="Audit Space1 tests")
    parser.add_argument("tests_dir", nargs="?", default=".", help="Tests directory")
    args = parser.parse_args()
    auditor = TestAuditor(args.tests_dir)
    report = auditor.audit()
    print(report)
    out_path = Path(args.tests_dir) / "test_audit_report.txt"
    out_path.write_text(report, encoding="utf-8")
    print("\nReport saved: " + str(out_path))


if __name__ == "__main__":
    main()
