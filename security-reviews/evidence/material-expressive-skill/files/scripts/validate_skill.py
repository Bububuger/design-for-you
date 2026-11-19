#!/usr/bin/env python3
"""Validate Agent Skill metadata and local Markdown references."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
INLINE_PATH_PATTERN = re.compile(r"\x60((?:references|templates)/[^\x60]+)\x60")
MAX_DESCRIPTION_LENGTH = 1024
MAX_SKILL_LINES = 500


def read_frontmatter(skill_file: Path) -> tuple[dict[str, str], str | None]:
    """Return simple top-level YAML values and the Markdown body."""
    content = skill_file.read_text(encoding="utf-8")
    if not content.startswith("---\n"):
        return {}, None

    closing = re.search(r"(?m)^---\s*$", content[4:])
    if closing is None:
        return {}, None

    frontmatter = content[4 : 4 + closing.start()]
    body = content[4 + closing.end() :]
    metadata: dict[str, str] = {}
    for line in frontmatter.splitlines():
        key, separator, value = line.partition(":")
        if separator:
            metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata, body


def _is_inside_root(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def validate(root: Path) -> list[str]:
    """Return all detected validation errors for a skill directory."""
    root = root.resolve()
    skill_file = root / "SKILL.md"
    errors: list[str] = []

    if not skill_file.is_file():
        return ["Missing required root file: SKILL.md"]

    try:
        metadata, body = read_frontmatter(skill_file)
    except (OSError, UnicodeError) as error:
        return [f"Could not read SKILL.md: {error}"]

    if body is None:
        errors.append("SKILL.md must start with YAML frontmatter delimited by ---")
        body = ""

    name = metadata.get("name", "")
    description = metadata.get("description", "")

    if not name:
        errors.append("Frontmatter is missing the required 'name' field")
    elif not NAME_PATTERN.fullmatch(name):
        errors.append("Skill name must use lowercase letters, numbers, and single hyphens")
    elif name != root.name:
        errors.append(
            f"Skill name '{name}' must match the skill directory name '{root.name}'"
        )

    if not description:
        errors.append("Frontmatter is missing the required 'description' field")
    elif len(description) > MAX_DESCRIPTION_LENGTH:
        errors.append(
            f"Description exceeds {MAX_DESCRIPTION_LENGTH} characters "
            f"({len(description)} found)"
        )

    line_count = len(skill_file.read_text(encoding="utf-8").splitlines())
    if line_count > MAX_SKILL_LINES:
        errors.append(
            f"SKILL.md has {line_count} lines; keep it at or below {MAX_SKILL_LINES}"
        )

    markdown_files = [skill_file, *root.rglob("*.md")]
    seen: set[Path] = set()
    for markdown_file in markdown_files:
        markdown_file = markdown_file.resolve()
        if markdown_file in seen or not _is_inside_root(markdown_file, root):
            continue
        seen.add(markdown_file)

        try:
            content = markdown_file.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            errors.append(f"Could not read {markdown_file.relative_to(root)}: {error}")
            continue

        destinations = [match.group(1).strip() for match in LINK_PATTERN.finditer(content)]
        destinations.extend(INLINE_PATH_PATTERN.findall(content))

        for destination in destinations:
            destination = destination.strip().strip("<>")
            parsed = urlsplit(destination)

            if parsed.scheme or destination.startswith("#") or not parsed.path:
                continue

            local_path = (markdown_file.parent / unquote(parsed.path)).resolve()
            if not _is_inside_root(local_path, root):
                errors.append(
                    f"{markdown_file.relative_to(root)}: reference escapes the skill directory: "
                    f"{destination}"
                )
            elif not local_path.exists():
                errors.append(
                    f"{markdown_file.relative_to(root)}: missing local reference: {destination}"
                )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Path to the skill directory (defaults to this repository)",
    )
    args = parser.parse_args()

    errors = validate(args.root)
    if errors:
        print("Skill validation failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(f"Skill validation passed: {args.root.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
