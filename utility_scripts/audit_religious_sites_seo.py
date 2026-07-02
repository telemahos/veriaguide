#!/usr/bin/env python3
"""Audit Religious Sites SEO content via WordPress REST API."""
from __future__ import annotations

import json
import re
import ssl
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = "https://veriaguide.gr/wp-json/wp/v2/religious_sites?per_page=100&page={page}&_fields=id,slug,title,excerpt,content"
GEO = ("veria", "veroia", "imathia", "greece", "byzantine", "macedonia", "orthodox")
BROKEN_LINK = re.compile(
    r"artifacts\.grokusercontent\.com|href=[\"']#[\"']", re.I
)


def strip_html(value: str) -> str:
    if not value:
        return ""
    text = re.sub(r"<[^>]+>", "", value)
    text = text.replace("&hellip;", "…").replace("&#8230;", "…").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", text).strip()


def fetch_posts() -> list[dict]:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    posts: list[dict] = []
    page = 1
    while True:
        with urllib.request.urlopen(API.format(page=page), context=ctx, timeout=90) as response:
            batch = json.load(response)
        if not batch:
            break
        posts.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return posts


def score_post(post: dict) -> dict:
    title = strip_html(post["title"]["rendered"])
    excerpt = strip_html(post["excerpt"]["rendered"])
    content = strip_html(post["content"]["rendered"])
    raw_content = post["content"]["rendered"]
    issues: list[str] = []
    score = 100

    if len(excerpt) < 40:
        issues.append("excerpt_too_short")
        score -= 35
    elif len(excerpt) < 80:
        issues.append("excerpt_thin")
        score -= 15

    if len(content) < 200:
        issues.append("content_thin")
        score -= 30
    elif len(content) < 500:
        issues.append("content_medium")
        score -= 10

    if not any(token in title.lower() for token in GEO):
        issues.append("title_no_geo")
        score -= 10

    combined = f"{excerpt} {content}".lower()
    if not any(token in combined for token in GEO):
        issues.append("body_no_geo")
        score -= 20

    if BROKEN_LINK.search(raw_content):
        issues.append("broken_link")
        score -= 15

    if "…" in excerpt or excerpt.endswith("..."):
        issues.append("excerpt_truncated")
        score -= 5

    if len(title) > 75:
        issues.append("title_long")
        score -= 5

    post_id = post["id"]
    slug = post["slug"]
    return {
        "id": post_id,
        "slug": slug,
        "title": title,
        "excerpt_len": len(excerpt),
        "content_len": len(content),
        "excerpt_preview": excerpt[:100] + ("…" if len(excerpt) > 100 else ""),
        "issues": issues,
        "score": max(0, score),
        "url": f"https://veriaguide.gr/religious_sites/{slug}",
        "wp_edit": f"https://veriaguide.gr/wp-admin/post.php?post={post_id}&action=edit",
    }


def write_markdown(report: dict, path: Path) -> None:
    lines = [
        "# Religious Sites – SEO Audit",
        "",
        f"> Generiert: {report['generated']} · Quelle: WordPress REST API",
        "",
        "## Übersicht",
        "",
        f"| Metrik | Wert |",
        f"|--------|------|",
        f"| Gesamt | {report['total']} |",
        f"| Gut (≥ 80) | {report['good_count']} |",
        f"| Schwach (< 80) | {report['weak_count']} |",
        f"| Kritisch (< 60) | {report['critical_count']} |",
        f"| Ø Excerpt-Länge | {report['avg_excerpt_len']} Zeichen |",
        f"| Ø Content-Länge | {report['avg_content_len']} Zeichen |",
        "",
        "## Häufige Probleme",
        "",
    ]
    for issue, count in report["issue_counts"].items():
        lines.append(f"- **{issue}:** {count} Beiträge")

    lines.extend(["", "## Kritisch (sofort bearbeiten)", ""])
    if report["critical"]:
        for item in report["critical"]:
            lines.append(f"### [{item['score']}] {item['title']}")
            lines.append(f"- Probleme: `{', '.join(item['issues'])}`")
            lines.append(f"- Excerpt: {item['excerpt_len']} Zeichen · Content: {item['content_len']} Zeichen")
            lines.append(f"- [Live]({item['url']}) · [WP bearbeiten]({item['wp_edit']})")
            lines.append("")
    else:
        lines.append("_Keine kritischen Einträge._\n")

    lines.extend(["## Schwach (< 80)", ""])
    weak_only = [w for w in report["weak"] if w["score"] >= 60]
    if weak_only:
        for item in weak_only:
            lines.append(
                f"- **[{item['score']}]** {item['title']} — "
                f"`{', '.join(item['issues'])}` · [WP]({item['wp_edit']})"
            )
    else:
        lines.append("_Keine weiteren schwachen Einträge außerhalb Kritisch._")

    broken = [i for i in report.get("broken_link_posts", [])]
    lines.extend(["", "## Kaputte Links (Grok / #)", ""])
    if broken:
        for item in broken:
            lines.append(f"- {item['title']} · [WP]({item['wp_edit']})")
    else:
        lines.append("_Keine kaputten Links gefunden._")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    posts = fetch_posts()
    scored = [score_post(post) for post in posts]
    scored.sort(key=lambda item: (item["score"], item["excerpt_len"]))

    weak = [item for item in scored if item["score"] < 80]
    critical = [item for item in scored if item["score"] < 60]
    good = [item for item in scored if item["score"] >= 80]
    broken_link_posts = [item for item in scored if "broken_link" in item["issues"]]

    report = {
        "generated": date.today().isoformat(),
        "total": len(scored),
        "good_count": len(good),
        "weak_count": len(weak),
        "critical_count": len(critical),
        "avg_excerpt_len": round(sum(item["excerpt_len"] for item in scored) / len(scored), 1) if scored else 0,
        "avg_content_len": round(sum(item["content_len"] for item in scored) / len(scored), 1) if scored else 0,
        "issue_counts": {
            issue: sum(1 for item in scored if issue in item["issues"])
            for issue in sorted({i for item in scored for i in item["issues"]})
        },
        "critical": critical,
        "weak": weak,
        "broken_link_posts": broken_link_posts,
        "all_scores": [{"title": item["title"], "score": item["score"], "slug": item["slug"]} for item in scored],
    }

    json_path = ROOT / "data" / "religious_sites_seo_audit.json"
    md_path = ROOT / "data" / "religious_sites_seo_audit.md"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(report, md_path)

    print(f"Audit: {report['total']} churches — good {report['good_count']}, weak {report['weak_count']}, critical {report['critical_count']}")
    print(f"Written: {json_path}")
    print(f"Written: {md_path}")


if __name__ == "__main__":
    main()
