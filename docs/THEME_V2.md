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

## Bootstrap removal
The new theme no longer loads Bootstrap CSS/JS (about 230 KB). Shared markup that still uses Bootstrap classes keeps working through
`static/css/v2/compat.css` (grid, spacing/flex/text utilities, buttons, forms, cards, alerts, list-group, accordion, modal, carousel,
rebuilt on v2 tokens) and `static/js/v2/ui.js` (modal, collapse/accordion, carousel via the same `data-bs-*` attributes).
The classic theme is unchanged and still loads Bootstrap.

## Build step
`python frontend/scripts/build_v2_css.py` concatenates the v2 CSS into `static/css/v2/all.css` (one render-blocking request).
Run it after editing any v2 CSS source file and commit the result; `tests/test_theme.py` fails if it is stale.
Bump the `?v=` in `templates/v2/base/layout.html` when shipping a change.

## Measured (Lighthouse 12, mobile preset, throttled)
Local runs use the app on localhost fed by a one-time snapshot of the public WP REST data (no compression, no CDN, images from the
live site), so **they are only comparable with each other, not with production**. The production row is the live classic site.

| Page | Run | Perf | A11y | LCP | FCP | Transfer |
|---|---|---|---|---|---|---|
| Home | local classic | 66 | 95 | 7.6 s | 4.2 s | 1552 KB |
| Home | local new | 78 | 100 | 5.0 s | 2.3 s | 905 KB |
| Home | **production classic** | 99 | 95 | 1.6 s | 1.2 s | 1007 KB |
| Detail (church) | local classic | 69 | 95 | 16.5 s | 3.1 s | 6330 KB |
| Detail (church) | local new | 68 | 100 | 10.0 s | 3.3 s | 4966 KB |
| Detail (church) | **production classic** | 72 | 95 | 11.9 s | 1.8 s | 5738 KB |

Reading: the new theme transfers about 40% fewer bytes on home and scores higher than classic under identical local conditions, but
production classic home already scores 99, so **do not expect a score gain on production home; measure the new theme on a staging
deploy before switching the default.** Detail pages are image-bound (a single church page loads 5-6 MB because WordPress serves
PNG screenshots of 0.6-1.9 MB each): converting uploads to WebP/JPEG is the largest remaining win and is WP/content-side.
Lighthouse scores vary by a few points between runs.

## Icons
`scripts/build_fa_lite.py` builds `static/vendor/fontawesome-lite/` (only the icons referenced in templates/JS/Python; solid and brands
fonts subset to those glyphs): 100 KB CSS + 283 KB fonts -> 18 KB CSS + 35 KB fonts. Run it after introducing a new `fa-*` icon
(a test fails if a used icon is missing). Icons that only appear inside WordPress-authored content would not be detected.
The classic theme still loads the full Font Awesome. Trimming `style.css` with PurgeCSS was tried and dropped: only ~3 KB gzip saved
because the classic-extended pages still use most of it.

## Known limits / next steps
- Pages without a v2 template (map, favorites, contact, submit, contribute) render classic markup inside the v2 shell, restyled via the
  compat layer. They look consistent but are not redesigned. `about` has a v2 copy only to fix an escaped `&amp;`.
- The classic `style.css` (about 90 KB) still loads; trimming it saves little (see Icons).
- The hub filter box still uses the classic autocomplete script (restyled).
- SEO score on localhost is 61 for both themes (non-production environment); production classic scores 92.

## Checklist (release gate)
- [ ] `cd frontend && pytest` green (includes `tests/test_theme.py`)
- [ ] EN / EL / DE: home, hub, detail, search (with and without results), 404, AI Guide start
- [ ] hreflang, canonical, JSON-LD, OG image present in the head of the new theme (shared layout)
- [ ] `/el/` and `/de/` links keep their prefix; trailing-slash redirects unchanged
- [ ] Cookie banner appears; analytics only after "Accept all"
- [ ] Keyboard: skip link, menu, submenus (Esc), search combobox (arrows/Enter/Esc), filters, gallery
- [ ] `prefers-reduced-motion`: no shimmer, no transforms
- [ ] 360px, 768px, 1280px: no horizontal scroll, tap targets >= 44px
- [ ] Lighthouse mobile on home + one detail page on a staging deploy of the new theme (LCP, CLS, a11y)
- [ ] Real-browser smoke test (menu, search combobox, section nav, gallery modal, favorites) - an automated puppeteer run passed 25/25 locally

## Visual QA list (screenshots)
1. Home, 1280px EN: hero, search, tiles, first listing row
2. Home, 390px DE: hero text wrapping, search button, chips, cookie banner
3. Hub `/el/religious-sites`: Greek headline glyphs, filters, cards, pagination
4. Detail (church) 1280px: breadcrumb, gallery, sticky section nav active state, sidebar map
5. Detail 390px: order of content/sidebar, gallery thumbs scroll
6. Search with results and with zero results (`/search?q=zzzz`)
7. 404 (EN and DE) with search combobox open and suggestions loading
8. Header: mobile menu open, desktop submenu open, focus rings visible
