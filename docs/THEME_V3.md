# VeriaGuide Theme v3 "Zeitalter"

Third theme next to `classic` and `new` (v2). Editorial, photo-led, dark by default with a light variant.

## Switching
- Theme: `?theme=zeitalter|new|classic` (cookie `vg_theme`), default from `DEFAULT_THEME` in the server `.env`.
  Footer link row "Design: Zeitalter · Modern · Classic".
- Dark/light: the sun/moon button in the header. Stored in `localStorage` (`vg_scheme`), applied by an inline head
  script before first paint (no flash). Default: dark.

## How it is built
- Template chain for `zeitalter`: `templates/v3/<name>` → `templates/v2/<name>` → classic (`app/theme.py`).
  v3 has its own layout, header, footer, home, hub (adds a category cover photo) and error pages; detail, search,
  AI Guide, forms reuse v2/classic markup restyled by `static/css/v3/zeitalter.css`.
- `zeitalter.css` loads after `static/css/v2/all.css` and re-maps the v2 tokens for dark (`:root`) and light
  (`:root[data-scheme="light"]`), so every v2 component follows the scheme.
- The classic `style.css` is imported into a lower cascade layer (`@import … layer(legacy)` in the v3 layout): it still
  styles classic markup, but any v2/v3 rule wins. A zero-specificity reset resets its grey text colours.
- Fonts: EB Garamond (display, roman + italic) and Commissioner (body), self-hosted, latin + greek subsets.

## Motion (`static/js/v3/motion.js`)
- Hero: slow zoom on the photo, headline rises line by line, lead and button fade in.
- Scroll: `[data-reveal]` (fade/rise), `[data-reveal="image"]` (image uncovers and settles), staggered siblings.
  Cards, detail sections, sidebar cards and page heads below the fold are tagged automatically.
- Parallax: `[data-parallax="0.1"]`; overlay header turns solid after 40 px.
- `prefers-reduced-motion`: no motion at all, content visible immediately. If the script fails, a CSS failsafe shows
  everything after 2.5 s.

## Photos
Wikimedia Commons, CC BY-SA 3.0/4.0, credited in the footer and in the hero caption. Sources and authors:
`static/img/v3/credits.json`. Replace with own photos by overwriting `static/img/v3/<name>-{800,1200}.webp`.

## Tests
`tests/test_theme.py` (v3 section): all languages, inner pages, hub cover, 404, cookie isolation from the other themes,
assets. A puppeteer run (local, real WP snapshot) checked: default dark, toggle + persistence, reveal, parallax,
overlay header, mobile menu, no horizontal scroll, reduced motion, no JS errors.
