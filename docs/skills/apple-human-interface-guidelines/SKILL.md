---
name: apple-human-interface-guidelines
description: Apply Apple Human Interface Guidelines to mobile, touch-first, iOS Safari, or Apple-platform-inspired UI work. Use when changing phone layouts, touch controls, visual hierarchy, dark mode, spacing, safe areas, legibility, or accessibility.
---

# Apple Human Interface Guidelines

Use this skill for mobile-first Streamlit UI changes and Apple-platform-inspired visual polish.

## Workflow

1. Check the current official Apple Human Interface Guidelines before major UI decisions:
   - https://developer.apple.com/design/human-interface-guidelines/
   - https://developer.apple.com/design/human-interface-guidelines/layout
   - https://developer.apple.com/design/human-interface-guidelines/accessibility
   - https://developer.apple.com/design/human-interface-guidelines/designing-for-ios
2. Choose the aesthetic direction before editing. Describe how the change supports hierarchy, harmony, and consistency.
3. Review layout against mobile constraints:
   - Content respects safe areas and avoids edges that fight device chrome.
   - Reading order puts the most important content near the top and leading side.
   - Cards, controls, and lists align consistently and scan cleanly while scrolling.
   - Dense controls stay usable on touch screens; avoid crowding tap targets.
4. Review visual treatment:
   - Text remains legible in light and dark surfaces.
   - Contrast is sufficient without relying only on color.
   - Surfaces distinguish controls from content.
   - Motion is subtle and has a reduced-motion fallback.
5. Review accessibility:
   - Information is perceivable without relying on one cue.
   - Text wraps or truncates intentionally without overlap.
   - Focus, hover, and active states are visible.
   - Layout adapts to small phone widths.
6. Verify the app after changes on local and mobile URLs when the Streamlit server is running.

## Project Constraints

Keep the implementation Streamlit-native and incremental. Do not introduce a new frontend framework for Apple-style polish.
