# Official sources and version verification

Use official documentation as the source of truth for Material behavior, API availability, accessibility requirements, and platform implementation details. This file is a starting index, not a replacement for checking the latest release notes.

**Reference review date:** 2026-11-16.

## Material Design

- [Material Design 3](https://m3.material.io/) — design system guidance and foundations.
- [Material 3 Expressive](https://m3.material.io/) — official Material entry point; follow the expressive links from the current site for the latest design guidance.
- [Build next-level UX with Material 3 Expressive](https://io.google/2025/explore/technical-session-24/) — Google I/O 2025 session introducing the design approach and related resources.

## Android and Jetpack Compose

- [Material Design 3 in Compose](https://developer.android.com/develop/ui/compose/designsystems/material3) — current Compose integration, theming, components, and Material 3 Expressive overview.
- [Compose Material 3 release notes](https://developer.android.com/jetpack/androidx/releases/compose-material3) — version and release-channel verification. Check this before using new APIs or dependencies.
- [Compose Material 3 API reference](https://developer.android.com/reference/kotlin/androidx/compose/material3/package-summary) — exact symbols, signatures, and annotations.
- [Adaptive apps: get started](https://developer.android.com/develop/adaptive-apps/guides/get-started-with-adaptive-apps) — app-window adaptation and window size classes.
- [Android accessibility](https://developer.android.com/guide/topics/ui/accessibility/apps) — platform accessibility guidance, including touch targets.

## Research context

- [Usability Hasn't Peaked: Exploring How Expressive Design Overcomes the Usability Plateau](https://research.google/pubs/usability-hasnt-peaked-exploring-how-expressive-design-overcomes-the-usability-plateau/) — Google Research publication on measured usability outcomes for expressive designs. Treat research results as study findings, not a guaranteed improvement for every product or population.

## Accessibility standards

- [Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/) — normative web accessibility standard.
- [Understanding Target Size (Minimum)](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum) — explanation of WCAG 2.2 success criterion 2.5.8.

## Agent Skill format

- [Agent Skills specification](https://agentskills.io/specification) — portable skill directory structure and `SKILL.md` metadata format.
- [Agent Skills project](https://github.com/agentskills/agentskills) — open specification and ecosystem.

## Version and API verification rules

When a task depends on a version-sensitive claim:

1. Inspect the version already used by the project.
2. Open the official library release notes and API reference.
3. Check whether the API is stable, experimental, deprecated, or unavailable for the target.
4. Verify platform and minimum OS constraints.
5. Check official migration notes before recommending an upgrade.
6. State the version actually verified and distinguish it from the current latest version if those differ.

Never copy a dependency version from this repository as if it were guaranteed to remain current. Never claim cross-platform support based only on an Android API.

## Source attribution

This project is an independent Agent Skill. It summarizes guidance in original wording and links to official sources. Material Design, Android, Jetpack Compose, and Google are names and marks of their respective owners. This repository is not affiliated with or endorsed by Google.
