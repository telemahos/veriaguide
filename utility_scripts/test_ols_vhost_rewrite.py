"""Assert OLS vhost rewrite order: security block, then auth, then proxy."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from ols_vhost_rewrite import AUTH_PASSTHROUGH, SECURITY_BLOCK, apply_rewrite

SCRIPT_DIR = Path(__file__).resolve().parent
FIXTURE = SCRIPT_DIR / "fixtures" / "vhost.conf.pre-rewrite"
FIX_SH = SCRIPT_DIR / "fix-ols-vhost-proxy.sh"

BEGIN = "# BEGIN security-hardening-20261007-rest"
END = "# END security-hardening-20261007-rest"


def _rewrite_section(text: str) -> str:
    match = re.search(r"rules <<<END_rules\n(.*?)\nEND_rules", text, flags=re.S)
    assert match, "rewrite rules missing"
    return match.group(1)


def test_block_order_after_rewrite_engine_on():
    out = apply_rewrite(FIXTURE.read_text())
    rules = _rewrite_section(out)
    engine = rules.index("RewriteEngine On")
    sec = rules.index(BEGIN)
    sec_end = rules.index(END)
    auth = rules.index("E=HTTP_AUTHORIZATION:%{HTTP:Authorization}")
    proxy = rules.index("http://127.0.0.1:8000")
    wp_keep = rules.index("^/wp-admin")

    assert engine < sec < sec_end < auth < wp_keep < proxy
    between = rules[rules.index("RewriteEngine On") + len("RewriteEngine On") : sec]
    assert between.strip() == ""
    assert SECURITY_BLOCK in rules
    assert AUTH_PASSTHROUGH in rules
    assert rules.count(BEGIN) == 1
    assert "acme-challenge" in rules
    assert r"^www\.veriaguide\.gr$" in rules


def test_apply_is_idempotent():
    once = apply_rewrite(FIXTURE.read_text())
    twice = apply_rewrite(once)
    assert once == twice
    assert once.count(BEGIN) == 1
    assert once.count("E=HTTP_AUTHORIZATION:%{HTTP:Authorization}") == 1
    assert once.count("extprocessor 127.0.0.1:8000") == 1
    assert once.count("RewriteEngine On") == 1


def test_shell_script_against_fixture(tmp_path: Path):
    vhost = tmp_path / "vhost.conf"
    vhost.write_text(FIXTURE.read_text())
    env = os.environ.copy()
    env["OLS_VHOST"] = str(vhost)
    env["OLS_SKIP_VERIFY"] = "1"
    subprocess.run(
        ["bash", str(FIX_SH)],
        check=True,
        env=env,
        cwd=str(SCRIPT_DIR),
    )
    text = vhost.read_text()
    rules = _rewrite_section(text)
    engine = rules.index("RewriteEngine On")
    assert rules.index(BEGIN) > engine
    assert rules.index("E=HTTP_AUTHORIZATION:%{HTTP:Authorization}") > rules.index(END)
    assert rules.index("http://127.0.0.1:8000") > rules.index(
        "E=HTTP_AUTHORIZATION:%{HTTP:Authorization}"
    )

    subprocess.run(
        ["bash", str(FIX_SH)],
        check=True,
        env=env,
        cwd=str(SCRIPT_DIR),
    )
    again = vhost.read_text()
    assert again.count(BEGIN) == 1
    assert again.count("rewrite  {") == 1
