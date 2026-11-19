# Accessibility and internationalization

Accessibility and localization are core design constraints. An expressive interface that cannot be read, navigated, translated, or operated reliably is not production-ready.

## Semantics and assistive technology

- Use native controls and semantic roles where possible.
- Give controls meaningful accessible names; icon-only controls need a descriptive label.
- Expose value, state, selection, expanded/collapsed state, and available actions.
- Keep reading and focus order aligned with the visual task order.
- Group related information without hiding important relationships from assistive technology.
- Announce important status changes when appropriate, but avoid repeatedly announcing decorative updates.
- Do not communicate meaning through color, shape, animation, or position alone.

## Contrast and color

- Check actual foreground/background combinations after theme, dynamic color, opacity, and state overlays resolve.
- As a web baseline, WCAG 2.2 AA requires at least 4.5:1 contrast for normal text and 3:1 for large text; relevant non-text UI components and graphical objects have their own 3:1 requirement.
- Do not assume a color role is automatically accessible in every pairing or on every custom surface.
- Check disabled, selected, error, warning, success, focus, and inverse states.
- Use text, icons, patterns, or labels alongside color for status.

For native platforms, verify applicable platform guidance and legal/product requirements in addition to web WCAG criteria.

## Touch, pointer, and keyboard

- On Android touch interfaces, Google's guidance recommends at least 48 dp by 48 dp interactive touch targets.
- For web content, WCAG 2.2 AA Success Criterion 2.5.8 specifies a 24 by 24 CSS pixel minimum pointer target, subject to documented exceptions and spacing rules. This is not the same measurement as Android dp.
- Prefer larger, well-spaced targets for frequent or high-risk actions.
- Support keyboard access for every interactive web control.
- Provide visible focus and a logical focus order.
- Avoid traps, unexpected focus jumps, and controls that only work on hover.
- Do not require dragging when a simpler single-pointer alternative can provide the same function.

## Text and visual presentation

- Support operating-system text scaling and browser zoom.
- Avoid fixed-height text containers that clip content.
- Use line length, line height, and paragraph spacing suited to reading.
- Do not encode information exclusively in a typeface, weight, or decorative style.
- Test with bold text and larger text settings where supported.
- Ensure focus indicators and text remain visible over expressive surfaces.

## Motion and sensory preferences

- Respect reduced-motion settings.
- Avoid flashing and rapid repeated movement.
- Do not use animation as the only way to reveal content or communicate a result.
- Provide a stable visual alternative to animated emphasis.
- Avoid relying exclusively on sound, haptics, or visual effects for critical feedback.

## Internationalization

Design for international content from the beginning:

- Use locale-aware formatting for dates, times, numbers, percentages, currencies, measurements, and names.
- Externalize all user-facing strings. Never concatenate fragments that require language-specific word order.
- Allow translations to expand and use font fallback for each supported writing system.
- Test Arabic and other right-to-left scripts using actual localized strings.
- Use logical start/end alignment and padding instead of hard-coded left/right assumptions.
- Mirror directional icons only when their meaning is directional; do not blindly mirror logos, media controls, or universal symbols.
- Verify mixed-direction text, phone numbers, URLs, identifiers, and embedded Latin terms.
- Ensure navigation, progress, charts, and gestures remain understandable in right-to-left layouts.
- Do not use flags as substitutes for language names.
- Provide a complete translation workflow and identify untranslated fallback behavior.

## Data visualizations and non-text content

- Pair charts and status graphics with labels, summaries, or accessible data.
- Provide text alternatives for meaningful images and diagrams.
- Do not make interaction discoverable only through color or motion.
- Ensure zoom, scrolling, and alternate representations work for complex visual content.

## Test checklist

- [ ] Screen reader can identify controls, roles, labels, values, and state.
- [ ] Reading order and focus order make sense.
- [ ] Contrast is tested for all meaningful themes and states.
- [ ] Keyboard-only and pointer-only use are supported where relevant.
- [ ] Touch targets are appropriate for the platform.
- [ ] Large text and zoom do not clip or overlap.
- [ ] Reduced motion preserves comprehension and task completion.
- [ ] RTL and long translated strings are tested.
- [ ] Dates, numbers, currencies, and units are locale-aware.
