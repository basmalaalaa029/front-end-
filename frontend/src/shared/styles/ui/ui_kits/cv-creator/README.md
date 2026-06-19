# CV Creator UI kit

Resume editor with inline AI suggestion rail.

**Components**
- `AppSidebar`, `AppHeader` (shared) — global chrome
- `CVCanvas` — the printable resume surface (header, sections, entries, skills)
- `SectionsPanel` — drag-handle list of sections (Summary / Experience / Education / Skills / Projects / Awards)
- `AIRail` — score gauge + section picker + suggestion stack with Apply/Dismiss

**Interaction:** clicking "Apply" on a suggestion briefly highlights the affected bullet on the canvas (mossy-tint background) to show what changed.
