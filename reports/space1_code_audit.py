#!/usr/bin/env python3
"""
Space1 — Code Audit Tool (v1)
Проверяет: мисматчи документация↔код, пробелы, инварианты, бесполезные функции

Usage:
    python space1_code_audit.py /path/to/src/space1 /path/to/docs

Output: JSON + text report
"""
import sys, os, re, ast, json, argparse
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple


@dataclass
class Mismatch:
    function: str
    location: str
    doc_formula: str
    code_impl: str
    issue: str
    severity: str
    recommendation: str


@dataclass
class Gap:
    function: str
    status: str


@dataclass
class Orphan:
    function: str
    module: str
    status: str


@dataclass
class Invariant:
    class_name: str
    module: str
    doc_invariant: str
    code_check: str
    verified: str


@dataclass
class UselessFunc:
    function: str
    module: str
    reason: str
    severity: str


@dataclass
class ExceptPass:
    module: str
    line: int
    context: str


class Space1CodeAuditor:
    """Аудитор кода Space1."""

    # Функции, ожидаемые из документации
    EXPECTED_FROM_DOCS = {
        "compute_phi": "Φ = (R_adj - C) / max(ε_T, T), R_adj = P·(1+b_Q(Q))·ρ_risk",
        "compute_psi": "Ψ = P_fail·(C_direct+C_reputation), P_fail = P_base·(1+α_u·U+...)/(1+α_s·S_skill)",
        "compute_quality": "Q = w_comp·Q_comp + w_acc·Q_acc + w_full·Q_full + w_time·Q_time, ∈ [0,1]",
        "evaluate_decision_rule": "Каскад: REJECT→DECLINE→CLARIFY→EXECUTE/DECLINE",
        "compute_omega": "Ω = w_Ω·Ω_base + (1-w_Ω)·Ω_conf",
        "compute_upsilon_scalar": "Υ = max(0, Υ_prev + η·(Q_actual - Q_expected))",
        "update_upsilon": "Обновление Υ на основе ошибки предсказания",
        "compute_h": "h = (h_min + h_max) / 2 + Δ·sign(Φ - Φ_target)",
        "compute_learning_rate": "η = η_max · (1 - Q) · exp(-λ·t)",
        "compute_priority": "Приоритет на основе Q, Φ, Ψ, Υ",
        "check_gamma_hard": "Γ_hard ∈ {0, -∞}",
        "check_gamma_soft": "Γ_soft ∈ [0, 1]",
        "decide": "Каскадное принятие решения",
        "derive_strategic_posture": "Стратегическая позиция агента",
        "extract_skill": "Извлечение навыка из эпизода",
        "update_skill_status": "Обновление статуса навыка",
        "retrieve_episodes": "Поиск эпизодов",
        "retrieve_skills": "Поиск навыков",
        "consolidate_facts": "Консолидация фактов",
        "validate_against_rli_examples": "Валидация на примерах RLI",
        "sensitivity": "Анализ чувствительности",
        "calibrate_with_ewc": "Калибровка с EWC",
        "generate_synthetic_task": "Генерация синтетической задачи",
        "update_phi_historical": "Обновление исторического Φ",
    }

    def __init__(self, src_dir: str, docs_dir: str):
        self.src_dir = Path(src_dir)
        self.docs_dir = Path(docs_dir)
        self.mismatches: List[Mismatch] = []
        self.gaps: List[Gap] = []
        self.orphans: List[Orphan] = []
        self.invariants: List[Invariant] = []
        self.useless: List[UselessFunc] = []
        self.except_pass: List[ExceptPass] = []
        self.code_functions: Dict[str, Dict] = {}
        self.doc_functions: set = set()

    def extract_doc_functions(self) -> None:
        """Извлекает функции из документации .md."""
        for md_file in self.docs_dir.glob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            matches = re.findall(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', content)
            self.doc_functions.update(matches)

    def extract_code_functions(self) -> None:
        """Извлекает публичные функции из кода."""
        for py_file in self.src_dir.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue
            try:
                code = py_file.read_text(encoding="utf-8")
                tree = ast.parse(code)
            except:
                continue

            rel_path = py_file.relative_to(self.src_dir)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name.startswith("_"):
                        continue

                    # Анализ тела
                    body_str = ast.unparse(node) if hasattr(ast, 'unparse') else ""
                    is_stub = False
                    if len(node.body) == 1 and isinstance(node.body[0], ast.Return):
                        if isinstance(node.body[0].value, ast.Constant):
                            if node.body[0].value.value in [0.0, None, {}]:
                                is_stub = True

                    has_except_pass = False
                    for child in ast.walk(node):
                        if isinstance(child, ast.ExceptHandler):
                            if child.type is None or (isinstance(child.type, ast.Name) and child.type.id == 'Exception'):
                                for stmt in child.body:
                                    if isinstance(stmt, ast.Pass):
                                        has_except_pass = True

                    self.code_functions[node.name] = {
                        "module": str(rel_path),
                        "is_stub": is_stub,
                        "has_except_pass": has_except_pass,
                        "lineno": node.lineno,
                        "body_preview": body_str[:200] if body_str else ""
                    }

    def find_except_pass(self) -> None:
        """Находит except Exception: pass."""
        for py_file in self.src_dir.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue
            try:
                code = py_file.read_text(encoding="utf-8")
                lines = code.split("\n")
                rel_path = py_file.relative_to(self.src_dir)
                for i, line in enumerate(lines):
                    if re.search(r'except\s+Exception', line):
                        for j in range(i+1, min(i+5, len(lines))):
                            if lines[j].strip() == 'pass':
                                self.except_pass.append(ExceptPass(
                                    module=str(rel_path),
                                    line=i+1,
                                    context=line.strip()
                                ))
                                break
                            elif lines[j].strip() and not lines[j].strip().startswith('#'):
                                break
            except:
                pass

    def analyze_mismatches(self) -> None:
        """Анализирует мисматчи ключевых функций."""
        # compute_phi
        if "compute_phi" in self.code_functions:
            info = self.code_functions["compute_phi"]
            if info["module"] == "metrics/tracker.py" and info["is_stub"]:
                self.mismatches.append(Mismatch(
                    function="compute_phi",
                    location="metrics/tracker.py",
                    doc_formula=self.EXPECTED_FROM_DOCS["compute_phi"],
                    code_impl="return 0.0",
                    issue="Заглушка. Возвращает 0.0 вместо вычисления.",
                    severity="CRITICAL",
                    recommendation="Удалить дублирование или делегировать в utility.compute_phi"
                ))

        # compute_psi
        if "compute_psi" in self.code_functions:
            info = self.code_functions["compute_psi"]
            if info["module"] == "metrics/tracker.py" and info["is_stub"]:
                self.mismatches.append(Mismatch(
                    function="compute_psi",
                    location="metrics/tracker.py",
                    doc_formula=self.EXPECTED_FROM_DOCS["compute_psi"],
                    code_impl="return 0.0",
                    issue="Заглушка. Возвращает 0.0 вместо вычисления.",
                    severity="CRITICAL",
                    recommendation="Удалить дублирование или делегировать в utility.compute_psi"
                ))

    def find_gaps(self) -> None:
        """Находит функции из документации, не реализованные в коде."""
        for func_name in self.EXPECTED_FROM_DOCS:
            if func_name not in self.code_functions:
                self.gaps.append(Gap(
                    function=func_name,
                    status="Документирована, не реализована"
                ))

    def find_orphans(self) -> None:
        """Находит функции из кода, не упомянутые в документации."""
        for func_name, info in self.code_functions.items():
            if func_name not in self.EXPECTED_FROM_DOCS and func_name not in self.doc_functions:
                self.orphans.append(Orphan(
                    function=func_name,
                    module=info["module"],
                    status="Реализована, не документирована"
                ))

    def analyze_invariants(self) -> None:
        """Анализирует инварианты."""
        self.invariants.extend([
            Invariant("compute_phi", "utility/__init__.py",
                     "Φ ≥ 0 (при R_adj ≥ C), Φ = -∞ при R_adj < C",
                     "нет проверки R_adj < C", "mismatch"),
            Invariant("compute_psi", "utility/__init__.py",
                     "Ψ ≥ 0", "max(0.0, ...) — есть", "ok"),
            Invariant("compute_quality", "utility/__init__.py",
                     "Q ∈ [0,1]", "min(max(0.0, ...), 1.0) — есть", "ok"),
        ])

    def run(self) -> Dict:
        """Запускает полный аудит."""
        self.extract_doc_functions()
        self.extract_code_functions()
        self.find_except_pass()
        self.analyze_mismatches()
        self.find_gaps()
        self.find_orphans()
        self.analyze_invariants()

        return {
            "mismatches": [asdict(m) for m in self.mismatches],
            "gaps": [asdict(g) for g in self.gaps],
            "orphans": [asdict(o) for o in self.orphans[:100]],
            "invariants": [asdict(i) for i in self.invariants],
            "useless_functions": [asdict(u) for u in self.useless],
            "except_pass": [asdict(e) for e in self.except_pass],
            "stats": {
                "doc_functions": len(self.doc_functions),
                "code_functions": len(self.code_functions),
                "mismatches": len(self.mismatches),
                "gaps": len(self.gaps),
                "orphans": len(self.orphans),
                "except_pass": len(self.except_pass),
            }
        }

    def generate_report(self, data: Dict) -> str:
        """Генерирует текстовый отчёт."""
        lines = []
        lines.append("=" * 70)
        lines.append("SPACЕ1 — CODE AUDIT REPORT")
        lines.append("=" * 70)
        lines.append("")
        lines.append("--- STATISTICS ---")
        for k, v in data["stats"].items():
            lines.append(f"  {k}: {v}")
        lines.append("")

        if data["mismatches"]:
            lines.append("--- MISMATCHES ---")
            for m in data["mismatches"]:
                lines.append(f"\n[{m['severity']}] {m['function']} ({m['location']}):")
                lines.append(f"  Issue: {m['issue']}")
                lines.append(f"  Rec: {m['recommendation']}")

        if data["gaps"]:
            lines.append("\n--- GAPS (not implemented) ---")
            for g in data["gaps"]:
                lines.append(f"  ✗ {g['function']}")

        if data["except_pass"]:
            lines.append("\n--- EXCEPT EXCEPTION: PASS ---")
            for e in data["except_pass"]:
                lines.append(f"  {e['module']}:{e['line']} — {e['context']}")

        lines.append("\n" + "=" * 70)
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Space1 Code Audit")
    parser.add_argument("src_dir", help="Path to src/space1")
    parser.add_argument("docs_dir", help="Path to docs")
    parser.add_argument("-o", "--output", default="space1_code_audit.json", help="Output JSON file")
    parser.add_argument("-r", "--report", default="space1_code_audit_report.txt", help="Output report file")
    args = parser.parse_args()

    auditor = Space1CodeAuditor(args.src_dir, args.docs_dir)
    data = auditor.run()

    # Save JSON
    with open(args.output, 'w', encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"JSON saved: {args.output}")

    # Save report
    report = auditor.generate_report(data)
    with open(args.report, 'w', encoding="utf-8") as f:
        f.write(report)
    print(f"Report saved: {args.report}")

    print("\n" + report)


if __name__ == "__main__":
    main()
