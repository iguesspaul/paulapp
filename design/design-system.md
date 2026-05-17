# Personal App — Design System
*Derived from mood board: Necto Mono · Leica · Mt. Fuji · Pastelle · Archival Portrait · Parametric Architecture*

---

## The Aesthetic

**"Warm Brutalism"** — The board resolves into a single sensibility: precision-built dark interfaces with an emotional warmth underneath. Monospace as the primary typographic voice (Necto Mono influence), deep charcoal not pure black (grain and humanity preserved), and a dueling accent system where **cobalt blue** (intellectual, structural) and **amber** (warmth, energy, aliveness) push against each other like the parametric building against the mountain.

The Leica dictates materiality: things should feel **machined**, not rounded into friendliness. The Pastelle book spread brings **catalog density** — information can be packed because the grid is confident. The portrait adds **grain as atmosphere**, not noise.

---

## Tailwind `@theme` (CSS)

Place this in your `app.css` (or `global.css`) inside the `@theme` layer for Tailwind v4:

```css
@import "tailwindcss";

@theme {
  /* ── Typography ─────────────────────────────────── */
  --font-mono: "Geist Mono", "JetBrains Mono", ui-monospace, monospace;
  --font-sans: "Geist", "DM Sans", ui-sans-serif, system-ui, sans-serif;

  /* Scale — monospace-first, editorial contrast */
  --text-xs:   0.6875rem;   /* 11px — metadata, timestamps */
  --text-sm:   0.75rem;     /* 12px — labels, tags */
  --text-base: 0.875rem;    /* 14px — body, list items */
  --text-md:   1rem;        /* 16px — card titles */
  --text-lg:   1.25rem;     /* 20px — section headers */
  --text-xl:   1.75rem;     /* 28px — page headers */
  --text-2xl:  2.5rem;      /* 40px — hero numbers (stats, scores) */
  --text-3xl:  4rem;        /* 64px — editorial display */

  --font-weight-normal:  400;
  --font-weight-medium:  500;
  --font-weight-bold:    700;

  --leading-tight:  1.1;
  --leading-normal: 1.5;
  --leading-loose:  1.8;

  --tracking-tighter: -0.04em;
  --tracking-tight:   -0.02em;
  --tracking-normal:   0;
  --tracking-wide:     0.06em;
  --tracking-widest:   0.12em;

  /* ── Color Palette ──────────────────────────────── */

  /* Backgrounds (dark-first) */
  --color-ground:    #0d0d0d;   /* true base — used sparingly */
  --color-base:      #111111;   /* app background */
  --color-surface:   #181818;   /* primary card/panel */
  --color-raised:    #1f1f1f;   /* elevated card, hover states */
  --color-overlay:   #282828;   /* modals, dropdowns */
  --color-border:    #2c2c2c;   /* default borders */
  --color-divider:   #222222;   /* subtle lines */

  /* Text */
  --color-text-primary:   #e8e6e0;   /* main text — warm white */
  --color-text-secondary: #8a887e;   /* muted */
  --color-text-tertiary:  #4a4845;   /* placeholder, disabled */
  --color-text-inverse:   #0d0d0d;   /* text on bright surfaces */

  /* Accent — Cobalt (structural, informational) */
  --color-cobalt-dim:    #0f2a4a;
  --color-cobalt-muted:  #163d6e;
  --color-cobalt:        #2563eb;   /* primary interactive */
  --color-cobalt-bright: #3b82f6;   /* hover state */
  --color-cobalt-glow:   #60a5fa;   /* active/focus rings */

  /* Accent — Amber (warmth, urgency, alive) */
  --color-amber-dim:    #2a1a04;
  --color-amber-muted:  #6b3a0c;
  --color-amber:        #d97706;   /* primary warm accent */
  --color-amber-bright: #f59e0b;   /* hover/highlight */
  --color-amber-glow:   #fbbf24;   /* active */

  /* Semantic */
  --color-success: #16a34a;
  --color-danger:  #dc2626;
  --color-warning: #ca8a04;
  --color-info:    var(--color-cobalt);

  /* Grain / Film */
  --color-grain-light: rgba(232, 230, 224, 0.03);
  --color-grain-heavy: rgba(232, 230, 224, 0.06);

  /* ── Spacing ─────────────────────────────────────── */
  --spacing-px:  1px;
  --spacing-0-5: 0.125rem;   /* 2px */
  --spacing-1:   0.25rem;    /* 4px */
  --spacing-2:   0.5rem;     /* 8px */
  --spacing-3:   0.75rem;    /* 12px */
  --spacing-4:   1rem;       /* 16px */
  --spacing-5:   1.25rem;    /* 20px */
  --spacing-6:   1.5rem;     /* 24px */
  --spacing-8:   2rem;       /* 32px */
  --spacing-10:  2.5rem;     /* 40px */
  --spacing-12:  3rem;       /* 48px */
  --spacing-16:  4rem;       /* 64px */
  --spacing-20:  5rem;       /* 80px */
  --spacing-24:  6rem;       /* 96px */

  /* ── Radius ──────────────────────────────────────── */
  --radius-none: 0;
  --radius-sm:   0.125rem;   /* 2px — tags, chips: nearly sharp */
  --radius-md:   0.375rem;   /* 6px — buttons, inputs */
  --radius-lg:   0.625rem;   /* 10px — cards */
  --radius-xl:   1rem;       /* 16px — modals, large panels */
  --radius-pill: 9999px;     /* tags, badges */

  /* ── Shadows ─────────────────────────────────────── */
  --shadow-sm:  0 1px 3px rgba(0,0,0,0.5);
  --shadow-md:  0 4px 12px rgba(0,0,0,0.6);
  --shadow-lg:  0 12px 32px rgba(0,0,0,0.7);
  --shadow-cobalt: 0 0 0 1px var(--color-cobalt);
  --shadow-amber:  0 0 12px rgba(217, 119, 6, 0.25);

  /* ── Transitions ────────────────────────────────── */
  --ease-out-expo:  cubic-bezier(0.16, 1, 0.3, 1);
  --ease-in-expo:   cubic-bezier(0.7, 0, 0.84, 0);
  --ease-bounce:    cubic-bezier(0.34, 1.56, 0.64, 1);
  --duration-fast:  120ms;
  --duration-base:  200ms;
  --duration-slow:  350ms;
}
```

