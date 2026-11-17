# Expressive design principles

Material 3 Expressive expands Material 3 with additional ways to shape emphasis, feedback, and personality. Treat it as a usability-oriented design approach, not a decorative theme or permission to make every element visually loud.

## The governing test

For every expressive choice, answer:

1. What user task or decision does this help?
2. Which piece of information or action should become easier to notice or understand?
3. Why is this particular expressive treatment better than a calmer M3 treatment?
4. Does it preserve familiar semantics, accessibility, and product identity?
5. Does the screen still work when animation, color, or visual emphasis is reduced?

If the choice has no clear answer, remove it.

## Expressive levers

Use these as a practical set of design levers. They are not a mandatory checklist and should not be interpreted as a claim that every platform implements all of them.

### Size and component flexibility

Use meaningful size contrast to make a primary action, key metric, current state, or next step easier to scan. Flexible component arrangements can create stronger hierarchy than making every component the same size.

- Reserve the strongest size emphasis for the most important content.
- Keep repeated items consistent unless their priority genuinely differs.
- Do not make a button large merely to make the screen feel expressive.
- Check how size changes behave in compact windows, large text, and localization.

### Shape

Use shape as a signal for role, grouping, state, or personality.

- Keep a coherent corner and shape language across related components.
- Use stronger shape contrast for meaningful distinction, not random variety.
- Preserve the familiar silhouette of controls so their function stays obvious.
- Consider shape transitions only when they clarify a state or continuity.

### Color

Use semantic color roles to communicate hierarchy, interaction, and status.

- Start from the theme's semantic roles rather than hard-coded colors.
- Use primary, secondary, and tertiary roles intentionally; do not make every container a different accent.
- Preserve readable foreground/background pairings in light and dark themes.
- Never use color as the only signal for status, selection, validation, or severity.
- Dynamic color is a personalization option where supported, not a reason to make brand identity or contrast unpredictable.

### Typography

Use typographic contrast to make content structure easier to scan.

- Make headings, labels, values, and supporting text visibly distinct.
- Reserve emphasized display or headline treatments for moments that deserve attention.
- Keep body copy comfortable for sustained reading.
- Avoid shrinking text to preserve a composition; adapt the layout instead.
- Test text scaling and translated strings before approval.

### Containment

Use containers, grouping, and separation to communicate relationships.

- Group controls that belong to one task or data entity.
- Use a container when it communicates structure, not just to decorate a surface.
- Avoid wrapping every list row, field, and section in its own card.
- Separate primary actions from secondary actions and destructive actions.
- Preserve enough whitespace to make groups legible.

### Motion

Use motion to explain cause and effect, continuity, progress, and state change.

- Animate only when the transition conveys useful information or feedback.
- Prefer motion that is brief, coherent, and consistent with the interaction.
- Keep task completion, error, and confirmation understandable without animation.
- Respect system reduced-motion settings and provide a calmer alternative.

## Where expression tends to help

Potentially useful moments include a clear primary action, a key status or progress change, a meaningful selection, a successful completion, or a high-level navigation transition.

These are prompts for evaluation, not recipes. Test against actual content and task priority.

## Where restraint usually wins

Use a calmer M3 treatment for dense tables, settings, long-form reading, repetitive forms, admin workflows, and frequently repeated controls unless stronger emphasis measurably helps users scan or act.

## Common failure modes

| Failure | Why it hurts | Better direction |
| --- | --- | --- |
| Every component is oversized | Hierarchy disappears and density suffers | Emphasize only the most important action or content |
| Random corner radii | Shapes stop communicating a coherent system | Define a deliberate shape scale and use it consistently |
| Accent color everywhere | Color loses its semantic role | Use a restrained semantic palette |
| Motion on every interaction | Adds noise, delay, and cognitive load | Animate meaningful transitions only |
| Nested cards everywhere | Adds visual borders without information | Use spacing, typography, and subtle surfaces first |
| Oversized display text for routine content | Reduces information density and scanning | Reserve expressive typography for key moments |
| Decorative gradients or blur without purpose | Weakens hierarchy and can reduce legibility | Use theme roles and intentional surface treatment |
| Copying a showcase screenshot literally | Ignores context, content, and platform behavior | Rebuild the interaction around the real task |

## Practical decision record

For a screen, document no more than a few major expressive decisions:

- **Priority:** what the user should notice first.
- **Treatment:** the chosen lever or component.
- **Reason:** the task or comprehension benefit.
- **Fallback:** behavior with reduced motion, constrained space, or limited platform support.
- **Verification:** how the team will check that the treatment helps.
