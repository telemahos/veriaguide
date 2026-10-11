"""Map the hard-coded colours of the classic stylesheet onto the Zeitalter theme tokens.

The classic `static/css/style.css` has literal light surfaces (white, #f8fafc, ...) and grey text. In the dark scheme they
would show light panels with light text. This script reads style.css and emits `static/css/v3/legacy-map.css`: for every
rule that uses literal colours AND whose classes occur in the templates/JS, a `.theme-zeitalter <selector>` rule that
re-maps ONLY the colour properties (the !important ones go into the `zt-force` layer, see the v3 layout) to var(--surface), var(--text), var(--text-muted), var(--border), ... so one rule set
works for dark and light. Re-run after changing style.css or adding templates:  python scripts/build_zeitalter_legacy.py
"""
import colorsys
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "static" / "css" / "style.css"
OUT = ROOT / "static" / "css" / "v3" / "legacy-map.css"

NAMED = {"white": (255, 255, 255), "black": (0, 0, 0), "transparent": None}
HEX = re.compile(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b")
RGB = re.compile(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+)\s*)?\)")


def parse_color(token: str):
    token = token.strip().lower()
    if token in NAMED:
        return NAMED[token] and (*NAMED[token], 1.0)
    m = HEX.fullmatch(token)
    if m:
        h = m.group(1)
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 1.0)
    m = RGB.fullmatch(token)
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)), float(m.group(4) or 1))
    return None