---

## Design Conventions

### 1 · Typography

**Rule: Monospace as the primary voice, sans only for prose density.**

- **Geist Mono** (or JetBrains Mono) is the workhorse. Use it for: all headings, all data values (scores, times, percentages, stats), navigation labels, button text, tags.
- **Geist Sans** is the supporting voice. Use only for: multi-line body text (task descriptions, movie summaries), tooltips, and inline prose longer than ~2 lines.
- Never mix two non-mono faces in the same component.

**Scale in practice:**
| Use case | Size | Weight | Font | Tracking |
|---|---|---|---|---|
| Hero stats / display numbers | `3xl` 64px | 700 | Mono | tight (-0.04em) |
| Page title | `xl` 28px | 700 | Mono | tight |
| Section header | `lg` 20px | 500 | Mono | tight |
| Card title | `md` 16px | 500 | Mono | normal |
| Body / description | `base` 14px | 400 | Sans | normal |
| Labels, tags, nav | `sm` 12px | 500 | Mono | wide (0.06em) |
| Timestamps, metadata | `xs` 11px | 400 | Mono | widest (0.12em) |

**All-caps is reserved exclusively for:** section labels (OUR MISSION), category tags, status chips. Use `tracking-widest` when setting text all-caps.

**All text that is not the aformentioned should be entirely lowercase** This includes titles of cards, text inside, body text, timestamps, metadata. 

---

### 2 · Color Usage

**The two-accent rule:** Every interactive or highlighted element uses either cobalt or amber — never both at once in the same component. The choice carries meaning:
- **Cobalt** → navigation, links, selected states, informational data, upcoming/future events
- **Amber** → active/in-progress items, streak indicators, urgency, live scores, "on" states

**Background layering (elevation model):**
```
base (#111111)          ← app bg, sidebar
  └── surface (#181818) ← default card
        └── raised (#1f1f1f) ← hover card, active row, expanded panel
              └── overlay (#282828) ← modals, context menus, dropdowns
```
Never jump more than one elevation level for a single nesting. A card on a page can be surface. A popover from that card is overlay.

**Grain overlay:** Apply a subtle film grain texture to the base background and to large hero areas. Implementation:
```css
.grain::after {
  content: "";
  position: absolute;
  inset: 0;
  background-image: url("data:image/svg+xml,..."); /* or SVG noise */
  opacity: 0.035;
  pointer-events: none;
}
```

---

### 3 · Borders & Edges

**Philosophy:** Borders are structural, not decorative. They define edges, not style.

