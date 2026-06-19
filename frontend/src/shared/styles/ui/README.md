# CareerPilot Design System

> An AI career copilot. Build a CV worth reading, analyze it against any role, find matching jobs, and rehearse the interview — all in one place.

CareerPilot is a desktop-first web product organized around four AI-driven surfaces:

| Surface | Role |
|---|---|
| **CV Creator** | Drag-and-drop editor with inline AI rewrites |
| **CV Analysis** | Score, gap analysis, and section-by-section critique against a target role |
| **Job Agent** | Autonomous search across boards + ranked match list |
| **Interview Sim** | Voice/text rehearsal with a recruiter-style AI + scored feedback |

The brand voice is a **professional advisor** — calm, specific, never gimmicky. The visual system is **earthy and grounded** (moss greens, warm clays, bone neutrals) with **AI features front and center** — clearly marked but never flashy.

> **Note:** This system was built from a written brief (no existing codebase, Figma, or logo). Everything here — wordmark, palette, type pairing, copy — is **proposed direction**, not a recreation. Treat it as v0; iterate freely.

---

## Index

| File | Purpose |
|---|---|
| `README.md` | This file — full guidelines |
| `SKILL.md` | Frontmatter for Claude Code / agent skill compatibility |
| `colors_and_type.css` | All design tokens (color, type, spacing, radii, shadows, motion) |
| `assets/` | Logo (`logo.svg`, `logo-mark.svg`, `logo-on-dark.svg`) |
| `preview/` | Design-system cards (16 cards across Type / Colors / Spacing / Components / Brand) |
| `ui_kits/cv-creator/` | CV editor — resume canvas, section blocks, AI suggestion rail |
| `ui_kits/cv-analysis/` | Score dashboard, gap matrix, section critique |
| `ui_kits/job-agent/` | Search results, match cards, agent task list |
| `ui_kits/interview-sim/` | Mock-interview session, transcript, scoreboard |

Fonts: **Geist** + **Geist Mono** (Google Fonts CDN, no local files needed). Icons: **Lucide** (CDN).

---

## Content fundamentals

CareerPilot's voice is a **trusted professional advisor** — like a good career coach who has done this 10,000 times and won't waste your time.

**Tone.** Calm, specific, outcome-oriented. We don't hype. We don't apologize. We don't lecture. We give a clear recommendation and the reasoning behind it, then get out of the way.

**Person.**
- **"We" + "you"** in product copy. *"We pulled 12 new matches for you this morning."*
- **"You"** when giving advice. *"Your summary buries the win — lead with the 38% improvement."*
- Never **"I"** from the AI. The copilot speaks as a service, not as a personality.

**Casing.** Sentence case everywhere — buttons, nav, page titles, modal headers. Reserve Title Case for proper nouns (CareerPilot, Stripe, Senior Product Designer) and the wordmark only.

**Punctuation.** Periods on full sentences; trim from fragments and CTAs. Em-dashes for tightening sentences — like that. Oxford comma always.

**Length.**
- Buttons: 1–3 words. *"Continue"*, *"Apply suggestion"*, *"Run analysis"*
- Section headings: ≤ 5 words
- Body paragraphs: 1–3 sentences in product UI; never wall-of-text
- AI suggestion cards: lead with the action, follow with one-sentence why

**AI-generated content is always labeled.** We use the `AI suggestion`, `Copilot`, or `Suggested by AI` badge any time the user is reading something the model wrote. Never sneak generations into the canvas as if the user typed them.

**Emoji: no.** Not in marketing, not in product, not in AI replies. The brand reads as professional; emoji breaks that. Unicode arrows (→), bullets (·), and currency glyphs are fine.

**Numbers are tabular.** Match scores, salary ranges, dates, counts — all set in Geist Mono so columns align.

**Voice samples.**

| ❌ Off-brand | ✅ On-brand |
|---|---|
| Wow, looks like your resume needs some love! 🎯 | Three sections need work before this is recruiter-ready. |
| Hi! I'm Cara, your AI buddy. Let's crush this job hunt together! | We've ranked 47 roles against your background. The top 6 are strong matches. |
| Click here to start your journey | Start a new resume |
| Sorry, something went wrong 😞 | We couldn't reach the job board. Retry in a few seconds. |

---

## Visual foundations

### Color

The palette is **earthy and grounded** — three brand scales (moss, clay, bone) with semantic mappings on top.

- **Moss** is the only brand color in product chrome. Buttons, focus rings, active nav, selected states, the AI badge, the logo mark — all moss-600 (`#3C6240`). Moss is also success.
- **Clay** is the rare accent — used for *secondary* CTAs ("Apply now"), Pro/upgrade affordances, the occasional category tag. Never for primary action.
- **Bone** replaces gray throughout. Backgrounds are warm cream (`#FAF7F0`), borders are bone-200 (`#ECE5D4`), text is near-black with a warm cast (`#1B1A16`). Never use a true neutral gray.
- **Inverse surfaces** (`#1F1A14`) appear in tooltips, the agent-task drawer, and code blocks. Crisp warm-black, not pure black.

### Type

Geist (sans) and Geist Mono are the only families. Two display sizes, four body sizes, two micro sizes. Headings use `-0.015em` to `-0.025em` tracking (tighter as they grow). Body line-height is **1.6** so dense product copy still breathes. Numbers and code drop into Geist Mono — match scores, salary ranges, hotkeys.

