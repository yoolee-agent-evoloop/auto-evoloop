from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_core_skill_files_have_public_stage_contract_sections() -> None:
    required_sections = [
        "## Purpose",
        "## Inputs",
        "## Outputs",
        "## Procedure",
        "## Human Gate",
        "## Failure Modes",
    ]
    skill_files = sorted((ROOT / "core_skills").glob("**/SKILL.md"))
    assert skill_files

    missing: dict[str, list[str]] = {}
    for path in skill_files:
        text = path.read_text(encoding="utf-8")
        absent = [section for section in required_sections if section not in text]
        if absent:
            missing[str(path.relative_to(ROOT))] = absent

    assert missing == {}