- Default border: `1px solid var(--color-border)` (#2c2c2c)
- Hover border: 1px solid #3a3a3a
- Active/selected border: 1px solid `var(--color-cobalt)` or `var(--color-amber)` depending on context
- **No box shadows for card distinction** — use a 1px border and the elevation color system
- Left-border accent (Pastelle catalog influence): for list items or section markers, a `2px solid var(--color-cobalt)` or `var(--color-amber)` left border on a flush-padded container is the preferred highlight mechanic, not a colored background

---

### 4 · Cards & Containers

**Anatomy of a card:**
```
padding: 16px (compact) or 20px (default) or 24px (spacious)
border-radius: var(--radius-lg) → 10px
background: var(--color-surface)
border: 1px solid var(--color-border)
```
Cards never have drop shadows — the border + background contrast creates the distinction.

**Catalog density (Pastelle influence):** Cards can be information-dense. Don't add whitespace for whitespace's sake. Tight rows of data within a card are good. The breathing room happens *between* cards in the grid, not inside them.

**Card types:**
- **Stat card** — monospace number at 40–64px, label in all-caps 12px below, minimal chrome
- **List card** — compact rows at 40–44px height, left-border accent on hover
- **Module card** — full feature panel (todo list, habit tracker), uses spacious padding, internal sections separated by `var(--color-divider)` lines

---

### 5 · Interactive States

All transitions use `var(--ease-out-expo)` at `var(--duration-base)` (200ms).

| State | Treatment |
|---|---|
| Default | As designed |
| Hover (clickable) | background shifts one elevation up + border lightens |
| Active/pressed | background drops to ground, scale: 0.98 |
| Selected | left-border in accent color + background tinted with 4% cobalt or amber |
| Disabled | opacity: 0.35, no pointer events |
| Focus | 1px solid `var(--color-cobalt-glow)` outline, 2px offset |

---

### 6 · Tags & Pills

Two variants only:

**Tag (sharp, Leica influence):**
```
font: 11px Mono, 500, tracking-widest, uppercase
padding: 2px 6px
border-radius: var(--radius-sm) → 2px
border: 1px solid var(--color-border)
background: transparent
color: var(--color-text-secondary)
```

**Pill (status, Necto Mono influence):**
```
font: 11px Mono, 500, tracking-wide, uppercase
padding: 3px 8px
border-radius: var(--radius-pill)
background: cobalt-dim or amber-dim
color: cobalt-glow or amber-glow
border: none
```
Pills are for live status (IN PROGRESS, LIVE, STREAK). Tags are for categories.

---

### 7 · Navigation

**Sidebar approach (recommended):**
- Width: 220px collapsed content, 16px padding each side
- Items: 14px Mono, 500, tracking-normal
- Active state: left `2px solid var(--color-cobalt)` + `color: var(--color-text-primary)`
- Inactive: `color: var(--color-text-secondary)`, hover shifts to secondary background
- Section dividers: 1px `var(--color-divider)` with 12px margin
- No icons unless they are precisely rendered (16×16 SVG, 1px stroke weight)

---

### 8 · Layout Grid

**Mobile-first, single column base → 12-column on desktop:**
- Sidebar: fixed 252px (220px content + 2×16px padding)
- Main content: fluid, max-width 960px
- Internal card grid: 2-col on tablet, 3-col on desktop, with `gap: 12px`
- Page padding: `24px` horizontal on all scroll content
- Section spacing: `32px` between major sections

**Editorial scale contrast (Mt. Fuji influence):** At least one element per main section should be significantly larger than everything else. A habit streak counter at 64px sitting above 12px labels. A sports score at 48px. A movie title at 28px with 12px metadata below it. This ratio is what gives the app energy.

---

### 9 · Motion

**Principles:**
- **Enter:** translate Y +4px to 0, opacity 0→1, 200ms ease-out-expo
- **Exit:** opacity 1→0, 120ms ease-in-expo (never translate on exit)
- **Data updates (scores, numbers):** counter/odometer animation, 400ms ease-out-expo
- **List reorder:** layout transition 200ms ease-out-expo
- **Never animate layout properties** (width, height, padding) — only transform and opacity

**Page transitions (SvelteKit):**
```javascript
// Crossfade between routes
// in: fly({ y: 6, duration: 200, easing: expoOut })
// out: fade({ duration: 120 })
```

---

### 10 · Feature-Specific Notes

**Todo / Project Manager:**
- Checkbox: custom 16×16 SVG, 1px stroke, fills with cobalt on check
- Completed items: `text-decoration: line-through`, text drops to tertiary color
- Priority: amber left-border for high priority, cobalt for in-progress, none for default
- Group headers: all-caps 11px Mono, tracking-widest, secondary color

**Sports:**
- Live scores use amber pill (LIVE) + large monospace numbers
- Upcoming uses cobalt (date in cobalt-bright)
- Standings table: monospace, alternating rows at surface vs raised background, no borders between rows
- Team names: title-case Sans, scores Mono

**Habit Tracker:**
- Calendar grid cells: 20×20px with 4px gap, filled with amber on complete, border only on incomplete
- Streak count: amber 40px+ display number
- Current day: cobalt-muted background cell

**Movie Recommendations:**
- Poster: 2:3 ratio, loaded with blur-up
- Metadata bar (year, genre, rating): all-caps 11px tags
- No ratings as stars — use a Mono percentage or decimal instead

---

### 11 · What to Avoid

- **No purple.** Not in this palette.
- **No white backgrounds.** Light mode is not planned; if it ever is, design it fresh.
- **No rounded-everything.** Radius is applied deliberately. Not every container is a pill. Keep `radius-sm` (2px) and `radius-none` in active use.
- **No gradients on interactive surfaces.** Gradient is only permitted on photography overlays (linear-gradient to darken) and data visualizations.
- **No colored backgrounds on cards.** Cards stay in the elevation system. Color lives in borders, text, and small indicators — not card fills.
- **No Inter.** Not in the spirit of this board.

---

## Quick Reference: Font Installation

```html
<!-- In app.html -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Geist+Mono:wght@400;500;700&family=Geist:wght@400;500;700&display=swap">
```

Or install via npm:
```bash
npm install geist
```
Then in CSS:
```css
@import 'geist/dist/geist-mono.css';
@import 'geist/dist/geist.css';
```
