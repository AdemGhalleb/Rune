# Rune — Design System & UX Specification

This document is the visual and interaction contract for Rune. It contains no code — every decision here should be directly implementable by a frontend engineer without needing to make a visual judgment call themselves.

**One note before the system itself:** the brief asks for a Knowledge Graph as a headline feature. Worth being explicit about the framing, since it matters for the design: a plain "notes linked to notes" graph (Obsidian's graph view) is a demo feature people stop using within a week — it doesn't tell you anything actionable. What's designed below is different and narrower: a graph whose nodes are **course concepts**, colored and sized by **tracked mastery**, so it functions as a visual mastery dashboard, not a decorative map of file links. That distinction shapes every decision in the Knowledge Graph section — keep it in mind if implementation pressure ever pulls it back toward a generic graph view.

---

## 1. Design Philosophy

Five principles govern every screen:

1. **Calm over busy.** No screen should compete for attention with itself. One primary action per view. Generous whitespace is the default, not an afterthought.
2. **Content is the interface.** Chrome (sidebars, headers, borders) recedes; the student's documents, conversations, and progress are what's visually loud.
3. **Earned color.** Neutral by default. Color appears only to carry meaning — mastery level, status, a single accent for interactive elements — never for decoration.
4. **Motion explains state, not decorates it.** Every animation answers "what just happened" or "what's about to happen." If it doesn't, it's cut.
5. **Trust through restraint.** This app touches a student's academic life and, later, their email. The interface should feel like software that takes that seriously — closer to Linear or Arc than to a hobbyist AI wrapper.

**What we're avoiding, specifically:** the boxy multi-pane density of Discord/Slack, the syntax-heavy utilitarianism of VSCode, and the now-generic "centered chat column on white background" look of ChatGPT clones. Rune should be recognizable as its own product from a single screenshot.

---

## 2. Typography

| Role | Family | Notes |
|---|---|---|
| UI / body | **Inter** (or **Geist Sans**) | Excellent at small sizes, neutral, doesn't call attention to itself — the right choice for an app people read inside for hours. |
| Headings / display | Same family, heavier weights | Deliberately *not* a separate display face — a second typeface reads as "marketing site," and this is a working tool. Hierarchy comes from weight and size, not typeface switching. |
| Code / technical (equations, file paths, extracted quotes) | **JetBrains Mono** or **Berkeley Mono** | Only place monospace appears — code blocks, LaTeX-adjacent math, file paths in document cards. |

**Scale** (desktop, 1x):

| Token | Size / Line-height | Weight | Use |
|---|---|---|---|
| `text-xs` | 12 / 16 | Regular | Metadata, timestamps, captions |
| `text-sm` | 13 / 20 | Regular | Secondary UI text, labels |
| `text-base` | 15 / 24 | Regular | Body text, chat messages — 15px not 16px; feels calibrated rather than default-browser |
| `text-lg` | 17 / 26 | Medium | Card titles, section headers |
| `text-xl` | 20 / 28 | Semibold | Panel headers |
| `text-2xl` | 26 / 34 | Semibold | Screen titles (Dashboard greeting, Settings page title) |
| `text-3xl` | 34 / 42 | Semibold | Onboarding / empty-state hero text only |

**Why this scale:** a 15px body size with tight, deliberate line-height increments (not a generic 1.5x multiplier) is what gives Linear and Raycast their "considered" feel versus a default browser stylesheet. Weight does most of the hierarchy work — we use four weights total (Regular 400, Medium 500, Semibold 600, Bold 700 reserved for rare emphasis), never more.

**Letter-spacing:** slightly negative (-0.01em to -0.02em) on headings ≥20px, 0 on body text. Never positive tracking except all-caps labels (+0.04em), used sparingly for things like section eyebrows ("KNOWLEDGE GAPS").

---

## 3. Spacing, Radius, Shadow, Grid

**Spacing scale** (4px base unit — every margin/padding value is a multiple of this):
```
2  4  8  12  16  24  32  48  64  96
```
Component-internal padding typically uses 8/12/16; layout-level gaps use 24/32/48+.

**Border radius:**
| Token | Value | Use |
|---|---|---|
| `radius-sm` | 6px | Inputs, small buttons, tags |
| `radius-md` | 10px | Cards, dropdowns, standard buttons |
| `radius-lg` | 16px | Modals, panels, large cards |
| `radius-full` | 9999px | Avatars, pills, icon buttons |

Never sharp (0px) corners anywhere — but also never above 16px on anything but pills; excessive rounding reads as playful/consumer rather than premium/professional, which is the wrong register here.

**Shadows** — used sparingly, only to indicate elevation above the base surface (modals, dropdowns, the command palette), never on static cards:
| Token | Use | Character |
|---|---|---|
| `shadow-sm` | Dropdowns, tooltips | Barely-there, 1-2px blur radius, ~4% opacity |
| `shadow-md` | Popovers, context menus | Soft, ~8% opacity, larger blur |
| `shadow-lg` | Modals, command palette | Most pronounced, still soft-edged — never a hard drop shadow |

Cards and panels at rest use **border, not shadow**, for definition — this is the single biggest lever for the "calm" feeling versus a more consumer-app aesthetic that shadows everything.

**Icon sizes:** 16px (inline with text), 20px (default UI icon size, nav/buttons), 24px (section headers, empty states). One icon set throughout — [Lucide](https://lucide.dev) (or Phosphor) — never mixed sets. Icons are always 1.5px stroke weight, never filled, except for a single active/selected state indicator (e.g., a filled dot on the active sidebar item).

**Layout grid:** desktop-first, minimum supported width 1280px, comfortable at 1440-1920px.
- Sidebar: fixed 260px (collapsible to 64px icon rail).
- Content area: fluid, max-width 880px for reading-focused views (chat, document detail), full-width for dashboard/graph/tables.
- Consistent 32px outer padding on all primary content areas.

---

## 4. Color System

Both themes are built from the **same semantic token names** — a component never references a raw color, only a token, so light/dark is a token-swap, not a per-component redesign.

### Semantic tokens

| Token | Purpose |
|---|---|
| `bg-base` | The window/app background — the quietest surface in the app |
| `bg-surface` | Cards, panels, the sidebar — one step up from base |
| `bg-surface-elevated` | Modals, dropdowns, popovers — the surface that sits "above" everything else |
| `border-subtle` | Default dividers and card borders — barely visible, present for structure not emphasis |
| `border-default` | Input borders, more visible separators |
| `text-primary` | Main content — document text, chat messages, headings |
| `text-secondary` | Supporting text — descriptions, metadata labels |
| `text-muted` | Timestamps, placeholder text, disabled states |
| `accent-primary` | The single brand/interactive color — primary buttons, active nav item, links, focus rings |
| `accent-subtle` | Accent at low opacity — selected-row backgrounds, active tab underline background |
| `success` | Completed tasks, "indexed" status, positive mastery |
| `warning` | Approaching deadlines, "needs review" mastery state, pending approval |
| `error` | Failed jobs, model-unavailable states, destructive-action confirmation |
| `info` | Neutral informational states — e.g., "syncing," background job indicators |
| `selection` | Selected text / selected list-item background |
| `hover` | Hover-state background for interactive rows/buttons — a very subtle wash, not a hard color change |
| `focus-ring` | Keyboard focus indicator — always visible, always the accent color, 2px, never removed for aesthetics |

**Usage rule:** `accent-primary` appears in exactly one place per screen as a rule of thumb — the primary action. Everything else uses the neutral scale. This is what keeps the app feeling calm rather than a rainbow of competing CTAs — a discipline Linear and Raycast both hold to strictly.

### Light Mode

- `bg-base`: warm off-white, not pure `#FFFFFF` — closer to `#FAFAF8`, with a faint warmth (a hint of yellow/red in the mix) rather than cool gray, which keeps long reading sessions from feeling clinical.
- `bg-surface`: very soft warm gray, `#F4F3F1`-family.
- `bg-surface-elevated`: pure white `#FFFFFF`, so modals/dropdowns visibly lift off the warmer base.
- `border-subtle`: near-invisible, ~`#00000008`-`#0000000F` equivalent — present on close inspection, not consciously noticed.
- `text-primary`: near-black warm gray, not pure black (`#1A1917`-family) — pure black on warm white is harsher than needed.
- `accent-primary`: a muted, desaturated indigo/blue (not electric blue) — trustworthy, calm, works identically in both themes at adjusted lightness.

### Dark Mode

- `bg-base`: deep charcoal, `#141413`-family — never pure black (`#000000`), which crushes contrast and looks cheap on OLED and non-OLED alike.
- `bg-surface`: one step lighter, `#1C1B1A`-family.
- `bg-surface-elevated`: another step up, `#242322`-family — modals should be clearly liftable from surface without needing a heavy shadow to prove it.
- `border-subtle`: soft light-gray at low opacity — subtlety matters even more in dark mode, where borders can easily look like glowing outlines if too bright.
- `text-primary`: warm off-white, not pure white — `#EDECE9`-family; pure white text on dark backgrounds causes eye strain over long sessions, which matters a lot for a study tool.
- `accent-primary`: the same hue as light mode, lightness/saturation adjusted for contrast on dark — the two themes should read as the same product, not two different apps.

**Both themes share:** identical spacing, radius, typography, and motion — only the color tokens swap. This is the "designed together" requirement — swap the theme mid-session (a toggle in Settings) and nothing should reflow or feel like a different app.

---

## 5. Components

Each entry: purpose, states, and the one or two decisions that matter most.

### Buttons
- **Primary:** filled `accent-primary`, white/near-white text, `radius-md`. One per screen/section, reserved for the single most important action.
- **Secondary:** `border-default` outline, `text-primary`, transparent fill. The default for most actions.
- **Ghost/tertiary:** no border, `text-secondary`, background appears only on hover. Used for low-emphasis actions (icon buttons, "Cancel").
- **Destructive:** outline or ghost by default, only fills solid `error` red on the confirming step of a destructive action (e.g., inside the "Delete workspace" confirmation modal, not on the initial trigger).
- States: default, hover (subtle lighten/darken + slight background wash), active/pressed (slightly deeper), disabled (50% opacity, no hover response), loading (spinner replaces label, button width preserved to avoid layout shift).

### Inputs
- Single-line height 36px, `radius-sm`, `border-default` at rest, `accent-primary` border + `focus-ring` on focus — never a color-only focus indicator (accessibility).
- Placeholder text at `text-muted`.
- Inline validation errors appear below the field in `error` color with a small icon — never a red border alone.

### Search Bar
- Appears in Documents and as the trigger surface for the Command Palette (see below) — visually consistent between the two so students learn one pattern.
- Icon-left, `bg-surface` fill, `border-subtle`, expands slightly (subtle width/shadow change) on focus.

### Sidebar / Navigation
- Fixed left rail, `bg-surface` against the app's `bg-base` content area — this contrast (however subtle) is what visually anchors navigation without needing borders everywhere.
- Sections top-to-bottom: workspace/course switcher (top), primary nav (Home, Chat, Documents, Learning, Knowledge Graph, Tasks, Email), settings/profile (bottom, visually separated).
- Active item: filled `accent-subtle` background, `accent-primary` text/icon, `radius-md`, no border — a soft highlight, not a hard tab.
- Collapsible to a 64px icon-only rail (tooltip on hover) — persistent user preference, not per-session.

### Cards (general)
- `bg-surface`, `border-subtle`, `radius-md`, no shadow at rest.
- Hover (where clickable): border shifts to `border-default`, no lift/shadow — motion is a background/border transition only, keeping the "calm" rule.

### Dropdowns / Select
- Trigger looks like a ghost button with a chevron; menu is `bg-surface-elevated`, `shadow-md`, `radius-md`, items use `hover` background on hover, `accent-subtle` on selected.

### Tabs
- Underline style, not filled-pill style — a 2px `accent-primary` underline under the active tab label, `text-secondary` for inactive, `text-primary` for active. Reserved for switching views within one context (e.g., Document detail: Preview / Chunks / Citations-used).

### Modals
- `bg-surface-elevated`, `radius-lg`, `shadow-lg`, centered, max-width 480px for confirmations / 640px for forms, backdrop is `bg-base` at ~40% opacity with light blur.
- Always dismissible via Escape and backdrop click, except mid-destructive-confirmation.

### Context Menus
- Same visual language as Dropdowns, triggered by right-click on documents, memories, tasks — a power-user affordance students discover naturally, not a primary interaction path.

### Command Palette
- **A first-class citizen of this app, not an afterthought** — given the Linear/Raycast inspiration, `Cmd/Ctrl+K` should feel like the fastest way to do anything: jump to a course, start a new chat, search documents, trigger "generate practice questions," open Settings.
- Centered overlay, `bg-surface-elevated`, `shadow-lg`, `radius-lg`, search input at top (identical styling to the main search bar), results grouped by type (Actions / Documents / Conversations / Courses) with muted section labels.
- Keyboard-first: arrow keys navigate, Enter selects, no mouse required for any palette action.

### Notifications (toast)
- Bottom-right stack, `bg-surface-elevated`, `shadow-md`, `radius-md`, auto-dismiss 4s for informational, persistent (manual dismiss) for anything requiring awareness (e.g., "3 new email extractions ready for review").
- Icon + short text only — never a place for a paragraph; link out to the relevant screen instead.

### Progress Indicators
- **Linear** (indexing progress, embedding progress): thin 2px bar, `accent-primary` fill on `bg-surface` track, `radius-full`. Used in the sync-status indicator and job-tracking UI.
- **Circular/spinner**: for indeterminate short waits (button loading states) only — never for long jobs, where the linear + percentage is more honest and less anxiety-inducing.
- **Percentage label** shown for any job expected to take >5 seconds; omitted for near-instant ones to avoid flicker.

### Loading States
- Skeleton screens (subtle pulsing `bg-surface` blocks matching the eventual content's shape) for anything that loads in under ~2s (document lists, conversation history).
- For genuinely long operations (initial workspace indexing), a dedicated state (see Dashboard/Empty States) rather than a skeleton — skeletons implying "almost done" for a multi-minute job is misleading.

### Empty States
- Every empty state answers "why is this empty" and "what do I do about it" — never just an icon and "No items found."
- Example (Documents, before any workspace selected): icon, one-line explanation, single primary button ("Select your workspace folder").
- Example (Knowledge Graph, before enough interaction data exists): explanation that mastery tracking builds up as they study/chat/practice — sets expectation rather than looking broken.

### Chat Bubbles
- **Not** the rounded speech-bubble-with-tail pattern (too casual/consumer for this product). Instead: user messages right-aligned in a subtle `accent-subtle`-tinted `bg-surface` block, `radius-md`; assistant messages left-aligned, no background at all (just text on `bg-base`), visually distinguishing "the assistant's voice" from "a boxed reply" — closer to how Claude Desktop/Linear present conversational text than a bubble-chat aesthetic.
- Assistant messages that include citations show a compact source-chip row directly beneath the response (see Source Citation Cards).

### Thinking / Tool-Execution Indicator
- A single-line, low-emphasis status row above the streaming response: muted text + subtle animated dots or a slow shimmer on the text itself (e.g., "Searching Operating Systems notes…" → "Checking your recent mastery…"). Replaces itself with the streamed answer — never a separate collapsible "chain of thought" panel by default (too technical/noisy for the target user), though a "show details" expand affordance can reveal the retrieval/tool steps for students who want it.

### Source Citation Cards
- Small, inline chip-style cards (not full document previews) directly under an assistant message: document icon, truncated title, page/section reference. Clicking opens the document at that location in a side panel, not a full navigation away from chat — preserves conversational flow.

### Knowledge Graph Nodes
- See §7 for full interaction spec. Visually: circular nodes, size = concept "weight" in the course (how much material references it), fill saturation/color = mastery level (see mastery-color mapping in §7) rather than arbitrary node colors per category — the color *is* the information.

### Flashcards
- Centered card, `bg-surface`, `radius-lg`, generous internal padding (32px+), question state and answer state are the same physical card (flip animation, see Motion), never two separate stacked cards — reduces visual clutter and matches the mental model of "turning a card over."

### Quiz Cards
- Single question per screen (not a scrolling list) — keeps focus, matches the "calm" principle even under a knowledge-testing context.
- Options as full-width selectable rows (not radio buttons + label as separate elements) — the whole row is the hit target, `border-default` at rest, `accent-subtle` fill on selection, `success`/`error` color revealed only after submission, not before (no leaking correctness through hover states).

### Deadline Cards
- Compact row: title, course tag (small colored pill using a per-course accent, not the semantic palette — see note below), relative due date (`text-warning` if <72 hours out, `text-muted` otherwise), status checkbox.
- **Course tags are the one place a wider color palette is allowed** — each course gets a consistent, muted color for quick visual scanning across a dense task list. This is separate from the semantic token system and assigned automatically (a fixed rotating palette of ~8 muted hues), not user-configured in v1.

### Settings Panels
- Single-column, grouped by section with clear headers (Workspace, AI Models, Privacy, Email, Appearance) — a sidebar-within-settings for navigation between groups, not one long scrolling page, given how many sections this product will accumulate (model config, privacy toggles, email, appearance).

### Workspace Selector
- First-run: a focused, centered, single-purpose screen (see §9 Onboarding flow) — not a generic settings field. This is a big decision for the student (which folder becomes "their brain") and deserves its own moment, not a buried form field.
- Post-onboarding: accessible from Settings > Workspace, same visual pattern as onboarding but non-modal.

### Document Cards
- List row (Documents view, dense): icon by file type, title, course tag, status indicator (`success` dot = indexed, `info` pulsing dot = processing, `error` dot = failed), relative modified time.
- Grid/card variant (optional, toggle in Documents view): larger card with a subtle file-type-colored top accent bar, title, course tag, chunk count as a small muted stat.

---

## 6. Motion

**Global rule: 150-250ms for most transitions, ease-out for things appearing/entering, ease-in for things leaving.** Nothing bounces, nothing overshoots — springy/playful motion is wrong for this product's register.

| Interaction | Duration | Character |
|---|---|---|
| Hover states (buttons, rows, cards) | 100ms | Simple opacity/background fade, no movement |
| Panel open (side panel, settings) | 200ms | Slide + fade from the relevant edge, ease-out |
| Modal open | 180ms | Scale from 98%→100% + fade, ease-out — a whisper of motion, not a pop |
| Page/view transitions (sidebar nav) | 150ms | Cross-fade only — no slide, since these are unrelated views, not a spatial sequence |
| Command palette open | 150ms | Fade + slight scale, backdrop blur fades in simultaneously |
| Dropdown/context menu | 120ms | Fade + 4px vertical offset resolving to 0 — fast enough to feel instant |
| Chat token streaming | n/a (real-time) | Tokens append with no per-token animation — a steady, calm stream reads as more trustworthy than a jittery typewriter effect; the *thinking indicator* (§5) carries the "processing" feeling, not character-by-character reveal tricks |
| Flashcard flip | 300ms | 3D-ish flip on the Y-axis, ease-in-out — the one place a slightly longer, more deliberate animation is earned, since it mimics a real physical action the student understands |
| Knowledge graph node selection | 200ms | Selected node + its direct edges brighten/scale slightly; everything else dims (not hides) — keeps spatial context |
| Loading skeletons | continuous, subtle | Slow (1.5s cycle) opacity pulse, never a hard left-to-right shimmer sweep — too "loud" for this product's tone |

**What's explicitly avoided:** parallax, bounce/spring easing, confetti or celebratory animation on task completion (a calm checkmark fade is enough — this isn't a gamified consumer app), page-transition slides that imply spatial navigation between unrelated views.

---

## 7. Application Layout & Navigation

**Structure:** persistent left sidebar (per §5) + a content area that is always one of these top-level views:

```
Home (Dashboard)
Chat
Documents
Learning        (Flashcards / Quizzes / Review)
Knowledge Graph
Tasks
Email
Settings
```

**Navigation model:** flat, not nested-tree — clicking a sidebar item replaces the content area entirely (cross-fade transition per §6). Course scoping (e.g., "show me Operating Systems specifically") happens via a **course switcher at the top of the content area**, not via sidebar nesting — this keeps the sidebar stable and shallow (a core Linear-style navigation principle: the primary nav should never need to scroll or expand infinitely as courses/data grow).

**Within-view secondary navigation** (e.g., Document detail's Preview/Chunks tabs, Settings' section list) uses Tabs or a settings-specific sub-sidebar, never a second global-feeling sidebar — one persistent nav surface only.

---

## 8. Dashboard (Home)

The home screen must justify itself as more than a launch pad to Chat. What the student sees, top to bottom:

```
┌──────────────────────────────────────────────────────────┐
│  Good afternoon, Alex.                          [🔍 ⌘K]   │
│                                                              │
│  ┌─ Today's Focus ─────────────────────────────────────┐  │
│  │  ● Review: Process Scheduling (Operating Systems)     │  │
│  │    Weak spot, last touched 9 days ago                 │  │
│  │  ● Practice: 5 questions on Dynamic Programming        │  │
│  │  ● Deadline in 2 days: Database project                │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─ Courses ──────────────────────────────────────────┐   │
│  │  [Operating Systems]  [Algorithms]  [Databases]  [+]  │   │
│  │   62% mastery          78% mastery    41% mastery      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─ Recent Activity ──────┐  ┌─ Upcoming ─────────────┐   │
│  │  Continue: "Explain     │  │  Database project — 2d  │   │
│  │  chapter 4" (OS)         │  │  Algo midterm — 9d      │   │
│  └──────────────────────────┘  └──────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

**Rationale for each block:**
- **Today's Focus is the top, largest element** — this is the direct expression of the product's core loop (weakness + deadline-ranked recommendations) from the earlier product strategy. It is not optional chrome; it's the reason the home screen exists as more than a chat launcher.
- **Courses row with mastery percentage** gives an at-a-glance state-of-the-semester view — clicking a course scopes the whole app (chat, documents, learning) to it.
- **Recent Activity / Upcoming** are secondary, smaller, and explicitly below the fold priority-wise — useful, not the headline.
- No blank chat box on this screen at all — Chat is one click away in the sidebar, but the home screen's job is to tell the student something, not ask them what they want.

---

## 9. Onboarding Flow (First-Run)

```
[1] Welcome            [2] Select Workspace         [3] Indexing            [4] First Chat
 "Your knowledge   →    Folder picker, clear    →    Progress view,    →    Suggested prompt,
  stays yours."          explanation that files       "This runs in           lands in Chat
  Single CTA.             aren't moved/copied.         the background —        pre-scoped to a
                          Optional: pick a               keep exploring."       just-indexed
                          default LLM (Ollama                                   course.
                          auto-detected vs cloud).
```

Each step is a **single focused screen**, centered content, generous whitespace, one primary action — no multi-field forms crammed into one view. Step 3 (Indexing) is not a blocking spinner — the student can proceed to explore Documents or Settings while it runs in the background, with a persistent progress indicator in the sidebar/header (per §5 Progress Indicators) until complete.

---

## 10. Chat Experience

**Layout:** single centered column (max-width per §3 grid), course switcher pinned at the top, message history scrolls above a fixed composer at the bottom.

**Sequence for a typical exchange:**
1. Student sends a message → immediately appears right-aligned (§5 Chat Bubbles).
2. Thinking indicator appears left-aligned below it (§5), cycling through brief status text as retrieval/memory-lookup happens server-side.
3. Response streams in as plain text (no bubble), tokens appended smoothly, no per-token animation (§6).
4. On completion, a compact citation-chip row appears beneath the response if sources were used (§5 Source Citation Cards).
5. If the response includes a generated artifact (practice quiz, flashcard set), it renders **inline as an embedded card** within the chat flow (not a separate modal) — e.g., a compact quiz-card preview with a "Start" button, keeping the conversational thread intact while still surfacing rich content.

**Tool execution:** visible only as the thinking-indicator status line by default (§5) — an optional "Show steps" expand link reveals a simple, muted list of what was checked (documents searched, memories referenced), for students who want the transparency without forcing it on everyone by default.

---

## 11. Knowledge Graph

**What it is, precisely:** a per-course graph where **nodes are concepts** (from the mastery taxonomy, not individual documents or notes) and **edges represent conceptual relationships** (prerequisite, related-topic) inferred during ingestion — not a file-link graph.

**Visual mapping:**
- **Node size** = how central/heavily-referenced the concept is in the course material.
- **Node color/saturation** = mastery level — a single-hue gradient (e.g., muted red → amber → the accent green) rather than arbitrary category colors, so the graph reads as a heatmap of understanding at a glance.
- **Edge thickness** = strength of conceptual relationship.

**Navigation:**
- Pan via click-drag, zoom via scroll/pinch — standard, no custom gesture vocabulary to learn.
- **Selection:** clicking a node brightens it and its direct edges, dims (not hides) everything else (§6) — preserves context of where the concept sits in the whole course.
- Selecting a node opens a compact side panel (not a modal — keep the graph visible) showing: concept name, current mastery %, "last practiced" date, and quick actions ("Practice this," "Ask about this").
- **Zoom levels:** at low zoom, only high-weight concept nodes show labels (avoids label clutter); labels progressively appear for smaller nodes as the student zooms in.

**Why this design, explicitly:** a graph that's just "here are your notes and how they link" doesn't help a student decide what to do next — it's the exact "impressive but useless" trap flagged earlier. A graph that visually says "this cluster is red, you're behind here" is a direct, glanceable expression of the mastery map and gives the student an actionable next step (click the red node → practice).

---

## 12. Learning (Flashcards, Quizzes, Review)

**Structure:** three modes under one "Learning" nav item, switchable via Tabs:

- **Review Session** — the default/recommended entry point: a queue auto-assembled from weak + due-for-review concepts (spaced-repetition-style decay), not a manual deck the student has to build. One flashcard or quiz question at a time, full-screen-focused (minimal chrome, sidebar can auto-collapse during a session to reduce distraction).
- **Flashcards** — auto-generated per concept from the student's own material; flip animation per §6; simple self-rating after reveal ("Got it" / "Still shaky") feeds directly into the mastery model.
- **Quiz Mode** — auto-generated multiple-choice/short-answer questions, weighted toward weak concepts (§5 Quiz Cards); a results summary at the end shows per-concept breakdown, not just a raw score — the breakdown is what's actionable.

**Daily recommendation surfacing:** the same "Today's Focus" data model from the Dashboard drives a "Recommended for you" queue at the top of the Learning view — one consistent recommendation source across the app, not two separate systems.

**Progress tracking:** a simple per-course mastery trend (small sparkline, not a dense analytics dashboard) — enough to show "this is moving in the right direction," not a data-heavy reporting screen that turns studying into spreadsheet-watching.

---

## 13. Key User Flows

**Flow: First question about course material**
```
Sidebar → Chat → (course switcher: select "Operating Systems")
→ type question → send → thinking indicator → streamed answer
→ citation chips appear → click a citation → side panel opens
   showing the source document at that page, chat stays visible
```

**Flow: Reviewing before an exam**
```
Dashboard → "Today's Focus" shows exam-proximity-ranked item
→ click "Review: Process Scheduling"
→ lands in Learning > Review Session, pre-filtered to that concept
→ complete cards/questions → session summary →
   mastery updates reflected immediately on next Dashboard visit
```

**Flow: Email deadline extraction (approval-gated)**
```
Background: email sync job runs → toast notification
  "1 new deadline detected" (persistent until dismissed/actioned)
→ click toast → Email > Extractions view
→ card shows original email summary + proposed task
→ [Approve] creates the task (Tasks view) and a deadline memory
   [Dismiss] discards it — nothing is created automatically either way
```

**Flow: Managing what Rune remembers**
```
Settings > Memory (or a dedicated Memory nav surface)
→ list grouped by category (Knowledge Gaps / Preferences / Goals / Deadlines)
→ each row: content, source course, edit/delete inline actions
→ delete requires no confirmation modal (low-stakes, easily reversible
   by nature of how memory re-accumulates) — a single click with an
   "Undo" toast, not a blocking confirmation dialog
```

---

## 14. UX Rationale Summary

| Decision | Why |
|---|---|
| No shadows on resting cards, borders instead | Primary lever for "calm" over "busy" — shadow-heavy UIs read as consumer/playful |
| One accent color, used sparingly | Prevents competing CTAs; trains the eye that color = "this matters" |
| Chat bubbles asymmetric (boxed user / plain assistant) | Distinguishes voices without the casual bubble-chat register of consumer messaging apps |
| No per-token streaming animation | A steady stream reads as more considered/trustworthy than a jittery typewriter effect |
| Dashboard leads with Today's Focus, not a chat box | Directly embodies the product's differentiator (proactive, mastery-driven) rather than presenting as "yet another chatbot" |
| Knowledge graph nodes = concepts + mastery color, not file links | Converts a demo feature into an actionable, glanceable status view |
| Command palette as first-class | Matches the Linear/Raycast inspiration directly; rewards power users without punishing everyone else with a cluttered UI |
| Approval-gated email flow has no auto-action | Trust — a wrong auto-created deadline is worse than a slightly slower manual step |
| Memory deletion has no confirmation modal | Matches the actual stakes (low, reversible) rather than defaulting to friction everywhere |
| Warm off-white/charcoal instead of pure white/black | Reduces eye strain for a tool meant to be used for hours at a stretch — a real ergonomic reason, not just a stylistic one |

---

This document, combined with the earlier architecture, repository, and API specifications, should give a frontend engineer everything needed to implement Rune's interface without making an independent visual decision — every component, color, spacing value, and motion timing above is intended as the literal source of truth.
