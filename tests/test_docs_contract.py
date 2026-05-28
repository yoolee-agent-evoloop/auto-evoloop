from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_PUBLIC_METHOD_FILES = [
    "core_skills/DESIGN.md",
    "core_skills/CONTEXT.md",
    "core_skills/00_meta/entropy-control/CHECKLIST.md",
    "core_skills/00_meta/meta-reflection/stages/S1.md",
    "core_skills/00_meta/meta-reflection/stages/S2.md",
    "core_skills/00_meta/meta-reflection/stages/S3.md",
    "core_skills/00_meta/meta-reflection/stages/S4.md",
    "core_skills/01_prepare/auto-trace-prep/references/environment-setup.md",
    "core_skills/02_analyze/auto-single-case-analyzer/references/attribution-framework.md",
    "core_skills/02_analyze/auto-single-case-analyzer/references/repair-principles-v1.6.0.md",
    "core_skills/02_analyze/auto-single-case-analyzer/references/report-templates.md",
    "core_skills/03_plan/auto-fix-planner/references/fix-plan-templates.md",
    "core_skills/04_execute/auto-fix-executor/references/optimization-report-template.md",
    "docs/alpha1-migration-plan.md",
]


def test_required_public_method_files_exist() -> None:
    missing = [path for path in REQUIRED_PUBLIC_METHOD_FILES if not (ROOT / path).exists()]
    assert missing == []


def test_only_readme_contains_chinese_text() -> None:
    chinese = re.compile(r"[\u4e00-\u9fff]")
    checked_roots = [
        ROOT / "CONTRIBUTING.md",
        ROOT / "docs",
        ROOT / "core_skills",
        ROOT / "examples",
    ]
    offending: list[str] = []
    for checked_root in checked_roots:
        paths = [checked_root] if checked_root.is_file() else checked_root.rglob("*")
        for path in paths:
            if path.is_file() and path.suffix in {".md", ".py", ".html", ".yaml", ".yml", ".toml"}:
                if chinese.search(path.read_text(encoding="utf-8")):
                    offending.append(str(path.relative_to(ROOT)))
    assert offending == []
