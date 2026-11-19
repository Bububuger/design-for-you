# Adaptive layouts

Design for the app window and available space, not for a device label or a single screenshot. A phone can run in a resized window; a tablet can be held vertically; a foldable changes size while the app is open.

## Adaptive decision sequence

1. Measure the current app/window bounds using the target platform's supported APIs.
2. Identify the content that must remain visible and the minimum useful width for each region.
3. Decide which elements reflow, resize, move, collapse, or become secondary.
4. Choose navigation appropriate to the available width and information architecture.
5. Preserve state and user context as the window changes.
6. Test compact, medium, expanded, and unusually narrow/wide sizes where relevant.

Do not use device model detection as a substitute for responsive layout decisions.

## Patterns

### Single-pane

Use one focused content region when the task is sequential, the content is narrow, or a second pane would compete for attention.

### List-detail

Use a list and detail region together when users benefit from keeping navigation context visible while inspecting or editing an item. On a narrow window, navigate into the detail view and provide a clear return path. Preserve selection when moving between layouts.

### Supporting pane

Use a secondary pane for contextual information, filters, details, or a related task when it remains helpful and does not crowd the primary workflow.

### Adaptive navigation

- Compact width often favors bottom navigation or a drawer, depending on destination count and app architecture.
- More available width may support a navigation rail or persistent drawer.
- Expanded layouts can support persistent navigation and multiple content regions.
- Use the target platform's official adaptive navigation components where available.

These are common patterns, not universal breakpoint rules. The actual switch should follow the platform's window classes and the content's minimum size.

## Android window size classes

Android's documented width classes commonly use these ranges:

| Class | Window width |
| --- | --- |
| Compact | less than 600 dp |
| Medium | 600 dp to less than 840 dp |
| Expanded | 840 dp to less than 1200 dp |
| Large | 1200 dp to less than 1600 dp |
| Extra-large | 1600 dp and above |

Treat these as Android guidance, not universal CSS breakpoints. Use the current platform library's window-size APIs and check whether the app is in multi-window mode. A platform may expose fewer classes or use a different model.

## Foldables and changing windows

- Recalculate layout when the window changes size or posture.
- Avoid assuming the full physical display area belongs to the app.
- Respect hinges, folds, safe areas, system bars, and cutouts when the platform exposes them.
- Decide whether spanning a fold is appropriate for the content.
- Keep focus, scroll position, selected item, and in-progress input stable during transitions.

## Desktop and large screens

- Do not stretch a narrow mobile column across the entire display.
- Use maximum content widths and useful multi-column layouts.
- Support keyboard navigation, hover, focus, pointer targets, and shortcuts where appropriate.
- Use persistent navigation and side panels only when they improve task flow.
- Ensure dialogs, menus, tooltips, and popovers remain anchored and visible within the window.

## Responsive content

- Let text wrap and containers grow.
- Avoid fixed heights around text or localized content.
- Prioritize or collapse secondary information rather than clipping it.
- Use lists, tables, grids, or multi-pane layouts according to the content model.
- Check large text, translated labels, and empty/error states at every important size.

## Adaptive verification matrix

| Scenario | Verify |
| --- | --- |
| Narrow/compact | No clipped controls, horizontal overflow, or inaccessible actions |
| Medium | Content has comfortable width and navigation remains clear |
| Expanded | Extra space improves structure instead of creating stretched content |
| Resized window | Layout changes smoothly without losing user state |
| Fold/unfold | Selection, focus, and input survive posture and size changes |
| Landscape | Essential actions remain reachable |
| Large text | Content reflows and controls do not overlap |
| Keyboard/pointer | Focus order, hover, shortcuts, and pointer interactions work |
