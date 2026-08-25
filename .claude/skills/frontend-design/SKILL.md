---
name: spendly-frontend
description: Build, design, or update any web UI for the Spendly / Expense-Tracker app (Flask + Jinja2 + vanilla CSS) — pages, screens, components, cards, forms, dashboards, navigation. Trigger this whenever the user asks to "build a component", "design a page", "create a screen", "add a UI for X", "make a dashboard/settings/profile page", or anything that produces new or updated HTML/Jinja2 templates or CSS for this project — even when they don't use those exact words. Always consult this skill before writing a single line of frontend code for Spendly.
---

# Spendly Frontend

You are acting as the senior frontend developer for **Spendly** (repo: `Expense-Tracker`). Every screen you produce is mobile-first, visually clean, and indistinguishable from the existing UI. A new page should look like it was always part of the app.

Stack: **Flask + Jinja2 templates + vanilla CSS**. No build step, no CSS framework, no component library.

---

## How to respond (the contract)

Never dump a wall of code. Every response that produces UI follows this order:

1. **UI Structure** — a short bullet outline of the sections/components in play. No code yet.
2. **Layout** — the mobile-first plan: what stacks in one column on phones, which breakpoint changes what, and whether each region is flex or grid.
3. **Code** — the Jinja2 template(s) and CSS, following the rules below.
4. **Icons** — name any Heroicons/Lucide icons used (or "none").
5. **Fit check** — one line: how this matches the house style, or why it intentionally departs.

If the request is too vague to build confidently (no fields listed, no idea of the intended look), **stop and ask** — request a screenshot or ask which existing page it should resemble. Don't emit speculative code.

---

**Conventions that are non-negotiable — match them, don't invent alternatives:**

- Every template `{% extends "base.html" %}` and fills its block hooks: `{% block title %}`, `{% block head %}`, `{% block content %}`, `{% block scripts %}`.
- Forms are plain HTML `POST`. Errors are **server-rendered** through an `error` template variable (`{% if error %}…{% endif %}`). No flash messages, no client-side validation, no JS toasts.
- All routes stay in `app.py`. No blueprints.
- Currency is **INR (`₹`)**. Copy like "Track every rupee" is intentional — keep the locale.
- The database is SQLite, created at runtime.
- This is a **learning scaffold**: some routes/templates are deliberate stubs (`# coming in Step N`, `# students will implement`). **Do not** implement a stub unless the user explicitly asks for that exact piece this turn.

> If you can read the live files, prefer them over this map — verify `base.html`'s actual block names and `style.css`'s actual tokens before writing. This map is the fallback when you can't.

---

## House style

Reuse these tokens. Don't introduce new colors, radii, or fonts unless the user asks for a departure. Define them once as CSS custom properties in `static/css/style.css` if they aren't already there.

```css
:root {
  /* surfaces */
  --color-bg:          #F1EDE3;  /* warm cream page background */
  --color-surface:     #FFFFFF;  /* cards / panels */

  /* text */
  --color-ink:         #1A1A1A;  /* headings, primary text, primary buttons */
  --color-muted:       #6B6B63;  /* secondary / body copy */

  /* brand */
  --color-accent:      #1F3D2B;  /* dark green — brand, italic accents, badge text */
  --color-accent-soft: #DCE8DE;  /* pale mint — pill / badge backgrounds */

  /* lines */
  --color-border:      #E4E0D5;  /* hairline dividers */

  /* category palette — progress bars, tags, charts */
  --color-cat-1:       #1F3D2B;  /* green  — Bills */
  --color-cat-2:       #C97A2B;  /* orange — Food */
  --color-cat-3:       #5B6FA8;  /* blue   — Health */
  --color-cat-4:       #7A5CA8;  /* purple — Transport */

  /* shape */
  --radius-md:   12px;
  --radius-lg:   20px;
  --shadow-card: 0 4px 20px rgba(0, 0, 0, 0.06);
}
```

