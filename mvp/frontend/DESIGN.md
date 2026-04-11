# SaaS-IA Design System

**Version:** 2.0 — Total Overhaul  
**Date:** 2026-04-12  
**Classifier:** APP UI (workspace-driven, data-dense, task-focused)  
**Stack:** Next.js 15 + Tailwind CSS 4 + Radix UI + MUI 6 (token-bridged)

---

## Philosophy

This is an AI command center. Not a SaaS marketing site. Not a dashboard template.

The user is a builder — someone who runs agents, processes data, monitors pipelines, and ships. The interface should feel like the cockpit of a precision instrument: calm, information-dense, and completely unambiguous. Every element earns its presence.

**Four principles:**

1. **Dark by default.** The app lives in the dark. Light mode is a secondary configuration, not a design priority.
2. **Utility language.** Every label is a status, an orientation, or an action. Never aspirational copy.
3. **Cyan is the one accent.** One accent color. Used sparingly. It signals "interactive" and "active" — nothing else.
4. **No decorative anything.** No blobs. No gradient orbs. No colored-circle icons. No left-border cards. If a section feels empty, the content is wrong, not the decoration budget.

---

## Reference: What This Should Feel Like

From the design-hub palette analysis:

- **Linear** (`#191A1B` surface, `#5E6AD2` accent) — masterclass in dark-mode-first product design
- **Raycast** (`#07080A` surface, `#18191A` card) — dark interior of a precision instrument
- **Vercel** (`#171717` surface, `#0072F5` accent) — developer infrastructure made invisible
- **Cursor** (`#26251E` surface, `#F54E00` accent) — warm minimalism meets code-editor elegance
- **MongoDB** (`#001E2B` surface, `#00ED64` accent) — deep-forest terminal

Our identity: **deep navy/slate** surfaces + **cyan** accent. Terminal-native. The AI works. You watch.

---

## Color System

### Primitive Palette

**Primary (Cyan)** — interactive, active, AI output
```
--color-primary-50:  hsl(187, 61%, 97%)
--color-primary-100: hsl(187, 71%, 94%)
--color-primary-200: hsl(187, 81%, 88%)
--color-primary-300: hsl(187, 88%, 78%)
--color-primary-400: hsl(187, 93%, 65%)   ← accent
--color-primary-500: hsl(187, 96%, 52%)   ← accent-dim
--color-primary-600: hsl(187, 98%, 42%)
--color-primary-700: hsl(187, 100%, 33%)
--color-primary-800: hsl(187, 100%, 25%)
--color-primary-900: hsl(187, 100%, 18%)
--color-primary-950: hsl(187, 100%, 12%)
```

**Neutral (Slate-Navy)** — surfaces, text, borders
```
--color-neutral-50:  hsl(210, 40%, 98%)
--color-neutral-100: hsl(210, 40%, 96%)
--color-neutral-200: hsl(214, 32%, 91%)
--color-neutral-300: hsl(213, 27%, 84%)
--color-neutral-400: hsl(215, 20%, 65%)
--color-neutral-500: hsl(215, 16%, 47%)
--color-neutral-600: hsl(215, 19%, 35%)
--color-neutral-700: hsl(215, 25%, 27%)
--color-neutral-800: hsl(217, 33%, 17%)
--color-neutral-900: hsl(222, 47%, 11%)
--color-neutral-950: hsl(229, 84%, 5%)
```

### Semantic — Dark Mode (Default)

| Token | Value | Usage |
|-------|-------|-------|
| `--bg-app` | `hsl(229, 84%, 5%)` | Page background — the void |
| `--bg-surface` | `hsl(222, 47%, 11%)` | Sidebar, navbar |
| `--bg-elevated` | `hsl(217, 33%, 17%)` | Cards, panels |
| `--bg-overlay` | `hsl(215, 25%, 27%)` | Dropdowns, hover states |
| `--text-high` | `hsl(210, 40%, 98%)` | Primary text |
| `--text-mid` | `hsl(215, 20%, 65%)` | Secondary text, labels |
| `--text-low` | `hsl(215, 19%, 35%)` | Disabled, metadata |
| `--border` | `hsl(217, 33%, 17%)` | Card borders |
| `--border-subtle` | `hsl(222, 47%, 11%)` | Section dividers |
| `--accent` | `hsl(187, 93%, 65%)` | Interactive elements, active nav |
| `--accent-dim` | `hsl(187, 96%, 52%)` | Hover state of accent |
| `--accent-glow` | `hsla(187, 96%, 47%, 0.15)` | Focus rings, subtle emphasis |
| `--accent-foreground` | `hsl(187, 96%, 5%)` | Text on accent backgrounds |

### Semantic — Light Mode

