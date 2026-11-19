# Material 3 Expressive review checklist

Use this checklist to evaluate a screen, flow, component library, or implementation. Mark an item as not applicable only when the reason is clear.

## Product and hierarchy

- [ ] The primary user task and next action are obvious.
- [ ] Content is grouped by meaning and task, not by arbitrary card boundaries.
- [ ] Navigation, actions, selection, and destructive behavior are distinct.
- [ ] Important content is scannable without hiding necessary detail.
- [ ] Empty, loading, error, success, and permission states are considered.

## Material foundations

- [ ] Components use semantic theme roles.
- [ ] Light and dark themes are coherent.
- [ ] Dynamic color and brand fallback are intentional where supported.
- [ ] Typography has a clear hierarchy and supports larger text.
- [ ] Shape usage is coherent and communicates role or grouping.
- [ ] Elevation and outlines have a clear purpose.
- [ ] Spacing and density fit the content and input mode.

## Expressive quality

- [ ] Each expressive treatment improves hierarchy, recognition, feedback, or emotional clarity.
- [ ] Size contrast is intentional and not applied uniformly.
- [ ] Color remains semantic and readable.
- [ ] Typography emphasizes only content that deserves attention.
- [ ] Containment clarifies relationships rather than adding visual noise.
- [ ] Motion explains cause, state, or spatial continuity.
- [ ] Familiar component meaning and interaction behavior remain recognizable.
- [ ] The interface remains understandable without decorative motion.

## Components and states

- [ ] Each component matches the user's task and platform.
- [ ] API and release-channel availability are verified.
- [ ] Primary and secondary action hierarchy is clear.
- [ ] Interactive states are defined and distinguishable.
- [ ] Forms have persistent labels and recoverable validation.
- [ ] Destructive actions have clear confirmation or undo behavior as appropriate.
- [ ] Loading and progress behavior is proportional to the wait.

## Adaptive behavior

- [ ] Layout is based on the current window size.
- [ ] Compact, medium, and expanded layouts are considered.
- [ ] Resizing and fold/unfold transitions preserve state.
- [ ] Large layouts use space productively without stretching narrow content.
- [ ] Keyboard, pointer, touch, and wearable input needs are addressed as applicable.

## Accessibility and localization

- [ ] Roles, names, values, states, and reading order are exposed.
- [ ] Contrast is checked on real foreground/background combinations.
- [ ] Touch/pointer targets and spacing meet the target platform's guidance.
- [ ] Keyboard and focus behavior are complete where relevant.
- [ ] Large text, zoom, and font fallback are tested.
- [ ] Reduced-motion preferences are respected.
- [ ] RTL, translated strings, locale-aware formatting, and mixed-direction text are tested.
- [ ] Meaning is not conveyed by color, motion, or shape alone.

## Engineering quality

- [ ] Existing architecture and project conventions are preserved.
- [ ] Dependencies are minimal and justified.
- [ ] No unsupported or invented API is introduced.
- [ ] Tests, lint, formatting, and build checks are run where available.
- [ ] The final diff contains no unrelated changes.
- [ ] Handoff includes platform limitations and actual verification results.

## Review outcome

Choose one:

- **Ready:** all critical product, behavior, platform, and accessibility requirements pass.
- **Ready with follow-up:** no release blocker remains; documented improvements can be tracked.
- **Needs changes:** one or more critical tasks, accessibility needs, interaction states, or platform requirements fail.

List concrete evidence and file/screen references for every issue. Avoid subjective comments such as "make it more Material" without identifying a specific semantic or usability problem.
