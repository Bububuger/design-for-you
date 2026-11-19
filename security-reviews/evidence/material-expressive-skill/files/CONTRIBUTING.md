# Contributing

Thank you for helping improve Material 3 Expressive Skill. Contributions should make the guidance more accurate, useful, accessible, and maintainable for people building products across platforms.

## Before opening a pull request

1. Search the existing references and issues so guidance is not duplicated.
2. Prefer official Material, Android, W3C, and platform documentation for normative or version-sensitive claims.
3. Clearly separate official requirements from recommendations, examples, and platform-specific interpretation.
4. Verify component names, API signatures, release channels, and dependency versions against current official documentation.
5. Keep the root `SKILL.md` focused. Move detailed material into a relevant file under `references/`.
6. Include a practical example or verification step when it improves the change.

## Content standards

- Use clear international English and explain acronyms on first use.
- Prefer actionable instructions over vague aesthetic language.
- Do not reproduce large sections of third-party documentation. Summarize in original wording and link to the source.
- Do not state that Material 3 Expressive APIs are available on every platform.
- Label platform-specific behavior and experimental APIs clearly.
- Avoid prescribing arbitrary token values when official guidance or platform constraints should determine them.
- Treat accessibility, localization, privacy, performance, and maintainability as core product requirements.
- Never present a design preference as a Google requirement unless the source explicitly says so.

## Local checks

Requirements: Python 3.10 or newer. No third-party Python packages are required.

```bash
python scripts/validate_skill.py
python -m unittest discover -s tests -v
```

Both commands must pass before a pull request is ready.

## Pull request checklist

- [ ] The change solves a clear problem and is scoped appropriately.
- [ ] Official sources are linked for material factual claims.
- [ ] Platform and version assumptions are explicit.
- [ ] Internal links and referenced files are valid.
- [ ] The validator and tests pass.
- [ ] Documentation and changelog are updated when appropriate.
- [ ] No generated files, secrets, personal data, or unrelated changes are included.

## Reporting an issue

Include the affected file, target platform, expected behavior, observed problem, and an official source or minimal reproduction when available.