| Token | Value |
|-------|-------|
| `--bg-app` | `hsl(210, 40%, 98%)` |
| `--bg-surface` | `hsl(0, 0%, 100%)` |
| `--bg-elevated` | `hsl(210, 40%, 96%)` |
| `--bg-overlay` | `hsl(214, 32%, 91%)` |
| `--text-high` | `hsl(222, 47%, 11%)` |
| `--text-mid` | `hsl(215, 25%, 27%)` |
| `--text-low` | `hsl(215, 20%, 65%)` |
| `--border` | `hsl(214, 32%, 91%)` |
| `--border-subtle` | `hsl(210, 40%, 96%)` |
| `--accent` | `hsl(187, 98%, 42%)` |
| `--accent-dim` | `hsl(187, 96%, 52%)` |

### Status Colors

| Purpose | Color | Dark mode token |
|---------|-------|----------------|
| Success | `#10B981` | `--success` |
| Warning | `#F59E0B` | `--warning` |
| Error | `#EF4444` | `--error` |
| Info | `hsl(187, 93%, 65%)` = accent | `--accent` |
| Running | `#06B6D4` | `--running` |

**Rule:** Never use red/green only combinations. Always add a label or icon alongside color.

---

## Typography

### Font Stack

```css
--font-sans:    "Inter Variable", "Inter", system-ui, sans-serif;
--font-mono:    "JetBrains Mono Variable", "JetBrains Mono", monospace;
--font-display: "Geist Variable", "Geist", sans-serif;
```

**Display** (`--font-display`) is used for headings h1–h2 and hero text only.  
**Sans** (`--font-sans`) is used for all UI text — labels, body, buttons, nav.  
**Mono** (`--font-mono`) is used for code, IDs, file paths, timestamps, technical values.

### Scale (Perfect Fourth — 1.333)

| Token | Size | Line-height | Weight | Usage |
|-------|------|-------------|--------|-------|
| `--text-xs` | 0.625rem | 1.6 | 400 | Metadata, timestamps |
| `--text-sm` | 0.75rem | 1.5 | 400 | Secondary labels, badges |
| `--text-base` | 0.875rem | 1.5 | 400 | Body copy, form fields |
| `--text-md` | 1rem | 1.4 | 500 | Card titles, nav items |
| `--text-lg` | 1.125rem | 1.3 | 600 | Section headers |
| `--text-xl` | 1.25rem | 1.25 | 600 | Page titles |
| `--text-2xl` | 1.5rem | 1.2 | 700 | h2, dashboard metrics |
| `--text-3xl` | 2rem | 1.15 | 700 | h1, hero stat |
| `--text-4xl` | 2.5rem | 1.1 | 700 | Large hero numbers |

**Rules:**
- Body text: minimum 14px (`--text-base` = 0.875rem). Never below 12px for any visible label.
- No letterspacing on lowercase body text.
- Headings: `letter-spacing: -0.02em` (tight).
- Use `text-wrap: balance` on all h1–h3.
- Tabular nums on all numeric columns: `font-variant-numeric: tabular-nums`.
- Mono font on: file paths, IDs, API keys, hashes, timestamps, token counts, latency values.

---

## Spacing

Base: 4px. Scale is multiples of 4.

```
--space-0: 0px
--space-1: 4px
--space-2: 8px
--space-3: 12px
--space-4: 16px
--space-5: 20px
--space-6: 24px
--space-8: 32px
--space-10: 40px
--space-12: 48px
--space-16: 64px
```

**Rules:**
- Related items: `--space-2` gap between them.
- Card internal padding: `--space-4` or `--space-5`.
- Section separation: `--space-8` or `--space-10`.
- Sidebar item padding: `10px 12px` (predictable, compact).
- Never use arbitrary pixel values in component styles. Use the scale.

---

## Border Radius

```
--radius-none: 0px
--radius-sm:   4px     ← badges, chips
--radius-md:   6px     ← inputs, buttons
--radius-lg:   8px     ← cards, panels
--radius-xl:   12px    ← large cards, modals
--radius-2xl:  16px    ← dialog max
--radius-full: 9999px  ← pills only
```

**Rule:** Radius hierarchy matters. A card (`--radius-lg`) contains a button (`--radius-md`). Inner elements always have smaller or equal radius. Never `border-radius: 24px` on a small button.

---

## Shadows

Shadows use cyan glow — consistent with the accent system. They communicate elevation, not decoration.

```
--shadow-sm:  0 0 4px 0 hsla(187, 96%, 47%, 0.30)
--shadow-md:  0 0 8px 0 hsla(187, 96%, 47%, 0.40), 0 2px 4px rgba(0,0,0,0.30)
--shadow-lg:  0 0 16px 0 hsla(187, 96%, 47%, 0.45), 0 4px 6px rgba(0,0,0,0.35)
--shadow-xl:  0 0 32px 0 hsla(187, 96%, 47%, 0.50), 0 8px 12px rgba(0,0,0,0.40)
--shadow-glow: 0 0 20px hsla(187, 96%, 47%, 0.60)
```

