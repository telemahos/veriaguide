#!/usr/bin/env bash
# Smoke test for a running VeriaGuide frontend (classic + new theme). Read-only GETs, ~40 requests.
# Usage: scripts/smoke_live.sh [BASE_URL]      default: https://veriaguide.gr
BASE="${1:-https://veriaguide.gr}"
fail=0
check() { # name, condition(0=ok)
  if [ "$2" -eq 0 ]; then echo "PASS  $1"; else echo "FAIL  $1"; fail=1; fi
}
get() { curl -s -m 30 -o /tmp/vg_body -D /tmp/vg_head -w "%{http_code}" "$@"; }

for path in "/" "/el/" "/de/" "/religious-sites" "/museums" "/search?q=church" "/contact" "/about" "/map" "/sitemap.xml" "/robots.txt"; do
  code=$(get "$BASE$path"); check "classic $path -> $code" $([ "$code" = "200" ] && echo 0 || echo 1)
done

# classic must not contain v2 assets
get "$BASE/" >/dev/null
check "classic home has no theme-new/v2 assets" $(grep -q "theme-new\|/static/css/v2/" /tmp/vg_body && echo 1 || echo 0)
check "classic home still loads bootstrap" $(grep -q "bootstrap" /tmp/vg_body && echo 0 || echo 1)

for path in "/" "/el/" "/de/" "/religious-sites" "/museums" "/search?q=church" "/contact" "/about" "/map"; do
  sep="?"; case "$path" in *\?*) sep="&";; esac
  code=$(get "$BASE$path${sep}theme=new")
  check "new $path -> $code" $([ "$code" = "200" ] && echo 0 || echo 1)
  check "  new $path: theme-new + v2 css" $(grep -q 'class="theme-new"' /tmp/vg_body && grep -q "/static/css/v2/all.css" /tmp/vg_body && echo 0 || echo 1)
  check "  new $path: no bootstrap" $(grep -qi "bootstrap" /tmp/vg_body && echo 1 || echo 0)
  check "  new $path: noindex header + cookie" $(grep -qi "x-robots-tag: noindex" /tmp/vg_head && grep -qi "set-cookie: vg_theme=new" /tmp/vg_head && echo 0 || echo 1)
  check "  new $path: canonical present" $(grep -q 'rel="canonical"' /tmp/vg_body && echo 0 || echo 1)
done
get "$BASE/?theme=new" >/dev/null
check "new home: hreflang en/el/de" $([ "$(grep -c 'hreflang=' /tmp/vg_body)" -ge 3 ] && echo 0 || echo 1)
check "new home: canonical has no ?theme" $(grep 'rel="canonical"' /tmp/vg_body | grep -q "theme=" && echo 1 || echo 0)

code=$(get "$BASE/definitely-not-a-page-xyz"); check "classic 404 -> $code" $([ "$code" = "404" ] && echo 0 || echo 1)
code=$(get "$BASE/definitely-not-a-page-xyz?theme=new"); check "new 404 -> $code" $([ "$code" = "404" ] && echo 0 || echo 1)
check "new 404 is v2 error page" $(grep -q "vg-error" /tmp/vg_body && echo 0 || echo 1)

# static assets
for a in /static/css/v2/all.css /static/js/v2/ui.js /static/js/v2/shell.js /static/js/v2/search.js /static/js/v2/detail.js \
         /static/fonts/inter-latin-wght-normal.woff2 /static/fonts/literata-latin-wght-normal.woff2 \
         /static/vendor/fontawesome-lite/all.min.css /static/vendor/fontawesome-lite/fonts/fa-solid-900.woff2; do
  code=$(get -I "$BASE$a"); check "asset $a -> $code" $([ "$code" = "200" ] && echo 0 || echo 1)
done

# No visitor impact: default (no cookie) must be classic unless DEFAULT_THEME=new is set
get "$BASE/" >/dev/null
echo "INFO  default theme without cookie: $(grep -q 'class="theme-new"' /tmp/vg_body && echo NEW || echo classic)"
exit $fail
