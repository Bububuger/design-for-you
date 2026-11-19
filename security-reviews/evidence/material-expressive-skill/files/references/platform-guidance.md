# Platform implementation guidance

Material 3 Expressive is a design-system expansion, not a universal implementation API. Use native components where the target platform exposes them. Elsewhere, adapt the semantic design principles and make the limitations explicit.

## Android — Jetpack Compose

This is the primary native path covered by the current Android Material 3 implementation.

- Use the current `androidx.compose.material3` library and its official documentation.
- Use Material theme subsystems for color, typography, and shapes rather than scattered local constants.
- Prefer official Material components and defaults when they fit the interaction.
- Check the exact API signature, opt-in annotation, dependency version, and release channel before using new or experimental APIs.
- Review edge-to-edge content, system bars, window insets, navigation, and predictive back behavior as relevant.
- Use adaptive APIs and window size classes for resize and large-screen behavior.
- Do not assume a version seen in an example is still current.

The official Android guide describes Compose Material 3 as including M3 Expressive updates. Confirm the release notes before selecting components or motion APIs.

## Wear OS

- Use the dedicated Wear Compose Material 3 library and wearable-specific guidance.
- Design for round screens, glanceability, short sessions, constrained input, and power use.
- Do not port a phone layout or assume the standard Android Compose Material 3 artifact is the correct Wear dependency.
- Check current Wear APIs and system conventions before implementing.

## Android Views

- Use the supported Material Components for Android and established View system patterns.
- Reuse Material theme roles and interaction principles where available.
- Do not call Compose-only APIs from a Views project or assume feature parity between libraries.
- Treat a Compose migration as a separate architecture project, not a routine styling step.

## Flutter

- Inspect the Flutter SDK version, current Material widgets, theme configuration, and any existing component package.
- Prefer the SDK's native Material 3 `ThemeData`, `ColorScheme`, text theme, shapes, and components when supported.
- Verify whether a desired M3 Expressive behavior exists in that SDK version before promising it.
- If you create a custom widget, use semantic tokens, accessibility semantics, focus behavior, and platform input conventions.
- Avoid copying Compose API names, motion physics, or component parameters into Dart.
- Test platform differences, large text, right-to-left layout, and desktop/web targets independently.

## Web

- Use semantic HTML, accessible controls, and responsive CSS as the implementation foundation.
- Represent M3 roles as design tokens or CSS custom properties with a clearly documented mapping.
- Check actual browser support for color, typography, motion, and layout features.
- Respect `prefers-reduced-motion`, zoom, keyboard focus, high-contrast settings where supported, and right-to-left document direction.
- Do not claim that Android Compose M3 Expressive components or their motion APIs are native web APIs.
- Treat third-party Material Web libraries as separate dependencies: check their current maintenance status, release health, accessibility, and API support before adopting them.

## React Native

- Inspect the project's UI library and supported versions before selecting components.
- Map the design system to the library's semantic theme and component variants.
- Use native accessibility roles, labels, focus behavior, and platform conventions.
- Do not assume a web React component or Android Compose component can be reused directly.
- Verify Android and iOS behavior separately.

## SwiftUI and other native platforms

- Use platform-native controls and interaction conventions where they provide a better experience.
- Recreate M3 semantic roles only where appropriate for the product and platform.
- Keep color, type, shape, and motion mappings explicit and maintainable.
- Avoid forcing Android-specific metaphors, navigation, or touch assumptions onto another platform.

## Platform comparison policy

When asked to build across platforms, provide a support matrix:

| Feature | Native support | Adaptation | User-visible difference |
| --- | --- | --- | --- |
| Component or pattern | Exact API and version verified | Custom or alternate native pattern | Describe behavior and visual difference |
| Motion | Platform motion API verified | Easing or static state | State reduced-motion behavior |
| Dynamic color | OS/library capability verified | Brand-derived fallback | Explain personalization limits |
| Adaptive layout | Native size APIs verified | Responsive constraints | List tested window classes |

Never write "fully supported" unless the exact component, behavior, release, and target platform have been verified.