**Rule:** Only use `--shadow-glow` on elements the user is actively hovering or focusing. Not on decorative backgrounds.

---

## Layout Architecture

### Shell Structure

```
┌─────────────────────────────────────────────────────┐
│  Topbar (48px)  — breadcrumbs, search, user menu    │
├──────────┬──────────────────────────────────────────┤
│  Sidebar │  Main content area                       │
│  (240px) │                                          │
│  bg-surface   bg-app                                │
│          │  max-width: 1400px, auto side margins    │
│          │  padding: 24px                           │
└──────────┴──────────────────────────────────────────┘
```

### Sidebar

- Width: 240px (expanded), 56px (collapsed icon-only)
- Background: `--bg-surface`
- No gradient background. No background images.
- Section labels: `--text-low`, `text-xs`, `letter-spacing: 0.08em`, UPPERCASE — 6 max characters
- Nav item height: 36px
- Active item: `--accent-glow` background, `--accent` text, left border `2px solid --accent`
- Hover item: `--bg-elevated` background
- Icons: 16px, monochrome, `--text-mid` color (not colored per category)

### Navigation Groups (from 42 backend modules)

```
SIDEBAR STRUCTURE
────────────────
▸ Overview
  Dashboard

▸ AI CORE
  Agents
  Multi-Agent Crew
  Memory
  AI Compare

▸ CREATE
  Content Studio
  Image Gen
  Video Gen
  Audio Studio
  Presentations
  Voice Clone

▸ ANALYZE
  Data Analyst
  Sentiment
  Instagram Intel
  AI Monitoring
  Cost Tracker

▸ KNOWLEDGE
  Web Crawler
  Transcription
  YouTube
  PDF Processor
  Knowledge Base

▸ ENGAGE
  Conversations
  Chatbot Builder
  Realtime AI
  Forms

▸ AUTOMATE
  Workflows
  Pipelines
  Integrations

▸ BUILD
  Code Sandbox
  Repo Analyzer
  Skill Seekers
  Fine-Tuning

▸ SEARCH
  Unified Search
  Marketplace

▸ PLATFORM (bottom, collapsed by default)
  Workspaces
  Billing
  API Keys
  Feature Flags
  Tenants
  Security
  Secrets
  Audit Log
```

### Topbar

- Height: 48px
- Background: `--bg-surface` with `border-bottom: 1px solid --border`
- Left: breadcrumb path (module name only, not full path)
- Center: global search (Cmd+K) — 320px wide
- Right: notifications icon, user avatar + name

---

## Component Rules

### Cards

**When to use a card:** Only when the content inside IS the interaction — a result item, a task, a document. Not for grouping statistics or wrapping sections.

**Card anatomy:**
```
surface-card = bg-elevated + border-border + radius-lg + padding-5
```

No colored left borders. No gradient backgrounds on cards. No drop shadows on idle cards. `--shadow-sm` on hover only.

**Stat display (not a card):** Metrics on the dashboard are NOT cards. They are inline stat rows — label above, value large, trend small below. No icon-in-circle.

### Buttons

```
Primary:   bg-accent, text-accent-foreground, radius-md, h-9 (36px), px-4
Secondary: bg-elevated, text-high, border-border, radius-md, h-9
Ghost:     transparent, text-mid, hover:bg-elevated
Danger:    bg-error/10, text-error, border-error/30, hover:bg-error/20
```

All buttons: `cursor-pointer`. Focus: `outline: 2px solid --accent-glow, outline-offset: 2px`.

**Label rules:** Always specific. "Run Agent" not "Submit". "Export PDF" not "Download". "Cancel Job" not "Cancel".

### Inputs / Forms

- Height: 36px (sm), 40px (md), 44px (lg)
- Border: `--border` idle, `--accent` focus
- Background: `--bg-elevated`
- Placeholder: `--text-low`
- Error state: red border + specific error message below (what went wrong + what to do)
- No floating labels. Label above, always visible.

### Tables

- Row height: 44px
- Header: `--text-low`, `text-xs`, uppercase, `letter-spacing: 0.06em`
- Alternating rows: off (use hover instead)
- Hover row: `--bg-elevated`
- Numeric columns: `font-variant-numeric: tabular-nums; text-align: right`
- ID/hash columns: `font-family: --font-mono; font-size: --text-xs`

### Badges / Status chips

```
Variants: default | success | warning | error | running | pending
Size:     xs (h-4, text-xs) | sm (h-5, text-xs) | md (h-6, text-sm)
Radius:   --radius-sm
```

