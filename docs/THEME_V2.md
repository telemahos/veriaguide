# VeriaGuide Theme v2 ("new" design)

The classic design is untouched. The new design is opt-in and lives next to it.

## Switching
- `?theme=new` / `?theme=classic` sets the `vg_theme` cookie (1 year). Those URLs send `X-Robots-Tag: noindex`.
- Default for visitors without a cookie: `DEFAULT_THEME` (`classic` or `new`, default `classic`).
- Footer link toggles between the two (i18n: EN/EL/DE).
- Code: `frontend/app/theme.py` (middleware + Jinja environment). For the new theme, `name` resolves to
  `templates/v2/<name>` when it exists, otherwise the classic template. `{% extends "classic:..." %}` bypasses
  the lookup (used to extend a classic template from its v2 override).

## Design brief
**Mood:** warm evening on a Byzantine square. Sand, olive, terracotta, Aegean blue. Airy, photo-led, no gradients as decoration.

| Token | Hex | Use |
|---|---|---|
| sand-50 / 100 / 200 / 300 | `#fbf7f0` `#f3ebdd` `#e9dfcb` `#dccfb6` | page, sections, tags, borders |
| ink-900 / 700 / 600 | `#241f19` `#3d362d` `#5b5247` | text, secondary text |
| olive-600 / 100 | `#566a33` `#e6ecd8` | nature tags, distance |
| terracotta-600 / 700 / 100 | `#a9472a` `#8a3a22` `#f6e1d8` | CTA, eyebrow |
| blue-800 / 700 / 600 / 100 | `#123c70` `#194c8c` `#1f5aa6` `#dde8f5` | links, header, focus |

All text pairs used in the UI are >= 4.5:1 (checked: body 15.3, muted 7.2, CTA 5.8, eyebrow 7.3, footer 9.0+).

**Type:** Literata (display, serif) + Inter (body), both variable, self-hosted woff2, latin + greek subsets,
`font-display: swap`. Scale (fluid, `clamp`): 12 / 14 / 16 / 18 / 20-24 / 24-30 / 30-40 / 36-60 px.
**Space:** 4px base, `--space-1..9`. **Radii:** 8 / 14 / 24 / pill. **Motion:** 150-250ms, off under `prefers-reduced-motion`.

**Files:** `static/css/v2/` `tokens.css` (all tokens + fonts), `base.css` (reset, type, primitives, buttons, skeleton),
`shell.css` (header, nav, footer, cookie banner), `components.css` (hero, search, tiles, cards, hub, chips, pagination, empty state),
`detail.css`, `ai-guide.css`, `error.css`. JS: `static/js/v2/` `shell.js`, `search.js`, `detail.js`.

**Components:** skip link, header + mobile menu + language switch, hero + search combobox, theme tiles, listing card,
breadcrumbs, hub filters, chips, pagination, skeleton, empty state, detail head + sticky section nav, AI Guide skin, error pages.

## Templates
| Page | v2 template | Notes |
|---|---|---|
| Shell | `v2/base/layout.html` | extends classic layout (head/SEO/consent unchanged), replaces header/main/footer |
| Home | `v2/base/index.html` | static LCP hero, no slider |
| Category hub | `v2/base/category-list.html` | classic scripts block inherited |
| Detail (all 10) | `v2/base/partials/detail_title|trust|sidebar_actions.html`, `v2/base/macros/detail_sections.html` | classic detail templates reused; restyled via `detail.css` |
| Search | `v2/search/results.html` | classic scripts inherited |
| AI Guide (all steps) | `v2/ai_guide/_base.html` + `ai-guide.css` | variable remap only |
| 404 / 429 / 500 / generic | `v2/errors/*` | standalone, no Bootstrap |

## Before / after
- Bootstrap navbar + dropdowns -> vanilla disclosure nav (`aria-expanded`, Escape, outside click).
- Blue/gold system-font look -> sand/olive/terracotta/blue with Literata + Inter.
- Auto-rotating hero slider -> single LCP image, search first.
- Directory rows -> 3:2 cards with skeleton, whole-card link, 44px favorite button.
- Bootstrap grid detail pages -> same markup, new type, cards, sticky section nav and breadcrumb.
- Fixed along the way (new theme only): escaped `&amp;` in "Save & Share", missing spaces in the trust box, German autocomplete links missing `/de`.

## Known limits / next steps
- Bootstrap CSS/JS, FontAwesome and `style.css` still load in the new theme: unmigrated pages (map, favorites, contact, submit,
  contribute, about, tours/hubs using `map-listings`) and the gallery modal/carousel depend on them. Removing them is the main remaining
  performance win.
- Pages without a v2 template render classic content inside the v2 shell.
- The hub filter box still uses the classic autocomplete script (restyled).

## Checklist (release gate)
- [ ] `cd frontend && pytest` green (includes `tests/test_theme.py`)
- [ ] EN / EL / DE: home, hub, detail, search (with and without results), 404, AI Guide start
- [ ] hreflang, canonical, JSON-LD, OG image present in the head of the new theme (shared layout)
- [ ] `/el/` and `/de/` links keep their prefix; trailing-slash redirects unchanged
- [ ] Cookie banner appears; analytics only after "Accept all"
- [ ] Keyboard: skip link, menu, submenus (Esc), search combobox (arrows/Enter/Esc), filters, gallery
- [ ] `prefers-reduced-motion`: no shimmer, no transforms
- [ ] 360px, 768px, 1280px: no horizontal scroll, tap targets >= 44px
- [ ] Lighthouse mobile on home + one detail page (LCP, CLS, a11y)

## Visual QA list (screenshots)
1. Home, 1280px EN: hero, search, tiles, first listing row
2. Home, 390px DE: hero text wrapping, search button, chips, cookie banner
3. Hub `/el/religious-sites`: Greek headline glyphs, filters, cards, pagination
4. Detail (church) 1280px: breadcrumb, gallery, sticky section nav active state, sidebar map
5. Detail 390px: order of content/sidebar, gallery thumbs scroll
6. Search with results and with zero results (`/search?q=zzzz`)
7. 404 (EN and DE) with search combobox open and suggestions loading
8. Header: mobile menu open, desktop submenu open, focus rings visible
