# Motion and feedback

Motion should explain state, causality, continuity, or spatial relationships. It is not a decoration layer to add after the interface is finished.

## Motion decisions

For each animation, identify:

- **Trigger:** what user action or system event starts it?
- **Meaning:** what information does the movement communicate?
- **Elements:** which elements move, transform, or change?
- **Direction:** why does this direction communicate the relationship?
- **Timing:** does the transition feel responsive and avoid blocking the task?
- **Interruption:** can the user reverse, dismiss, or continue without waiting?
- **Fallback:** what happens when reduced motion is enabled?

If movement conveys no useful information, prefer an immediate state change.

## Motion principles

- Prefer continuity when an object changes position, size, or container.
- Use shared or related motion only when the relationship between old and new states is meaningful.
- Make entrance and exit behavior consistent for related surfaces.
- Avoid animating large areas for small actions unless the transition helps explain the change.
- Avoid long animations that delay interaction or hide updated content.
- Keep repeated interactions predictable.
- Do not use motion alone to communicate success, error, or status.

## Spring-based motion and APIs

M3 Expressive introduces richer motion capabilities in supported implementations, including physics-informed motion systems. Use the platform's official motion scheme and component defaults when available.

Do not copy damping, stiffness, duration, or easing values from an unrelated framework and label them as official Material tokens. Verify the current API and token guidance for the target release. If the platform does not expose a Material motion scheme, document the adaptation and keep transitions consistent.

## Feedback hierarchy

Choose the least interruptive feedback that makes the outcome clear:

1. **Inline state:** validation, connection state, and contextual information.
2. **Component state:** selected, pressed, expanded, or disabled state.
3. **Transient message:** brief confirmation or a recoverable notice.
4. **Modal interruption:** permission, high-risk decision, or a task that truly requires attention.

Do not use a dialog for routine success. Do not rely on a transient message for information the user must retain.

## Loading and progress

- Use a determinate indicator when meaningful progress can be measured.
- Use indeterminate progress only when completion time or percentage is genuinely unknown.
- Keep the relevant context visible during a wait.
- Prefer stable skeletons when the final content geometry is known and loading is long enough to justify them.
- Do not display a spinner for a near-instant operation.
- Expose progress and status accessibly.
- Provide cancel, retry, or recovery where the operation supports it.

## Reduced motion

Respect the platform's reduced-motion or animation settings. When motion is reduced:

- Remove decorative movement and parallax.
- Replace spatial transitions with a subtle fade or immediate change where appropriate.
- Preserve status and causality through text, icon, or static state.
- Avoid flashing, rapid pulsing, or repeated attention-grabbing movement.
- Verify that no task depends on animation to reveal information.

## Motion review

- [ ] Every animation has a stated purpose.
- [ ] Motion does not block input or delay completion.
- [ ] Related transitions use consistent logic.
- [ ] Status remains understandable without motion.
- [ ] Reduced-motion behavior is implemented and tested.
- [ ] Frame rate and rendering performance are checked on target devices.