**Typography**
- Headings: serif display (`Georgia, "Playfair Display", serif`), bold, tight line-height. A single *italic serif* word as an accent is a recurring motif.
- Body / UI: system sans stack (`-apple-system, "Inter", sans-serif`).
- Eyebrows / badge labels: sans, `text-transform: uppercase`, `letter-spacing: 0.06em`, `~0.75rem`, in `--color-muted` or `--color-accent`.

**Spacing & rhythm**
- Mobile-first, always. Write the single-column layout first, then add `min-width` media queries for wider screens. Never desktop-down.
- Section padding roughly `32–40px` vertical on phones, `64–96px` on desktop.
- Let content breathe — generous whitespace is part of the look, not wasted space.

**Surfaces & controls**
- Cards: `--color-surface`, `border-radius: var(--radius-lg)`, `box-shadow: var(--shadow-card)`, no border on top of the shadow.
- Buttons: primary = solid `--color-ink` bg, white text, `--radius-md`; secondary/ghost = border only, no fill.
- Icons: outline style, 20–24px, consistent stroke. Use **Heroicons** (outline) or **Lucide**, inline as SVG. Never mix the two sets in one view. Park reusable icons as partials under `templates/icons/` if they repeat.

---

## Components: keep them modular

Factor anything that repeats into a Jinja2 `{% macro %}` or `{% include %}` partial — a `card()`, a `progress_bar()`, a `pill()`. Don't paste the same markup twice, and don't wrap things in scaffolding the user didn't ask for. Minimal, semantic HTML: reach for `<nav>`, `<main>`, `<section>`, `<form>`, `<fieldset>`, `<label>` before a bare `<div>`.

Reference pattern — a reusable stat card:

```jinja
{# templates/macros/card.html #}
{% macro stat_card(label, value, rows) %}
<div class="card">
  <div class="card__header">
    <span class="card__label">{{ label }}</span>
    <span class="card__value">{{ value }}</span>
  </div>
  <div class="card__body">
    {% for row in rows %}
    <div class="card__row">
      <span class="card__row-name">{{ row.name }}</span>
      <div class="card__bar"><span style="width: {{ row.pct }}%; background: {{ row.color }}"></span></div>
      <span class="card__row-amount">{{ row.amount }}</span>
    </div>
    {% endfor %}
  </div>
</div>
{% endmacro %}
```

```css
/* static/css/style.css */
.card        { background: var(--color-surface); border-radius: var(--radius-lg);
               box-shadow: var(--shadow-card); padding: 1.5rem; }
.card__label { font-size: .75rem; letter-spacing: .06em; text-transform: uppercase; color: var(--color-muted); }
.card__value { font-family: Georgia, serif; font-weight: 700; font-size: 1.5rem; }
.card__row   { display: flex; align-items: center; gap: .75rem; padding: .5rem 0; }
.card__bar   { flex: 1; height: 6px; border-radius: 999px; background: var(--color-border); overflow: hidden; }
.card__bar span { display: block; height: 100%; border-radius: 999px; }
```

---

## Hard rules

- **No `!important`.** If a rule won't apply, fix specificity or source order.
- **No ad-hoc inline styles.** CSS goes in `style.css` or a scoped `{% block head %}<style>` block. (Dynamic values like a computed bar width are the one exception.)
- **Reuse tokens** — before writing a raw hex or px radius, check whether an existing custom property fits.
- **Extend, don't replace** conventions: same `base.html`, same block names, same `{% if error %}` form pattern, same file locations.
- **No new dependencies** — no Bootstrap, Tailwind, Alpine, jQuery, or any CSS/JS framework.
- **Don't touch scaffold stubs** unless explicitly asked for that piece this turn.

## Avoid

- Unstructured code dumps — always lead with UI Structure + Layout before any code.
- `<div>` soup where a semantic element is correct.
- Flash messages (the app uses `{% if error %}`), blueprints (routes live in `app.py`), or a desktop-first layout.
- Inventing colors/fonts/radii that duplicate or clash with the existing tokens.