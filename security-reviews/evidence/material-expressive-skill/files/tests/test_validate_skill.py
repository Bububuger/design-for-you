"""Tests for the dependency-free Agent Skill validator."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_skill import read_frontmatter, validate  # noqa: E402


class ValidateSkillTests(unittest.TestCase):
    def _make_skill(self, parent: Path, body: str = "") -> Path:
        skill_root = parent / "sample-skill"
        skill_root.mkdir()
        (skill_root / "SKILL.md").write_text(
            "---\n"
            "name: sample-skill\n"
            "description: A test skill for validating local references.\n"
            "license: MIT\n"
            "---\n\n"
            f"{body}",
            encoding="utf-8",
        )
        return skill_root

    def test_repository_is_valid(self) -> None:
        self.assertEqual(validate(ROOT), [])

    def test_missing_skill_file_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "empty-skill"
            root.mkdir()
            self.assertIn("Missing required root file: SKILL.md", validate(root))

    def test_name_must_match_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._make_skill(Path(directory))
            skill_file = root / "SKILL.md"
            skill_file.write_text(
                skill_file.read_text(encoding="utf-8").replace(
                    "name: sample-skill", "name: another-skill"
                ),
                encoding="utf-8",
            )
            self.assertTrue(
                any("must match the skill directory name" in e for e in validate(root))
            )

    def test_broken_local_link_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._make_skill(Path(directory), "[Missing](references/missing.md)")
            errors = validate(root)
            self.assertTrue(any("missing local reference" in e for e in errors))

    def test_frontmatter_is_parsed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._make_skill(Path(directory), "Instructions.")
            metadata, body = read_frontmatter(root / "SKILL.md")
            self.assertEqual(metadata["name"], "sample-skill")
            self.assertIn("Instructions.", body or "")


if __name__ == "__main__":
    unittest.main()
