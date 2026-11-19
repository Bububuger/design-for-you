# Production implementation workflow

Use this workflow for end-to-end design and engineering tasks. Scale it to the scope; do not turn a small, well-defined change into a redesign.

## 1. Repository reconnaissance

Before editing:

- Read project instructions, README, architecture, dependency manifests, and relevant screens.
- Identify framework and target platforms.
- Find the existing theme, typography, color roles, spacing, reusable components, navigation, and state model.
- Inspect tests, lint rules, formatting, and build commands.
- Check for ongoing work and preserve unrelated changes.

Do not replace the design system or upgrade dependencies without a clear requirement.

## 2. Translate the request into a product brief

Define the user, task, primary action, content hierarchy, screen states, constraints, and acceptance criteria. Use `templates/design-brief.md` for a substantial change.

If assumptions are necessary, state only those that materially affect the implementation.

## 3. Plan before styling

Create a short plan containing:

- Screens or components affected.
- Information architecture and navigation decisions.
- Semantic theme roles and relevant components.
- Adaptive and accessibility requirements.
- Data/state transitions and failure handling.
- Tests and verification steps.

Do not start with decorative tokens or gradients.

## 4. Build or reuse foundations

- Reuse existing theme architecture when sound.
- Add or refine semantic color roles and complete light/dark schemes.
- Establish type, shape, and elevation roles.
- Make repeated spacing and component choices reusable.
- Keep token names and values documented.
- Avoid one-off literals that bypass the theme without a reason.

## 5. Implement structure and interaction

Build in logical order:

1. Navigation and screen structure.
2. Primary content and hierarchy.
3. Main actions and forms.
4. Secondary controls and supporting content.
5. Loading, empty, error, success, and permission states.
6. Motion and expressive treatment.
7. Responsive/adaptive behavior.

Use native Material components where appropriate and supported.

## 6. Add expressive treatment

For each expressive change, write down the user benefit. Prefer a small number of strong decisions instead of uniform exaggeration. Verify that expression does not reduce readability, density, action discoverability, or brand consistency.

## 7. Verify quality

Run the project's available checks:

- Formatter and linter.
- Unit and component tests.
- Relevant build or type checks.
- UI tests for important flows.
- Accessibility checks and manual screen-reader/keyboard review where possible.
- Visual review in light and dark themes.
- Compact and expanded window tests.
- Large text, RTL, and long-string tests where relevant.
- Reduced-motion behavior.

Use screenshots or recordings only as evidence for the exact state and viewport tested. Do not claim a test passed if it was not run.

## 8. Review the diff

Check for accidental dependency changes, duplicate components, hard-coded colors, clipping, missing states, broken semantics, incorrect API usage, unused code, and unrelated edits.

Read [review-checklist.md](review-checklist.md) before final approval.

## 9. Handoff

Summarize:

- What changed and why.
- Main design decisions and expressive treatments.
- Platform/API assumptions and known limitations.
- Tests and commands actually run, including results.
- Remaining risks or follow-up work.

Use [the handoff template](../templates/implementation-handoff.md).
