#!/usr/bin/env python3
"""Store Greek title, excerpt and content on existing WordPress listings.

One-time translator. UI strings are translated in the app; this script only
fills title_el, excerpt_el and content_el so editors can correct them later.
"""
import argparse
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = "https://veriaguide.gr"
COLLECTIONS = (
    "religious_sites",
    "museums",
    "archaeological_sites",
    "hiking_trails",
    "tours",
    "hidden_gems",
    "ski_resorts",
    "accommodations",
    "restaurants",
    "cafes",
)


def load_local_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key in ("OPENROUTER_API_KEY", "OPENROUTER_MODEL"):
            os.environ.setdefault(key, value.strip().strip('"').strip("'"))


def wp_credentials() -> tuple[str, str]:
    user = os.getenv("WP_API_USERNAME", "").strip()
    password = os.getenv("WP_API_PASSWORD", "").strip()
    if user and password:
        return user, password
    ssh_host = os.getenv("SSH_HOST", "").strip()
    wp_root = os.getenv("WP_DOCUMENT_ROOT", "").strip()
    if not ssh_host or not wp_root:
        raise SystemExit(
            "Set WP_API_USERNAME and WP_API_PASSWORD, or SSH_HOST and WP_DOCUMENT_ROOT to load them from the server .env"
        )
    raw = subprocess.check_output(
        [
            "ssh",
            ssh_host,
            f"grep -E '^WP_API_(USERNAME|PASSWORD)=' {wp_root}/.env",
        ],
        text=True,
    )
    found = {}
    for line in raw.splitlines():
        key, value = line.split("=", 1)
        found[key] = value.strip().strip('"').strip("'")
    return found["WP_API_USERNAME"], found["WP_API_PASSWORD"]


def request_json(url: str, method: str = "GET", payload: dict | None = None, auth: tuple[str, str] | None = None):
    data = None if payload is None else json.dumps(payload).encode()
    headers = {"Content-Type": "application/json", "User-Agent": "veriaguide-translate-el"}
    if auth:
        import base64

        token = base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
        headers["Authorization"] = f"Basic {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=120) as response:
        return json.loads(response.read().decode())


def fetch_posts(collection: str) -> list[dict]:
    posts = []
    page = 1
    while True:
        url = f"{SITE}/wp-json/wp/v2/{collection}?per_page=100&page={page}&status=publish"
        try:
            batch = request_json(url)
        except urllib.error.HTTPError as exc:
            if exc.code == 400 and page > 1:
                break
            raise
        if not batch:
            break
        posts.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return posts


def openrouter_translate(title: str, excerpt: str, content: str) -> dict[str, str]:
    key = os.environ["OPENROUTER_API_KEY"]
    model = os.environ.get("OPENROUTER_MODEL") or "google/gemini-2.5-flash"
    if "flash-exp" in model:
        model = "google/gemini-2.5-flash"
    prompt = json.dumps({"title": title, "excerpt": excerpt, "content": content}, ensure_ascii=False)
    body = {
        "model": model,
        "temperature": 0.2,
        "max_tokens": 4000,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You translate Veria, Greece tourism pages from English to Greek. "
                    "Keep HTML tags, attributes and URLs unchanged. Translate only visible text. "
                    "Use these place names: Βέροια, Βεργίνα, Ημαθία, Μακεδονία, Απόστολος Παύλος. "
                    "Return a JSON object with keys title, excerpt and content. No markdown."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    }
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as response:
        payload = json.loads(response.read().decode())
    text = payload["choices"][0]["message"]["content"].strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    translated = json.loads(text)
    return {
        "title_el": str(translated["title"]).strip(),
        "excerpt_el": str(translated["excerpt"]).strip(),
        "content_el": str(translated["content"]).strip(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="Stop after this many translations (0 = all)")
    args = parser.parse_args()
    load_local_env()
    if not os.environ.get("OPENROUTER_API_KEY"):
        raise SystemExit("OPENROUTER_API_KEY is missing")
    username, password = wp_credentials()
    translated = skipped = failed = 0
    for collection in COLLECTIONS:
        for post in fetch_posts(collection):
            meta = post.get("meta") or {}
            if isinstance(meta, dict) and (meta.get("title_el") or "").strip():
                skipped += 1
                continue
            title = (post.get("title") or {}).get("rendered") or ""
            excerpt = (post.get("excerpt") or {}).get("rendered") or ""
            content = (post.get("content") or {}).get("rendered") or ""
            if not title.strip():
                skipped += 1
                continue
            try:
                fields = openrouter_translate(title, excerpt, content)
                request_json(
                    f"{SITE}/wp-json/veriaguide/v1/translation",
                    method="POST",
                    payload={"id": post["id"], **fields},
                    auth=(username, password),
                )
            except urllib.error.HTTPError as exc:
                failed += 1
                print(f"failed {collection} {post.get('id')}: HTTP {exc.code}")
                if exc.code in (401, 402, 429):
                    print(f"stopped translated={translated} skipped={skipped} failed={failed}")
                    return
            except Exception as exc:
                failed += 1
                print(f"failed {collection} {post.get('id')}: {exc.__class__.__name__}")
                continue
            translated += 1
            print(f"ok {collection} {post.get('id')}")
            if args.limit and translated >= args.limit:
                print(f"done translated={translated} skipped={skipped} failed={failed}")
                return
            time.sleep(0.4)
    print(f"done translated={translated} skipped={skipped} failed={failed}")


if __name__ == "__main__":
    main()
