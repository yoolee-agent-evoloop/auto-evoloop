from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_core_skill_files_have_public_stage_contract_sections() -> None:
    required_markers = {
        "purpose": ["## Purpose", "## \u9002\u7528", "# Trace Prep", "# Single Case Analyzer", "# Fix Planner", "# Fix Executor", "# Meta-Reflection"],
        "inputs": ["## Inputs", "## \u8f93\u5165", "## \u8f93\u5165\u7269\u6599", "\u8f93\u5165\uff1a"],
        "outputs": ["## Outputs", "## \u8f93\u51fa", "## \u8f93\u51fa Artifact", "\u8f93\u51fa\uff1a"],
        "procedure": ["## Procedure", "## \u6267\u884c\u6d41\u7a0b", "## Step", "## Phase"],
        "human_gate": ["## Human Gate", "## HITL", "HITL", "\u4eba\u5de5 review", "AskUserQuestion"],
        "failure_modes": ["## Failure Modes", "\u5931\u8d25", "\u5f02\u5e38", "\u56de\u9000", "\u7194\u65ad", "\u5931\u6548", "fallback"],
    }
    skill_files = sorted((ROOT / "core_skills").glob("**/SKILL.md"))
    assert skill_files

    missing: dict[str, list[str]] = {}
    for path in skill_files:
        text = path.read_text(encoding="utf-8")
        absent = [
            name
            for name, markers in required_markers.items()
            if not any(marker in text for marker in markers)
        ]
        if absent:
            missing[str(path.relative_to(ROOT))] = absent

    assert missing == {}
