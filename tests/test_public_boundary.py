from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_chinese_text_is_limited_to_readme_and_core_methodology() -> None:
    chinese = re.compile(r"[\u4e00-\u9fff]")
    checked_roots = [
        ROOT / "CONTRIBUTING.md",
        ROOT / "docs",
        ROOT / "core_skills",
        ROOT / "examples",
        ROOT / "tests",
        ROOT / "pyproject.toml",
    ]

    offending: list[str] = []
    for checked_root in checked_roots:
        paths = [checked_root] if checked_root.is_file() else checked_root.rglob("*")
        for path in paths:
            if path.is_file() and path.suffix in {".md", ".py", ".html", ".yaml", ".yml", ".toml"}:
                relative = path.relative_to(ROOT)
                if relative == Path("CONTRIBUTING.md") or relative.parts[0] == "core_skills":
                    continue
                if chinese.search(path.read_text(encoding="utf-8")):
                    offending.append(str(relative))

    assert offending == []


def test_required_public_alpha_docs_exist() -> None:
    required = [
        "README.md",
        "CONTRIBUTING.md",
        "docs/README.md",
        "docs/quickstart.md",
        "docs/concepts.md",
        "docs/architecture.md",
        "docs/sanitization-policy.md",
        "docs/public-migration-inventory.md",
        "core_skills/DESIGN.md",
        "core_skills/CONTEXT.md",
        "core_skills/README.md",
    ]

    missing = [path for path in required if not (ROOT / path).exists()]
    assert missing == []
