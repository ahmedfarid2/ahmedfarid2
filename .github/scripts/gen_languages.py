#!/usr/bin/env python3
"""Generate a static "Most Used Languages" SVG from a user's public repos.

Runs inside GitHub Actions using only the built-in GITHUB_TOKEN (public read),
so it needs no personal access token. Aggregates language byte counts across all
public, non-fork repositories owned by GH_USER and renders a compact dark-themed
card that is committed to the repo as languages.svg — because GitHub serves that
file directly, it can never render as the broken "image not exist" icon.
"""

import json
import os
import sys
import urllib.request
import urllib.error

USER = os.environ.get("GH_USER", "ahmedfarid2")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUTPUT = os.environ.get("OUTPUT", "languages.svg")
TOP_N = int(os.environ.get("TOP_N", "8"))
# Languages to exclude from the breakdown (matches the old card's hide= list)
EXCLUDE = {s.strip().lower() for s in os.environ.get(
    "EXCLUDE", "jupyter notebook").split(",") if s.strip()}

# GitHub linguist colors for the languages likely to appear; unknown -> grey.
COLORS = {
    "php": "#4F5D95", "javascript": "#f1e05a", "typescript": "#3178c6",
    "dart": "#00B4AB", "python": "#3572A5", "html": "#e34c26", "css": "#563d7c",
    "scss": "#c6538c", "less": "#1d365d", "vue": "#41b883", "blade": "#f7523f",
    "go": "#00ADD8", "shell": "#89e051", "ruby": "#701516", "java": "#b07219",
    "kotlin": "#A97BFF", "swift": "#F05138", "c": "#555555", "c++": "#f34b7d",
    "c#": "#178600", "objective-c": "#438eff", "rust": "#dea584",
    "dockerfile": "#384d54", "makefile": "#427819", "hcl": "#844FBA",
    "vim script": "#199f4b", "lua": "#000080", "perl": "#0298c3",
    "mdx": "#fcb32c", "astro": "#ff5a03", "svelte": "#ff3e00",
    "jupyter notebook": "#DA5B0B", "smarty": "#f0c040", "procfile": "#858585",
}
DEFAULT_COLOR = "#858585"


def api(url):
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", f"{USER}-languages-svg")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def list_public_repos():
    repos, page = [], 1
    while True:
        batch = api(f"https://api.github.com/users/{USER}/repos"
                    f"?per_page=100&type=owner&page={page}")
        if not batch:
            break
        for repo in batch:
            if repo.get("fork"):
                continue
            repos.append(repo["name"])
        if len(batch) < 100:
            break
        page += 1
    return repos


def aggregate_languages(repos):
    totals = {}
    for name in repos:
        try:
            langs = api(f"https://api.github.com/repos/{USER}/{name}/languages")
        except urllib.error.HTTPError:
            continue
        for lang, size in langs.items():
            if lang.lower() in EXCLUDE:
                continue
            totals[lang] = totals.get(lang, 0) + int(size)
    return totals


def esc(text):
    return (text.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def build_svg(totals):
    items = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:TOP_N]
    grand = sum(size for _, size in items) or 1
    items = [(name, size, 100.0 * size / grand) for name, size in items]

    width = 360
    pad = 25
    bar_w = width - 2 * pad
    rows = (len(items) + 1) // 2
    height = 62 + rows * 26 + 12

    def color(name):
        return COLORS.get(name.lower(), DEFAULT_COLOR)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}" '
        f'fill="none" role="img" aria-label="Most Used Languages">',
        '<style>text{font-family:"Segoe UI",Ubuntu,Sans-Serif;}</style>',
        f'<rect x="0.5" y="0.5" width="{width-1}" height="{height-1}" rx="8" '
        f'fill="#0D1117"/>',
        f'<text x="{pad}" y="30" fill="#00FFAA" font-size="16" '
        f'font-weight="600">Most Used Languages</text>',
    ]

    # Stacked proportion bar
    bar_y = 44
    x = float(pad)
    parts.append(f'<rect x="{pad}" y="{bar_y}" rx="4" width="{bar_w}" '
                 f'height="8" fill="#21262d"/>')
    parts.append(f'<mask id="m"><rect x="{pad}" y="{bar_y}" rx="4" '
                 f'width="{bar_w}" height="8" fill="#fff"/></mask>')
    parts.append('<g mask="url(#m)">')
    for name, _size, pct in items:
        seg = bar_w * pct / 100.0
        parts.append(f'<rect x="{x:.2f}" y="{bar_y}" width="{seg:.2f}" '
                     f'height="8" fill="{color(name)}"/>')
        x += seg
    parts.append('</g>')

    # Two-column legend
    col_x = [pad, pad + bar_w // 2 + 5]
    start_y = 78
    for i, (name, _size, pct) in enumerate(items):
        cx = col_x[i % 2]
        cy = start_y + (i // 2) * 26
        parts.append(f'<circle cx="{cx+5}" cy="{cy-4}" r="5" '
                     f'fill="{color(name)}"/>')
        parts.append(f'<text x="{cx+18}" y="{cy}" fill="#C9D1D9" '
                     f'font-size="12">{esc(name)} '
                     f'<tspan fill="#8b949e">{pct:.1f}%</tspan></text>')

    parts.append('</svg>')
    return "\n".join(parts)


def main():
    repos = list_public_repos()
    totals = aggregate_languages(repos)
    if not totals:
        print("No language data found; leaving existing SVG unchanged.",
              file=sys.stderr)
        return 0
    svg = build_svg(totals)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(svg)
    top = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:TOP_N]
    print(f"Scanned {len(repos)} repos. Top languages: "
          + ", ".join(n for n, _ in top))
    return 0


if __name__ == "__main__":
    sys.exit(main())