No emoji in badges. Status: dot + label. Never color-only.

### Empty States

Required format: icon (24px, monochrome) + heading (specific) + body (1 sentence, what to do) + CTA button.

Example: "No agents yet" → "Run your first agent to automate a task. Agents can browse the web, analyze data, write code, and more." + "Create Agent" button.

Never: "No items found." alone.

### Loading States

Skeleton shapes must match the content they represent. A text line skeleton for a text line. A stat block skeleton for a stat block. No generic gray rectangle where a chart will appear.

Loading text: "Running…" not "Running..." (ellipsis character `…` not three dots).

---

## Motion

- Entering elements: `ease-out`, 150ms
- Exiting elements: `ease-in`, 100ms
- Moving elements: `ease-in-out`, 200ms
- Page transitions: slide + fade, 200ms
- Data updates (chart, stat): number count-up, 400ms ease-out

**`prefers-reduced-motion`:** All animations except opacity transitions must be disabled.

**Only animate:** `transform` and `opacity`. Never `width`, `height`, `top`, `left`, `max-height`.

**No `transition: all`.** Always list explicit properties.

---

## AI Slop Blacklist (hard NO)

These patterns are banned. If you find them in the code, remove them:

1. Purple/violet/indigo gradient backgrounds — we have cyan, that's it
2. 3-column feature grid with icon-in-colored-circle
3. Icons in colored circles as navigation or section decoration
4. `text-align: center` on all headings inside cards
5. Uniform `border-radius: 24px` on everything
6. Decorative blobs, floating circles, radial gradient orbs as backgrounds
7. Emoji in headings or as bullet points
8. `border-left: 3px solid <accent>` cards
9. "Welcome to SaaS-IA", "Unlock the power of...", "Your all-in-one AI solution"
10. Cookie-cutter section rhythm in page content

**Specific to the existing codebase — currently failing:**
- `WelcomeBanner` has two radial gradient orbs (lines 97–100 in dashboard/page.tsx) — remove
- `WelcomeBanner` uses `background: linear-gradient(135deg, hsl(187,96%,10%) 0%, hsl(260,60%,12%) 100%)` — the purple component `hsl(260,60%,12%)` violates the single-accent rule
- `StatCard` uses `linear-gradient(135deg, ${gradientFrom}, ${gradientTo})` on the icon container — colored circles
- Dashboard hero uses emoji `👋` — remove
- "Your AI platform is running smoothly" — aspirational copy, not utility

---

## Page-Specific Rules

### Dashboard

The dashboard is a **command center**, not a homepage. It answers: what's happening right now?

**Layout:**
```
Row 1: System status bar (one line — active modules count, API health, last sync)
Row 2: 4 stat columns (no cards — inline layout with dividers)
Row 3: Split — main content (2/3) + sidebar (1/3)
  Main: Recent activity feed (real data from all modules)
  Sidebar: Quick actions + AI budget remaining
Row 4: Charts (usage over time, top modules)
```

**No "Welcome back" banner.** The user knows they're back. The status bar tells them what's running.

### Module Pages

Each module page follows this pattern:
```
Header: Module name (h1) + one-sentence description + primary action button
Body:   Two-panel layout
  Left panel (60%):  Input / configuration
  Right panel (40%): Output / results / history
```

No decorative section headers. No "About this module" copy blocks.

### Auth Pages

- Full-screen, dark, minimal
- Logo centered at top
- Form: max-width 400px, centered
- No marketing copy on auth pages. No testimonials. No feature lists.
- Error states inline, specific

---

## Accessibility

- WCAG AA minimum everywhere. Body text 4.5:1, large text 3:1.
- `focus-visible` ring: `outline: 2px solid var(--accent), outline-offset: 2px` on all interactive elements. Never `outline: none` without a replacement.
- All icons that convey meaning have `aria-label`.
- Touch targets: minimum 44px on any interactive element.
- ARIA landmarks: `<main>`, `<nav aria-label="sidebar">`, `<header>`.

---

## What's Changed From v1

| v1 (Sneat/Materio) | v2 (SaaS-IA Command Center) |
|--------------------|----------------------------|
| Purple primary (`#8C57FF`) | Cyan primary (`hsl(187, 93%, 65%)`) |
| Purple-tinted dark surfaces | Deep navy surfaces |
| Icon-in-gradient-circle stat cards | Inline stat rows, no icons |
| Gradient welcome banner with orbs | Compact system status bar |
| Generic SaaS copy | Utility labels only |
| MUI sx prop inline styles | CSS tokens + Tailwind utilities |
| Sneat template navigation | Module-aware grouped navigation |
| Colored category icons | Monochrome icons, accent for active only |
