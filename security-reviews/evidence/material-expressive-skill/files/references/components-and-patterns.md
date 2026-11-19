# Components and interaction patterns

Choose components from the user's task and platform capability. A component is correct because its behavior and semantics fit the interaction, not because it looks expressive in a showcase.

## Selection sequence

1. Identify the user action: navigate, select, enter data, reveal detail, confirm, filter, or act on a single object.
2. Identify the expected behavior and state model.
3. Check whether the target platform offers a Material component for that role.
4. Choose the least surprising supported variant.
5. Verify component availability, maturity, and API signature against the current official documentation.
6. Document any custom component and how it preserves Material semantics.

## Common component families

The exact names, variants, and supported options vary by library. Use this as a semantic map, not as a promise of API availability on every platform.

| User need | Candidate family | Design checks |
| --- | --- | --- |
| Commit to the primary action | Filled button or platform's emphasized action | One clear primary action per context; label describes the outcome |
| Secondary action | Tonal, outlined, or text button | Lower emphasis than the primary action |
| One main action available while browsing | Floating action button | Action is genuinely primary and contextual; do not use as decoration |
| Choose one or more options | Chips, segmented controls, menus, selection controls | Selected state is unmistakable and keyboard/screen-reader accessible |
| Navigate top-level destinations | Navigation bar, rail, drawer, or platform-specific navigation | Choose from available width and destination count |
| Search within content | Search field or search bar | Search, clear, submit, and empty-result states are defined |
| Display repeated records | List, list item, table, or collection | Prioritize scan speed and content density |
| Reveal supporting content | Card, expandable region, sheet, dialog, tooltip | Match interruption level and dismiss behavior to importance |
| Enter structured data | Text fields, selection controls, pickers | Labels, validation, help, keyboard, and error behavior are explicit |
| Show system feedback | Snackbar, inline message, progress, or dialog | Feedback is timely, understandable, and recoverable |

## Actions and hierarchy

- Make the primary action visually distinct without giving every control equal emphasis.
- Use concise, specific labels. Prefer an outcome ("Save changes") over a vague command ("OK") when appropriate.
- Place secondary actions nearby but visually subordinate.
- Separate destructive actions and explain irreversible consequences.
- Do not use an icon-only control when a text label or accessible name is needed.
- Never use color alone to signal the meaning of a control or its state.

## Lists and collections

- Optimize rows for scan speed and predictable alignment.
- Use leading visuals only when they identify the entity or help recognition.
- Keep row actions discoverable without creating accidental activation.
- Use dividers, tonal grouping, or containers only when they clarify relationships.
- Define empty, loading, error, and no-results behavior.
- For large collections, consider search, sorting, filtering, pagination, or virtualization appropriate to the platform.

## Forms

- Use a persistent label; do not rely on placeholder-only labels.
- Group related fields and establish a logical keyboard order.
- State requirements before submission when possible.
- Validate at a useful time and explain how to recover.
- Preserve entered values after a recoverable error.
- Distinguish inline field errors from global submission failures.
- Support autofill, password managers, IME actions, and platform keyboard behavior.

## Cards and containers

Use a card when the content forms a meaningful entity or interaction group. Avoid cardifying every section or row. Prefer typography, spacing, and surfaces to unnecessary outlines and shadows.

## Navigation

- Separate destinations from actions.
- Keep navigation labels recognizable and consistent.
- Choose a bottom bar, rail, or drawer according to available window space and product information architecture.
- Preserve state when moving between destinations when expected by the product.
- Ensure navigation works with keyboard, accessibility services, and deep links where relevant.

## Component states

Define the required states before implementation:

- Enabled and disabled.
- Hovered, focused, pressed, and dragged where the input method supports them.
- Selected and unselected.
- Loading, progress, and completion.
- Error and recovery.
- Empty and no-results.
- Expanded, collapsed, open, and dismissed.
- Read-only and permission-limited where appropriate.

Do not invent a component state if the underlying interaction does not have that state.

## Custom components

A custom component may be appropriate when no native or official component meets the product need. It should:

- Have a documented semantic role and interaction contract.
- Use theme tokens and state layers consistently.
- Expose accessible names, roles, values, and actions.
- Support focus, keyboard, screen reader, and pointer/touch input as relevant.
- Define disabled and error behavior.
- Be tested across themes, text scales, and window sizes.
- Avoid visually imitating a Material component while breaking its expected behavior.
