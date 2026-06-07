# Project Instructions

This is a local-first Python + Streamlit credit card benefit tracker.

Core rules:

- Stay with Python, Streamlit, pandas/openpyxl, and local CSV/Excel files.
- Do not add bank sync, auth, scraping, cloud sync, or complex frontend frameworks.
- Preserve the existing app structure and data workflow.
- Make small, incremental, maintainable changes.
- Do not rebuild from scratch unless explicitly asked.
- Keep the app private, beginner-friendly, scan-friendly, and action-oriented.
- Completed and ignored benefits should stay out of the main active view unless the user chooses to show them.
- Prefer simple Streamlit-native UI over custom complexity.
- Do not modify original Excel source data unless explicitly requested.

UI/design workflow rules:

- For any UI, CSS, visual design, mobile layout, accessibility, or interaction polish task, first read and apply the installed `frontend-design` skill at `C:\Users\yuxua\.codex\skills\frontend-design\SKILL.md`.
- For any UI, CSS, visual design, mobile layout, accessibility, or interaction polish task, also read and apply the installed `web-design-guidelines` skill at `C:\Users\yuxua\.codex\skills\web-design-guidelines\SKILL.md`.
- When using `web-design-guidelines`, fetch the latest guideline source named in that skill before reviewing or changing UI code.
- For mobile, touch, iOS Safari, or phone-first UI work, also read and apply the project-local Apple Human Interface Guidelines skill at `docs\skills\apple-human-interface-guidelines\SKILL.md`.
- When applying Apple Human Interface Guidelines, check hierarchy, harmony with device constraints, platform consistency, safe areas, reading order, alignment, adaptive layout, legibility, contrast, touch ergonomics, and accessibility.
- Before editing UI code, explicitly choose a clear aesthetic direction and state how the change supports it.
- Apply UI changes systematically through typography, color, spacing, surfaces, focus states, touch targets, motion/reduced-motion, and text overflow handling instead of only adding ad hoc CSS patches.
- After UI changes, verify the app still loads locally and check both `http://127.0.0.1:8501/?mobile=true` and the current LAN URL when the local Streamlit server is running.

Design brief rule:

Only read `PRODUCT_DESIGN_BRIEF.md` when the user asks for a major UI redesign or explicitly references the design brief. For small scoped changes, follow the short `AGENTS.md` rules and avoid reading the full brief.
