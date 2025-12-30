# BetBoard Menu Bar UX Guide

This document defines the UX principles and layout for the SwiftUI menu bar app.
It is intentionally minimal: surface key info fast, avoid clutter, and keep the
menu compact.

## Goals
- Fast glanceable updates: key moves, watchlist, headlines.
- Minimal clicks: one click to see everything important.
- Professional feel: consistent typography, spacing, and hierarchy.
- Non-touting: show market changes + news, never "best bets".

## Menu Bar Item
- Use a simple, legible SF Symbol or custom template icon.
- Default state: monochrome template icon that respects light/dark mode.
- Optional indicator: a small dot or badge count for "notable moves".
- Avoid busy animations; update only when counts change.

## Menu Content Structure
Order is stable and predictable:
1) Header row (app name + last updated time)
2) Tabs (NFL / CFB / UFC) as segmented control or compact picker
3) Watchlist (top 5)
4) Notable Moves (top 5)
5) Headlines (top 5)
6) Actions (Refresh, Settings, Quit)

## Layout Rules
- Keep the full menu height short enough to fit typical screens; use top N lists.
- Each row should be single-line, no wrapping where possible.
- Use subtle dividers between sections, not heavy borders.
- Use consistent alignment: left-align team names and headlines.
- Favor density over decoration; avoid large paddings.

## Interaction Rules
- Single click opens menu; no additional windows by default.
- Use "Open Details" only if needed (e.g., open full app window later).
- Allow keyboard navigation and standard menu shortcuts.
- Refresh respects rate limits; show a brief "Updated" timestamp instead of spinners.

## Content Formatting
- Event rows: "Away @ Home — 7:30p"
- Move rows: "Spread -2.5 → -3.5 (Book)" or "ML -120 → -105"
- Headlines: short title only; open in browser on click.

## Accessibility
- All items should have clear labels for VoiceOver.
- Respect Reduce Motion and Increase Contrast settings.
- Avoid color-only meaning; pair dots with text count.

## SwiftUI Notes
- Use `MenuBarExtra` for the status item and menu content.
- Use `Section` and `Divider` to organize lists.
- Keep list rows as `Button` for click targets; provide `keyboardShortcut` where sensible.
- Store settings in `AppStorage`, and API key in Keychain.

## Reference Links
- Apple HIG: Menus (JS-only site): https://developer.apple.com/design/human-interface-guidelines/menus
- Apple HIG: macOS (overview): https://developer.apple.com/design/human-interface-guidelines/macos
- Menu bar extras overview: https://developer.apple.com/design/human-interface-guidelines/macos/menus
