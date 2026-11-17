# Design foundations and semantic tokens

Use this reference when defining or reviewing a Material theme. Exact token names and values can differ by platform and library release; verify them against the current official system and the project's actual dependency.

## Build a token system, not a bag of colors

Organize visual decisions around semantic roles:

- **Color:** primary, on-primary, primary-container, on-primary-container, secondary, tertiary, error, surface, surface-container, on-surface, outline, inverse roles, and other roles provided by the target library.
- **Typography:** display, headline, title, body, and label roles, with appropriate size, weight, line height, and letter spacing.
- **Shape:** a small, coherent scale of corner and component shapes; use named theme tokens where available.
- **Elevation:** tonal and shadow-based elevation where supported, used to communicate hierarchy and layering.
- **Spacing and layout:** consistent spacing decisions that respond to content and available width.
- **Iconography:** consistent family, optical size, fill/weight, and alignment.

Do not invent token names and assume that they are part of a platform's API. When a target does not expose a role directly, map it deliberately in the app's own design tokens.

## Color and color schemes

1. Choose source colors that fit the product brand and its content.
2. Generate or define complete semantic schemes, not only a primary color.
3. Review foreground/background pairings for text, icons, controls, disabled states, and focus.
4. Design both light and dark appearances.
5. Consider dynamic color when the operating system and framework support it and the product permits it.
6. Provide a predictable fallback where dynamic color is unavailable or disabled.
7. Test selected, error, success, warning, and disabled states in both themes.

Do not treat raw seed colors as accessible UI colors. Semantic roles and actual rendered pairings determine usability.

## Typography

- Use a type scale with clear roles rather than arbitrary one-off sizes.
- Use display or expressive headline styles sparingly for high-priority content.
- Use body styles for sustained reading and labels for concise control text.
- Maintain readable line length and line height.
- Allow text to grow; do not clip essential content at larger accessibility text sizes.
- Test scripts with different metrics, including Arabic, CJK, Indic, and Latin where relevant.
- Use the product's approved typeface and ensure font fallback is intentional.

Typography conveys hierarchy, but it must not carry meaning that the content or semantics fail to communicate.

## Shape

- Define a recognizable and reusable shape vocabulary.
- Apply shape tokens by component role.
- Keep repeated controls and list items visually consistent.
- Introduce contrasting shapes only when they help distinguish meaningful groups or states.
- Check content clipping, text wrapping, and touch feedback after changing corner geometry.

Shape variety is not a substitute for information architecture.

## Elevation and surfaces

- Prefer surface hierarchy, spacing, and clear typography before adding shadows.
- Use elevation to communicate a real layer or interaction relationship.
- Avoid applying a shadow to every card or using outline plus shadow plus tint without a reason.
- Keep surface contrast sufficient in both themes.
- Verify overlays, dialogs, menus, and sheets against platform conventions.

## Spacing and density

- Establish spacing tokens that work as a coherent rhythm.
- Use whitespace to clarify groups and action relationships.
- Choose density based on the task, content amount, and input mode.
- Do not blindly apply an 8 dp grid or a fixed spacing value where the platform component system defines different geometry.
- Prefer adaptive constraints and content-aware sizing over fixed screen assumptions.

## Dynamic color and brand

Dynamic color can personalize an app on supported platforms, but brand and product requirements may constrain it. Define an intentional fallback. Check that critical state, brand recognition, and readability remain stable under multiple generated palettes. Do not make a dynamic palette the only accessible configuration.

## Theme verification checklist

- [ ] Complete semantic roles are defined or deliberately mapped.
- [ ] Light and dark themes are both reviewed.
- [ ] Dynamic color behavior and fallback are understood.
- [ ] Foreground/background contrast is checked after runtime colors resolve.
- [ ] Typography supports large text and long translations.
- [ ] Shapes are consistent and purposeful.
- [ ] Elevation is meaningful rather than decorative.
- [ ] Components use theme roles instead of local hard-coded values.