### Backgrounds & imagery

No full-bleed photography in product chrome. No gradients (the AI button is the one exception, a subtle moss-600 → moss-700). No hand-drawn illustrations. The marketing surface can feature **single editorial photographs** of people at work (warm-graded, golden-hour) but the product is type + cards on warm cream. No textures. No noise overlays.

### Animation

Motion is **subtle, not playful**. Transitions are 140–220ms with `cubic-bezier(0.22, 0.61, 0.36, 1)` (decelerate). Bounces and springs are reserved for the AI-token reveal (when copilot returns a suggestion). Page navigation is instant (no fade). Hover states fade in over 140ms. Don't animate layout shifts.

### States

- **Hover:** primary buttons darken (moss-600 → moss-700). Secondary buttons get a 1px border darkening + cream fill. Cards lift via shadow-md → shadow-lg. Never scale on hover.
- **Press:** buttons shift to moss-800. No scale-down. No ripple.
- **Focus:** 3px focus ring at `rgba(60,98,64,0.25)`. Always visible — never `outline: none` without a replacement.
- **Disabled:** 50% opacity + `cursor: not-allowed`. No greying-to-gray; keep brand color.

### Borders, radii, elevation

- **Borders** are bone-200 by default — `1px solid #ECE5D4`. Stronger borders (`#D9D0BB`) only for inputs and dividers between major regions.
- **Radii:** 6px for buttons/inputs, **10px for cards** (the workhorse), 14px for panels, 20px for hero/empty-state illustrations. Pill (999px) is **badge-only**, never containers.
- **Shadows** are warm-tinted (`rgba(40, 30, 15, x)`), never neutral gray. Most cards rest at `shadow-xs` (1px hairline); the active/focused card lifts to `shadow-md`. Modals at `shadow-xl`.
- **Inner shadow** on inputs (`inset 0 1px 2px rgba(40,30,15,.05)`) — subtle press-in, makes them feel like writable surfaces.

### Layout

- **Desktop-first.** Min product width 1280px; designs comfortable to 1440px+.
- **Sidebar nav** at 260px (collapsed 64px). Fixed.
- **Header** at 60px. Fixed.
- **Content** in two patterns: a single 760px reading column (CV editor, analysis), or a three-pane layout (list / detail / context — used in Job Agent).
- **Cards** carry their own padding (18–24px depending on density). Grid gap between cards is 12–16px.

### Transparency & blur

Reserved for **the AI suggestion overlay** (semi-transparent surface above the canvas with 12px backdrop-blur) and **dropdown menus** (95% white over a 4px blur, so the canvas hints through). Everything else is opaque.

### Imagery color cast

When marketing uses photography: **warm-graded, slight golden tint, soft contrast**. Subjects are mid-career professionals working — no stock-handshake. Faces are visible. No B&W. No grain. No filter packs.

---

## Iconography

**Lucide** is the icon system — clean line icons at 1.75 stroke width, currentColor inheritance, sized in three steps: **16px** (inline), **20px** (default UI), **24px** (large affordances).

- **Loaded from CDN** in this design system (`https://unpkg.com/lucide@latest/dist/umd/lucide.min.js`). No local copy. Use `<i data-lucide="name"></i>` then `lucide.createIcons()`.
- **Stroke** is 1.75 — between Lucide default (2) and Phosphor's thin (1.5). Just enough weight to read at 16px without feeling chunky.
- **Never fill icons.** No two-tone, no solid variants. Outline only.
- **Brand-aligned subset** (most-used): `file-text`, `sparkles`, `briefcase`, `search`, `target`, `message-square`, `mic`, `play`, `check-circle-2`, `alert-triangle`, `download`, `upload`, `settings`, `bell`, `user`, `bookmark`, `building-2`, `map-pin`, `dollar-sign`, `arrow-right`. See `preview/iconography.html`.
- **AI marker** is always `sparkles` — wherever AI is in the UI, sparkles is the icon. Don't substitute.

**No emoji.** Not for empty states, not for celebrations, not for "fun" CTAs. The brand is professional; emoji breaks the register.

**No custom illustration.** Empty states use a small Lucide icon (24–32px) above one line of copy and one CTA. No floating people, no abstract shapes, no spot illustrations. If/when illustration is needed, brief a real illustrator — don't have the agent draw SVG.

---

## UI kits

Each kit lives in `ui_kits/<surface>/`:
- `README.md` — what's in it
- `index.html` — interactive click-through assembled from the components
- `*.jsx` — small, focused components (sidebar, header, score card, etc.)

Open `ui_kits/cv-creator/index.html` etc. directly to see each surface.

---

## Open questions / known caveats

- **No real logo provided.** The leaf-on-page wordmark is a quick proposed mark — likely wants a proper design pass.
- **Font substitution risk.** Geist on Google Fonts has the latest weights, but if your brand calls for true on-disk control, drop TTF/WOFF2 files into `fonts/` and swap the `@import` for `@font-face`.
- **Domain copy is invented.** Job titles, companies, salary ranges, interview questions — all plausible-sounding placeholders. Replace with real fixtures before user-testing.
- **No mobile breakpoints.** Desktop-first as requested; mobile is intentionally out of scope for v0.
