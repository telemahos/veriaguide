"""Build a trimmed Font Awesome (only the icons referenced in the code) for the v2 theme.

Scans templates, JS and Python for `fa-<name>` tokens, keeps those icon rules from the vendored
Font Awesome Free 6.4 CSS, and subsets the three woff2 fonts to the used glyphs.
Run after adding a new icon:  python scripts/build_fa_lite.py   (needs: pip install fonttools brotli)
Output: static/vendor/fontawesome-lite/  (committed; Font Awesome Free: icons CC BY 4.0, fonts OFL 1.1)
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "static" / "vendor" / "fontawesome"
OUT = ROOT / "static" / "vendor" / "fontawesome-lite"
FONTS = ("fa-brands-400", "fa-regular-400", "fa-solid-900")


def used_tokens() -> set[str]:
    tokens: set[str] = set()
    files = [p for pat in ("templates/**/*.html", "static/js/**/*.js", "app/**/*.py")
             for p in ROOT.glob(pat) if "admin" not in p.parts]
    for path in files:
        tokens |= set(re.findall(r"\bfa-[a-z0-9-]+", path.read_text(errors="ignore")))
    return tokens


def main() -> None:
    css = (SRC / "css" / "all.min.css").read_text()
    used = used_tokens()
    rule = re.compile(r'((?:\.fa-[a-z0-9-]+:before,?)+)\{content:"\\([0-9a-f]+)"\}')
    codepoints: set[int] = set()

    def keep(match: re.Match) -> str:
        names = re.findall(r"\.(fa-[a-z0-9-]+):before", match.group(1))
        wanted = [n for n in names if n in used]
        if not wanted:
            return ""
        codepoints.add(int(match.group(2), 16))
        selectors = ",".join(f".{n}:before" for n in wanted)
        return f'{selectors}{{content:"\\{match.group(2)}"}}'

    css = rule.sub(keep, css)
    css = re.sub(r"@font-face\{font-family:\"Font Awesome 5[^}]*\}", "", css)          # FA5 aliases
    css = re.sub(r"@font-face\{font-family:\"FontAwesome\"[^}]*\}", "", css)            # v4 compat
    css = css.replace("../webfonts/", "fonts/")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "fonts").mkdir(exist_ok=True)
    (OUT / "all.min.css").write_text(css)

    unicodes = ",".join(f"U+{c:04X}" for c in sorted(codepoints))
    for name in FONTS:
        target = OUT / "fonts" / f"{name}.woff2"
        result = subprocess.run(
            [sys.executable, "-m", "fontTools.subset", str(SRC / "webfonts" / f"{name}.woff2"),
             f"--unicodes={unicodes}", "--flavor=woff2", f"--output-file={target}",
             "--layout-features=*", "--no-hinting"],
            capture_output=True, text=True,
        )
        if result.returncode != 0:  # fa-regular-400 cannot be parsed by fontTools; it is small, copy as is
            print(f"{name}: subset failed, copying original")
            shutil.copyfile(SRC / "webfonts" / f"{name}.woff2", target)
    sizes = {p.name: p.stat().st_size for p in [OUT / "all.min.css", *(OUT / "fonts").glob("*.woff2")]}
    print(f"{len(codepoints)} icons kept;", sizes)


if __name__ == "__main__":
    main()