def lum(rgb) -> float:
    def f(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb[:3]
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def saturation(rgb) -> float:
    r, g, b = (c / 255 for c in rgb[:3])
    return colorsys.rgb_to_hsv(r, g, b)[1]


def map_text(rgb):
    L = lum(rgb)
    if rgb[3] < 1 or L >= 0.6:
        return None                      # light/translucent text: designed for dark panels, keep
    if saturation(rgb) > 0.55 and L > 0.12:
        return None                      # accents (orange, red, green) keep their meaning
    return "var(--text)" if L < 0.1 else "var(--text-muted)"


def map_bg(rgb):
    L = lum(rgb)
    if rgb[3] < 1:
        return None
    if L >= 0.97:
        return "var(--surface)"
    if L >= 0.78:
        return "var(--surface-alt)"
    if L < 0.14 and saturation(rgb) > 0.2:
        return "var(--zt-panel)"         # navy panels become a neutral dark panel in both schemes
    return None


def map_border(rgb):
    return "var(--border)" if rgb[3] == 1 and lum(rgb) >= 0.55 else None


VAR_BG = {"--primary-color": "var(--zt-panel)", "--primary-dark": "var(--zt-panel)", "--dark-color": "var(--zt-panel)",
          "--light-color": "var(--surface-alt)", "--light-blue": "var(--surface-alt)", "--accent-warm-light": "var(--surface-alt)"}
VAR_TEXT = {"--primary-color": "var(--link)", "--primary-dark": "var(--text)", "--dark-color": "var(--text)",
            "--secondary-color": "var(--text-muted)", "--accent-warm-dark": "var(--link)"}
VAR_BORDER = {"--light-blue": "var(--border)", "--light-color": "var(--border)"}


def map_var(prop: str, value: str):
    m = re.fullmatch(r"var\((--[\w-]+)\)", value)
    if not m:
        return None
    name = m.group(1)
    if prop in ("background", "background-color"):
        return VAR_BG.get(name)
    if prop == "color":
        return VAR_TEXT.get(name)
    if prop.startswith("border") and prop.endswith("color"):
        return VAR_BORDER.get(name)
    return None


def transform(prop: str, value: str):
    """Return the replacement value for a colour property, or None to drop the declaration."""
    prop = prop.strip().lower()
    value = value.strip()
    imp = " !important" if value.endswith("!important") else ""
    value = value.replace("!important", "").strip()
    if "gradient" in value or "url(" in value:
        return None
    if value.startswith("var("):
        r = map_var(prop, value)
        return f"{prop}: {r}{imp}" if r else None
    if "var(" in value:
        return None
    if prop == "color":
        c = parse_color(value)
        r = c and map_text(c)
    elif prop in ("background", "background-color"):
        c = parse_color(value)
        r = c and map_bg(c)
    elif prop in ("border-color", "border-top-color", "border-bottom-color", "border-left-color", "border-right-color"):
        c = parse_color(value)
        r = c and map_border(c)
    elif prop in ("border", "border-top", "border-bottom", "border-left", "border-right"):
        m = re.match(r"^(\S+\s+\S+)\s+(\S.*)$", value)
        c = m and parse_color(m.group(2))
        r = c and map_border(c)
        if r:
            return f"{prop}: {m.group(1)} {r}{imp}"
        return None
    else:
        return None
    return f"{prop}: {r}{imp}" if r else None


def used_classes() -> set[str]:
    tokens: set[str] = set()
    files = [p for pat in ("templates/**/*.html", "static/js/**/*.js", "app/**/*.py") for p in ROOT.glob(pat)
             if "admin" not in p.parts]
    for path in files:
        tokens |= set(re.findall(r"[A-Za-z_][\w-]*", path.read_text(errors="ignore")))
    return tokens


def split_rules(css: str):
    """Yield (selector, body, media) for flat rules, descending one level into @media."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    i, n = 0, len(css)
    while i < n:
        j = css.find("{", i)
        if j < 0:
            break
        head = css[i:j].strip()
        depth, k = 1, j + 1
        while k < n and depth:
            depth += {"{": 1, "}": -1}.get(css[k], 0)
            k += 1
        body = css[j + 1:k - 1]
        if head.startswith("@media"):
            for sel, b, _ in split_rules(body):
                yield sel, b, head
        elif head.startswith("@"):
            pass                         # @font-face, @keyframes, ...
        else:
            yield head, body, None
        i = k


def main() -> None:
    used = used_classes()
    out_plain, out_media, out_force = [], {}, []
    kept = 0
    for selector, body, media in split_rules(SRC.read_text()):
        decls = []
        for d in re.split(r";(?![^(]*\))", body):
            if ":" not in d:
                continue
            prop, value = d.split(":", 1)
            new = transform(prop, value)
            if new:
                decls.append(new)
        if not decls:
            continue
        sels = []
        for sel in (s.strip() for s in selector.split(",")):
            if not sel or re.match(r"^(html|body|:root|\*)\b", sel) or ":root" in sel:
                continue
            classes = re.findall(r"\.([A-Za-z_][\w-]*)", sel)
            if classes and not all(c in used for c in classes):
                continue
            if not classes:
                continue                 # bare element selectors are handled by the zero-specificity reset
            sels.append(".theme-zeitalter " + sel)
        if not sels:
            continue
        if any(d.startswith(("background:", "background-color:")) and "var(--zt-panel)" in d for d in decls):
            decls.append("color: #F6F0E4")   # dark panels always carry light text (descendants inherit it)
        rule = ",\n".join(sels) + " { " + "; ".join(decls) + "; }"
        kept += 1
        if "!important" in rule:
            out_force.append(rule)       # layered !important of an EARLIER layer wins: zt-force is declared before legacy
        elif media:
            out_media.setdefault(media, []).append(rule)
        else:
            out_plain.append(rule)
    header = ("/* GENERATED by scripts/build_zeitalter_legacy.py from static/css/style.css - do not edit.\n"
              "   Re-maps the classic stylesheet's literal colours to the Zeitalter tokens (dark + light). */\n")
    parts = [header, "\n".join(out_plain)]
    for media, rules in out_media.items():
        parts.append(f"\n{media} {{\n" + "\n".join(rules) + "\n}")
    if out_force:
        parts.append("\n@layer zt-force {\n" + "\n".join(out_force) + "\n}")
    OUT.write_text("\n".join(parts) + "\n")
    print(f"{kept} rules -> {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
