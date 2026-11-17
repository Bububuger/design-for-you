# Example: an expressive task-list screen

This is a decision walkthrough, not a fixed UI recipe. It shows how to add expression to a familiar task-list workflow without turning every row into a showcase component.

## Product task

A user opens a daily planner to understand what needs attention and add a new task.

**Primary action:** review the next important task and complete it.

**Secondary actions:** browse upcoming tasks, filter the list, and create a task.

## Information hierarchy

1. Current day and concise overview.
2. One high-priority task that needs attention.
3. The remaining task list, ordered by time or priority.
4. Navigation to other planner destinations.
5. A create-task action.

## Expressive decisions

| Area | Treatment | Why it helps | Restraint |
| --- | --- | --- | --- |
| Daily overview | A clear headline with a compact completion summary | Makes the current context easy to scan | Do not turn every count into oversized display text |
| Priority task | Stronger containment and a distinct shape treatment | Separates the next action from routine rows | Keep the action and task label familiar |
| Completion | Immediate selected/completed state with brief meaningful feedback | Confirms the user's action | No celebratory animation for every repeated task |
| Task list | Calm, consistent list items | Supports rapid scanning | Avoid nesting each row in a large card |
| Create task | A prominent add action | Makes the main creation path discoverable | Use a floating action pattern only if it fits the app's navigation and screen context |

## Responsive behavior

- **Compact:** show the overview, priority task, and list in one vertical flow; use a navigation pattern suitable for the app's destination count.
- **Medium:** consider a navigation rail and more visible task context.
- **Expanded:** consider a list-detail layout if opening a task requires meaningful detail; do not simply stretch the compact column.
- **Resized window:** preserve the selected task, scroll position, and any in-progress task draft.

## States to design

- First use with no tasks.
- Tasks loading.
- No results after filtering.
- Task completion and undo where supported.
- Save failure while creating or editing a task.
- Permission or sync failure.
- Offline state, if synchronization is part of the product.

## Accessibility and localization

- Provide a meaningful accessible name for completion controls.
- Do not indicate priority or completion by color alone.
- Support keyboard focus and activation on desktop/web.
- Allow task titles to wrap and respect large text.
- Test long translated strings and right-to-left task content.
- Keep time and date formatting locale-aware.
- Ensure reduced motion does not hide completion feedback.

## Verification questions

1. Can a returning user identify the next important task immediately?
2. Is the priority treatment meaningfully different from routine tasks?
3. Can users complete and undo a task without relying on motion or color?
4. Does the layout remain usable at compact and expanded widths?
5. Does the screen remain clear with large text and RTL content?

If the answer to any critical question is no, refine hierarchy or behavior before adding more expression.
